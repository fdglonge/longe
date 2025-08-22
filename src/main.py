#!/usr/bin/env python3

import os
import sys

# Aggiungi percorsi
sys.path.append(os.path.dirname(__file__))


def show_welcome_menu():
    """Mostra il menu di benvenuto"""
    print("🏥 Benvenuto a Longeviva, io sono Longi!")
    print("=" * 50)
    print("Scegli un'opzione:")
    print("0️⃣  - Nuova registrazione")
    print("1️⃣  - Accesso (Login)")
    print("2️⃣  - Esci")
    print("=" * 50)


def show_post_login_menu():
    """Mostra il menu post-login con le nuove opzioni"""
    print("\n🎯 Cosa vorresti fare oggi?")
    print("=" * 50)
    print("1️⃣  - Recupera i tuoi dati personali")
    print("2️⃣  - Avvia chat con Longi per diario alimentare")
    print("3️⃣  - Esci")
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
            choice = input("Inserisci la tua scelta (1/2/3): ").strip()
            if choice in ['1', '2', '3']:
                return int(choice)
            else:
                print("❌ Scelta non valida. Inserisci 1, 2 o 3.")
        except KeyboardInterrupt:
            print("\n👋 Arrivederci!")
            return 3
        except Exception:
            print("❌ Input non valido. Riprova.")


def handle_registration():
    """Gestisce il processo di registrazione"""
    print("\n🆕 Avvio processo di registrazione...")

    try:
        from LLM.llm_assistant import LLMAssistant
        print("✅ Assistente caricato")

        # Inizializza
        print("⚡ Inizializzazione...")
        assistant = LLMAssistant()

        # Controlla ricerca semantica
        try:
            from utils.semantic_search import enhance_doctor_recommendation
            if enhance_doctor_recommendation(assistant):
                print("🧠 Ricerca semantica attivata")
            else:
                print("⚠️ Ricerca semantica fallita - uso metodo tradizionale")
        except ImportError:
            print("⚠️ Ricerca semantica non disponibile - uso metodo tradizionale")

        print("🚀 Sistema pronto per la registrazione!\n")

        # Avvia conversazione di registrazione
        assistant.start_conversation()

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
    """Gestisce il processo di login"""
    print("\n🔐 Processo di accesso...")

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

    try:
        # Importa e usa LoginInHandler
        from utils.login_in_handler import LoginInHandler

        print("🔍 Verifica credenziali...")
        login_handler = LoginInHandler(email)

        # Se arriviamo qui, il login è andato a buon fine
        print("✅ Login effettuato con successo!")

        # Avvia la sessione post-login
        start_post_login_session(login_handler)

    except ImportError as e:
        print(f"❌ Errore caricamento LoginInHandler: {e}")
        return False
    except Exception as e:
        print(f"❌ Errore durante il login: {e}")
        import traceback
        traceback.print_exc()
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
    return assistant.start_food_diary_mode()


def start_post_login_session(login_handler):
    """Avvia la sessione dopo il login completato - VERSIONE AGGIORNATA"""
    print("\n🎯 Sessione avviata!")
    print("I tuoi dati sono già disponibili nel sistema.\n")

    try:
        # Carica l'assistente LLM
        from LLM.llm_assistant import LLMAssistant

        # Inizializza l'assistente
        assistant = LLMAssistant()

        # Passa i dati del paziente all'assistente
        patient_data = login_handler.get_data()
        if patient_data:
            assistant.set_patient_from_data(patient_data)
            print("📋 Dati del tuo profilo caricati correttamente.")

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

        # Menu post-login
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
                # Chat diario alimentare
                result = handle_food_diary_chat(assistant)
                if result == 'exit':
                    break
                input("\nPremi INVIO per continuare...")

            elif choice == 3:
                # Esci
                print("\n👋 Grazie per aver usato Longeviva!")
                print("Ci vediamo presto per continuare il tuo percorso di benessere!")
                break

    except ImportError as e:
        print(f"❌ Errore caricamento assistente: {e}")
    except Exception as e:
        print(f"❌ Errore nella sessione: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Funzione principale"""
    try:
        while True:
            show_welcome_menu()
            choice = get_user_choice()

            if choice == 0:
                # Registrazione
                success = handle_registration()
                if success:
                    print("\n✅ Registrazione completata!")
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

    except KeyboardInterrupt:
        print("\n👋 Sistema chiuso dall'utente")
    except Exception as e:
        print(f"❌ Errore generale: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()