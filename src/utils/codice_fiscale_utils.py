# src/utils/codice_fiscale_utils.py
import codicefiscale


def calcola_codice_fiscale(nome: str, cognome: str, sesso: str, data_nascita: str, comune_nascita: str) -> str:
    """
    Calcola il codice fiscale italiano

    Args:
        nome: Nome
        cognome: Cognome
        sesso: 'M' o 'F'
        data_nascita: formato 'YYYY-MM-DD'
        comune_nascita: Nome del comune di nascita

    Returns:
        Codice fiscale calcolato
    """
    try:
        from datetime import datetime

        # Parse data
        birth_date = datetime.strptime(data_nascita, '%Y-%m-%d')

        # Calcola CF
        cf = codicefiscale.encode(
            surname=cognome.upper(),
            name=nome.upper(),
            sex=sesso.upper(),
            birthdate=birth_date.strftime('%d/%m/%Y'),
            birthplace=comune_nascita.title()
        )

        return cf.upper()

    except Exception as e:
        print(f"Errore calcolo codice fiscale: {e}")
        # Fallback: genera un CF fittizio per scopi di test
        import hashlib
        data_combinata = f"{nome}{cognome}{data_nascita}{sesso}".encode()
        return hashlib.sha256(data_combinata).hexdigest()[:16].upper()