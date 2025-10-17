#!/bin/bash

# Setup API Gateway per Longeviva - Solo i 5 servizi reali
set -e

PROJECT_ID="longeviva-web-app-dev"
REGION="us-central1"
GATEWAY_ID="longeviva-api-gateway"
CONFIG_ID="longeviva-api-config"
DOMAIN="api.longeviva.com"

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

# Definizione dei 5 servizi reali di Longeviva (deve corrispondere al deploy script)
declare -a SERVICES=(
    "/inserisci-anagrafica:POST:inserisci-anagrafica"
    "/completa-storiamedica:POST:completa-storiamedica"
    "/genera-sommario:POST:genera-sommario"
    "/raccomanda-dottore:POST:raccomanda-dottore"
    "/genera-lista-spesa:GET:genera-lista-spesa"
)

print_header "LONGEVIVA API GATEWAY SETUP"
echo "Configurazione gateway per i 5 servizi reali di Longeviva"

# Set project
gcloud config set project $PROJECT_ID

# Enable required APIs
print_status "Abilitazione API Gateway e servizi correlati..."
gcloud services enable \
    apigateway.googleapis.com \
    servicecontrol.googleapis.com \
    servicemanagement.googleapis.com

# Function per ottenere gli URL dei servizi
get_service_urls() {
    print_status "Recupero URL servizi Cloud Run..."

    declare -A SERVICE_URLS

    for service_def in "${SERVICES[@]}"; do
        IFS=':' read -r endpoint_path http_method cloud_run_name <<< "$service_def"

        print_status "Recupero URL per servizio: $cloud_run_name"

        # Get the Cloud Run service URL
        service_url=$(gcloud run services describe "$cloud_run_name" --region=$REGION --format="value(status.url)" 2>/dev/null || echo "")

        if [ -z "$service_url" ]; then
            print_error "Servizio $cloud_run_name non trovato! Deployare prima i servizi."
            exit 1
        fi

        SERVICE_URLS["$endpoint_path"]="$service_url"
        echo "  $endpoint_path → $service_url"
    done

    # Export for use in OpenAPI spec generation
    export SERVICE_URLS
}

# Crea specifica OpenAPI
create_openapi_spec() {
    print_status "Creazione specifica OpenAPI..."

    cat > openapi_longeviva.yaml << 'EOF'
swagger: '2.0'
info:
  title: Longeviva Unified API
  description: 'API unificata per tutti i microservizi Longeviva - mapping 1:1'
  version: '1.0.0'
  contact:
    name: Longeviva Team
    email: support@longeviva.com

host: api.longeviva.com
schemes:
  - https

produces:
  - application/json

consumes:
  - application/json

# Security definitions (opzionale per ora)
securityDefinitions:
  api_key:
    type: apiKey
    name: x-api-key
    in: header

paths:
EOF

    # Aggiungi ogni endpoint specifico
    for service_def in "${SERVICES[@]}"; do
        IFS=':' read -r endpoint_path http_method cloud_run_name <<< "$service_def"

        # Get service URL from gcloud
        service_url=$(gcloud run services describe "$cloud_run_name" --region=$REGION --format="value(status.url)" 2>/dev/null)

        case "$endpoint_path" in
            "/inserisci-anagrafica")
                cat >> openapi_longeviva.yaml << EOF
  /inserisci-anagrafica:
    post:
      summary: Estrae dati anagrafici da testo
      description: Estrae dati anagrafici strutturati da messaggio di testo libero
      operationId: inserisci_anagrafica
      x-google-backend:
        address: $service_url
        path_translation: APPEND_PATH_TO_ADDRESS
      parameters:
        - name: body
          in: body
          required: true
          schema:
            type: object
            properties:
              messaggio:
                type: string
                description: Messaggio contenente dati anagrafici
            required:
              - messaggio
      responses:
        200:
          description: Dati estratti con successo
          schema:
            type: object
            properties:
              success:
                type: boolean
              message:
                type: string
              dati_estratti:
                type: object
              is_complete:
                type: boolean
              campi_mancanti:
                type: array
                items:
                  type: string
        400:
          description: Richiesta non valida
        500:
          description: Errore interno del server

