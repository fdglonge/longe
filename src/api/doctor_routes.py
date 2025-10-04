# src/api/routes/doctor_routes.py
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
import traceback

from .schemas.doctor_schemas import (
    RaccomandaDottoreResponse,
    DoctorInfo
)
from ..dependencies import get_patient_handler
from ..Patient.patients_handler import PatientHandler
from ..Doctor.doctors_handler import DoctorHandler
from ..utils.semantic_search import SemanticDoctorMatcher

router = APIRouter()

# Inizializza il matcher semantico globalmente
semantic_matcher = SemanticDoctorMatcher()


def _parse_patient_data(additional_notes):
    """
    Estrae preferenze E motivo visita da additionalNotes

    Returns:
        tuple: (preferences dict, motivo_visita str)
    """
    # Inizializza a None per capire se i valori vengono trovati
    preferences = {
        'vicinanza': None,
        'specializzazione': None,
        'costo': None,
        'area_interesse': None
    }

    motivo_visita = None

    if not additional_notes:
        print("⚠️ additionalNotes vuoto")
        # Usa default solo se completamente vuoto
        for key in preferences:
            preferences[key] = 3
        return preferences, motivo_visita

    print(f"📄 DEBUG: Parsing additionalNotes")

    lines = additional_notes.split('\n')
    in_motivo_section = False
    motivo_lines = []

    for line in lines:
        line_stripped = line.strip()

        # Cerca sezione MOTIVO VISITA
        if '=== MOTIVO VISITA ===' in line_stripped:
            in_motivo_section = True
            continue

        # Fine sezione motivo
        if in_motivo_section and '===' in line_stripped:
            in_motivo_section = False
            continue

        # Raccogli righe motivo
        if in_motivo_section and line_stripped:
            motivo_lines.append(line_stripped)

        # Parse preferenze - VERSIONE CORRETTA
        # Rimuovi bullet point e normalizza
        clean_line = line_stripped.replace('•', '').replace('*', '').strip()

        if 'Vicinanza:' in clean_line or 'vicinanza:' in clean_line.lower():
            try:
                parts = clean_line.split(':')[1].strip()
                value = int(parts.split('/')[0].strip())
                preferences['vicinanza'] = value
                print(f"✓ Vicinanza trovata: {value}")
            except Exception as e:
                print(f"✗ Errore parsing Vicinanza: {e}")

        elif 'Specializzazione:' in clean_line or 'specializzazione:' in clean_line.lower():
            try:
                parts = clean_line.split(':')[1].strip()
                value = int(parts.split('/')[0].strip())
                preferences['specializzazione'] = value
                print(f"✓ Specializzazione trovata: {value}")
            except Exception as e:
                print(f"✗ Errore parsing Specializzazione: {e}")

        elif 'Costo:' in clean_line or 'costo:' in clean_line.lower():
            try:
                parts = clean_line.split(':')[1].strip()
                value = int(parts.split('/')[0].strip())
                preferences['costo'] = value
                print(f"✓ Costo trovato: {value}")
            except Exception as e:
                print(f"✗ Errore parsing Costo: {e}")

        elif 'Area di Interesse:' in clean_line or 'Area Interesse:' in clean_line or 'area interesse:' in clean_line.lower():
            try:
                parts = clean_line.split(':')[1].strip()
                value = int(parts.split('/')[0].strip())
                preferences['area_interesse'] = value
                print(f"✓ Area Interesse trovata: {value}")
            except Exception as e:
                print(f"✗ Errore parsing Area Interesse: {e}")

    # Motivo visita
    motivo_visita = ' '.join(motivo_lines) if motivo_lines else None

    # Assegna valori di default SOLO per quelli non trovati
    for key in preferences:
        if preferences[key] is None:
            preferences[key] = 3
            print(f"⚠️ {key} non trovato, uso default: 3")

    print(f"✅ Preferenze finali: {preferences}")
    print(f"✅ Motivo visita: {motivo_visita}")

    return preferences, motivo_visita


