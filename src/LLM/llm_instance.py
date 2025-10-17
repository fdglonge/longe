from src.Patient.patient_instance import Patient
from src.Doctor.doctor_instance import Doctor
import re
import json
import traceback


class LLM:
    def __init__(self, model_name="mistral:7b"):
        self.model_name = model_name
        self.ollama_client = None
        self.context = None

        # Stati del flusso conversazionale aggiornati
        self.conversation_state = "init"
        # Stati: init, collect_overview, confirm_data, collect_missing_data,
        #        collect_purpose, recommend_doctor, schedule_appointment, closing

        self.current_question = None
        self.patient = Patient()  # Inizializza con un oggetto Patient vuoto
        self.recommended_doctor = None
        self.extracted_data = {}  # Dati estratti dall'overview
        self.missing_data = []  # Dati mancanti da richiedere

        # Liste per specializzazioni e condizioni mediche
        self.specializations = [
            "Medicina Generale", "Cardiologia", "Dermatologia", "Neurologia",
            "Psichiatria", "Ortopedia", "Oculistica", "Odontoiatria",
            "Ginecologia", "Pediatria"
        ]

        # Parole chiave per estrazione dati
        self.data_extraction_patterns = {
            "name": [
                r"mi chiamo (\w+)",
                r"sono (\w+)",
                r"il mio nome è (\w+)",
                r"sono il/la signor/a (\w+)"
            ],
            "age": [
                r"ho (\d+) anni",
                r"(\d+) anni",
                r"età (\d+)",
                r"sono un/a (\w+) di (\d+) anni"
            ],
            "city": [
                r"vivo a (\w+)",
                r"abito a (\w+)",
                r"di (\w+)",
                r"sono di (\w+)",
                r"da (\w+)"
            ],
            "height": [
                r"alto/a (\d+\.?\d*) (?:cm|centimetri)",
                r"(\d+\.?\d*) (?:cm|centimetri)",
                r"altezza (\d+\.?\d*)",
                r"sono alto/a (\d+\.?\d*)"
            ],
            "weight": [
                r"peso (\d+\.?\d*) (?:kg|chili)",
                r"(\d+\.?\d*) (?:kg|chili)",
                r"peso (\d+\.?\d*)"
            ],
            "sex": [
                r"sono un uomo",
                r"sono una donna",
                r"maschio",
                r"femmina",
                r"genere (\w+)"
            ],
            "phone": [
                r"(\+?39\s?\d{3}\s?\d{6,7})",
                r"(\d{10})",
                r"telefono (\+?39\s?\d{3}\s?\d{6,7})"
            ],
            "allergies": [
                r"allergico/a (?:a|al|alla) ([\w\s,]+)",
                r"allergie? (?:a|al|alla) ([\w\s,]+)",
                r"non posso prendere ([\w\s,]+)"
            ]
        }

        # Inizializza connessione Ollama
        self._init_ollama()

    def _init_ollama(self):
        """Inizializza la connessione con Ollama"""
        try:
            import ollama
            self.ollama_client = ollama
            print("Connessione a Ollama stabilita con successo.")

            # Test del modello
            try:
                print(f"Test del modello '{self.model_name}'...")
                response = self.ollama_client.generate(
                    model=self.model_name,
                    prompt="Ciao",
                    stream=False
                )
                print(f"Test completato! Modello '{self.model_name}' funzionante.")
                return True
            except Exception as e:
                print(f"Errore nel testare il modello: {e}")

                # Fallback a modelli alternativi
                fallback_models = ["mistral:7b", "llama2", "codellama"]
                for model in fallback_models:
                    try:
                        print(f"Tentativo con il modello alternativo '{model}'...")
                        response = self.ollama_client.generate(
                            model=model,
                            prompt="Ciao",
                            stream=False
                        )
                        print(f"Modello alternativo '{model}' funzionante.")
                        self.model_name = model
                        return True
                    except:
                        continue

                print("Nessun modello funzionante trovato. Modalità fallback attivata.")
                return False
        except ImportError:
            print("Errore: la libreria Ollama non è installata.")
            return False
        except Exception as e:
            print(f"Errore generale: {e}")
            return False

    def generate_response(self, prompt, system_prompt=None):
        """Genera una risposta dall'LLM usando Ollama"""
        if not self.ollama_client:
            # Risposte di fallback
            fallback_responses = {
                "init": "Benvenuto! Sono Longi di Longeviva. Per iniziare, potresti farmi una panoramica generale su di te?",
                "collect_overview": "Perfetto! Ora vorrei confermare i dati che ho capito dalla tua descrizione.",
                "confirm_data": "I dati sono corretti? Possiamo procedere?",
                "collect_missing_data": "Mi servono ancora alcune informazioni per completare il tuo profilo.",
                "collect_purpose": "Qual è il motivo della tua visita oggi?",
                "recommend_doctor": "Ti consiglio di consultare un medico specializzato per il tuo problema.",
                "schedule_appointment": "Vuoi prenotare un appuntamento?",
                "closing": "Grazie per aver utilizzato i nostri servizi!",
                "authentication": "Mi serve il tuo nome e cognome per verificare se sei già registrato."
            }
            return fallback_responses.get(self.conversation_state,
                                          "Mi dispiace, non riesco a elaborare la richiesta."), None

        try:
            request = {
                'model': self.model_name,
                'prompt': prompt
            }

            if system_prompt:
                request['system'] = system_prompt

            if self.context:
                request['context'] = self.context

            response = self.ollama_client.generate(**request)
            self.context = response.get('context')

            return response['response'], self.context
        except Exception as e:
            print(f"Errore nella generazione della risposta: {e}")
            return "Mi dispiace, non sono riuscito a elaborare la tua richiesta.", None

    def start_conversation(self):
        """Avvia la conversazione con il paziente"""
        self.conversation_state = "init"
        self.patient = Patient()  # Assicurati che il paziente sia inizializzato qui

        system_prompt = """
        Sei Longi di Longeviva, un assistente medico virtuale intelligente. 
        Il tuo compito è raccogliere informazioni sui pazienti in modo naturale e efficiente.
        Prima chiedi una panoramica generale, poi estrai i dati e confermi con il paziente.
        Sii amichevole, professionale e rassicurante.
        """

        welcome_prompt = """
        Presentati come Longi di Longeviva, assistente virtuale del centro medico Longeviva.
        Spiega che per creare il profilo del paziente, preferisci iniziare con una panoramica generale
        piuttosto che fare tante domande separate.
        Chiedi al paziente di presentarsi liberamente includendo nome, età, città, e qualsiasi informazione
        personale e medica che ritiene rilevante.
        """

        response, _ = self.generate_response(welcome_prompt, system_prompt)
        print(f"\nAssistente: {response}")

        self.conversation_state = "collect_overview"
        self.current_question = "general_overview"

        # Avvia il loop di conversazione
        self.conversation_loop()

    def conversation_loop(self):
        """Loop principale della conversazione"""
        while True:
            try:
                user_input = input("\nTu: ")

                # Gestisci comandi di uscita
                if user_input.lower() in ["exit", "quit", "esci", "fine"]:
                    self.handle_exit()
                    break

                # Debug
                print(f"🔍 DEBUG: Stato attuale: {self.conversation_state}, Domanda: {self.current_question}")

                # Elabora l'input dell'utente in base allo stato corrente
                if self.conversation_state == "authentication":
                    print(f"🔍 DEBUG: Chiamata a handle_authentication con input: '{user_input}'")
                    try:
                        self.handle_authentication(user_input)
                    except Exception as e:
                        print(f"❌ ERROR: Exception in handle_authentication: {e}")
                        traceback.print_exc()
                        # Assicurati che patient sia sempre inizializzato in caso di errore
                        if self.patient is None:
                            self.patient = Patient()
                        # Fallback alla raccolta dello scopo in caso di errore
                        self.conversation_state = "collect_purpose"
                        self.current_question = "main_purpose"
                        self.ask_for_purpose()

                elif self.conversation_state == "collect_overview":
                    self.handle_overview_collection(user_input)
                elif self.conversation_state == "confirm_data":
                    self.handle_data_confirmation(user_input)
                elif self.conversation_state == "collect_missing_data":
                    self.handle_missing_data_collection(user_input)
                elif self.conversation_state == "collect_purpose":
                    self.handle_purpose_info(user_input)
                elif self.conversation_state == "recommend_doctor":
                    self.handle_doctor_recommendation(user_input)
                elif self.conversation_state == "schedule_appointment":
                    self.handle_appointment_scheduling(user_input)
                elif self.conversation_state == "closing":
                    self.handle_closing(user_input)
                    if self.current_question == "end":
                        break
                elif self.conversation_state == "confirm_identity":
                    self.handle_identity_confirmation(user_input)
                elif self.conversation_state == "registration":
                    self.handle_registration(user_input)
                else:
                    print(f"⚠️ WARN: Stato non riconosciuto: {self.conversation_state}")
                    # Fallback alla raccolta dello scopo
                    self.conversation_state = "collect_purpose"
                    self.current_question = "main_purpose"
                    self.ask_for_purpose()

            except Exception as e:
                print(f"❌ Errore nel loop di conversazione: {e}")
                traceback.print_exc()

                # Assicurati che patient sia sempre inizializzato in caso di errore
                if self.patient is None:
                    self.patient = Patient()

                # Risposta di fallback
                print("\nAssistente: Mi scuso per l'errore. Come posso aiutarti?")

                # Resetta lo stato in caso di errore
                self.conversation_state = "collect_purpose"
                self.current_question = "main_purpose"

    def handle_overview_collection(self, user_input):
        """Gestisce la raccolta dell'overview generale e l'estrazione dei dati"""
        print("DEBUG: Elaborazione overview generale")

        # Estrai dati dall'input dell'utente
        self.extracted_data = self.extract_data_from_text(user_input)

        # Popola il paziente con i dati estratti
        self.populate_patient_from_extracted_data()

        # Determina quali dati mancano
        self.missing_data = self.identify_missing_essential_data()

        # Genera riassunto dei dati estratti
        summary = self.generate_data_summary()

        system_prompt = """
        Sei Longi di Longeviva. Hai appena estratto alcune informazioni dal racconto del paziente.
        Mostra un riassunto organizzato dei dati che hai capito e chiedi conferma.
        Sii preciso e organizzato nel presentare le informazioni.
        """

        prompt = f"""
        Grazie per la panoramica! Ho estratto queste informazioni dal tuo racconto:

        {summary}

        Ho capito bene questi dati? Se c'è qualcosa da correggere o aggiungere, dimmelo pure.
        Dopo la conferma, ti chiederò le informazioni mancanti per completare il profilo.
        """

        response, _ = self.generate_response(prompt, system_prompt)
        print(f"\nAssistente: {response}")

        # Passa allo stato di conferma
        self.conversation_state = "confirm_data"
        self.current_question = "data_confirmation"

    def handle_data_confirmation(self, user_input):
        """Gestisce la conferma dei dati estratti"""
        user_input_lower = user_input.lower()

        if any(word in user_input_lower for word in ["sì", "si", "corretto", "giusto", "ok", "bene", "esatto"]):
            # Dati confermati, procedi con la raccolta di dati mancanti
            if self.missing_data:
                self.conversation_state = "collect_missing_data"
                self.current_question = self.missing_data[0]  # Inizia dal primo dato mancante
                self.ask_for_missing_data(self.missing_data[0])
            else:
                # Tutti i dati essenziali sono presenti, passa al motivo della visita
                self.conversation_state = "collect_purpose"
                self.current_question = "main_purpose"
                self.ask_for_purpose()

        elif any(word in user_input_lower for word in ["no", "sbagliato", "errore", "correggere"]):
            # Chiedi correzioni
            system_prompt = """
            Il paziente vuole correggere alcuni dati. Chiedi specificatamente cosa deve essere corretto
            e sii pronto a ricevere le correzioni.
            """

            prompt = """
            Nessun problema! Dimmi cosa devo correggere. Puoi specificare esattamente quali 
            informazioni sono sbagliate e fornirmi quelle corrette.
            """

            response, _ = self.generate_response(prompt, system_prompt)
            print(f"\nAssistente: {response}")

            # Rimani nello stesso stato per ricevere le correzioni

        else:
            # Input ambiguo, chiedi chiarimenti
            system_prompt = "Chiedi chiarimenti su cosa vuole fare il paziente riguardo ai dati mostrati."
            prompt = "Non ho capito bene. I dati che ho estratto sono corretti o c'è qualcosa da modificare?"

            response, _ = self.generate_response(prompt, system_prompt)
            print(f"\nAssistente: {response}")

    def handle_missing_data_collection(self, user_input):
        """Gestisce la raccolta dei dati mancanti"""
        current_missing = self.current_question

        # Processa il dato corrente
        if current_missing == "name":
            self.patient.set_name(user_input.strip())
        elif current_missing == "surname":
            self.patient.set_surname(user_input.strip())
        elif current_missing == "age":
            try:
                self.patient.set_age(int(user_input.strip()))
            except:
                self.ask_for_missing_data("age", "Per favore inserisci un'età valida (numero).")
                return
        elif current_missing == "sex":
            if user_input.upper() in ["M", "F", "MASCHIO", "FEMMINA", "UOMO", "DONNA"]:
                sex = "M" if user_input.upper() in ["M", "MASCHIO", "UOMO"] else "F"
                self.patient.set_sex(sex)
            else:
                self.ask_for_missing_data("sex", "Per favore specifica 'M' per maschio o 'F' per femmina.")
                return
        elif current_missing == "city":
            self.patient.set_city(user_input.strip())
        elif current_missing == "height":
            try:
                self.patient.set_height(user_input.strip())
            except:
                self.ask_for_missing_data("height", "Per favore inserisci l'altezza in centimetri (es. 175).")
                return
        elif current_missing == "weight":
            try:
                self.patient.set_weight(user_input.strip())
            except:
                self.ask_for_missing_data("weight", "Per favore inserisci il peso in kg (es. 70).")
                return
        elif current_missing == "phone":
            self.patient.set_contact_info(phone=user_input.strip())
        elif current_missing == "allergies":
            self.patient.set_allergies(user_input.strip())

        # Rimuovi il dato appena raccolto dalla lista
        self.missing_data.remove(current_missing)

        # Procedi al prossimo dato mancante o al motivo della visita
        if self.missing_data:
            self.current_question = self.missing_data[0]
            self.ask_for_missing_data(self.missing_data[0])
        else:
            # Tutti i dati raccolti, passa al motivo della visita
            self.conversation_state = "collect_purpose"
            self.current_question = "main_purpose"
            self.ask_for_purpose()

    def ask_for_missing_data(self, data_type, error_message=None):
        """Chiede un dato specifico mancante"""
        system_prompt = "Chiedi al paziente il dato mancante in modo naturale e amichevole."

        prompts = {
            "name": "Come ti chiami? (nome)",
            "surname": "Qual è il tuo cognome?",
            "age": "Quanti anni hai?",
            "sex": "Sei maschio o femmina? (M/F)",
            "city": "In che città vivi?",
            "height": "Qual è la tua altezza in centimetri?",
            "weight": "Quanto pesi in kg?",
            "phone": "Potresti fornirmi un numero di telefono per contattarti?",
            "allergies": "Hai allergie particolari? (scrivi 'nessuna' se non ne hai)"
        }

        if error_message:
            prompt = f"{error_message} {prompts.get(data_type, 'Fornisci questa informazione:')}"
        else:
            prompt = prompts.get(data_type, "Fornisci questa informazione:")

        response, _ = self.generate_response(prompt, system_prompt)
        print(f"\nAssistente: {response}")

    def ask_for_purpose(self):
        """Chiede il motivo della visita"""
        system_prompt = """
        Ora che hai tutte le informazioni di base del paziente, chiedi il motivo della visita medica.
        Sii empatico e incoraggia il paziente a fornire dettagli.
        """

        name = self.patient.get_name() if self.patient and self.patient.get_name() else "utente"

        prompt = f"""
        Perfetto {name}! Ora ho tutte le informazioni di base per il tuo profilo.

        Potresti dirmi qual è il motivo per cui desideri una visita medica? 
        Descrivi pure il problema o i sintomi che ti preoccupano, anche nei dettagli.
        """

        response, _ = self.generate_response(prompt, system_prompt)
        print(f"\nAssistente: {response}")

    def handle_purpose_info(self, user_input):
        """Gestisce la raccolta delle informazioni sul motivo della visita"""
        system_prompt = """
        Sei Longi di Longeviva. Il paziente ti ha spiegato il motivo della visita.
        Mostra empatia e comprensione, poi procedi all'analisi per trovare lo specialista più adatto.
        """

        # Salva il motivo della visita
        self.patient.set_purpose(user_input)

        name = self.patient.get_name() if self.patient and self.patient.get_name() else "utente"

        prompt = f"""
        Capisco, {name}. Grazie per aver condiviso questi dettagli importanti.

        Il tuo problema: "{user_input}"

        Ora analizzerò le tue informazioni per trovare lo specialista più adatto a te, 
        considerando sia la tua posizione geografica che le tue esigenze specifiche.

        Un momento mentre elaboro...
        """

        response, _ = self.generate_response(prompt, system_prompt)
        print(f"\nAssistente: {response}")

        # Passa alla raccomandazione del medico
        self.conversation_state = "recommend_doctor"
        self.current_question = "show_recommendation"

        # Procedi immediatamente con la raccomandazione
        self.process_doctor_recommendation()

    def extract_data_from_text(self, text):
        """Estrae dati strutturati dal testo libero dell'utente - VERSIONE MIGLIORATA"""
        extracted = {}
        text_lower = text.lower()

        print(f"DEBUG: Analizzando testo: '{text}'")

        # Estrazione nome - Pattern più flessibili
        name_patterns = [
            r"mi chiamo (\w+)",
            r"sono (\w+)",
            r"il mio nome è (\w+)",
            r"nome (\w+)",
            r"^(\w+),",  # Nome all'inizio seguito da virgola
            r"ciao,?\s+(\w+)",  # "Ciao Francesco" o "Ciao, Francesco"
        ]
        for pattern in name_patterns:
            match = re.search(pattern, text_lower)
            if match:
                extracted["name"] = match.group(1).title()
                break

        # Estrazione età - Pattern migliorati
        age_patterns = [
            r"ho (\d+) anni",
            r"(\d+) anni",
            r"età (\d+)",
            r"sono (\w+) di (\d+) anni",  # Cattura anche il secondo gruppo
        ]
        for pattern in age_patterns:
            match = re.search(pattern, text_lower)
            if match:
                # Prendi l'ultimo gruppo che contiene un numero
                groups = match.groups()
                for group in groups:
                    if group and group.isdigit():
                        extracted["age"] = int(group)
                        break
                if "age" in extracted:
                    break

        # Estrazione città - Pattern migliorati
        city_patterns = [
            r"vivo a (\w+)",
            r"abito a (\w+)",
            r"di (\w+)",
            r"sono di (\w+)",
            r"da (\w+)",
            r"a (\w+)",  # Generico "a Milano"
            r"città (\w+)",
            r"(?:vivo|abito|sono|sto)\s+(?:a|da|di|in)\s+(\w+)",
        ]
        for pattern in city_patterns:
            match = re.search(pattern, text_lower)
            if match:
                city_candidate = match.group(1).title()
                # Lista di città italiane comuni per validazione
                italian_cities = [
                    "Roma", "Milano", "Napoli", "Torino", "Palermo", "Genova",
                    "Bologna", "Firenze", "Bari", "Catania", "Venezia", "Verona",
                    "Messina", "Padova", "Trieste", "Brescia", "Parma", "Modena",
                    "Reggio", "Perugia", "Livorno", "Cagliari", "Foggia", "Rimini"
                ]
                if city_candidate in italian_cities:
                    extracted["city"] = city_candidate
                    break

        # Estrazione genere
        if any(word in text_lower for word in ["sono un uomo", "maschio", "sono maschio", "uomo"]):
            extracted["sex"] = "M"
        elif any(word in text_lower for word in ["sono una donna", "femmina", "sono femmina", "donna"]):
            extracted["sex"] = "F"

        # Estrazione altezza - Pattern migliorati
        height_patterns = [
            r"alto (\d+\.?\d*)\s*(?:cm|centimetri|metri)?",
            r"alta (\d+\.?\d*)\s*(?:cm|centimetri|metri)?",
            r"(\d+\.?\d*)\s*(?:cm|centimetri)",
            r"altezza (\d+\.?\d*)",
            r"(?:sono|misuro)\s+(\d+\.?\d*)\s*(?:cm|centimetri)?"
        ]
        for pattern in height_patterns:
            match = re.search(pattern, text_lower)
            if match:
                height_val = float(match.group(1))
                # Se è in metri (es. 1.86), converti in cm
                if height_val < 3:
                    height_val *= 100
                extracted["height"] = height_val
                break

        # Estrazione peso
        weight_patterns = [
            r"peso (\d+\.?\d*)\s*(?:kg|chili|chilogrammi)?",
            r"(\d+\.?\d*)\s*(?:kg|chili|chilogrammi)",
            r"peso (\d+\.?\d*)"
        ]
        for pattern in weight_patterns:
            match = re.search(pattern, text_lower)
            if match:
                extracted["weight"] = float(match.group(1))
                break

        # Estrazione telefono
        phone_patterns = [
            r"(\+?39\s?\d{3}\s?\d{6,7})",
            r"(\d{10})",
            r"telefono (\+?39\s?\d{3}\s?\d{6,7})",
            r"(\d{3}\s?\d{3}\s?\d{4})"
        ]
        for pattern in phone_patterns:
            match = re.search(pattern, text)
            if match:
                extracted["phone"] = match.group(1)
                break

        # Estrazione allergie
        allergy_patterns = [
            r"allergico (?:a|al|alla|ai|alle) ([\w\s,]+)",
            r"allergica (?:a|al|alla|ai|alle) ([\w\s,]+)",
            r"allergie? (?:a|al|alla|ai|alle) ([\w\s,]+)",
            r"non posso prendere ([\w\s,]+)",
            r"allergie ([\w\s,]+)"
        ]
        for pattern in allergy_patterns:
            match = re.search(pattern, text_lower)
            if match:
                extracted["allergies"] = match.group(1).strip()
                break

        # Se non trova allergie specifiche ma menziona "nessuna allergia"
        if any(phrase in text_lower for phrase in ["nessuna allergia", "non ho allergie", "senza allergie"]):
            extracted["allergies"] = "Nessuna"

        # NUOVO: Estrazione problemi di salute/sintomi
        health_issues = []

        # Pattern per problemi di salute
        health_patterns = [
            r"(?:problemi?|disturbi?|difficoltà)\s+(?:con|di|della?|del)\s+([\w\s]+)",
            r"(?:mal di|dolore|dolori)\s+([\w\s]+)",
            r"(?:ho|soffro di|problemi di)\s+([\w\s]+)",
            r"(?:sintomi?|segni?)\s+(?:di|come)\s+([\w\s]+)",
            r"(?:sento|provo|avverto)\s+([\w\s]+)"
        ]

        for pattern in health_patterns:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                issue = match.group(1).strip()
                if len(issue) > 2 and issue not in health_issues:
                    health_issues.append(issue)

        # Pattern specifici per sintomi comuni
        specific_symptoms = {
            r"mal di testa|emicrania|cefalea": "mal di testa",
            r"dolori? articolari?": "dolori articolari",
            r"problemi? (?:di )?alimentazione": "problemi alimentazione",
            r"difficoltà a dormire|insonnia|non riesco a dormire": "disturbi del sonno",
            r"dolori? al petto": "dolori al petto",
            r"problemi? cardiaci?": "problemi cardiaci",
            r"problemi? di pelle": "problemi dermatologici",
            r"ansia|stress|depressione": "problemi psicologici"
        }

        for pattern, symptom in specific_symptoms.items():
            if re.search(pattern, text_lower):
                health_issues.append(symptom)

        if health_issues:
            extracted["health_issues"] = health_issues
            # Il primo problema diventa il purpose principale
            extracted["purpose"] = health_issues[0]

        print(f"DEBUG: Dati estratti migliorati: {extracted}")
        return extracted

    def populate_patient_from_extracted_data(self):
        """Popola l'oggetto paziente con i dati estratti"""
        # Assicurati che patient esista
        if self.patient is None:
            self.patient = Patient()

        if "name" in self.extracted_data:
            self.patient.set_name(self.extracted_data["name"])

        if "age" in self.extracted_data:
            self.patient.set_age(self.extracted_data["age"])

        if "city" in self.extracted_data:
            self.patient.set_city(self.extracted_data["city"])

        if "sex" in self.extracted_data:
            self.patient.set_sex(self.extracted_data["sex"])

        if "height" in self.extracted_data:
            self.patient.set_height(self.extracted_data["height"])

        if "weight" in self.extracted_data:
            self.patient.set_weight(self.extracted_data["weight"])

        if "phone" in self.extracted_data:
            self.patient.set_contact_info(phone=self.extracted_data["phone"])

        if "allergies" in self.extracted_data:
            self.patient.set_allergies(self.extracted_data["allergies"])

    def identify_missing_essential_data(self):
        """Identifica quali dati essenziali mancano"""
        essential_fields = ["name", "age", "sex", "city", "phone"]
        missing = []

        # Assicurati che patient esista
        if self.patient is None:
            self.patient = Patient()

        if not self.patient.get_name():
            missing.append("name")

        if not self.patient.get_age():
            missing.append("age")

        if not self.patient.get_sex():
            missing.append("sex")

        if not self.patient.get_city():
            missing.append("city")

        if not self.patient.get_contact_info().get("phone"):
            missing.append("phone")

        # Dati opzionali ma utili
        if not self.patient.get_height():
            missing.append("height")

        if not self.patient.get_weight():
            missing.append("weight")

        if not self.patient.get_allergies():
            missing.append("allergies")

        return missing

    def generate_data_summary(self):
        """Genera un riassunto organizzato dei dati estratti"""
        summary_parts = []

        # Assicurati che patient esista
        if self.patient is None:
            self.patient = Patient()

        # Dati anagrafici
        if self.patient.get_name():
            summary_parts.append(f"📋 Nome: {self.patient.get_name()}")

        if self.patient.get_age():
            summary_parts.append(f"🎂 Età: {self.patient.get_age()} anni")

        if self.patient.get_sex():
            sex_text = "Maschio" if self.patient.get_sex() == "M" else "Femmina"
            summary_parts.append(f"👤 Sesso: {sex_text}")

        if self.patient.get_city():
            summary_parts.append(f"🏙️ Città: {self.patient.get_city()}")

        # Dati fisici
        physical_data = []
        if self.patient.get_height():
            physical_data.append(f"Altezza: {self.patient.get_height()} cm")

        if self.patient.get_weight():
            physical_data.append(f"Peso: {self.patient.get_weight()} kg")

        if physical_data:
            summary_parts.append(f"📏 {', '.join(physical_data)}")

        # Contatti
        if self.patient.get_contact_info().get("phone"):
            summary_parts.append(f"📞 Telefono: {self.patient.get_contact_info()['phone']}")

        # Allergie
        if self.patient.get_allergies():
            summary_parts.append(f"⚠️ Allergie: {self.patient.get_allergies()}")

        if not summary_parts:
            return "Non sono riuscito a estrarre informazioni specifiche dalla tua descrizione."

        return "\n".join(summary_parts)

    def process_doctor_recommendation(self):
        """Elabora la raccomandazione del medico (sarà implementato in llm_assistant)"""
        # Questo metodo sarà sovrascritto da llm_assistant
        system_prompt = "Simula la raccomandazione di un medico in base ai sintomi descritti."

        # Assicurati che patient esista
        if self.patient is None:
            self.patient = Patient()

        name = self.patient.get_name() or "utente"
        purpose = self.patient.get_purpose() or "problemi generali di salute"

        prompt = f"""
        Ecco la mia raccomandazione per te, {name}.

        In base al tuo problema: "{purpose}", ti consiglio di consultare un medico specializzato in Medicina Generale.

        Il Dr. Mario Rossi è disponibile nella tua zona e ha esperienza nel trattare casi simili.
        Ha 15 anni di esperienza e ottime recensioni dai pazienti.

        Vuoi che proceda con la prenotazione di un appuntamento?
        """

        response, _ = self.generate_response(prompt, system_prompt)
        print(f"\nAssistente: {response}")

        # Crea un medico fittizio
        from src.Doctor.doctor_instance import Doctor
        self.recommended_doctor = Doctor(
            name="Mario",
            surname="Rossi",
            specialization="Medicina Generale",
            experience_years=15
        )

        # Passa allo stato successivo
        self.conversation_state = "schedule_appointment"
        self.current_question = "wants_appointment"

    def handle_doctor_recommendation(self, user_input):
        """Gestisce la risposta dell'utente alla raccomandazione del medico"""
        # Versione base
        if any(word in user_input.lower() for word in ["sì", "si", "ok", "bene", "procedi", "prenota"]):
            system_prompt = "Il paziente vuole prenotare un appuntamento. Conferma e procedi."

            # Assicurati che patient esista
            if self.patient is None:
                self.patient = Patient()

            name = self.patient.get_name() or "utente"

            prompt = f"""
            Ottimo {name}! Ti aiuterò a prenotare un appuntamento con il Dott. {self.recommended_doctor.get_surname()}.
            Prima però, avrei bisogno di alcune informazioni per ottimizzare la tua esperienza.
            """

            response, _ = self.generate_response(prompt, system_prompt)
            print(f"\nAssistente: {response}")

            self.conversation_state = "schedule_appointment"
            self.current_question = "appointment_details"
        else:
            system_prompt = "Il paziente non sembra interessato a prenotare subito. Offri alternative."

            # Assicurati che patient esista
            if self.patient is None:
                self.patient = Patient()

            name = self.patient.get_name() or "utente"

            prompt = f"""
            Capisco {name}. Se preferisci pensarci, puoi sempre contattarci più tardi per prenotare.
            Posso aiutarti con qualcos'altro? O magari preferisci avere maggiori informazioni sul dottore?
            """

            response, _ = self.generate_response(prompt, system_prompt)
            print(f"\nAssistente: {response}")

            self.conversation_state = "closing"
            self.current_question = "anything_else"

    def handle_appointment_scheduling(self, user_input):
        """Gestisce la pianificazione dell'appuntamento"""
        # Versione base del metodo
        system_prompt = "Simula la prenotazione di un appuntamento."

        # Assicurati che patient esista
        if self.patient is None:
            self.patient = Patient()

        name = self.patient.get_name() or "utente"
        email = self.patient.get_contact_info().get('email') or "la tua email"

        prompt = f"""
        Perfetto {name}! Ho prenotato un appuntamento per te con il Dott. {self.recommended_doctor.get_surname()} 
        per il prossimo lunedì alle 15:00.

        Riceverai una conferma via email a {email}.
        C'è altro in cui posso aiutarti?
        """

        response, _ = self.generate_response(prompt, system_prompt)
        print(f"\nAssistente: {response}")

        self.conversation_state = "closing"
        self.current_question = "anything_else"

    def handle_closing(self, user_input):
        """Gestisce la chiusura della conversazione"""
        system_prompt = "Concludi la conversazione in modo cordiale e professionale."

        if self.current_question == "anything_else":
            if any(word in user_input.lower() for word in ["sì", "si", "certo", "ok"]):
                prompt = "Come posso aiutarti ancora?"
                self.current_question = "final_request"
            else:
                prompt = """
                Grazie per aver utilizzato i servizi di Longeviva! È stato un piacere assisterti.
                Se hai bisogno di ulteriore aiuto in futuro, non esitare a contattarci nuovamente.
                Ti auguro una buona giornata e una pronta guarigione!
                """
                self.current_question = "end"
        else:
            prompt = "C'è altro in cui posso esserti utile?"
            self.current_question = "anything_else"

        response, _ = self.generate_response(prompt, system_prompt)
        print(f"\nAssistente: {response}")

    def handle_exit(self):
        """Gestisce l'uscita dall'applicazione"""
        system_prompt = "Saluta cordialmente il paziente."
        prompt = "Grazie per aver utilizzato Longeviva. Arrivederci e prenditi cura di te!"

        response, _ = self.generate_response(prompt, system_prompt)
        print(f"\nAssistente: {response}")

    def format_date(self, date_str):
        """Formatta una data in formato leggibile"""
        try:
            import datetime
            date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()

            weekdays = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
            weekday = weekdays[date_obj.weekday()]

            months = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
                      "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
            month = months[date_obj.month - 1]

            return f"{weekday} {date_obj.day} {month} {date_obj.year}"
        except:
            return date_str

    # Metodi per l'autenticazione
    def handle_authentication(self, user_input):
        """Gestisce il processo di autenticazione/identificazione iniziale"""
        print(f"🔍 DEBUG: Funzione handle_authentication chiamata con input: '{user_input}'")

        # Assicurati che patient esista
        if self.patient is None:
            self.patient = Patient()

        # Estrai nome e cognome dall'input
        name = None
        surname = None

        # Cerca pattern "Nome Cognome"
        name_pattern = r"([A-Za-zÀ-ÿ]+)(?:\s+)([A-Za-zÀ-ÿ]+)"
        match = re.search(name_pattern, user_input)
        if match:
            name = match.group(1)
            surname = match.group(2)
            print(f"✅ DEBUG: Estratto nome '{name}' e cognome '{surname}' con regex")
        else:
            # Tenta un approccio semplice
            words = user_input.strip().split()
            if len(words) >= 2:
                name = words[0]
                surname = ' '.join(words[1:])  # Prende tutto il resto come cognome
                print(f"✅ DEBUG: Estratto nome '{name}' e cognome '{surname}' con split")

        if not name or not surname:
            # Non è stato possibile estrarre sia nome che cognome
            system_prompt = "Chiedi nuovamente nome e cognome in modo chiaro."
            prompt = "Mi serve sia il nome che il cognome insieme. Puoi fornirmeli entrambi in un unico messaggio? (es. 'Mario Rossi')"

            response, _ = self.generate_response(prompt, system_prompt)
            print(f"\nAssistente: {response}")
            return

        # A questo punto abbiamo estratto nome e cognome
        print(f"Nome estratto: {name}, Cognome estratto: {surname}")

        # Assegna nome e cognome al paziente
        self.patient.set_name(name)
        self.patient.set_surname(surname)

        # Cerca il paziente nel database (funzione che verrà sovrascritta da LLMAssistant)
        # Qui simuliamo solo che il paziente non è stato trovato

        # Passa alla raccolta dello scopo
        self.conversation_state = "collect_purpose"
        self.current_question = "main_purpose"

        # Chiedi il motivo della visita
        system_prompt = "Il paziente ha fornito il suo nome. Chiedi il motivo della visita."
        prompt = f"""
        Grazie {name}! Ora, come posso aiutarti oggi? 
        Qual è il motivo per cui desideri consultare un medico?
        """

        response, _ = self.generate_response(prompt, system_prompt)
        print(f"\nAssistente: {response}")

    def handle_identity_confirmation(self, user_input):
        """Gestisce la conferma dell'identità del paziente"""
        # Assicurati che patient esista
        if self.patient is None:
            self.patient = Patient()

        if any(word in user_input.lower() for word in ["sì", "si", "confermo", "esatto"]):
            # Identità confermata
            system_prompt = "L'utente ha confermato la sua identità. Chiedi lo scopo della visita."
            name = self.patient.get_name() or "utente"

            prompt = f"""
            Perfetto, {name}! Come posso aiutarti oggi?
            Qual è il motivo per cui desideri consultare un medico?
            """

            response, _ = self.generate_response(prompt, system_prompt)
            print(f"\nAssistente: {response}")

            self.conversation_state = "collect_purpose"
            self.current_question = "main_purpose"
        else:
            # Identità non confermata
            system_prompt = "L'utente non ha confermato l'identità. Chiedi nuovamente il nome."
            prompt = """
            Mi scuso per la confusione. Potresti fornirmi di nuovo il tuo nome completo?
            """

            response, _ = self.generate_response(prompt, system_prompt)
            print(f"\nAssistente: {response}")

            self.conversation_state = "authentication"
            self.current_question = "name_surname"

    def handle_registration(self, user_input):
        """Gestisce il processo di registrazione"""
        # Assicurati che patient esista
        if self.patient is None:
            self.patient = Patient()

        if self.current_question == "wants_registration":
            if any(word in user_input.lower() for word in ["sì", "si", "certo", "voglio"]):
                # Vuole registrarsi
                system_prompt = "L'utente vuole registrarsi. Chiedi i dati essenziali."
                name = self.patient.get_name() or "utente"

                prompt = f"""
                Ottimo {name}! Per registrarti, ho bisogno di alcune informazioni:

                1. La tua età
                2. Sesso (M/F)
                3. Città di residenza
                4. Email o telefono
                5. Eventuali allergie

                Puoi fornirmi queste informazioni?
                """

                response, _ = self.generate_response(prompt, system_prompt)
                print(f"\nAssistente: {response}")

                self.current_question = "registration_data"
            else:
                # Non vuole registrarsi
                system_prompt = "L'utente non vuole registrarsi. Procedi comunque."
                name = self.patient.get_name() or "utente"

                prompt = f"""
                Nessun problema, {name}! Possiamo comunque procedere.

                Come posso aiutarti oggi? Qual è il motivo della tua visita?
                """

                response, _ = self.generate_response(prompt, system_prompt)
                print(f"\nAssistente: {response}")

                self.conversation_state = "collect_purpose"
                self.current_question = "main_purpose"
        elif self.current_question == "registration_data":
            # Estrai i dati dalla risposta dell'utente e compilali
            # Qui implementiamo una semplice estrazione
            text = user_input.lower()

            # Età
            age_match = re.search(r"(\d+)\s*anni", text)
            if age_match:
                self.patient.set_age(int(age_match.group(1)))

            # Sesso
            if "maschio" in text or "uomo" in text or " m " in text:
                self.patient.set_sex("M")
            elif "femmina" in text or "donna" in text or " f " in text:
                self.patient.set_sex("F")

            # Città
            city_patterns = [r"vivo a (\w+)", r"abito a (\w+)", r"città (\w+)"]
            for pattern in city_patterns:
                match = re.search(pattern, text)
                if match:
                    self.patient.set_city(match.group(1).title())
                    break

            # Email
            email_match = re.search(r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)", text)
            if email_match:
                self.patient.set_contact_info(email=email_match.group(1))

            # Allergie
            if "nessuna allergia" in text or "non ho allergie" in text:
                self.patient.set_allergies("Nessuna")
            else:
                allergy_match = re.search(r"allergic[oa] (?:a|al|alla|ai|alle) ([\w\s,]+)", text)
                if allergy_match:
                    self.patient.set_allergies(allergy_match.group(1).strip())

            # Cambia stato
            self.conversation_state = "collect_purpose"
            self.current_question = "main_purpose"

            # Conferma la registrazione
            system_prompt = "Conferma la registrazione. Chiedi il motivo della visita."
            name = self.patient.get_name() or "utente"

            prompt = f"""
            Grazie {name}! Ho salvato le tue informazioni.

            Ora, come posso aiutarti oggi? Qual è il motivo della tua visita?
            """

            response, _ = self.generate_response(prompt, system_prompt)
            print(f"\nAssistente: {response}")
        else:
            # Fallback
            self.conversation_state = "collect_purpose"
            self.current_question = "main_purpose"
            self.ask_for_purpose()