EOF
                ;;
            "/completa-storiamedica")
                cat >> openapi_longeviva.yaml << EOF
  /completa-storiamedica:
    post:
      summary: Estrae storia medica da testo
      description: Estrae storia medica strutturata da messaggio di testo libero
      operationId: completa_storiamedica
      x-google-backend:
        address: $service_url
        path_translation: APPEND_PATH_TO_ADDRESS
      parameters:
        - name: body
          in: body
          required: true
          schema:
            type: object
            properties:
              messaggio:
                type: string
                description: Messaggio contenente storia medica
            required:
              - messaggio
      responses:
        200:
          description: Storia medica estratta con successo
          schema:
            type: object
            properties:
              success:
                type: boolean
              message:
                type: string
              dati_estratti:
                type: object
              is_complete:
                type: boolean
              campi_mancanti:
                type: array
                items:
                  type: string

EOF
                ;;
            "/genera-sommario")
                cat >> openapi_longeviva.yaml << EOF
  /genera-sommario:
    post:
      summary: Genera sommario onboarding
      description: Genera sommario personalizzato dai dati di onboarding del paziente
      operationId: genera_sommario
      x-google-backend:
        address: $service_url
        path_translation: APPEND_PATH_TO_ADDRESS
      parameters:
        - name: body
          in: body
          required: true
          schema:
            type: object
            properties:
              nome:
                type: string
                description: Nome del paziente
              onBoardingData:
                type: object
                properties:
                  reasons:
                    type: array
                    items:
                      type: string
                  goals:
                    type: array
                    items:
                      type: string
                  expectations:
                    type: array
                    items:
                      type: string
            required:
              - nome
              - onBoardingData
      responses:
        200:
          description: Sommario generato con successo
          schema:
            type: object
            properties:
              success:
                type: boolean
              message:
                type: string
              onBoardingSummary:
                type: string

EOF
                ;;
            "/raccomanda-dottore")
                cat >> openapi_longeviva.yaml << EOF
  /raccomanda-dottore:
    post:
      summary: Raccomanda medici con AI
      description: Cerca e raccomanda medici utilizzando matching AI basato su criteri specifici
      operationId: raccomanda_dottore
      x-google-backend:
        address: $service_url
        path_translation: APPEND_PATH_TO_ADDRESS
      parameters:
        - name: body
          in: body
          required: true
          schema:
            type: object
            properties:
              motivo_visita:
                type: string
                description: Motivo della visita medica
              citta:
                type: string
                description: Città del paziente
              scelta_medico:
                type: object
                properties:
                  vicinanza:
                    type: integer
                    minimum: 1
                    maximum: 5
                  specializzazione:
                    type: integer
                    minimum: 1
                    maximum: 5
                  costo:
                    type: integer
                    minimum: 1
                    maximum: 5
                  area_interesse:
                    type: integer
                    minimum: 1
                    maximum: 5
            required:
              - motivo_visita
              - citta
              - scelta_medico
      responses:
        200:
          description: Medici raccomandati trovati
          schema:
            type: object
            properties:
              success:
                type: boolean
              message:
                type: string
              dottori:
                type: array
                items:
                  type: object
                  properties:
                    id:
                      type: string
                    nome:
                      type: string
                    cognome:
                      type: string
                    specializzazione:
                      type: string
                    citta:
                      type: string
                    match_score:
                      type: number
              total_dottori:
                type: integer

EOF
                ;;
            "/genera-lista-spesa")
                cat >> openapi_longeviva.yaml << EOF
  /genera-lista-spesa/{id_dieta}:
    get:
      summary: Genera lista spesa da dieta
      description: Genera una lista della spesa settimanale per una dieta specifica
      operationId: genera_lista_spesa
      x-google-backend:
        address: $service_url
        path_translation: APPEND_PATH_TO_ADDRESS
      parameters:
        - name: id_dieta
          in: path
          required: true
          type: string
          description: ID della dieta
      responses:
        200:
          description: Lista spesa generata con successo
          schema:
            type: object
            properties:
              success:
                type: boolean
              message:
                type: string
              id_dieta:
                type: string
              lista_spesa:
                type: string
              generated_at:
                type: string
        404:
          description: Dieta non trovata

