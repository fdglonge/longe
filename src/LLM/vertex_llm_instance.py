import os
import json
from typing import Optional, Tuple
import traceback
from google.cloud import aiplatform
from google.oauth2 import service_account
import vertexai
from vertexai.generative_models import GenerativeModel, Part
import requests


class VertexLLM:
    """
    Classe LLM che utilizza Google Vertex AI invece di Ollama locale
    """

    def __init__(self, project_id: str = None, location: str = "us-central1", model_name: str = "gemini-1.5-flash"):
        """
        Inizializza il client Vertex AI

        Args:
            project_id: ID del progetto Google Cloud
            location: Regione di Vertex AI
            model_name: Nome del modello (gemini-1.5-flash, gemini-1.5-pro, etc.)
        """
        self.project_id = project_id or os.environ.get('GOOGLE_CLOUD_PROJECT')
        self.location = location
        self.model_name = model_name
        self.model = None
        self.chat_session = None

        # Stati del flusso conversazionale (compatibilità con codice esistente)
        self.conversation_state = "init"
        self.current_question = None

        # Inizializza Vertex AI
        self._init_vertex_ai()

    def _init_vertex_ai(self):
        """Inizializza la connessione con Vertex AI"""
        try:
            if not self.project_id:
                raise ValueError("GOOGLE_CLOUD_PROJECT non configurato nelle variabili d'ambiente")

            # Inizializza Vertex AI
            vertexai.init(project=self.project_id, location=self.location)

            # Crea il modello
            self.model = GenerativeModel(
                model_name=self.model_name,
                system_instruction="""Sei Longi di Longeviva, un assistente medico virtuale intelligente e amichevole.
                Aiuti i pazienti con registrazione, raccolta dati medici e raccomandazioni di specialisti.
                Rispondi sempre in italiano, sii professionale ma caloroso."""
            )

            # Test del modello
            test_response = self.model.generate_content("Ciao, come stai?")
            print(f"✅ Vertex AI configurato con successo!")
            print(f"📍 Progetto: {self.project_id}")
            print(f"🌍 Regione: {self.location}")
            print(f"🤖 Modello: {self.model_name}")

            return True

        except Exception as e:
            print(f"❌ Errore configurazione Vertex AI: {e}")
            print("💡 Verifica:")
            print("  1. GOOGLE_CLOUD_PROJECT nelle variabili d'ambiente")
            print("  2. Credenziali Google Cloud configurate")
            print("  3. Vertex AI API abilitata nel progetto")
            traceback.print_exc()
            return False

    def generate_response(self, prompt: str, system_prompt: str = None) -> Tuple[str, Optional[str]]:
        """
        Genera una risposta usando Vertex AI - compatibile con l'interfaccia esistente

        Args:
            prompt: Messaggio dell'utente
            system_prompt: Istruzioni di sistema (opzionale, già configurato nel modello)

        Returns:
            Tuple[risposta, context] per compatibilità con codice esistente
        """
        if not self.model:
            return self._fallback_response(), None

        try:
            # Se c'è un system_prompt specifico, lo includiamo nel prompt
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"ISTRUZIONI: {system_prompt}\n\nUTENTE: {prompt}"

            # Genera risposta
            response = self.model.generate_content(
                full_prompt,
                generation_config={
                    'temperature': 0.7,
                    'top_p': 0.8,
                    'top_k': 40,
                    'max_output_tokens': 1024,
                }
            )

            # Estrai il testo della risposta
            response_text = response.text if response.text else "Mi dispiace, non sono riuscito a elaborare la richiesta."

            return response_text, None  # Context non necessario con Vertex AI

        except Exception as e:
            print(f"❌ Errore Vertex AI: {e}")
            return self._fallback_response(), None

    def start_chat_session(self) -> bool:
        """
        Avvia una sessione di chat persistente per conversazioni multi-turno
        """
        try:
            if not self.model:
                return False

            self.chat_session = self.model.start_chat()
            print("💬 Sessione chat Vertex AI avviata")
            return True

        except Exception as e:
            print(f"❌ Errore avvio chat session: {e}")
            return False

    def send_message_in_session(self, message: str) -> str:
        """
        Invia un messaggio nella sessione di chat esistente
        """
        try:
            if not self.chat_session:
                # Se non c'è una sessione attiva, usa generate_response normale
                response, _ = self.generate_response(message)
                return response

            response = self.chat_session.send_message(message)
            return response.text if response.text else "Non ho ricevuto una risposta valida."

        except Exception as e:
            print(f"❌ Errore invio messaggio: {e}")
            return "Mi dispiace, ho avuto un problema tecnico. Riprova."

    def _fallback_response(self) -> str:
        """Risposta di fallback se Vertex AI non funziona"""
        fallback_responses = {
            "init": "Benvenuto! Sono Longi di Longeviva. Per iniziare, potresti farmi una panoramica generale su di te?",
            "collect_overview": "Perfetto! Ora vorrei confermare i dati che ho capito dalla tua descrizione.",
            "confirm_data": "I dati sono corretti? Possiamo procedere?",
            "collect_missing_data": "Mi servono ancora alcune informazioni per completare il tuo profilo.",
            "collect_purpose": "Qual è il motivo della tua visita oggi?",
            "recommend_doctor": "Ti consiglio di consultare un medico specializzato per il tuo problema.",
            "schedule_appointment": "Vuoi prenotare un appuntamento?",
            "closing": "Grazie per aver utilizzato i nostri servizi!",
        }

        return fallback_responses.get(self.conversation_state,
                                      "Mi dispiace, sto avendo problemi tecnici. Come posso aiutarti?")

    def check_vertex_ai_status(self) -> dict:
        """
        Controlla lo stato di Vertex AI e le configurazioni
        """
        status = {
            'vertex_ai_initialized': bool(self.model),
            'project_id': self.project_id,
            'location': self.location,
            'model_name': self.model_name,
            'chat_session_active': bool(self.chat_session)
        }

        return status

    # Metodi per compatibilità con LLM esistente
    def start_conversation(self):
        """Compatibilità con l'interfaccia LLM esistente"""
        self.conversation_state = "init"
        self.start_chat_session()
        return True

    def set_conversation_state(self, state: str):
        """Imposta lo stato della conversazione"""
        self.conversation_state = state

    def get_conversation_state(self) -> str:
        """Ottiene lo stato della conversazione"""
        return self.conversation_state


