# src/api/schemas/longi_schemas.py
from pydantic import BaseModel, ConfigDict
from typing import Optional


class GeneraListaSpesaResponse(BaseModel):
    success: bool
    message: str
    id_dieta: str
    lista_spesa: str
    generated_at: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Lista della spesa generata con successo",
                "id_dieta": "NrQQ7PJNHLyaoX1q71dI",
                "lista_spesa": "=== COLAZIONI ===\n- Yogurt greco 0%...",
                "generated_at": "2025-01-04T10:30:00"
            }
        }
    )