EOF
                ;;
        esac
    done

    print_status "Specifica OpenAPI creata: openapi_longeviva.yaml"
}

# Crea configurazione API (senza gateway)
create_api_config() {
    print_status "Creazione API..."

    # Create the API first
    gcloud api-gateway apis create $GATEWAY_ID \
        --project=$PROJECT_ID || true  # Continue if already exists

    print_status "API creata: $GATEWAY_ID"
}

# Deploy configurazione API Gateway
deploy_api_gateway() {
    print_status "Creazione configurazione API Gateway..."

    # Create API config
    gcloud api-gateway api-configs create $CONFIG_ID \
        --api=$GATEWAY_ID \
        --openapi-spec=openapi_longeviva.yaml \
        --project=$PROJECT_ID \
        --backend-auth-service-account=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")-compute@developer.gserviceaccount.com

    print_status "Deploy API Gateway..."

    # Create the gateway
    gcloud api-gateway gateways create $GATEWAY_ID \
        --api=$GATEWAY_ID \
        --api-config=$CONFIG_ID \
        --location=$REGION \
        --project=$PROJECT_ID

    # Get gateway URL
    GATEWAY_URL=$(gcloud api-gateway gateways describe $GATEWAY_ID --location=$REGION --format="value(defaultHostname)")

    print_status "API Gateway deployato con successo!"
    echo "Gateway URL: https://$GATEWAY_URL"
}

# Test gateway
test_gateway() {
    print_status "Test endpoint API Gateway..."

    GATEWAY_URL=$(gcloud api-gateway gateways describe $GATEWAY_ID --location=$REGION --format="value(defaultHostname)" 2>/dev/null || echo "")

    if [ -z "$GATEWAY_URL" ]; then
        print_warning "Gateway non ancora deployato, salto i test"
        return
    fi

    # Test health endpoint di un servizio direttamente
    print_status "Test health endpoint..."
    service_url=$(gcloud run services describe "inserisci-anagrafica" --region=$REGION --format="value(status.url)" 2>/dev/null)
    if curl -f "$service_url/health" > /dev/null 2>&1; then
        echo "✅ Health check diretto passato"
    else
        echo "❌ Health check diretto fallito"
    fi

    # Test endpoint gateway
    print_status "Test endpoint gateway..."
    test_payload='{"messaggio":"test estrazione dati"}'
    if curl -f "https://$GATEWAY_URL/inserisci-anagrafica" -X POST -H "Content-Type: application/json" -d "$test_payload" > /dev/null 2>&1; then
        echo "✅ Test endpoint gateway passato"
    else
        echo "⚠️  Test endpoint gateway fallito (normale durante setup iniziale)"
    fi
}

# Setup dominio personalizzato (opzionale)
setup_custom_domain() {
    print_warning "Setup dominio personalizzato per api.longeviva.com richiede:"
    echo "1. Verifica proprietà dominio in Google Cloud Console"
    echo "2. Setup certificato SSL"
    echo "3. Configurazione DNS"
    echo ""
    echo "Passi manuali necessari:"
    echo "1. Vai alla console API Gateway"
    echo "2. Clicca sul gateway: $GATEWAY_ID"
    echo "3. Aggiungi dominio personalizzato: $DOMAIN"
    echo "4. Segui le istruzioni per SSL e DNS"
    echo ""
    GATEWAY_URL=$(gcloud api-gateway gateways describe $GATEWAY_ID --location=$REGION --format="value(defaultHostname)" 2>/dev/null || echo "GATEWAY_URL")
    echo "URL Gateway per ora: https://$GATEWAY_URL"
}

# Cleanup gateway esistente (se necessario)
cleanup_existing() {
    print_warning "Pulizia gateway esistente (se presente)..."

    # Delete existing gateway
    gcloud api-gateway gateways delete $GATEWAY_ID --location=$REGION --quiet 2>/dev/null || true

    # Delete existing config
    gcloud api-gateway api-configs delete $CONFIG_ID --api=$GATEWAY_ID --quiet 2>/dev/null || true

    print_status "Pulizia completata"
}

