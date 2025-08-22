# LLM/__init__.py
"""
Inizializzatore per le estensioni LLMAssistant
"""


def initialize_llm_extensions():
    """Inizializza tutte le estensioni per LLMAssistant"""
    try:
        # Importa e applica l'estensione del diario alimentare
        from LLM.llm_assistant_food_diary import extend_llm_assistant_with_food_diary
        from LLM.llm_assistant import LLMAssistant

        # Estendi la classe
        extend_llm_assistant_with_food_diary(LLMAssistant)

        print("🍽️ Estensione diario alimentare caricata")
        return True

    except ImportError as e:
        print(f"⚠️ Estensione diario alimentare non disponibile: {e}")
        return False
    except Exception as e:
        print(f"❌ Errore nel caricamento estensioni: {e}")
        return False


# Applica automaticamente le estensioni quando il modulo viene importato
if __name__ != "__main__":
    initialize_llm_extensions()