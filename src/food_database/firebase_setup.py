#!/usr/bin/env python3
"""
Longeviva Firebase Setup - Alternative Methods
Setup Firebase senza service account key quando non disponibile
"""

import subprocess
import sys
import os
import json


class SimpleFirebaseSetup:
    """Setup Firebase usando metodi alternativi"""

    def __init__(self, project_id: str = "longeviva-web-app-dev"):
        self.project_id = project_id

    def check_gcloud_installed(self) -> bool:
        """Verifica se gcloud CLI è installato"""
        try:
            result = subprocess.run(['gcloud', '--version'],
                                    capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Google Cloud CLI già installato")
                return True
            else:
                print("❌ Google Cloud CLI non trovato")
                return False
        except FileNotFoundError:
            print("❌ Google Cloud CLI non installato")
            return False

    def install_gcloud_instructions(self):
        """Istruzioni per installare gcloud CLI"""
        print("\n🔧 INSTALLA GOOGLE CLOUD CLI:")
        print("=" * 40)

        # Detect OS
        import platform
        os_name = platform.system().lower()

        if os_name == "linux":
            print("# Linux/Ubuntu:")
            print("curl https://sdk.cloud.google.com | bash")
            print("exec -l $SHELL")

        elif os_name == "darwin":
            print("# macOS:")
            print("curl https://sdk.cloud.google.com | bash")
            print("# Oppure con Homebrew:")
            print("brew install --cask google-cloud-sdk")

        elif os_name == "windows":
            print("# Windows:")
            print("# Scarica da: https://cloud.google.com/sdk/docs/install")
            print("# Oppure con Chocolatey:")
            print("choco install gcloudsdk")

        print("\n🔗 Link diretto: https://cloud.google.com/sdk/docs/install")

    def setup_gcloud_auth(self) -> bool:
        """Setup autenticazione gcloud"""
        try:
            print("\n🔐 SETUP AUTENTICAZIONE GCLOUD:")
            print("=" * 40)

            # Check if already authenticated
            result = subprocess.run(['gcloud', 'auth', 'list', '--filter=status:ACTIVE'],
                                    capture_output=True, text=True)

            if "ACTIVE" in result.stdout:
                print("✅ Già autenticato con gcloud")
            else:
                print("🔄 Esecuzione autenticazione...")

                # Login interattivo
                subprocess.run(['gcloud', 'auth', 'login'], check=True)

                # Setup application default credentials
                subprocess.run(['gcloud', 'auth', 'application-default', 'login'], check=True)

                print("✅ Autenticazione completata")

            # Set project
            print(f"🎯 Impostazione progetto: {self.project_id}")
            subprocess.run(['gcloud', 'config', 'set', 'project', self.project_id], check=True)

            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Errore durante setup gcloud: {e}")
            return False
        except Exception as e:
            print(f"❌ Errore inatteso: {e}")
            return False

    def test_firebase_access(self) -> bool:
        """Test accesso Firebase con credenziali correnti"""
        try:
            print("\n🧪 TEST ACCESSO FIREBASE:")
            print("=" * 30)

            # Test using Python
            import firebase_admin
            from firebase_admin import firestore

            # Try to initialize with default credentials
            if not firebase_admin._apps:
                firebase_admin.initialize_app(options={'projectId': self.project_id})

            # Use the default database
            db = firestore.client()

            # Test basic operation
            test_doc = db.collection('_test').document('connectivity_test')
            test_doc.set({
                'test': True,
                'timestamp': firestore.SERVER_TIMESTAMP
            })

            # Cleanup
            test_doc.delete()

            print("✅ Accesso Firebase verificato (default database)")
            return True

        except Exception as e:
            print(f"❌ Test accesso Firebase fallito: {e}")
            print("\nPossibili soluzioni:")
            print("1. Verifica permessi progetto Firebase")
            print("2. Assicurati di essere Owner/Editor del progetto")
            print("3. Controlla che Firestore sia abilitato")
            return False

    def check_permissions(self):
        """Verifica permessi progetto"""
        try:
            print("\n👤 VERIFICA PERMESSI:")
            print("=" * 25)

            # Get current account
            result = subprocess.run(['gcloud', 'auth', 'list', '--filter=status:ACTIVE', '--format=value(account)'],
                                    capture_output=True, text=True)

            if result.returncode == 0 and result.stdout.strip():
                email = result.stdout.strip()
                print(f"📧 Account attivo: {email}")

                # Check project permissions
                iam_result = subprocess.run(['gcloud', 'projects', 'get-iam-policy', self.project_id,
                                             '--flatten=bindings[].members',
                                             '--format=csv(bindings.members,bindings.role)'],
                                            capture_output=True, text=True)

                if email in iam_result.stdout:
                    print("✅ Permessi progetto confermati")

                    # Show roles
                    lines = iam_result.stdout.split('\n')
                    user_roles = [line for line in lines if email in line]
                    print("📋 Ruoli utente:")
                    for role_line in user_roles:
                        if ',' in role_line:
                            role = role_line.split(',')[1]
                            print(f"   - {role}")
                else:
                    print("⚠️  Verificare permessi progetto manualmente")

            return True

        except Exception as e:
            print(f"⚠️  Impossibile verificare permessi: {e}")
            return False


def main():
    """Main setup senza service account"""
    setup = SimpleFirebaseSetup()

    print("🚀 LONGEVIVA FIREBASE - SETUP ALTERNATIVO")
    print("=" * 45)
    print("Setup Firebase senza service account key")

    # Step 1: Check gcloud
    if not setup.check_gcloud_installed():
        setup.install_gcloud_instructions()
        print("\n❗ Installa gcloud CLI e ri-esegui questo script")
        return False

    # Step 2: Setup authentication
    if not setup.setup_gcloud_auth():
        print("❌ Setup autenticazione fallito")
        return False

    # Step 3: Check permissions
    setup.check_permissions()

    # Step 4: Test Firebase access
    if not setup.test_firebase_access():
        print("\n🔧 TROUBLESHOOTING:")
        print("1. Vai su Firebase Console: https://console.firebase.google.com/")
        print(f"2. Verifica progetto: {setup.project_id}")
        print("3. Controlla che Firestore sia abilitato")
        print("4. Verifica di essere Owner/Editor del progetto")
        return False

    print("\n🎉 SETUP COMPLETATO!")
    print("✅ Firebase configurato correttamente")
    print("✅ Puoi ora eseguire: python longeviva_food_database.py")

    return True


if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)