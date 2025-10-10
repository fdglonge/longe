# src/api/schemas/patient_schemas.py
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional


# ============ INSERISCI ANAGRAFICA ============

class InserisciAnagraficaRequest(BaseModel):
    messaggio: str = Field(..., min_length=10)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "messaggio": "Mi chiamo Mario Rossi, la mia email è mario.rossi@email.com. Sono nato il 28 gennaio 1990 a Roma ma attualmente vivo a Milano. Sono un uomo, sono alto 175 centimetri e peso 70 kg."
            }
        }
    )


class InserisciAnagraficaResponse(BaseModel):
    success: bool
    message: str
    dati_estratti: Dict[str, Any]
    is_complete: bool
    campi_mancanti: List[str]


# ============ COMPLETA STORIA MEDICA ============

class CompletaStoriaMedicaRequest(BaseModel):
    messaggio: str = Field(..., min_length=10)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "messaggio": "Non ho allergie alimentari o farmacologiche. Non bevo alcol, dormo circa 7-8 ore per notte. Faccio sport 3 volte a settimana, principalmente corsa a intensità moderata. Non sono fumatore. Seguo una dieta mediterranea con molta frutta e verdura. Ho scaricato Longeviva perché voglio migliorare il mio stile di vita in modo strutturato. Il mio obiettivo principale è perdere peso e avere più energia durante la giornata. Mi aspetto un percorso personalizzato con consigli pratici. Per la scelta del medico, la vicinanza è molto importante per me, così come la specializzazione. Il costo non è un problema prioritario."
            }
        }
    )


class CompletaStoriaMedicaResponse(BaseModel):
    success: bool
    message: str
    dati_estratti: Dict[str, Any]
    is_complete: bool
    campi_mancanti: List[str]


# ============ RICEVI SOMMARIO ============

class PatientSummaryInfo(BaseModel):
    nome: str
    cognome: str
    email: str
    eta: int
    sesso: str


class SommarioCompleto(BaseModel):
    anagrafica: dict
    lifestyle: dict
    allergie: List[str]
    obiettivi: dict
    preferenze_medico: dict
    sintesi_testuale: Optional[str] = None


class RiceviSommarioResponse(BaseModel):
    success: bool
    patient: PatientSummaryInfo
    sommario: SommarioCompleto
    generated_at: str