import warnings
import sys
import os
import re
import traceback
import random
from datetime import datetime
from difflib import SequenceMatcher
from collections import defaultdict
import unicodedata
from typing import Dict, List, Tuple, Optional

# Aggiungi percorsi per import
current_dir = os.path.dirname(__file__)
src_dir = os.path.dirname(current_dir)
sys.path.insert(0, src_dir)

# Sopprime gli avvisi di Firebase
warnings.filterwarnings("ignore", category=UserWarning, module="google.cloud.firestore_v1.base_collection")

# Import moduli
from LLM.llm_instance import LLM
from Doctor.doctors_handler import DoctorHandler
from Patient.patients_handler import PatientHandler
from Patient.patient_instance import Patient
from Doctor.doctor_instance import Doctor, create_sample_doctors

# Import utility per registrazione
try:
    from utils.registration_handler import RegistrationHandler
except ImportError:
    print("⚠️ RegistrationHandler non trovato - uso registrazione semplice")
    RegistrationHandler = None


def get_best_doctor_for_purpose(doctors, purpose, city=None, preferences=None):
    """Trova il miglior medico per il problema specificato - VERSIONE MIGLIORATA"""
    if not doctors:
        return None, "Medicina Generale"

    purpose_lower = purpose.lower()

    # Mapping problema-specialista MIGLIORATO
    specialty_keywords = {
        'cardiologia': ['cuore', 'petto', 'battiti', 'pressione', 'tachicardia', 'aritmia', 'cardiovascolare',
                        'infarto', 'angina'],
        'dermatologia': ['pelle', 'macchie', 'brufoli', 'acne', 'prurito', 'dermatite', 'eczema', 'psoriasi', 'cute',
                         'lesioni'],
        'neurologia': ['mal di testa', 'emicrania', 'vertigini', 'tremori', 'cefalea', 'neurologico', 'nervi',
                       'sclerosi', 'epilessia'],
        'ortopedia': ['ossa', 'fratture', 'ginocchio', 'schiena', 'articolazioni', 'muscoli', 'postura', 'lombalgia',
                      'cervicale'],
        'oculistica': ['occhi', 'vista', 'miopia', 'glaucoma', 'cataratta', 'oculare', 'visione', 'retina',
                       'presbiopia'],
        'gastroenterologia': ['stomaco', 'digestione', 'gastrite', 'intestino', 'addome', 'nausea', 'colite',
                              'reflusso'],
        'psichiatria': ['depressione', 'ansia', 'stress', 'panico', 'mentale', 'psicologico', 'umore', 'disturbi'],
        'pneumologia': ['polmoni', 'respirazione', 'tosse', 'asma', 'bronchi', 'respiro', 'fiato', 'bronchite'],
        'urologia': ['reni', 'vescica', 'urinario', 'prostata', 'calcoli', 'cistite'],
        'ginecologia': ['ginecologico', 'mestruazioni', 'gravidanza', 'utero', 'ovaie', 'ciclo', 'femminile'],
        'pediatria': ['bambino', 'bambini', 'pediatrico', 'infanzia', 'neonato', 'crescita'],
        'endocrinologia': ['tiroide', 'diabete', 'ormoni', 'metabolismo', 'endocrino', 'glicemia', 'insulina']
    }

    # Trova la specializzazione migliore
    best_score = 0
    best_specialty = "medicina generale"

    for specialty, keywords in specialty_keywords.items():
        score = sum(1 for keyword in keywords if keyword in purpose_lower)
        if score > best_score:
            best_score = score
            best_specialty = specialty

    # FALLBACK PRIORITARIO: Medicina generale nella stessa città
    if city and best_score == 0:  # Nessuna specializzazione identificata
        city_general_doctors = []
        for d in doctors:
            spec_lower = d.get_specialization().lower()
            city_match = (hasattr(d, 'city_of_work') and d.city_of_work and
                          d.city_of_work.lower() == city.lower()) or \
                         (d.get_city() and d.get_city().lower() == city.lower())

            if ("generale" in spec_lower or "family" in spec_lower) and city_match:
                city_general_doctors.append(d)

        if city_general_doctors:
            return city_general_doctors[0], "Medicina Generale"

    # Filtra medici per specializzazione
    matching_doctors = [
        d for d in doctors
        if best_specialty.lower() in d.get_specialization().lower()
    ]

    if matching_doctors:
        # Priorità per città se specificata
        if city:
            city_doctors = []
            for d in matching_doctors:
                city_match = (hasattr(d, 'city_of_work') and d.city_of_work and
                              d.city_of_work.lower() == city.lower()) or \
                             (d.get_city() and d.get_city().lower() == city.lower())
                if city_match:
                    city_doctors.append(d)

            if city_doctors:
                return city_doctors[0], best_specialty.title()

        return matching_doctors[0], best_specialty.title()

    # Fallback: medicina generale (qualsiasi città)
    general_doctors = [d for d in doctors
                       if "generale" in d.get_specialization().lower()]
    if general_doctors:
        # Priorità alla stessa città anche nel fallback
        if city:
            city_general = []
            for d in general_doctors:
                city_match = (hasattr(d, 'city_of_work') and d.city_of_work and
                              d.city_of_work.lower() == city.lower()) or \
                             (d.get_city() and d.get_city().lower() == city.lower())
                if city_match:
                    city_general.append(d)

            if city_general:
                return city_general[0], "Medicina Generale"

        return general_doctors[0], "Medicina Generale"

    return doctors[0], doctors[0].get_specialization()


def find_doctors_near_patient(doctors, city, specialization, max_results=3):
    """Trova medici vicini al paziente"""
    if not doctors:
        return []

    if city:
        city_doctors = []
        for d in doctors:
            city_match = (hasattr(d, 'city_of_work') and d.city_of_work and
                          d.city_of_work.lower() == city.lower()) or \
                         (d.get_city() and d.get_city().lower() == city.lower())
            if city_match:
                city_doctors.append(d)

        return city_doctors[:max_results]

    return doctors[:max_results]


def get_doctors_statistics(doctors):
    """Genera statistiche sui medici"""
    if not doctors:
        return {
            'total_doctors': 0,
            'specializations': {},
            'cities': {},
            'average_experience': 0,
            'most_common_specialization': 'N/A'
        }

    specializations = {}
    cities = {}
    total_experience = 0

    for doc in doctors:
        spec = doc.get_specialization()
        city = getattr(doc, 'city_of_work', doc.get_city())
        exp = doc.get_years_of_experience()

        specializations[spec] = specializations.get(spec, 0) + 1
        cities[city] = cities.get(city, 0) + 1
        total_experience += exp

    most_common_spec = max(specializations.items(), key=lambda x: x[1])[0] if specializations else 'N/A'

    return {
        'total_doctors': len(doctors),
        'specializations': specializations,
        'cities': cities,
        'average_experience': total_experience / len(doctors),
        'most_common_specialization': most_common_spec
    }


