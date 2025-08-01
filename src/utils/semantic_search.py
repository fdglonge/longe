# src/utils/semantic_search.py
import traceback
import sys
import os

# Aggiungi il path per importare dalle directory parent
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Importi per ricerca semantica
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity

    SEMANTIC_SEARCH_AVAILABLE = True
    print("✅ Ricerca semantica disponibile")
except ImportError as e:
    print("⚠️ Moduli per ricerca semantica non disponibili:")
    print(f"   {e}")
    print("📋 Installa con: pip install sentence-transformers scikit-learn numpy")
    SEMANTIC_SEARCH_AVAILABLE = False


class SemanticDoctorMatcher:
    """
    Classe dedicata alla ricerca semantica dei medici - VERSIONE MIGLIORATA
    """

    def __init__(self):
        self.model = None
        self.embedding_cache = {}
        self._initialize_model()

    def _initialize_model(self):
        """Inizializza il modello per embeddings semantici"""
        if not SEMANTIC_SEARCH_AVAILABLE:
            print("❌ Ricerca semantica non disponibile - modalità fallback attiva")
            return

        # Lista di modelli in ordine di preferenza
        models_to_try = [
            ('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2', 'Multilingual MiniLM'),
            ('sentence-transformers/all-MiniLM-L6-v2', 'All MiniLM L6'),
            ('sentence-transformers/distiluse-base-multilingual-cased', 'DistilUSE Multilingual'),
            ('paraphrase-multilingual-MiniLM-L12-v2', 'MiniLM Fallback')
        ]

        print("🔄 Caricamento modello di embedding semantico...")

        for model_name, model_desc in models_to_try:
            try:
                print(f"   Tentativo con {model_desc}...")
                self.model = SentenceTransformer(model_name)
                print(f"✅ Modello {model_desc} caricato con successo")
                return
            except Exception as e:
                print(f"   ⚠️ {model_desc} non disponibile: {e}")
                continue

        # Se nessun modello funziona
        print("❌ Nessun modello di embedding disponibile")
        self.model = None

    def find_best_matching_doctors(self, problem_description, all_doctors, patient_city=None, max_results=5):
        """
        Trova i medici più adatti usando ricerca semantica avanzata

        Args:
            problem_description (str): Descrizione del problema del paziente
            all_doctors (list): Lista di tutti i medici disponibili
            patient_city (str): Città del paziente per preferenza geografica
            max_results (int): Numero massimo di risultati

        Returns:
            list: Lista di medici ordinati per rilevanza semantica
        """
        if not self.model or not all_doctors:
            print("⚠️ Ricerca semantica non disponibile - uso metodo tradizionale")
            return self._fallback_search(problem_description, all_doctors, patient_city, max_results)

        print(f"\n🔍 RICERCA SEMANTICA AVANZATA AVVIATA")
        print(f"📝 Problema: '{problem_description}'")
        print(f"👨‍⚕️ Medici nel database: {len(all_doctors)}")
        print(f"🏙️ Città paziente: {patient_city}")

        # 1. Migliora la descrizione del problema per il matching
        enhanced_problem = self._enhance_problem_description(problem_description)

        # 2. Ottieni embedding del problema del paziente
        problem_embedding = self._get_embedding(enhanced_problem)
        if problem_embedding is None:
            return self._fallback_search(problem_description, all_doctors, patient_city, max_results)

        # 3. Calcola similarità per ogni medico
        doctor_scores = []

        for doctor in all_doctors:
            try:
                # Ottieni la specializzazione del medico
                specialization = doctor.get_specialization() if doctor.get_specialization() else "medicina generale"

                # Migliora la rappresentazione della specializzazione
                enhanced_specialization = self._enhance_specialization_description(specialization, doctor)

                # Calcola embedding della specializzazione
                spec_embedding = self._get_embedding(enhanced_specialization)
                if spec_embedding is not None:
                    # Calcola similarità coseno
                    similarity = cosine_similarity([problem_embedding], [spec_embedding])[0][0]

                    # Aggiungi bonus per città del paziente
                    city_bonus = 0
                    if patient_city and hasattr(doctor, 'city_of_work') and doctor.city_of_work:
                        if doctor.city_of_work.lower() == patient_city.lower():
                            city_bonus = 0.15  # 15% bonus per stessa città
                        elif self._are_nearby_cities(doctor.city_of_work, patient_city):
                            city_bonus = 0.05  # 5% bonus per città vicine

                    final_score = similarity + city_bonus

                    doctor_scores.append({
                        'doctor': doctor,
                        'similarity': similarity,
                        'final_score': final_score,
                        'specialization': specialization,
                        'enhanced_specialization': enhanced_specialization
                    })

                    print(f"  → {doctor.get_full_name()}: {specialization} = {similarity:.3f}")

            except Exception as e:
                print(f"⚠️ Errore processando {doctor.get_full_name()}: {e}")
                continue

        # 4. Ordina per punteggio finale
        doctor_scores.sort(key=lambda x: x['final_score'], reverse=True)

        # 5. Applica filtro qualità (solo medici con similarità > 0.1)
        filtered_scores = [s for s in doctor_scores if s['similarity'] > 0.1]

        if not filtered_scores:
            print("⚠️ Nessun medico con similarità sufficiente, uso fallback")
            return self._fallback_search(problem_description, all_doctors, patient_city, max_results)

        # 6. Prepara risultati finali
        results = []
        for i, score_data in enumerate(filtered_scores[:max_results]):
            doctor = score_data['doctor']

            # Aggiungi metadati al medico per la presentazione
            doctor.semantic_score = score_data['similarity']
            doctor.final_score = score_data['final_score']
            doctor.matched_specialization = score_data['specialization']

            results.append(doctor)

            print(f"🎯 {i + 1}. {doctor.get_full_name()} - {score_data['specialization']} "
                  f"(Score: {score_data['similarity']:.3f})")

        print(f"✅ Ricerca semantica completata: {len(results)} risultati")
        return results

    def _enhance_problem_description(self, problem):
        """Migliora la descrizione del problema per un matching migliore"""
        # Mappa sinonimi e termini medici più specifici
        problem_lower = problem.lower()

        # Dizionario di espansioni semantiche
        semantic_expansions = {
            'mal di testa': 'cefalea emicrania dolore cranico neurologico',
            'dolore al petto': 'dolore toracico cardiaco petto cardiovascolare',
            'problemi di pelle': 'dermatologico cutaneo epidermide dermatite',
            'dolori articolari': 'artralgia reumatologia ortopedia articolazioni',
            'problemi di cuore': 'cardiologico cardiovascolare cardiaco miocardio',
            'ansia': 'psicologico mentale psichiatrico stress emotivo',
            'depressione': 'psichiatrico mentale umore psicologico',
            'problemi digestivi': 'gastroenterologico digestivo stomaco intestino',
            'mal di schiena': 'lombalgia ortopedico vertebrale colonna spinale',
            'problemi respiratori': 'pneumologico polmonare respiratorio bronchiale',
            'dolori muscolari': 'mialgia ortopedico muscolare fisioterapico'
        }

        enhanced = problem
        for key, expansion in semantic_expansions.items():
            if key in problem_lower:
                enhanced += f" {expansion}"

        return enhanced

    def _enhance_specialization_description(self, specialization, doctor):
        """Migliora la descrizione della specializzazione includendo area di interesse"""
        base_spec = specialization.lower()

        # Aggiungi informazioni contestuali sulla specializzazione
        specialization_contexts = {
            'medicina generale': 'medicina familiare cure primarie prevenzione salute generale medico di base',
            'cardiologia': 'cuore cardiovascolare pressione arteriosa infarto aritmie ipertensione',
            'dermatologia': 'pelle cute dermatiti acne psoriasi eczema melanoma lesioni cutanee',
            'neurologia': 'sistema nervoso cervello emicrania epilessia sclerosi alzheimer parkinson',
            'ortopedia': 'ossa articolazioni fratture legamenti tendini traumatologia sportiva',
            'gastroenterologia': 'apparato digerente stomaco intestino fegato gastrite colite',
            'pneumologia': 'polmoni respirazione asma bronchite tubercolosi insufficienza respiratoria',
            'urologia': 'apparato urinario reni vescica prostata calcoli renali',
            'ginecologia': 'apparato genitale femminile utero ovaie gravidanza menopausa',
            'pediatria': 'medicina infantile bambini neonati sviluppo crescita vaccinazioni',
            'psichiatria': 'salute mentale depressione ansia disturbi psicologici terapia psichiatrica',
            'endocrinologia': 'ormoni tiroide diabete metabolismo ghiandole endocrine obesità',
            'oculistica': 'occhi vista retina glaucoma cataratta miopia presbiopia',
            'otorinolaringoiatria': 'orecchio naso gola udito sinusiti faringiti laringiti'
        }

        enhanced = specialization
        for spec, context in specialization_contexts.items():
            if spec in base_spec:
                enhanced += f" {context}"
                break

        # Aggiungi area di interesse se disponibile
        if hasattr(doctor, 'area_of_interest') and doctor.area_of_interest:
            enhanced += f" {doctor.area_of_interest}"

        return enhanced

    def _are_nearby_cities(self, city1, city2):
        """Verifica se due città sono vicine (versione semplificata)"""
        # Raggruppa città per regioni/aree metropolitane
        city_groups = [
            ['roma', 'frascati', 'tivoli', 'guidonia', 'ciampino'],
            ['milano', 'monza', 'bergamo', 'brescia', 'varese'],
            ['napoli', 'caserta', 'salerno', 'avellino', 'benevento'],
            ['torino', 'asti', 'cuneo', 'alessandria', 'novara'],
            ['bologna', 'modena', 'reggio emilia', 'parma', 'ferrara'],
            ['firenze', 'prato', 'pistoia', 'arezzo', 'siena']
        ]

        city1_lower = city1.lower()
        city2_lower = city2.lower()

        for group in city_groups:
            if city1_lower in group and city2_lower in group:
                return True

        return False

    def _get_embedding(self, text):
        """Ottiene embedding per un testo con cache"""
        if not self.model:
            return None

        # Usa cache
        if text in self.embedding_cache:
            return self.embedding_cache[text]

        try:
            embedding = self.model.encode([text])[0]
            self.embedding_cache[text] = embedding
            return embedding
        except Exception as e:
            print(f"❌ Errore generazione embedding per '{text}': {e}")
            return None

    def _fallback_search(self, problem_description, all_doctors, patient_city, max_results):
        """Ricerca fallback con keyword matching SUPER MIGLIORATA"""
        print("🔄 Utilizzo ricerca keyword fallback avanzata...")

        # Mapping keyword per specialità MOLTO ESPANSO con sinonimi
        keyword_mapping = {
            'cardiologia': [
                'cuore', 'petto', 'battiti', 'pressione', 'tachicardia', 'aritmia', 'cardiovascolare',
                'infarto', 'angina', 'ipertensione', 'ipotensione', 'cardiopatia', 'coronarie',
                'fibrillazione', 'bradicardia', 'extrasistole', 'soffio', 'valvola', 'miocardio'
            ],
            'dermatologia': [
                'pelle', 'macchie', 'brufoli', 'acne', 'prurito', 'dermatite', 'eczema', 'psoriasi',
                'cute', 'lesioni', 'eritema', 'orticaria', 'melanoma', 'nevo', 'verruca', 'micosi',
                'dermatosi', 'vescicole', 'pustole', 'comedoni', 'seborrea', 'vitiligine'
            ],
            'neurologia': [
                'mal di testa', 'emicrania', 'vertigini', 'tremori', 'cefalea', 'neurologico', 'nervi',
                'sclerosi', 'epilessia', 'convulsioni', 'paralisi', 'paresi', 'neuropatia', 'alzheimer',
                'parkinson', 'distonia', 'mielite', 'nevralgia', 'ictus', 'tia', 'demenza'
            ],
            'ortopedia': [
                'ossa', 'fratture', 'ginocchio', 'schiena', 'articolazioni', 'muscoli', 'postura',
                'lombalgia', 'cervicale', 'artrite', 'artrosi', 'tendinite', 'borsite', 'lussazione',
                'distorsione', 'ernia', 'disco', 'vertebre', 'legamenti', 'menisco', 'cartilagine'
            ],
            'oculistica': [
                'occhi', 'vista', 'miopia', 'glaucoma', 'cataratta', 'oculare', 'visione', 'retina',
                'presbiopia', 'astigmatismo', 'ipermetropia', 'maculopatia', 'congiuntivite', 'ptosi',
                'diplopia', 'fotofobia', 'lacrimazione', 'blefarite', 'strabismo', 'daltonismo'
            ],
            'gastroenterologia': [
                'stomaco', 'digestione', 'gastrite', 'intestino', 'addome', 'nausea', 'colite', 'reflusso',
                'ulcera', 'ernia iatale', 'meteorismo', 'gonfiore', 'diarrea', 'stipsi', 'colon',
                'duodeno', 'esofago', 'gastroenterite', 'morbo crohn', 'celiachia', 'epatite'
            ],
            'psichiatria': [
                'depressione', 'ansia', 'stress', 'panico', 'mentale', 'psicologico', 'umore', 'disturbi',
                'bipolare', 'schizofrenia', 'psicosi', 'fobia', 'ossessivo', 'compulsivo', 'ptsd',
                'disturbo alimentare', 'insonnia', 'attacchi panico', 'burnout', 'borderline'
            ],
            'pneumologia': [
                'polmoni', 'respirazione', 'tosse', 'asma', 'bronchi', 'respiro', 'fiato', 'bronchite',
                'polmonite', 'tubercolosi', 'enfisema', 'fibrosi', 'dispnea', 'apnea', 'sinusite',
                'faringite', 'laringite', 'tracheite', 'pleurite', 'embolia polmonare'
            ],
            'urologia': [
                'reni', 'vescica', 'urinario', 'prostata', 'calcoli', 'cistite', 'incontinenza',
                'ematuria', 'disuria', 'pielonefrite', 'ipertrofia prostatica', 'nefrite',
                'glomerulonefrite', 'insufficienza renale', 'dialisi', 'trapianto rene'
            ],
            'ginecologia': [
                'ginecologico', 'mestruazioni', 'gravidanza', 'utero', 'ovaie', 'ciclo', 'femminile',
                'endometriosi', 'fibromi', 'cisti ovariche', 'amenorrea', 'dismenorrea', 'menorragia',
                'menopausa', 'pap test', 'hpv', 'candida', 'vaginite', 'cervice'
            ],
            'pediatria': [
                'bambino', 'bambini', 'pediatrico', 'infanzia', 'neonato', 'crescita', 'vaccini',
                'febbre bambino', 'otite', 'bronchiolite', 'gastroenterite pediatrica', 'dermatite atopica',
                'asma infantile', 'enuresi', 'ritardo crescita', 'autismo', 'adhd'
            ],
            'endocrinologia': [
                'tiroide', 'diabete', 'ormoni', 'metabolismo', 'endocrino', 'glicemia', 'insulina',
                'ipotiroidismo', 'ipertiroidismo', 'tiroidite', 'noduli tiroidei', 'obesità',
                'sindrome metabolica', 'colesterolo', 'trigliceridi', 'cortisolo', 'testosterone'
            ]
        }

        problem_lower = problem_description.lower()

        # Preprocessing del testo del problema per catturare più varianti
        problem_words = set(problem_lower.split())
        problem_text = f" {problem_lower} "  # Aggiungi spazi per match parole intere

        specialty_scores = {}

        # Algoritmo di scoring più sofisticato
        for specialty, keywords in keyword_mapping.items():
            score = 0
            matched_keywords = []

            for keyword in keywords:
                keyword_lower = keyword.lower()

                # 1. Match esatto di frase
                if keyword_lower == problem_lower.strip():
                    score += 10  # Massimo punteggio per match esatto
                    matched_keywords.append(keyword)

                # 2. Match frase completa nel testo
                elif keyword_lower in problem_lower:
                    score += 5  # Alto punteggio per frase contenuta
                    matched_keywords.append(keyword)

                # 3. Match di parole singole
                else:
                    keyword_words = set(keyword_lower.split())
                    common_words = keyword_words.intersection(problem_words)
                    if common_words:
                        # Punteggio proporzionale alle parole in comune
                        word_score = len(common_words) / len(keyword_words)
                        score += word_score * 2
                        if word_score > 0.5:  # Se almeno metà parole matchano
                            matched_keywords.append(keyword)

            if score > 0:
                specialty_scores[specialty] = {
                    'score': score,
                    'matched_keywords': matched_keywords
                }

        print(f"🎯 Analisi keyword completata:")
        for spec, data in sorted(specialty_scores.items(), key=lambda x: x[1]['score'], reverse=True):
            print(f"   {spec}: {data['score']:.1f} punti - Keywords: {', '.join(data['matched_keywords'][:3])}")

        # Strategia di fallback a cascata
        results = []

        # 1. Se abbiamo match di specialità, usali
        if specialty_scores:
            best_specialties = sorted(specialty_scores.keys(),
                                      key=lambda x: specialty_scores[x]['score'],
                                      reverse=True)

            for specialty in best_specialties[:2]:  # Top 2 specialità
                matching_doctors = [
                    d for d in all_doctors
                    if d.get_specialization() and specialty.lower() in d.get_specialization().lower()
                ]

                # Priorità geografica
                if patient_city and matching_doctors:
                    city_doctors = []
                    for d in matching_doctors:
                        doctor_city = getattr(d, 'city_of_work', d.get_city())
                        if doctor_city and doctor_city.lower() == patient_city.lower():
                            city_doctors.append(d)

                    results.extend(city_doctors[:2])

                    # Aggiungi altri se necessario
                    remaining = [d for d in matching_doctors if d not in city_doctors]
                    results.extend(remaining[:max_results - len(results)])
                else:
                    results.extend(matching_doctors[:max_results - len(results)])

                if len(results) >= max_results:
                    break

        # 2. Fallback primario: Medicina generale nella stessa città
        if not results and patient_city:
            print(f"🔄 Fallback: Medicina generale in {patient_city}")
            for d in all_doctors:
                spec_lower = d.get_specialization().lower()
                doctor_city = getattr(d, 'city_of_work', d.get_city())

                city_match = doctor_city and doctor_city.lower() == patient_city.lower()
                is_general = 'generale' in spec_lower or 'family' in spec_lower

                if is_general and city_match:
                    results.append(d)
                    if len(results) >= max_results:
                        break

        # 3. Fallback secondario: Medicina generale qualsiasi città
        if not results:
            print("🔄 Fallback: Medicina generale qualsiasi città")
            general_doctors = []
            other_doctors = []

            for d in all_doctors:
                spec_lower = d.get_specialization().lower()
                if 'generale' in spec_lower or 'family' in spec_lower:
                    general_doctors.append(d)
                else:
                    other_doctors.append(d)

            # Priorità sempre alla stessa città, anche per medicina generale
            if patient_city:
                city_general = []
                other_general = []

                for d in general_doctors:
                    doctor_city = getattr(d, 'city_of_work', d.get_city())
                    if doctor_city and doctor_city.lower() == patient_city.lower():
                        city_general.append(d)
                    else:
                        other_general.append(d)

                results = city_general[:max_results]
                if len(results) < max_results:
                    results.extend(other_general[:max_results - len(results)])
            else:
                results = general_doctors[:max_results]

        # 4. Fallback finale: qualsiasi medico
        if not results:
            print("🔄 Fallback finale: qualsiasi medico disponibile")
            results = all_doctors[:max_results]

        final_results = results[:max_results]
        print(f"✅ Fallback completato: {len(final_results)} medici trovati")

        return final_results


