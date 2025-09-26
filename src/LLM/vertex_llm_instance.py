import os
import json
from typing import Optional, Tuple
import traceback
import requests
import subprocess
import vertexai
from vertexai.generative_models import GenerativeModel


class VertexLLM:
    """
    Classe LLM che utilizza Google Vertex AI con supporto per Mistral Small
    """

    def __init__(self, project_id: str = None, location: str = None, model_name: str = None):
        """
        Inizializza il client Vertex AI

        Args:
            project_id: ID del progetto Google Cloud
            location: Regione di Vertex AI
            model_name: Nome del modello
        """
        self.project_id = project_id or os.environ.get('GOOGLE_CLOUD_PROJECT', 'longeviva-web-app-dev')
        self.location = location or os.environ.get('VERTEX_AI_LOCATION', 'europe-west4')
        self.model_name = model_name or os.environ.get('VERTEX_AI_MODEL', 'mistral-small-2503')

        # Per Mistral - USA L'SDK, NON REST API
        self.is_mistral = 'mistral' in self.model_name.lower()

        # Per Gemini
        self.model = None
        self.chat_session = None

        # Stati del flusso conversazionale
        self.conversation_state = "init"
        self.current_question = None

        # Inizializza
        if self.is_mistral:
            self._init_mistral()
        else:
            self._init_vertex_ai()

    def _init_mistral(self):
        """Inizializza per Mistral Small usando rawPredict API"""
        try:
            # Test del token di accesso
            import subprocess
            result = subprocess.run(['gcloud', 'auth', 'print-access-token'],
                                    capture_output=True, text=True, check=True)
            token = result.stdout.strip()

            if not token:
                raise Exception("Token di accesso non valido")

            # Non serve inizializzare Vertex AI per rawPredict
            self.model = True  # Flag che indica che è configurato

            print(f"✅ Mistral Small configurato con rawPredict!")
            print(f"📍 Progetto: {self.project_id}")
            print(f"🌍 Regione: {self.location}")
            print(f"🤖 Modello: {self.model_name}")
            return True

        except Exception as e:
            print(f"❌ Errore configurazione Mistral: {e}")
            return False

    def _init_vertex_ai(self):
        """Inizializza per Gemini"""
        try:
            if not self.project_id:
                raise ValueError("GOOGLE_CLOUD_PROJECT non configurato")

            vertexai.init(project=self.project_id, location=self.location)

            self.model = GenerativeModel(
                model_name=self.model_name,
                system_instruction="""Sei Longi di Longeviva, un assistente medico virtuale intelligente e amichevole.
                Aiuti i pazienti con registrazione, raccolta dati medici e raccomandazioni di specialisti.
                Rispondi sempre in italiano, sii professionale ma caloroso."""
            )

            # Test del modello
            test_response = self.model.generate_content("Ciao, come stai?")
            print(f"✅ Gemini configurato con successo!")
            print(f"📍 Progetto: {self.project_id}")
            print(f"🌍 Regione: {self.location}")
            print(f"🤖 Modello: {self.model_name}")
            return True

        except Exception as e:
            print(f"❌ Errore configurazione Gemini: {e}")
            traceback.print_exc()
            return False

    def generate_response(self, prompt: str, system_prompt: str = None) -> Tuple[str, Optional[str]]:
        """
        Genera una risposta usando Mistral Small o Gemini
        """
        if self.is_mistral:
            return self._generate_mistral_response(prompt, system_prompt)
        else:
            return self._generate_gemini_response(prompt, system_prompt)

    def _generate_mistral_response(self, prompt: str, system_prompt: str = None):
        """Genera risposta con Mistral Small usando rawPredict API"""
        print("DEBUG: Inizio _generate_mistral_response")

        try:
            # Ottieni token di accesso
            import subprocess
            result = subprocess.run(['gcloud', 'auth', 'print-access-token'],
                                    capture_output=True, text=True, check=True)
            token = result.stdout.strip()

            # URL rawPredict
            url = f"https://{self.location}-aiplatform.googleapis.com/v1/projects/{self.project_id}/locations/{self.location}/publishers/mistralai/models/mistral-small-2503:rawPredict"

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            # Costruisci messaggi
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            payload = {
                "model": "mistral-small-2503",
                "messages": messages,
                "max_tokens": 1000,
                "temperature": 0.7,
                "stream": False
            }

            print(f"DEBUG: Invio richiesta a rawPredict...")

            import requests
            response = requests.post(url, headers=headers, json=payload, timeout=30)

            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content'], None
            else:
                print(f"DEBUG: Errore rawPredict {response.status_code}: {response.text}")
                return self._fallback_response(), None

        except Exception as e:
            print(f"DEBUG: Errore Mistral rawPredict: {e}")
            traceback.print_exc()
            return self._fallback_response(), None

    def _generate_gemini_response(self, prompt: str, system_prompt: str = None):
        """Genera risposta con Gemini"""
        if not self.model:
            return self._fallback_response(), None

        try:
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"ISTRUZIONI: {system_prompt}\n\nUTENTE: {prompt}"

            response = self.model.generate_content(
                full_prompt,
                generation_config={
                    'temperature': 0.7,
                    'top_p': 0.8,
                    'top_k': 40,
                    'max_output_tokens': 1024,
                }
            )

            response_text = response.text if response.text else "Mi dispiace, non sono riuscito a elaborare la richiesta."
            return response_text, None

        except Exception as e:
            print(f"Errore Gemini: {e}")
            return self._fallback_response(), None

    def start_chat_session(self) -> bool:
        """Avvia una sessione di chat persistente"""
        if self.is_mistral:
            # Mistral non ha sessioni persistenti, ritorna sempre True
            return True

        try:
            if not self.model:
                return False

            self.chat_session = self.model.start_chat()
            print("💬 Sessione chat Gemini avviata")
            return True

        except Exception as e:
            print(f"❌ Errore avvio chat session: {e}")
            return False

    def send_message_in_session(self, message: str) -> str:
        """Invia un messaggio nella sessione di chat esistente"""
        if self.is_mistral:
            # Per Mistral, usa generate_response normale
            response, _ = self.generate_response(message)
            return response

        try:
            if not self.chat_session:
                response, _ = self.generate_response(message)
                return response

            response = self.chat_session.send_message(message)
            return response.text if response.text else "Non ho ricevuto una risposta valida."

        except Exception as e:
            print(f"❌ Errore invio messaggio: {e}")
            return "Mi dispiace, ho avuto un problema tecnico. Riprova."

    def _fallback_response(self) -> str:
        """Risposta di fallback se il modello non funziona"""
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
        """Controlla lo stato del sistema"""
        status = {
            'model_type': 'mistral' if self.is_mistral else 'gemini',
            'model_initialized': bool(self.model),
            'project_id': self.project_id,
            'location': self.location,
            'model_name': self.model_name,
            'chat_session_active': bool(self.chat_session) if not self.is_mistral else True
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
        # Test Mistral
        print("\n1️⃣ Test Mistral Small...")
        mistral_llm = VertexLLM(model_name="mistral-small-2503")
        response, _ = mistral_llm.generate_response("Ciao, mi chiamo Mario e ho 35 anni")
        print(f"✅ Mistral risposta: {response[:100]}...")

        # Test Gemini per confronto
        print("\n2️⃣ Test Gemini per confronto...")
        gemini_llm = VertexLLM(model_name="gemini-1.5-flash")
        response2, _ = gemini_llm.generate_response("Ciao, mi chiamo Mario e ho 35 anni")
        print(f"✅ Gemini risposta: {response2[:100]}...")

        # Status check
        status = mistral_llm.check_vertex_ai_status()
        print(f"📊 Status Mistral: {status}")

        return True

    except Exception as e:
        print(f"❌ Test fallito: {e}")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_vertex_llm()