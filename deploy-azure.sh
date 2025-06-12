#!/bin/bash

# HR Candidate Management Tool - Azure Deployment Script
# This script automates the creation of all required Azure resources

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

# Check if Azure CLI is installed
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    if ! command -v az &> /dev/null; then
        print_error "Azure CLI is not installed. Please install it first."
        exit 1
    fi
    
    if ! az account show &> /dev/null; then
        print_error "Please login to Azure CLI first: az login"
        exit 1
    fi
    
    print_status "Prerequisites check passed"
}

# Get user input for configuration
get_configuration() {
    print_header "Configuration Setup"
    
    echo "Please provide the following information:"
    
    # Resource Group
    read -p "Enter Resource Group name (default: hr-candidate-tool-rg): " RESOURCE_GROUP
    RESOURCE_GROUP=${RESOURCE_GROUP:-hr-candidate-tool-rg}
    
    # Location
    echo "Available locations: eastus, westus2, westeurope, northeurope, eastasia, southeastasia"
    read -p "Enter Azure region (default: eastus): " LOCATION
    LOCATION=${LOCATION:-eastus}
    
    # Unique suffix for resource names
    UNIQUE_SUFFIX=$(date +%s | tail -c 6)
    
    # Resource names
    STORAGE_ACCOUNT="hrstore${UNIQUE_SUFFIX}"
    ACR_NAME="hracr${UNIQUE_SUFFIX}"
    OPENAI_NAME="hr-openai-${UNIQUE_SUFFIX}"
    APP_SERVICE_PLAN="hr-plan-${UNIQUE_SUFFIX}"
    WEB_APP_NAME="hr-candidate-${UNIQUE_SUFFIX}"
    
    echo ""
    print_status "Configuration:"
    echo "  Resource Group: $RESOURCE_GROUP"
    echo "  Location: $LOCATION"
    echo "  Storage Account: $STORAGE_ACCOUNT"
    echo "  Container Registry: $ACR_NAME"
    echo "  OpenAI Service: $OPENAI_NAME"
    echo "  App Service Plan: $APP_SERVICE_PLAN"
    echo "  Web App: $WEB_APP_NAME"
    echo ""
    
    read -p "Continue with this configuration? (y/N): " CONFIRM
    if [[ ! $CONFIRM =~ ^[Yy]$ ]]; then
        print_error "Deployment cancelled"
        exit 1
    fi
}

# Create Resource Group
create_resource_group() {
    print_header "Creating Resource Group"
    
    if az group show --name $RESOURCE_GROUP &> /dev/null; then
        print_warning "Resource group $RESOURCE_GROUP already exists"
    else
        print_status "Creating resource group: $RESOURCE_GROUP"
        az group create --name $RESOURCE_GROUP --location "$LOCATION"
        print_status "Resource group created successfully"
    fi
}

# Create Storage Account
create_storage_account() {
    print_header "Creating Storage Account"
    
    print_status "Creating storage account: $STORAGE_ACCOUNT"
    az storage account create \
        --name $STORAGE_ACCOUNT \
        --resource-group $RESOURCE_GROUP \
        --location "$LOCATION" \
        --sku Standard_LRS \
        --kind StorageV2
    
    print_status "Getting storage connection string"
    STORAGE_CONNECTION=$(az storage account show-connection-string \
        --name $STORAGE_ACCOUNT \
        --resource-group $RESOURCE_GROUP \
        --query connectionString --output tsv)
    
    print_status "Creating backup container"
    az storage container create \
        --name hr-backups \
        --connection-string "$STORAGE_CONNECTION"
    
    print_status "Storage account created successfully"
}

# Create Container Registry
create_container_registry() {
    print_header "Creating Container Registry"
    
    print_status "Creating ACR: $ACR_NAME"
    az acr create \
        --resource-group $RESOURCE_GROUP \
        --name $ACR_NAME \
        --sku Basic \
        --admin-enabled true
    
    print_status "Getting ACR credentials"
    ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query username --output tsv)
    ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query passwords[0].value --output tsv)
    
    print_status "Container registry created successfully"
}

