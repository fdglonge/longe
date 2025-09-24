#!/usr/bin/env python3

import os
import sys
from Patient.diet_management import handle_diet_chat_option

# Aggiungi percorsi
sys.path.append(os.path.dirname(__file__))


def show_welcome_menu():
    """Mostra il menu di benvenuto"""
    print("🏥 Benvenuto a Longeviva, io sono Longi!")
    print("=" * 50)
    print("Scegli un'opzione:")
    print("0️⃣  - Nuova registrazione")
    print("1️⃣  - Accesso con email e password")
    print("2️⃣  - Esci")
    print("=" * 50)


def show_post_login_menu():
    """Mostra il menu post-login/post-registrazione"""
    print("\n🎯 Cosa vorresti fare oggi?")
    print("=" * 50)
    print("1️⃣  - Recupera i tuoi dati personali")
    print("2️⃣  - Avvia chat con Longi per diario alimentare")
    print("3️⃣  - Prenota un meeting con uno specialista")
    print("4️⃣  - Esci")
    print("=" * 50)


def get_user_choice():
    """Ottiene la scelta dell'utente"""
    while True:
        try:
            choice = input("Inserisci la tua scelta (0/1/2): ").strip()
            if choice in ['0', '1', '2']:
                return int(choice)
            else:
                print("❌ Scelta non valida. Inserisci 0, 1 o 2.")
        except KeyboardInterrupt:
            print("\n👋 Arrivederci!")
            sys.exit(0)
        except Exception:
            print("❌ Input non valido. Riprova.")


def get_post_login_choice():
    """Ottiene la scelta dell'utente nel menu post-login"""
    while True:
        try:
            choice = input("Inserisci la tua scelta (1/2/3/4): ").strip()
            if choice in ['1', '2', '3', '4']:
                return int(choice)
            else:
                print("❌ Scelta non valida. Inserisci 1, 2, 3 o 4.")
        except KeyboardInterrupt:
            print("\n👋 Arrivederci!")
            return 4
        except Exception:
            print("❌ Input non valido. Riprova.")


def show_registration_completion(registration_handler):
    """
    Mostra il completamento della registrazione con le credenziali generate
    """
    if not registration_handler:
        return

    email, password, doc_id = registration_handler.get_generated_credentials()

    if email and password:
        print("\n" + "=" * 60)
        print("🎉 REGISTRAZIONE COMPLETATA CON SUCCESSO!")
        print("=" * 60)
        print(f"📧 Email: {email}")
        print(f"🔑 Password: {password}")
        print("=" * 60)
        print("⚠️  IMPORTANTE: Salva queste credenziali!")
        print("    Ti serviranno per accedere al sistema.")
        print("=" * 60)

        # Chiedi se vuole salvare le credenziali
        try:
            save_choice = input("\nVuoi che ti mostri di nuovo le credenziali? (s/n): ").strip().lower()
            if save_choice == 's':
                print(f"\n📋 Email: {email}")
                print(f"📋 Password: {password}")
                print("\n💡 Suggerimento: Screenshot o appunta queste credenziali!")

        except KeyboardInterrupt:
            pass


