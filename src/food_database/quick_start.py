#!/usr/bin/env python3
"""
Longeviva Food Database - Quick Start
Script rapido per deployment immediato
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command, description):
    """Execute command with logging"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completato")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} fallito: {e}")
        if e.stdout:
            print(f"Output: {e.stdout}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return False


def check_file_exists(filepath, description):
    """Check if file exists"""
    if os.path.exists(filepath):
        print(f"✅ {description} trovato: {filepath}")
        return True
    else:
        print(f"❌ {description} mancante: {filepath}")
        return False


def main():
    """Quick start deployment"""
    print("🚀 LONGEVIVA FOOD DATABASE - QUICK START")
    print("=" * 50)

    # Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or python_version.minor < 8:
        print("❌ Python 3.8+ richiesto")
        return False

    print(f"✅ Python {python_version.major}.{python_version.minor} OK")

    # Install requirements
    if not run_command("pip install -r requirements.txt", "Installazione dipendenze"):
        return False

    # Check Firebase credentials
    if not check_file_exists("service-account-key.json", "Service Account Key"):
        print("\n🔧 SETUP RICHIESTO:")
        print("1. Esegui: python firebase_setup.py")
        print("2. Segui istruzioni Firebase Console")
        print("3. Ri-esegui questo script")
        return False

    # Deploy to development
    print("\n📦 DEPLOYMENT DATABASE SVILUPPO")
    if not run_command("python longeviva_food_database.py", "Popolamento database sviluppo"):
        return False

    print("\n🎉 DEPLOYMENT COMPLETATO!")
    print("\n📊 STATISTICHE:")
    print("- Database: longeviva-web-app-dev-sviluppo")
    print("- Collection: foods")
    print("- Alimenti: 150+")
    print("- Categorie: 7 (Proteine, Carboidrati, Verdure, Frutta, Grassi, Latticini, Bevande)")

    print("\n🔄 PROSSIMI STEPS:")
    print("1. Verifica dati su Firebase Console")
    print("2. Test integrazione Flutter")
    print("3. Per produzione: python migration_prod.py")

    print("\n📚 DOCUMENTAZIONE:")
    print("- Guida completa: README_IMPLEMENTAZIONE.md")
    print("- Setup Firebase: firebase_setup.py")
    print("- Migrazione prod: migration_prod.py")

    return True


if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)