# src/utils/registration_handler.py - AGGIORNATO CON CALCOLO ETÀ
import re
from datetime import datetime
import json
import sys
import os

# Aggiungi il path per importare dalle directory parent
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from Patient.patients_handler import PatientHandler


def calculate_age_from_birthdate(birth_date_str):
    """
    Calcola l'età dalla data di nascita in formato DD/MM/YYYY
    """
    try:
        # Parse della data di nascita
        day, month, year = birth_date_str.split('/')
        birth_date = datetime(int(year), int(month), int(day))

        # Calcola l'età
        today = datetime.now()
        age = today.year - birth_date.year

        # Verifica se il compleanno è già passato quest'anno
        if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
            age -= 1

        return age
    except Exception as e:
        print(f"⚠️ Errore nel calcolo dell'età: {e}")
        return None


def calculate_fiscal_code(name, surname, birth_date, sex, birth_city):
    """
    Calcola il codice fiscale italiano
    """
    try:
        # Mappatura mesi
        month_codes = ['A', 'B', 'C', 'D', 'E', 'H', 'L', 'M', 'P', 'R', 'S', 'T']

        # Tabella città comuni (versione semplificata)
        city_codes = {
            'roma': 'H501', 'milano': 'F205', 'napoli': 'F839', 'torino': 'L219',
            'palermo': 'G273', 'genova': 'D969', 'bologna': 'A944', 'firenze': 'D612',
            'bari': 'A662', 'catania': 'C351', 'venezia': 'L736', 'verona': 'L781',
            'messina': 'F158', 'padova': 'G224', 'trieste': 'L424', 'brescia': 'B157'
        }

        # Estrai componenti
        consonants = 'BCDFGHJKLMNPQRSTVWXYZ'
        vowels = 'AEIOU'

        def extract_consonants_vowels(text):
            text = text.upper().replace(' ', '')
            cons = ''.join([c for c in text if c in consonants])
            vows = ''.join([c for c in text if c in vowels])
            return cons, vows

        # Cognome (3 caratteri)
        surname_cons, surname_vows = extract_consonants_vowels(surname)
        surname_code = (surname_cons + surname_vows + 'XXX')[:3]

        # Nome (3 caratteri)
        name_cons, name_vows = extract_consonants_vowels(name)
        if len(name_cons) >= 4:
            name_code = name_cons[0] + name_cons[2] + name_cons[3]
        else:
            name_code = (name_cons + name_vows + 'XXX')[:3]

        # Data di nascita (formato DD/MM/YYYY)
        day, month, year = birth_date.split('/')
        year_code = year[-2:]
        month_code = month_codes[int(month) - 1]

        # Giorno (per le donne +40)
        day_code = str(int(day) + (40 if sex.upper() == 'F' else 0)).zfill(2)

        # Città
        city_code = city_codes.get(birth_city.lower(), 'Z999')

        # Calcolo check digit (semplificato)
        partial_code = surname_code + name_code + year_code + month_code + day_code + city_code
        check_digit = 'Z'  # Semplificato

        return partial_code + check_digit

    except Exception as e:
        print(f"⚠️ Errore calcolo codice fiscale: {e}")
        return "CALCOLO_NON_RIUSCITO"