# Main execution
case "${1:-}" in
    "--cleanup")
        cleanup_existing
        print_status "Pulizia completata. Esegui con --deploy per creare nuovo gateway."
        ;;
    "--create-spec-only")
        get_service_urls
        create_openapi_spec
        print_status "Specifica OpenAPI creata. Deploy con: $0 --deploy"
        ;;
    "--deploy")
        get_service_urls
        create_openapi_spec
        create_api_config
        deploy_api_gateway
        test_gateway
        setup_custom_domain
        print_header "🎉 API GATEWAY SETUP COMPLETATO!"
        ;;
    "--test")
        test_gateway
        ;;
    "--force-deploy")
        cleanup_existing
        get_service_urls
        create_openapi_spec
        create_api_config
        deploy_api_gateway
        test_gateway
        setup_custom_domain
        print_header "🎉 API GATEWAY FORCE DEPLOYATO!"
        ;;
    *)
        echo "Usage: $0 [--create-spec-only|--deploy|--test|--cleanup|--force-deploy]"
        echo ""
        echo "Opzioni:"
        echo "  --create-spec-only  Crea solo specifica OpenAPI"
        echo "  --deploy           Crea specifica e deploya API Gateway"
        echo "  --test             Testa gateway esistente"
        echo "  --cleanup          Rimuovi gateway e config esistenti"
        echo "  --force-deploy     Pulisci e rideploya tutto"
        echo ""
        echo "Prerequisiti:"
        echo "  - Tutti i servizi Cloud Run devono essere deployati prima"
        echo "  - I servizi devono essere accessibili e healthy"
        exit 1
        ;;
esac

# Istruzioni riassuntive
if [ "${1:-}" = "--deploy" ] || [ "${1:-}" = "--force-deploy" ]; then
    print_header "Come usare il tuo API Gateway"

    GATEWAY_URL=$(gcloud api-gateway gateways describe $GATEWAY_ID --location=$REGION --format="value(defaultHostname)" 2>/dev/null || echo "GATEWAY_URL")

    echo "🔗 Endpoint API unificato: https://$GATEWAY_URL"
    echo ""
    echo "📋 Esempi di chiamate API:"
    echo ""
    echo "# Estrai dati anagrafici"
    echo "curl -X POST https://$GATEWAY_URL/inserisci-anagrafica \\"
    echo "  -H 'Content-Type: application/json' \\"
    echo "  -d '{\"messaggio\": \"Mi chiamo Mario Rossi, nato il 15/01/1990 a Milano\"}'"
    echo ""
    echo "# Completa storia medica"
    echo "curl -X POST https://$GATEWAY_URL/completa-storiamedica \\"
    echo "  -H 'Content-Type: application/json' \\"
    echo "  -d '{\"messaggio\": \"Non ho allergie, dormo 7 ore, faccio sport 3 volte\"}'"
    echo ""
    echo "# Genera sommario onboarding"
    echo "curl -X POST https://$GATEWAY_URL/genera-sommario \\"
    echo "  -H 'Content-Type: application/json' \\"
    echo "  -d '{\"nome\": \"Mario\", \"onBoardingData\": {\"reasons\": [\"1\"], \"goals\": [\"2\"], \"expectations\": [\"3\"]}}'"
    echo ""
    echo "# Raccomanda dottore"
    echo "curl -X POST https://$GATEWAY_URL/raccomanda-dottore \\"
    echo "  -H 'Content-Type: application/json' \\"
    echo "  -d '{\"motivo_visita\": \"controllo cardiologico\", \"citta\": \"Milano\", \"scelta_medico\": {\"vicinanza\": 4, \"specializzazione\": 5, \"costo\": 3, \"area_interesse\": 4}}'"
    echo ""
    echo "# Genera lista spesa"
    echo "curl https://$GATEWAY_URL/genera-lista-spesa/dieta123"
    echo ""
    echo "🌐 Prossimo: Setup dominio personalizzato api.longeviva.com seguendo le istruzioni sopra"
    echo ""
    echo "📊 Monitoraggio:"
    echo "- Logs: gcloud logging read 'resource.type=\"api_gateway\"'"
    echo "- Metriche: Google Cloud Console > API Gateway > $GATEWAY_ID"
fi