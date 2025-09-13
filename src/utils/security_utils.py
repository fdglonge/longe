# src/utils/security_utils.py
import hashlib
import secrets
import string
import os
from typing import Tuple


class SecurityUtils:
    """
    Utilità per la gestione della sicurezza del sistema Longeviva
    """

    # Salt fisso per il sistema (in produzione dovrebbe essere in variabile d'ambiente)
    SYSTEM_SALT = os.environ.get('LONGEVIVA_SALT', 'longeviva_2024_secure_salt_default')

    @staticmethod
    def generate_firebase_document_id(fiscal_code: str) -> str:
        """
        Genera l'ID del documento Firebase dal codice fiscale
        Questo diventerà l'ID univoco del paziente su Firebase

        Args:
            fiscal_code: Codice fiscale del paziente

        Returns:
            str: ID del documento Firebase (SHA256 del CF + salt)
        """
        if not fiscal_code:
            raise ValueError("Codice fiscale non può essere vuoto")

        # Normalizza il codice fiscale (maiuscolo, rimuovi spazi)
        normalized_cf = fiscal_code.upper().strip().replace(' ', '')

        # Combina codice fiscale + salt di sistema
        salted_cf = f"{normalized_cf}{SecurityUtils.SYSTEM_SALT}"

        # Hash SHA256 - questo diventa l'ID del documento Firebase
        document_id = hashlib.sha256(salted_cf.encode('utf-8')).hexdigest()

        print(f"🔐 Document ID Firebase generato per CF: {normalized_cf[:6]}***")
        return document_id

    @staticmethod
    def generate_random_password(length: int = 12) -> str:
        """
        Genera una password casuale sicura

        Args:
            length: Lunghezza della password (default 12)

        Returns:
            str: Password casuale leggibile
        """
        # Caratteri per la password (esclude caratteri ambigui come 0, O, l, 1)
        characters = "abcdefghijkmnpqrstuvwxyzABCDEFGHJKMNPQRSTUVWXYZ23456789!@#$%&*"

        # Assicura almeno: 1 maiuscola, 1 minuscola, 1 numero, 1 simbolo
        password_parts = [
            secrets.choice("ABCDEFGHJKMNPQRSTUVWXYZ"),  # Maiuscola
            secrets.choice("abcdefghijkmnpqrstuvwxyz"),  # Minuscola
            secrets.choice("23456789"),  # Numero
            secrets.choice("!@#$%&*")  # Simbolo
        ]

        # Riempie il resto della lunghezza
        for _ in range(length - 4):
            password_parts.append(secrets.choice(characters))

        # Mescola i caratteri
        secrets.SystemRandom().shuffle(password_parts)

        password = ''.join(password_parts)
        print(f"🔑 Password generata: {len(password)} caratteri")
        return password

    @staticmethod
    def hash_password(password: str, salt: str = None) -> Tuple[str, str]:
        """
        Hash di una password con salt individuale

        Args:
            password: Password in chiaro
            salt: Salt personalizzato (se None, ne genera uno nuovo)

        Returns:
            Tuple[str, str]: (password_hashata, salt_usato)
        """
        if salt is None:
            # Genera un salt casuale per questa password
            salt = secrets.token_hex(32)  # 64 caratteri hex

        # Combina password + salt individuale + salt di sistema
        salted_password = f"{password}{salt}{SecurityUtils.SYSTEM_SALT}"

        # Hash SHA256
        password_hash = hashlib.sha256(salted_password.encode('utf-8')).hexdigest()

        print(f"🔐 Password hashata con salt personalizzato")
        return password_hash, salt

    @staticmethod
    def verify_password(password: str, stored_hash: str, salt: str) -> bool:
        """
        Verifica una password contro l'hash memorizzato

        Args:
            password: Password in chiaro da verificare
            stored_hash: Hash memorizzato nel database
            salt: Salt usato per l'hash originale

        Returns:
            bool: True se la password è corretta
        """
        # Ricalcola l'hash con la stessa logica
        computed_hash, _ = SecurityUtils.hash_password(password, salt)

        # Confronta gli hash (constant-time comparison per sicurezza)
        return secrets.compare_digest(computed_hash, stored_hash)

    @staticmethod
    def generate_patient_credentials(fiscal_code: str) -> Tuple[str, str, str, str]:
        """
        Genera tutte le credenziali per un nuovo paziente

        Args:
            fiscal_code: Codice fiscale del paziente

        Returns:
            Tuple[str, str, str, str]: (document_id, password_chiaro, password_hash, salt)
        """
        # Genera ID documento Firebase
        document_id = SecurityUtils.generate_firebase_document_id(fiscal_code)

        # Genera password casuale
        password_plain = SecurityUtils.generate_random_password()

        # Hash della password
        password_hash, salt = SecurityUtils.hash_password(password_plain)

        print(f"🔐 Credenziali complete generate per paziente")
        return document_id, password_plain, password_hash, salt


# Funzione di test
if __name__ == "__main__":
    print("🧪 Test SecurityUtils")

    # Test con codice fiscale di esempio
    test_fiscal_code = "RSSMRA85M01H501X"

    print(f"\n1. Test generazione ID documento:")
    doc_id = SecurityUtils.generate_firebase_document_id(test_fiscal_code)
    print(f"   Document ID: {doc_id}")

    print(f"\n2. Test generazione password:")
    password = SecurityUtils.generate_random_password()
    print(f"   Password: {password}")

    print(f"\n3. Test hash password:")
    password_hash, salt = SecurityUtils.hash_password(password)
    print(f"   Hash: {password_hash[:20]}...")
    print(f"   Salt: {salt[:20]}...")

    print(f"\n4. Test verifica password:")
    # Test corretto
    is_valid = SecurityUtils.verify_password(password, password_hash, salt)
    print(f"   Password corretta: {is_valid}")

    # Test errato
    is_invalid = SecurityUtils.verify_password("password_sbagliata", password_hash, salt)
    print(f"   Password errata: {is_invalid}")

    print(f"\n5. Test credenziali complete:")
    doc_id, pwd_plain, pwd_hash, pwd_salt = SecurityUtils.generate_patient_credentials(test_fiscal_code)
    print(f"   Document ID: {doc_id}")
    print(f"   Password: {pwd_plain}")
    print(f"   Hash: {pwd_hash[:20]}...")
    print(f"   Salt: {pwd_salt[:20]}...")