class IntelligentInputClassifier:
    """
    Sistema di classificazione intelligente che impara dai pattern esistenti
    e si adatta automaticamente ai typo senza dizionari hardcoded.
    """

    def __init__(self):
        # Estrae automaticamente keywords dai pattern esistenti
        self.learned_keywords = self._extract_keywords_from_patterns()
        self.similarity_threshold = 0.75
        self.min_word_length = 4  # Solo parole >= 4 caratteri per fuzzy matching

    def _extract_keywords_from_patterns(self) -> Dict[str, List[str]]:
        """Estrae automaticamente le keywords dai pattern regex esistenti"""
        # Pattern esistenti dal codice originale
        existing_patterns = {
            'data_query': [
                r'\b(quando|che giorno|che data|in che anno|che anno)\s+(sono\s+nat[oa]|è\s+la\s+mia\s+nascita)',
                r'\b(qual\s*è|dimmi|mostra|visualizza)\s+(la\s+mia\s+|il\s+mio\s+)?(data\s+di\s+nascita|compleanno|età)',
                r'\b(quanti\s+anni\s+ho|che\s+età\s+ho)',
                r'\b(quanto\s+peso|qual\s*è\s+il\s+mio\s+peso|dimmi\s+il\s+peso)',
                r'\b(quanto\s+sono\s+alt[oa]|qual\s*è\s+la\s+mia\s+altezza)',
                r'\b(che\s+allergie\s+ho|quali\s+sono\s+le\s+mie\s+allergie)',
                r'\b(qual\s*è\s+la\s+mia\s+email|dimmi\s+la\s+mia\s+mail)',
                r'\b(dimmi\s+i\s+miei\s+dati|mostra\s+profilo)',
            ],
            'medical_request': [
                r'\b(ho\s+mal\s+di|mi\s+fa\s+male|sento\s+dolore)',
                r'\b(ho\s+la\s+febbre|ho\s+temperatura|mi\s+sento\s+male)',
                r'\b(ho\s+tosse|tossisco|respiro\s+male)',
                r'\b(ho\s+nausea|vomito|stomaco)',
                r'\b(ho\s+problemi\s+di|soffro\s+di)',
            ],
            'appointment_related': [
                r'\b(prenota|prenotare|appuntamento|visita)',
                r'\b(quando\s+posso\s+vedere|disponibilità)',
                r'\b(vorrei\s+fissare|voglio\s+fissare)',
            ]
        }

        keywords = defaultdict(set)

        for category, patterns in existing_patterns.items():
            for pattern in patterns:
                # Estrae parole significative dai pattern regex
                words = self._extract_words_from_regex(pattern)
                keywords[category].update(words)

        # Converte set in list per facilità d'uso
        return {cat: list(words) for cat, words in keywords.items()}

    def _extract_words_from_regex(self, pattern: str) -> List[str]:
        """Estrae parole significative da un pattern regex"""
        # Rimuove caratteri regex e estrae parole
        clean_pattern = re.sub(r'[\\()\[\]{}^$*+?.|]', ' ', pattern)
        clean_pattern = re.sub(r'\\[bswdBSWD]', ' ', clean_pattern)

        words = []
        for word in clean_pattern.split():
            # Filtra solo parole alfabetiche significative
            if (len(word) >= 3 and
                    word.isalpha() and
                    word not in ['che', 'del', 'mio', 'mia', 'una', 'sono', 'hai', 'può']):
                words.append(word.lower())

        return words

    def _normalize_text(self, text: str) -> str:
        """Normalizza il testo rimuovendo accenti e caratteri speciali"""
        # Rimuove accenti
        text = unicodedata.normalize('NFD', text)
        text = ''.join(char for char in text if unicodedata.category(char) != 'Mn')

        # Converte a lowercase e rimuove punteggiatura
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        text = re.sub(r'\s+', ' ', text.strip())

        return text

    def _find_closest_match(self, word: str, candidates: List[str]) -> Optional[Tuple[str, float]]:
        """Trova la parola più simile usando fuzzy matching avanzato"""
        if len(word) < self.min_word_length:
            return None

        best_match = None
        best_score = 0

        for candidate in candidates:
            if len(candidate) < self.min_word_length:
                continue

            # Usa SequenceMatcher per similarità più precisa
            similarity = SequenceMatcher(None, word, candidate).ratio()

            # Bonus per lunghezza simile
            len_diff = abs(len(word) - len(candidate))
            len_penalty = len_diff / max(len(word), len(candidate))
            adjusted_similarity = similarity * (1 - len_penalty * 0.3)

            # Bonus se iniziano con stessa lettera
            if word[0] == candidate[0]:
                adjusted_similarity += 0.1

            if adjusted_similarity > best_score and adjusted_similarity >= self.similarity_threshold:
                best_score = adjusted_similarity
                best_match = candidate

        return (best_match, best_score) if best_match else None

    def _auto_correct_typos(self, text: str) -> Tuple[str, List[str]]:
        """Corregge automaticamente i typo usando fuzzy matching"""
        normalized = self._normalize_text(text)
        words = normalized.split()
        corrected_words = []
        corrections_made = []

        # Crea un pool di tutte le keywords conosciute
        all_keywords = []
        for keyword_list in self.learned_keywords.values():
            all_keywords.extend(keyword_list)

        for word in words:
            if len(word) >= self.min_word_length:
                match_result = self._find_closest_match(word, all_keywords)
                if match_result:
                    corrected_word, confidence = match_result
                    corrected_words.append(corrected_word)
                    corrections_made.append(f"{word} -> {corrected_word} ({confidence:.2f})")
                else:
                    corrected_words.append(word)
            else:
                corrected_words.append(word)

        corrected_text = ' '.join(corrected_words)
        return corrected_text, corrections_made

    def _calculate_category_score(self, text: str, category: str) -> float:
        """Calcola il punteggio di appartenenza a una categoria"""
        if category not in self.learned_keywords:
            return 0.0

        keywords = self.learned_keywords[category]
        text_words = set(text.split())

        # Punteggio basato su exact match
        exact_matches = len(text_words.intersection(set(keywords)))
        exact_score = exact_matches / len(keywords) if keywords else 0

        # Punteggio basato su fuzzy match
        fuzzy_score = 0
        fuzzy_matches = 0
        for text_word in text_words:
            for keyword in keywords:
                if len(text_word) >= self.min_word_length and len(keyword) >= self.min_word_length:
                    similarity = SequenceMatcher(None, text_word, keyword).ratio()
                    if similarity >= self.similarity_threshold:
                        fuzzy_score += similarity
                        fuzzy_matches += 1

        # Normalizza il fuzzy score per il numero di keywords, non per similarity totale
        fuzzy_score = fuzzy_matches / len(keywords) if keywords else 0

        # Combina i punteggi con peso maggiore per exact match
        combined_score = (exact_score * 0.7) + (fuzzy_score * 0.3)

        # BOOST per frasi specifiche molto comuni
        if category == 'data_query':
            # Frasi che sono chiaramente data_query
            data_phrases = [
                'data di nascita', 'quando nato', 'quando nata', 'che eta', 'quanti anni',
                'peso', 'altezza', 'allergie', 'profilo', 'dati', 'informazioni'
            ]

            text_lower = text.lower()
            for phrase in data_phrases:
                if phrase in text_lower:
                    combined_score += 0.5  # Boost significativo
                    break

        return min(combined_score, 1.0)  # Cap a 1.0

    def _detect_question_intent(self, text: str) -> bool:
        """Rileva se il testo è una domanda basandosi su pattern linguistici"""
        # Indicatori di domanda
        question_indicators = [
            text.strip().endswith('?'),
            any(word in text.lower() for word in ['quando', 'che', 'qual', 'quanti', 'dove', 'come', 'perché']),
            text.lower().startswith(('dimmi', 'mostra', 'visualizza', 'sai')),
        ]

        return any(question_indicators)

    def classify_input(self, user_input: str, debug: bool = True) -> str:
        """
        Classifica l'input dell'utente usando machine learning e pattern recognition
        """
        if debug:
            print(f"🧠 DEBUG: Input originale: '{user_input}'")

        # Step 1: Normalizza e correggi typo automaticamente
        corrected_text, corrections = self._auto_correct_typos(user_input)

        if debug and corrections:
            print(f"🔧 DEBUG: Correzioni automatiche: {corrections}")
            print(f"🔧 DEBUG: Testo corretto: '{corrected_text}'")

        # Step 2: Calcola punteggi per ogni categoria
        scores = {}
        for category in self.learned_keywords.keys():
            scores[category] = self._calculate_category_score(corrected_text, category)

        if debug:
            print(f"📊 DEBUG: Punteggi categorie: {scores}")

        # Step 3: Controlla pattern specifici per data_query PRIMA della logica generale
        corrected_lower = corrected_text.lower()
        original_lower = user_input.lower()

        # Pattern espliciti per data_query - QUESTI HANNO PRIORITÀ ASSOLUTA
        explicit_data_patterns = [
            # Peso
            r'\b(quanto\s+peso|peso|mio\s+peso|il\s+peso)\b',
            # Altezza
            r'\b(quanto\s+sono\s+alt[oa]|altezza|mia\s+altezza|alt[oa]\s+sono)\b',
            # Età
            r'\b(quanti\s+anni|che\s+età|mia\s+età|anni\s+ho)\b',
            # Data nascita
            r'\b(quando\s+(sono\s+)?nat[oa]|data\s+nascita|compleanno)\b',
            # Email/telefono
            r'\b(mia\s+email|mio\s+telefono|email|mail|numero)\b',
            # Allergie
            r'\b(allergie|allergico)\b',
            # Profilo generale
            r'\b(profilo|dati|informazioni\s+personali)\b'
        ]

        # Se trova un pattern esplicito, è sicuramente data_query
        for pattern in explicit_data_patterns:
            if re.search(pattern, corrected_lower) or re.search(pattern, original_lower):
                if debug:
                    print(f"✅ DEBUG: Trovato pattern esplicito data_query: {pattern}")
                    print(f"✅ DEBUG: Classificato come 'data_query' (pattern match)")
                return 'data_query'

        # Step 4: Determina la categoria migliore con i punteggi
        best_category = max(scores.items(), key=lambda x: x[1])
        best_score = best_category[1]

        # Step 5: Applica logica di decisione intelligente
        if best_score > 0.2:  # Soglia di confidenza
            result = best_category[0]
        else:
            # Fallback intelligente basato su context clues
            is_question = self._detect_question_intent(user_input)

            # Controllo più ampio per data_query indicators
            data_indicators = [
                'data', 'nascita', 'nato', 'nata', 'quando', 'eta', 'anni',
                'peso', 'altezza', 'allergie', 'profilo', 'dati', 'informazioni',
                'email', 'telefono', 'contatti', 'quanto', 'sono', 'alt', 'alta', 'alto'
            ]

            has_data_indicators = any(indicator in corrected_lower for indicator in data_indicators)

            if is_question and has_data_indicators:
                # Se è una domanda con indicatori di dati personali, è data_query
                result = 'data_query'
            elif is_question:
                # Se è una domanda generica, probabilmente è data_query
                result = 'data_query'
            else:
                # Altrimenti probabilmente è medical_request
                result = 'medical_request'

        if debug:
            confidence = best_score if best_score > 0.2 else 0.5
            print(f"✅ DEBUG: Classificato come '{result}' (confidenza: {confidence:.2f})")

        return result


