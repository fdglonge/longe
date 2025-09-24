#!/usr/bin/env python3

import sys
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional

# Aggiungi percorsi per import
current_dir = os.path.dirname(__file__)
src_dir = os.path.dirname(current_dir)
sys.path.insert(0, src_dir)


def get_patient_diet(patient_id: str, db_client) -> Optional[Dict[str, Any]]:
    """
    Recupera la dieta del paziente dalla subcollection diets

    Args:
        patient_id: ID del paziente
        db_client: Client Firebase Firestore

    Returns:
        Dict contenente la dieta del paziente o None se non trovata
    """
    try:
        print(f"DEBUG: Cercando diete per patient_id: {patient_id}")

        # Accede alla subcollection diets del paziente specifico
        diets_subcollection = db_client.collection('patients').document(patient_id).collection('diets')

        # Ottieni tutte le diete del paziente
        diet_docs = diets_subcollection.get()

        print(f"DEBUG: Trovati {len(diet_docs)} documenti dieta nella subcollection")

        if diet_docs:
            # Prendi la prima dieta disponibile
            diet_doc = diet_docs[0]
            diet_data = diet_doc.to_dict()
            diet_data['id'] = diet_doc.id

            print(f"Dieta trovata - ID: {diet_doc.id}")
            print(f"Nome dieta: {diet_data.get('name', 'N/A')}")

            return diet_data

        print("Nessuna dieta trovata nella subcollection")
        return None

    except Exception as e:
        print(f"Errore nel recuperare la dieta: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def format_diet_context(diet_data: Dict[str, Any]) -> str:
    """
    Formatta i dati della dieta in un contesto leggibile per il modello

    Args:
        diet_data: Dati della dieta dal database

    Returns:
        Stringa formattata con il contesto della dieta
    """
    from datetime import datetime

    context = f"""
INFORMAZIONI DIETA PAZIENTE:

Nome dieta: {diet_data.get('name', 'N/A')}
Tipo dieta: {diet_data.get('dietType', 'N/A')}
Tipo alimentazione: {diet_data.get('foodType', 'N/A')}
Calorie totali giornaliere: {diet_data.get('totalKcal', 'N/A')} kcal
Status: {diet_data.get('status', 'N/A')}

Note aggiuntive: {diet_data.get('additionalNotes', 'Nessuna nota')}

Intolleranze/Allergie: {', '.join(diet_data.get('intolerancesAllergies', [])) if diet_data.get('intolerancesAllergies') else 'Nessuna'}

Ripartizione macronutrienti:
- Carboidrati: {diet_data.get('macronutrientsDivision', {}).get('carbohydrates', 'N/A')}%
- Proteine: {diet_data.get('macronutrientsDivision', {}).get('proteins', 'N/A')}%
- Grassi: {diet_data.get('macronutrientsDivision', {}).get('fats', 'N/A')}%

Pasti coinvolti: {', '.join(diet_data.get('mealsInvolved', [])) if diet_data.get('mealsInvolved') else 'N/A'}

PIANO SETTIMANALE COMPLETO:
"""

    # Mappa giorni inglesi -> italiani
    day_mapping = {
        'Monday': 'Lunedì',
        'Tuesday': 'Martedì',
        'Wednesday': 'Mercoledì',
        'Thursday': 'Giovedì',
        'Friday': 'Venerdì',
        'Saturday': 'Sabato',
        'Sunday': 'Domenica'
    }

    # Ottieni giorno attuale per evidenziarlo
    current_day = datetime.now().strftime('%A')  # Es: 'Monday'

    # Aggiunge il piano settimanale dettagliato
    weekly_plan = diet_data.get('weeklyPlan', [])
    for day_plan in weekly_plan:
        day_eng = day_plan.get('day', 'N/A')
        day_ita = day_mapping.get(day_eng, day_eng)

        # Evidenzia il giorno corrente
        if day_eng == current_day:
            context += f"\n🔥 === {day_ita.upper()} (OGGI) === 🔥\n"
        else:
            context += f"\n--- {day_ita.upper()} ---\n"

        meals = day_plan.get('meals', [])
        daily_total_kcal = 0

        for meal in meals:
            meal_name = meal.get('name', 'N/A')
            total_kcal = meal.get('totalKcal', 'N/A')
            recipe = meal.get('recipe', 'N/A')

            # Converti kcal in numero se possibile
            try:
                kcal_num = int(str(total_kcal).replace('kcal', ''))
                daily_total_kcal += kcal_num
                kcal_display = f"{kcal_num} kcal"
            except:
                kcal_display = str(total_kcal)

            context += f"\n🍽️ {meal_name.upper()} ({kcal_display}):\n"
            context += f"Ricetta: {recipe}\n"

            # Aggiunge gli alimenti del pasto
            foods = meal.get('foods', [])
            if foods:
                context += "Alimenti:\n"
                for food in foods:
                    food_name = food.get('name', 'N/A')
                    weight = food.get('weight', 'N/A')
                    calories = food.get('calories', 'N/A')
                    context += f"  - {food_name}: {weight} ({calories})\n"

            context += f"Macros: {meal.get('totalCarbohydrates', 'N/A')} carb, {meal.get('totalProteins', 'N/A')} prot, {meal.get('totalFats', 'N/A')} grassi\n"

        # Totale giornaliero
        if daily_total_kcal > 0:
            context += f"\nTOTALE {day_ita}: {daily_total_kcal} kcal\n"

    # Aggiunge istruzioni specifiche per oggi
    context += f"\n\n🎯 IMPORTANTE: Quando l'utente chiede 'cosa devo mangiare oggi' o simili, rispondi SEMPRE basandoti ESCLUSIVAMENTE sul piano di OGGI ({day_mapping.get(current_day, current_day)}) specificato sopra. NON inventare pasti diversi!"

    return context


def diet_chat_interface(assistant, patient_data: Dict[str, Any], diet_data: Dict[str, Any]):
    """
    Interfaccia di chat specializzata per domande sulla dieta del paziente

    Args:
        assistant: LLMAssistant instance
        patient_data: Dati del paziente
        diet_data: Dati della dieta del paziente
    """
    print("\n💬 CHAT DIETA PERSONALIZZATA")
    print("=" * 50)
    print("Puoi fare domande sulla tua dieta, chiedere sostituzioni di alimenti o modifiche ai pasti.")
    print("Scrivi 'menu' per tornare al menu principale o 'esci' per uscire.")

    # Prepara il contesto per il modello
    diet_context = format_diet_context(diet_data)
    patient_context = f"""
INFORMAZIONI PAZIENTE:
Nome: {patient_data.get('name', 'N/A')} {patient_data.get('surname', 'N/A')}
Età: {patient_data.get('age', 'N/A')} anni
Sesso: {patient_data.get('gender', 'N/A')}
Peso: {patient_data.get('weight', 'N/A')} kg
Altezza: {patient_data.get('height', 'N/A')} cm
Livello attività: {patient_data.get('activityLevel', 'N/A')}
"""

    system_prompt = f"""
Sei un assistente nutrizionale specializzato. Rispondi ESCLUSIVAMENTE a domande riguardanti la dieta specifica del paziente.

{patient_context}

{diet_context}

ISTRUZIONI:
- Rispondi solo a domande sulla dieta del paziente
- Puoi suggerire sostituzioni alimentari compatibili con la dieta
- Puoi spiegare i pasti e le ricette della dieta
- Puoi fornire consigli su timing e preparazione dei pasti
- NON rispondere a domande generiche su nutrizione non correlate alla dieta specifica
- NON fornire consigli medici
- Se la domanda è fuori contesto, rispondi: "Mi dispiace, posso aiutarti solo con domande specifiche sulla tua dieta personalizzata."

Rispondi sempre in italiano in modo amichevole e professionale.
"""

    # Chat loop
    chat_history = []

    while True:
        try:
            user_input = input("\nTu: ").strip()

            if user_input.lower() in ['menu', 'torna', 'indietro']:
                print("\nTorno al menu principale...")
                break

            elif user_input.lower() in ['esci', 'exit', 'quit']:
                print("\nArrivederci!")
                return 'exit'

            elif not user_input:
                print("Fai una domanda sulla tua dieta!")
                continue

            # Aggiungi alla cronologia
            chat_history.append(f"Utente: {user_input}")

            # Prepara il prompt completo con cronologia recente
            recent_history = "\n".join(chat_history[-6:]) if chat_history else ""

            full_prompt = f"""CRONOLOGIA RECENTE:
{recent_history}

DOMANDA ATTUALE: {user_input}

Rispondi come assistente nutrizionale seguendo le istruzioni del sistema."""

            print("\nAssistente: Elaboro la risposta...")

            try:
                # Usa l'LLM dell'assistente (Mistral tramite Ollama) per generare la risposta
                response, context = assistant.generate_response(full_prompt, system_prompt)

                if response and response.strip():
                    print(f"Assistente Nutrizionale: {response}")
                    chat_history.append(f"Assistente: {response}")
                else:
                    print("Assistente Nutrizionale: Mi dispiace, non riesco a elaborare una risposta al momento.")

            except Exception as e:
                print(f"Errore nella generazione della risposta: {str(e)}")
                print("Assistente Nutrizionale: Mi dispiace, ho avuto un problema tecnico. Riprova!")

        except KeyboardInterrupt:
            print("\nChat interrotta.")
            break
        except Exception as e:
            print(f"Errore: {str(e)}")


def handle_diet_chat_option(assistant):
    """
    Gestisce l'opzione 2 - Chat sulla dieta del paziente

    Args:
        assistant: LLMAssistant instance
    """
    print("\n🍽️ GESTIONE DIETA PERSONALIZZATA")
    print("=" * 50)

    # Verifica che ci sia un paziente
    if not assistant.patient or not assistant.authenticated:
        print("❌ Nessun paziente autenticato")
        print("Devi prima effettuare il login per accedere a questa funzionalità.")
        input("\nPremi INVIO per continuare...")
        return None

    # DEBUG: Mostra informazioni paziente
    print(f"📋 DEBUG Paziente loggato:")
    print(f"   Nome: {assistant.patient.get_name()}")
    print(f"   Cognome: {assistant.patient.get_surname()}")

    # Ottieni l'ID del paziente - prova diversi attributi
    patient_id = None
    patient_data = {}

    # DEBUG: Controlla tutti gli attributi disponibili del paziente
    print(f"📋 DEBUG Attributi paziente disponibili:")
    if hasattr(assistant.patient, '__dict__'):
        for attr, value in assistant.patient.__dict__.items():
            if value is not None:
                print(f"   {attr}: {str(value)[:50]}{'...' if len(str(value)) > 50 else ''}")

    # Prova a ottenere l'ID paziente in diversi modi
    id_attempts = [
        ('assistant.patient.id', getattr(assistant.patient, 'id', None)),
        ('assistant.patient.get_id()', getattr(assistant.patient, 'get_id', lambda: None)()),
        ('assistant.patient.uid', getattr(assistant.patient, 'uid', None)),
        ('assistant.patient.fiscal_code hash', getattr(assistant.patient, 'fiscal_code', None))
    ]

    print(f"\n🔍 DEBUG Tentativo identificazione paziente:")
    for method, value in id_attempts:
        print(f"   {method}: {value}")
        if value and not patient_id:
            patient_id = value

    # Se non trovato con metodi diretti, prova a cercare nel database per nome+cognome
    if not patient_id:
        print(f"⚠️ ID paziente non trovato direttamente, cerco nel database...")

        # Ottieni il client del database
        db_client = None
        if hasattr(assistant, 'patient_db') and hasattr(assistant.patient_db, 'db'):
            db_client = assistant.patient_db.db
        elif hasattr(assistant, 'db'):
            db_client = assistant.db

        if db_client:
            try:
                name = assistant.patient.get_name()
                surname = assistant.patient.get_surname()

                if name and surname:
                    print(f"   Cerco: {name} {surname}")
                    patients_ref = db_client.collection('patients')
                    query = patients_ref.where('name', '==', name).where('surname', '==', surname)
                    results = query.get()

                    if results:
                        patient_doc = results[0]
                        patient_id = patient_doc.id
                        print(f"   ✅ Trovato nel database: {patient_id}")
                    else:
                        print(f"   ❌ Paziente non trovato nel database")

            except Exception as e:
                print(f"   ❌ Errore ricerca database: {e}")

    if not patient_id:
        print("❌ Impossibile identificare il paziente")
        print("Problema tecnico nell'identificazione del profilo.")
        input("\nPremi INVIO per continuare...")
        return None

    print(f"\n🆔 ID Paziente identificato: {patient_id}")
    print(f"🔍 Cerco la dieta per il paziente: {assistant.patient.get_name()}")

    # Ottieni il client del database
    db_client = None
    if hasattr(assistant, 'patient_db') and hasattr(assistant.patient_db, 'db'):
        db_client = assistant.patient_db.db
    elif hasattr(assistant, 'db'):
        db_client = assistant.db
    else:
        print("❌ Impossibile accedere al database")
        print("Problema tecnico nella connessione al database.")
        input("\nPremi INVIO per continuare...")
        return None

    # Recupera la dieta del paziente
    diet_data = get_patient_diet(patient_id, db_client)

    if diet_data is None:
        # Nessuna dieta trovata
        print("⚠️ NON È PRESENTE ALCUNA DIETA")
        print("Torna indietro per schedulare un meeting con un nostro nutrizionista")
        print("")
        print("Cosa vuoi fare?")
        print("1. Torna al menu principale")
        print("2. Prenota appuntamento nutrizionista")

        while True:
            try:
                choice = input("\nScegli (1/2): ").strip()
                if choice == '1':
                    return None
                elif choice == '2':
                    print("\nReindirizzo alla prenotazione appuntamento...")
                    return 'book_appointment'
                else:
                    print("Scegli 1 o 2")
            except KeyboardInterrupt:
                return None

    else:
        # Dieta trovata - costruisci i dati del paziente
        patient_data = {
            'name': assistant.patient.get_name(),
            'surname': assistant.patient.get_surname(),
            'age': assistant.patient.get_age(),
            'gender': assistant.patient.get_sex(),
            'weight': assistant.patient.get_weight(),
            'height': assistant.patient.get_height(),
            'activityLevel': getattr(assistant.patient, 'activity_level', 'N/A')
        }

        print(f"✅ Dieta trovata: {diet_data.get('name', 'Senza nome')}")
        print(f"📊 {diet_data.get('totalKcal', 'N/A')} kcal/giorno - {diet_data.get('dietType', 'N/A')}")
        print()

        # Avvia l'interfaccia di chat
        result = diet_chat_interface(assistant, patient_data, diet_data)

        return result