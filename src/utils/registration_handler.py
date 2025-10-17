# src/utils/registration_handler.py - VERSIONE COMPLETA CON SICUREZZA
import re
from datetime import datetime
import json
import sys
import os

# Aggiungi il path per importare dalle directory parent
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.Patient.patients_handler import PatientHandler
from src.utils.security_utils import SecurityUtils


def calculate_age_from_birthdate(birth_date_str):
    """
    Calcola l'età dalla data di nascita in formato DD/MM/YYYY
    """
    try:
        day, month, year = birth_date_str.split('/')
        birth_date = datetime(int(year), int(month), int(day))
        today = datetime.now()
        age = today.year - birth_date.year
        if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
            age -= 1
        return age
    except Exception as e:
        print(f"⚠️ Errore nel calcolo dell'età: {e}")
        return None


def calculate_birth_date_from_age(age):
    """
    Calcola una data di nascita approssimativa dall'età
    """
    try:
        current_year = datetime.now().year
        birth_year = current_year - age
        return f"01/01/{birth_year}"
    except Exception as e:
        print(f"⚠️ Errore nel calcolo della data di nascita: {e}")
        return None


def parse_date_italian(date_string):
    """
    Parsa date in formato italiano come "28 gennaio 1999" o "28/01/1999"
    """
    month_names = {
        'gennaio': '01', 'febbraio': '02', 'marzo': '03', 'aprile': '04',
        'maggio': '05', 'giugno': '06', 'luglio': '07', 'agosto': '08',
        'settembre': '09', 'ottobre': '10', 'novembre': '11', 'dicembre': '12'
    }

    date_string = date_string.lower().strip()

    # Formato "28 gennaio 1999"
    for month_name, month_num in month_names.items():
        if month_name in date_string:
            pattern = rf'(\d{{1,2}})\s+{month_name}\s+(\d{{4}})'
            match = re.search(pattern, date_string)
            if match:
                day = match.group(1).zfill(2)
                year = match.group(2)
                return f"{day}/{month_num}/{year}"

    # Formato DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY
    date_patterns = [
        r'(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{4})',
        r'(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2})'
    ]

    for pattern in date_patterns:
        match = re.search(pattern, date_string)
        if match:
            day = match.group(1).zfill(2)
            month = match.group(2).zfill(2)
            year = match.group(3)

            if len(year) == 2:
                year_int = int(year)
                if year_int <= 30:
                    year = f"20{year}"
                else:
                    year = f"19{year}"

            return f"{day}/{month}/{year}"

    return None


def calculate_fiscal_code(name, surname, birth_date, sex, birth_city):
    """
    Calcola il codice fiscale italiano
    """
    try:
        month_codes = ['A', 'B', 'C', 'D', 'E', 'H', 'L', 'M', 'P', 'R', 'S', 'T']
        city_codes = {
            'roma': 'H501', 'milano': 'F205', 'napoli': 'F839', 'torino': 'L219',
            'palermo': 'G273', 'genova': 'D969', 'bologna': 'A944', 'firenze': 'D612',
            'bari': 'A662', 'catania': 'C351', 'venezia': 'L736', 'verona': 'L781',
            'messina': 'F158', 'padova': 'G224', 'trieste': 'L424', 'brescia': 'B157'
        }

        consonants = 'BCDFGHJKLMNPQRSTVWXYZ'
        vowels = 'AEIOU'

        def extract_consonants_vowels(text):
            text = text.upper().replace(' ', '')
            cons = ''.join([c for c in text if c in consonants])
            vows = ''.join([c for c in text if c in vowels])
            return cons, vows

        surname_cons, surname_vows = extract_consonants_vowels(surname)
        surname_code = (surname_cons + surname_vows + 'XXX')[:3]

        name_cons, name_vows = extract_consonants_vowels(name)
        if len(name_cons) >= 4:
            name_code = name_cons[0] + name_cons[2] + name_cons[3]
        else:
            name_code = (name_cons + name_vows + 'XXX')[:3]

        day, month, year = birth_date.split('/')
        year_code = year[-2:]
        month_code = month_codes[int(month) - 1]
        day_code = str(int(day) + (40 if sex.upper() == 'F' else 0)).zfill(2)
        city_code = city_codes.get(birth_city.lower(), 'Z999')
        partial_code = surname_code + name_code + year_code + month_code + day_code + city_code
        check_digit = 'Z'

        return partial_code + check_digit

    except Exception as e:
        print(f"⚠️ Errore calcolo codice fiscale: {e}")
        return "CALCOLO_NON_RIUSCITO"


