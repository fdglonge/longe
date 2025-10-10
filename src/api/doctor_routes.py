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

        recommended_doctors = semantic_matcher.find_best_matching_doctors(
            problem_description=request.messaggio,
            all_doctors=all_doctors,
            patient_city=None,
            max_results=10
        )

        if not recommended_doctors:
            return RaccomandaDottoreResponse(
                success=True,
                message="Nessun dottore trovato",
                dottori=[],
                total_dottori=0
            )

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


@router.get("/lista_tutti_dottori", response_model=RaccomandaDottoreResponse)
async def lista_tutti_dottori():
    try:
        doctor_handler = DoctorHandler()
        all_doctors = doctor_handler.get_all_doctors()

        doctors_list = []
        for doctor in all_doctors:
            if doctor.is_active_doctor():
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
                    match_score=None
                )
                doctors_list.append(doctor_info)

        return RaccomandaDottoreResponse(
            success=True,
            message=f"Lista di {len(doctors_list)} dottori",
            dottori=doctors_list,
            total_dottori=len(doctors_list)
        )

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))