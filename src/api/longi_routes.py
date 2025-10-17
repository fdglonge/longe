# src/api/routes/longi_routes.py
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
import traceback
from collections import defaultdict
import re

from .schemas.longi_schemas import GeneraListaSpesaResponse
from src.dependencies import get_patient_handler, get_vertex_llm
from src.Patient.patients_handler import PatientHandler
from src.LLM.vertex_llm_instance import VertexLLM

router = APIRouter()


def _extract_ingredients_from_diet(diet_data: dict) -> dict:
    """
    Estrae tutti gli ingredienti dalla dieta e li organizza per categoria pasto
    """
    ingredients = {
        'colazioni': defaultdict(list),
        'pranzi': defaultdict(list),
        'spuntini': defaultdict(list),
        'cene': defaultdict(list)
    }

    weekly_plan = diet_data.get('weeklyPlan', [])

    for day_plan in weekly_plan:
        meals = day_plan.get('meals', [])

        for meal in meals:
            meal_name = meal.get('name', '').lower()
            foods = meal.get('foods', [])

            # Categorizza il pasto
            category = None
            if 'colazione' in meal_name or 'breakfast' in meal_name:
                category = 'colazioni'
            elif 'pranzo' in meal_name or 'lunch' in meal_name:
                category = 'pranzi'
            elif 'spuntino' in meal_name or 'snack' in meal_name:
                category = 'spuntini'
            elif 'cena' in meal_name or 'dinner' in meal_name:
                category = 'cene'

            if not category:
                continue

            # Aggiungi ingredienti
            for food in foods:
                food_name = food.get('name', '')
                weight = food.get('weight', '')

                if food_name:
                    ingredients[category][food_name].append(weight)

    return ingredients


def _aggregate_quantities(quantities: list) -> str:
    """
    Aggrega le quantità di un ingrediente
    Esempio: ['100g', '150g', '100g'] -> 'circa 350g totali'
    """
    if not quantities:
        return "q.b."

    total_grams = 0
    total_ml = 0
    count = 0

    for qty in quantities:
        qty_str = str(qty).lower()
        try:
            # Estrai numeri dalla stringa
            numbers = re.findall(r'\d+', qty_str)
            if numbers:
                num = int(numbers[0])
                count += 1

                if 'ml' in qty_str:
                    total_ml += num
                elif 'g' in qty_str:
                    total_grams += num
        except:
            pass

    # Formatta risultato
    if total_grams > 0 and total_ml > 0:
        return f"{total_grams}g + {total_ml}ml"
    elif total_grams > 0:
        return f"{total_grams}g"
    elif total_ml > 0:
        return f"{total_ml}ml"
    else:
        return f"{len(quantities)} porzioni"


