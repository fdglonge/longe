#!/usr/bin/env python3

import os
import sys

# Aggiungi percorsi
sys.path.append(os.path.dirname(__file__))


def main():
    """Avvia Longeviva - VERSIONE CORRETTA"""
    print("🏥 Longeviva - Avvio sistema...")

    try:
        # Carica LLMAssistant
        print("📦 Caricamento assistente...")
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

        print("🚀 Sistema pronto!\n")

        # Avvia conversazione (ora inizia direttamente con registrazione)
        assistant.start_conversation()

    except ImportError as e:
        print(f"❌ Errore caricamento moduli: {e}")
        print("💡 Assicurati che tutti i moduli siano presenti")
    except KeyboardInterrupt:
        print("\n👋 Sistema chiuso dall'utente")
    except Exception as e:
        print(f"❌ Errore: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()