class LLMAssistant:
    """
    Assistente LLM principale per Longeviva - VERSIONE COMPLETA E PULITA
    """

    def __init__(self, model_name="mistral:7b"):
        print("🏥 Inizializzazione del sistema Longeviva...")

        # Inizializza handler database
        self.patient_db = PatientHandler()
        self.doctor_db = DoctorHandler()

        # Carica medici
        self.available_doctors = self._load_doctors()
        self._show_database_stats()

        # Inizializza LLM
        self.model_name = model_name
        self.llm = LLM(self.model_name)

        # Stato conversazione
        self.conversation_state = "structured_registration"
        self.current_question = "start_registration"
        self.patient = Patient()
        self.authenticated = False
        self.recommended_doctor = None
        self.registration_handler = None

        # Booking state
        self.booking_attempts = 0
        self.max_booking_attempts = 3
        self.user_proposed_dates = []

        print("✅ Sistema pronto!")

    def _load_doctors(self):
        """Carica medici dal database o usa esempi"""
        if self.doctor_db.initialized:
            try:
                db_doctors = self.doctor_db.get_all_doctors()
                if db_doctors and len(db_doctors) > 0:
                    print(f"📊 Caricati {len(db_doctors)} medici dal database")
                    return db_doctors
            except Exception as e:
                print(f"⚠️ Errore caricamento medici: {e}")

        print("ℹ️ Uso medici di esempio")
        return create_sample_doctors()

    def _show_database_stats(self):
        """Mostra statistiche medici"""
        stats = get_doctors_statistics(self.available_doctors)
        print(f"📊 Database medici: {stats['total_doctors']} medici, "
              f"{len(stats['specializations'])} specializzazioni")

    # ================================
    # GESTIONE CONVERSAZIONE PRINCIPALE
    # ================================

    def start_conversation(self):
        """Avvia la conversazione con registrazione - SENZA raccomandazione automatica"""
        if RegistrationHandler:
            self.registration_handler = RegistrationHandler(self.patient, self.patient_db)
            welcome_msg, first_question = self.registration_handler.start_registration()

            print(f"\nAssistente: {welcome_msg}")
            print(f"\n{first_question}")

            self.conversation_state = "structured_registration"
        else:
            print("\nAssistente: Benvenuto a Longeviva! Come posso aiutarti oggi?")
            self.conversation_state = "collect_purpose"

        # ✅ MODIFICA: Il conversation_loop ora ritorna solo il successo della registrazione
        # Non fa più raccomandazioni automatiche
        success = self.conversation_loop()

        # ✅ Ritorna semplicemente il successo, senza raccomandazioni automatiche
        return success

    def start_logged_in_conversation(self):
        """Avvia la conversazione per un utente già loggato"""
        if not self.authenticated or not self.patient:
            print("❌ Paziente non autenticato")
            return

        print(f"\n🎉 Bentornato, {self.patient.get_name()}!")
        print("=" * 50)

        self._show_patient_summary()

        print(f"\nCome posso aiutarti oggi?")
        print("Puoi:")
        print("• Chiedermi informazioni sui tuoi dati (es. 'Quando sono nato?')")
        print("• Descrivere un problema medico per trovare lo specialista giusto")
        print("• Prenotare una visita")

        self.conversation_state = "collect_purpose"
        self.conversation_loop()

    def conversation_loop(self):
        """Loop principale della conversazione"""
        while True:
            try:
                user_input = input("\nTu: ").strip()

                # Gestione speciale per input vuoto durante registrazione strutturata
                if not user_input and self.conversation_state == "structured_registration":
                    # Se siamo nella fase di summary, l'input vuoto significa "continua"
                    if (hasattr(self, 'registration_handler') and
                            hasattr(self.registration_handler, 'current_phase') and
                            self.registration_handler.current_phase == "show_summary"):
                        user_input = "continua"  # Simula input di conferma
                    else:
                        continue  # Per altre fasi della registrazione, input vuoto non è valido
                elif not user_input:
                    # Per tutti gli altri stati, ignora input vuoto
                    continue

                # Comandi di uscita universali
                if user_input.lower() in ['esci', 'exit', 'quit']:
                    print("\n👋 Arrivederci! Grazie per aver usato Longeviva!")
                    break

                # ===== GESTIONE REGISTRAZIONE STRUTTURATA =====
                if self.conversation_state == "structured_registration":
                    if hasattr(self, 'registration_handler'):
                        success, response, next_question = self.registration_handler.process_answer(user_input)

                        print(f"\nAssistente: {response}")

                        if success:
                            # Registrazione completata - esci dal loop
                            return True

                        if next_question:
                            print(f"\n{next_question}")

                        continue
                    else:
                        print("❌ Errore: Handler di registrazione non disponibile")
                        break

                # ===== GESTIONE ALTRI STATI CONVERSAZIONE =====

                # Stato: Raccolta motivo visita
                elif self.conversation_state == "collect_purpose":
                    if user_input:
                        self.patient.set_purpose(user_input)
                        print(f"\nAssistente: Ho registrato il motivo della tua visita: '{user_input}'")

                        # Prosegui con raccolta dati clinici o raccomandazione medico
                        print("\nPassiamo alla raccolta dei tuoi dati clinici...")
                        self.conversation_state = "collect_clinical_data"
                    else:
                        print("\nAssistente: Per favore, descrivi il motivo per cui vorresti consultare un medico.")
                    continue

                # Stato: Raccolta dati clinici
                elif self.conversation_state == "collect_clinical_data":
                    # Qui potresti implementare una logica per raccogliere dati clinici
                    # Se necessario, oppure passare direttamente alla raccomandazione
                    print("\nAssistente: Grazie per le informazioni cliniche.")
                    self.conversation_state = "recommend_doctor"
                    continue

                # Stato: Raccomandazione medico
                elif self.conversation_state == "recommend_doctor":
                    self.recommend_doctor()
                    self.conversation_state = "handle_booking"
                    continue

                # Stato: Gestione prenotazione
                elif self.conversation_state == "handle_booking":
                    if user_input.lower() in ['sì', 'si', 'yes', 'ok', 'prenota']:
                        if self.recommended_doctor:
                            print(
                                f"\n✅ Ottimo! Procedo con la prenotazione per il Dr. {self.recommended_doctor.get_full_name()}")
                            # Qui implementeresti la logica di prenotazione
                            print("📅 (Logica di prenotazione da implementare)")
                        else:
                            print("\n❌ Non è stato selezionato alcun medico per la prenotazione.")
                    elif user_input.lower() in ['no', 'non ora', 'dopo']:
                        print("\n👍 Nessun problema! Puoi prenotare in qualsiasi momento.")
                    else:
                        print("\n❓ Non ho capito. Vuoi prenotare un appuntamento? (sì/no)")
                        continue

                    # Fine conversazione
                    print("\n👋 Grazie per aver usato Longeviva!")
                    break

                # Stato: Modalità diario alimentare
                elif self.conversation_state == "food_diary_mode":
                    if user_input.lower() in ['menu', 'torna', 'indietro']:
                        return 'menu'
                    elif user_input.lower() in ['esci', 'exit', 'quit']:
                        return 'exit'

                    # Processa input diario alimentare
                    try:
                        response = self.handle_food_diary_input(user_input)
                        print(f"\nLongi: {response}")
                    except Exception as e:
                        print(f"\n❌ Errore nel diario alimentare: {e}")
                    continue

                # Stato: Query sui dati
                elif self.conversation_state == "data_query":
                    if user_input.lower() in ['menu', 'torna', 'indietro']:
                        return 'menu'
                    elif user_input.lower() in ['esci', 'exit', 'quit']:
                        return 'exit'

                    # Classifica e gestisci query sui dati
                    try:
                        input_type = self.classify_user_input(user_input)

                        if input_type == 'data_query':
                            self.handle_data_query(user_input)
                        else:
                            print("\nTi posso aiutare solo con domande sui tuoi dati personali.")
                            print("Esempi: 'quanto peso?', 'che età ho?', 'quali sono le mie allergie?'")
                    except Exception as e:
                        print(f"\n❌ Errore nella query dati: {e}")
                    continue

                # Stato: Chat generica
                elif self.conversation_state == "general_chat":
                    try:
                        # Gestione chat generica con LLM
                        response = self.get_llm_response(user_input)
                        print(f"\nAssistente: {response}")
                    except Exception as e:
                        print(f"\n❌ Errore nella chat: {e}")
                    continue

                # Stato non riconosciuto
                else:
                    print(f"\n❌ Stato conversazione non riconosciuto: {self.conversation_state}")
                    print("Riavvio in modalità chat generica...")
                    self.conversation_state = "general_chat"
                    continue

            except KeyboardInterrupt:
                print("\n👋 Conversazione interrotta dall'utente")
                return False

            except EOFError:
                print("\n👋 Fine input - chiusura conversazione")
                return False

            except Exception as e:
                print(f"\n❌ Errore imprevisto nella conversazione: {e}")
                print("Tentativo di continuare...")

                # Log dell'errore per debug
                import traceback
                print(f"Debug traceback: {traceback.format_exc()}")

                # Reset a stato sicuro
                self.conversation_state = "general_chat"
                continue

        return True

    def process_user_input(self, user_input):
        """Processa l'input dell'utente in base allo stato"""
        if self.conversation_state == "structured_registration":
            self.handle_registration(user_input)
        elif self.conversation_state == "collect_purpose":
            self.handle_purpose_collection(user_input)
        elif self.conversation_state == "doctor_recommendation_provided":
            self.handle_appointment_booking(user_input)
        elif self.conversation_state == "booking_date_proposal":
            self.handle_date_proposal(user_input)
        elif self.conversation_state == "booking_slot_selection":
            self.handle_slot_selection(user_input)
        elif self.conversation_state == "booking_confirmed":
            self.handle_post_booking(user_input)
        elif self.conversation_state == "booking_failed":
            self.handle_booking_failure(user_input)
        else:
            self.handle_generic_response(user_input)

    # ================================
    # CLASSIFICAZIONE INPUT INTELLIGENTE
    # ================================

    def classify_user_input(self, user_input):
        """Classifica l'input dell'utente per determinare il tipo di richiesta - VERSIONE INTELLIGENTE"""

        # Inizializza il classificatore intelligente se non esiste
        if not hasattr(self, '_intelligent_classifier'):
            self._intelligent_classifier = IntelligentInputClassifier()

        # Usa il classificatore intelligente
        return self._intelligent_classifier.classify_input(user_input, debug=True)

    # ================================
    # GESTIONE REGISTRAZIONE
    # ================================

    def handle_registration(self, user_input):
        """Gestisce il processo di registrazione strutturato"""
        if not self.registration_handler:
            self.registration_handler = RegistrationHandler(self.patient, self.patient_db)
            welcome_msg, first_question = self.registration_handler.start_registration()
            print(f"\nAssistente: {welcome_msg}")
            if first_question:
                print(f"\n{first_question}")
            return

        is_complete, message, next_question = self.registration_handler.process_answer(user_input)

        if is_complete:
            print(f"\nAssistente: {message}")
            self.authenticated = True
            self.handle_registration_completion()
            self.conversation_state = "doctor_recommendation_provided"
        else:
            response = message
            if next_question:
                response += f"\n\n{next_question}"
            print(f"\nAssistente: {response}")

    def handle_registration_completion(self):
        """Gestisce il completamento della registrazione e avvia la ricerca semantica"""
        if not self.registration_handler:
            return

        preferences = self.registration_handler.get_preferences()
        motivation_data = self.registration_handler.get_motivation_data()

        print(f"🎯 DEBUG: Preferenze raccolte: {preferences}")
        print(f"🧠 DEBUG: Dati motivazionali: {motivation_data}")

        purpose = self.patient.get_purpose()
        if not purpose:
            print("⚠️ Nessun motivo della visita specificato")
            return

        self._semantic_doctor_search(purpose, preferences, motivation_data)

    # ================================
    # GESTIONE SCOPO VISITA INTELLIGENTE
    # ================================

    def handle_purpose_collection(self, user_input):
        """Gestisce raccolta motivo visita - VERSIONE INTELLIGENTE"""
        print(f"🔍 DEBUG: handle_purpose_collection chiamato con: '{user_input}'")

        if self.authenticated and self.patient and self.patient.get_name():
            # Utente loggato - usa metodo intelligente
            print(f"👤 DEBUG: Utente loggato, usando metodo intelligente")
            self.handle_logged_in_purpose_collection(user_input)
        else:
            # Nuovo utente - usa metodo originale
            print(f"🆕 DEBUG: Nuovo utente, usando metodo originale")
            self.patient.set_purpose(user_input)
            print(f"\nAssistente: Grazie!")
            print("Analizzo le informazioni per trovare lo specialista più adatto...")
            self.recommend_doctor()

    def handle_logged_in_purpose_collection(self, user_input):
        """Gestisce la raccolta del motivo per utenti loggati - VERSIONE INTELLIGENTE"""
        print(f"🔍 DEBUG: handle_logged_in_purpose_collection chiamato con: '{user_input}'")

        # Prima classifica l'input
        input_type = self.classify_user_input(user_input)
        print(f"🎯 DEBUG: Input classificato come: {input_type}")

        if input_type == 'data_query':
            # L'utente sta chiedendo informazioni sui suoi dati
            print(f"📋 DEBUG: Gestendo data_query")
            self.handle_data_query(user_input)
            return  # Non cambiare stato, rimani in ascolto

        elif input_type == 'general_chat':
            # Chat generale
            print(f"💬 DEBUG: Gestendo general_chat")
            print(f"\nAssistente: Ciao {self.patient.get_name()}! Come posso aiutarti oggi?")
            print(
                "Puoi chiedermi informazioni sui tuoi dati o descrivermi un problema medico per trovare lo specialista giusto.")
            return

        elif input_type == 'appointment_related':
            # Richiesta di appuntamento senza problema specifico
            print(f"📅 DEBUG: Gestendo appointment_related")
            print(
                f"\nAssistente: Perfetto! Per trovare il medico più adatto, potresti descrivermi il motivo della visita?")
            print("Ad esempio: 'controllo generale', 'mal di testa', 'problemi digestivi', ecc.")
            return

        elif input_type == 'medical_request':
            # Vera richiesta medica - procedi come prima
            print(f"🏥 DEBUG: Gestendo medical_request")
            self.patient.set_purpose(user_input)
            self.update_patient_purpose_in_db(user_input)

            name = self.patient.get_name()
            print(f"\nPerfetto, {name}! Ho registrato la tua richiesta.")
            print(f"")
            print(f"🎯 **ANALISI PERSONALIZZATA IN CORSO...**")
            print(f"Sto considerando:")
            print(f"• Il tuo profilo medico esistente")
            print(f"• La tua posizione geografica ({self.patient.get_city() or 'Non specificata'})")
            print(f"• Le tue preferenze precedenti")
            print(f"• Specialisti disponibili nella tua zona")
            print(f"")
            print(f"Un momento...")

            # Procedi con la raccomandazione del medico
            self.recommend_doctor()

        else:
            # Fallback
            print(f"❓ DEBUG: Gestendo fallback")
            print(f"\nAssistente: Non sono sicuro di aver capito. Stai cercando:")
            print("1. Informazioni sui tuoi dati personali?")
            print("2. Un medico per un problema specifico?")
            print("Puoi essere più specifico?")

    # ================================
    # GESTIONE QUERY SUI DATI PERSONALI
    # ================================

    def handle_data_query(self, user_input):
        """Gestisce le domande sui dati del paziente"""
        if not self.patient:
            print("\nAssistente: Non ho informazioni su di te. Effettua prima il login.")
            return

        input_lower = user_input.lower().strip()

        # Analizza che tipo di dato viene richiesto
        if re.search(r'\b(quando|che giorno|data.*nascita|compleanno)', input_lower):
            self._answer_birth_date()
        elif re.search(r'\b(quanti.*anni|età)', input_lower):
            self._answer_age()
        elif re.search(r'\b(peso)', input_lower):
            self._answer_weight()
        elif re.search(r'\b(altezza|alt[oa])', input_lower):
            self._answer_height()
        elif re.search(r'\b(bmi)', input_lower):
            self._answer_bmi()
        elif re.search(r'\b(email|mail)', input_lower):
            self._answer_email()
        elif re.search(r'\b(telefono|numero)', input_lower):
            self._answer_phone()
        elif re.search(r'\b(allergie)', input_lower):
            self._answer_allergies()
        elif re.search(r'\b(profilo|dati|informazioni|chi.*sono)', input_lower):
            self._answer_full_profile()
        else:
            # Domanda generica sui dati
            self._answer_general_data_question(user_input)

    def _answer_birth_date(self):
        """Risponde alla domanda sulla data di nascita"""
        birth_date = self.patient.get_birth_date()
        if birth_date:
            try:
                # Parse della data dal formato Firebase
                birth = datetime.fromisoformat(birth_date.replace('Z', '+00:00'))
                formatted_date = birth.strftime("%d %B %Y")
                print(f"\nAssistente: Sei nato il {formatted_date}.")
            except:
                print(f"\nAssistente: La tua data di nascita nei nostri archivi è: {birth_date}")
        else:
            print("\nAssistente: Non ho informazioni sulla tua data di nascita nei nostri archivi.")

        print("C'è altro che vorresti sapere sui tuoi dati o posso aiutarti con qualcos'altro?")

    def _answer_age(self):
        """Risponde alla domanda sull'età"""
        age = self.patient.get_age()
        if age:
            print(f"\nAssistente: Hai {age} anni.")
        else:
            print("\nAssistente: Non riesco a calcolare la tua età dai dati disponibili.")
        print("C'è altro che vorresti sapere?")

    def _answer_weight(self):
        """Risponde alla domanda sul peso"""
        weight = self.patient.get_weight()
        if weight:
            print(f"\nAssistente: Il tuo peso registrato è {weight} kg.")
        else:
            print("\nAssistente: Non ho informazioni sul tuo peso nei nostri archivi.")
        print("Posso aiutarti con altro?")

    def _answer_height(self):
        """Risponde alla domanda sull'altezza"""
        height = self.patient.get_height()
        if height:
            print(f"\nAssistente: La tua altezza registrata è {height} cm.")
        else:
            print("\nAssistente: Non ho informazioni sulla tua altezza nei nostri archivi.")
        print("C'è altro che ti interessa sapere?")

    def _answer_bmi(self):
        """Calcola e risponde con il BMI"""
        bmi = self._calculate_bmi()
        if bmi > 0:
            category = self._get_bmi_category(bmi)
            print(f"\nAssistente: Il tuo BMI è {bmi:.1f}, che corrisponde alla categoria '{category}'.")

            # Aggiungi commento basato sul BMI
            if bmi < 18.5:
                print("Questo indica sottopeso. Potrebbe essere utile consultare un nutrizionista.")
            elif bmi < 25:
                print("Questo indica un peso normale. Ottimo!")
            elif bmi < 30:
                print("Questo indica sovrappeso. Considera di consultare un nutrizionista per consigli sulla dieta.")
            else:
                print("Questo indica obesità. Ti consiglio di consultare un medico per un piano di gestione del peso.")
        else:
            print("\nAssistente: Non riesco a calcolare il BMI perché mancano i dati di altezza o peso.")
        print("Posso aiutarti con altro?")

    def _answer_email(self):
        """Risponde alla domanda sull'email"""
        email = self.patient.get_email()
        if email:
            print(f"\nAssistente: La tua email registrata è: {email}")
        else:
            print("\nAssistente: Non ho una email registrata per te.")
        print("C'è altro che vorresti sapere?")

    def _answer_phone(self):
        """Risponde alla domanda sul telefono"""
        phone = self.patient.get_phone()
        if phone:
            print(f"\nAssistente: Il tuo numero di telefono registrato è: {phone}")
        else:
            print("\nAssistente: Non ho un numero di telefono registrato per te.")
        print("Posso aiutarti con altro?")

    def _answer_allergies(self):
        """Risponde alla domanda sulle allergie"""
        allergies = self.patient.get_allergies()
        if allergies and allergies.lower() != 'nessuna':
            print(f"\nAssistente: Le tue allergie registrate sono: {allergies}")
            print("⚠️ Ricorda sempre di informare i medici delle tue allergie prima di qualsiasi trattamento.")
        else:
            print("\nAssistente: Non hai allergie registrate nei nostri archivi.")
        print("C'è altro che ti interessa sapere?")

    def _answer_full_profile(self):
        """Mostra il profilo completo"""
        print(f"\n👤 **ECCO IL TUO PROFILO COMPLETO:**")
        print("=" * 50)

        # Informazioni di base
        print(f"📋 **Dati anagrafici:**")
        print(f"• Nome: {self.patient.get_full_name()}")
        print(f"• Età: {self.patient.get_age()} anni")

        # Data di nascita
        birth_date = self.patient.get_birth_date()
        if birth_date:
            try:
                birth = datetime.fromisoformat(birth_date.replace('Z', '+00:00'))
                formatted_date = birth.strftime("%d %B %Y")
                print(f"• Data di nascita: {formatted_date}")
            except:
                print(f"• Data di nascita: {birth_date}")

        # Sesso
        sex = self.patient.get_sex()
        if sex:
            sex_display = "Maschio" if sex == "M" else "Femmina"
            print(f"• Sesso: {sex_display}")

        # Dati fisici
        height = self.patient.get_height()
        weight = self.patient.get_weight()
        if height or weight:
            print(f"\n📏 **Dati fisici:**")
            if height:
                print(f"• Altezza: {height} cm")
            if weight:
                print(f"• Peso: {weight} kg")

            bmi = self._calculate_bmi()
            if bmi > 0:
                category = self._get_bmi_category(bmi)
                print(f"• BMI: {bmi:.1f} ({category})")

        # Contatti
        email = self.patient.get_email()
        phone = self.patient.get_phone()
        if email or phone:
            print(f"\n📞 **Contatti:**")
            if email:
                print(f"• Email: {email}")
            if phone:
                print(f"• Telefono: {phone}")

        # Informazioni mediche
        allergies = self.patient.get_allergies()
        if allergies and allergies.lower() != 'nessuna':
            print(f"\n⚠️ **Allergie:** {allergies}")

        print("\nC'è qualche informazione specifica che vorresti approfondire?")

    def _answer_general_data_question(self, user_input):
        """Gestisce domande generiche sui dati"""
        print(f"\nAssistente: Ho capito che stai chiedendo informazioni sui tuoi dati.")
        print("Posso aiutarti con:")
        print("• Data di nascita e età")
        print("• Dati fisici (altezza, peso, BMI)")
        print("• Informazioni di contatto")
        print("• Allergie registrate")
        print("• Profilo completo")
        print("\nCosa ti interessa sapere nello specifico?")

    # ================================
    # GESTIONE PAZIENTI E DATI
    # ================================

    def set_patient_from_data(self, patient_data):
        """Imposta i dati del paziente da un dizionario (usato dopo il login)"""
        if not patient_data:
            print("⚠️ Nessun dato paziente fornito")
            return False

        try:
            # Crea nuovo paziente direttamente dai dati Firebase
            self.patient = Patient(data=patient_data)

            # Aggiungi campi aggiuntivi per la conversazione
            city = (patient_data.get('city') or
                    patient_data.get('address', {}).get('city', ''))
            if city:
                self.patient.set_city(city)

            # Purpose - potrebbe essere in vari campi
            purpose = (patient_data.get('last_purpose') or
                       patient_data.get('purpose') or
                       patient_data.get('lastVisitReason', ''))
            if purpose:
                self.patient.set_purpose(purpose)

            # Marca come autenticato
            self.authenticated = True

            print(f"✅ Dati paziente caricati: {self.patient.get_full_name()}")
            return True

        except Exception as e:
            print(f"❌ Errore nel caricamento dati paziente: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _show_patient_summary(self):
        """Mostra un riassunto del profilo del paziente"""
        if not self.patient:
            return

        print("📋 **IL TUO PROFILO:**")
        print(f"👤 Nome: {self.patient.get_full_name()}")

        age = self.patient.get_age()
        if age:
            print(f"🎂 Età: {age} anni")

        city = self.patient.get_city()
        if city:
            print(f"🏙️ Città: {city}")
        else:
            print(f"🏙️ Città: Non specificata")

        # Mostra dati fisici se disponibili
        height = self.patient.get_height()
        weight = self.patient.get_weight()
        if height and weight:
            bmi = self._calculate_bmi()
            print(f"📏 Fisico: {height} cm, {weight} kg (BMI: {bmi:.1f})")

        # Mostra allergie se presenti
        allergies = self.patient.get_allergies()
        if allergies and allergies.lower() != 'nessuna':
            print(f"⚠️ Allergie: {allergies}")

        # Mostra ultima visita se disponibile
        last_purpose = self.patient.get_purpose()
        if last_purpose:
            print(f"🩺 Ultima richiesta: {last_purpose}")

    def _calculate_bmi(self):
        """Calcola il BMI del paziente"""
        try:
            height = self.patient.get_height()
            weight = self.patient.get_weight()

            if height and weight:
                height_m = float(height) / 100  # Converte cm in metri
                weight_kg = float(weight)

                if height_m > 0 and weight_kg > 0:
                    return weight_kg / (height_m ** 2)
        except:
            pass
        return 0

    def _get_bmi_category(self, bmi):
        """Restituisce la categoria BMI"""
        if bmi < 18.5:
            return "Sottopeso"
        elif bmi < 25:
            return "Normale"
        elif bmi < 30:
            return "Sovrappeso"
        else:
            return "Obesità"

    def update_patient_purpose_in_db(self, purpose):
        """Aggiorna il motivo della visita nel database"""
        try:
            self.patient.set_purpose(purpose)
            print(f"📝 Motivo della visita aggiornato: {purpose}")
            # TODO: Implementare aggiornamento nel database Firebase
        except Exception as e:
            print(f"⚠️ Errore aggiornamento database: {e}")

    # ================================
    # GESTIONE RACCOMANDAZIONI MEDICO
    # ================================

    def recommend_doctor(self):
        """Raccomanda un medico"""
        purpose = self.patient.get_purpose()
        patient_city = self.patient.get_city()

        best_doctor, specialization = get_best_doctor_for_purpose(
            self.available_doctors, purpose, patient_city
        )

        if best_doctor:
            self.recommended_doctor = best_doctor

            print(f"\n👨‍⚕️ MEDICO RACCOMANDATO:")
            print(f"• Nome: {best_doctor.get_full_name()}")
            print(f"• Specializzazione: {best_doctor.get_specialization()}")

            # Gestisci città correttamente
            city_display = getattr(best_doctor, 'city_of_work', best_doctor.get_city())
            print(f"• Città: {city_display}")
            print(f"• Esperienza: {best_doctor.get_years_of_experience()} anni")

            print(f"\nIl Dr. {best_doctor.get_surname()} è perfetto per il tuo caso.")
            print("Vuoi prenotare un appuntamento?")

            self.conversation_state = "doctor_recommendation_provided"
        else:
            print("\nAssistente: Non riesco a trovare un medico adatto. Riprova con una descrizione diversa.")
            self.conversation_state = "collect_purpose"

    def _semantic_doctor_search(self, purpose, preferences, motivation_data):
        """Esegue ricerca semantica avanzata considerando preferenze e motivazioni"""
        print(f"\n🔍 RICERCA SEMANTICA AVANZATA AVVIATA")
        print(f"📝 Problema: '{purpose}'")
        print(f"⚖️ Preferenze: {preferences}")

        try:
            # Importa il matcher semantico
            from utils.semantic_search import SemanticDoctorMatcher
            matcher = SemanticDoctorMatcher()

            # Trova i migliori medici
            recommended_doctors = matcher.find_best_matching_doctors(
                problem_description=purpose,
                all_doctors=self.available_doctors,
                patient_city=self.patient.get_city(),
                max_results=3
            )

            if not recommended_doctors:
                print("❌ Nessun medico trovato con ricerca semantica - fallback tradizionale")
                self.recommend_doctor()
                return

            # Applica le preferenze dell'utente per riordinare i risultati
            ranked_doctors = self._rank_doctors_by_preferences(recommended_doctors, preferences)

            # Prendi il primo medico come raccomandazione principale
            self.recommended_doctor = ranked_doctors[0]

            # Genera risposta personalizzata
            self._generate_personalized_recommendation(ranked_doctors, preferences, motivation_data)

        except ImportError:
            print("⚠️ Ricerca semantica non disponibile - uso metodo tradizionale")
            self.recommend_doctor()
        except Exception as e:
            print(f"❌ Errore nella ricerca semantica: {e}")
            traceback.print_exc()
            self.recommend_doctor()

    def _rank_doctors_by_preferences(self, doctors, preferences):
        """Riordina i medici in base alle preferenze dell'utente"""
        if not preferences:
            return doctors

        print(f"📊 Riordinamento medici in base alle preferenze...")

        scored_doctors = []

        for doctor in doctors:
            score = 0

            # Fattore vicinanza
            if 'vicinanza' in preferences:
                vicinanza_importance = preferences['vicinanza']
                doctor_city = getattr(doctor, 'city_of_work', doctor.get_city())
                patient_city = self.patient.get_city()

                if doctor_city and patient_city:
                    if doctor_city.lower() == patient_city.lower():
                        score += vicinanza_importance * 2  # Bonus per stessa città
                    else:
                        score += vicinanza_importance * 0.5  # Penalità per città diversa

            # Fattore specializzazione (usa già il punteggio semantico)
            if 'specializzazione' in preferences and hasattr(doctor, 'semantic_score'):
                spec_importance = preferences['specializzazione']
                score += doctor.semantic_score * spec_importance * 10

            # Fattore costo (simulato)
            if 'costo' in preferences:
                costo_importance = preferences['costo']
                experience = doctor.get_years_of_experience()
                if costo_importance >= 4:  # Vuole prezzi bassi
                    score += max(0, (20 - experience)) * 0.1
                else:  # Non gli importa il prezzo
                    score += experience * 0.1

            # Fattore area di interesse
            if 'area_interesse' in preferences:
                area_importance = preferences['area_interesse']
                if hasattr(doctor, 'area_of_interest') and doctor.area_of_interest:
                    score += area_importance * 0.8  # Bonus per area di interesse specifica
                else:
                    score += area_importance * 0.3  # Bonus minore se non specificata

            scored_doctors.append((doctor, score))
            print(f"  → {doctor.get_full_name()}: {score:.2f} punti")

        # Ordina per punteggio decrescente
        scored_doctors.sort(key=lambda x: x[1], reverse=True)

        return [doctor for doctor, score in scored_doctors]

    def _generate_personalized_recommendation(self, ranked_doctors, preferences, motivation_data):
        """Genera una raccomandazione personalizzata basata su tutti i dati raccolti"""
        name = self.patient.get_name() or "utente"

        # Crea messaggio personalizzato basato sulle motivazioni
        motivation_text = ""
        if 'objectives' in motivation_data:
            objectives = motivation_data['objectives']
            obj_summary = []
            for obj in objectives[:2]:  # Prendi solo i primi 2 per brevità
                if "Perdere peso" in obj:
                    obj_summary.append("perdere peso")
                elif "Avere più energia" in obj:
                    obj_summary.append("avere più energia")
                elif "Migliorare" in obj:
                    obj_summary.append("migliorare la composizione corporea")
                elif "Aumentare" in obj:
                    obj_summary.append("aumentare la consapevolezza alimentare")
                elif "Vivere" in obj:
                    obj_summary.append("vivere più a lungo")
                elif "Sentirmi" in obj:
                    obj_summary.append("sentirsi meglio")

            if obj_summary:
                if len(obj_summary) == 1:
                    motivation_text = f"\n🎯 Considerando il tuo obiettivo di {obj_summary[0]}"
                else:
                    motivation_text = f"\n🎯 Considerando i tuoi obiettivi di {obj_summary[0]} e {obj_summary[1]}"

        # Info sui medici raccomandati
        doctors_info = []
        for i, doctor in enumerate(ranked_doctors, 1):
            city_info = getattr(doctor, 'city_of_work', doctor.get_city())

            # Informazioni personalizzate basate sulle preferenze
            pref_notes = []
            if 'vicinanza' in preferences and preferences['vicinanza'] >= 4:
                if city_info and self.patient.get_city() and city_info.lower() == self.patient.get_city().lower():
                    pref_notes.append("🏠 Nella tua città")
                else:
                    pref_notes.append("🚗 Fuori città")

            if 'specializzazione' in preferences and preferences['specializzazione'] >= 4:
                if hasattr(doctor, 'semantic_score'):
                    pref_notes.append(f"🎯 Match AI: {doctor.semantic_score:.0%}")

            if 'area_interesse' in preferences and preferences['area_interesse'] >= 4:
                if hasattr(doctor, 'area_of_interest') and doctor.area_of_interest:
                    pref_notes.append(f"🔬 Area: {doctor.area_of_interest}")

            pref_text = " • " + " • ".join(pref_notes) if pref_notes else ""

            doctors_info.append(f"""
    {i}. 👨‍⚕️ **{doctor.get_full_name()}**
       🏥 {doctor.get_specialization()}
       📍 {city_info}
       ⏱️ {doctor.get_years_of_experience()} anni{pref_text}
            """)

        # Crea spiegazione personalizzata delle preferenze
        pref_explanation = ""
        if preferences:
            pref_parts = []
            if preferences.get('vicinanza', 0) >= 4:
                pref_parts.append("la vicinanza geografica")
            if preferences.get('specializzazione', 0) >= 4:
                pref_parts.append("l'alta specializzazione")
            if preferences.get('costo', 0) >= 4:
                pref_parts.append("il miglior rapporto qualità-prezzo")
            if preferences.get('area_interesse', 0) >= 4:
                pref_parts.append("l'area di interesse specifica")

            if pref_parts:
                pref_explanation = f"\n💡 Ho dato priorità a {', '.join(pref_parts)} come hai indicato."

        # Genera il messaggio completo
        message = f"""
    Perfetto, {name}! Ho completato l'analisi del tuo profilo utilizzando l'intelligenza artificiale.
    {motivation_text}

    🧠 **RACCOMANDAZIONI AI PERSONALIZZATE:**
    {''.join(doctors_info)}

    🎯 **Raccomandazione principale:** Il **Dr. {self.recommended_doctor.get_surname()}** è la scelta ottimale per te.
    {pref_explanation}

    Il sistema ha analizzato semanticamente il tuo problema "{self.patient.get_purpose()}" 
    e ha considerato tutte le tue preferenze per trovare la migliore corrispondenza.

    Vuoi prenotare un appuntamento con il Dr. {self.recommended_doctor.get_surname()}?
        """

        print(f"\nAssistente: {message}")

        # Aggiorna stato conversazione
        self.conversation_state = "doctor_recommendation_provided"
        self.current_question = "booking_preference"

    # ================================
    # GESTIONE PRENOTAZIONI
    # ================================

    def handle_appointment_booking(self, user_input):
        """Gestisce prenotazione appuntamento"""
        if any(word in user_input.lower() for word in ["sì", "si", "prenota", "appuntamento"]):
            print(f"\nAssistente: Perfetto! Procediamo con la prenotazione.")
            print(f"Dr. {self.recommended_doctor.get_surname()} è disponibile per visite.")
            print(f"")
            print(f"Quando preferiresti fare la visita?")
            print(f"Proponi pure una data e un orario (es. 'Lunedì 15 gennaio alle 10:00' o 'Mercoledì pomeriggio').")

            self.conversation_state = "booking_date_proposal"
            self.booking_attempts = 0
        else:
            print(
                f"\nAssistente: Il Dr. {self.recommended_doctor.get_surname()} è specializzato in {self.recommended_doctor.get_specialization()}.")
            print("Ha ottime recensioni e molta esperienza nel suo campo.")
            print("Vuoi prenotare un appuntamento?")

    def handle_date_proposal(self, user_input):
        """Gestisce le proposte di data dell'utente"""
        self.booking_attempts += 1
        self.user_proposed_dates.append(user_input)

        # Simula verifica disponibilità
        is_available = self._check_doctor_availability(user_input)

        if is_available:
            # Data disponibile - conferma prenotazione
            booking_id = f"BOOK-{random.randint(10000, 99999)}"

            print(f"\n✅ Ottima notizia! Il Dr. {self.recommended_doctor.get_surname()} è disponibile per {user_input}.")
            print(f"")
            print(f"📅 **PRENOTAZIONE CONFERMATA:**")
            print(f"• Dr. {self.recommended_doctor.get_full_name()}")
            print(f"• Data e ora: {user_input}")
            print(f"• Numero prenotazione: {booking_id}")
            print(f"• Indirizzo: {self.recommended_doctor.get_address()}")
            print(f"• Telefono studio: {self.recommended_doctor.get_phone() or '06-12345678'}")
            print(f"")
            print(
                f"Riceverai una conferma via email. Ti ricordiamo di portare con te un documento di identità e la tessera sanitaria.")

            self.conversation_state = "booking_confirmed"
        else:
            # Data non disponibile
            if self.booking_attempts >= self.max_booking_attempts:
                # Dopo 3 tentativi, invita a contattare via email
                doctor_email = self.recommended_doctor.get_email() or "info@longeviva.it"

                print(
                    f"\nMi dispiace, dopo {self.max_booking_attempts} tentativi non sono riuscito a trovare una disponibilità compatibile.")
                print(f"")
                print(f"Ti invito a contattare direttamente il Dr. {self.recommended_doctor.get_surname()} via email:")
                print(f"📧 **{doctor_email}**")
                print(f"")
                print(f"Nella email, specifica:")
                print(f"• Il tuo nome: {self.patient.get_name()} {self.patient.get_surname()}")
                print(f"• Le date che hai proposto: {', '.join(self.user_proposed_dates)}")
                print(f"• Il motivo della visita: {self.patient.get_purpose()}")
                print(f"")
                print(f"Il dottore ti risponderà entro 24 ore con le sue disponibilità.")

                self.conversation_state = "booking_failed"
            else:
                # Proponi di riprovare
                attempts_left = self.max_booking_attempts - self.booking_attempts
                print(
                    f"\nMi dispiace, il Dr. {self.recommended_doctor.get_surname()} non è disponibile per {user_input}.")
                print(f"")
                if attempts_left > 1:
                    print(f"Hai ancora {attempts_left} tentativi. Puoi proporre un'altra data?")
                    print(f"Magari prova con giorni diversi o orari alternativi.")
                else:
                    print(f"Hai ancora {attempts_left} tentativo. Vuoi proporre un'altra data?")

    def _check_doctor_availability(self, proposed_date):
        """Simula il controllo della disponibilità del medico"""
        # 70% di probabilità che sia disponibile
        return random.random() > 0.3

    def handle_slot_selection(self, user_input):
        """Gestisce selezione slot appuntamento"""
        slots = ["Domani alle 10:00", "Dopodomani alle 15:30", "Venerdì alle 9:15"]

        try:
            choice = int(user_input.strip())
            if 1 <= choice <= 3:
                selected_slot = slots[choice - 1]
                booking_id = f"BOOK-{random.randint(10000, 99999)}"

                print(f"\n✅ Appuntamento prenotato!")
                print(f"• Dr. {self.recommended_doctor.get_full_name()}")
                print(f"• Data: {selected_slot}")
                print(f"• Numero prenotazione: {booking_id}")
                print(f"• Indirizzo: {self.recommended_doctor.get_address()}")
                print("\nRiceverai una conferma via email.")

                self.conversation_state = "booking_confirmed"
            else:
                print("\nAssistente: Scegli 1, 2 o 3 per uno degli slot disponibili.")
        except ValueError:
            print("\nAssistente: Inserisci il numero dello slot (1, 2 o 3).")

    def handle_post_booking(self, user_input):
        """Gestisce la conversazione dopo la prenotazione confermata"""
        print("\nAssistente: C'è altro in cui posso aiutarti?")
        print("Puoi sempre tornare su Longeviva per gestire i tuoi appuntamenti o per prenotare altre visite.")

    def handle_booking_failure(self, user_input):
        """Gestisce la conversazione dopo il fallimento della prenotazione"""
        print(
            f"\nAssistente: Spero che il Dr. {self.recommended_doctor.get_surname()} possa trovarti un appuntamento presto!")
        print("C'è altro in cui posso aiutarti oggi?")

    # ================================
    # METODI DI UTILITÀ E SUPPORTO
    # ================================

    def handle_generic_response(self, user_input):
        """Gestisce risposte generiche"""
        print("\nAssistente: C'è altro in cui posso aiutarti?")

    def generate_response(self, prompt, system_prompt=None):
        """Genera una risposta usando l'LLM esistente"""
        if hasattr(self, 'llm') and self.llm:
            return self.llm.generate_response(prompt, system_prompt)
        else:
            # Fallback response
            return f"Risposta generata: {prompt}", None

    def get_patient_history_context(self):
        """Restituisce un contesto basato sulla storia del paziente"""
        if not self.patient:
            return ""

        context_parts = []

        # Informazioni demografiche
        context_parts.append(f"Paziente: {self.patient.get_full_name()}, {self.patient.get_age()} anni")

        if self.patient.get_city():
            context_parts.append(f"Residenza: {self.patient.get_city()}")

        # Informazioni fisiche per BMI e valutazioni
        height = self.patient.get_height()
        weight = self.patient.get_weight()
        if height and weight:
            bmi = self._calculate_bmi()
            if bmi > 0:
                bmi_category = self._get_bmi_category(bmi)
                context_parts.append(f"BMI: {bmi:.1f} ({bmi_category})")

        # Allergie importanti per prescrizioni
        allergies = self.patient.get_allergies()
        if allergies and allergies.lower() != 'nessuna':
            context_parts.append(f"Allergie note: {allergies}")

        # Storia delle visite precedenti
        if hasattr(self.patient, 'medical_history') and self.patient.medical_history:
            context_parts.append(f"Storia medica: {len(self.patient.medical_history)} eventi")

        return " | ".join(context_parts)

    # ================================
    # METODI MANCANTI DAL CODICE ORIGINALE
    # ================================

    def find_doctors_near_patient(self, doctors, city, specialization, max_results=3):
        """Trova medici vicini al paziente"""
        if not doctors:
            return []

        if city:
            city_doctors = []
            for d in doctors:
                city_match = (hasattr(d, 'city_of_work') and d.city_of_work and
                              d.city_of_work.lower() == city.lower()) or \
                             (d.get_city() and d.get_city().lower() == city.lower())
                if city_match:
                    city_doctors.append(d)

            return city_doctors[:max_results]

        return doctors[:max_results]

    def get_doctors_statistics(self):
        """Genera statistiche sui medici - metodo istanza"""
        return get_doctors_statistics(self.available_doctors)

    # ================================
    # METODI MANCANTI - PARTE FINALE
    # ================================

    def handle_identity_confirmation(self, user_input):
        """Gestisce la conferma dell'identità del paziente"""
        if not self.patient:
            self.patient = Patient()

        if any(word in user_input.lower() for word in ["sì", "si", "confermo", "esatto"]):
            # Identità confermata
            name = self.patient.get_name() or "utente"
            print(f"\nAssistente: Perfetto, {name}! Come posso aiutarti oggi?")
            print("Qual è il motivo per cui desideri consultare un medico?")
            self.conversation_state = "collect_purpose"
            self.current_question = "main_purpose"
        else:
            # Identità non confermata
            print("\nAssistente: Mi scuso per la confusione. Potresti fornirmi di nuovo il tuo nome completo?")
            self.conversation_state = "authentication"
            self.current_question = "name_surname"

    def handle_authentication(self, user_input):
        """Gestisce il processo di autenticazione/identificazione iniziale"""
        print(f"🔍 DEBUG: Funzione handle_authentication chiamata con input: '{user_input}'")

        if not self.patient:
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
            print(
                "\nAssistente: Mi serve sia il nome che il cognome insieme. Puoi fornirmeli entrambi in un unico messaggio? (es. 'Mario Rossi')")
            return

        # Assegna nome e cognome al paziente
        self.patient.set_name(name)
        self.patient.set_surname(surname)

        # Passa alla raccolta dello scopo
        self.conversation_state = "collect_purpose"
        self.current_question = "main_purpose"

        print(f"\nAssistente: Grazie {name}! Ora, come posso aiutarti oggi?")
        print("Qual è il motivo per cui desideri consultare un medico?")

    def handle_data_confirmation(self, user_input):
        """Gestisce la conferma dei dati estratti"""
        user_input_lower = user_input.lower()

        if any(word in user_input_lower for word in ["sì", "si", "corretto", "giusto", "ok", "bene", "esatto"]):
            # Dati confermati, procedi con la raccolta di dati mancanti
            missing_data = self.identify_missing_essential_data()
            if missing_data:
                self.conversation_state = "collect_missing_data"
                self.current_question = missing_data[0]  # Inizia dal primo dato mancante
                self.ask_for_missing_data(missing_data[0])
            else:
                # Tutti i dati essenziali sono presenti, passa al motivo della visita
                self.conversation_state = "collect_purpose"
                self.current_question = "main_purpose"
                self.ask_for_purpose()

        elif any(word in user_input_lower for word in ["no", "sbagliato", "errore", "correggere"]):
            # Chiedi correzioni
            print("\nAssistente: Nessun problema! Dimmi cosa devo correggere.")
            print("Puoi specificare esattamente quali informazioni sono sbagliate e fornirmi quelle corrette.")

        else:
            # Input ambiguo, chiedi chiarimenti
            print(
                "\nAssistente: Non ho capito bene. I dati che ho estratto sono corretti o c'è qualcosa da modificare?")

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
        missing_data = getattr(self, 'missing_data', [])
        if current_missing in missing_data:
            missing_data.remove(current_missing)

        # Procedi al prossimo dato mancante o al motivo della visita
        if missing_data:
            self.current_question = missing_data[0]
            self.ask_for_missing_data(missing_data[0])
        else:
            # Tutti i dati raccolti, passa al motivo della visita
            self.conversation_state = "collect_purpose"
            self.current_question = "main_purpose"
            self.ask_for_purpose()

    def ask_for_missing_data(self, data_type, error_message=None):
        """Chiede un dato specifico mancante"""
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

        print(f"\nAssistente: {prompt}")

    def ask_for_purpose(self):
        """Chiede il motivo della visita"""
        name = self.patient.get_name() if self.patient and self.patient.get_name() else "utente"

        print(f"\nAssistente: Perfetto {name}! Ora ho tutte le informazioni di base per il tuo profilo.")
        print("Potresti dirmi qual è il motivo per cui desideri una visita medica?")
        print("Descrivi pure il problema o i sintomi che ti preoccupano, anche nei dettagli.")

    def identify_missing_essential_data(self):
        """Identifica quali dati essenziali mancano"""
        essential_fields = ["name", "age", "sex", "city", "phone"]
        missing = []

        if not self.patient:
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

    def extract_data_from_text(self, text):
        """Estrae dati strutturati dal testo libero dell'utente"""
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

        # Estrazione età
        age_patterns = [
            r"ho (\d+) anni",
            r"(\d+) anni",
            r"età (\d+)",
            r"sono (\w+) di (\d+) anni",
        ]
        for pattern in age_patterns:
            match = re.search(pattern, text_lower)
            if match:
                groups = match.groups()
                for group in groups:
                    if group and group.isdigit():
                        extracted["age"] = int(group)
                        break
                if "age" in extracted:
                    break

        # Altri pattern di estrazione...
        # (resto dell'implementazione abbreviata per spazio)

        print(f"DEBUG: Dati estratti: {extracted}")
        return extracted

    def populate_patient_from_extracted_data(self):
        """Popola l'oggetto paziente con i dati estratti"""
        if not hasattr(self, 'extracted_data'):
            return

        if not self.patient:
            self.patient = Patient()

        if "name" in self.extracted_data:
            self.patient.set_name(self.extracted_data["name"])
        if "age" in self.extracted_data:
            self.patient.set_age(self.extracted_data["age"])
        if "city" in self.extracted_data:
            self.patient.set_city(self.extracted_data["city"])
        if "sex" in self.extracted_data:
            self.patient.set_sex(self.extracted_data["sex"])
        # ... altri campi

    def generate_data_summary(self):
        """Genera un riassunto organizzato dei dati estratti"""
        summary_parts = []

        if not self.patient:
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

        # Altri dati...
        if not summary_parts:
            return "Non sono riuscito a estrarre informazioni specifiche dalla tua descrizione."

        return "\n".join(summary_parts)

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

        print(f"\nAssistente: Grazie per la panoramica! Ho estratto queste informazioni dal tuo racconto:")
        print(f"\n{summary}")
        print(f"\nHo capito bene questi dati? Se c'è qualcosa da correggere o aggiungere, dimmelo pure.")
        print("Dopo la conferma, ti chiederò le informazioni mancanti per completare il profilo.")

        # Passa allo stato di conferma
        self.conversation_state = "confirm_data"
        self.current_question = "data_confirmation"

    def handle_doctor_recommendation(self, user_input):
        """Gestisce la risposta dell'utente alla raccomandazione del medico"""
        if any(word in user_input.lower() for word in ["sì", "si", "ok", "bene", "procedi", "prenota"]):
            if not self.patient:
                self.patient = Patient()

            name = self.patient.get_name() or "utente"
            print(
                f"\nAssistente: Ottimo {name}! Ti aiuterò a prenotare un appuntamento con il Dott. {self.recommended_doctor.get_surname()}.")
            print("Prima però, avrei bisogno di alcune informazioni per ottimizzare la tua esperienza.")

            self.conversation_state = "schedule_appointment"
            self.current_question = "appointment_details"
        else:
            if not self.patient:
                self.patient = Patient()

            name = self.patient.get_name() or "utente"
            print(
                f"\nAssistente: Capisco {name}. Se preferisci pensarci, puoi sempre contattarci più tardi per prenotare.")
            print("Posso aiutarti con qualcos'altro? O magari preferisci avere maggiori informazioni sul dottore?")

            self.conversation_state = "closing"
            self.current_question = "anything_else"

    def handle_appointment_scheduling(self, user_input):
        """Gestisce la pianificazione dell'appuntamento"""
        if not self.patient:
            self.patient = Patient()

        name = self.patient.get_name() or "utente"
        email = self.patient.get_contact_info().get('email') or "la tua email"

        print(
            f"\nAssistente: Perfetto {name}! Ho prenotato un appuntamento per te con il Dott. {self.recommended_doctor.get_surname()}")
        print("per il prossimo lunedì alle 15:00.")
        print(f"\nRiceverai una conferma via email a {email}.")
        print("C'è altro in cui posso aiutarti?")

        self.conversation_state = "closing"
        self.current_question = "anything_else"

    def handle_closing(self, user_input):
        """Gestisce la chiusura della conversazione"""
        if self.current_question == "anything_else":
            if any(word in user_input.lower() for word in ["sì", "si", "certo", "ok"]):
                print("\nAssistente: Come posso aiutarti ancora?")
                self.current_question = "final_request"
            else:
                print("\nAssistente: Grazie per aver utilizzato i servizi di Longeviva! È stato un piacere assisterti.")
                print("Se hai bisogno di ulteriore aiuto in futuro, non esitare a contattarci nuovamente.")
                print("Ti auguro una buona giornata e una pronta guarigione!")
                self.current_question = "end"
        else:
            print("\nAssistente: C'è altro in cui posso esserti utile?")
            self.current_question = "anything_else"

    def handle_exit(self):
        """Gestisce l'uscita dall'applicazione"""
        print("\nAssistente: Grazie per aver utilizzato Longeviva. Arrivederci e prenditi cura di te!")

    def format_date(self, date_str):
        """Formatta una data in formato leggibile"""
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            weekdays = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
            weekday = weekdays[date_obj.weekday()]
            months = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
                      "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
            month = months[date_obj.month - 1]
            return f"{weekday} {date_obj.day} {month} {date_obj.year}"
        except:
            return date_str

    def start_food_diary_mode(self):
        """Avvia la modalità diario alimentare con Mistral"""
        self.conversation_state = "food_diary_mode"
        self.food_diary_session = {
            'start_time': datetime.now(),
            'entries': [],
            'context': []
        }

        # Crea il prompt di sistema personalizzato per il diario alimentare
        system_prompt = self._create_food_diary_system_prompt()

        # Messaggio di benvenuto personalizzato
        welcome_prompt = self._create_food_diary_welcome_prompt()

        # Genera la prima risposta di Longi
        response, context = self.generate_response(welcome_prompt, system_prompt)
        print(f"\nLongi: {response}")

        # Avvia il loop della chat
        self._food_diary_conversation_loop(system_prompt)

    def _create_food_diary_system_prompt(self):
        """Crea il prompt di sistema per la modalità diario alimentare"""
        patient_context = self.get_patient_context_for_nutrition()

        system_prompt = f"""Sei Longi, un nutrizionista virtuale esperto e amichevole di Longeviva. 
    Il tuo ruolo è aiutare l'utente a creare e gestire un diario alimentare personalizzato.

    CONTESTO PAZIENTE:
    {patient_context}

    COMPORTAMENTO:
    - Sei caloroso, motivante e professionale
    - Parli in italiano e usi un tono amichevole ma competente
    - Fai domande specifiche per capire le abitudini alimentari
    - Dai consigli pratici e personalizzati
    - Incoraggia sempre il paziente nei suoi sforzi
    - Non fornisci mai diagnosi mediche, ma solo consigli nutrizionali generali

    OBIETTIVI DELLA SESSIONE:
    1. Aiutare a registrare pasti e spuntini della giornata
    2. Fornire feedback nutrizionale costruttivo
    3. Suggerire miglioramenti alle abitudini alimentari
    4. Motivare verso scelte più sane
    5. Rispondere a domande su alimentazione e nutrizione

    FORMATO RISPOSTE:
    - Mantieni le risposte concise ma complete (max 150 parole)
    - Usa emoji appropriati per rendere la conversazione più vivace
    - Fai una domanda alla volta per guidare la conversazione
    - Se l'utente registra un pasto, riassumi e commenta le scelte nutrizionali

    LIMITI:
    - Non prescrivere diete specifiche senza supervisione medica
    - Non diagnosticare condizioni mediche
    - Incoraggia sempre a consultare un professionista per casi complessi"""

        return system_prompt

    def _create_food_diary_welcome_prompt(self):
        """Crea il messaggio di benvenuto personalizzato per il diario alimentare"""
        name = self.patient.get_name() if self.patient else "amico"
        age = self.patient.get_age() if self.patient else None
        weight = self.patient.get_weight() if self.patient else None
        height = self.patient.get_height() if self.patient else None

        welcome_context = f"L'utente si chiama {name}"
        if age:
            welcome_context += f", ha {age} anni"
        if height and weight:
            bmi = self._calculate_bmi()
            if bmi > 0:
                welcome_context += f", altezza {height}cm, peso {weight}kg (BMI: {bmi:.1f})"

        prompt = f"""Dai il benvenuto caloroso a {name} per la sessione di diario alimentare. 
    Presenta brevemente cosa farai (aiutare con il diario alimentare, dare consigli nutrizionali).
    Contesto: {welcome_context}

    Poi chiedi cosa ha mangiato oggi o se preferisce iniziare registrando il prossimo pasto.
    Mantieni un tono entusiasta e motivante!"""

        return prompt

    def get_patient_context_for_nutrition(self):
        """Ottiene il contesto del paziente specifico per la nutrizione"""
        if not self.patient:
            return "Nessun dato paziente disponibile"

        context_parts = []

        # Info base
        name = self.patient.get_name()
        age = self.patient.get_age()
        sex = self.patient.get_sex()

        if name:
            context_parts.append(f"Nome: {name}")
        if age:
            context_parts.append(f"Età: {age} anni")
        if sex:
            sex_text = "maschio" if sex == "M" else "femmina"
            context_parts.append(f"Sesso: {sex_text}")

        # Dati fisici e BMI
        height = self.patient.get_height()
        weight = self.patient.get_weight()
        if height and weight:
            bmi = self._calculate_bmi()
            if bmi > 0:
                bmi_category = self._get_bmi_category(bmi)
                context_parts.append(f"Fisico: {height}cm, {weight}kg, BMI {bmi:.1f} ({bmi_category})")

        # Allergie importanti per la nutrizione
        allergies = self.patient.get_allergies()
        if allergies and allergies.lower() != 'nessuna':
            context_parts.append(f"Allergie: {allergies}")

        # Lifestyle se disponibile
        if hasattr(self.patient, 'get_lifestyle'):
            lifestyle = self.patient.get_lifestyle()
            if lifestyle:
                if 'typeOfDiet' in lifestyle:
                    context_parts.append(f"Dieta attuale: {lifestyle['typeOfDiet']}")
                if 'physicalActivityFrequency' in lifestyle:
                    context_parts.append(f"Attività fisica: {lifestyle['physicalActivityFrequency']}")

        # Motivo della visita (potrebbe essere rilevante)
        purpose = self.patient.get_purpose()
        if purpose:
            context_parts.append(f"Motivo visita: {purpose}")

        return " | ".join(context_parts) if context_parts else "Dati limitati disponibili"

    def _food_diary_conversation_loop(self, system_prompt):
        """Loop della conversazione per il diario alimentare"""
        print("\n💡 Consigli: puoi dirmi cosa hai mangiato, chiedere consigli nutrizionali,")
        print("    o scrivere 'menu' per tornare al menu principale")

        while True:
            try:
                user_input = input("\nTu: ").strip()

                if user_input.lower() in ['menu', 'torna', 'indietro']:
                    print("\nLongi: Perfetto! È stato un piacere aiutarti con il diario alimentare! 🥗")
                    print("Continua così e ci sentiamo presto per altri consigli nutrizionali!")
                    break

                elif user_input.lower() in ['esci', 'exit', 'quit']:
                    print("\nLongi: Ciao! Ricorda di prenderti cura della tua alimentazione! 🌟")
                    return 'exit'

                elif not user_input:
                    print("Dimmi qualcosa! Sono qui per aiutarti! 😊")
                    continue

                # Processa l'input alimentare
                self._process_food_diary_input(user_input, system_prompt)

            except KeyboardInterrupt:
                print("\nLongi: Alla prossima! Continua a fare scelte alimentari sagge! 👋")
                break
            except Exception as e:
                print(f"❌ Errore: {e}")
                print("Longi: Scusa, ho avuto un piccolo problema tecnico. Riprova!")

    def _process_food_diary_input(self, user_input, system_prompt):
        """Processa l'input dell'utente per il diario alimentare"""
        try:
            # Aggiungi il contesto della conversazione precedente
            conversation_context = self._build_conversation_context()

            # Crea il prompt completo
            full_prompt = f"""CRONOLOGIA CONVERSAZIONE:
    {conversation_context}

    MESSAGGIO UTENTE ATTUALE: {user_input}

    Rispondi come Longi, il nutrizionista virtuale. Se l'utente ha descritto un pasto:
    1. Riconosci e riassumi cosa ha mangiato
    2. Commenta gli aspetti positivi
    3. Suggerisci eventuali miglioramenti (senza essere critico)
    4. Fai una domanda per continuare la conversazione

    Se l'utente fa una domanda nutrizionale, rispondi con consigli pratici e scientificamente corretti."""

            # Genera risposta con Mistral
            response, context = self.generate_response(full_prompt, system_prompt)

            # Salva nell'history della conversazione
            self.food_diary_session['entries'].append({
                'timestamp': datetime.now(),
                'user_input': user_input,
                'assistant_response': response
            })

            print(f"\nLongi: {response}")

        except Exception as e:
            print(f"❌ Errore nel processare input: {e}")
            print("Longi: Mi dispiace, non sono riuscito a processare quello che hai detto. Riprova!")

    def _build_conversation_context(self):
        """Costruisce il contesto della conversazione per il diario alimentare"""
        if not hasattr(self, 'food_diary_session') or not self.food_diary_session['entries']:
            return "Inizio conversazione"

        # Prendi gli ultimi 3-4 scambi per non sovraccaricare il prompt
        recent_entries = self.food_diary_session['entries'][-3:]

        context_parts = []
        for entry in recent_entries:
            timestamp = entry['timestamp'].strftime("%H:%M")
            context_parts.append(f"[{timestamp}] Utente: {entry['user_input']}")
            context_parts.append(f"[{timestamp}] Longi: {entry['assistant_response']}")

        return "\n".join(context_parts)

    def save_food_diary_session(self):
        """Salva la sessione del diario alimentare (per implementazioni future)"""
        if not hasattr(self, 'food_diary_session'):
            return

        try:
            # Qui potresti salvare la sessione nel database o in un file
            session_summary = {
                'patient_id': getattr(self.patient, 'id', 'unknown'),
                'start_time': self.food_diary_session['start_time'],
                'duration_minutes': (datetime.now() - self.food_diary_session['start_time']).total_seconds() / 60,
                'entries_count': len(self.food_diary_session['entries']),
                'entries': self.food_diary_session['entries']
            }

            print(f"📊 Sessione diario alimentare completata:")
            print(f"   Durata: {session_summary['duration_minutes']:.1f} minuti")
            print(f"   Messaggi scambiati: {session_summary['entries_count']}")

            # TODO: Implementare salvataggio nel database Firebase

        except Exception as e:
            print(f"⚠️ Errore nel salvare la sessione: {e}")

    # Metodo helper per il prompt nutrizionale avanzato
    def _create_advanced_nutrition_prompt(self, user_input, meal_type=None):
        """Crea un prompt avanzato per analisi nutrizionale"""
        patient_info = self.get_patient_context_for_nutrition()

        current_time = datetime.now()
        time_context = ""
        if current_time.hour < 10:
            time_context = "È mattina, quindi probabilmente colazione"
        elif current_time.hour < 14:
            time_context = "È l'ora di pranzo"
        elif current_time.hour < 18:
            time_context = "È pomeriggio, forse uno spuntino"
        else:
            time_context = "È sera, probabilmente cena"

        prompt = f"""ANALISI NUTRIZIONALE RICHIESTA:
    Paziente: {patient_info}
    Orario: {current_time.strftime('%H:%M')} ({time_context})
    Input utente: "{user_input}"

    Come nutrizionista virtuale Longi, analizza questo messaggio e:
    1. Identifica se descrive un pasto o una domanda nutrizionale
    2. Se è un pasto: commentalo costruttivamente (positivi + suggerimenti)
    3. Se è una domanda: rispondi con consigli pratici
    4. Mantieni tono amichevole e motivante
    5. Fai una domanda per continuare la conversazione

    Max 150 parole, usa emoji appropriati."""

        return prompt