def _generate_shopping_list_with_ai(diet_data: dict, llm: VertexLLM) -> str:
    """
    Genera la lista della spesa usando Vertex AI Mistral con prompt ottimizzato
    """
    print("Generazione lista spesa con Mistral AI...")

    # Estrai e aggrega ingredienti
    ingredients = _extract_ingredients_from_diet(diet_data)

    # System prompt CHIARO E SPECIFICO
    system_prompt = """Sei un assistente nutrizionale che crea liste della spesa professionali.

REGOLE IMPORTANTI:
1. Mantieni le quantità totali già calcolate (NON ricalcolare)
2. Organizza per categoria: COLAZIONI, PRANZI, SPUNTINI, CENE
3. Usa un formato pulito e leggibile
4. Ordina alfabeticamente gli ingredienti in ogni categoria
5. NON aggiungere commenti o note extra
6. Rispondi SOLO con la lista formattata"""

    # Prepara dati aggregati
    diet_name = diet_data.get('name', 'Dieta')

    sections = []
    categories = [
        ('colazioni', 'COLAZIONI'),
        ('pranzi', 'PRANZI'),
        ('spuntini', 'SPUNTINI'),
        ('cene', 'CENE')
    ]

    for cat_key, cat_name in categories:
        items = ingredients.get(cat_key, {})
        if items:
            lines = [f"- {food}: {_aggregate_quantities(qty)}"
                     for food, qty in sorted(items.items())]
            sections.append(f"=== {cat_name} ===\n" + "\n".join(lines))

    ingredients_text = "\n\n".join(sections)

    # User prompt
    user_prompt = f"""Crea una lista della spesa settimanale per "{diet_name}".

INGREDIENTI AGGREGATI:
{ingredients_text}

Formatta in modo professionale mantenendo le quantità totali già calcolate.
Non inventare ingredienti, usa solo quelli forniti."""

    try:
        print("Chiamata Mistral AI...")
        response, _ = llm.generate_response(user_prompt, system_prompt)

        # Verifica che non sia fallback
        if "Benvenuto" in response or "Longi" in response or not response.strip():
            print("WARNING: Response non valida, uso fallback")
            return _generate_fallback_shopping_list(ingredients)

        return response.strip()

    except Exception as e:
        print(f"ERROR: {e}")
        traceback.print_exc()
        return _generate_fallback_shopping_list(ingredients)


def _generate_fallback_shopping_list(ingredients: dict) -> str:
    """
    Lista della spesa pulita senza AI (fallback)
    """
    text = "LISTA DELLA SPESA SETTIMANALE\n"
    text += "=" * 60 + "\n\n"

    categories = [
        ('colazioni', 'COLAZIONI'),
        ('pranzi', 'PRANZI'),
        ('spuntini', 'SPUNTINI'),
        ('cene', 'CENE')
    ]

    for category_key, category_title in categories:
        items = ingredients.get(category_key, {})
        if items:
            text += f"=== {category_title} ===\n"

            for food, quantities in sorted(items.items()):
                aggregated = _aggregate_quantities(quantities)
                text += f"- {food}: {aggregated}\n"

            text += "\n"

    text += "=" * 60 + "\n"
    text += "Nota: Controlla la dispensa prima di acquistare.\n"

    return text


@router.get("/diete/{id_dieta}/genera_lista_spesa", response_model=GeneraListaSpesaResponse)
async def genera_lista_spesa(
        id_dieta: str,
        patient_handler: PatientHandler = Depends(get_patient_handler),
        llm: VertexLLM = Depends(get_vertex_llm)
):
    """
    Genera una lista della spesa settimanale per una dieta usando AI.
    """
    try:
        db = patient_handler.db

        if not db:
            raise HTTPException(
                status_code=500,
                detail="Database non disponibile"
            )

        print(f"Ricerca dieta: {id_dieta}")

        # Cerca dieta
        patients_ref = db.collection('patients')
        patients_docs = patients_ref.stream()

        diet_data = None
        for patient_doc in patients_docs:
            try:
                diet_ref = db.collection('patients').document(patient_doc.id).collection('diets').document(id_dieta)
                diet_doc = diet_ref.get()

                if diet_doc.exists:
                    diet_data = diet_doc.to_dict()
                    diet_data['id'] = diet_doc.id
                    print(f"Dieta trovata")
                    break
            except:
                continue

        if not diet_data:
            raise HTTPException(
                status_code=404,
                detail=f"Dieta non trovata: {id_dieta}"
            )

        if 'weeklyPlan' not in diet_data or not diet_data['weeklyPlan']:
            raise HTTPException(
                status_code=400,
                detail="La dieta non ha un piano settimanale"
            )

        # Genera lista spesa
        lista_spesa = _generate_shopping_list_with_ai(diet_data, llm)

        return GeneraListaSpesaResponse(
            success=True,
            message="Lista della spesa generata con successo",
            id_dieta=id_dieta,
            lista_spesa=lista_spesa,
            generated_at=datetime.now().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Errore: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Errore interno: {str(e)}")