class RegistrationHandler:
    """
    Gestisce il processo di registrazione strutturato del paziente
    """

    def __init__(self, patient, patient_db):
        self.patient = patient
        self.patient_db = patient_db
        self.current_step = 0
        self.current_phase = "motivation_questions"
        self.motivation_data = {}
        self.registration_data = {}
        self.preferences_data = {}

        # Contatori per gestire i tentativi falliti
        self.first_data_attempts = 0
        self.second_data_attempts = 0
        self.lifestyle_data_attempts = 0
        self.max_attempts = 2  # Dopo 2 tentativi, passa al formato strutturato

        # Definizione delle domande motivazionali
        self.motivation_questions = [
            {
                "field": "download_reason",
                "question": """Perché hai scaricato Longeviva? Rispondi con i numeri degli oggetti che ti interessano, ad esempio: 1,2,3.

1. Voglio migliorare il mio stile di vita con un supporto pratico e costante.
2. Ho bisogno di un aiuto concreto per rimettermi in forma.
3. Cerco un modo semplice per mangiare meglio e muovermi di più.
4. Mi interessa la longevità e voglio prendermi cura della mia salute oggi.
5. Mi ha incuriosito l'approccio innovativo con l'AI e la community""",
                "type": "multiple_choice",
                "options": [
                    "Voglio migliorare il mio stile di vita con un supporto pratico e costante",
                    "Ho bisogno di un aiuto concreto per rimettermi in forma",
                    "Cerco un modo semplice per mangiare meglio e muovermi di più",
                    "Mi interessa la longevità e voglio prendermi cura della mia salute oggi",
                    "Mi ha incuriosito l'approccio innovativo con l'AI e la community"
                ]
            },
            {
                "field": "objectives",
                "question": """Quali sono i tuoi obiettivi? Rispondi con i numeri degli oggetti che ti interessano, ad esempio: 1,2,3.

1. Perdere peso in modo sano e sostenibile.
2. Avere più energia durante la giornata.
3. Migliorare la mia composizione corporea.
4. Aumentare la mia consapevolezza alimentare.
5. Vivere più a lungo e in salute.
6. Sentirmi meglio fisicamente e mentalmente.""",
                "type": "multiple_choice",
                "options": [
                    "Perdere peso in modo sano e sostenibile",
                    "Avere più energia durante la giornata",
                    "Migliorare la mia composizione corporea",
                    "Aumentare la mia consapevolezza alimentare",
                    "Vivere più a lungo e in salute",
                    "Sentirmi meglio fisicamente e mentalmente"
                ]
            },
            {
                "field": "expectations",
                "question": """Cosa ti aspetti da questo percorso? Rispondi con i numeri degli oggetti che ti interessano, ad esempio: 1,2,3.

1. Un percorso personalizzato e facile da seguire.
2. Consigli pratici, non complicati.
3. Sentirmi seguito/a da chi capisce le mie esigenze.
4. Imparare abitudini che durino nel tempo.
5. Un'esperienza motivante che mi tenga attivo/a e coinvolto/a.""",
                "type": "multiple_choice",
                "options": [
                    "Un percorso personalizzato e facile da seguire",
                    "Consigli pratici, non complicati",
                    "Sentirmi seguito/a da chi capisce le mie esigenze",
                    "Imparare abitudini che durino nel tempo",
                    "Un'esperienza motivante che mi tenga attivo/a e coinvolto/a"
                ]
            }
        ]

        # Domande per le preferenze medico
        self.preference_questions = [
            {
                "field": "vicinanza",
                "question": "Quanto è importante per te la VICINANZA del medico? (1 = poco importante, 5 = molto importante)",
                "type": "rating"
            },
            {
                "field": "specializzazione",
                "question": "Quanto è importante per te la SPECIALIZZAZIONE del medico? (1 = poco importante, 5 = molto importante)",
                "type": "rating"
            },
            {
                "field": "costo",
                "question": "Quanto è importante per te il COSTO della visita? (1 = qualsiasi prezzo, 5 = il miglior prezzo possibile)",
                "type": "rating"
            },
            {
                "field": "area_interesse",
                "question": "Quanto è importante per te l'AREA DI INTERESSE specifica del medico? (1 = poco importante, 5 = molto importante)",
                "type": "rating"
            }
        ]

    def start_registration(self):
        """Inizia il processo di registrazione"""
        self.current_step = 0
        self.current_phase = "motivation_questions"

        welcome_message = """
Ciao! Sono Longi, il tuo assistente personale di Longeviva! 🏥✨

Per offrirti il miglior servizio possibile, vorrei conoscerti meglio attraverso alcune domande.

Iniziamo!
        """

        return welcome_message.strip(), self._get_current_question()

    def process_answer(self, user_input):
        """Processa la risposta dell'utente secondo il nuovo flusso SEMPLIFICATO"""
        if self.current_phase == "motivation_questions":
            return self._process_motivation_answer(user_input)
        elif self.current_phase == "show_summary":
            return self._process_summary_confirmation(user_input)
        elif self.current_phase == "collect_first_data":
            return self._process_first_data_message(user_input)
        elif self.current_phase == "collect_missing_first_data":
            return self._process_missing_first_data(user_input)
        elif self.current_phase == "collect_second_data":
            return self._process_second_data_message(user_input)
        elif self.current_phase == "collect_missing_second_data":
            return self._process_missing_second_data(user_input)
        elif self.current_phase == "preference_questions":
            return self._process_preference_answer(user_input)
        elif self.current_phase == "complete":
            return True, "Registrazione completata!", None
        else:
            return True, "Errore nel flusso di registrazione.", None

    def _process_motivation_answer(self, user_input):
        """Processa le risposte alle domande motivazionali"""
        current_question = self.motivation_questions[self.current_step]
        field = current_question["field"]

        if current_question["type"] == "multiple_choice":
            try:
                numbers = [int(x.strip()) for x in re.findall(r'\d+', user_input)]
                if not numbers:
                    return False, "Per favore inserisci almeno un numero dall'elenco.", current_question["question"]

                options = current_question["options"]
                selected_options = []
                for num in numbers:
                    if 1 <= num <= len(options):
                        selected_options.append(options[num - 1])

                if not selected_options:
                    return False, "I numeri inseriti non sono validi. Riprova.", current_question["question"]

                self.motivation_data[field] = selected_options

            except:
                return False, "Formato non valido. Inserisci i numeri separati da virgola (es: 1,2,3)", \
                    current_question["question"]

        self.current_step += 1

        if self.current_step >= len(self.motivation_questions):
            self.current_phase = "show_summary"
            summary = self._create_motivation_summary()

            summary_message = f"""
Perfetto! Ho capito questo su di te:

{summary}

Ora procediamo con la raccolta dei tuoi dati per completare la registrazione.
Premi invio per continuare.
            """

            return False, summary_message.strip(), None

        return False, "Perfetto!", self._get_current_question()

    def _process_summary_confirmation(self, user_input):
        """Processa la conferma del riassunto e passa alla raccolta dati"""
        self.current_phase = "collect_first_data"

        first_data_message = """
Ora ho bisogno delle tue informazioni anagrafiche e fisiche.

Scrivi un messaggio naturale che includa:
- Il tuo nome e cognome
- La tua data di nascita (DD/MM/YYYY) 
- Se sei maschio o femmina
- La città dove sei nato/a
- La città dove vivi attualmente
- La tua altezza (in cm)
- Il tuo peso (in kg)

Esempio: "Sono Mario Rossi, nato il 15/03/1990, sono maschio, nato a Roma dove vivo tuttora. Sono alto 175 cm e peso 70 kg."

Puoi scrivere in modo naturale come preferisci!
        """

        return False, first_data_message.strip(), None

    def _complete_first_data_collection(self):
        """Completa la raccolta dei primi dati e passa al secondo messaggio COMPLETO"""
        self.registration_data.update(self.partial_first_data)
        self._populate_patient_first_data()

        # ✅ NUOVO: Calcola l'età se abbiamo la data di nascita ma non l'età
        age_calculation_message = ""
        if 'birth_date' in self.partial_first_data and 'age' not in self.partial_first_data:
            calculated_age = calculate_age_from_birthdate(self.partial_first_data['birth_date'])
            if calculated_age:
                self.registration_data['age'] = calculated_age
                self.patient.set_age(calculated_age)
                age_calculation_message = f"\n💡 Ho rilevato la tua data di nascita ({self.partial_first_data['birth_date']}) e ho calcolato automaticamente che hai {calculated_age} anni."
                print(f"✅ Età calcolata automaticamente: {calculated_age} anni")

        if all(k in self.partial_first_data for k in ['name', 'surname', 'birth_date', 'sex', 'birth_city']):
            fiscal_code = calculate_fiscal_code(
                self.partial_first_data['name'],
                self.partial_first_data['surname'],
                self.partial_first_data['birth_date'],
                self.partial_first_data['sex'],
                self.partial_first_data['birth_city']
            )
            self.registration_data['fiscal_code'] = fiscal_code
            self.patient.set_fiscal_code(fiscal_code)

        self.current_phase = "collect_second_data"

        second_data_message = f"""
Perfetto!{age_calculation_message} Ora ho bisogno di tutte le informazioni sul tuo stile di vita e salute.

Dimmi tutto quello che riesci in un messaggio naturale:

**Salute:**
- Se hai allergie (o scrivi "nessuna" se non ne hai)
- Che tipo di dieta segui (mediterranea, vegana, vegetariana, normale, ecc.)
- Il problema di salute o il motivo per cui vuoi consultare un medico

**Stile di vita:**
- Che attività sportiva fai e quanto spesso (es. "palestra 3 volte a settimana", "non faccio sport")
- Con che intensità (leggera, moderata, intensa)
- Quante ore dormi di solito ogni notte
- Quanto spesso bevi alcolici (mai, raramente, occasionalmente, regolarmente)
- Fumi? (mai, occasionalmente, regolarmente, ex fumatore)

Puoi scrivere tutto insieme in modo naturale come preferisci!
        """

        return False, second_data_message.strip(), None

    def _process_second_data_message(self, user_input):
        """Processa il secondo messaggio con TUTTI i dati lifestyle e salute"""
        # Estrai sia i dati del secondo messaggio che quelli lifestyle
        extracted_second = self._extract_second_data(user_input)
        extracted_lifestyle = self._extract_lifestyle_data(user_input)

        # Unisci tutti i dati estratti
        extracted_data = {**extracted_second, **extracted_lifestyle}

        # Controlla cosa manca da ENTRAMBI i set di dati
        missing_second = self._check_missing_second_data(extracted_second)
        missing_lifestyle = self._check_missing_lifestyle_data(extracted_lifestyle)
        missing_data = missing_second + missing_lifestyle

        if missing_data:
            self.current_phase = "collect_missing_second_data"
            self.missing_second_fields = missing_data  # Ora contiene tutto
            self.partial_second_data = extracted_data

            missing_message = f"""
Grazie! Mi mancano ancora alcune informazioni:

{self._format_missing_combined_data(missing_data)}

Puoi fornirmele?
            """

            return False, missing_message.strip(), None
        else:
            # Tutti i dati raccolti, vai direttamente alle preferenze
            self.registration_data.update(extracted_data)
            self._populate_patient_all_lifestyle_data()

            self.current_phase = "preference_questions"
            self.current_step = 0

            pref_intro = """
Perfetto! Ora, per trovare il medico più adatto a te, vorrei capire le tue preferenze.

Ti farò alcune domande su cosa è importante per te nella scelta del medico.
            """

            return False, pref_intro.strip(), self._get_current_question()

    def _process_missing_second_data(self, user_input):
        """Processa i dati mancanti del secondo messaggio - VERSIONE UNIFICATA"""
        self.second_data_attempts += 1

        # Dopo 2 tentativi, passa al formato strutturato
        if self.second_data_attempts > self.max_attempts:
            return self._handle_structured_input_combined_data(user_input)

        # Prova estrazione normale di ENTRAMBI i tipi
        additional_second = self._extract_second_data(user_input)
        additional_lifestyle = self._extract_lifestyle_data(user_input)
        additional_data = {**additional_second, **additional_lifestyle}

        self.partial_second_data.update(additional_data)

        # Ricontrolla cosa manca
        missing_second = self._check_missing_second_data(self.partial_second_data)
        missing_lifestyle = self._check_missing_lifestyle_data(self.partial_second_data)
        missing_data = missing_second + missing_lifestyle

        if missing_data:
            self.missing_second_fields = missing_data

            # Se è il secondo tentativo, avvisa
            if self.second_data_attempts == self.max_attempts:
                missing_message = f"""
Mi mancano ancora questi dati:

{self._format_missing_combined_data(missing_data)}

⚠️ Se ho difficoltà a capire la prossima volta, ti chiederò di usare un formato più semplice.
Per favore, prova ancora a fornirmeli.
                """
            else:
                missing_message = f"""
Mi mancano ancora questi dati:

{self._format_missing_combined_data(missing_data)}

Per favore forniscimeli.
                """
            return False, missing_message.strip(), None
        else:
            # Tutti i dati raccolti
            self.registration_data.update(self.partial_second_data)
            self._populate_patient_all_lifestyle_data()

            self.current_phase = "preference_questions"
            self.current_step = 0

            pref_intro = """
Perfetto! Ora, per trovare il medico più adatto a te, vorrei capire le tue preferenze.

Ti farò alcune domande su cosa è importante per te nella scelta del medico.
            """

            return False, pref_intro.strip(), self._get_current_question()

    def _handle_structured_input_combined_data(self, user_input):
        """Gestisce input strutturato per TUTTI i dati del secondo messaggio"""
        print(f"🔧 DEBUG: Passaggio a formato strutturato per: {self.missing_second_fields}")

        # Prova a parsare input strutturato con virgole per TUTTI i tipi
        parsed_second = self._parse_comma_separated_second_input(user_input, self.missing_second_fields)
        parsed_lifestyle = self._parse_comma_separated_lifestyle_input(user_input, self.missing_second_fields)
        parsed_data = {**parsed_second, **parsed_lifestyle}

        if parsed_data:
            self.partial_second_data.update(parsed_data)

            missing_second = self._check_missing_second_data(self.partial_second_data)
            missing_lifestyle = self._check_missing_lifestyle_data(self.partial_second_data)
            missing_data = missing_second + missing_lifestyle

            if not missing_data:
                self.registration_data.update(self.partial_second_data)
                self._populate_patient_all_lifestyle_data()

                self.current_phase = "preference_questions"
                self.current_step = 0

                pref_intro = """
Perfetto! Ora, per trovare il medico più adatto a te, vorrei capire le tue preferenze.

Ti farò alcune domande su cosa è importante per te nella scelta del medico.
                """

                return False, pref_intro.strip(), self._get_current_question()

        # Se ancora mancano dati, chiedi formato strutturato
        examples = []

        # Ordine per i dati combinati
        combined_order = ['allergies', 'diet', 'purpose', 'physical_activity_frequency', 'physical_activity_intensity',
                          'sleep_hours', 'alcohol_frequency', 'smoking_frequency']

        for field in combined_order:
            if field in self.missing_second_fields:
                if field == 'allergies':
                    examples.append('nessuna')
                elif field == 'diet':
                    examples.append('mediterranea')
                elif field == 'purpose':
                    examples.append('mal di testa')
                elif field == 'physical_activity_frequency':
                    examples.append('mai')
                elif field == 'physical_activity_intensity':
                    examples.append('leggera')
                elif field == 'sleep_hours':
                    examples.append('7')
                elif field == 'alcohol_frequency':
                    examples.append('mai')
                elif field == 'smoking_frequency':
                    examples.append('mai')

        structured_message = f"""
Mi scuso, non riesco ancora a capire perfettamente! 😅

Scrivi semplicemente i dati mancanti separati da virgole:

{', '.join(examples)}

Esempio: {', '.join(examples[:len(self.missing_second_fields)])}
        """

        return False, structured_message.strip(), None

    def _format_missing_combined_data(self, missing_fields):
        """Formatta l'elenco dei dati mancanti combinati"""
        field_names = {
            'allergies': 'Allergie',
            'diet': 'Tipo di dieta',
            'purpose': 'Motivo della consultazione medica',
            'physical_activity_frequency': 'Frequenza attività fisica (es. "3 volte a settimana", "mai")',
            'physical_activity_intensity': 'Intensità attività fisica (leggera, moderata, intensa)',
            'sleep_hours': 'Ore di sonno per notte (es. "7 ore")',
            'alcohol_frequency': 'Frequenza consumo alcol (mai, raramente, occasionalmente, regolarmente)',
            'smoking_frequency': 'Abitudine al fumo (mai, occasionalmente, regolarmente, ex fumatore)'
        }

        return '\n'.join([f"• {field_names.get(field, field)}" for field in missing_fields])

    def _populate_patient_all_lifestyle_data(self):
        """Popola TUTTI i dati lifestyle e salute nel paziente"""
        data = self.registration_data

        # Popola allergie e purpose
        if 'allergies' in data:
            self.patient.set_allergies(data['allergies'])
        if 'purpose' in data:
            self.patient.set_purpose(data['purpose'])

        # Recupera il lifestyle esistente o crea nuovo
        existing_lifestyle = self.patient.get_lifestyle() or {}

        # Mappa TUTTI i campi lifestyle
        lifestyle_mapping = {
            'diet': 'typeOfDiet',
            'physical_activity_frequency': 'physicalActivityFrequency',
            'physical_activity_intensity': 'physicalActivityIntensity',
            'sleep_hours': 'hoursOfSleep',
            'alcohol_frequency': 'alcoholFrequency',
            'smoking_frequency': 'smokerFrequency'
        }

        # Aggiorna lifestyle con TUTTI i nuovi dati
        for extracted_field, model_field in lifestyle_mapping.items():
            if extracted_field in data:
                existing_lifestyle[model_field] = data[extracted_field]

        # Imposta lifestyle completo
        self.patient.set_lifestyle(existing_lifestyle)
        print(f"🔍 DEBUG: Lifestyle completo impostato: {existing_lifestyle}")

    def _process_first_data_message(self, user_input):
        """Processa il primo messaggio con dati anagrafici - VERSIONE SICURA"""
        try:
            extracted_data = self._extract_first_data(user_input)
            missing_data = self._check_missing_first_data(extracted_data)

            if missing_data:
                self.current_phase = "collect_missing_first_data"
                self.missing_fields = missing_data
                self.partial_first_data = extracted_data

                # ✅ NUOVO: Controlla se abbiamo calcolato l'età e informa l'utente
                age_info_message = ""
                if extracted_data.get('age_calculated_from_birthdate'):
                    birth_date = extracted_data.get('birth_date', '')
                    age = extracted_data.get('age', '')
                    age_info_message = f"\n\n💡 Ho rilevato la tua data di nascita ({birth_date}) e ho calcolato automaticamente che hai {age} anni."

                missing_message = f"""
Grazie!{age_info_message} Ho capito alcune informazioni, ma mi mancano ancora:

{self._format_missing_data(missing_data)}

Puoi fornirmele?
                """

                return False, missing_message.strip(), None
            else:
                return self._complete_first_data_collection()

        except Exception as e:
            print(f"❌ Errore nell'estrazione dati: {e}")
            import traceback
            traceback.print_exc()

            # Fallback sicuro: considera tutti i dati come mancanti
            all_fields = ['name', 'surname', 'birth_date', 'sex', 'birth_city', 'city', 'height', 'weight']

            missing_message = f"""
Mi scuso, ho avuto difficoltà a processare le informazioni. 

Mi servono questi dati:

{self._format_missing_data(all_fields)}

Puoi fornirmeli?
            """

            self.current_phase = "collect_missing_first_data"
            self.missing_fields = all_fields
            self.partial_first_data = {}

            return False, missing_message.strip(), None

    def _process_missing_first_data(self, user_input):
        """Processa i dati mancanti del primo messaggio - CON FALLBACK STRUTTURATO"""
        self.first_data_attempts += 1

        # Dopo 2 tentativi, passa al formato strutturato
        if self.first_data_attempts > self.max_attempts:
            return self._handle_structured_input_first_data(user_input)

        # Prova estrazione normale
        additional_data = self._extract_first_data(user_input)

        # Fallback intelligente se l'estrazione non funziona
        if not additional_data and self.missing_fields:
            user_input_clean = user_input.strip()

            # Riconoscimento pattern semplici
            if len(self.missing_fields) == 1:
                field = self.missing_fields[0]

                if field == 'surname':
                    surname_simple_patterns = [
                        r'^([A-Za-zÀ-ÿ]+)$',
                        r'([A-Za-zÀ-ÿ]+)$'
                    ]
                    for pattern in surname_simple_patterns:
                        match = re.search(pattern, user_input_clean)
                        if match and len(match.group(1)) > 1:
                            additional_data['surname'] = match.group(1).title()
                            print(f"🔍 DEBUG: Cognome riconosciuto: {additional_data['surname']}")
                            break

                elif field == 'birth_date':
                    date_simple_patterns = [
                        r'(\d{1,2}/\d{1,2}/\d{4})',
                        r'(\d{1,2}-\d{1,2}-\d{4})',
                        r'(\d{1,2}\.\d{1,2}\.\d{4})'
                    ]
                    for pattern in date_simple_patterns:
                        match = re.search(pattern, user_input_clean)
                        if match:
                            date_parts = re.split(r'[/\-.]', match.group(1))
                            if len(date_parts) == 3:
                                day, month, year = date_parts
                                additional_data['birth_date'] = f"{day.zfill(2)}/{month.zfill(2)}/{year}"
                                print(f"🔍 DEBUG: Data riconosciuta: {additional_data['birth_date']}")
                                break

                elif field in ['city', 'birth_city']:
                    italian_cities = [
                        'roma', 'milano', 'napoli', 'torino', 'palermo', 'genova',
                        'bologna', 'firenze', 'bari', 'catania', 'venezia', 'verona',
                        'messina', 'padova', 'trieste', 'brescia', 'parma', 'modena',
                        'reggio', 'perugia', 'livorno', 'cagliari', 'foggia', 'rimini',
                        'salerno', 'ferrara', 'pescara', 'monza', 'forlì', 'ravenna'
                    ]

                    potential_city = user_input_clean.lower()
                    if potential_city in italian_cities:
                        additional_data[field] = potential_city.title()
                        print(f"🔍 DEBUG: {field} riconosciuta: {additional_data[field]}")

                elif field == 'height':
                    height_match = re.search(r'(\d+)(?:\s*cm)?', user_input_clean)
                    if height_match:
                        height = int(height_match.group(1))
                        if 120 <= height <= 250:
                            additional_data['height'] = str(height)
                            print(f"🔍 DEBUG: Altezza riconosciuta: {additional_data['height']} cm")

                elif field == 'weight':
                    weight_match = re.search(r'(\d+)(?:\s*kg)?', user_input_clean)
                    if weight_match:
                        weight = int(weight_match.group(1))
                        if 30 <= weight <= 300:
                            additional_data['weight'] = str(weight)
                            print(f"🔍 DEBUG: Peso riconosciuto: {additional_data['weight']} kg")

                elif field == 'sex':
                    sex_lower = user_input_clean.lower()
                    if sex_lower in ['m', 'maschio', 'uomo', 'male']:
                        additional_data['sex'] = 'M'
                        print(f"🔍 DEBUG: Sesso riconosciuto: M")
                    elif sex_lower in ['f', 'femmina', 'donna', 'female']:
                        additional_data['sex'] = 'F'
                        print(f"🔍 DEBUG: Sesso riconosciuto: F")

        self.partial_first_data.update(additional_data)
        missing_data = self._check_missing_first_data(self.partial_first_data)

        if missing_data:
            self.missing_fields = missing_data

            # Se è il secondo tentativo, avvisa che al prossimo userà formato strutturato
            if self.first_data_attempts == self.max_attempts:
                missing_message = f"""
Mi mancano ancora questi dati:

{self._format_missing_data(missing_data)}

⚠️ Se ho difficoltà a capire la prossima volta, ti chiederò di usare un formato più semplice.
Per favore, prova ancora a fornirmeli.
                """
            else:
                missing_message = f"""
Mi mancano ancora questi dati:

{self._format_missing_data(missing_data)}

Per favore forniscimeli.
                """
            return False, missing_message.strip(), None
        else:
            # Completa i dati e passa al secondo messaggio
            self.registration_data.update(self.partial_first_data)
            self._populate_patient_first_data()

            # ✅ NUOVO: Calcola l'età se abbiamo la data di nascita ma non l'età E informa l'utente
            age_calculation_message = ""
            if 'birth_date' in self.partial_first_data and 'age' not in self.partial_first_data:
                calculated_age = calculate_age_from_birthdate(self.partial_first_data['birth_date'])
                if calculated_age:
                    self.registration_data['age'] = calculated_age
                    self.patient.set_age(calculated_age)
                    age_calculation_message = f"\n\n💡 Ho rilevato la tua data di nascita ({self.partial_first_data['birth_date']}) e ho calcolato automaticamente che hai {calculated_age} anni."
                    print(f"✅ Età calcolata automaticamente: {calculated_age} anni")

            if all(k in self.partial_first_data for k in ['name', 'surname', 'birth_date', 'sex', 'birth_city']):
                fiscal_code = calculate_fiscal_code(
                    self.partial_first_data['name'],
                    self.partial_first_data['surname'],
                    self.partial_first_data['birth_date'],
                    self.partial_first_data['sex'],
                    self.partial_first_data['birth_city']
                )
                self.registration_data['fiscal_code'] = fiscal_code
                self.patient.set_fiscal_code(fiscal_code)

            # Crea il messaggio con eventuale notifica del calcolo età
            if age_calculation_message:
                completion_message = f"Perfetto!{age_calculation_message}"
                return False, completion_message, None
            else:
                return self._complete_first_data_collection()

    def _handle_structured_input_first_data(self, user_input):
        """Gestisce input strutturato per i dati del primo messaggio"""
        print(f"🔧 DEBUG: Passaggio a formato strutturato per: {self.missing_fields}")

        # Prova a parsare input strutturato con virgole
        parsed_data = self._parse_comma_separated_input(user_input, self.missing_fields)

        if parsed_data:
            self.partial_first_data.update(parsed_data)
            missing_data = self._check_missing_first_data(self.partial_first_data)

            if not missing_data:
                return self._complete_first_data_collection()

        # Se ancora mancano dati, chiedi formato strutturato
        examples = []
        field_order = ['surname', 'birth_date', 'sex', 'birth_city', 'city', 'height', 'weight']

        for field in field_order:
            if field in self.missing_fields:
                if field == 'surname':
                    examples.append('Rossi')
                elif field == 'birth_date':
                    examples.append('15/03/1990')
                elif field == 'sex':
                    examples.append('M')
                elif field == 'birth_city':
                    examples.append('Roma')
                elif field == 'city':
                    examples.append('Milano')
                elif field == 'height':
                    examples.append('175')
                elif field == 'weight':
                    examples.append('70')

        structured_message = f"""
Mi scuso, non riesco ancora a capire perfettamente! 😅

Scrivi semplicemente i dati mancanti separati da virgole, in questo ordine:

{', '.join(examples)}

Esempio per i tuoi dati mancanti: {', '.join(examples[:len(self.missing_fields)])}
        """

        return False, structured_message.strip(), None

    def _parse_comma_separated_input(self, user_input, missing_fields):
        """Parsing di input separato da virgole"""
        parsed = {}
        parts = [part.strip() for part in user_input.split(',')]

        # Ordine standard dei campi
        field_order = ['surname', 'birth_date', 'sex', 'birth_city', 'city', 'height', 'weight']
        ordered_missing = [f for f in field_order if f in missing_fields]

        for i, part in enumerate(parts):
            if i < len(ordered_missing):
                field = ordered_missing[i]

                if field == 'surname':
                    if len(part) > 1:
                        parsed['surname'] = part.title()
                elif field == 'birth_date':
                    date_match = re.search(r'(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{4})', part)
                    if date_match:
                        day, month, year = date_match.groups()
                        parsed['birth_date'] = f"{day.zfill(2)}/{month.zfill(2)}/{year}"
                elif field == 'sex':
                    if part.upper() in ['M', 'F', 'MASCHIO', 'FEMMINA', 'UOMO', 'DONNA']:
                        parsed['sex'] = 'M' if part.upper() in ['M', 'MASCHIO', 'UOMO'] else 'F'
                elif field in ['birth_city', 'city']:
                    if len(part) > 1:
                        parsed[field] = part.title()
                elif field == 'height':
                    height_match = re.search(r'(\d+)', part)
                    if height_match:
                        height = int(height_match.group(1))
                        if 120 <= height <= 250:
                            parsed['height'] = str(height)
                elif field == 'weight':
                    weight_match = re.search(r'(\d+)', part)
                    if weight_match:
                        weight = int(weight_match.group(1))
                        if 30 <= weight <= 300:
                            parsed['weight'] = str(weight)

        print(f"🔧 DEBUG: Dati comma-separated parsati: {parsed}")
        return parsed

    def _parse_comma_separated_second_input(self, user_input, missing_fields):
        """Parsing di input separato da virgole per secondo messaggio"""
        parsed = {}
        parts = [part.strip() for part in user_input.split(',')]

        # Ordine standard dei campi
        field_order = ['allergies', 'diet', 'purpose']
        ordered_missing = [f for f in field_order if f in missing_fields]

        for i, part in enumerate(parts):
            if i < len(ordered_missing):
                field = ordered_missing[i]

                if field == 'allergies':
                    parsed['allergies'] = self._parse_allergies_list(part)
                elif field == 'diet':
                    parsed['diet'] = part.lower()
                elif field == 'purpose':
                    parsed['purpose'] = part

        print(f"🔧 DEBUG: Dati comma-separated secondo messaggio parsati: {parsed}")
        return parsed

    def _parse_comma_separated_lifestyle_input(self, user_input, missing_fields):
        """Parsing di input separato da virgole per dati lifestyle"""
        parsed = {}
        parts = [part.strip() for part in user_input.split(',')]

        # Ordine standard dei campi
        field_order = ['physical_activity_frequency', 'physical_activity_intensity', 'sleep_hours', 'alcohol_frequency',
                       'smoking_frequency']
        ordered_missing = [f for f in field_order if f in missing_fields]

        for i, part in enumerate(parts):
            if i < len(ordered_missing):
                field = ordered_missing[i]
                part_lower = part.lower()

                if field == 'physical_activity_frequency':
                    if 'mai' in part_lower or 'non' in part_lower:
                        parsed['physical_activity_frequency'] = 'mai'
                    elif 'giorn' in part_lower or 'tutti' in part_lower:
                        parsed['physical_activity_frequency'] = 'giornalmente'
                    elif 'settiman' in part_lower or re.search(r'\d+.*settiman', part_lower):
                        parsed['physical_activity_frequency'] = 'settimanalmente'
                    else:
                        parsed['physical_activity_frequency'] = part_lower

                elif field == 'physical_activity_intensity':
                    if 'leggera' in part_lower or 'bassa' in part_lower:
                        parsed['physical_activity_intensity'] = 'leggera'
                    elif 'moderata' in part_lower or 'media' in part_lower:
                        parsed['physical_activity_intensity'] = 'moderata'
                    elif 'intensa' in part_lower or 'alta' in part_lower:
                        parsed['physical_activity_intensity'] = 'intensa'
                    else:
                        parsed['physical_activity_intensity'] = part_lower

                elif field == 'sleep_hours':
                    hours_match = re.search(r'(\d+)', part)
                    if hours_match:
                        parsed['sleep_hours'] = int(hours_match.group(1))

                elif field == 'alcohol_frequency':
                    if 'mai' in part_lower or 'non' in part_lower:
                        parsed['alcohol_frequency'] = 'mai'
                    elif 'raram' in part_lower:
                        parsed['alcohol_frequency'] = 'raramente'
                    elif 'occasion' in part_lower:
                        parsed['alcohol_frequency'] = 'occasionalmente'
                    elif 'regolar' in part_lower:
                        parsed['alcohol_frequency'] = 'regolarmente'
                    else:
                        parsed['alcohol_frequency'] = part_lower

                elif field == 'smoking_frequency':
                    if 'mai' in part_lower or 'non' in part_lower:
                        parsed['smoking_frequency'] = 'mai'
                    elif 'ex' in part_lower or 'smesso' in part_lower:
                        parsed['smoking_frequency'] = 'ex fumatore'
                    elif 'occasion' in part_lower or 'raram' in part_lower:
                        parsed['smoking_frequency'] = 'occasionalmente'
                    elif 'regolar' in part_lower or 'spesso' in part_lower:
                        parsed['smoking_frequency'] = 'regolarmente'
                    else:
                        parsed['smoking_frequency'] = part_lower

        print(f"🔧 DEBUG: Dati comma-separated lifestyle parsati: {parsed}")
        return parsed

    def _process_preference_answer(self, user_input):
        """Processa le risposte alle domande sulle preferenze"""
        current_question = self.preference_questions[self.current_step]
        field = current_question["field"]

        try:
            rating = int(user_input.strip())
            if not (1 <= rating <= 5):
                return False, "Per favore inserisci un numero da 1 a 5:", current_question["question"]

            self.preferences_data[field] = rating

        except ValueError:
            return False, "Per favore inserisci un numero da 1 a 5:", current_question["question"]

        self.current_step += 1

        if self.current_step >= len(self.preference_questions):
            return self._complete_registration()

        return False, "Grazie!", self._get_current_question()

    def _complete_registration(self):
        """Completa la registrazione e avvia la ricerca semantica"""
        try:
            self._populate_patient_all_data()

            complete_notes = self._create_complete_notes()
            self.patient.set_additional_notes(complete_notes)

            patient_id = self.patient_db.save_patient(self.patient)

            if patient_id:
                success_message = """
✅ Registrazione completata con successo!

Il tuo profilo è stato salvato e ora procederò con la ricerca del medico più adatto alle tue esigenze utilizzando l'intelligenza artificiale.

Un momento mentre analizzo le tue preferenze...
                """

                return True, success_message.strip(), None
            else:
                return False, "Errore nel salvataggio. Riprova.", None

        except Exception as e:
            print(f"❌ Errore nella registrazione: {e}")
            return False, "Si è verificato un errore. Riprova.", None

    def _extract_first_data(self, text):
        """Estrae i dati anagrafici dal primo messaggio - VERSIONE CORRETTA"""
        extracted = {}
        text_lower = text.lower()

        print(f"🔍 DEBUG: Estrazione primo messaggio: '{text}'")

        # PRIORITY 1: Estrazione data di nascita - CORRETTA
        date_patterns = [
            r'nato\s+(?:il\s+)?(\d{1,2}/\d{1,2}/\d{4})',
            r'nata\s+(?:il\s+)?(\d{1,2}/\d{1,2}/\d{4})',
            r'nascita.*?(\d{1,2}/\d{1,2}/\d{4})',
            r'\b(\d{1,2}/\d{1,2}/\d{4})\b',  # Pattern generico con word boundary
            r'(\d{1,2}-\d{1,2}-\d{4})',  # Formato con trattini
            r'(\d{1,2}\.\d{1,2}\.\d{4})'  # Formato con punti
        ]

        for pattern in date_patterns:
            match = re.search(pattern, text)  # USA IL TESTO ORIGINALE, non lowercase
            if match:
                date_str = match.group(1)
                # Normalizza il formato
                date_normalized = re.sub(r'[-.]', '/', date_str)
                day, month, year = date_normalized.split('/')
                extracted['birth_date'] = f"{day.zfill(2)}/{month.zfill(2)}/{year}"
                print(f"🔍 DEBUG: Data estratta: {extracted['birth_date']}")

                # ✅ NUOVO: Calcola automaticamente l'età dalla data di nascita
                calculated_age = calculate_age_from_birthdate(extracted['birth_date'])
                if calculated_age:
                    extracted['age'] = calculated_age
                    extracted['age_calculated_from_birthdate'] = True  # Flag per messaggio informativo
                    print(f"🔍 DEBUG: Età calcolata automaticamente: {calculated_age} anni")
                break

        # PRIORITY 2: Estrazione nome e cognome CORRETTA
        # Lista estesa di parole da escludere dai nomi/cognomi
        excluded_words = ['nato', 'nata', 'sono', 'del', 'della', 'di', 'da', 'il', 'la', 'un', 'una', 'che', 'dove',
                          'come', 'chiamo', 'alto', 'alta', 'peso', 'vivo', 'abito', 'palermo', 'roma', 'milano', 'cm',
                          'kg', 'gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno', 'luglio', 'agosto',
                          'settembre', 'ottobre', 'novembre', 'dicembre', 'e', 'ed', 'ma', 'poi', 'anche', 'con',
                          'per', 'in', 'a', 'ad', 'su', 'tra', 'fra', 'oggi', 'ieri', 'domani', 'ora', 'adesso']

        def is_valid_name_part(word):
            """Verifica se una parola può essere parte di un nome/cognome"""
            if not word or len(word) < 2:
                return False
            if word.lower() in excluded_words:
                return False
            # ✅ CORREZIONE: Non escludere "faccio" quando è parte di "di cognome faccio"
            if word.lower() == 'faccio':
                return False  # "faccio" è un verbo, non un cognome
            if any(char.isdigit() for char in word):
                return False
            if not word.replace(' ', '').isalpha():
                return False
            return True

        # Pattern CONSERVATIVI per evitare match errati
        # 1. Pattern per "mi chiamo Nome Cognome" (sicuro)
        mi_chiamo_pattern = r'mi chiamo ([A-Za-zÀ-ÿ]+)\s+([A-Za-zÀ-ÿ]+(?:\s+[A-Za-zÀ-ÿ]+)*?)(?:\s*[,.]|\s*$)'
        match = re.search(mi_chiamo_pattern, text, re.IGNORECASE)
        if match:
            name_candidate = match.group(1).strip()
            surname_candidate = match.group(2).strip()

            if is_valid_name_part(name_candidate):
                extracted['name'] = name_candidate.title()

                if is_valid_name_part(surname_candidate):
                    extracted['surname'] = surname_candidate.title()
                    print(f"🔍 DEBUG: Nome e cognome estratti (mi chiamo): {extracted['name']} {extracted['surname']}")
                else:
                    print(f"🔍 DEBUG: Solo nome estratto (mi chiamo): {extracted['name']}")

        # 2. Pattern per "sono Nome" (solo nome, conservativo)
        elif re.search(r'\bsono\s+([A-Za-zÀ-ÿ]+)(?:\s+e\s|\s+nato|\s+nata|\s*,)', text, re.IGNORECASE):
            match = re.search(r'\bsono\s+([A-Za-zÀ-ÿ]+)(?:\s+e\s|\s+nato|\s+nata|\s*,)', text, re.IGNORECASE)
            name_candidate = match.group(1).strip()

            if is_valid_name_part(name_candidate):
                extracted['name'] = name_candidate.title()
                print(f"🔍 DEBUG: Solo nome estratto (sono): {extracted['name']}")

        # 3. Pattern per "il mio nome è Nome Cognome"
        elif re.search(r'il mio nome è ([A-Za-zÀ-ÿ]+)(?:\s+([A-Za-zÀ-ÿ]+(?:\s+[A-Za-zÀ-ÿ]+)*))?', text, re.IGNORECASE):
            match = re.search(r'il mio nome è ([A-Za-zÀ-ÿ]+)(?:\s+([A-Za-zÀ-ÿ]+(?:\s+[A-Za-zÀ-ÿ]+)*))?', text,
                              re.IGNORECASE)
            name_candidate = match.group(1).strip()
            surname_candidate = match.group(2).strip() if match.group(2) else None

            if is_valid_name_part(name_candidate):
                extracted['name'] = name_candidate.title()

                if surname_candidate and is_valid_name_part(surname_candidate):
                    extracted['surname'] = surname_candidate.title()
                    print(
                        f"🔍 DEBUG: Nome e cognome estratti (il mio nome è): {extracted['name']} {extracted['surname']}")
                else:
                    print(f"🔍 DEBUG: Solo nome estratto (il mio nome è): {extracted['name']}")

        # Pattern separati per cognome (quando fornito esplicitamente) - CORRETTI E MIGLIORATI
        surname_patterns = [
            # Pattern specifico per "di cognome faccio/sono COGNOME"
            r'di cognome (?:faccio|sono|mi chiamo)\s+([A-Za-zÀ-ÿ]+(?:\s+[A-Za-zÀ-ÿ]+){0,3})(?:\s+e\s|\s+nato|\s+nata|\s*,|\s*\.|\s*$)',
            # Pattern per "cognome è/faccio/sono COGNOME"
            r'cognome\s+(?:è|faccio|sono|mi chiamo)\s+([A-Za-zÀ-ÿ]+(?:\s+[A-Za-zÀ-ÿ]+){0,3})(?:\s+e\s|\s+nato|\s+nata|\s*,|\s*\.|\s*$)',
            # Pattern per "il mio cognome è COGNOME"
            r'il mio cognome è\s+([A-Za-zÀ-ÿ]+(?:\s+[A-Za-zÀ-ÿ]+){0,3})(?:\s+e\s|\s+nato|\s+nata|\s*,|\s*\.|\s*$)',
            # Pattern generico per "cognome: COGNOME"
            r'(?:il\s+)?cognome:?\s+([A-Za-zÀ-ÿ]+(?:\s+[A-Za-zÀ-ÿ]+){0,3})(?:\s+e\s|\s+nato|\s+nata|\s*,|\s*\.|\s*$)'
        ]

        # Estrazione cognome separata (solo se non già estratto)
        if not extracted.get('surname'):
            for pattern in surname_patterns:
                try:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        surname_candidate = match.group(1).strip()
                        print(f"🔍 DEBUG: Pattern cognome matched: '{pattern}' → '{surname_candidate}'")

                        # Validazione aggiuntiva: il cognome non può contenere parole della blacklist
                        surname_words = surname_candidate.split()
                        valid_surname_words = []

                        for word in surname_words:
                            if is_valid_name_part(word):
                                valid_surname_words.append(word)
                            else:
                                # Se troviamo una parola non valida, fermati
                                print(f"🔍 DEBUG: Parola non valida nel cognome: '{word}'")
                                break

                        if valid_surname_words:
                            final_surname = ' '.join(valid_surname_words)
                            extracted['surname'] = final_surname.title()
                            print(f"🔍 DEBUG: Cognome estratto separatamente: {extracted['surname']}")
                            break
                        else:
                            print(f"🔍 DEBUG: Cognome candidato '{surname_candidate}' scartato - nessuna parola valida")
                except Exception as e:
                    print(f"🔍 DEBUG: Errore pattern cognome '{pattern}': {e}")
                    continue

        # PRIORITY 3: Estrazione sesso MIGLIORATA
        sex_patterns = [
            r'sono (?:un\s+)?(maschio|uomo|ragazzo|m)\b',
            r'sono (?:una\s+)?(femmina|donna|ragazza|f)\b',
            r'sesso.*?(M|F|maschio|femmina|uomo|donna)',
            r'\b(maschio|femmina|uomo|donna|m|f)\b'
        ]

        for pattern in sex_patterns:
            match = re.search(pattern, text_lower)
            if match:
                value = match.group(1).lower()
                if value in ['maschio', 'uomo', 'ragazzo', 'm']:
                    extracted['sex'] = 'M'
                    print(f"🔍 DEBUG: Sesso estratto: M")
                    break
                elif value in ['femmina', 'donna', 'ragazza', 'f']:
                    extracted['sex'] = 'F'
                    print(f"🔍 DEBUG: Sesso estratto: F")
                    break

        # PRIORITY 4: Estrazione città MIGLIORATA
        italian_cities = [
            'roma', 'milano', 'napoli', 'torino', 'palermo', 'genova',
            'bologna', 'firenze', 'bari', 'catania', 'venezia', 'verona',
            'messina', 'padova', 'trieste', 'brescia', 'parma', 'modena',
            'reggio', 'perugia', 'livorno', 'cagliari', 'foggia', 'rimini',
            'salerno', 'ferrara', 'pescara', 'monza', 'forlì', 'ravenna',
            'bergamo', 'vicenza', 'terni', 'novara', 'piacenza', 'ancona'
        ]

        # Pattern per città di nascita
        birth_city_patterns = [
            r'nato\s+(?:a|ad|in)\s+([A-Za-zÀ-ÿ]+)(?:\s|$|,|\.|e)',
            r'nata\s+(?:a|ad|in)\s+([A-Za-zÀ-ÿ]+)(?:\s|$|,|\.|e)',
            r'originario\s+(?:di|da)\s+([A-Za-zÀ-ÿ]+)',
            r'originaria\s+(?:di|da)\s+([A-Za-zÀ-ÿ]+)',
            r'sono\s+(?:nato|nata)\s+(?:a|ad|in)?\s*([A-Za-zÀ-ÿ]+)'
        ]

        for pattern in birth_city_patterns:
            match = re.search(pattern, text_lower)
            if match:
                city_name = match.group(1).strip().lower()
                if city_name in italian_cities:
                    extracted['birth_city'] = city_name.title()
                    print(f"🔍 DEBUG: Città di nascita estratta: {extracted['birth_city']}")
                    break

        # Pattern per città di residenza
        residence_city_patterns = [
            r'vivo\s+(?:a|ad|in|ancora\s+a|tuttora\s+a)\s+([A-Za-zÀ-ÿ]+)(?:\s|$|,|\.|e)',
            r'abito\s+(?:a|ad|in)\s+([A-Za-zÀ-ÿ]+)(?:\s|$|,|\.|e)',
            r'risiedo\s+(?:a|ad|in)\s+([A-Za-zÀ-ÿ]+)(?:\s|$|,|\.|e)',
            r'attualmente\s+(?:a|ad|in)\s+([A-Za-zÀ-ÿ]+)(?:\s|$|,|\.|e)'
        ]

        for pattern in residence_city_patterns:
            match = re.search(pattern, text_lower)
            if match:
                city_name = match.group(1).strip().lower()
                if city_name in italian_cities:
                    extracted['city'] = city_name.title()
                    print(f"🔍 DEBUG: Città di residenza estratta: {extracted['city']}")
                    break

        # Gestione speciale: "nato e vivo a Palermo" = stessa città
        if ('nato e vivo' in text_lower or 'nata e vivo' in text_lower):
            combined_patterns = [
                r'(?:nato|nata)\s+e\s+vivo\s+(?:a|ad|in)\s+([A-Za-zÀ-ÿ]+)',
                r'(?:nato|nata)\s+e\s+(?:vivo|abito)\s+(?:a|ad|in)\s+([A-Za-zÀ-ÿ]+)'
            ]

            for pattern in combined_patterns:
                match = re.search(pattern, text_lower)
                if match:
                    city_name = match.group(1).strip().lower()
                    if city_name in italian_cities:
                        extracted['birth_city'] = city_name.title()
                        extracted['city'] = city_name.title()
                        print(f"🔍 DEBUG: Stessa città nascita/residenza: {extracted['city']}")
                        break

        # PRIORITY 5: Estrazione altezza e peso MIGLIORATA
        height_patterns = [
            r'alto\s+(\d+)\s*cm',
            r'alta\s+(\d+)\s*cm',
            r'altezza\s+(?:di\s+)?(\d+)',
            r'(\d+)\s*cm(?:\s+e\s+peso|\s*\.|\s*$|,)',
            r'sono\s+alto\s+(\d+)',
            r'sono\s+alta\s+(\d+)',
            r'misuro\s+(\d+)'
        ]

        for pattern in height_patterns:
            match = re.search(pattern, text_lower)
            if match:
                height = int(match.group(1))
                if 120 <= height <= 250:  # Range ragionevole
                    extracted['height'] = str(height)
                    print(f"🔍 DEBUG: Altezza estratta: {height} cm")
                    break

        weight_patterns = [
            r'peso\s+(\d+)\s*kg',
            r'(\d+)\s*kg(?:\s*$|\s*\.|,)',
            r'peso.*?(\d+)(?:\s*kg)?',
            r'pesa\s+(\d+)'
        ]

        for pattern in weight_patterns:
            match = re.search(pattern, text_lower)
            if match:
                weight = int(match.group(1))
                if 30 <= weight <= 300:  # Range ragionevole
                    extracted['weight'] = str(weight)
                    print(f"🔍 DEBUG: Peso estratto: {weight} kg")
                    break

        # FALLBACK: Gestione input strutturato tipo "Di Gangi, 28/01/1999, Palermo"
        if ',' in text and len(text.split(',')) >= 2:
            parts = [p.strip() for p in text.split(',')]

            for i, part in enumerate(parts):
                # Controlla se è una data
                date_match = re.search(r'\b(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{4})\b', part)
                if date_match and not extracted.get('birth_date'):
                    date_str = re.sub(r'[-.]', '/', date_match.group(1))
                    day, month, year = date_str.split('/')
                    extracted['birth_date'] = f"{day.zfill(2)}/{month.zfill(2)}/{year}"
                    print(f"🔍 DEBUG: Data da input strutturato: {extracted['birth_date']}")

                    # ✅ NUOVO: Calcola l'età anche qui
                    calculated_age = calculate_age_from_birthdate(extracted['birth_date'])
                    if calculated_age:
                        extracted['age'] = calculated_age
                        extracted['age_calculated_from_birthdate'] = True  # Flag per messaggio informativo
                        print(f"🔍 DEBUG: Età calcolata da input strutturato: {calculated_age} anni")

                # Controlla se è una città
                if part.lower() in italian_cities and not extracted.get('birth_city'):
                    extracted['birth_city'] = part.title()
                    print(f"🔍 DEBUG: Città da input strutturato: {extracted['birth_city']}")

                # Controlla se è un cognome (se non abbiamo già nome E cognome)
                if (not extracted.get('surname') and extracted.get('name') and
                        len(part.split()) <= 2 and
                        is_valid_name_part(part)):
                    extracted['surname'] = part.title()
                    print(f"🔍 DEBUG: Cognome da input strutturato: {extracted['surname']}")

                # Controlla se è solo un nome (quando non c'è già un nome)
                elif (not extracted.get('name') and
                      len(part.split()) == 1 and
                      is_valid_name_part(part)):
                    extracted['name'] = part.title()
                    print(f"🔍 DEBUG: Nome da input strutturato: {extracted['name']}")

        print(f"🔍 DEBUG: Dati estratti finali: {extracted}")
        return extracted

    def _extract_second_data(self, text):
        """Estrae i dati lifestyle dal secondo messaggio"""
        extracted = {}
        text_lower = text.lower()

        print(f"🔍 DEBUG: Estrazione secondo messaggio: '{text}'")

        # Estrazione allergie migliorata
        if 'non ho allergie' in text_lower or 'nessuna allergia' in text_lower or 'allergie nessuna' in text_lower:
            extracted['allergies'] = 'Nessuna'
            print(f"🔍 DEBUG: Allergie estratte: Nessuna")
        else:
            allergie_patterns = [
                r'allergie?:?\s*(.*?)(?:\s*\.|$|\s*,\s*(?:dieta|diet|mangio|problema|motivo))',
                r'allergico?\s+a\s+(.*?)(?:\s*\.|$|\s*,)',
                r'allergia\s+a\s+(.*?)(?:\s*\.|$|\s*,)',
                r'ho.*?allergie?\s+a\s+(.*?)(?:\s*\.|$|\s*,)',
            ]

            for pattern in allergie_patterns:
                match = re.search(pattern, text_lower)
                if match:
                    allergie_text = match.group(1).strip()
                    if allergie_text and len(allergie_text) > 1:
                        extracted['allergies'] = self._parse_allergies_list(allergie_text)
                        print(f"🔍 DEBUG: Allergie estratte: {extracted['allergies']}")
                        break

        # Estrazione tipo di dieta
        diet_patterns = [
            r'dieta\s+(.*?)(?:\s*\.|$|\s*,\s*(?:problema|motivo|consulto))',
            r'seguo.*?dieta\s+(.*?)(?:\s*\.|$|\s*,)',
            r'mangio\s+(.*?)(?:\s*\.|$|\s*,)',
            r'alimentazione\s+(.*?)(?:\s*\.|$|\s*,)',
            r'tipo.*?dieta.*?:\s*(.*?)(?:\s*\.|$|\s*,)'
        ]

        for pattern in diet_patterns:
            match = re.search(pattern, text_lower)
            if match:
                diet_text = match.group(1).strip()
                if diet_text and len(diet_text) > 1:
                    extracted['diet'] = diet_text
                    print(f"🔍 DEBUG: Dieta estratta: {extracted['diet']}")
                    break

        # Estrazione motivo/problema
        purpose_patterns = [
            r'problema\s+(.*?)(?:\s*\.|$)',
            r'motivo\s+(.*?)(?:\s*\.|$)',
            r'consulto.*?per\s+(.*?)(?:\s*\.|$)',
            r'medico.*?per\s+(.*?)(?:\s*\.|$)',
            r'soffro\s+di\s+(.*?)(?:\s*\.|$)',
            r'ho\s+(mal.*?)(?:\s*\.|$)',
            r'visitare.*?per\s+(.*?)(?:\s*\.|$)'
        ]

        for pattern in purpose_patterns:
            match = re.search(pattern, text_lower)
            if match:
                purpose_text = match.group(1).strip()
                if purpose_text and len(purpose_text) > 1:
                    extracted['purpose'] = purpose_text
                    print(f"🔍 DEBUG: Motivo estratto: {extracted['purpose']}")
                    break

        print(f"🔍 DEBUG: Dati secondo messaggio estratti: {extracted}")
        return extracted

    def _parse_allergies_list(self, allergie_text):
        """Parsing intelligente delle allergie"""
        # Pulisci il testo
        allergie_text = allergie_text.strip()

        # Pattern per separatori
        separators = [
            r',\s*e\s+',  # ", e "
            r'\s+e\s+',  # " e "
            r',\s*',  # ", "
            r';\s*',  # "; "
        ]

        # Sostituisci tutti i separatori con virgole
        for sep in separators:
            allergie_text = re.sub(sep, ',', allergie_text)

        # Splitta e pulisci
        allergie_list = [a.strip() for a in allergie_text.split(',') if a.strip()]

        # Rimuovi duplicati mantenendo l'ordine
        seen = set()
        unique_allergie = []
        for allergia in allergie_list:
            allergia_clean = allergia.lower().strip()
            if allergia_clean not in seen and allergia_clean:
                seen.add(allergia_clean)
                unique_allergie.append(allergia.title())

        result = ', '.join(unique_allergie) if unique_allergie else 'Nessuna'
        print(f"🔍 DEBUG: Allergie parsate: '{allergie_text}' → {unique_allergie} → '{result}'")
        return result

    def _extract_lifestyle_data(self, text):
        """Estrae i dati lifestyle completi"""
        extracted = {}
        text_lower = text.lower()

        print(f"🔍 DEBUG: Estrazione dati lifestyle: '{text}'")

        # Estrazione attività fisica FREQUENZA
        activity_frequency_patterns = [
            (r'non faccio sport|non pratico|sedentario|mai sport', 'mai'),
            (r'tutti i giorni|giornalmente|ogni giorno', 'giornalmente'),
            (r'(\d+)\s*volte.*?settimana', 'settimanalmente'),
            (r'settimanalmente|a settimana', 'settimanalmente'),
            (r'occasionalmente|raramente|qualche volta', 'occasionalmente'),
            (r'regolarmente|spesso', 'settimanalmente')
        ]

        for pattern, frequency in activity_frequency_patterns:
            if isinstance(pattern, str):
                if re.search(pattern, text_lower):
                    extracted['physical_activity_frequency'] = frequency
                    break
            else:
                match = re.search(pattern, text_lower)
                if match:
                    freq_num = int(match.group(1))
                    if freq_num >= 6:
                        extracted['physical_activity_frequency'] = 'giornalmente'
                    elif freq_num >= 3:
                        extracted['physical_activity_frequency'] = 'settimanalmente'
                    else:
                        extracted['physical_activity_frequency'] = 'occasionalmente'
                    break

        # Estrazione attività fisica INTENSITÀ
        intensity_patterns = [
            (r'intensità.*?(leggera|bassa)', 'leggera'),
            (r'intensità.*?(moderata|media)', 'moderata'),
            (r'intensità.*?(intensa|alta|vigorosa)', 'intensa'),
            (r'leggera|blanda|soft', 'leggera'),
            (r'moderata|media|normale', 'moderata'),
            (r'intensa|forte|vigorosa|pesante|alta', 'intensa'),
            (r'non.*?intensità|senza intensità', 'leggera')
        ]

        for pattern, intensity in intensity_patterns:
            if re.search(pattern, text_lower):
                extracted['physical_activity_intensity'] = intensity
                break

        # Se non fa sport, imposta intensità vuota
        if extracted.get('physical_activity_frequency') == 'mai':
            extracted['physical_activity_intensity'] = ''

        # Estrazione ore di sonno
        sleep_patterns = [
            r'dormo (\d+)\s*ore',
            r'(\d+)\s*ore.*?sonno',
            r'(\d+)\s*ore.*?notte',
            r'sonno.*?(\d+)\s*ore',
            r'(\d+)\s*ore'
        ]

        for pattern in sleep_patterns:
            match = re.search(pattern, text_lower)
            if match:
                hours = int(match.group(1))
                if 4 <= hours <= 12:  # Range ragionevole
                    extracted['sleep_hours'] = hours
                    break

        # Estrazione frequenza alcol
        alcohol_patterns = [
            (r'non bevo|mai alcol|astemio', 'mai'),
            (r'raramente|quasi mai', 'raramente'),
            (r'occasionalmente|qualche volta|weekend', 'occasionalmente'),
            (r'regolarmente|spesso|tutti i giorni|ogni sera', 'regolarmente')
        ]

        for pattern, frequency in alcohol_patterns:
            if re.search(pattern, text_lower):
                extracted['alcohol_frequency'] = frequency
                break

        # Estrazione abitudine fumo
        smoking_patterns = [
            (r'non fumo|mai fumato|non ho mai', 'mai'),
            (r'occasionalmente|raramente|qualche volta', 'occasionalmente'),
            (r'fumo|sigarette|regolarmente.*?fumo', 'regolarmente'),
            (r'ex fumatore|smesso|prima fumavo', 'ex fumatore')
        ]

        for pattern, frequency in smoking_patterns:
            if re.search(pattern, text_lower):
                extracted['smoking_frequency'] = frequency
                break

        print(f"🔍 DEBUG: Dati lifestyle estratti: {extracted}")
        return extracted

    def _check_missing_first_data(self, data):
        """Controlla quali dati del primo messaggio mancano"""
        required_fields = ['name', 'surname', 'birth_date', 'sex', 'birth_city', 'city', 'height', 'weight']
        missing = []

        for field in required_fields:
            if field not in data or not data[field]:
                missing.append(field)

        return missing

    def _check_missing_second_data(self, data):
        """Controlla quali dati del secondo messaggio mancano"""
        required_fields = ['allergies', 'diet', 'purpose']
        missing = []

        for field in required_fields:
            if field not in data or not data[field]:
                missing.append(field)

        return missing

    def _check_missing_lifestyle_data(self, data):
        """Controlla quali dati lifestyle mancano"""
        required_fields = ['physical_activity_frequency', 'physical_activity_intensity', 'sleep_hours',
                           'alcohol_frequency',
                           'smoking_frequency']
        missing = []

        for field in required_fields:
            if field not in data or data[field] == '' or data[field] is None:
                # Eccezione: se non fa sport, l'intensità può essere vuota
                if field == 'physical_activity_intensity' and data.get('physical_activity_frequency') == 'mai':
                    continue
                missing.append(field)

        return missing

    def _format_missing_data(self, missing_fields):
        """Formatta l'elenco dei dati mancanti del primo messaggio"""
        field_names = {
            'name': 'Nome',
            'surname': 'Cognome',
            'birth_date': 'Data di nascita (DD/MM/YYYY)',
            'sex': 'Sesso (maschio/femmina)',
            'birth_city': 'Città di nascita',
            'city': 'Città di residenza attuale',
            'height': 'Altezza (in cm)',
            'weight': 'Peso (in kg)'
        }

        formatted_list = []
        for field in missing_fields:
            field_name = field_names.get(field, field)

            if field == 'city' and hasattr(self, 'partial_first_data') and 'birth_city' in self.partial_first_data:
                birth_city = self.partial_first_data['birth_city']
                field_name = f"Città di residenza attuale (vivi ancora a {birth_city}? Se sì scrivi '{birth_city}', altrimenti indica dove vivi ora)"

            formatted_list.append(f"• {field_name}")

        return '\n'.join(formatted_list)

    def _populate_patient_first_data(self):
        """Popola i dati del primo messaggio nel paziente"""
        data = self.registration_data

        if 'name' in data:
            self.patient.set_name(data['name'])
        if 'surname' in data:
            self.patient.set_surname(data['surname'])
        if 'birth_date' in data:
            self.patient.set_birth_date(self._convert_birthdate(data['birth_date']))
        if 'age' in data:
            self.patient.set_age(data['age'])
        if 'sex' in data:
            self.patient.set_sex(data['sex'].upper())
        if 'city' in data:
            self.patient.set_city(data['city'])
        if 'height' in data:
            self.patient.set_height(float(data['height']))
        if 'weight' in data:
            self.patient.set_weight(float(data['weight']))

    def _populate_patient_all_data(self):
        """Popola tutti i dati del paziente"""
        # Questo metodo chiama tutti i metodi di popolamento
        self._populate_patient_first_data()
        self._populate_patient_all_lifestyle_data()

    def _get_current_question(self):
        """Ottiene la domanda corrente"""
        if self.current_phase == "motivation_questions":
            if self.current_step < len(self.motivation_questions):
                return self.motivation_questions[self.current_step]["question"]
        elif self.current_phase == "preference_questions":
            if self.current_step < len(self.preference_questions):
                return self.preference_questions[self.current_step]["question"]
        return None

    def _create_motivation_summary(self):
        """Crea un riassunto narrativo delle risposte motivazionali"""
        summary_parts = []

        # Crea un resoconto narrativo invece di elenchi puntati
        if 'download_reason' in self.motivation_data:
            reasons = self.motivation_data['download_reason']
            if len(reasons) == 1:
                reason_text = f"Hai scaricato Longeviva perché {reasons[0].lower()}."
            elif len(reasons) == 2:
                reason_text = f"Hai scaricato Longeviva perché {reasons[0].lower()} e {reasons[1].lower()}."
            else:
                reason_text = f"Hai scaricato Longeviva perché {', '.join([r.lower() for r in reasons[:-1]])} e {reasons[-1].lower()}."
            summary_parts.append(reason_text)

        if 'objectives' in self.motivation_data:
            objectives = self.motivation_data['objectives']
            if len(objectives) == 1:
                obj_text = f"Il tuo obiettivo principale è {objectives[0].lower()}."
            elif len(objectives) == 2:
                obj_text = f"I tuoi obiettivi principali sono {objectives[0].lower()} e {objectives[1].lower()}."
            else:
                obj_text = f"I tuoi obiettivi principali sono {', '.join([o.lower() for o in objectives[:-1]])} e {objectives[-1].lower()}."
            summary_parts.append(obj_text)

        if 'expectations' in self.motivation_data:
            expectations = self.motivation_data['expectations']
            if len(expectations) == 1:
                exp_text = f"Ti aspetti {expectations[0].lower()}."
            elif len(expectations) == 2:
                exp_text = f"Ti aspetti {expectations[0].lower()} e {expectations[1].lower()}."
            else:
                exp_text = f"Ti aspetti {', '.join([e.lower() for e in expectations[:-1]])} e {expectations[-1].lower()}."
            summary_parts.append(exp_text)

        return " ".join(summary_parts)

    def _create_complete_notes(self):
        """Crea le note complete con obiettivi e preferenze"""
        notes_parts = []

        motivation_summary = self._create_motivation_summary()
        notes_parts.append(f"=== PROFILO MOTIVAZIONALE ===\n{motivation_summary}")

        if self.preferences_data:
            pref_summary = "\n=== PREFERENZE MEDICO ===\n"
            pref_labels = {
                'vicinanza': 'Vicinanza',
                'specializzazione': 'Specializzazione',
                'costo': 'Costo',
                'area_interesse': 'Area di Interesse'
            }

            for field, rating in self.preferences_data.items():
                label = pref_labels.get(field, field)
                pref_summary += f"• {label}: {rating}/5\n"

            notes_parts.append(pref_summary.strip())

        if 'additional_notes' in self.registration_data:
            notes_parts.append(f"\n=== NOTE AGGIUNTIVE ===\n{self.registration_data['additional_notes']}")

        return '\n\n'.join(notes_parts)

    def _convert_birthdate(self, date_str):
        """Converte la data di nascita nel formato richiesto"""
        try:
            day, month, year = date_str.split('/')
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}T00:00:00.000"
        except:
            return date_str

    def get_preferences(self):
        """Restituisce le preferenze raccolte per la ricerca semantica"""
        return self.preferences_data

    def get_motivation_data(self):
        """Restituisce i dati motivazionali per la ricerca semantica"""
        return self.motivation_data