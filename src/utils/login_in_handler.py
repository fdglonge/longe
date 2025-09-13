from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore
import os
import sys
from typing import Dict, Optional

# Aggiungi percorsi per import
current_dir = os.path.dirname(__file__)
src_dir = os.path.dirname(current_dir)
sys.path.insert(0, src_dir)

try:
    from Patient.patient_instance import Patient
    from utils.security_utils import SecurityUtils
except ImportError:
    print("⚠️ Impossibile importare dipendenze - modalità test")
    Patient = None
    SecurityUtils = None


class LoginInHandler:
    """
    Classe per la gestione del login con email e password.
    VERSIONE AGGIORNATA CON AUTENTICAZIONE SICURA
    """

    def __init__(self, email: str, password: str):
        self.email = email.lower().strip()  # Normalizza email
        self.password = password  # Password in chiaro (sarà verificata)
        self.db = None
        self.patient_data = None
        self.patient_doc_id = None
        self.login_successful = False

        # Inizializza Firebase
        if self.firebase_access():
            # Effettua il login con email e password
            self.login()
        else:
            raise Exception("Impossibile connettersi al database")

    def firebase_access(self) -> bool:
        """
        Inizializza la connessione a Firebase
        Returns:
            bool: True se la connessione è riuscita, False altrimenti
        """
        try:
            # Controlla se Firebase è già inizializzato
            if not firebase_admin._apps:
                base_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
                default_path = os.path.join(base_path, "key_firebase.json")
                cred_path = os.environ.get('FIREBASE_CREDENTIALS_PATH', default_path)

                print(f"🔍 Cerco credenziali Firebase in: {cred_path}")

                if os.path.exists(cred_path):
                    cred = credentials.Certificate(cred_path)
                    firebase_admin.initialize_app(cred)
                    self.db = firestore.client()
                    print("🔥 Firebase inizializzato con credenziali")
                else:
                    print(f"❌ File di credenziali Firebase non trovato: {cred_path}")
                    # Prova a cercare in percorsi alternativi
                    alternative_paths = [
                        "./key_firebase.json",
                        "../key_firebase.json",
                        "key_firebase.json"
                    ]
                    for alt_path in alternative_paths:
                        print(f"🔍 Tentativo con percorso alternativo: {alt_path}")
                        if os.path.exists(alt_path):
                            cred = credentials.Certificate(alt_path)
                            firebase_admin.initialize_app(cred)
                            self.db = firestore.client()
                            print(f"✅ Firebase inizializzato con {alt_path}")
                            break
                    else:
                        print("❌ Nessun file di credenziali Firebase trovato")
                        return False
            else:
                # Firebase già inizializzato, ottieni solo il client
                self.db = firestore.client()
                print("✅ Connessione a Firebase già attiva")

            return True

        except Exception as e:
            print(f"❌ Errore connessione Firebase: {e}")
            return False

    def login(self) -> bool:
        """
        Controlla email e password e effettua il login
        Returns:
            bool: True se il login è riuscito, False altrimenti
        """
        try:
            print(f"🔍 Tentativo di login con email: {self.email}")

            # Verifica che SecurityUtils sia disponibile
            if not SecurityUtils:
                raise Exception("SecurityUtils non disponibile")

            # Query per trovare il paziente con questa email
            patients_ref = self.db.collection('patients')
            query = patients_ref.where('email', '==', self.email)
            docs = query.get()

            if not docs:
                print(f"❌ Nessun account trovato per l'email: {self.email}")
                raise Exception(f"Account non trovato per l'email: {self.email}")

            # Paziente trovato, verifica la password
            for doc in docs:
                patient_data = doc.to_dict()

                # Controlla che ci siano i dati di autenticazione
                stored_password_hash = patient_data.get('passwordHash')
                stored_salt = patient_data.get('passwordSalt')

                if not stored_password_hash or not stored_salt:
                    print("❌ Account senza dati di autenticazione. Contatta il supporto.")
                    raise Exception("Account senza dati di autenticazione validi")

                # Verifica la password
                is_password_valid = SecurityUtils.verify_password(
                    self.password,
                    stored_password_hash,
                    stored_salt
                )

                if is_password_valid:
                    # Login riuscito!
                    self.patient_doc_id = doc.id
                    self.patient_data = patient_data
                    self.login_successful = True

                    name = patient_data.get('name', 'N/A')
                    surname = patient_data.get('surname', 'N/A')
                    print(f"✅ Login riuscito! Paziente: {name} {surname}")

                    # Aggiorna ultimo accesso
                    self.update_last_access()

                    return True
                else:
                    print("❌ Password errata")
                    raise Exception("Password errata")

            # Se arriviamo qui, qualcosa è andato storto
            print("❌ Errore imprevisto durante il login")
            raise Exception("Errore imprevisto durante l'autenticazione")

        except Exception as e:
            print(f"❌ Errore durante il login: {e}")
            self.login_successful = False
            raise e

    def get_data(self) -> Optional[Dict]:
        """
        In caso di login andato bene, recupera tutti i dati del paziente
        Returns:
            Dict: Dizionario con tutti i dati del paziente, None se login fallito
        """
        if not self.login_successful or not self.patient_data:
            print("❌ Login non effettuato o dati non disponibili")
            return None

        try:
            # Recupera dati aggiornati dal database
            if self.patient_doc_id:
                doc_ref = self.db.collection('patients').document(self.patient_doc_id)
                fresh_data = doc_ref.get()

                if fresh_data.exists:
                    self.patient_data = fresh_data.to_dict()
                    print("📊 Dati del paziente aggiornati dal database")
                else:
                    print("⚠️ Documento paziente non più esistente, uso dati in cache")

            # Log dei dati recuperati (nascondendo informazioni sensibili)
            masked_data = self._mask_sensitive_data(self.patient_data.copy())
            print(f"📋 Dati recuperati: {masked_data}")

            return self.patient_data

        except Exception as e:
            print(f"❌ Errore nel recupero dati: {e}")
            return self.patient_data  # Restituisci almeno i dati in cache

    def _mask_sensitive_data(self, data: Dict) -> Dict:
        """
        Maschera dati sensibili per il logging
        Args:
            data: Dizionario dei dati del paziente
        Returns:
            Dict: Dati con informazioni sensibili mascherate
        """
        if not data:
            return {}

        masked = data.copy()

        # Maschera email
        email = masked.get('email', '')
        if email and '@' in email:
            local, domain = email.split('@', 1)
            masked['email'] = f"{local[:2]}***@{domain}"

        # Maschera telefono se presente
        if 'contact_info' in masked and 'phone' in masked['contact_info']:
            phone = str(masked['contact_info']['phone'])
            if len(phone) > 4:
                masked['contact_info']['phone'] = f"***{phone[-4:]}"

        # Maschera codice fiscale se presente
        if 'fiscalCode' in masked:
            cf = masked['fiscalCode']
            if len(cf) > 4:
                masked['fiscalCode'] = f"***{cf[-4:]}"

        # Rimuovi dati di autenticazione dal log
        if 'passwordHash' in masked:
            masked['passwordHash'] = "***MASKED***"
        if 'passwordSalt' in masked:
            masked['passwordSalt'] = "***MASKED***"

        return masked

    def create_patient_instance(self) -> Optional[Patient]:
        """
        Crea un'istanza di Patient dai dati recuperati
        Returns:
            Patient: Istanza del paziente o None se fallito
        """
        if not self.login_successful or not self.patient_data or not Patient:
            return None

        try:
            # Crea nuovo paziente dai dati del database
            patient = Patient(data=self.patient_data)

            # Imposta l'ID del documento
            patient.id = self.patient_doc_id

            print("✅ Istanza Patient creata dai dati del database")
            return patient

        except Exception as e:
            print(f"❌ Errore nella creazione dell'istanza Patient: {e}")
            import traceback
            traceback.print_exc()
            return None

    def update_last_access(self):
        """Aggiorna il timestamp dell'ultimo accesso"""
        if not self.login_successful or not self.patient_doc_id:
            return

        try:
            from datetime import datetime

            doc_ref = self.db.collection('patients').document(self.patient_doc_id)
            doc_ref.update({
                'lastAccess': datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3],
                'accessCount': firestore.Increment(1)
            })

            print("📅 Ultimo accesso aggiornato")

        except Exception as e:
            print(f"⚠️ Errore aggiornamento ultimo accesso: {e}")

    def get_patient_summary(self) -> str:
        """
        Restituisce un riassunto leggibile del paziente
        Returns:
            str: Riassunto del paziente
        """
        if not self.patient_data:
            return "Nessun dato disponibile"

        name = self.patient_data.get('name', 'N/A')
        surname = self.patient_data.get('surname', 'N/A')
        age = self.patient_data.get('age', 'N/A')

        # Calcola età dalla data di nascita se disponibile
        if 'birthdate' in self.patient_data and str(age) == 'N/A':
            try:
                from datetime import datetime
                birthdate_str = self.patient_data['birthdate']
                # Assumendo formato ISO: "1999-01-28T00:00:00.000"
                birthdate = datetime.fromisoformat(birthdate_str.replace('Z', '+00:00'))
                age = datetime.now().year - birthdate.year
            except:
                age = 'N/A'

        # Gestisci city da vari campi possibili
        city = (self.patient_data.get('city') or
                self.patient_data.get('address', {}).get('city', 'N/A'))

        # Gestisci last purpose
        last_purpose = (self.patient_data.get('last_purpose') or
                        self.patient_data.get('purpose') or
                        self.patient_data.get('lastVisitReason') or
                        'Nessuna visita precedente')

        return f"""
👤 {name} {surname}
🎂 Età: {age} anni
🏙️ Città: {city}
📧 Email: {self.email}
🩺 Ultima richiesta: {last_purpose}
        """.strip()

    def is_logged_in(self) -> bool:
        """
        Verifica se il login è stato effettuato con successo
        Returns:
            bool: True se loggato, False altrimenti
        """
        return self.login_successful

    def get_patient_id(self) -> Optional[str]:
        """
        Restituisce l'ID del documento del paziente
        Returns:
            str: ID del documento o None
        """
        return self.patient_doc_id if self.login_successful else None

    def change_password(self, new_password: str) -> bool:
        """
        Cambia la password del paziente loggato

        Args:
            new_password: Nuova password in chiaro

        Returns:
            bool: True se il cambio è riuscito
        """
        if not self.login_successful or not self.patient_doc_id or not SecurityUtils:
            print("❌ Login non effettuato o SecurityUtils non disponibile")
            return False

        try:
            # Hash della nuova password
            password_hash, password_salt = SecurityUtils.hash_password(new_password)

            # Aggiorna il documento
            doc_ref = self.db.collection('patients').document(self.patient_doc_id)
            doc_ref.update({
                'passwordHash': password_hash,
                'passwordSalt': password_salt,
                'updatedAt': datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]
            })

            print("✅ Password cambiata con successo")
            return True

        except Exception as e:
            print(f"❌ Errore nel cambio password: {e}")
            return False


# Funzione di test
if __name__ == "__main__":
    print("🧪 Test LoginInHandler con autenticazione")

    try:
        email = input("Inserisci email: ").strip()
        password = input("Inserisci password: ").strip()

        login_handler = LoginInHandler(email, password)

        if login_handler.is_logged_in():
            print("\n" + "=" * 50)
            print("LOGIN RIUSCITO!")
            print("=" * 50)

            print(login_handler.get_patient_summary())

            # Test recupero dati
            data = login_handler.get_data()
            if data:
                print(f"\n📊 Dati completi disponibili: {len(data)} campi")

            # Test creazione Patient
            patient = login_handler.create_patient_instance()
            if patient:
                print(f"✅ Istanza Patient creata: {patient.get_full_name()}")

            # Test cambio password (opzionale)
            change_pwd = input("\nVuoi cambiare la password? (s/n): ").strip().lower()
            if change_pwd == 's':
                new_password = input("Nuova password: ").strip()
                if login_handler.change_password(new_password):
                    print("✅ Password cambiata!")
                else:
                    print("❌ Errore nel cambio password")

        else:
            print("❌ Login fallito")

    except Exception as e:
        print(f"❌ Errore nel test: {e}")
        import traceback

        traceback.print_exc()