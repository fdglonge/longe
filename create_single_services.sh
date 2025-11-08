#!/bin/bash

# Script per deployare i 5 servizi reali di Longeviva
# Usa i file esistenti patient_routes.py, doctor_routes.py, longi_routes.py
set -e

PROJECT_ID="longeviva-web-app-dev"
REGION="us-central1"

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

# Definizione dei 5 servizi reali basati sui file esistenti
declare -a SERVICES=(
    "inserisci-anagrafica:POST:src/api/patient_routes.py:inserisci_anagrafica"
    "completa-storiamedica:POST:src/api/patient_routes.py:completa_storiamedica"
    "genera-sommario:POST:src/api/patient_routes.py:genera_sommario"
    "raccomanda-dottore:POST:src/api/doctor_routes.py:raccomanda_dottore"
    "genera-lista-spesa:GET:src/api/longi_routes.py:genera_lista_spesa"
)

print_header "DEPLOY SERVIZI LONGEVIVA REALI"
echo "Deploy dei 5 servizi usando i file di codice esistenti"

# Verifica prerequisiti
if [ ! -f "src/api/patient_routes.py" ]; then
    print_error "File src/api/patient_routes.py non trovato!"
    exit 1
fi

if [ ! -f "src/api/doctor_routes.py" ]; then
    print_error "File src/api/doctor_routes.py non trovato!"
    exit 1
fi

if [ ! -f "src/api/longi_routes.py" ]; then
    print_error "File src/api/longi_routes.py non trovato!"
    exit 1
fi

# Set project
gcloud config set project $PROJECT_ID

# Enable APIs
print_status "Abilitazione API richieste..."
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    aiplatform.googleapis.com \
    firestore.googleapis.com

# Clean up old services directory
if [ -d "services" ]; then
    print_warning "Rimozione directory servizi esistente..."
    rm -rf services
fi

mkdir -p services

# Function per creare un singolo servizio da file esistente
create_service_from_existing() {
    local service_name=$1
    local http_method=$2
    local source_file=$3
    local function_name=$4

    print_status "Creazione servizio: $service_name da $source_file"

    # Create service directory
    mkdir -p "services/$service_name"
    cd "services/$service_name"

    # Copy della struttura src completa (dependencies)
    cp -r ../../src .

    # Create requirements.txt based on the actual project
    cat > requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
google-cloud-aiplatform==1.38.0
google-cloud-firestore==2.13.1
firebase-admin
python-multipart==0.0.6
httpx==0.25.2
python-dotenv==1.0.0
numpy==1.24.3
requests==2.31.0
EOF

    # Create Dockerfile
    cat > Dockerfile << 'EOF'
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Environment variables
ENV PYTHONPATH=/app
ENV PORT=8080
ENV HOST=0.0.0.0

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the application
CMD ["python", "main.py"]
EOF

    # Create .dockerignore
    cat > .dockerignore << 'EOF'
__pycache__
*.pyc
.git
.gitignore
.pytest_cache/
.env
.env.local
.venv/
venv/
tests/
*.md
README.md
Dockerfile
.dockerignore
EOF

    # Create main.py che importa il codice esistente
    create_main_py "$service_name" "$source_file" "$function_name"

    cd ../..
}

# Function per creare main.py che usa il codice esistente
create_main_py() {
    local service_name=$1
    local source_file=$2
    local function_name=$3

    case $service_name in
        "inserisci-anagrafica")
            cat > main.py << 'EOF'
import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import the existing route
from src.api.patient_routes import inserisci_anagrafica

app = FastAPI(
    title="Longeviva Inserisci Anagrafica Service",
    description="Servizio per estrazione dati anagrafici da testo",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "inserisci-anagrafica"}

# Add the existing route
app.add_api_route("/inserisci-anagrafica", inserisci_anagrafica, methods=["POST"])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
EOF
            ;;
        "completa-storiamedica")
            cat > main.py << 'EOF'
import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import the existing route
from src.api.patient_routes import completa_storiamedica

app = FastAPI(
    title="Longeviva Completa Storia Medica Service",
    description="Servizio per estrazione storia medica da testo",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "completa-storiamedica"}

# Add the existing route
app.add_api_route("/completa-storiamedica", completa_storiamedica, methods=["POST"])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
EOF
            ;;
        "genera-sommario")
            cat > main.py << 'EOF'
import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import the existing route
from src.api.patient_routes import genera_sommario

app = FastAPI(
    title="Longeviva Genera Sommario Service",
    description="Servizio per generazione sommario onboarding",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "genera-sommario"}