# Factory function per sostituire facilmente LLM
def create_llm_instance(use_vertex=True, **kwargs):
    """
    Factory per creare l'istanza LLM appropriata

    Args:
        use_vertex: Se True usa Vertex AI, altrimenti Ollama
        **kwargs: Parametri specifici per l'LLM
    """
    if use_vertex:
        return VertexLLM(**kwargs)
    else:
        # Fallback a Ollama esistente
        from .llm_instance import LLM
        return LLM(**kwargs)


# Test function
def test_vertex_llm():
    """Test di base per verificare il funzionamento"""
    print("🧪 Test Vertex AI LLM...")

    try:
        # Crea istanza
        llm = VertexLLM()

        # Test semplice
        response, _ = llm.generate_response("Ciao, mi chiamo Mario e ho 35 anni")
        print(f"✅ Test risposta: {response[:100]}...")

        # Test chat session
        if llm.start_chat_session():
            chat_response = llm.send_message_in_session("Come stai oggi?")
            print(f"✅ Test chat session: {chat_response[:100]}...")

        # Status check
        status = llm.check_vertex_ai_status()
        print(f"📊 Status: {status}")

        return True

    except Exception as e:
        print(f"❌ Test fallito: {e}")
        return False


if __name__ == "__main__":
    test_vertex_llm()