# Create OpenAI Service
create_openai_service() {
    print_header "Creating Azure OpenAI Service"
    
    print_status "Creating OpenAI service: $OPENAI_NAME"
    az cognitiveservices account create \
        --name $OPENAI_NAME \
        --resource-group $RESOURCE_GROUP \
        --location "$LOCATION" \
        --kind OpenAI \
        --sku S0 \
        --yes
    
    print_status "Getting OpenAI endpoint and key"
    OPENAI_ENDPOINT=$(az cognitiveservices account show \
        --name $OPENAI_NAME \
        --resource-group $RESOURCE_GROUP \
        --query properties.endpoint --output tsv)
    
    OPENAI_KEY=$(az cognitiveservices account keys list \
        --name $OPENAI_NAME \
        --resource-group $RESOURCE_GROUP \
        --query key1 --output tsv)
    
    print_status "Deploying GPT-4o-mini model"
    az cognitiveservices account deployment create \
        --name $OPENAI_NAME \
        --resource-group $RESOURCE_GROUP \
        --deployment-name gpt-4o-mini \
        --model-name gpt-4o-mini \
        --model-version "2024-07-18" \
        --model-format OpenAI \
        --scale-settings-scale-type "Standard"
    
    print_status "OpenAI service created successfully"
}

# Create App Service
create_app_service() {
    print_header "Creating App Service"
    
    print_status "Creating App Service Plan: $APP_SERVICE_PLAN"
    az appservice plan create \
        --name $APP_SERVICE_PLAN \
        --resource-group $RESOURCE_GROUP \
        --sku B1 \
        --is-linux
    
    print_status "Creating Web App: $WEB_APP_NAME"
    az webapp create \
        --resource-group $RESOURCE_GROUP \
        --plan $APP_SERVICE_PLAN \
        --name $WEB_APP_NAME \
        --deployment-container-image-name "nginx:latest"  # Placeholder image
    
    print_status "Configuring Web App for containers"
    az webapp config container set \
        --name $WEB_APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --docker-custom-image-name $ACR_NAME.azurecr.io/hr-candidate-app:latest \
        --docker-registry-server-url https://$ACR_NAME.azurecr.io \
        --docker-registry-server-user $ACR_USERNAME \
        --docker-registry-server-password $ACR_PASSWORD
    
    print_status "App Service created successfully"
}

# Configure App Settings
configure_app_settings() {
    print_header "Configuring Application Settings"
    
    print_status "Setting environment variables"
    az webapp config appsettings set \
        --resource-group $RESOURCE_GROUP \
        --name $WEB_APP_NAME \
        --settings \
        AZURE_STORAGE_CONNECTION_STRING="$STORAGE_CONNECTION" \
        AZURE_OPENAI_ENDPOINT="$OPENAI_ENDPOINT" \
        AZURE_OPENAI_API_KEY="$OPENAI_KEY" \
        AZURE_OPENAI_API_VERSION="2024-02-15-preview" \
        AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4o-mini" \
        BACKUP_CONTAINER="hr-backups" \
        AUTO_BACKUP_ENABLED="True" \
        BACKUP_RETENTION_DAYS="30" \
        MAX_FILE_SIZE_MB="10" \
        MAX_SEARCH_RESULTS="100" \
        LOG_LEVEL="INFO" \
        DB_PATH="/home/data/hr_candidates.db"
    
    print_status "Application settings configured successfully"
}

# Create Service Principal for GitHub Actions
create_service_principal() {
    print_header "Creating Service Principal for GitHub Actions"
    
    print_status "Creating service principal"
    SUBSCRIPTION_ID=$(az account show --query id --output tsv)
    
    SERVICE_PRINCIPAL=$(az ad sp create-for-rbac \
        --name "hr-candidate-tool-deploy-${UNIQUE_SUFFIX}" \
        --role contributor \
        --scopes /subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP \
        --sdk-auth)
    
    print_status "Service principal created successfully"
}

