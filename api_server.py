#!/usr/bin/env python3
"""
FastAPI Server per Longeviva con Vertex AI
Permette chiamate HTTPS per integrazioni esterne
"""

import os
import sys
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uvicorn
from datetime import datetime
import logging

# Aggiungi il percorso del progetto
current_dir = os.path.dirname(__file__)
sys.path.insert(0, current_dir)

# Import moduli Longeviva
try:
    from LLM.llm_assistant import create_llm_assistant_auto, LLMAssistant
    from Patient.patient_instance import Patient
    from utils.login_in_handler import LoginInHandler
except ImportError as e:
    print(f"❌ Errore import moduli Longeviva: {e}")
    sys.exit(1)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inizializza FastAPI
app = FastAPI(
    title="Longeviva API",
    description="API REST per il sistema medico Longeviva con Vertex AI",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In produzione, specifica domini specifici
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Modelli Pydantic per API
class ChatRequest(BaseModel):
    message: str
    patient_id: Optional[str] = None
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    timestamp: datetime
    llm_backend: str


class RegistrationRequest(BaseModel):
    name: str
    surname: str
    age: Optional[int] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class SystemStatusResponse(BaseModel):
    status: str
    llm_backend: str
    vertex_ai_available: bool
    database_status: Dict[str, bool]
    total_doctors: int
    timestamp: datetime


# Storage sessions globali (in produzione usare Redis/Database)
sessions = {}
assistants_cache = {}


def get_or_create_assistant(session_id: str) -> LLMAssistant:
    """Ottieni o crea un assistente per la sessione"""
    if session_id not in assistants_cache:
        assistants_cache[session_id] = create_llm_assistant_auto()
        logger.info(f"Nuovo assistente creato per sessione {session_id}")

    return assistants_cache[session_id]


# ==================== ENDPOINTS API ====================

@app.get("/")
async def root():
    """Homepage API"""
    return {
        "service": "Longeviva API",
        "version": "2.0.0",
        "status": "active",
        "vertex_ai": os.environ.get('GOOGLE_CLOUD_PROJECT') is not None
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test creazione assistente
        test_assistant = create_llm_assistant_auto()
        status = test_assistant.get_system_status()

        return {
            "status": "healthy",
            "timestamp": datetime.now(),
            "llm_backend": status["llm_backend"],
            "database": status["database_initialized"]
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")


@app.get("/system/status", response_model=SystemStatusResponse)
async def get_system_status():
    """Ottieni lo status completo del sistema"""
    try:
        assistant = create_llm_assistant_auto()
        status = assistant.get_system_status()

        return SystemStatusResponse(
            status="active",
            llm_backend=status["llm_backend"],
            vertex_ai_available=status["vertex_ai_available"],
            database_status=status["database_initialized"],
            total_doctors=status["total_doctors"],
            timestamp=datetime.now()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Endpoint principale per chat con Longi
    """
    try:
        # Genera session_id se non fornito
        session_id = request.session_id or f"session_{datetime.now().timestamp()}"

        # Ottieni assistente per la sessione
        assistant = get_or_create_assistant(session_id)

        # Se c'è un patient_id, carica i dati del paziente
        if request.patient_id:
            # Qui dovresti implementare il caricamento del paziente dal DB
            # patient_data = load_patient_data(request.patient_id)
            # assistant.set_patient_from_data(patient_data)
            pass

        # Genera risposta
        response_text = assistant.get_llm_response(request.message)

        # Salva nella sessione
        if session_id not in sessions:
            sessions[session_id] = []

        sessions[session_id].append({
            "timestamp": datetime.now(),
            "user_message": request.message,
            "assistant_response": response_text
        })

        return ChatResponse(
            response=response_text,
            session_id=session_id,
            timestamp=datetime.now(),
            llm_backend=assistant.get_system_status()["llm_backend"]
        )

    except Exception as e:
        logger.error(f"Errore chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/auth/login")
async def login_endpoint(request: LoginRequest):
    """
    Endpoint di login
    """
    try:
        # Usa il LoginInHandler esistente
        login_handler = LoginInHandler(request.email, request.password)
        patient_data = login_handler.get_data()

        if not patient_data:
            raise HTTPException(status_code=401, detail="Credenziali non valide")

        # Genera session token (in produzione usa JWT)
        session_token = f"token_{datetime.now().timestamp()}"

        return {
            "success": True,
            "session_token": session_token,
            "patient": {
                "name": patient_data.get("name", ""),
                "surname": patient_data.get("surname", ""),
                "email": patient_data.get("email", "")
            }
        }

    except Exception as e:
        if "Account non trovato" in str(e) or "Password errata" in str(e):
            raise HTTPException(status_code=401, detail=str(e))
        else:
            logger.error(f"Errore login: {e}")
            raise HTTPException(status_code=500, detail="Errore interno del server")


@app.post("/patients/register")
async def register_patient(request: RegistrationRequest):
    """
    Endpoint di registrazione paziente
    """
    try:
        # Crea assistente per gestire registrazione
        assistant = create_llm_assistant_auto()

        # Crea paziente con i dati forniti
        patient = Patient()
        patient.set_name(request.name)
        patient.set_surname(request.surname)

        if request.age:
            patient.set_age(request.age)
        if request.email:
            patient.set_contact_info(email=request.email)
        if request.phone:
            patient.set_contact_info(phone=request.phone)
        if request.city:
            patient.set_city(request.city)

        # Qui dovresti salvare nel database
        # patient_id = save_patient_to_database(patient)

        return {
            "success": True,
            "message": "Registrazione completata",
            "patient_id": f"temp_{datetime.now().timestamp()}"  # Temporaneo
        }

    except Exception as e:
        logger.error(f"Errore registrazione: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/doctors/recommend")
async def recommend_doctor(problem: str, city: Optional[str] = None):
    """
    Endpoint per raccomandazione medico
    """
    try:
        assistant = create_llm_assistant_auto()

        # Crea paziente temporaneo per la raccomandazione
        temp_patient = Patient()
        temp_patient.set_purpose(problem)
        if city:
            temp_patient.set_city(city)

        assistant.patient = temp_patient

        # Ottieni raccomandazione
        from LLM.llm_assistant import get_best_doctor_for_purpose
        best_doctor, specialization = get_best_doctor_for_purpose(
            assistant.available_doctors, problem, city
        )

        if best_doctor:
            return {
                "success": True,
                "doctor": {
                    "name": best_doctor.get_full_name(),
                    "specialization": best_doctor.get_specialization(),
                    "city": getattr(best_doctor, 'city_of_work', best_doctor.get_city()),
                    "experience_years": best_doctor.get_years_of_experience(),
                    "phone": best_doctor.get_phone(),
                    "email": best_doctor.get_email()
                },
                "specialization_detected": specialization
            }
        else:
            return {
                "success": False,
                "message": "Nessun medico trovato per questo problema"
            }

    except Exception as e:
        logger.error(f"Errore raccomandazione medico: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/food-diary/chat")
async def food_diary_chat(request: ChatRequest):
    """
    Endpoint specifico per diario alimentare
    """
    try:
        session_id = request.session_id or f"food_diary_{datetime.now().timestamp()}"
        assistant = get_or_create_assistant(session_id)

        # Imposta modalità diario alimentare
        assistant.conversation_state = "food_diary_mode"

        # Crea prompt specifico per diario alimentare
        system_prompt = """Sei Longi, nutrizionista virtuale di Longeviva. 
        Aiuta l'utente con il diario alimentare, dai consigli nutrizionali pratici 
        e mantieni un tono amichevole e motivante."""

        response_text = assistant.get_llm_response(request.message, system_prompt)

        return ChatResponse(
            response=response_text,
            session_id=session_id,
            timestamp=datetime.now(),
            llm_backend=assistant.get_system_status()["llm_backend"]
        )

    except Exception as e:
        logger.error(f"Errore food diary chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== BACKGROUND TASKS ====================

@app.post("/system/clear-sessions")
async def clear_old_sessions(background_tasks: BackgroundTasks):
    """
    Pulisci sessioni vecchie (da chiamare periodicamente)
    """

    def cleanup():
        # Implementa logica di pulizia sessioni vecchie
        cutoff_time = datetime.now().timestamp() - 3600  # 1 ora

        sessions_to_remove = []
        for session_id in sessions:
            if any(msg["timestamp"].timestamp() < cutoff_time for msg in sessions[session_id]):
                sessions_to_remove.append(session_id)

        for session_id in sessions_to_remove:
            del sessions[session_id]
            if session_id in assistants_cache:
                del assistants_cache[session_id]

        logger.info(f"Pulite {len(sessions_to_remove)} sessioni vecchie")

    background_tasks.add_task(cleanup)
    return {"message": "Pulizia sessioni avviata in background"}


# ==================== MAIN ====================

def create_app():
    """Factory per creare l'app"""
    return app


if __name__ == "__main__":
    # Configurazione server
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8000))
    debug = os.environ.get("DEBUG", "false").lower() == "true"

    print(f"🚀 Avvio Longeviva API Server")
    print(f"📍 Host: {host}:{port}")
    print(f"🌐 Vertex AI: {'✅' if os.environ.get('GOOGLE_CLOUD_PROJECT') else '❌'}")
    print(f"📚 Docs: http://{host}:{port}/docs")

    # Avvia server
    uvicorn.run(
        "api_server:app",
        host=host,
        port=port,
        reload=debug,
        access_log=True
    )