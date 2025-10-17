# LLM/llm_assistant_food_diary.py
"""
Estensione per la classe LLMAssistant che aggiunge funzionalità di diario alimentare
"""

from datetime import datetime
import re


def extend_llm_assistant_with_food_diary(LLMAssistantClass):
    """
    Estende la classe LLMAssistant esistente con funzionalità di diario alimentare
    """

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
        return self._food_diary_conversation_loop(system_prompt)

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
- Incoraggi sempre il paziente nei suoi sforzi
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
                    self.save_food_diary_session()
                    break

                elif user_input.lower() in ['esci', 'exit', 'quit']:
                    print("\nLongi: Ciao! Ricorda di prenderti cura della tua alimentazione! 🌟")
                    self.save_food_diary_session()
                    return 'exit'

                elif not user_input:
                    print("Dimmi qualcosa! Sono qui per aiutarti! 😊")
                    continue

                # Processa l'input alimentare
                self._process_food_diary_input(user_input, system_prompt)

            except KeyboardInterrupt:
                print("\nLongi: Alla prossima! Continua a fare scelte alimentari sagge! 👋")
                self.save_food_diary_session()
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
        """Salva la sessione del diario alimentare"""
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

            print(f"\n📊 Sessione diario alimentare completata:")
            print(f"   Durata: {session_summary['duration_minutes']:.1f} minuti")
            print(f"   Messaggi scambiati: {session_summary['entries_count']}")

            # TODO: Implementare salvataggio nel database Firebase
            # self._save_to_firebase(session_summary)

        except Exception as e:
            print(f"⚠️ Errore nel salvare la sessione: {e}")

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

    def _analyze_food_content(self, food_description):
        """Analizza il contenuto nutrizionale del cibo descritto"""
        food_lower = food_description.lower()

        # Database semplice di analisi nutrizionale
        nutrition_analysis = {
            'proteins': [],
            'carbs': [],
            'fats': [],
            'vegetables': [],
            'fruits': [],
            'processed': [],
            'healthy_choices': [],
            'suggestions': []
        }

        # Proteine
        protein_foods = ['pollo', 'pesce', 'carne', 'uova', 'legumi', 'fagioli', 'lenticchie', 'ceci', 'tonno',
                         'salmone']
        for protein in protein_foods:
            if protein in food_lower:
                nutrition_analysis['proteins'].append(protein)
                nutrition_analysis['healthy_choices'].append(f"Ottima fonte di proteine: {protein}")

        # Carboidrati
        carb_foods = ['pasta', 'riso', 'pane', 'patate', 'cereali', 'avena', 'quinoa', 'farro']
        for carb in carb_foods:
            if carb in food_lower:
                nutrition_analysis['carbs'].append(carb)
                if carb in ['quinoa', 'farro', 'avena']:
                    nutrition_analysis['healthy_choices'].append(f"Carboidrato complesso eccellente: {carb}")

        # Verdure
        vegetable_foods = ['insalata', 'pomodori', 'zucchine', 'broccoli', 'spinaci', 'carote', 'verdure']
        for veg in vegetable_foods:
            if veg in food_lower:
                nutrition_analysis['vegetables'].append(veg)
                nutrition_analysis['healthy_choices'].append(f"Ricco di vitamine e fibre: {veg}")

        # Suggerimenti basati sull'analisi
        if not nutrition_analysis['vegetables']:
            nutrition_analysis['suggestions'].append(
                "Prova ad aggiungere più verdure al pasto per aumentare vitamine e fibre")

        if not nutrition_analysis['proteins']:
            nutrition_analysis['suggestions'].append(
                "Considera l'aggiunta di una fonte proteica per un pasto più bilanciato")

        return nutrition_analysis

    # Aggiungi tutti i metodi alla classe
    LLMAssistantClass.start_food_diary_mode = start_food_diary_mode
    LLMAssistantClass._create_food_diary_system_prompt = _create_food_diary_system_prompt
    LLMAssistantClass._create_food_diary_welcome_prompt = _create_food_diary_welcome_prompt
    LLMAssistantClass.get_patient_context_for_nutrition = get_patient_context_for_nutrition
    LLMAssistantClass._food_diary_conversation_loop = _food_diary_conversation_loop
    LLMAssistantClass._process_food_diary_input = _process_food_diary_input
    LLMAssistantClass._build_conversation_context = _build_conversation_context
    LLMAssistantClass.save_food_diary_session = save_food_diary_session
    LLMAssistantClass._create_advanced_nutrition_prompt = _create_advanced_nutrition_prompt
    LLMAssistantClass._analyze_food_content = _analyze_food_content

    return LLMAssistantClass


# Funzione per applicare l'estensione automaticamente
def apply_food_diary_extension():
    """Applica automaticamente l'estensione del diario alimentare"""
    try:
        from src.LLM.llm_assistant import LLMAssistant
        extend_llm_assistant_with_food_diary(LLMAssistant)
        print("✅ Estensione diario alimentare applicata con successo")
        return True
    except ImportError as e:
        print(f"❌ Errore nell'applicare l'estensione: {e}")
        return False