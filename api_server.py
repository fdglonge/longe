#!/usr/bin/env python3
"""
API Server per Longeviva con Vertex AI
"""

import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

# Setup paths
current_dir = os.path.dirname(__file__)
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.join(current_dir, 'src'))

# Import routes
from src.api import patient_routes, doctor_routes, longi_routes

# FastAPI app
app = FastAPI(
    title="Longi AI APIs",
    description="API intelligenti per Longeviva con Vertex AI",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registra routes
app.include_router(
    patient_routes.router,
    #prefix="/api/v1/pazienti",
    tags=["Pazienti"]
)

app.include_router(
    doctor_routes.router,
    #prefix="/api/v1/dottori",
    tags=["Dottori"]
)

app.include_router(
    longi_routes.router,
    #prefix="/api/v1/longi",
    tags=["Longi AI"]
)


# Health checks
@app.get("/")
async def root():
    return {
        "service": "Longi AI APIs",
        "version": "2.0.0",
        "status": "active",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "vertex_ai_configured": bool(os.environ.get('GOOGLE_CLOUD_PROJECT'))
    }


if __name__ == "__main__":
    import uvicorn

    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8080))

    print(f"\n{'=' * 50}")
    print(f"Longi AI APIs")
    print(f"{'=' * 50}")
    print(f"Host: http://{host}:{port}")
    print(f"Docs: http://{host}:{port}/docs")
    print(f"Health: http://{host}:{port}/health")
    print(f"{'=' * 50}\n")

    uvicorn.run(app, host=host, port=port, reload=False)