class RegistrationHandler:
    """
    Gestisce il processo di registrazione strutturato del paziente - VERSIONE COMPLETA CON SICUREZZA
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
        self.clinical_data_attempts = 0
        self.max_attempts = 2

        # Variabili per le credenziali generate
        self.generated_password = None
        self.patient_document_id = None

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
        """Processa la risposta dell'utente secondo il flusso completo"""
        if self.current_phase == "motivation_questions":
            return self._process_motivation_answer(user_input)
        elif self.current_phase == "show_summary":
            return self._process_summary_confirmation(user_input)
        elif self.current_phase == "collect_first_data":
            return self._process_first_data_message(user_input)
        elif self.current_phase == "collect_missing_first_data":
            return self._process_missing_first_data(user_input)
        elif self.current_phase == "collect_purpose":
            return self._process_purpose_message(user_input)
        elif self.current_phase == "collect_clinical_data":
            return self._process_clinical_data_message(user_input)
        elif self.current_phase == "collect_missing_clinical_data":
            return self._process_missing_clinical_data(user_input)
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
    {summary}

    Ora procediamo con la raccolta dei tuoi dati per completare la registrazione.
    Premi invio per continuare.
            """

            return False, summary_message.strip(), None

        return False, "Perfetto!", self._get_current_question()

    def _process_summary_confirmation(self, user_input):
        """Processa la conferma del riassunto e passa alla raccolta dati"""
        # ✅ Non importa cosa scrive l'utente, procediamo sempre alla raccolta dati
        self.current_phase = "collect_first_data"

        first_data_message = """
    Ora ho bisogno delle tue informazioni anagrafiche.

    Scrivi un messaggio naturale che includa:
    - Il tuo nome e cognome
    - La tua email (servirà per accedere al sistema)
    - La tua data di nascita (puoi scriverla come "15/03/1990" oppure "15 marzo 1990") oppure la tua età
    - Se sei maschio o femmina
    - La città dove sei nato/a
    - La città dove vivi attualmente
    - La tua altezza (in cm)
    - Il tuo peso (in kg)

    Esempio: "Sono Mario Rossi, email mario.rossi@email.com, nato il 15 marzo 1990, sono maschio, nato a Roma dove vivo tuttora. Sono alto 175 cm e peso 70 kg."

    Puoi scrivere in modo naturale come preferisci!
        """

        return False, first_data_message.strip(), None

    def _process_first_data_message(self, user_input):
        """Processa il primo messaggio con dati anagrafici"""
        try:
            extracted_data = self._extract_first_data(user_input)
            missing_data = self._check_missing_first_data(extracted_data)

            if missing_data:
                self.current_phase = "collect_missing_first_data"
                self.missing_fields = missing_data
                self.partial_first_data = extracted_data  # ✅ Inizializza qui

                age_info_message = ""
                if extracted_data.get('age_calculated_from_birthdate'):
                    birth_date = extracted_data.get('birth_date', '')
                    age = extracted_data.get('age', '')
                    age_info_message = f"\n\n💡 Ho rilevato la tua data di nascita ({birth_date}) e ho calcolato automaticamente che hai {age} anni."
                elif extracted_data.get('birth_date_calculated_from_age'):
                    age = extracted_data.get('age', '')
                    birth_date = extracted_data.get('birth_date', '')
                    age_info_message = f"\n\n💡 Hai {age} anni, ho impostato una data di nascita approssimativa ({birth_date})."

                missing_message = f"""
    Grazie!{age_info_message} Ho capito alcune informazioni, ma mi mancano ancora:

    {self._format_missing_data(missing_data)}

    Puoi fornirmele?
                """

                return False, missing_message.strip(), None
            else:
                self.partial_first_data = extracted_data  # ✅ Inizializza anche nel caso di successo
                return self._complete_first_data_collection()

        except Exception as e:
            print(f"❌ Errore nell'estrazione dati: {e}")
            all_fields = ['name', 'surname', 'email', 'birth_date', 'sex', 'birth_city', 'city', 'height', 'weight']

            # ✅ FIX PRINCIPALE: Inizializza partial_first_data nel blocco except
            self.partial_first_data = {}

            missing_message = f"""
    Mi scuso, ho avuto difficoltà a processare le informazioni. 

    Mi servono questi dati:

    {self._format_missing_data(all_fields)}

    Puoi fornirmeli?
            """

            self.current_phase = "collect_missing_first_data"
            self.missing_fields = all_fields

            return False, missing_message.strip(), None

    def _extract_first_data(self, text):
        """Estrae i dati anagrafici dal primo messaggio - VERSIONE CORRETTA DEFINITIVA"""
        extracted = {}
        text_lower = text.lower()

        print(f"🔍 DEBUG: Estrazione primo messaggio: '{text}'")

        # Estrazione email
        email_patterns = [
            r'email\s*[:\-]?\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            r'mail\s*[:\-]?\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            r'\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b'
        ]

        for pattern in email_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                extracted['email'] = match.group(1).lower()
                print(f"🔍 DEBUG: Email estratta: {extracted['email']}")
                break

        # Estrazione data di nascita
        date_patterns = [
            r'nato\s+(?:il\s+)?(\d{1,2}\s+[a-zA-Z]+\s+\d{4})',
            r'nata\s+(?:il\s+)?(\d{1,2}\s+[a-zA-Z]+\s+\d{4})',
            r'nato\s+(?:il\s+)?(\d{1,2}/\d{1,2}/\d{4})',
            r'nata\s+(?:il\s+)?(\d{1,2}/\d{1,2}/\d{4})',
            r'\b(\d{1,2}\s+[a-zA-Z]+\s+\d{4})\b',
            r'\b(\d{1,2}/\d{1,2}/\d{4})\b'
        ]

        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                parsed_date = parse_date_italian(date_str)
                if parsed_date:
                    extracted['birth_date'] = parsed_date
                    print(f"🔍 DEBUG: Data estratta: {extracted['birth_date']}")
                    calculated_age = calculate_age_from_birthdate(extracted['birth_date'])
                    if calculated_age:
                        extracted['age'] = calculated_age
                        extracted['age_calculated_from_birthdate'] = True
                        print(f"🔍 DEBUG: Età calcolata: {calculated_age} anni")
                    break

        # Estrazione età se non trovata data
        if 'birth_date' not in extracted:
            age_patterns = [
                r'ho (\d+) anni',
                r'(\d+) anni',
                r'età (\d+)'
            ]
            for pattern in age_patterns:
                match = re.search(pattern, text_lower)
                if match:
                    age = int(match.group(1))
                    if 0 < age < 120:
                        extracted['age'] = age
                        birth_date_approx = calculate_birth_date_from_age(age)
                        if birth_date_approx:
                            extracted['birth_date'] = birth_date_approx
                            extracted['birth_date_calculated_from_age'] = True
                            print(f"🔍 DEBUG: Età estratta: {age}")
                        break

        # ESTRAZIONE NOME E COGNOME - VERSIONE SICURA
        excluded_words = ['nato', 'nata', 'sono', 'del', 'della', 'di', 'da', 'il', 'la', 'un', 'una', 'che', 'dove',
                          'come', 'chiamo', 'alto', 'alta', 'peso', 'vivo', 'abito', 'email', 'mail', 'cm', 'kg',
                          'uomo', 'donna', 'maschio', 'femmina', 'e', 'ed']

        def is_valid_name_part(word):
            if not word or len(word) < 2:
                return False
            if word.lower() in excluded_words:
                return False
            if any(char.isdigit() for char in word):
                return False
            if '@' in word:
                return False
            if not word.replace("'", "").isalpha():
                return False
            return True

        # Pattern sicuri per nome e cognome
        name_patterns = [
            r'(?:mi chiamo|sono)\s+([A-Za-zÀ-ÿ\']+)\s+([A-Za-zÀ-ÿ\']+)(?:\s*[,.]|\s+e\s|\s+nato|\s+nata|\s+email)',
            r'il mio nome è\s+([A-Za-zÀ-ÿ\']+)(?:\s+([A-Za-zÀ-ÿ\']+))?'
        ]

        for pattern in name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name_candidate = match.group(1).strip()
                surname_candidate = match.group(2).strip() if len(match.groups()) > 1 and match.group(2) else None

                print(f"🔍 DEBUG: Pattern matched - Nome: '{name_candidate}', Cognome: '{surname_candidate}'")

                if is_valid_name_part(name_candidate):
                    extracted['name'] = name_candidate.title()
                    print(f"🔍 DEBUG: Nome estratto: {extracted['name']}")

                    if surname_candidate and is_valid_name_part(surname_candidate):
                        extracted['surname'] = surname_candidate.title()
                        print(f"🔍 DEBUG: Cognome estratto: {extracted['surname']}")
                    break

        # ESTRAZIONE SESSO - PRIORITARIA
        sex_patterns = [
            r'sono\s+(?:un\s+)?(uomo|maschio)',
            r'sono\s+(?:una\s+)?(donna|femmina)',
            r'\b(uomo|donna|maschio|femmina)\b'
        ]

        for pattern in sex_patterns:
            match = re.search(pattern, text_lower)
            if match:
                value = match.group(1).lower()
                if value in ['uomo', 'maschio']:
                    extracted['sex'] = 'M'
                    print(f"🔍 DEBUG: Sesso estratto: M")
                    break
                elif value in ['donna', 'femmina']:
                    extracted['sex'] = 'F'
                    print(f"🔍 DEBUG: Sesso estratto: F")
                    break

        # ESTRAZIONE CITTÀ - MIGLIORATA
        italian_cities = [
            'roma', 'milano', 'napoli', 'torino', 'palermo', 'genova',
            'bologna', 'firenze', 'bari', 'catania', 'venezia', 'verona',
            'messina', 'padova', 'trieste', 'brescia', 'parma', 'modena'
        ]

        # Pattern per città di nascita
        birth_city_patterns = [
            r'nato\s+(?:a|ad|in)\s+([A-Za-zÀ-ÿ]+)',
            r'nata\s+(?:a|ad|in)\s+([A-Za-zÀ-ÿ]+)',
            r'originario\s+(?:di|da)\s+([A-Za-zÀ-ÿ]+)',
            r'originaria\s+(?:di|da)\s+([A-Za-zÀ-ÿ]+)'
        ]

        for pattern in birth_city_patterns:
            match = re.search(pattern, text_lower)
            if match:
                city_name = match.group(1).strip().lower()
                if city_name in italian_cities:
                    extracted['birth_city'] = city_name.title()
                    print(f"🔍 DEBUG: Città di nascita: {extracted['birth_city']}")
                    break

        # Pattern per città di residenza
        residence_patterns = [
            r'vivo\s+(?:a|ad|in|ancora\s+a|tuttora\s+a)\s+([A-Za-zÀ-ÿ]+)',
            r'abito\s+(?:a|ad|in)\s+([A-Za-zÀ-ÿ]+)',
            r'risiedo\s+(?:a|ad|in)\s+([A-Za-zÀ-ÿ]+)'
        ]

        for pattern in residence_patterns:
            match = re.search(pattern, text_lower)
            if match:
                city_name = match.group(1).strip().lower()
                if city_name in italian_cities:
                    extracted['city'] = city_name.title()
                    print(f"🔍 DEBUG: Città di residenza: {extracted['city']}")
                    break

        # Gestione "dove vivo tuttora" = stessa città
        if 'tuttora' in text_lower and 'birth_city' in extracted and 'city' not in extracted:
            extracted['city'] = extracted['birth_city']
            print(f"🔍 DEBUG: Stessa città (tuttora): {extracted['city']}")

        # ESTRAZIONE ALTEZZA E PESO
        height_patterns = [
            r'alto\s+(\d+)\s*cm',
            r'alta\s+(\d+)\s*cm',
            r'altezza\s+(\d+)',
            r'(\d+)\s*cm(?:\s+e\s+peso)'
        ]

        for pattern in height_patterns:
            match = re.search(pattern, text_lower)
            if match:
                height = int(match.group(1))
                if 120 <= height <= 250:
                    extracted['height'] = str(height)
                    print(f"🔍 DEBUG: Altezza: {height} cm")
                    break

        weight_patterns = [
            r'peso\s+(\d+)\s*kg',
            r'(\d+)\s*kg(?:\s*$|\s*\.)',
            r'peso\s+(\d+)'
        ]

        for pattern in weight_patterns:
            match = re.search(pattern, text_lower)
            if match:
                weight = int(match.group(1))
                if 30 <= weight <= 300:
                    extracted['weight'] = str(weight)
                    print(f"🔍 DEBUG: Peso: {weight} kg")
                    break

        print(f"🔍 DEBUG: Dati estratti finali: {extracted}")
        return extracted

    def _check_missing_first_data(self, data):
        """Controlla quali dati del primo messaggio mancano"""
        required_fields = ['name', 'surname', 'email', 'sex', 'birth_city', 'city', 'height', 'weight']
        missing = []

        for field in required_fields:
            if field not in data or not data[field]:
                missing.append(field)

        # Logica speciale per età/data di nascita
        has_birth_date = 'birth_date' in data and data['birth_date']
        has_age = 'age' in data and data['age']

        if not has_birth_date and not has_age:
            missing.append('birth_date_or_age')

        return missing

    def _complete_first_data_collection(self):
        """Completa la raccolta dei primi dati e passa al motivo della visita"""
        self.registration_data.update(self.partial_first_data)
        self._populate_patient_first_data()

        # Calcola l'età se abbiamo la data di nascita ma non l'età
        age_calculation_message = ""
        if 'birth_date' in self.partial_first_data and 'age' not in self.partial_first_data:
            calculated_age = calculate_age_from_birthdate(self.partial_first_data['birth_date'])
            if calculated_age:
                self.registration_data['age'] = calculated_age
                self.patient.set_age(calculated_age)
                age_calculation_message = f"\n💡 Ho calcolato automaticamente che hai {calculated_age} anni dalla tua data di nascita."

        # Calcola codice fiscale se possibile
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

        self.current_phase = "collect_purpose"

        purpose_message = f"""
