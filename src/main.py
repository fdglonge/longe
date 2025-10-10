# src/api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

# CRITICAL: Aggiungi la cartella src al Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Ora gli import relativi funzionano
from api import patient_routes, doctor_routes

# Inizializza FastAPI
app = FastAPI(
    title="Longeviva API",
    description="API conversazionale per gestione pazienti e raccomandazione dottori con AI",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc"  # ReDoc UI alternativa
)

# CORS - permetti richieste da frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In produzione: ["https://tuodominio.com"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Includi routes
app.include_router(
    patient_routes.router,
    prefix="/api/patients",
    tags=["Patients 👤"]
)

app.include_router(
    doctor_routes.router,
    prefix="/api/doctors",
    tags=["Doctors 🩺"]
)

# Root endpoint
@app.get("/", tags=["System"])
async def root():
    return {
        "status": "🟢 online",
        "service": "Longeviva API",
        "version": "1.0.0",
        "endpoints": {
            "patients_anagrafica": "POST /api/patients/inserisci_anagrafica",
            "patients_storia": "POST /api/patients/completa_storiamedica",
            "patients_sommario": "GET /api/patients/ricevi_sommario/{email}",
            "doctors_raccomanda": "POST /api/doctors/raccomanda_dottore",
            "doctors_lista": "GET /api/doctors/lista_tutti_dottori",
            "docs": "/docs (Swagger UI)",
            "redoc": "/redoc (ReDoc UI)"
        }
    }

@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "firebase": "connected",
        "semantic_search": "active"
    }

# Per avvio locale
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # Auto-reload durante sviluppo
    )