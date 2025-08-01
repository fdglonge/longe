import firebase_admin
from firebase_admin import credentials, firestore
import os
from Doctor.doctor_instance import Doctor
from datetime import datetime


class DoctorHandler:
    """
    Handler per la gestione dei dottori su Firebase - VERSIONE CORRETTA
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

    def search_doctor(self, name=None, surname=None, specialization=None):
        """
        Cerca un dottore per nome, cognome o specializzazione
        """
        if not self.initialized or not self.db:
            print("⚠️ Database non disponibile, ricerca non possibile")
            return None

        try:
            doctors_ref = self.db.collection('doctors')
            query = doctors_ref

            # Filtra per nome se fornito
            if name:
                name = name.strip().title()
                query = query.where('name', '==', name)

            # Filtra per cognome se fornito
            if surname:
                surname = surname.strip().title()
                query = query.where('surname', '==', surname)

            # Filtra per specializzazione se fornita
            if specialization:
                specialization = specialization.strip().lower()
                query = query.where('specialty', '==', specialization)

            # Esegui la query
            results = query.get()

            # Processa i risultati
            if name and surname:
                # Cerca un dottore specifico
                for doc in results:
                    doctor_data = doc.to_dict()
                    doctor_data['id'] = doc.id
                    print(f"✅ Trovato dottore: {doctor_data.get('name', 'N/A')} {doctor_data.get('surname', 'N/A')}")
                    return self.create_doctor_from_data(doctor_data)

                print(f"🔍 Nessun dottore trovato con nome: {name} {surname}")
                return None
            else:
                # Cerca per specializzazione o tutti i dottori
                doctors = []
                for doc in results:
                    doctor_data = doc.to_dict()
                    doctor_data['id'] = doc.id
                    doctor = self.create_doctor_from_data(doctor_data)
                    if doctor and doctor.get_name():  # Verifica dati minimi
                        doctors.append(doctor)

                if doctors:
                    if specialization:
                        print(f"✅ Trovati {len(doctors)} dottori con specializzazione: {specialization}")
                    else:
                        print(f"✅ Trovati {len(doctors)} dottori")
                    return doctors
                else:
                    print(f"🔍 Nessun dottore trovato con i criteri specificati")
                    return None

        except Exception as e:
            print(f"❌ Errore durante la ricerca del dottore: {str(e)}")
            return None

    def create_doctor_from_data(self, data):
        """
        Crea un oggetto Doctor dai dati del database - VERSIONE CORRETTA
        """
        try:
            # ✅ CORRETTO: Passa tutto il dizionario alla classe Doctor
            doctor = Doctor(data=data)
            return doctor

        except Exception as e:
            print(f"❌ Errore durante la creazione dell'oggetto dottore: {str(e)}")
            return None

    def get_all_doctors(self, limit=50):
        """
        Recupera tutti i dottori dal database
        """
        if not self.initialized or not self.db:
            print("⚠️ Database non disponibile, ricerca non possibile")
            return []

        try:
            doctors_ref = self.db.collection('doctors').limit(limit)
            results = doctors_ref.get()

            doctors = []
            for doc in results:
                try:
                    doctor_data = doc.to_dict()
                    doctor_data['id'] = doc.id
                    print(f"🔍 Dottore trovato: {doctor_data.get('name', 'N/A')} {doctor_data.get('surname', 'N/A')}")

                    # ✅ CORRETTO: Usa create_doctor_from_data che passa il dizionario completo
                    doctor_obj = self.create_doctor_from_data(doctor_data)

                    if doctor_obj and doctor_obj.get_name():
                        doctors.append(doctor_obj)
                    else:
                        print(f"⚠️ Dottore ignorato - dati incompleti: {doctor_data.get('id')}")

                except Exception as e:
                    print(f"⚠️ Errore nella creazione del dottore: {str(e)}")

            print(f"✅ Recuperati {len(doctors)} dottori dal database")
            return doctors

        except Exception as e:
            print(f"❌ Errore durante il recupero dei dottori: {str(e)}")
            return []

    def save_doctor(self, doctor):
        """
        Salva un dottore nel database Firebase
        """
        if not self.initialized or not self.db:
            print("⚠️ Database non disponibile, salvataggio non possibile")
            return None

        try:
            # Controlla che ci siano i dati minimi necessari
            if not doctor.get_name():
                print("❌ Impossibile salvare il dottore: nome mancante")
                return None

            # Usa to_dict() per convertire in formato Firebase
            doctor_data = doctor.to_dict()
            doctor_data['createdAt'] = datetime.now()

            # Usa ID esistente se disponibile
            doctor_id = None
            if hasattr(doctor, 'id') and doctor.id:
                doctor_id = doctor.id
                doctor_ref = self.db.collection('doctors').document(doctor_id)
                doctor_ref.set(doctor_data)
                print(f"✅ Dottore aggiornato con ID: {doctor_id}")
            else:
                # Crea un nuovo documento
                doctor_ref = self.db.collection('doctors').add(doctor_data)
                doctor_id = doctor_ref[1].id
                print(f"✅ Nuovo dottore creato con ID: {doctor_id}")

            return doctor_id

        except Exception as e:
            print(f"❌ Errore durante il salvataggio del dottore: {str(e)}")
            return None