Perfetto!{age_calculation_message}

Ora dimmi: **qual è il motivo per cui desideri consultare un medico?**

Descrivi liberamente il tuo problema, i sintomi che avverti, o quello che ti preoccupa.
Più dettagli mi fornisci, meglio posso aiutarti a trovare lo specialista giusto.
        """

        return False, purpose_message.strip(), None

    def _process_missing_first_data(self, user_input):
        """Processa i dati mancanti del primo messaggio"""
        self.first_data_attempts += 1

        if self.first_data_attempts > self.max_attempts:
            return self._handle_structured_input_first_data(user_input)

        additional_data = self._extract_first_data(user_input)
        if not additional_data and self.missing_fields:
            additional_data = self._extract_single_field(user_input)

        self.partial_first_data.update(additional_data)
        missing_data = self._check_missing_first_data(self.partial_first_data)

        if missing_data:
            self.missing_fields = missing_data

            if self.first_data_attempts == self.max_attempts:
                missing_message = f"""
Mi mancano ancora questi dati:

{self._format_missing_data(missing_data)}

⚠️ Se ho difficoltà a capire la prossima volta, ti chiederò di usare un formato più semplice.
                """
            else:
                missing_message = f"""
Mi mancano ancora questi dati:

{self._format_missing_data(missing_data)}
                """
            return False, missing_message.strip(), None
        else:
            return self._complete_first_data_collection()

    def _extract_single_field(self, user_input):
        """Estrae singoli campi quando mancano specifici dati"""
        extracted = {}
        user_input_clean = user_input.strip()

        if len(self.missing_fields) == 1:
            field = self.missing_fields[0]

            if field == 'name':
                # Pattern per nome singolo
                name_patterns = [
                    r'^([A-Za-zÀ-ÿ\']+)$',  # Solo il nome
                    r'(?:nome|chiamo)\s+(?:è\s+)?([A-Za-zÀ-ÿ\']+)',
                    r'sono\s+([A-Za-zÀ-ÿ\']+)',
                    r'mi chiamo\s+([A-Za-zÀ-ÿ\']+)'
                ]

                for pattern in name_patterns:
                    match = re.search(pattern, user_input_clean, re.IGNORECASE)
                    if match:
                        name_candidate = match.group(1).strip()
                        if len(name_candidate) > 1 and name_candidate.isalpha():
                            extracted['name'] = name_candidate.title()
                            print(f"🔍 DEBUG: Nome estratto singolo: {extracted['name']}")
                            break

            if field == 'email':
                email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', user_input_clean)
                if email_match:
                    extracted['email'] = email_match.group(1).lower()

            elif field == 'surname':
                # Pattern per cognome singolo
                surname_patterns = [
                    r'^([A-Za-zÀ-ÿ\']+(?:\s+[A-Za-zÀ-ÿ\']+)*)$',  # Solo il cognome
                    r'cognome\s+(?:è\s+)?([A-Za-zÀ-ÿ\']+(?:\s+[A-Za-zÀ-ÿ\']+)*)',
                    r'di cognome\s+([A-Za-zÀ-ÿ\']+(?:\s+[A-Za-zÀ-ÿ\']+)*)'
                ]

                for pattern in surname_patterns:
                    match = re.search(pattern, user_input_clean, re.IGNORECASE)
                    if match:
                        surname_candidate = match.group(1).strip()
                        if len(surname_candidate) > 1 and surname_candidate.replace(' ', '').isalpha():
                            extracted['surname'] = surname_candidate.title()
                            print(f"🔍 DEBUG: Cognome estratto singolo: {extracted['surname']}")
                            break

            elif field == 'birth_date_or_age':
                parsed_date = parse_date_italian(user_input_clean)
                if parsed_date:
                    extracted['birth_date'] = parsed_date
                    calculated_age = calculate_age_from_birthdate(parsed_date)
                    if calculated_age:
                        extracted['age'] = calculated_age
                        extracted['age_calculated_from_birthdate'] = True
                else:
                    age_match = re.search(r'(\d+)', user_input_clean)
                    if age_match:
                        age = int(age_match.group(1))
                        if 0 < age < 120:
                            extracted['age'] = age
                            birth_date_approx = calculate_birth_date_from_age(age)
                            if birth_date_approx:
                                extracted['birth_date'] = birth_date_approx
                                extracted['birth_date_calculated_from_age'] = True

            elif field in ['city', 'birth_city']:
                if user_input_clean.replace(' ', '').isalpha():
                    extracted[field] = user_input_clean.title()

            elif field == 'height':
                height_match = re.search(r'(\d+)(?:\s*cm)?', user_input_clean)
                if height_match:
                    height = int(height_match.group(1))
                    if 120 <= height <= 250:
                        extracted['height'] = str(height)

            elif field == 'weight':
                weight_match = re.search(r'(\d+)(?:\s*kg)?', user_input_clean)
                if weight_match:
                    weight = int(weight_match.group(1))
                    if 30 <= weight <= 300:
                        extracted['weight'] = str(weight)

            elif field == 'sex':
                sex_lower = user_input_clean.lower()
                if sex_lower in ['m', 'maschio', 'uomo', 'male']:
                    extracted['sex'] = 'M'
                elif sex_lower in ['f', 'femmina', 'donna', 'female']:
                    extracted['sex'] = 'F'

        return extracted

    def _handle_structured_input_first_data(self, user_input):
        """Gestisce input strutturato per i dati del primo messaggio"""
        parsed_data = self._parse_comma_separated_input(user_input, self.missing_fields)

        if parsed_data:
            self.partial_first_data.update(parsed_data)
            missing_data = self._check_missing_first_data(self.partial_first_data)

            if not missing_data:
                return self._complete_first_data_collection()

        # Formato strutturato
        examples = []
        field_order = ['surname', 'email', 'birth_date_or_age', 'sex', 'birth_city', 'city', 'height', 'weight']

        for field in field_order:
            if field in self.missing_fields:
                if field == 'surname':
                    examples.append('Rossi')
                elif field == 'email':
                    examples.append('mario.rossi@email.com')
                elif field == 'birth_date_or_age':
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
Mi scuso, non riesco ancora a capire perfettamente!

Scrivi i dati mancanti separati da virgole:

{', '.join(examples[:len(self.missing_fields)])}
        """

        return False, structured_message.strip(), None

    def _parse_comma_separated_input(self, user_input, missing_fields):
        """Parsing di input separato da virgole per primi dati"""
        parsed = {}
        parts = [part.strip() for part in user_input.split(',')]

        field_order = ['surname', 'email', 'birth_date_or_age', 'sex', 'birth_city', 'city', 'height', 'weight']
        ordered_missing = [f for f in field_order if f in missing_fields]

        for i, part in enumerate(parts):
            if i < len(ordered_missing):
                field = ordered_missing[i]

                if field == 'email':
                    if '@' in part and '.' in part:
                        parsed['email'] = part.lower()
                elif field == 'surname':
                    if len(part) > 1:
                        parsed['surname'] = part.title()
                elif field == 'birth_date_or_age':
                    parsed_date = parse_date_italian(part)
                    if parsed_date:
                        parsed['birth_date'] = parsed_date
                        calculated_age = calculate_age_from_birthdate(parsed_date)
                        if calculated_age:
                            parsed['age'] = calculated_age
                            parsed['age_calculated_from_birthdate'] = True
                    else:
                        age_match = re.search(r'(\d+)', part)
                        if age_match:
                            age = int(age_match.group(1))
                            if 0 < age < 120:
                                parsed['age'] = age
                                birth_date_approx = calculate_birth_date_from_age(age)
                                if birth_date_approx:
                                    parsed['birth_date'] = birth_date_approx
                                    parsed['birth_date_calculated_from_age'] = True
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

        return parsed

    def _process_purpose_message(self, user_input):
        """Processa il messaggio con il motivo della visita"""
        self.registration_data['purpose'] = user_input
        self.patient.set_purpose(user_input)

        self.current_phase = "collect_clinical_data"

        clinical_data_message = """
Grazie per aver condiviso il motivo della tua visita.

Ora, per completare la tua cartella clinica, mi servirebbe che mi parlassi del tuo stile di vita e della tua salute in generale.

Dimmi tutto quello che riesci in un messaggio naturale:

**Allergie e dieta:**
- Eventuali allergie (alimentari, farmaci, etc.) - se non ne hai scrivi "nessuna"
- Che tipo di dieta segui (mediterranea, vegana, vegetariana, normale, etc.)

**Stile di vita:**
- Che attività sportiva fai e quanto spesso (es. "palestra 3 volte a settimana", "cammino ogni giorno", "non faccio sport")
- Con che intensità pratichi sport (leggera, moderata, intensa)
- Quante ore dormi di solito ogni notte
- Quanto spesso bevi alcolici (mai, raramente, occasionalmente, regolarmente)
- Fumi? (mai, occasionalmente, regolarmente, ex fumatore)

Puoi scrivere tutto insieme in modo naturale come preferisci!
        """

        return False, clinical_data_message.strip(), None

    def _process_clinical_data_message(self, user_input):
        """Processa il messaggio con i dati clinici"""
        extracted_clinical = self._extract_clinical_data(user_input)
        missing_clinical = self._check_missing_clinical_data(extracted_clinical)

        if missing_clinical:
            self.current_phase = "collect_missing_clinical_data"
            self.missing_clinical_fields = missing_clinical
            self.partial_clinical_data = extracted_clinical

            missing_message = f"""
Grazie! Mi mancano ancora alcune informazioni:

{self._format_missing_clinical_data(missing_clinical)}

Puoi fornirmele?
            """

            return False, missing_message.strip(), None
        else:
            self.registration_data.update(extracted_clinical)
            self._populate_patient_clinical_data()

            self.current_phase = "preference_questions"
            self.current_step = 0

            pref_intro = """
Perfetto! Ora, per trovare il medico più adatto a te, vorrei capire le tue preferenze.

Ti farò alcune domande su cosa è importante per te nella scelta del medico.
            """

            return False, pref_intro.strip(), self._get_current_question()

    def _extract_clinical_data(self, text):
        """Estrae i dati clinici dal messaggio"""
        extracted = {}
        text_lower = text.lower()

        # Estrazione allergie
        if 'non ho allergie' in text_lower or 'nessuna allergia' in text_lower or 'allergie nessuna' in text_lower:
            extracted['allergies'] = 'Nessuna'
        else:
            allergie_patterns = [
                r'allergie?:?\s*(.*?)(?:\s*\.|$|\s*,\s*(?:dieta|diet|mangio))',
                r'allergico?\s+a\s+(.*?)(?:\s*\.|$|\s*,)',
                r'allergia\s+a\s+(.*?)(?:\s*\.|$|\s*,)'
            ]

            for pattern in allergie_patterns:
                match = re.search(pattern, text_lower)
                if match:
                    allergie_text = match.group(1).strip()
                    if allergie_text and len(allergie_text) > 1:
                        extracted['allergies'] = self._parse_allergies_list(allergie_text)
                        break

        # Estrazione dieta
        diet_patterns = [
            r'dieta\s+(.*?)(?:\s*\.|$|\s*,)',
            r'seguo.*?dieta\s+(.*?)(?:\s*\.|$|\s*,)',
            r'mangio\s+(.*?)(?:\s*\.|$|\s*,)',
            r'alimentazione\s+(.*?)(?:\s*\.|$|\s*,)'
        ]

        for pattern in diet_patterns:
            match = re.search(pattern, text_lower)
            if match:
                diet_text = match.group(1).strip()
                if diet_text and len(diet_text) > 1:
                    extracted['diet'] = diet_text
                    break

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

        # Estrazione intensità
        intensity_patterns = [
            (r'intensità.*?(leggera|bassa)', 'leggera'),
            (r'intensità.*?(moderata|media)', 'moderata'),
            (r'intensità.*?(intensa|alta|vigorosa)', 'intensa'),
            (r'leggera|blanda|soft', 'leggera'),
            (r'moderata|media|normale', 'moderata'),
            (r'intensa|forte|vigorosa|pesante|alta', 'intensa')
        ]

        for pattern, intensity in intensity_patterns:
            if re.search(pattern, text_lower):
                extracted['physical_activity_intensity'] = intensity
                break

        if extracted.get('physical_activity_frequency') == 'mai':
            extracted['physical_activity_intensity'] = ''

        # Estrazione ore di sonno
        sleep_patterns = [
            r'dormo (\d+)\s*ore',
            r'(\d+)\s*ore.*?sonno',
            r'(\d+)\s*ore.*?notte',
            r'sonno.*?(\d+)\s*ore'
        ]

        for pattern in sleep_patterns:
            match = re.search(pattern, text_lower)
            if match:
                hours = int(match.group(1))
                if 4 <= hours <= 12:
                    extracted['sleep_hours'] = hours
                    break

        # Estrazione alcol
        alcohol_patterns = [
            (r'non bevo|mai alcol|astemio', 'mai'),
            (r'raramente|quasi mai', 'raramente'),
            (r'occasionalmente|qualche volta|weekend', 'occasionalmente'),
            (r'regolarmente|spesso|tutti i giorni', 'regolarmente')
        ]

        for pattern, frequency in alcohol_patterns:
            if re.search(pattern, text_lower):
                extracted['alcohol_frequency'] = frequency
                break

        # Estrazione fumo
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

        return extracted

    def _parse_allergies_list(self, allergie_text):
        """Parsing intelligente delle allergie"""
        allergie_text = allergie_text.strip()

        if allergie_text.lower() in ['nessuna', 'no', 'nessuno', 'niente']:
            return 'Nessuna'

        separators = [r',\s*e\s+', r'\s+e\s+', r',\s*', r';\s*']

        for sep in separators:
            allergie_text = re.sub(sep, ',', allergie_text)

        allergie_list = [a.strip() for a in allergie_text.split(',') if a.strip()]

        seen = set()
        unique_allergie = []
        for allergia in allergie_list:
            allergia_clean = allergia.lower().strip()
            if allergia_clean not in seen and allergia_clean:
                seen.add(allergia_clean)
                unique_allergie.append(allergia.title())

        return ', '.join(unique_allergie) if unique_allergie else 'Nessuna'

    def _check_missing_clinical_data(self, data):
        """Controlla quali dati clinici mancano"""
        required_fields = ['allergies', 'diet', 'physical_activity_frequency', 'physical_activity_intensity',
                           'sleep_hours', 'alcohol_frequency', 'smoking_frequency']
        missing = []

        for field in required_fields:
            if field not in data or data[field] == '' or data[field] is None:
                if field == 'physical_activity_intensity' and data.get('physical_activity_frequency') == 'mai':
                    continue
                missing.append(field)

        return missing

    def _process_missing_clinical_data(self, user_input):
        """Processa i dati clinici mancanti"""
        self.clinical_data_attempts += 1

        if self.clinical_data_attempts > self.max_attempts:
            return self._handle_structured_clinical_input(user_input)

        additional_data = self._extract_clinical_data(user_input)
        self.partial_clinical_data.update(additional_data)

        missing_clinical = self._check_missing_clinical_data(self.partial_clinical_data)

        if missing_clinical:
            self.missing_clinical_fields = missing_clinical

            if self.clinical_data_attempts == self.max_attempts:
                missing_message = f"""
Mi mancano ancora questi dati:

{self._format_missing_clinical_data(missing_clinical)}

⚠️ Se ho difficoltà a capire la prossima volta, ti chiederò di usare un formato più semplice.
                """
            else:
                missing_message = f"""
Mi mancano ancora questi dati:

{self._format_missing_clinical_data(missing_clinical)}
                """

            return False, missing_message.strip(), None
        else:
            self.registration_data.update(self.partial_clinical_data)
            self._populate_patient_clinical_data()

            self.current_phase = "preference_questions"
            self.current_step = 0

            pref_intro = """
Perfetto! Ora, per trovare il medico più adatto a te, vorrei capire le tue preferenze.

Ti farò alcune domande su cosa è importante per te nella scelta del medico.
            """

            return False, pref_intro.strip(), self._get_current_question()

    def _handle_structured_clinical_input(self, user_input):
        """Gestisce input strutturato per dati clinici"""
        parsed_data = self._parse_comma_separated_clinical_input(user_input, self.missing_clinical_fields)

        if parsed_data:
            self.partial_clinical_data.update(parsed_data)
            missing_clinical = self._check_missing_clinical_data(self.partial_clinical_data)

            if not missing_clinical:
                self.registration_data.update(self.partial_clinical_data)
                self._populate_patient_clinical_data()

                self.current_phase = "preference_questions"
                self.current_step = 0

                pref_intro = """
Perfetto! Ora, per trovare il medico più adatto a te, vorrei capire le tue preferenze.

Ti farò alcune domande su cosa è importante per te nella scelta del medico.
                """

                return False, pref_intro.strip(), self._get_current_question()

        # Formato strutturato
        examples = []
        clinical_order = ['allergies', 'diet', 'physical_activity_frequency', 'physical_activity_intensity',
                          'sleep_hours', 'alcohol_frequency', 'smoking_frequency']

        for field in clinical_order:
            if field in self.missing_clinical_fields:
                if field == 'allergies':
                    examples.append('nessuna')
                elif field == 'diet':
                    examples.append('mediterranea')
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
Mi scuso, non riesco ancora a capire perfettamente!

