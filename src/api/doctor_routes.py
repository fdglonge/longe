# src/api/doctor_routes.py
from fastapi import APIRouter, HTTPException, Depends
import traceback

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


def _apply_preference_adjustments(doctors_with_scores, preferences):
    """Applica aggiustamenti basati su preferenze paziente"""
    for doctor_info in doctors_with_scores:
        base_score = doctor_info.match_score or 50

        # Aggiustamento COSTO
        peso_costo = preferences.costo
        tariffa = doctor_info.tariffa_oraria
        costo_adj = 0
        if peso_costo >= 4:
            if tariffa <= 70:
                costo_adj = 10
            elif tariffa <= 90:
                costo_adj = 5
            elif tariffa > 110:
                costo_adj = -10

        # Aggiustamento AREA INTERESSE
        peso_area = preferences.area_interesse
        area_adj = 0
        if doctor_info.area_interesse and peso_area >= 4:
            area_adj = 5

        doctor_info.match_score = min(100, base_score + costo_adj + area_adj)

    return doctors_with_scores


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

        # Ricerca semantica con città
        recommended_doctors = semantic_matcher.find_best_matching_doctors(
            problem_description=request.motivo_visita,
            all_doctors=all_doctors,
            patient_city=request.citta,
            max_results=10
        )

        if not recommended_doctors:
            return RaccomandaDottoreResponse(
                success=True,
                message="Nessun dottore trovato",
                dottori=[],
                total_dottori=0
            )

        # Converti in DoctorInfo
        doctors_with_scores = []
        for doctor in recommended_doctors:
            semantic_score = getattr(doctor, 'semantic_score', 0.5) * 100

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
                match_score=semantic_score
            )
            doctors_with_scores.append(doctor_info)

        # Applica aggiustamenti con preferenze
        doctors_with_scores = _apply_preference_adjustments(doctors_with_scores, request.scelta_medico)

        # Ordina e prendi top 5
        doctors_with_scores.sort(key=lambda d: d.match_score, reverse=True)
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