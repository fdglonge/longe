#!/bin/bash

# Script per deployare le Firebase Functions di Longeviva
# Include le 5 nuove API Functions
set -e

PROJECT_ID="longeviva-web-app-dev"
FUNCTIONS_DIR="functions"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}======================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}======================================${NC}"
}

# Lista delle 5 nuove Longeviva Functions
LONGEVIVA_FUNCTIONS=(
    "inserisciAnagrafica"
    "completaStoriaMedica"
    "generaSommario"
    "raccomandaDottore"
    "generaListaSpesa"
)

print_header "DEPLOY FIREBASE FUNCTIONS LONGEVIVA"
echo "Deploy delle 5 nuove API Longeviva come Cloud Functions"

# Check if Firebase CLI is installed
if ! command -v firebase &> /dev/null; then
    print_error "Firebase CLI non installato. Installalo con: npm install -g firebase-tools"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "firebase.json" ]; then
    print_warning "firebase.json non trovato. Creazione configurazione base..."
    cat > firebase.json << 'EOF'
{
  "functions": [
    {
      "source": "functions",
      "codebase": "default",
      "ignore": [
        "node_modules",
        ".git",
        "firebase-debug.log",
        "firebase-debug.*.log"
      ]
    }
  ],
  "firestore": {
    "rules": "firestore.rules",
    "indexes": "firestore.indexes.json"
  },
  "storage": {
    "rules": "storage.rules"
  }
}
EOF
fi

# Check if .firebaserc exists
if [ ! -f ".firebaserc" ]; then
    print_warning ".firebaserc non trovato. Creazione configurazione progetto..."
    cat > .firebaserc << EOF
{
  "projects": {
    "default": "$PROJECT_ID"
  }
}
EOF
fi

# Create functions directory if it doesn't exist
if [ ! -d "$FUNCTIONS_DIR" ]; then
    print_status "Creazione directory functions..."
    mkdir -p $FUNCTIONS_DIR
fi

cd $FUNCTIONS_DIR

# Check if this is an update or fresh install
EXISTING_INDEX=false
if [ -f "index.js" ]; then
    EXISTING_INDEX=true
    print_warning "Trovato index.js esistente. Backup in corso..."
    cp index_v1.js index_v1.js.backup.$(date +%Y%m%d_%H%M%S)
fi

print_header "SETUP DIPENDENZE"

# Create package.json se non esiste
if [ ! -f "package.json" ]; then
    print_status "Creazione package.json..."
    cat > package.json << 'EOF'
{
  "name": "longeviva-firebase-functions",
  "version": "1.0.0",
  "description": "Firebase Functions for Longeviva platform - complete with existing + new functions",
  "main": "index.js",
  "scripts": {
    "serve": "firebase emulators:start --only functions",
    "shell": "firebase functions:shell",
    "start": "npm run shell",
    "deploy": "firebase deploy --only functions",
    "deploy:specific": "firebase deploy --only functions:inserisciAnagrafica,functions:completaStoriaMedica,functions:generaSommario,functions:raccomandaDottore,functions:generaListaSpesa",
    "logs": "firebase functions:log",
    "test": "jest",
    "lint": "eslint .",
    "lint:fix": "eslint . --fix"
  },
  "engines": {
    "node": "18"
  },
  "dependencies": {
    "firebase-admin": "^11.11.0",
    "firebase-functions": "^4.5.0",
    "@google-cloud/aiplatform": "^3.11.0",
    "@google-cloud/firestore": "^7.1.0",
    "axios": "^1.6.0",
    "crypto": "^1.0.1",
    "uuid": "^9.0.1"
  },
  "devDependencies": {
    "eslint": "^8.15.0",
    "eslint-config-google": "^0.14.0",
    "jest": "^29.0.0",
    "firebase-functions-test": "^3.1.0"
  },
  "private": true,
  "keywords": [
    "firebase",
    "functions",
    "longeviva",
    "healthcare",
    "cloud-functions"
  ],
  "author": "Longeviva Team",
  "license": "UNLICENSED"
}
EOF
fi

# Install dependencies
print_status "Installazione dipendenze npm..."
npm install

print_header "VERIFICA CONFIGURAZIONE"

# Login check
print_status "Verifica autenticazione Firebase..."
if ! firebase projects:list > /dev/null 2>&1; then
    print_warning "Login richiesto. Esegui: firebase login"
    exit 1
fi

