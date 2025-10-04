#!/usr/bin/env python3
"""
API Server semplificata per Longeviva con Vertex AI
"""

import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn
from datetime import datetime

# Aggiungi percorsi
current_dir = os.path.dirname(__file__)
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.join(current_dir, 'src'))

# Import semplificati con fallback
try:
    from src.LLM.vertex_llm_instance import VertexLLM
except ImportError:
    try:
        from LLM.vertex_llm_instance import VertexLLM
    except ImportError:
        VertexLLM = None

app = FastAPI(
    title="Longeviva API",
    description="API semplificata per Longeviva",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Modelli
class ChatRequest(BaseModel):
    message: str


class DoctorRecommendRequest(BaseModel):
    problem: str
    city: Optional[str] = None


# Cache globale per LLM
llm_instance = None


def get_llm():
    """Ottieni istanza LLM globale"""
    global llm_instance
    if llm_instance is None:
        if VertexLLM:
            llm_instance = VertexLLM()
        else:
            raise HTTPException(status_code=500, detail="LLM non disponibile")
    return llm_instance


@app.get("/")
async def root():
    return {
        "service": "Longeviva API",
        "status": "active",
        "vertex_ai": bool(os.environ.get('GOOGLE_CLOUD_PROJECT'))
    }


@app.get("/health")
async def health():
    try:
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "vertex_ai": bool(os.environ.get('GOOGLE_CLOUD_PROJECT')),
            "model": os.environ.get('VERTEX_AI_MODEL', 'mistral-small-2503')
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@app.post("/chat")
async def chat(request: ChatRequest):
    """Chat con Mistral Small"""
    try:
        llm = get_llm()
        response, _ = llm.generate_response(request.message)

        return {
            "response": response,
            "timestamp": datetime.now().isoformat(),
            "model": "mistral-small-2503"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/doctors")
async def list_doctors():
    """Lista medici di esempio"""
    doctors = [
        {
            "name": "Dr. Mario Rossi",
            "specialization": "Medicina Generale",
            "city": "Milano",
            "experience": 15
        },
        {
            "name": "Dr. Anna Bianchi",
            "specialization": "Cardiologia",
            "city": "Roma",
            "experience": 12
        },
        {
            "name": "Dr. Giuseppe Verdi",
            "specialization": "Neurologia",
            "city": "Napoli",
            "experience": 20
        }
    ]
    return {"doctors": doctors}


@app.post("/recommend-doctor")
async def recommend_doctor(request: DoctorRecommendRequest):
    """Raccomanda un medico basato sul problema"""
    try:
        # Logica semplificata per raccomandazione
        specializations = {
            "cuore": "Cardiologia",
            "testa": "Neurologia",
            "mal di testa": "Neurologia",
            "pressione": "Cardiologia",
            "dolore": "Medicina Generale"
        }

        problem_lower = request.problem.lower()
        recommended_spec = "Medicina Generale"

        for keyword, spec in specializations.items():
            if keyword in problem_lower:
                recommended_spec = spec
                break

        # Medico raccomandato basato su specializzazione
        if recommended_spec == "Cardiologia":
            doctor = {
                "name": "Dr. Anna Bianchi",
                "specialization": "Cardiologia",
                "city": request.city or "Roma",
                "experience": 12,
                "phone": "06-12345678"
            }
        elif recommended_spec == "Neurologia":
            doctor = {
                "name": "Dr. Giuseppe Verdi",
                "specialization": "Neurologia",
                "city": request.city or "Napoli",
                "experience": 20,
                "phone": "081-87654321"
            }
        else:
            doctor = {
                "name": "Dr. Mario Rossi",
                "specialization": "Medicina Generale",
                "city": request.city or "Milano",
                "experience": 15,
                "phone": "02-11223344"
            }

        return {
            "success": True,
            "problem": request.problem,
            "specialization_detected": recommended_spec,
            "recommended_doctor": doctor
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status")
async def status():
    """Status del sistema"""
    try:
        return {
            "status": "active",
            "vertex_ai_project": os.environ.get('GOOGLE_CLOUD_PROJECT'),
            "vertex_ai_location": os.environ.get('VERTEX_AI_LOCATION'),
            "vertex_ai_model": os.environ.get('VERTEX_AI_MODEL'),
            "llm_available": VertexLLM is not None,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8080))

    print(f"Avvio Longeviva API Server")
    print(f"Host: {host}:{port}")
    print(f"Vertex AI: {os.environ.get('GOOGLE_CLOUD_PROJECT', 'Non configurato')}")

    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=False
    )