# Generate environment file
generate_env_file() {
    print_header "Generating Environment Configuration"
    
    cat > .env.production << EOF
# Azure Storage Configuration
AZURE_STORAGE_CONNECTION_STRING=$STORAGE_CONNECTION

# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=$OPENAI_ENDPOINT
AZURE_OPENAI_API_KEY=$OPENAI_KEY
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini

# Database Configuration
DB_PATH=/home/data/hr_candidates.db

# Backup Configuration
BACKUP_CONTAINER=hr-backups
AUTO_BACKUP_ENABLED=True
BACKUP_RETENTION_DAYS=30

# Application Configuration
MAX_FILE_SIZE_MB=10
MAX_SEARCH_RESULTS=100
LOG_LEVEL=INFO
DEBUG=False
EOF

    print_status "Environment file created: .env.production"
}

# Print summary
print_summary() {
    print_header "Deployment Summary"
    
    echo "✅ Azure resources created successfully!"
    echo ""
    echo "📊 Resource Information:"
    echo "  Resource Group: $RESOURCE_GROUP"
    echo "  Storage Account: $STORAGE_ACCOUNT"
    echo "  Container Registry: $ACR_NAME"
    echo "  OpenAI Service: $OPENAI_NAME"
    echo "  Web App: $WEB_APP_NAME"
    echo "  Web App URL: https://$WEB_APP_NAME.azurewebsites.net"
    echo ""
    echo "🔑 GitHub Secrets to Add:"
    echo "  AZURE_CREDENTIALS: (see below)"
    echo "  ACR_USERNAME: $ACR_USERNAME"
    echo "  ACR_PASSWORD: $ACR_PASSWORD"
    echo "  AZURE_RESOURCE_GROUP: $RESOURCE_GROUP"
    echo "  AZURE_STORAGE_CONNECTION_STRING: (see .env.production)"
    echo "  AZURE_OPENAI_ENDPOINT: $OPENAI_ENDPOINT"
    echo "  AZURE_OPENAI_API_KEY: (see .env.production)"
    echo "  AZURE_OPENAI_API_VERSION: 2024-02-15-preview"
    echo "  AZURE_OPENAI_DEPLOYMENT_NAME: gpt-4o-mini"
    echo ""
    echo "🔧 Service Principal JSON (for AZURE_CREDENTIALS secret):"
    echo "$SERVICE_PRINCIPAL"
    echo ""
    echo "📝 Next Steps:"
    echo "  1. Add the above secrets to your GitHub repository"
    echo "  2. Update .github/workflows/deploy.yml with resource names:"
    echo "     - AZURE_WEBAPP_NAME: $WEB_APP_NAME"
    echo "     - REGISTRY_NAME: $ACR_NAME"
    echo "  3. Push your code to trigger deployment"
    echo "  4. Monitor deployment in GitHub Actions"
    echo ""
    echo "💰 Estimated Monthly Cost: ~\$25-40 USD"
    echo "📧 Keep this information safe for future reference!"
}

# Cleanup function for failed deployments
cleanup_on_error() {
    print_error "Deployment failed. Cleaning up resources..."
    read -p "Delete created resources? (y/N): " CLEANUP
    if [[ $CLEANUP =~ ^[Yy]$ ]]; then
        print_status "Deleting resource group: $RESOURCE_GROUP"
        az group delete --name $RESOURCE_GROUP --yes --no-wait
        print_status "Cleanup initiated"
    fi
}

# Trap errors and cleanup
trap cleanup_on_error ERR

# Main execution
main() {
    print_header "HR Candidate Management Tool - Azure Deployment"
    echo "This script will create all required Azure resources for the application."
    echo ""
    
    check_prerequisites
    get_configuration
    create_resource_group
    create_storage_account
    create_container_registry
    create_openai_service
    create_app_service
    configure_app_settings
    create_service_principal
    generate_env_file
    print_summary
    
    print_status "Deployment completed successfully! 🎉"
}

# Run main function
main "$@"
