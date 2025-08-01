import warnings
import sys
import os
import re
import traceback
import random

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


class LLMAssistant:
    """
    Assistente LLM principale per Longeviva con registrazione strutturata - VERSIONE CORRETTA
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

        # Stato conversazione - INIZIA DIRETTAMENTE CON REGISTRAZIONE
        self.conversation_state = "structured_registration"
        self.current_question = "start_registration"
        self.patient = Patient()
        self.authenticated = False
        self.recommended_doctor = None
        self.registration_handler = None

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

    def start_conversation(self):
        """Avvia la conversazione DIRETTAMENTE con registrazione"""
        # NUOVO: Non chiede più nome/cognome, inizia con registrazione motivazionale
        if RegistrationHandler:
            self.registration_handler = RegistrationHandler(self.patient, self.patient_db)
            welcome_msg, first_question = self.registration_handler.start_registration()

            print(f"\nAssistente: {welcome_msg}")
            print(f"\n{first_question}")

            self.conversation_state = "structured_registration"
        else:
            # Fallback se RegistrationHandler non disponibile
            print("\nAssistente: Benvenuto a Longeviva! Come posso aiutarti oggi?")
            self.conversation_state = "collect_purpose"

        self.conversation_loop()

    def conversation_loop(self):
        """Loop principale della conversazione"""
        while True:
            try:
                user_input = input("\nTu: ").strip()

                if user_input.lower() in ["exit", "quit", "esci"]:
                    print("\nGrazie per aver usato Longeviva!")
                    break

                self.process_user_input(user_input)

            except KeyboardInterrupt:
                print("\n\nConversazione terminata.")
                break
            except Exception as e:
                print(f"\n❌ Errore: {e}")
                print("Riprova o digita 'exit' per uscire.")

    def process_user_input(self, user_input):
        """Processa l'input dell'utente in base allo stato"""
        if self.conversation_state == "structured_registration":
            self.handle_registration(user_input)
        elif self.conversation_state == "collect_purpose":
            self.handle_purpose_collection(user_input)
        elif self.conversation_state == "doctor_recommendation_provided":
            self.handle_appointment_booking(user_input)
        elif self.conversation_state == "booking_slot_selection":
            self.handle_slot_selection(user_input)
        else:
            self.handle_generic_response(user_input)

    def handle_registration(self, user_input):
        """Gestisce il nuovo processo di registrazione strutturato"""
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

            # Avvia la ricerca semantica personalizzata
            self.handle_registration_completion()

            # Cambia stato per gestire le successive interazioni
            self.conversation_state = "doctor_recommendation_provided"
        else:
            response = message
            if next_question:
                response += f"\n\n{next_question}"
            print(f"\nAssistente: {response}")

    def handle_purpose_collection(self, user_input):
        """Gestisce raccolta motivo visita (fallback se non viene da registrazione)"""
        self.patient.set_purpose(user_input)

        print(f"\nAssistente: Grazie!")
        print("Analizzo le informazioni per trovare lo specialista più adatto...")

        self.recommend_doctor()

    def handle_appointment_booking(self, user_input):
        """Gestisce prenotazione appuntamento"""
        if any(word in user_input.lower() for word in ["sì", "si", "prenota", "appuntamento"]):
            slots = ["Domani alle 10:00", "Dopodomani alle 15:30", "Venerdì alle 9:15"]

            print(f"\nAssistente: Disponibilità Dr. {self.recommended_doctor.get_surname()}:")
            for i, slot in enumerate(slots, 1):
                print(f"{i}. {slot}")
            print("\nQuale preferisci? (1, 2 o 3)")

            self.conversation_state = "booking_slot_selection"
        else:
            print(
                f"\nAssistente: Il Dr. {self.recommended_doctor.get_surname()} è specializzato in {self.recommended_doctor.get_specialization()}.")
            print("Ha ottime recensioni e molta esperienza nel suo campo.")
            print("Vuoi prenotare un appuntamento?")

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

    def handle_generic_response(self, user_input):
        """Gestisce risposte generiche"""
        print("\nAssistente: C'è altro in cui posso aiutarti?")

    def recommend_doctor(self):
        """Raccomanda un medico - VERSIONE MIGLIORATA"""
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

    def handle_registration_completion(self):
        """
        Gestisce il completamento della registrazione e avvia la ricerca semantica
        """
        if not self.registration_handler:
            return

        # Ottieni i dati dalle preferenze
        preferences = self.registration_handler.get_preferences()
        motivation_data = self.registration_handler.get_motivation_data()

        print(f"🎯 DEBUG: Preferenze raccolte: {preferences}")
        print(f"🧠 DEBUG: Dati motivazionali: {motivation_data}")

        # Ottieni il motivo della visita (ora è in purpose)
        purpose = self.patient.get_purpose()

        if not purpose:
            print("⚠️ Nessun motivo della visita specificato")
            return

        # Avvia ricerca semantica avanzata
        self._semantic_doctor_search(purpose, preferences, motivation_data)

    def _semantic_doctor_search(self, purpose, preferences, motivation_data):
        """
        Esegue ricerca semantica avanzata considerando preferenze e motivazioni
        """
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
        """
        Riordina i medici in base alle preferenze dell'utente
        """
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

            # Fattore costo (simulato - in un sistema reale useresti dati veri)
            if 'costo' in preferences:
                costo_importance = preferences['costo']
                # Simulazione: medici con esperienza maggiore costano di più
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
        """
        Genera una raccomandazione personalizzata basata su tutti i dati raccolti
        """
        name = self.patient.get_name() or "utente"

        # Crea messaggio personalizzato basato sulle motivazioni
        motivation_text = ""
        if 'objectives' in motivation_data:
            objectives = motivation_data['objectives']
            motivation_text = f"\n🎯 Considerando i tuoi obiettivi ({', '.join(objectives[:2])}{'...' if len(objectives) > 2 else ''})"

        # Crea informazioni sui medici trovati
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
        system_prompt = """
        Sei Longi di Longeviva con intelligenza artificiale avanzata. 
        Hai appena completato un'analisi completa del profilo del paziente.
        Presenta i risultati in modo professionale, personalizzato e rassicurante.
        """

        prompt = f"""
Perfetto, {name}! Ho completato l'analisi del tuo profilo utilizzando l'intelligenza artificiale.
{motivation_text}

🧠 **RACCOMANDAZIONI AI PERSONALIZZATE:**
{''.join(doctors_info)}

🎯 **Raccomandazione principale:** Il **Dr. {self.recommended_doctor.get_surname()}** è la scelta ottimale per te.
{pref_explanation}

Il sistema ha analizzato semanticamente il tuo problema "{self.patient.get_purpose()}" 
e ha considerato tutte le tue preferenze per trovare la migliore corrispondenza.

Vuoi che ti aiuti a prenotare un appuntamento con il Dr. {self.recommended_doctor.get_surname()}, 
o preferisci avere maggiori informazioni su uno degli altri specialisti?
        """

        response, _ = self.llm.generate_response(prompt, system_prompt)
        print(f"\nAssistente: {response}")

        # Aggiorna stato conversazione
        self.conversation_state = "doctor_recommendation_provided"
        self.current_question = "booking_preference"