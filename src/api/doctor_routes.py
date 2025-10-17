# src/api/doctor_routes.py
from fastapi import APIRouter, HTTPException, Depends
import traceback
import numpy as np

from api.schemas.doctor_schemas import (
    RaccomandaDottoreRequest,
    RaccomandaDottoreResponse,
    DoctorInfo
)
from dependencies import get_patient_handler
from Patient.patients_handler import PatientHandler
from Doctor.doctors_handler import DoctorHandler
from utils.semantic_search import SemanticDoctorMatcher

router = APIRouter()

semantic_matcher = SemanticDoctorMatcher()


def calculate_matching_score(doctor, semantic_score: float, preferences: dict, patient_city: str) -> float:
    """
    Calcola il matching score usando la formula:

    Σ(i=1 to n) [sim_cos(embedding_score_i) × user_score_i] / (n × max_score)

    Dove:
    - n = numero di variabili considerate (4: vicinanza, specializzazione, costo, area_interesse)
    - sim_cos(embedding_score) = similarità coseno normalizzata [0,1]
    - user_score = importanza data dall'utente [1,5]
    - max_score = 5 (punteggio massimo possibile)
    """

    # Parametri
    n = 4  # 4 variabili: vicinanza, specializzazione, costo, area_interesse
    max_score = 5

    # 1. VICINANZA - embedding score basato su città
    if patient_city and doctor.get_city():
        vicinanza_embedding = 1.0 if doctor.get_city().lower() == patient_city.lower() else 0.3
    else:
        vicinanza_embedding = 0.5  # default se non abbiamo info città

    # 2. SPECIALIZZAZIONE - usa il semantic_score già calcolato
    specializzazione_embedding = semantic_score  # già in range [0,1]

    # 3. COSTO - normalizza tariffa in [0,1] (inverso: più basso = meglio)
    # Assumiamo range tariffe 50€-200€
    tariffa = doctor.get_hourly_fees()
    costo_embedding = max(0, min(1, 1 - (tariffa - 50) / 150))  # inverso e normalizzato

    # 4. AREA INTERESSE - match binario
    if doctor.get_area_of_interest():
        area_embedding = 1.0  # ha un'area di interesse definita
    else:
        area_embedding = 0.5  # non specificata

    # User scores dalle preferenze
    user_vicinanza = preferences.get('vicinanza', 3)
    user_specializzazione = preferences.get('specializzazione', 3)
    user_costo = preferences.get('costo', 3)
    user_area = preferences.get('area_interesse', 3)

    # Applica la formula
    numeratore = (
            (vicinanza_embedding * user_vicinanza) +
            (specializzazione_embedding * user_specializzazione) +
            (costo_embedding * user_costo) +
            (area_embedding * user_area)
    )

    denominatore = n * max_score

    matching_score = (numeratore / denominatore) * 100  # converti in percentuale

    return min(100, max(0, matching_score))  # clamp tra 0 e 100


@router.post("/raccomanda_dottore", response_model=RaccomandaDottoreResponse)
async def raccomanda_dottore(
        request: RaccomandaDottoreRequest,
        patient_handler: PatientHandler = Depends(get_patient_handler)
):
    try:
        doctor_handler = DoctorHandler()
        all_doctors = doctor_handler.get_all_doctors()

        if not all_doctors:
            return RaccomandaDottoreResponse(
                success=True,
                message="Nessun dottore disponibile",
                dottori=[],
                total_dottori=0
            )

        # Ricerca semantica (ottiene semantic_score per specializzazione)
        recommended_doctors = semantic_matcher.find_best_matching_doctors(
            problem_description=request.motivo_visita,
            all_doctors=all_doctors,
            patient_city=request.citta,
            max_results=20  # prendiamo più candidati per riordinarli con la nuova formula
        )

        if not recommended_doctors:
            return RaccomandaDottoreResponse(
                success=True,
                message="Nessun dottore trovato",
                dottori=[],
                total_dottori=0
            )

        # Converti le preferenze da SceltaMedico a dict
        preferences = {
            'vicinanza': request.scelta_medico.vicinanza,
            'specializzazione': request.scelta_medico.specializzazione,
            'costo': request.scelta_medico.costo,
            'area_interesse': request.scelta_medico.area_interesse
        }

        # Calcola il matching score con la NUOVA FORMULA
        doctors_with_scores = []
        for doctor in recommended_doctors:
            # Semantic score dalla ricerca (già in range [0,1])
            semantic_score = getattr(doctor, 'semantic_score', 0.5)

            # CALCOLA MATCHING SCORE CON LA FORMULA
            matching_score = calculate_matching_score(
                doctor=doctor,
                semantic_score=semantic_score,
                preferences=preferences,
                patient_city=request.citta
            )

            doctor_info = DoctorInfo(
                id=doctor.id or "unknown",
                nome=doctor.get_name(),
                cognome=doctor.get_surname(),
                specializzazione=doctor.get_specialization(),
                citta=doctor.get_city(),
                indirizzo=doctor.get_address(),
                telefono=doctor.get_phone(),
                email=doctor.get_email(),
                tariffa_oraria=doctor.get_hourly_fees(),
                organizzazione=doctor.get_organization(),
                lingue=doctor.get_languages_spoken(),
                area_interesse=doctor.get_area_of_interest(),
                foto_profilo=doctor.get_profile_picture_url(),
                match_score=matching_score
            )
            doctors_with_scores.append(doctor_info)

        # Ordina per matching score
        doctors_with_scores.sort(key=lambda d: d.match_score, reverse=True)

        # Prendi top 5
        top_doctors = doctors_with_scores[:5]

        return RaccomandaDottoreResponse(
            success=True,
            message=f"Trovati {len(top_doctors)} dottori",
            dottori=top_doctors,
            total_dottori=len(doctors_with_scores)
        )

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))