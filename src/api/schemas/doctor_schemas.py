# src/api/schemas/doctor_schemas.py
from pydantic import BaseModel, ConfigDict
from typing import List, Optional


class DoctorInfo(BaseModel):
    """Informazioni dottore per response"""
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
    criteri_ricerca: Optional[dict] = None
    total_dottori: int

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Trovati 5 dottori raccomandati per te",
                "dottori": [
                    {
                        "id": "abc123",
                        "nome": "Mario",
                        "cognome": "Rossi",
                        "specializzazione": "Cardiologia",
                        "citta": "Milano",
                        "indirizzo": "Via Roma 123, Milano",
                        "telefono": "02-12345678",
                        "email": "mario.rossi@clinic.it",
                        "tariffa_oraria": 80.0,
                        "organizzazione": "Ospedale San Raffaele",
                        "lingue": ["Italiano", "Inglese"],
                        "area_interesse": "Cardiologia sportiva",
                        "foto_profilo": "https://...",
                        "match_score": 85.5
                    }
                ],
                "criteri_ricerca": {
                    "vicinanza": 5,
                    "specializzazione": 4,
                    "costo": 3,
                    "area_interesse": 4
                },
                "total_dottori": 10
            }
        }
    )