def create_semantic_matcher():
    """Factory function per creare un matcher semantico"""
    return SemanticDoctorMatcher()


def enhance_doctor_recommendation(assistant):
    """
    Potenzia un'istanza di LLMAssistant con ricerca semantica
    """
    try:
        # Crea il matcher semantico
        semantic_matcher = SemanticDoctorMatcher()

        # Salva il metodo originale se esiste
        if hasattr(assistant, 'recommend_doctor'):
            original_recommend_doctor = assistant.recommend_doctor

            def enhanced_recommend_doctor(self):
                """Versione migliorata con ricerca semantica"""
                print("🔍 DEBUG: Raccomandazione medico con ricerca semantica avanzata")

                # Ottieni informazioni del paziente
                purpose = self.patient.get_purpose()
                patient_city = self.patient.get_city()

                print(f"📋 Problema: {purpose}")
                print(f"🏙️ Città paziente: {patient_city}")

                if not purpose:
                    print("⚠️ Nessun problema specificato")
                    return

                # Usa tutti i medici caricati dal database
                if not hasattr(self, 'available_doctors') or not self.available_doctors:
                    print("❌ Nessun medico disponibile nel database")
                    return

                # RICERCA SEMANTICA
                recommended_doctors = semantic_matcher.find_best_matching_doctors(
                    problem_description=purpose,
                    all_doctors=self.available_doctors,
                    patient_city=patient_city,
                    max_results=3
                )

                if not recommended_doctors:
                    print("❌ Nessun medico trovato")
                    return

                # Prendi il primo medico come raccomandazione principale
                self.recommended_doctor = recommended_doctors[0]

                # Genera risposta dettagliata
                system_prompt = """
                Sei Longi di Longeviva con ricerca semantica avanzata. 
                Presenta i risultati della ricerca AI in modo professionale e rassicurante.
                Spiega brevemente perché questi medici sono stati selezionati.
                """

                # Prepara informazioni sui medici trovati
                doctors_info = []
                for i, doctor in enumerate(recommended_doctors, 1):
                    city_info = getattr(doctor, 'city_of_work',
                                        getattr(doctor, 'city',
                                                doctor.get_city() if hasattr(doctor,
                                                                             'get_city') else 'Disponibile dopo contatto'))
                    score_info = ""
                    if hasattr(doctor, 'semantic_score'):
                        score_info = f" (Rilevanza AI: {doctor.semantic_score:.1%})"

                    doctors_info.append(f"""
{i}. 👨‍⚕️ **{doctor.get_full_name()}**
   🏥 Specializzazione: {doctor.get_specialization()}
   📍 Città: {city_info}
   ⏱️ Esperienza: {doctor.get_years_of_experience()} anni{score_info}
                    """)

                name = self.patient.get_name() or "utente"

                prompt = f"""
Perfetto, {name}! Ho utilizzato l'intelligenza artificiale per analizzare il tuo problema 
e trovare gli specialisti più adatti.

🧠 **RISULTATI RICERCA SEMANTICA AI:**

{''.join(doctors_info)}

Il sistema ha analizzato semanticamente la tua descrizione "{purpose}" e ha trovato 
questi specialisti con la migliore corrispondenza alle tue esigenze.

Il **Dr. {self.recommended_doctor.get_surname()}** è la mia raccomandazione principale 
per il tuo caso specifico.

Vuoi che ti aiuti a prenotare un appuntamento con uno di questi medici, 
o preferisci avere maggiori informazioni?
                """

                response, _ = self.generate_response(prompt, system_prompt)
                print(f"\nAssistente: {response}")

                # Aggiorna stato conversazione
                self.conversation_state = "doctor_recommendation_provided"
                self.current_question = "booking_preference"

            # Sostituisci il metodo usando il binding corretto
            import types
            assistant.recommend_doctor = types.MethodType(enhanced_recommend_doctor, assistant)

            print("✅ LLMAssistant potenziato con ricerca semantica")
            return True
        else:
            print("⚠️ Metodo recommend_doctor non trovato nell'assistente")
            return False

    except Exception as e:
        print(f"❌ Errore nel potenziamento LLMAssistant: {e}")
        traceback.print_exc()
        return False


