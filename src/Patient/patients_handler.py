import firebase_admin
from firebase_admin import credentials, firestore
import os
from Patient.patient_instance import Patient
from datetime import datetime
import json


class PatientHandler:
    """
    Handler per la gestione dei pazienti su Firebase - VERSIONE CORRETTA
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

    def search_patient(self, name=None, surname=None, email=None, fiscal_code=None):
        """
        Cerca un paziente per nome e cognome, email o codice fiscale
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
                email = email.strip().lower()
                query = patients_ref.where('email', '==', email)
                results = query.get()

                if len(results) > 0:
                    patient_data = results[0].to_dict()
                    patient_data['id'] = results[0].id
                    print(f"✅ Trovato paziente con email: {email}")
                    return self.create_patient_from_data(patient_data)

            # Cerca per codice fiscale
            if fiscal_code:
                fiscal_code = fiscal_code.strip().upper()
                query = patients_ref.where('fiscalCode', '==', fiscal_code)
                results = query.get()

                if len(results) > 0:
                    patient_data = results[0].to_dict()
                    patient_data['id'] = results[0].id
                    print(f"✅ Trovato paziente con codice fiscale: {fiscal_code}")
                    return self.create_patient_from_data(patient_data)

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
            # ✅ CORREZIONE: Assicurati che lifeStyle sia mappato correttamente

            # Se i dati contengono 'lifeStyle' (camelCase da Firebase),
            # mappalo a 'lifestyle' (lowercase per l'oggetto Python)
            if 'lifeStyle' in data and 'lifestyle' not in data:
                data['lifestyle'] = data['lifeStyle']

            # ✅ VERIFICA che lifestyle abbia tutti i campi richiesti
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

            # ✅ VERIFICA FINALE che il lifestyle sia stato impostato correttamente
            print(f"🔧 DEBUG: Patient creato, lifestyle = {patient.get_lifestyle()}")

            return patient

        except Exception as e:
            print(f"❌ Errore durante la creazione dell'oggetto paziente: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def save_patient(self, patient):
        """
        Salva un paziente nel database Firebase - VERSIONE CON DEBUG
        """
        if not self.initialized or not self.db:
            print("⚠️ Database non disponibile, salvataggio non possibile")
            return None

        try:
            # Controlla che ci siano i dati minimi necessari
            if not patient.get_name() or not patient.get_surname():
                print("❌ Impossibile salvare il paziente: nome o cognome mancanti")
                return None

            # ✅ DEBUG: Verifica cosa stiamo per salvare
            patient_data = self.debug_save_patient(patient)

            # Aggiungi timestamp
            patient_data['createdAt'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]
            patient_data['updatedAt'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]

            # Usa ID esistente se disponibile
            patient_id = None
            if hasattr(patient, 'id') and patient.id:
                patient_id = patient.id
                patient_ref = self.db.collection('patients').document(patient_id)
                patient_ref.set(patient_data)
                print(f"✅ Paziente aggiornato con ID: {patient_id}")
            else:
                # Crea un nuovo documento
                patient_ref = self.db.collection('patients').add(patient_data)
                patient_id = patient_ref[1].id
                print(f"✅ Nuovo paziente creato con ID: {patient_id}")

            return patient_id

        except Exception as e:
            print(f"❌ Errore durante il salvataggio del paziente: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

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
        print(f"   • lifeStyle presente: {'lifeStyle' in patient_data}")
        if 'lifeStyle' in patient_data:
            lifestyle = patient_data['lifeStyle']
            print(f"   • lifeStyle campi: {list(lifestyle.keys())}")
            print(f"   • smokerFrequency: '{lifestyle.get('smokerFrequency')}'")
            print(f"   • hoursOfSleep: {lifestyle.get('hoursOfSleep')}")
            print(f"   • physicalActivityFrequency: '{lifestyle.get('physicalActivityFrequency')}'")
            print(f"   • physicalActivityIntensity: '{lifestyle.get('physicalActivityIntensity')}'")
            print(f"   • alcoholFrequency: '{lifestyle.get('alcoholFrequency')}'")
            print(f"   • typeOfDiet: '{lifestyle.get('typeOfDiet')}'")

        return patient_data