Scrivi i dati mancanti separati da virgole:

{', '.join(examples[:len(self.missing_clinical_fields)])}
        """

        return False, structured_message.strip(), None

    def _parse_comma_separated_clinical_input(self, user_input, missing_fields):
        """Parsing di input separato da virgole per dati clinici"""
        parsed = {}
        parts = [part.strip() for part in user_input.split(',')]

        clinical_order = ['allergies', 'diet', 'physical_activity_frequency', 'physical_activity_intensity',
                          'sleep_hours', 'alcohol_frequency', 'smoking_frequency']
        ordered_missing = [f for f in clinical_order if f in missing_fields]

        for i, part in enumerate(parts):
            if i < len(ordered_missing):
                field = ordered_missing[i]
                part_lower = part.lower()

                if field == 'allergies':
                    parsed['allergies'] = self._parse_allergies_list(part)
                elif field == 'diet':
                    parsed['diet'] = part.lower()
                elif field == 'physical_activity_frequency':
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

    def _check_existing_registrations(self):
        """
        Controlla se email o codice fiscale sono già registrati

        Returns:
            tuple: (email_exists, fiscal_code_exists)
        """
        email_exists = False
        fiscal_code_exists = False

        if 'email' in self.registration_data:
            email_exists = self.patient_db.check_email_exists(self.registration_data['email'])

        if 'fiscal_code' in self.registration_data:
            fiscal_code_exists = self.patient_db.check_fiscal_code_exists(self.registration_data['fiscal_code'])

        return email_exists, fiscal_code_exists

    def _complete_registration(self):
        """
        Completa la registrazione con il nuovo sistema di sicurezza - SENZA raccomandazione automatica medico
        """
        try:
            # Controlla duplicati prima di procedere
            email_exists, fiscal_code_exists = self._check_existing_registrations()

            if email_exists:
                return False, "❌ Questa email è già registrata nel sistema. Prova ad effettuare il login.", None

            if fiscal_code_exists:
                return False, "❌ Questo codice fiscale è già registrato nel sistema.", None

            # Popola tutti i dati del paziente
            self._populate_patient_all_data()

            # Crea le note complete
            complete_notes = self._create_complete_notes()
            self.patient.set_additional_notes(complete_notes)

            # Salva il paziente con il nuovo sistema di sicurezza
            patient_id, generated_password = self.patient_db.save_patient(self.patient)

            if patient_id and generated_password:
                # Salva le credenziali per mostrarle all'utente
                self.patient_document_id = patient_id
                self.generated_password = generated_password

                # ✅ MODIFICA: Rimuovi il messaggio sulla ricerca del medico
                success_message = f"""
    ✅ Registrazione completata con successo!

    🔐 **CREDENZIALI DI ACCESSO IMPORTANTI:**
    📧 Email: {self.patient.get_email()}
    🔑 Password: {generated_password}

    ⚠️  **IMPORTANTE**: Salva queste credenziali in un posto sicuro!
    La password è stata generata automaticamente e ti servirà per accedere al sistema.

    Il tuo profilo è stato salvato correttamente nel sistema.
    Ora puoi utilizzare tutte le funzionalità di Longeviva!
                """

                return True, success_message.strip(), None
            else:
                return False, "Errore nel salvataggio. Riprova.", None

        except Exception as e:
            print(f"❌ Errore nella registrazione: {e}")
            return False, "Si è verificato un errore. Riprova.", None

    def get_generated_credentials(self):
        """
        Restituisce le credenziali generate per l'utente

        Returns:
            tuple: (email, password, document_id)
        """
        return (
            self.patient.get_email() if self.patient else None,
            self.generated_password,
            self.patient_document_id
        )

    def _populate_patient_first_data(self):
        """Popola i dati del primo messaggio nel paziente"""
        data = self.registration_data

        if 'name' in data:
            self.patient.set_name(data['name'])
        if 'surname' in data:
            self.patient.set_surname(data['surname'])
        if 'email' in data:
            self.patient.set_contact_info(email=data['email'])
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

    def _populate_patient_clinical_data(self):
        """Popola i dati clinici nel paziente"""
        data = self.registration_data

        if 'allergies' in data:
            self.patient.set_allergies(data['allergies'])

        # Recupera il lifestyle esistente o crea nuovo
        existing_lifestyle = self.patient.get_lifestyle() or {}

        # Mappa i campi lifestyle
        lifestyle_mapping = {
            'diet': 'typeOfDiet',
            'physical_activity_frequency': 'physicalActivityFrequency',
            'physical_activity_intensity': 'physicalActivityIntensity',
            'sleep_hours': 'hoursOfSleep',
            'alcohol_frequency': 'alcoholFrequency',
            'smoking_frequency': 'smokerFrequency'
        }

        # Aggiorna lifestyle con i nuovi dati
        for extracted_field, model_field in lifestyle_mapping.items():
            if extracted_field in data:
                existing_lifestyle[model_field] = data[extracted_field]

        # Imposta lifestyle completo
        self.patient.set_lifestyle(existing_lifestyle)
        print(f"🔍 DEBUG: Lifestyle completo impostato: {existing_lifestyle}")

    def _populate_patient_all_data(self):
        """Popola tutti i dati del paziente"""
        self._populate_patient_first_data()
        self._populate_patient_clinical_data()

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
        name = self.patient.get_name() if self.patient and self.patient.get_name() else "L'utente"

        summary_parts = []

        # Messaggio di apertura personalizzato
        display_name = name.replace("L'utente", "utente") if name == "L'utente" else name
        summary_parts.append(f"Perfetto, {display_name}! Ho capito cosa ti ha portato qui:")

        # Crea un resoconto narrativo
        if 'download_reason' in self.motivation_data:
            reasons = self.motivation_data['download_reason']
            reason_transformations = {
                "Voglio migliorare il mio stile di vita con un supporto pratico e costante": "vuoi migliorare il tuo stile di vita con un supporto pratico e costante",
                "Ho bisogno di un aiuto concreto per rimettermi in forma": "hai bisogno di un aiuto concreto per rimetterti in forma",
                "Cerco un modo semplice per mangiare meglio e muovermi di più": "cerchi un modo semplice per mangiare meglio e muoverti di più",
                "Mi interessa la longevità e voglio prendermi cura della mia salute oggi": "sei interessato alla longevità e vuoi prenderti cura della tua salute oggi",
                "Mi ha incuriosito l'approccio innovativo con l'AI e la community": "sei incuriosito dall'approccio innovativo con l'AI e la community"
            }

            transformed_reasons = [reason_transformations.get(r, r.lower()) for r in reasons]

            if len(transformed_reasons) == 1:
                reason_text = f"Hai scelto Longeviva perché {transformed_reasons[0]}."
            elif len(transformed_reasons) == 2:
                reason_text = f"Hai scelto Longeviva perché {transformed_reasons[0]} e {transformed_reasons[1]}."
            else:
                reason_text = f"Hai scelto Longeviva perché {', '.join(transformed_reasons[:-1])} e {transformed_reasons[-1]}."
            summary_parts.append(reason_text)

        if 'objectives' in self.motivation_data:
            objectives = self.motivation_data['objectives']
            objective_transformations = {
                "Perdere peso in modo sano e sostenibile": "perdere peso in modo sano e sostenibile",
                "Avere più energia durante la giornata": "avere più energia durante la giornata",
                "Migliorare la mia composizione corporea": "migliorare la tua composizione corporea",
                "Aumentare la mia consapevolezza alimentare": "aumentare la tua consapevolezza alimentare",
                "Vivere più a lungo e in salute": "vivere più a lungo e in salute",
                "Sentirmi meglio fisicamente e mentalmente": "sentirti meglio fisicamente e mentalmente"
            }

            transformed_objectives = [objective_transformations.get(o, o.lower()) for o in objectives]

            if len(transformed_objectives) == 1:
                obj_text = f"Il tuo obiettivo principale è {transformed_objectives[0]}."
            elif len(transformed_objectives) == 2:
                obj_text = f"I tuoi obiettivi principali sono {transformed_objectives[0]} e {transformed_objectives[1]}."
            else:
                obj_text = f"I tuoi obiettivi principali sono {', '.join(transformed_objectives[:-1])} e {transformed_objectives[-1]}."
            summary_parts.append(obj_text)

        if 'expectations' in self.motivation_data:
            expectations = self.motivation_data['expectations']
            expectation_transformations = {
                "Un percorso personalizzato e facile da seguire": "un percorso personalizzato e facile da seguire",
                "Consigli pratici, non complicati": "consigli pratici, non complicati",
                "Sentirmi seguito/a da chi capisce le mie esigenze": "sentirti seguito da chi capisce le tue esigenze",
                "Imparare abitudini che durino nel tempo": "imparare abitudini che durino nel tempo",
                "Un'esperienza motivante che mi tenga attivo/a e coinvolto/a": "un'esperienza motivante che ti tenga attivo e coinvolto"
            }

            transformed_expectations = [expectation_transformations.get(e, e.lower()) for e in expectations]

            if len(transformed_expectations) == 1:
                exp_text = f"Ti aspetti {transformed_expectations[0]}."
            elif len(transformed_expectations) == 2:
                exp_text = f"Ti aspetti {transformed_expectations[0]} e {transformed_expectations[1]}."
            else:
                exp_text = f"Ti aspetti {', '.join(transformed_expectations[:-1])} e {transformed_expectations[-1]}."
            summary_parts.append(exp_text)

        return "\n\n".join(summary_parts)

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

    def _format_missing_data(self, missing_fields):
        """Formatta l'elenco dei dati mancanti del primo messaggio"""
        field_names = {
            'name': 'Nome',
            'surname': 'Cognome',
            'email': 'Email (per accesso al sistema)',
            'birth_date_or_age': 'Data di nascita (DD/MM/YYYY o "28 gennaio 1990") oppure età',
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

    def _format_missing_clinical_data(self, missing_fields):
        """Formatta l'elenco dei dati clinici mancanti"""
        field_names = {
            'allergies': 'Allergie (o scrivi "nessuna")',
            'diet': 'Tipo di dieta',
            'physical_activity_frequency': 'Frequenza attività fisica (es. "3 volte a settimana", "mai")',
            'physical_activity_intensity': 'Intensità attività fisica (leggera, moderata, intensa)',
            'sleep_hours': 'Ore di sonno per notte (es. "7")',
            'alcohol_frequency': 'Frequenza consumo alcol (mai, raramente, occasionalmente, regolarmente)',
            'smoking_frequency': 'Abitudine al fumo (mai, occasionalmente, regolarmente, ex fumatore)'
        }

        return '\n'.join([f"• {field_names.get(field, field)}" for field in missing_fields])

    def get_preferences(self):
        """Restituisce le preferenze raccolte per la ricerca semantica"""
        return self.preferences_data

    def get_motivation_data(self):
        """Restituisce i dati motivazionali per la ricerca semantica"""
        return self.motivation_data