# Add the existing route
app.add_api_route("/genera-sommario", genera_sommario, methods=["POST"])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
EOF
            ;;
        "raccomanda-dottore")
            cat > main.py << 'EOF'
import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import the existing route
from src.api.doctor_routes import raccomanda_dottore

app = FastAPI(
    title="Longeviva Raccomanda Dottore Service",
    description="Servizio per raccomandazione medici con AI",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "raccomanda-dottore"}

# Add the existing route
app.add_api_route("/raccomanda-dottore", raccomanda_dottore, methods=["POST"])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
EOF
            ;;
        "genera-lista-spesa")
            cat > main.py << 'EOF'
import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import the existing route
from src.api.longi_routes import genera_lista_spesa

app = FastAPI(
    title="Longeviva Genera Lista Spesa Service",
    description="Servizio per generazione lista spesa da dieta",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "genera-lista-spesa"}

# Add the existing route - with path parameter
app.add_api_route("/genera-lista-spesa/{id_dieta}", genera_lista_spesa, methods=["GET"])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
EOF
            ;;
    esac
}

# Function per deployare un servizio
deploy_service() {
    local service_name=$1

    print_status "Deploy servizio: $service_name"

    gcloud run deploy "$service_name" \
        --source "./services/$service_name" \
        --platform managed \
        --region $REGION \
        --allow-unauthenticated \
        --set-env-vars="GOOGLE_CLOUD_PROJECT=$PROJECT_ID,SERVICE_NAME=$service_name" \
        --memory=2Gi \
        --cpu=1 \
        --timeout=600 \
        --max-instances=10 \
        --min-instances=0

    # Get service URL
    local service_url
    service_url=$(gcloud run services describe "$service_name" --region=$REGION --format="value(status.url)")
    echo "✅ Servizio deployato: $service_name → $service_url"

    # Test health endpoint
    if curl -f "$service_url/health" > /dev/null 2>&1; then
        echo "✅ Health check OK per $service_name"
    else
        echo "⚠️  Health check fallito per $service_name"
    fi

    echo ""
}

# Parse command line arguments
DEPLOY_SERVICES=false
CREATE_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --deploy)
            DEPLOY_SERVICES=true
            shift
            ;;
        --create-only)
            CREATE_ONLY=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [--deploy] [--create-only]"
            echo "Opzioni:"
            echo "  --deploy      Crea e deploya servizi su Cloud Run"
            echo "  --create-only Crea solo la struttura senza deployare"
            exit 0
            ;;
        *)
            print_error "Opzione sconosciuta: $1"
            exit 1
            ;;
    esac
done

# Main execution
print_header "Deploy Microservizi Longeviva dai File Esistenti"

# Create all services from existing files
for service_def in "${SERVICES[@]}"; do
    IFS=':' read -r service_name http_method source_file function_name <<< "$service_def"
    create_service_from_existing "$service_name" "$http_method" "$source_file" "$function_name"
done

print_status "Strutture servizi create con successo!"

# Deploy if requested
if [ "$DEPLOY_SERVICES" = true ] && [ "$CREATE_ONLY" = false ]; then
    print_header "Deploy Servizi su Cloud Run"

    for service_def in "${SERVICES[@]}"; do
        IFS=':' read -r service_name http_method source_file function_name <<< "$service_def"
        deploy_service "$service_name"
    done

    print_header "🎉 TUTTI I SERVIZI DEPLOYATI!"

    # Show summary
    echo "URL dei servizi:"
    for service_def in "${SERVICES[@]}"; do
        IFS=':' read -r service_name http_method source_file function_name <<< "$service_def"
        service_url=$(gcloud run services describe "$service_name" --region=$REGION --format="value(status.url)" 2>/dev/null || echo "Non deployato")
        echo "$service_name ($http_method): $service_url"
    done

elif [ "$CREATE_ONLY" = false ]; then
    echo ""
    echo "📝 Servizi creati localmente. Per deployare:"
    echo "   $0 --deploy"
    echo ""
    echo "Per testare localmente, entra nella directory del servizio:"
    echo "   cd services/inserisci-anagrafica && python main.py"
fi

print_header "Servizi Deployati"
echo "I 5 servizi ora usano il codice reale dai file esistenti:"
echo "- inserisci-anagrafica: da patient_routes.py"
echo "- completa-storiamedica: da patient_routes.py"
echo "- genera-sommario: da patient_routes.py"
echo "- raccomanda-dottore: da doctor_routes.py"
echo "- genera-lista-spesa: da longi_routes.py"