# src/api/schemas/patient_schemas.py
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional


# ============ INSERISCI ANAGRAFICA ============

class InserisciAnagraficaRequest(BaseModel):
    messaggio: str = Field(..., min_length=10)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "messaggio": "La mia email è mario.rossi@email.com. Sono nato il 28 gennaio 1990 a Roma ma attualmente vivo a Milano. Sono un uomo, sono alto 175 centimetri e peso 70 kg."
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
                "messaggio": "Non ho allergie alimentari o farmacologiche. Non bevo alcol, dormo circa 7-8 ore per notte. Faccio sport 3 volte a settimana, principalmente corsa a intensità moderata. Non sono fumatore. Seguo una dieta mediterranea."
            }
        }
    )


class CompletaStoriaMedicaResponse(BaseModel):
    success: bool
    message: str
    dati_estratti: Dict[str, Any]
    is_complete: bool
    campi_mancanti: List[str]


# ============ GENERA SOMMARIO ============

class OnBoardingData(BaseModel):
    expectations: List[str] = Field(..., description="Aspettative del paziente")
    goals: List[str] = Field(..., description="Obiettivi del paziente")
    reasons: List[str] = Field(..., description="Motivi per cui ha scelto Longeviva")


class GeneraSommarioRequest(BaseModel):
    nome: str = Field(..., min_length=1, description="Nome del paziente")
    onBoardingData: OnBoardingData

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nome": "Mario",
                "onBoardingData": {
                    "expectations": [
                        "Un percorso personalizzato",
                        "Consigli pratici",
                        "Supporto costante"
                    ],
                    "goals": [
                        "Perdere peso",
                        "Avere più energia",
                        "Migliorare la salute generale"
                    ],
                    "reasons": [
                        "Voglio migliorare il mio stile di vita",
                        "Cerco un approccio strutturato",
                        "Mi interessa la longevità"
                    ]
                }
            }
        }
    )


class GeneraSommarioResponse(BaseModel):
    success: bool
    message: str
    onBoardingSummary: str = Field(..., description="Sommario generato dall'AI")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Sommario generato con successo",
                "onBoardingSummary": "Mario ha scelto Longeviva per migliorare il suo stile di vita in modo strutturato, con particolare interesse verso la longevità. I suoi obiettivi principali sono perdere peso, aumentare i livelli di energia e migliorare la salute generale. Si aspetta un percorso personalizzato con consigli pratici e un supporto costante nel suo percorso di benessere."
            }
        }
    )