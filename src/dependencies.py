# src/api/dependencies.py
from firebase_admin import firestore
from src.Patient.patients_handler import PatientHandler
from src.LLM.vertex_llm_instance import VertexLLM
from typing import Optional

# Singleton instances
_patient_handler: Optional[PatientHandler] = None
_vertex_llm: Optional[VertexLLM] = None


def get_patient_handler() -> PatientHandler:
    """Ottiene l'istanza singleton di PatientHandler"""
    global _patient_handler
    if _patient_handler is None:
        _patient_handler = PatientHandler()
    return _patient_handler


def get_vertex_llm() -> VertexLLM:
    """Ottiene l'istanza singleton di VertexLLM"""
    global _vertex_llm
    if _vertex_llm is None:
        _vertex_llm = VertexLLM()
    return _vertex_llm


def get_db():
    """Ottiene il client Firestore"""
    handler = get_patient_handler()
    return handler.db if handler.initialized else None