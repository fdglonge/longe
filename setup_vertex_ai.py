#!/usr/bin/env python3
"""
Script di setup per configurare Vertex AI per Longeviva
"""

import os
import sys
import json
import subprocess
from pathlib import Path


def print_step(step_num, description):
    """Print formatted step"""
    print(f"\n{'=' * 10} STEP {step_num}: {description} {'=' * 10}")


def check_gcloud_installed():
    """Verifica se Google Cloud CLI è installato"""
    try:
        result = subprocess.run(['gcloud', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Google Cloud CLI è installato")
            return True
        else:
            print("❌ Google Cloud CLI non trovato")
            return False
    except FileNotFoundError:
        print("❌ Google Cloud CLI non installato")
        return False


def install_dependencies():
    """Installa le dipendenze necessarie"""
    print("📦 Installazione dipendenze...")

    try:
        subprocess.run([
            sys.executable, '-m', 'pip', 'install',
            'google-cloud-aiplatform', 'vertexai', 'google-auth'
        ], check=True)
        print("✅ Dipendenze installate con successo")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Errore installazione dipendenze: {e}")
        return False


def setup_google_cloud_project():
    """Configura il progetto Google Cloud"""
    print("\n🌐 CONFIGURAZIONE PROGETTO GOOGLE CLOUD")

    # Chiedi il project ID
    project_id = input("Inserisci il tuo Google Cloud Project ID: ").strip()
    if not project_id:
        print("❌ Project ID richiesto")
        return None

    # Imposta nelle variabili d'ambiente
    os.environ['GOOGLE_CLOUD_PROJECT'] = project_id

    # Verifica se gcloud è configurato
    try:
        result = subprocess.run(['gcloud', 'config', 'get-value', 'project'],
                                capture_output=True, text=True)
        current_project = result.stdout.strip()

        if current_project != project_id:
            print(f"🔄 Imposto progetto corrente: {project_id}")
            subprocess.run(['gcloud', 'config', 'set', 'project', project_id], check=True)
            print("✅ Progetto impostato")
        else:
            print(f"✅ Progetto già configurato: {project_id}")

    except subprocess.CalledProcessError:
        print("⚠️ Errore configurazione gcloud - continuo comunque")

    return project_id


def enable_apis(project_id):
    """Abilita le API necessarie"""
    print("\n🔌 ABILITAZIONE API")

    apis = [
        'aiplatform.googleapis.com',
        'ml.googleapis.com',
        'compute.googleapis.com'
    ]

    for api in apis:
        print(f"🔄 Abilitazione {api}...")
        try:
            subprocess.run([
                'gcloud', 'services', 'enable', api,
                '--project', project_id
            ], check=True, capture_output=True)
            print(f"✅ {api} abilitata")
        except subprocess.CalledProcessError as e:
            print(f"⚠️ Errore abilitazione {api}: {e}")


def setup_authentication():
    """Configura l'autenticazione"""
    print("\n🔐 CONFIGURAZIONE AUTENTICAZIONE")

    print("Scegli il metodo di autenticazione:")
    print("1. Application Default Credentials (consigliato per sviluppo)")
    print("2. Service Account Key File")

    choice = input("Scelta (1/2): ").strip()

    if choice == "1":
        print("🔄 Setup Application Default Credentials...")
        try:
            subprocess.run(['gcloud', 'auth', 'application-default', 'login'], check=True)
            print("✅ Application Default Credentials configurate")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Errore configurazione ADC: {e}")
            return False

    elif choice == "2":
        key_path = input("Inserisci il path del file JSON della service account: ").strip()
        if os.path.exists(key_path):
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = key_path
            print(f"✅ Service Account configurata: {key_path}")
            return True
        else:
            print("❌ File non trovato")
            return False
    else:
        print("❌ Scelta non valida")
        return False


def create_env_file(project_id):
    """Crea file .env con le configurazioni"""
    env_content = f"""# Configurazione Longeviva Vertex AI
GOOGLE_CLOUD_PROJECT={project_id}

# Opzionale: Se usi Service Account Key
# GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json

# Configurazione Vertex AI
VERTEX_AI_LOCATION=us-central1
VERTEX_AI_MODEL=gemini-1.5-flash

# Configurazione esistente Firebase
# Mantieni le tue configurazioni Firebase esistenti
"""

    env_path = Path('.env')

    if env_path.exists():
        print("⚠️ File .env già esistente")
        overwrite = input("Vuoi sovrascrivere? (s/N): ").strip().lower()
        if overwrite != 's':
            print("📝 Configurazioni manuali necessarie:")
            print(f"   Aggiungi: GOOGLE_CLOUD_PROJECT={project_id}")
            return

    try:
        with open(env_path, 'w') as f:
            f.write(env_content)
        print(f"✅ File .env creato con configurazioni")
        print(f"📍 Percorso: {env_path.absolute()}")
    except Exception as e:
        print(f"❌ Errore creazione .env: {e}")


def test_vertex_ai_connection():
    """Test la connessione Vertex AI"""
    print("\n🧪 TEST CONNESSIONE VERTEX AI")

    try:
        # Prova a importare e testare
        from LLM.vertex_llm_instance import test_vertex_llm

        if test_vertex_llm():
            print("🎉 Vertex AI configurato correttamente!")
            return True
        else:
            print("❌ Test Vertex AI fallito")
            return False

    except ImportError as e:
        print(f"❌ Errore import modulo Vertex AI: {e}")
        print("💡 Assicurati che il file vertex_llm_instance.py sia nella cartella LLM/")
        return False
    except Exception as e:
        print(f"❌ Errore test: {e}")
        return False


def show_next_steps():
    """Mostra i prossimi passi"""
    print("\n🎯 PROSSIMI PASSI:")
    print("=" * 50)
    print("1. 🔄 Riavvia l'applicazione Longeviva")
    print("2. 🚀 Nel menu principale, scegli 'Configurazione sistema'")
    print("3. 📊 Verifica lo status del sistema")
    print("4. 🧪 Esegui un test della connessione LLM")
    print("5. ✨ Goditi Longeviva con Vertex AI!")
    print()
    print("📚 Documentazione aggiuntiva:")
    print("   - Google Cloud Console: https://console.cloud.google.com")
    print("   - Vertex AI: https://cloud.google.com/vertex-ai")
    print("=" * 50)


def main():
    """Funzione principale dello setup"""
    print("🏥 SETUP LONGEVIVA - VERTEX AI")
    print("=" * 50)
    print("Questo script configurerà Vertex AI per il tuo sistema Longeviva")

    # Step 1: Check prerequisiti
    print_step(1, "VERIFICA PREREQUISITI")

    if not check_gcloud_installed():
        print("💡 Installa Google Cloud CLI da: https://cloud.google.com/sdk/docs/install")
        print("Poi riavvia questo script")
        return False

    # Step 2: Installa dipendenze
    print_step(2, "INSTALLAZIONE DIPENDENZE")
    if not install_dependencies():
        return False

    # Step 3: Setup progetto
    print_step(3, "CONFIGURAZIONE PROGETTO")
    project_id = setup_google_cloud_project()
    if not project_id:
        return False

    # Step 4: Abilita API
    print_step(4, "ABILITAZIONE API")
    enable_apis(project_id)

    # Step 5: Setup autenticazione
    print_step(5, "AUTENTICAZIONE")
    if not setup_authentication():
        print("⚠️ Autenticazione fallita - potresti doverla configurare manualmente")

    # Step 6: Crea .env
    print_step(6, "CONFIGURAZIONE AMBIENTE")
    create_env_file(project_id)

    # Step 7: Test
    print_step(7, "TEST CONFIGURAZIONE")
    test_vertex_ai_connection()

    # Step 8: Next steps
    show_next_steps()

    print("\n🎉 Setup completato!")
    return True


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Setup annullato dall'utente")
    except Exception as e:
        print(f"\n❌ Errore durante setup: {e}")
        import traceback

        traceback.print_exc()