def test_semantic_search():
    """Test della ricerca semantica"""
    print("🧪 TEST: Ricerca semantica")

    try:
        matcher = SemanticDoctorMatcher()

        # Crea medici di test
        class TestDoctor:
            def __init__(self, name, surname, specialization, city="Roma"):
                self.name = name
                self.surname = surname
                self.specialization = specialization
                self.city_of_work = city
                self.area_of_interest = ""

            def get_name(self): return self.name

            def get_surname(self): return self.surname

            def get_full_name(self): return f"{self.name} {self.surname}"

            def get_specialization(self): return self.specialization

            def get_city(self): return self.city_of_work

            def get_years_of_experience(self): return 10

        test_doctors = [
            TestDoctor("Mario", "Rossi", "Cardiologia", "Milano"),
            TestDoctor("Anna", "Verdi", "Dermatologia", "Roma"),
            TestDoctor("Luigi", "Bianchi", "Neurologia", "Milano"),
        ]

        # Test ricerca
        results = matcher.find_best_matching_doctors(
            "Ho dolori al petto e battiti irregolari",
            test_doctors,
            patient_city="Milano",
            max_results=2
        )

        print(f"✅ Test completato: {len(results)} risultati")
        for doctor in results:
            print(f"   → {doctor.get_full_name()} - {doctor.get_specialization()}")

    except Exception as e:
        print(f"❌ Errore nel test: {e}")


if __name__ == "__main__":
    test_semantic_search()