#!/bin/bash

# Script di deployment per Longeviva su Google Cloud
# Supporta Cloud Run, App Engine e GKE

set -e  # Exit on error

PROJECT_ID=""
#REGION="europe-west4"
REGION="us-central1"
SERVICE_NAME="longi-ai-apis"
DEPLOYMENT_TYPE=""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--project)
            PROJECT_ID="$2"
            shift 2
            ;;
        -r|--region)
            REGION="$2"
            shift 2
            ;;
        -t|--type)
            DEPLOYMENT_TYPE="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 -p PROJECT_ID [-r REGION] [-t cloud-run|app-engine]"
            echo "Options:"
            echo "  -p, --project    Google Cloud Project ID (required)"
            echo "  -r, --region     Region (default: us-central1)"
            echo "  -t, --type       Deployment type: cloud-run or app-engine"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Validate required parameters
if [ -z "$PROJECT_ID" ]; then
    print_error "Project ID is required. Use -p PROJECT_ID"
    exit 1
fi

if [ -z "$DEPLOYMENT_TYPE" ]; then
    echo "Select deployment type:"
    echo "1. Cloud Run (recommended)"
    echo "2. App Engine"
    read -p "Choice (1/2): " choice

    case $choice in
        1) DEPLOYMENT_TYPE="cloud-run" ;;
        2) DEPLOYMENT_TYPE="app-engine" ;;
        *)
            print_error "Invalid choice"
            exit 1
            ;;
    esac
fi

print_status "Starting deployment to Google Cloud"
print_status "Project: $PROJECT_ID"
print_status "Region: $REGION"
print_status "Type: $DEPLOYMENT_TYPE"

# Check prerequisites
print_status "Checking prerequisites..."

# Check gcloud
if ! command -v gcloud &> /dev/null; then
    print_error "gcloud CLI not found. Install from https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check Docker (for Cloud Run)
if [ "$DEPLOYMENT_TYPE" = "cloud-run" ] && ! command -v docker &> /dev/null; then
    print_error "Docker not found. Install Docker for Cloud Run deployment"
    exit 1
fi

# Set project
print_status "Setting project..."
gcloud config set project $PROJECT_ID

# Enable APIs
print_status "Enabling required APIs..."
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    aiplatform.googleapis.com \
    ml.googleapis.com

# Create Dockerfile for Cloud Run
if [ "$DEPLOYMENT_TYPE" = "cloud-run" ]; then
    print_status "Creating Dockerfile..."
    cat > Dockerfile << EOF
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements_vertex.txt .
RUN pip install --no-cache-dir -r requirements_vertex.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8080
ENV HOST=0.0.0.0

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8080/health || exit 1

# Run the application
CMD ["python", "api_server.py"]
EOF

    # Create .dockerignore
    cat > .dockerignore << EOF
__pycache__
*.pyc
.git
.gitignore
README.md
Dockerfile
.dockerignore
tests/
.pytest_cache/
.env.local
.venv/
venv/
EOF

    print_status "Building and deploying to Cloud Run..."

    # Build and deploy with Cloud Build
    gcloud run deploy $SERVICE_NAME \
        --source . \
        --platform managed \
        --region $REGION \
        --allow-unauthenticated \
        --set-env-vars="GOOGLE_CLOUD_PROJECT=$PROJECT_ID" \
        --memory=1Gi \
        --cpu=1 \
        --timeout=300 \
        --max-instances=10 \
        --min-instances=0

    # Get the service URL
    SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")
    print_status "Cloud Run deployment completed!"
    print_status "Service URL: $SERVICE_URL"
    print_status "API Documentation: $SERVICE_URL/docs"

fi

# App Engine deployment
if [ "$DEPLOYMENT_TYPE" = "app-engine" ]; then
    print_status "Creating app.yaml for App Engine..."

    cat > app.yaml << EOF
runtime: python39

env_variables:
  GOOGLE_CLOUD_PROJECT: $PROJECT_ID

automatic_scaling:
  min_instances: 0
  max_instances: 10
  target_cpu_utilization: 0.6

resources:
  cpu: 1
  memory_gb: 1
  disk_size_gb: 10

handlers:
- url: /.*
  script: auto
EOF

    print_status "Deploying to App Engine..."
    gcloud app deploy app.yaml --quiet

    APP_URL=$(gcloud app describe --format="value(defaultHostname)")
    print_status "App Engine deployment completed!"
    print_status "Service URL: https://$APP_URL"
    print_status "API Documentation: https://$APP_URL/docs"
fi

# Test the deployment
print_status "Testing the deployment..."
if [ "$DEPLOYMENT_TYPE" = "cloud-run" ]; then
    TEST_URL="$SERVICE_URL/health"
else
    TEST_URL="https://$APP_URL/health"
fi

if curl -f "$TEST_URL" > /dev/null 2>&1; then
    print_status "Health check passed! Deployment is working."
else
    print_warning "Health check failed. Check logs for issues."
fi

# Show final information
print_status "Deployment Summary:"
echo "=================================="
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Type: $DEPLOYMENT_TYPE"
if [ "$DEPLOYMENT_TYPE" = "cloud-run" ]; then
    echo "Service URL: $SERVICE_URL"
    echo "API Docs: $SERVICE_URL/docs"
else
    echo "Service URL: https://$APP_URL"
    echo "API Docs: https://$APP_URL/docs"
fi
echo "=================================="

print_status "Next steps:"
echo "1. Test your API endpoints"
echo "2. Configure domain name (optional)"
echo "3. Set up monitoring and alerts"
echo "4. Configure CI/CD pipeline"

# Create monitoring script
print_status "Creating monitoring script..."
cat > monitor_deployment.sh << EOF
#!/bin/bash
# Simple monitoring script for Longeviva deployment

PROJECT_ID="$PROJECT_ID"
SERVICE_NAME="$SERVICE_NAME"
REGION="$REGION"

while true; do
    echo "\$(date): Checking service health..."

    if [ "$DEPLOYMENT_TYPE" = "cloud-run" ]; then
        STATUS=\$(gcloud run services describe \$SERVICE_NAME --region=\$REGION --format="value(status.conditions[0].type)")
        URL=\$(gcloud run services describe \$SERVICE_NAME --region=\$REGION --format="value(status.url)")
    else
        # App Engine monitoring
        URL="https://\$(gcloud app describe --format="value(defaultHostname)")"
        STATUS="Ready"  # App Engine doesn't have the same status format
    fi

    if curl -f "\$URL/health" > /dev/null 2>&1; then
        echo "✅ Service is healthy: \$URL"
    else
        echo "❌ Service health check failed!"
        # Here you could add notification logic (email, Slack, etc.)
    fi

    sleep 300  # Check every 5 minutes
done
EOF

chmod +x monitor_deployment.sh

print_status "Deployment completed successfully!"
print_warning "Remember to:"
echo "- Set up proper authentication for production"
echo "- Configure environment variables"
echo "- Set up database connections"
echo "- Configure logging and monitoring"
echo "- Test all endpoints thoroughly"