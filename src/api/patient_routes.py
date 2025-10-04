# src/api/routes/patient_routes.py
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
import traceback

from .schemas.patient_schemas import (
    InserisciAnagraficaRequest,
    InserisciAnagraficaResponse,
    CompletaStoriaMedicaRequest,
    CompletaStoriaMedicaResponse,
    RiceviSommarioResponse,
    PatientSummaryInfo,
    SommarioCompleto
)
from ..dependencies import get_patient_handler
from ..Patient.patients_handler import PatientHandler
from ..Patient.patient_instance import Patient

router = APIRouter()


def _format_obiettivi_text(obiettivi, scelta_medico, motivo_visita):
    """Formatta gli obiettivi come nel tuo esempio Firebase"""

    # Estrai le scelte selezionate usando le opzioni dal body
    motivo_scelte = [obiettivi.motivo_scaricamento.opzioni_disponibili[i - 1]
                     for i in obiettivi.motivo_scaricamento.risposta]

    obiettivi_scelte = [obiettivi.obiettivi_principali.opzioni_disponibili[i - 1]
                        for i in obiettivi.obiettivi_principali.risposta]

    aspettative_scelte = [obiettivi.aspettative_percorso.opzioni_disponibili[i - 1]
                          for i in obiettivi.aspettative_percorso.risposta]

    text = f"""=== PROFILO MOTIVAZIONALE ===
Hai scelto Longeviva perché {', '.join(motivo_scelte).lower()}.

I tuoi obiettivi principali sono {', '.join(obiettivi_scelte).lower()}.

Ti aspetti {', '.join(aspettative_scelte).lower()}.

=== MOTIVO VISITA ===
{motivo_visita}

=== PREFERENZE MEDICO ===
- Vicinanza: {scelta_medico.vicinanza}/5
- Specializzazione: {scelta_medico.specializzazione}/5
- Costo: {scelta_medico.costo}/5
- Area di Interesse: {scelta_medico.area_interesse}/5"""

    return text