def handle_registration():
    """Gestisce il processo di registrazione"""
    print("\n🆕 Avvio processo di registrazione...")

    try:
        # MODIFICA: Usa la factory function per LLM automatico
        from LLM.llm_assistant import create_llm_assistant_auto
        print("⚡ Inizializzazione assistente intelligente...")

        # Crea assistente con auto-detect del backend migliore
        assistant = create_llm_assistant_auto()

        # Mostra info sul sistema
        status = assistant.get_system_status()
        print(f"✅ Sistema attivo: {status['llm_backend']}")

        if status['llm_backend'] == 'Vertex AI':
            print("🌐 Connesso a Google Cloud Vertex AI")
            if status.get('vertex_ai_status', {}).get('project_id'):
                print(f"📍 Progetto: {status['vertex_ai_status']['project_id']}")
        else:
            print("🏠 Modalità locale con Ollama")

        # Test connessione
        if not assistant.test_llm_connection():
            print("⚠️ Problema connessione LLM - continuo comunque...")

        # Controlla ricerca semantica (codice esistente)
        try:
            from utils.semantic_search import enhance_doctor_recommendation
            if enhance_doctor_recommendation(assistant):
                print("🧠 Ricerca semantica attivata")
            else:
                print("⚠️ Ricerca semantica fallita - uso metodo tradizionale")
        except ImportError:
            print("⚠️ Ricerca semantica non disponibile - uso metodo tradizionale")

        print("🚀 Sistema pronto per la registrazione!\n")

        # Avvia conversazione di registrazione (codice esistente)
        success = assistant.start_conversation()

        if success and hasattr(assistant, 'registration_handler'):
            # Mostra le credenziali generate
            show_registration_completion(assistant.registration_handler)

            # ✅ MODIFICA PRINCIPALE: Rimuovi la raccomandazione automatica del medico
            # Dopo registrazione, vai direttamente al menu post-login
            print("\n🎉 Registrazione completata! Benvenuto in Longeviva!")
            print("Ora puoi utilizzare tutte le funzionalità del sistema.")

            # Avvia direttamente la sessione utente con il menu
            start_user_session(assistant)

    except ImportError as e:
        print(f"❌ Errore caricamento moduli: {e}")
        print("💡 Assicurati che tutti i moduli siano presenti")
        return False
    except Exception as e:
        print(f"❌ Errore durante la registrazione: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


def handle_login():
    """Gestisce il processo di login con email e password"""
    print("\n🔐 Processo di accesso...")

    # Raccolta email
    while True:
        try:
            email = input("📧 Inserisci la tua email: ").strip()

            if not email:
                print("❌ Email non può essere vuota. Riprova.")
                continue

            # Validazione email base
            if '@' not in email or '.' not in email:
                print("❌ Formato email non valido. Riprova.")
                continue

            break

        except KeyboardInterrupt:
            print("\n👋 Operazione annullata.")
            return False
        except Exception:
            print("❌ Errore nell'inserimento. Riprova.")

    # Raccolta password
    while True:
        try:
            # Prova a usare getpass per nascondere la password
            try:
                import getpass
                password = getpass.getpass("🔑 Inserisci la tua password: ")
            except ImportError:
                # Fallback se getpass non è disponibile
                password = input("🔑 Inserisci la tua password: ")

            if not password:
                print("❌ Password non può essere vuota. Riprova.")
                continue

            break

        except KeyboardInterrupt:
            print("\n👋 Operazione annullata.")
            return False
        except Exception:
            print("❌ Errore nell'inserimento. Riprova.")

    try:
        # Importa e usa LoginInHandler con email e password
        from utils.login_in_handler import LoginInHandler

        print("🔍 Verifica credenziali...")
        login_handler = LoginInHandler(email, password)

        # Se arriviamo qui, il login è andato a buon fine
        print("✅ Login effettuato con successo!")

        # auto-detect assistente
        from LLM.llm_assistant import create_llm_assistant_auto
        assistant = create_llm_assistant_auto()

        # Mostra backend utilizzato
        status = assistant.get_system_status()
        print(f"✅ Login completato! Sistema: {status['llm_backend']}")

        # Passa i dati del paziente all'assistente
        patient_data = login_handler.get_data()
        if patient_data:
            success = assistant.set_patient_from_data(patient_data)
            if success:
                print("📋 Dati del tuo profilo caricati correttamente.")
            else:
                print("⚠️ Errore nel caricamento del profilo, procedo comunque.")

        # Controlla ricerca semantica
        try:
            from utils.semantic_search import enhance_doctor_recommendation
            if enhance_doctor_recommendation(assistant):
                print("🧠 Ricerca semantica attivata")
        except ImportError:
            print("⚠️ Ricerca semantica non disponibile")

        print("🚀 Sistema pronto!\n")

        # Mostra benvenuto personalizzato
        name = assistant.patient.get_name() if assistant.patient else "utente"
        print(f"🎉 Bentornato, {name}!")

        # Avvia sessione utente
        start_user_session(assistant)

    except ImportError as e:
        print(f"❌ Errore caricamento LoginInHandler: {e}")
        return False
    except Exception as e:
        error_message = str(e)

        # Gestisci errori specifici con messaggi user-friendly
        if "Account non trovato" in error_message:
            print("❌ Account non trovato per questa email.")
            print("💡 Suggerimento: Verifica l'email o procedi con la registrazione.")
        elif "Password errata" in error_message:
            print("❌ Password errata.")
            print("💡 Suggerimento: Controlla di aver inserito la password corretta.")
        elif "Account senza dati di autenticazione" in error_message:
            print("❌ Account creato prima dell'implementazione del sistema di sicurezza.")
            print("💡 Contatta il supporto per aggiornare il tuo account.")
        else:
            print(f"❌ Errore durante il login: {error_message}")

        return False

    return True


def handle_data_retrieval(assistant):
    """Gestisce il recupero dati personali"""
    print("\n📋 RECUPERO DATI PERSONALI")
    print("=" * 50)

    if not assistant.patient:
        print("❌ Nessun dato paziente disponibile")
        return

    # Mostra il profilo completo
    assistant._answer_full_profile()

    # Loop per domande sui dati
    print("\nPuoi farmi domande specifiche sui tuoi dati (es. 'quanto peso?', 'che età ho?')")
    print("Scrivi 'menu' per tornare al menu principale o 'esci' per uscire.")

    while True:
        try:
            user_input = input("\nTu: ").strip()

            if user_input.lower() in ['menu', 'torna', 'indietro']:
                break
            elif user_input.lower() in ['esci', 'exit', 'quit']:
                return 'exit'

            # Classifica l'input
            input_type = assistant.classify_user_input(user_input)

            if input_type == 'data_query':
                assistant.handle_data_query(user_input)
            else:
                print("Ti posso aiutare solo con domande sui tuoi dati personali.")
                print("Esempi: 'quanto peso?', 'che età ho?', 'quali sono le mie allergie?'")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Errore: {e}")


def handle_food_diary_chat(assistant):
    """Gestisce la chat con Longi per il diario alimentare"""
    print("\n🍽️ DIARIO ALIMENTARE CON LONGI")
    print("=" * 50)
    print("Ciao! Sono Longi, il tuo nutrizionista virtuale!")
    print("Ti aiuterò a creare e gestire il tuo diario alimentare.")
    print("Puoi raccontarmi cosa hai mangiato, chiedere consigli nutrizionali,")
    print("o semplicemente chattare su alimentazione e benessere.")
    print("\nScrivi 'menu' per tornare al menu principale o 'esci' per uscire.")

    # Avvia la modalità diario alimentare
    try:
        return assistant.start_food_diary_mode()
    except Exception as e:
        print(f"❌ Errore nell'avvio del diario alimentare: {e}")
        print("Torno al menu principale...")
        return None


def handle_specialist_booking(assistant):
    """Gestisce la prenotazione di un meeting con uno specialista"""
    print("\n👨‍⚕️ PRENOTAZIONE MEETING CON SPECIALISTA")
    print("=" * 50)

    if not assistant.patient:
        print("❌ Nessun dato paziente disponibile")
        return

    name = assistant.patient.get_name()
    print(f"Ciao {name}! Ti aiuterò a prenotare un meeting con lo specialista più adatto.")
    print("\nPer trovare il medico perfetto per te, dimmi:")
    print("Qual è il motivo per cui desideri consultare uno specialista?")
    print("Descrivi pure il problema, i sintomi o la visita che ti serve.")
    print("\nScrivi 'menu' per tornare al menu principale.")

    while True:
        try:
            user_input = input("\nTu: ").strip()

            if user_input.lower() in ['menu', 'torna', 'indietro']:
                break
            elif user_input.lower() in ['esci', 'exit', 'quit']:
                return 'exit'
            elif not user_input:
                print("Per favore, descrivi il motivo della visita.")
                continue

            # Salva il motivo della visita
            assistant.patient.set_purpose(user_input)

            print(f"\nPerfetto! Ho registrato la tua richiesta: '{user_input}'")
            print("🔍 Sto analizzando il tuo caso per trovare lo specialista più adatto...")
            print("📍 Considerando la tua posizione e le tue esigenze...")

            # Usa il sistema di raccomandazione esistente dell'assistente
            assistant.recommend_doctor()

            if assistant.recommended_doctor:
                print("\n📅 Vuoi procedere con la prenotazione di un appuntamento?")

                booking_choice = input("Rispondi 'sì' per prenotare o 'no' per tornare al menu: ").strip().lower()

                if booking_choice in ['sì', 'si', 'yes', 'ok', 'prenota']:
                    # Avvia il processo di booking usando il sistema esistente
                    print("\n🗓️ PRENOTAZIONE APPUNTAMENTO")
                    print("=" * 40)

                    # Simula la disponibilità e propone slot
                    doctor = assistant.recommended_doctor
                    print(f"📋 Medico: Dr. {doctor.get_full_name()}")
                    print(f"🏥 Specializzazione: {doctor.get_specialization()}")

                    # Propone slot disponibili (per ora simulati)
                    print("\n📅 Slot disponibili:")
                    print("1. Lunedì 15 gennaio, ore 10:00")
                    print("2. Mercoledì 17 gennaio, ore 15:30")
                    print("3. Venerdì 19 gennaio, ore 09:15")

                    slot_choice = input("\nScegli uno slot (1/2/3) o 'annulla': ").strip()

                    if slot_choice in ['1', '2', '3']:
                        slots = [
                            "Lunedì 15 gennaio, ore 10:00",
                            "Mercoledì 17 gennaio, ore 15:30",
                            "Venerdì 19 gennaio, ore 09:15"
                        ]
                        selected_slot = slots[int(slot_choice) - 1]

                        # Simula prenotazione completata
                        booking_id = f"BOOK-{hash(f'{name}{selected_slot}') % 100000:05d}"

                        print(f"\n✅ PRENOTAZIONE CONFERMATA!")
                        print("=" * 40)
                        print(f"📋 Paziente: {name}")
                        print(f"👨‍⚕️ Medico: Dr. {doctor.get_full_name()}")
                        print(f"📅 Data e ora: {selected_slot}")
                        print(f"🆔 Codice prenotazione: {booking_id}")
                        print(f"📍 Indirizzo: {doctor.get_address()}")
                        print(f"📞 Telefono: {doctor.get_phone_number() or '06-12345678'}")
                        print("\n📧 Riceverai una conferma via email.")
                        print("📱 Ti invieremo un promemoria 24h prima dell'appuntamento.")

                        break
                    elif slot_choice.lower() == 'annulla':
                        print("Prenotazione annullata.")
                        break
                    else:
                        print("Scelta non valida.")
                else:
                    print("Prenotazione annullata. Puoi sempre tornare quando vuoi!")
                    break
            else:
                print("❌ Non sono riuscito a trovare uno specialista adatto.")
                print("Riprova con una descrizione diversa del problema.")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Errore: {e}")


def show_system_configuration_menu():
    """Mostra menu di configurazione del sistema"""
    print("\n⚙️ CONFIGURAZIONE SISTEMA LONGEVIVA")
    print("=" * 50)
    print("1️⃣  - Mostra status sistema")
    print("2️⃣  - Test connessione LLM")
    print("3️⃣  - Cambia backend LLM")
    print("4️⃣  - Configurazione Vertex AI")
    print("0️⃣  - Torna al menu principale")
    print("=" * 50)


def handle_system_configuration():
    """Gestisce la configurazione del sistema"""
    try:
        from LLM.llm_assistant import create_llm_assistant_auto
        assistant = create_llm_assistant_auto()

        while True:
            show_system_configuration_menu()
            choice = input("Inserisci la tua scelta (0/1/2/3/4): ").strip()

            if choice == "0":
                break
            elif choice == "1":
                # Mostra status
                status = assistant.get_system_status()
                print("\n📊 STATUS SISTEMA:")
                print("=" * 30)
                print(f"🤖 Backend LLM: {status['llm_backend']}")
                print(f"☁️ Vertex AI disponibile: {'Sì' if status['vertex_ai_available'] else 'No'}")
                if status.get('google_cloud_project'):
                    print(f"📍 Progetto GCloud: {status['google_cloud_project']}")
                print(f"🗃️ Database pazienti: {'✅' if status['database_initialized']['patients'] else '❌'}")
                print(f"👨‍⚕️ Database medici: {'✅' if status['database_initialized']['doctors'] else '❌'}")
                print(f"📋 Medici caricati: {status['total_doctors']}")

            elif choice == "2":
                # Test connessione
                print("\n🧪 Test connessione LLM...")
                if assistant.test_llm_connection():
                    print("✅ Connessione LLM funzionante!")
                else:
                    print("❌ Problema connessione LLM")

            elif choice == "3":
                # Cambia backend
                current_backend = "Vertex AI" if assistant.using_vertex_ai else "Ollama"
                print(f"\n🔄 Backend attuale: {current_backend}")
                print("Vuoi cambiare a:")
                print("1. Vertex AI (Google Cloud)")
                print("2. Ollama (Locale)")

                backend_choice = input("Scelta (1/2): ").strip()
                if backend_choice == "1":
                    if assistant.switch_llm_backend(True):
                        print("✅ Passaggio a Vertex AI completato!")
                    else:
                        print("❌ Errore passaggio a Vertex AI")
                elif backend_choice == "2":
                    if assistant.switch_llm_backend(False):
                        print("✅ Passaggio a Ollama completato!")
                    else:
                        print("❌ Errore passaggio a Ollama")

            elif choice == "4":
                # Configurazione Vertex AI
                print("\n☁️ CONFIGURAZIONE VERTEX AI")
                print("=" * 30)
                print("Per usare Vertex AI serve:")
                print("1. Progetto Google Cloud attivo")
                print("2. Vertex AI API abilitata")
                print("3. Credenziali configurate")
                print("4. Variabile GOOGLE_CLOUD_PROJECT")
                print()

                current_project = os.environ.get('GOOGLE_CLOUD_PROJECT')
                if current_project:
                    print(f"📍 Progetto attuale: {current_project}")
                else:
                    print("❌ GOOGLE_CLOUD_PROJECT non configurata")
                    new_project = input("Inserisci ID progetto Google Cloud (o invio per saltare): ").strip()
                    if new_project:
                        os.environ['GOOGLE_CLOUD_PROJECT'] = new_project
                        print(f"✅ GOOGLE_CLOUD_PROJECT impostata: {new_project}")
                        print("⚠️ Riavvia l'applicazione per applicare le modifiche")

            input("\nPremi INVIO per continuare...")

    except Exception as e:
        print(f"❌ Errore configurazione sistema: {e}")

def start_user_session(assistant):
    """Avvia la sessione utente unificata per login e registrazione"""

    # Menu principale unificato
    while True:
        show_post_login_menu()
        choice = get_post_login_choice()

        if choice == 1:
            # Recupera dati personali
            result = handle_data_retrieval(assistant)
            if result == 'exit':
                break
            input("\nPremi INVIO per continuare...")

        elif choice == 2:
            # Chat dieta personalizzata
            result = handle_diet_chat_option(assistant)
            if result == 'exit':
                break
            elif result == 'book_appointment':
                # Reindirizza alla prenotazione appuntamento
                result = handle_specialist_booking(assistant)
                if result == 'exit':
                    break
            input("\nPremi INVIO per continuare...")

        elif choice == 3:
            # Prenota meeting con specialista
            result = handle_specialist_booking(assistant)
            if result == 'exit':
                break
            input("\nPremi INVIO per continuare...")

        elif choice == 4:
            # Esci
            print("\n👋 Grazie per aver usato Longeviva!")
            print("Ci vediamo presto per continuare il tuo percorso di benessere!")
            break


def main():
    """Funzione principale"""
    try:
        while True:
            show_welcome_menu()
            print("3️⃣  - Configurazione sistema")
            choice = get_user_choice()

            if choice == 0:
                # Registrazione
                success = handle_registration()
                if success:
                    print("\n✅ Sessione completata!")
                    break
                else:
                    print("\n❌ Registrazione fallita. Riprova.")
                    input("\nPremi INVIO per continuare...")

            elif choice == 1:
                # Login
                success = handle_login()
                if success:
                    print("\n✅ Sessione completata!")
                    break
                else:
                    print("\n❌ Login fallito. Riprova.")
                    input("\nPremi INVIO per continuare...")

            elif choice == 2:
                # Esci
                print("\n👋 Grazie per aver scelto Longeviva!")
                break

            elif choice == 3:
                # NUOVO: Configurazione sistema
                handle_system_configuration()

    except KeyboardInterrupt:
        print("\n👋 Sistema chiuso dall'utente")
    except Exception as e:
        print(f"❌ Errore generale: {e}")
        import traceback
        traceback.print_exc()

def get_user_choice_extended():
    """Ottiene la scelta dell'utente (versione estesa)"""
    while True:
        try:
            choice = input("Inserisci la tua scelta (0/1/2/3): ").strip()
            if choice in ['0', '1', '2', '3']:
                return int(choice)
            else:
                print("❌ Scelta non valida. Inserisci 0, 1, 2 o 3.")
        except KeyboardInterrupt:
            print("\n👋 Arrivederci!")
            sys.exit(0)
        except Exception:
            print("❌ Input non valido. Riprova.")


if __name__ == "__main__":
    main()