# Set project
print_status "Impostazione progetto Firebase: $PROJECT_ID"
firebase use $PROJECT_ID

print_header "DEPLOY FUNCTIONS"

# Parse command line arguments
DEPLOY_MODE="longeviva"
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --all)
            DEPLOY_MODE="all"
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [options]"
            echo ""
            echo "Opzioni:"
            echo "  --all              Deploy tutte le functions (esistenti + nuove)"
            echo "  --dry-run          Simula il deploy senza eseguirlo"
            echo "  --help, -h         Mostra questo aiuto"
            echo ""
            echo "Funzioni Longeviva che saranno deployate:"
            for func in "${LONGEVIVA_FUNCTIONS[@]}"; do
                echo "  - $func"
            done
            exit 0
            ;;
        *)
            print_error "Opzione sconosciuta: $1"
            print_error "Usa --help per vedere le opzioni disponibili"
            exit 1
            ;;
    esac
done

if [ "$DRY_RUN" = true ]; then
    print_warning "MODALITA DRY RUN - nessun deploy effettivo"
    echo ""
    echo "Sarebbe eseguito:"
    if [ "$DEPLOY_MODE" = "longeviva" ]; then
        echo "firebase deploy --only $(printf "functions:%s," "${LONGEVIVA_FUNCTIONS[@]}" | sed 's/,$//')"
    else
        echo "firebase deploy --only functions"
    fi
    echo ""
    echo "Per eseguire il deploy reale, rimuovi --dry-run"
    exit 0
fi

# Verifica che index_v1.js esista
if [ ! -f "index.js" ]; then
    print_error "File index.js non trovato nella directory functions!"
    print_error "Crea il file index.js con il contenuto delle Cloud Functions prima di deployare."
    exit 1
fi

print_status "Inizio deploy..."

if [ "$DEPLOY_MODE" = "longeviva" ]; then
    print_status "Deploy solo funzioni Longeviva..."

    # Build the functions list for --only flag
    FUNCTIONS_LIST=$(printf "functions:%s," "${LONGEVIVA_FUNCTIONS[@]}" | sed 's/,$//')

    print_status "Comando: firebase deploy --only $FUNCTIONS_LIST"
    firebase deploy --only "$FUNCTIONS_LIST"

else
    print_status "Deploy tutte le funzioni..."
    firebase deploy --only functions
fi

print_header "DEPLOY COMPLETATO!"

# Show deployed functions info
print_status "Riepilogo funzioni deployate:"

if [ "$DEPLOY_MODE" = "longeviva" ]; then
    echo ""
    echo "NUOVE FUNZIONI LONGEVIVA API:"
    for func in "${LONGEVIVA_FUNCTIONS[@]}"; do
        echo "   $func - Callable Function (sicura, autenticata)"
    done
else
    echo ""
    echo "TUTTE LE FUNCTIONS (esistenti + nuove):"
    echo "   Funzioni esistenti: preservate e deployate"
    echo "   Nuove funzioni Longeviva:"
    for func in "${LONGEVIVA_FUNCTIONS[@]}"; do
        echo "   $func - Callable Function (sicura, autenticata)"
    done
fi

echo ""
print_status "Caratteristiche delle nuove functions:"
echo "   Autenticazione obbligatoria (context.auth)"
echo "   Controllo ruoli utente (DOCTOR/CLINIC/PATIENT)"
echo "   Nessuna URL pubblica (callable functions)"
echo "   Logging completo delle attivita"
echo "   Integrazione nativa con Firebase/Firestore"

echo ""
print_status "Come chiamare le functions dal client:"
echo ""
echo "// Import Firebase Functions"
echo "import { getFunctions, httpsCallable } from 'firebase/functions';"
echo ""
echo "// Chiama una function"
echo "const functions = getFunctions();"
echo "const inserisciAnagrafica = httpsCallable(functions, 'inserisciAnagrafica');"
echo ""
echo "const result = await inserisciAnagrafica({"
echo "  messaggio: 'Sono Mario, nato il 15/03/90 a Roma...'"
echo "});"

echo ""
print_status "Monitoring e logs:"
echo "   firebase functions:log"
echo "   firebase functions:log --only inserisciAnagrafica"

echo ""
print_status "Test delle functions:"
echo "   firebase emulators:start --only functions"
echo "   Poi testa su http://localhost:5001"

print_header "DEPLOY COMPLETATO CON SUCCESSO!"

cd .. # Return to project root