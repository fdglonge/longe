# src/api/schemas/doctor_schemas.py
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional


class SceltaMedico(BaseModel):
    vicinanza: int = Field(..., ge=1, le=5, description="Importanza vicinanza (1-5)")
    specializzazione: int = Field(..., ge=1, le=5, description="Importanza specializzazione (1-5)")
    costo: int = Field(..., ge=1, le=5, description="Importanza costo (1-5)")
    area_interesse: int = Field(..., ge=1, le=5, description="Importanza area interesse (1-5)")


class RaccomandaDottoreRequest(BaseModel):
    motivo_visita: str = Field(..., min_length=10, description="Descrizione del problema/sintomo")
    citta: str = Field(..., min_length=2, description="Città del paziente")
    scelta_medico: SceltaMedico

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "motivo_visita": "Ho dolori al ginocchio quando corro, probabilmente legato allo sport",
                "citta": "Milano",
                "scelta_medico": {
                    "vicinanza": 5,
                    "specializzazione": 4,
                    "costo": 3,
                    "area_interesse": 5
                }
            }
        }
    )


class DoctorInfo(BaseModel):
    id: str
    nome: str
    cognome: str
    specializzazione: str
    citta: str
    indirizzo: Optional[str]
    telefono: Optional[str]
    email: Optional[str]
    tariffa_oraria: float
    organizzazione: Optional[str]
    lingue: List[str]
    area_interesse: Optional[str]
    foto_profilo: Optional[str] = None
    match_score: Optional[float] = None


class RaccomandaDottoreResponse(BaseModel):
    success: bool
    message: str
    dottori: List[DoctorInfo]
    total_dottori: int