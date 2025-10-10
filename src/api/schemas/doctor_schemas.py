# src/api/schemas/doctor_schemas.py
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional


class RaccomandaDottoreRequest(BaseModel):
    messaggio: str = Field(..., min_length=10)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "messaggio": "Ho dolori al ginocchio quando corro"
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