@router.post("/inserisci_anagrafica", response_model=InserisciAnagraficaResponse)
async def inserisci_anagrafica(
        request: InserisciAnagraficaRequest,
        patient_handler: PatientHandler = Depends(get_patient_handler)
):
    """
    Inserisce l'anagrafica di un nuovo paziente.
    Il codice fiscale viene calcolato automaticamente.
    """
    try:
        dati = request.dati_personali

        # 1. CALCOLA CODICE FISCALE AUTOMATICAMENTE
        from utils.codice_fiscale_utils import calcola_codice_fiscale

        codice_fiscale = calcola_codice_fiscale(
            nome=dati.nome,
            cognome=dati.cognome,
            sesso=dati.sesso,
            data_nascita=dati.data_nascita,
            comune_nascita=dati.citta_nascita
        )

        print(f"Codice fiscale calcolato: {codice_fiscale}")

        # 2. Controllo duplicati
        if patient_handler.check_email_exists(dati.email):
            raise HTTPException(
                status_code=400,
                detail="Email già registrata nel sistema"
            )

        if patient_handler.check_fiscal_code_exists(codice_fiscale):
            raise HTTPException(
                status_code=400,
                detail="Codice fiscale già presente (possibile duplicato)"
            )

        # 3. Crea oggetto Patient
        patient = Patient()
        patient.set_name(dati.nome)
        patient.set_surname(dati.cognome)
        patient.set_contact_info(email=dati.email)
        patient.set_fiscal_code(codice_fiscale)
        patient.set_sex(dati.sesso)
        patient.set_height(dati.altezza)
        patient.set_weight(dati.peso)

        # Converti data nascita in formato Firebase
        birth_date = datetime.strptime(dati.data_nascita, '%Y-%m-%d')
        patient.set_birth_date(birth_date.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3])

        # Note con città
        patient.set_additional_notes(
            f"Città di nascita: {dati.citta_nascita}\n"
            f"Città di residenza: {dati.citta_residenza}"
        )

        # 4. Salva nel database
        patient_id, generated_password = patient_handler.save_patient(patient)

        if not patient_id:
            raise HTTPException(
                status_code=500,
                detail="Errore durante il salvataggio del paziente"
            )

        # 5. Response
        return InserisciAnagraficaResponse(
            success=True,
            message="Anagrafica inserita con successo",
            patient_id=patient_id,
            email=dati.email,
            password=generated_password,
            codice_fiscale=codice_fiscale
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Errore in inserisci_anagrafica: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Errore interno: {str(e)}")


@router.post("/completa_storiamedica", response_model=CompletaStoriaMedicaResponse)
async def completa_storiamedica(
        request: CompletaStoriaMedicaRequest,
        patient_handler: PatientHandler = Depends(get_patient_handler)
):
    """
    Completa la storia medica di un paziente esistente.

    - Cerca paziente per email
    - Aggiorna allergie e lifestyle
    - Salva obiettivi e preferenze medico in additionalNotes
    """
    try:
        # 1. Cerca paziente
        patient = patient_handler.search_patient_by_email(request.email)

        if not patient:
            raise HTTPException(
                status_code=404,
                detail=f"Nessun paziente trovato con email: {request.email}"
            )

        # 2. Aggiorna allergie
        patient.set_allergies(request.allergie)

        # 3. Aggiorna lifestyle
        lifestyle_data = {
            'alcoholFrequency': request.lifestyle.frequenza_alcol,
            'hoursOfSleep': request.lifestyle.ore_sonno,
            'physicalActivityFrequency': request.lifestyle.frequenza_attivita_fisica,
            'physicalActivityIntensity': request.lifestyle.intensita_attivita_fisica,
            'smokerFrequency': request.lifestyle.fumatore,
            'typeOfDiet': request.lifestyle.tipo_dieta
        }
        patient.set_lifestyle(lifestyle_data)

        # 4. Formatta obiettivi per additionalNotes
        obiettivi_text = _format_obiettivi_text(
            request.obiettivi,
            request.scelta_medico,
            request.motivo_visita
        )

        # Appendi alle note esistenti
        existing_notes = patient.get_additional_notes() or ""
        patient.set_additional_notes(f"{existing_notes}\n\n{obiettivi_text}")

        # 5. Salva aggiornamenti
        patient_id, _ = patient_handler.save_patient(patient, plain_password=None)

        if not patient_id:
            raise HTTPException(
                status_code=500,
                detail="Errore durante l'aggiornamento del paziente"
            )

        return CompletaStoriaMedicaResponse(
            success=True,
            message="Storia medica completata con successo",
            patient_id=patient_id,
            sommario_generato=False
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Errore in completa_storiamedica: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Errore interno: {str(e)}")


@router.get("/ricevi_sommario/{email}", response_model=RiceviSommarioResponse)
async def ricevi_sommario(
        email: str,
        patient_handler: PatientHandler = Depends(get_patient_handler)
):
    """
    Riceve il sommario completo di un paziente.

    - Cerca paziente per email
    - Genera sommario strutturato dai dati esistenti
    """
    try:
        # 1. Cerca paziente
        patient = patient_handler.search_patient_by_email(email)

        if not patient:
            raise HTTPException(
                status_code=404,
                detail=f"Nessun paziente trovato con email: {email}"
            )

        # 2. Info paziente
        patient_info = PatientSummaryInfo(
            nome=patient.get_name(),
            cognome=patient.get_surname(),
            email=patient.get_email(),
            eta=patient.get_age() or 0,
            sesso=patient.get_sex()
        )

        # 3. Anagrafica
        anagrafica = {
            "nome": patient.get_name(),
            "cognome": patient.get_surname(),
            "email": patient.get_email(),
            "codice_fiscale": patient.get_fiscal_code(),
            "data_nascita": patient.get_birth_date(),
            "eta": patient.get_age(),
            "sesso": patient.get_sex(),
            "altezza": patient.get_height(),
            "peso": patient.get_weight()
        }

        # 4. Lifestyle
        lifestyle = patient.get_lifestyle() or {}

        # 5. Allergie
        allergie = patient.allergies if hasattr(patient, 'allergies') else []

        # 6. Parse obiettivi e preferenze da additionalNotes
        additional_notes = patient.get_additional_notes() or ""

        obiettivi_dict = {
            "testo_completo": additional_notes
        }

        preferenze_medico = {}
        if "PREFERENZE MEDICO" in additional_notes:
            lines = additional_notes.split('\n')
            for line in lines:
                if 'Vicinanza:' in line:
                    preferenze_medico['vicinanza'] = line.split(':')[1].strip()
                elif 'Specializzazione:' in line:
                    preferenze_medico['specializzazione'] = line.split(':')[1].strip()
                elif 'Costo:' in line:
                    preferenze_medico['costo'] = line.split(':')[1].strip()
                elif 'Area di Interesse:' in line:
                    preferenze_medico['area_interesse'] = line.split(':')[1].strip()

        # 7. Sommario completo
        sommario = SommarioCompleto(
            anagrafica=anagrafica,
            lifestyle=lifestyle,
            allergie=allergie,
            obiettivi=obiettivi_dict,
            preferenze_medico=preferenze_medico,
            sintesi_testuale=additional_notes
        )

        return RiceviSommarioResponse(
            success=True,
            patient=patient_info,
            sommario=sommario,
            generated_at=datetime.now().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Errore in ricevi_sommario: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Errore interno: {str(e)}")