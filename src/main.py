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
    print("1️⃣  - Accesso con email e password")
    print("2️⃣  - Esci")
    print("=" * 50)


def show_post_login_menu():
    """Mostra il menu post-login"""
    print("\n🎯 Cosa vorresti fare oggi?")
    print("=" * 50)
    print("1️⃣  - Recupera i tuoi dati personali")
    print("2️⃣  - Avvia chat con Longi per diario alimentare")
    print("3️⃣  - Cambia password")
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
        success = assistant.start_conversation()

        if success and hasattr(assistant, 'registration_handler'):
            # Mostra le credenziali generate
            show_registration_completion(assistant.registration_handler)

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

        # Avvia la sessione post-login
        start_post_login_session(login_handler)

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


def handle_password_change(login_handler):
    """
    Gestisce il cambio password
    """
    print("\n🔑 CAMBIO PASSWORD")
    print("=" * 50)

    try:
        # Chiedi la nuova password
        try:
            import getpass
            new_password = getpass.getpass("🔑 Inserisci la nuova password: ")
            confirm_password = getpass.getpass("🔑 Conferma la nuova password: ")
        except ImportError:
            new_password = input("🔑 Inserisci la nuova password: ")
            confirm_password = input("🔑 Conferma la nuova password: ")

        if not new_password:
            print("❌ La password non può essere vuota.")
            return

        if new_password != confirm_password:
            print("❌ Le password non coincidono.")
            return

        if len(new_password) < 8:
            print("❌ La password deve essere lunga almeno 8 caratteri.")
            return

        # Cambia la password
        if login_handler.change_password(new_password):
            print("✅ Password cambiata con successo!")
        else:
            print("❌ Errore nel cambio password.")

    except KeyboardInterrupt:
        print("\n👋 Operazione annullata.")
    except Exception as e:
        print(f"❌ Errore: {e}")


def start_post_login_session(login_handler):
    """Avvia la sessione dopo il login completato"""
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
                # Cambio password
                handle_password_change(login_handler)
                input("\nPremi INVIO per continuare...")

            elif choice == 4:
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