def _apply_preference_adjustments(doctors_with_semantic_scores, patient_preferences):
    """
    Applica aggiustamenti basati su preferenze paziente (costo, area)
    mantenendo il semantic score come base
    """
    for doctor_info in doctors_with_semantic_scores:
        # Parte dal semantic score (già calcolato)
        base_score = doctor_info.match_score or 50

        # COSTO: aggiusta in base a preferenza
        peso_costo = patient_preferences.get('costo', 3)
        tariffa = doctor_info.tariffa_oraria

        costo_adjustment = 0
        if peso_costo >= 4:  # Costo molto importante
            if tariffa <= 70:
                costo_adjustment = 10
            elif tariffa <= 90:
                costo_adjustment = 5
            elif tariffa <= 110:
                costo_adjustment = 0
            else:
                costo_adjustment = -10
        elif peso_costo >= 2:
            if tariffa <= 90:
                costo_adjustment = 5
            else:
                costo_adjustment = 0

        # AREA INTERESSE: bonus se presente e importante
        peso_area = patient_preferences.get('area_interesse', 3)
        area_adjustment = 0
        if doctor_info.area_interesse and peso_area >= 4:
            area_adjustment = 5

        # Score finale
        doctor_info.match_score = min(100, base_score + costo_adjustment + area_adjustment)

    return doctors_with_semantic_scores


@router.get("/raccomanda_dottore", response_model=RaccomandaDottoreResponse)
async def raccomanda_dottore(
        email: Optional[str] = Query(None, description="Email del paziente per raccomandazioni personalizzate"),
        patient_handler: PatientHandler = Depends(get_patient_handler)
):
    """
    Raccomanda dottori usando ricerca semantica AI.

    - Se email fornita: usa semantic search + preferenze paziente
    - Se email NON fornita: ritorna tutti i dottori disponibili
    """
    try:
        doctor_handler = DoctorHandler()

        # CASO 1: CON EMAIL - Raccomandazioni personalizzate con AI
        if email:
            # Cerca paziente
            patient = patient_handler.search_patient_by_email(email)

            if not patient:
                raise HTTPException(
                    status_code=404,
                    detail=f"Paziente non trovato con email: {email}"
                )

            # Estrai preferenze E motivo visita
            additional_notes = patient.get_additional_notes() or ""
            patient_preferences, motivo_visita = _parse_patient_data(additional_notes)
            patient_city = patient.get_city()

            print(f"Città paziente: {patient_city}")

            if not motivo_visita:
                raise HTTPException(
                    status_code=400,
                    detail="Motivo della visita non trovato. Completa prima la storia medica."
                )

            # Ottieni tutti i dottori
            all_doctors = doctor_handler.get_all_doctors()

            if not all_doctors:
                return RaccomandaDottoreResponse(
                    success=True,
                    message="Nessun dottore disponibile",
                    dottori=[],
                    criteri_ricerca=patient_preferences,
                    total_dottori=0
                )

            # USA RICERCA SEMANTICA
            print("Avvio ricerca semantica AI...")
            recommended_doctors = semantic_matcher.find_best_matching_doctors(
                problem_description=motivo_visita,
                all_doctors=all_doctors,
                patient_city=patient_city,
                max_results=10
            )

            if not recommended_doctors:
                return RaccomandaDottoreResponse(
                    success=True,
                    message="Nessun dottore trovato con i criteri specificati",
                    dottori=[],
                    criteri_ricerca=patient_preferences,
                    total_dottori=0
                )

            # Converti in DoctorInfo mantenendo semantic score
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

            # Applica aggiustamenti per costo e area interesse
            doctors_with_scores = _apply_preference_adjustments(doctors_with_scores, patient_preferences)

            # Riordina per score finale
            doctors_with_scores.sort(key=lambda d: d.match_score, reverse=True)

            # Prendi top 5
            top_doctors = doctors_with_scores[:5]

            return RaccomandaDottoreResponse(
                success=True,
                message=f"Trovati {len(top_doctors)} dottori raccomandati tramite AI semantica",
                dottori=top_doctors,
                criteri_ricerca=patient_preferences,
                total_dottori=len(doctors_with_scores)
            )

        # CASO 2: SENZA EMAIL - Tutti i dottori
        else:
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
                message=f"Trovati {len(doctors_list)} dottori disponibili",
                dottori=doctors_list,
                criteri_ricerca=None,
                total_dottori=len(doctors_list)
            )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Errore in raccomanda_dottore: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Errore interno: {str(e)}")