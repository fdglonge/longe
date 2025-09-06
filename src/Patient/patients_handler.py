import firebase_admin
from firebase_admin import credentials, firestore
import os
from Patient.patient_instance import Patient
from datetime import datetime
import json

# Import delle nuove utility di sicurezza
from utils.security_utils import SecurityUtils


class PatientHandler:
    """
    Handler per la gestione dei pazienti su Firebase - VERSIONE CON SICUREZZA
    """

    def __init__(self):
        """
        Inizializza la connessione a Firebase
        """
        self.db = None
        self.initialized = False
        try:
            # Tenta di inizializzare Firebase (solo se non è già stato fatto)
            if not firebase_admin._apps:
                # Cerca il file delle credenziali
                base_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
                default_path = os.path.join(base_path, "key_firebase.json")
                cred_path = os.environ.get('FIREBASE_CREDENTIALS_PATH', default_path)

                print(f"🔍 Cerco credenziali Firebase in: {cred_path}")

                if os.path.exists(cred_path):
                    cred = credentials.Certificate(cred_path)
                    firebase_admin.initialize_app(cred)
                    self.db = firestore.client()
                    self.initialized = True
                    print("✅ Connessione a Firebase stabilita con successo")
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
                            self.initialized = True
                            print(f"✅ Connessione a Firebase stabilita con successo usando: {alt_path}")
                            break
            else:
                # Firebase già inizializzato, ottieni solo il client
                self.db = firestore.client()
                self.initialized = True
                print("✅ Connessione a Firebase già attiva")

        except Exception as e:
            print(f"❌ Errore durante l'inizializzazione di Firebase: {str(e)}")
            print("⚠️ Il sistema funzionerà in modalità offline")

    def search_patient_by_email(self, email):
        """
        Cerca un paziente solo per email (per il login)
        """
        if not self.initialized or not self.db:
            print("⚠️ Database non disponibile, ricerca non possibile")
            return None

        try:
            patients_ref = self.db.collection('patients')
            email = email.strip().lower()
            query = patients_ref.where('email', '==', email)
            results = query.get()

            if len(results) > 0:
                patient_data = results[0].to_dict()
                patient_data['id'] = results[0].id
                print(f"✅ Trovato paziente con email: {email}")
                return self.create_patient_from_data(patient_data)

            print(f"🔍 Nessun paziente trovato con email: {email}")
            return None

        except Exception as e:
            print(f"❌ Errore durante la ricerca del paziente: {str(e)}")
            return None

    def verify_patient_login(self, email, password):
        """
        Verifica le credenziali di login (email + password)

        Args:
            email: Email del paziente
            password: Password in chiaro

        Returns:
            Patient: Oggetto paziente se login riuscito, None altrimenti
        """
        if not self.initialized or not self.db:
            print("⚠️ Database non disponibile, login non possibile")
            return None

        try:
            # Cerca il paziente per email
            patients_ref = self.db.collection('patients')
            email = email.strip().lower()
            query = patients_ref.where('email', '==', email)
            results = query.get()

            if len(results) == 0:
                print(f"❌ Nessun account trovato per l'email: {email}")
                return None

            # Prendi il primo risultato
            patient_doc = results[0]
            patient_data = patient_doc.to_dict()
            patient_data['id'] = patient_doc.id

            # Verifica la password
            stored_password_hash = patient_data.get('passwordHash')
            stored_salt = patient_data.get('passwordSalt')

            if not stored_password_hash or not stored_salt:
                print("❌ Dati di autenticazione mancanti per questo account")
                return None

            # Verifica password con SecurityUtils
            is_valid = SecurityUtils.verify_password(password, stored_password_hash, stored_salt)

            if is_valid:
                print(f"✅ Login riuscito per: {email}")
                return self.create_patient_from_data(patient_data)
            else:
                print("❌ Password errata")
                return None

        except Exception as e:
            print(f"❌ Errore durante il login: {str(e)}")
            return None

    def search_patient(self, name=None, surname=None, email=None, fiscal_code=None):
        """
        Cerca un paziente per diversi criteri (mantenuto per compatibilità)
        """
        if not self.initialized or not self.db:
            print("⚠️ Database non disponibile, ricerca non possibile")
            return None

        try:
            patients_ref = self.db.collection('patients')

            # Cerca per nome e cognome
            if name and surname:
                name = name.strip().title()
                surname = surname.strip().title()
                query = patients_ref.where('name', '==', name).where('surname', '==', surname)
                results = query.get()

                if len(results) > 0:
                    patient_data = results[0].to_dict()
                    patient_data['id'] = results[0].id
                    print(f"✅ Trovato paziente: {name} {surname}")
                    return self.create_patient_from_data(patient_data)

            # Cerca per email
            if email:
                return self.search_patient_by_email(email)

            # Cerca per codice fiscale (ora usa l'ID documento)
            if fiscal_code:
                try:
                    # Genera l'ID documento dall'hash del codice fiscale
                    document_id = SecurityUtils.generate_firebase_document_id(fiscal_code.strip())

                    # Cerca direttamente per ID documento
                    doc_ref = patients_ref.document(document_id)
                    doc = doc_ref.get()

                    if doc.exists:
                        patient_data = doc.to_dict()
                        patient_data['id'] = doc.id
                        print(f"✅ Trovato paziente con codice fiscale")
                        return self.create_patient_from_data(patient_data)
                    else:
                        print(f"🔍 Nessun paziente trovato con questo codice fiscale")

                except Exception as e:
                    print(f"⚠️ Errore nella ricerca per codice fiscale: {e}")

            # Nessun risultato trovato
            print(f"🔍 Nessun paziente trovato con i criteri specificati")
            return None

        except Exception as e:
            print(f"❌ Errore durante la ricerca del paziente: {str(e)}")
            return None

    def create_patient_from_data(self, data):
        """
        Crea un oggetto Patient dai dati del database - VERSIONE CORRETTA
        """
        try:
            # Se i dati contengono 'lifeStyle' (camelCase da Firebase),
            # mappalo a 'lifestyle' (lowercase per l'oggetto Python)
            if 'lifeStyle' in data and 'lifestyle' not in data:
                data['lifestyle'] = data['lifeStyle']

            # Verifica che lifestyle abbia tutti i campi richiesti
            if 'lifestyle' in data and data['lifestyle']:
                required_fields = {
                    'physicalActivityFrequency': '',
                    'physicalActivityIntensity': '',
                    'typeOfDiet': '',
                    'alcoholFrequency': '',
                    'hoursOfSleep': 0,
                    'smokerFrequency': ''
                }

                lifestyle = data['lifestyle']
                for field, default_value in required_fields.items():
                    if field not in lifestyle:
                        lifestyle[field] = default_value

                data['lifestyle'] = lifestyle
                print(f"🔧 DEBUG: Lifestyle letto da DB: {lifestyle}")
            else:
                # Crea lifestyle vuoto se non presente
                data['lifestyle'] = {
                    'physicalActivityFrequency': '',
                    'physicalActivityIntensity': '',
                    'typeOfDiet': '',
                    'alcoholFrequency': '',
                    'hoursOfSleep': 0,
                    'smokerFrequency': ''
                }
                print("🔧 DEBUG: Creato lifestyle vuoto")

            # Crea l'oggetto Patient
            patient = Patient(data=data)

            print(f"🔧 DEBUG: Patient creato, lifestyle = {patient.get_lifestyle()}")
            return patient

        except Exception as e:
            print(f"❌ Errore durante la creazione dell'oggetto paziente: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def save_patient(self, patient, plain_password=None):
        """
        Salva un paziente nel database Firebase - VERSIONE CON SICUREZZA

        Args:
            patient: Oggetto Patient
            plain_password: Password in chiaro (solo per nuovi pazienti)

        Returns:
            tuple: (patient_id, password_mostrata_utente) o (None, None) se errore
        """
        if not self.initialized or not self.db:
            print("⚠️ Database non disponibile, salvataggio non possibile")
            return None, None

        try:
            # Controlla che ci siano i dati minimi necessari
            if not patient.get_name() or not patient.get_surname():
                print("❌ Impossibile salvare il paziente: nome o cognome mancanti")
                return None, None

            # Controlla che ci sia il codice fiscale
            fiscal_code = patient.get_fiscal_code()
            if not fiscal_code:
                print("❌ Impossibile salvare il paziente: codice fiscale mancante")
                return None, None

            # Prepara i dati del paziente
            patient_data = self.debug_save_patient(patient)

            # Aggiungi timestamp
            patient_data['createdAt'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]
            patient_data['updatedAt'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]

            # Genera l'ID documento dal codice fiscale
            document_id = SecurityUtils.generate_firebase_document_id(fiscal_code)

            # Controlla se è un nuovo paziente o aggiornamento
            patient_ref = self.db.collection('patients').document(document_id)
            existing_doc = patient_ref.get()

            password_to_show = None

            if existing_doc.exists:
                # Paziente esistente - aggiorna senza toccare la password
                print(f"📝 Aggiornamento paziente esistente: {document_id}")
                patient_ref.update(patient_data)
            else:
                # Nuovo paziente - genera credenziali complete
                if plain_password is None:
                    # Genera password casuale se non fornita
                    _, plain_password, password_hash, password_salt = SecurityUtils.generate_patient_credentials(
                        fiscal_code)
                else:
                    # Usa password fornita
                    password_hash, password_salt = SecurityUtils.hash_password(plain_password)

                # Aggiungi credenziali ai dati
                patient_data['passwordHash'] = password_hash
                patient_data['passwordSalt'] = password_salt

                # Salva nuovo paziente con ID specifico
                patient_ref.set(patient_data)
                password_to_show = plain_password

                print(f"✅ Nuovo paziente creato con ID: {document_id}")
                print(f"🔑 Password generata: {plain_password}")

            return document_id, password_to_show

        except Exception as e:
            print(f"❌ Errore durante il salvataggio del paziente: {str(e)}")
            import traceback
            traceback.print_exc()
            return None, None

    def update_patient_password(self, patient_id, new_password):
        """
        Aggiorna la password di un paziente esistente

        Args:
            patient_id: ID del documento Firebase
            new_password: Nuova password in chiaro

        Returns:
            bool: True se aggiornamento riuscito
        """
        if not self.initialized or not self.db:
            print("⚠️ Database non disponibile")
            return False

        try:
            # Hash della nuova password
            password_hash, password_salt = SecurityUtils.hash_password(new_password)

            # Aggiorna il documento
            patient_ref = self.db.collection('patients').document(patient_id)
            patient_ref.update({
                'passwordHash': password_hash,
                'passwordSalt': password_salt,
                'updatedAt': datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]
            })

            print(f"✅ Password aggiornata per paziente {patient_id}")
            return True

        except Exception as e:
            print(f"❌ Errore aggiornamento password: {e}")
            return False

    def update_patient_notes(self, patient_id, additional_notes):
        """
        Aggiorna solo le note aggiuntive di un paziente esistente
        """
        if not self.initialized or not self.db:
            print("⚠️ Database non disponibile")
            return False

        try:
            patient_ref = self.db.collection('patients').document(patient_id)
            patient_ref.update({
                'additionalNotes': additional_notes,
                'updatedAt': datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]
            })
            print(f"✅ Note aggiornate per paziente {patient_id}")
            return True
        except Exception as e:
            print(f"❌ Errore aggiornamento note: {e}")
            return False

    def debug_save_patient(self, patient):
        """Debug per verificare cosa viene salvato"""
        print("🔍 DEBUG: Preparazione salvataggio paziente")
        patient_data = patient.to_dict()

        print(f"   • Nome: {patient_data.get('name')}")
        print(f"   • Email: {patient_data.get('email')}")
        print(f"   • Codice Fiscale: {patient_data.get('fiscalCode', 'N/A')[:6]}***")
        print(f"   • lifeStyle presente: {'lifeStyle' in patient_data}")

        if 'lifeStyle' in patient_data:
            lifestyle = patient_data['lifeStyle']
            print(f"   • lifeStyle campi: {list(lifestyle.keys())}")

        return patient_data

    def check_email_exists(self, email):
        """
        Controlla se un'email è già registrata

        Args:
            email: Email da controllare

        Returns:
            bool: True se l'email esiste già
        """
        if not self.initialized or not self.db:
            return False

        try:
            patients_ref = self.db.collection('patients')
            email = email.strip().lower()
            query = patients_ref.where('email', '==', email)
            results = query.get()

            return len(results) > 0

        except Exception as e:
            print(f"❌ Errore controllo email: {e}")
            return False

    def check_fiscal_code_exists(self, fiscal_code):
        """
        Controlla se un codice fiscale è già registrato

        Args:
            fiscal_code: Codice fiscale da controllare

        Returns:
            bool: True se il codice fiscale esiste già
        """
        if not self.initialized or not self.db:
            return False

        try:
            # Genera l'ID documento dall'hash del codice fiscale
            document_id = SecurityUtils.generate_firebase_document_id(fiscal_code.strip())

            # Controlla se il documento esiste
            patient_ref = self.db.collection('patients').document(document_id)
            doc = patient_ref.get()

            return doc.exists

        except Exception as e:
            print(f"❌ Errore controllo codice fiscale: {e}")
            return False