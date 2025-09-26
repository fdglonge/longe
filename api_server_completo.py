#!/usr/bin/env python3
"""
API Server per Longeviva che USA IL TUO CODICE COMPLETO
"""

import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uvicorn
from datetime import datetime

# Aggiungi percorsi per importare IL TUO CODICE
current_dir = os.path.dirname(__file__)
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.join(current_dir, 'src'))

# Import del TUO sistema completo
try:
    from src.LLM.llm_assistant import create_llm_assistant_auto, LLMAssistant
    from src.Patient.patient_instance import Patient
    from src.utils.login_in_handler import LoginInHandler
    from src.utils.registration_handler import RegistrationHandler
except ImportError:
    try:
        from LLM.llm_assistant import create_llm_assistant_auto, LLMAssistant
        from Patient.patient_instance import Patient
        from utils.login_in_handler import LoginInHandler
        from utils.registration_handler import RegistrationHandler
    except ImportError as e:
        print(f"Errore import: {e}")
        sys.exit(1)

app = FastAPI(
    title="Longeviva API - Sistema Completo",
    description="API che usa il sistema Longeviva completo con Mistral Small",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Modelli per API
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class RegistrationStartRequest(BaseModel):
    start_registration: bool = True


class RegistrationAnswerRequest(BaseModel):
    answer: str
    session_id: str


class DoctorRecommendRequest(BaseModel):
    problem: str
    city: Optional[str] = None
    patient_data: Optional[Dict[str, Any]] = None


# Storage sessioni
sessions = {}


@app.get("/")
async def root():
    return {
        "service": "Longeviva API - Sistema Completo",
        "status": "active",
        "features": [
            "Chat con Mistral Small",
            "Registrazione paziente completa",
            "Login con Firebase",
            "Raccomandazioni medico intelligenti",
            "Database medici reale"
        ]
    }


@app.get("/health")
async def health():
    try:
        # Testa il TUO sistema
        assistant = create_llm_assistant_auto()
        status = assistant.get_system_status()

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "llm_backend": status.get("llm_backend"),
            "vertex_ai_available": status.get("vertex_ai_available"),
            "total_doctors": status.get("total_doctors"),
            "database_status": status.get("database_initialized")
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@app.post("/auth/login")
async def login(request: LoginRequest):
    """Login usando IL TUO LoginInHandler"""
    try:
        login_handler = LoginInHandler(request.email, request.password)
        patient_data = login_handler.get_data()

        if not patient_data:
            raise HTTPException(status_code=401, detail="Credenziali non valide")

        # Crea sessione
        session_id = f"login_{datetime.now().timestamp()}"
        assistant = create_llm_assistant_auto()
        success = assistant.set_patient_from_data(patient_data)

        if success:
            sessions[session_id] = {
                "assistant": assistant,
                "authenticated": True,
                "patient_data": patient_data,
                "created_at": datetime.now()
            }

            return {
                "success": True,
                "session_id": session_id,
                "patient": {
                    "name": assistant.patient.get_full_name(),
                    "email": assistant.patient.get_email(),
                    "city": assistant.patient.get_city()
                }
            }
        else:
            raise HTTPException(status_code=500, detail="Errore caricamento dati paziente")

    except Exception as e:
        if "Account non trovato" in str(e) or "Password errata" in str(e):
            raise HTTPException(status_code=401, detail=str(e))
        else:
            raise HTTPException(status_code=500, detail=str(e))


@app.post("/registration/start")
async def start_registration(request: RegistrationStartRequest):
    """Avvia registrazione usando IL TUO RegistrationHandler"""
    try:
        session_id = f"reg_{datetime.now().timestamp()}"
        assistant = create_llm_assistant_auto()

        # Crea il TUO registration handler
        registration_handler = RegistrationHandler(assistant.patient, assistant.patient_db)
        welcome_msg, first_question = registration_handler.start_registration()

        sessions[session_id] = {
            "assistant": assistant,
            "registration_handler": registration_handler,
            "authenticated": False,
            "created_at": datetime.now()
        }

        return {
            "session_id": session_id,
            "welcome_message": welcome_msg,
            "first_question": first_question
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/registration/answer")
async def registration_answer(request: RegistrationAnswerRequest):
    """Continua registrazione usando IL TUO sistema"""
    try:
        if request.session_id not in sessions:
            raise HTTPException(status_code=404, detail="Sessione non trovata")

        session = sessions[request.session_id]
        registration_handler = session["registration_handler"]

        success, response, next_question = registration_handler.process_answer(request.answer)

        if success:
            # Registrazione completata
            session["authenticated"] = True
            email, password, doc_id = registration_handler.get_generated_credentials()

            return {
                "registration_complete": True,
                "message": response,
                "credentials": {
                    "email": email,
                    "password": password,
                    "doc_id": doc_id
                }
            }
        else:
            return {
                "registration_complete": False,
                "response": response,
                "next_question": next_question
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat")
async def chat(request: ChatRequest):
    """Chat usando IL TUO LLMAssistant completo"""
    try:
        if request.session_id and request.session_id in sessions:
            # Usa sessione esistente
            assistant = sessions[request.session_id]["assistant"]
        else:
            # Crea nuovo assistente
            session_id = f"chat_{datetime.now().timestamp()}"
            assistant = create_llm_assistant_auto()
            sessions[session_id] = {
                "assistant": assistant,
                "authenticated": False,
                "created_at": datetime.now()
            }
            request.session_id = session_id

        # Usa il TUO sistema di classificazione input
        input_type = assistant.classify_user_input(request.message)

        if input_type == 'data_query' and assistant.patient:
            # Gestisci domande sui dati usando IL TUO codice
            assistant.handle_data_query(request.message)
            response = "Query sui dati processata"
        else:
            # Chat normale
            response = assistant.get_llm_response(request.message)

        return {
            "response": response,
            "session_id": request.session_id,
            "input_classified_as": input_type,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/recommend-doctor")
async def recommend_doctor(request: DoctorRecommendRequest):
    """Raccomandazione medico usando IL TUO sistema intelligente"""
    try:
        assistant = create_llm_assistant_auto()

        # Crea paziente temporaneo o usa dati forniti
        if request.patient_data:
            patient = Patient(data=request.patient_data)
        else:
            patient = Patient()

        patient.set_purpose(request.problem)
        if request.city:
            patient.set_city(request.city)

        assistant.patient = patient

        # USA IL TUO sistema di raccomandazione
        assistant.recommend_doctor()

        if assistant.recommended_doctor:
            doctor = assistant.recommended_doctor
            return {
                "success": True,
                "problem": request.problem,
                "recommended_doctor": {
                    "name": doctor.get_full_name(),
                    "specialization": doctor.get_specialization(),
                    "city": getattr(doctor, 'city_of_work', doctor.get_city()),
                    "experience_years": doctor.get_years_of_experience(),
                    "phone": doctor.get_phone(),
                    "email": doctor.get_email(),
                    "address": doctor.get_address()
                }
            }
        else:
            return {
                "success": False,
                "message": "Nessun medico trovato per questo problema"
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/food-diary")
async def food_diary_chat(request: ChatRequest):
    """Diario alimentare usando IL TUO sistema"""
    try:
        if request.session_id and request.session_id in sessions:
            assistant = sessions[request.session_id]["assistant"]
        else:
            session_id = f"food_{datetime.now().timestamp()}"
            assistant = create_llm_assistant_auto()
            sessions[session_id] = {
                "assistant": assistant,
                "authenticated": False,
                "created_at": datetime.now()
            }
            request.session_id = session_id

        # Usa IL TUO sistema diario alimentare
        assistant.conversation_state = "food_diary_mode"

        # Usa IL TUO metodo per diario alimentare
        response = assistant.handle_food_diary_input(request.message)

        return {
            "response": response,
            "session_id": request.session_id,
            "mode": "food_diary",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/system/status")
async def system_status():
    """Status usando IL TUO sistema"""
    try:
        assistant = create_llm_assistant_auto()
        status = assistant.get_system_status()

        return {
            "status": "active",
            "llm_backend": status.get("llm_backend"),
            "vertex_ai_available": status.get("vertex_ai_available"),
            "database_initialized": status.get("database_initialized"),
            "total_doctors": status.get("total_doctors"),
            "google_cloud_project": status.get("google_cloud_project"),
            "active_sessions": len(sessions),
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

    print(f"Avvio Longeviva API Server con SISTEMA COMPLETO")
    print(f"Host: {host}:{port}")

    uvicorn.run(
        "api_server:app",
        host=host,
        port=port,
        reload=False
    )