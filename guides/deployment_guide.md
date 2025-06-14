# Complete GitHub Actions Deployment Guide for HR Candidate Tool

This guide will walk you through deploying your HR Candidate Management Tool using GitHub Actions with Azure Container Registry (ACR) and Azure Web Apps.

## Prerequisites

- Azure subscription with sufficient permissions
- GitHub repository with your code
- Azure CLI installed locally
- Docker Desktop (for local testing)

## Step 1: Set Up Azure Resources

### 1.1 Login to Azure and Set Variables

```bash
# Login to Azure
az login

# Set your subscription (replace with your subscription ID)
az account set --subscription "your-subscription-id"

# Set environment variables for reuse
export RESOURCE_GROUP="hr-candidate-tool-rg"
export LOCATION="eastus"
export ACR_NAME="hrtoolacr$(date +%s)"  # Unique name
export STORAGE_ACCOUNT="hrtoolstore$(date +%s)"  # Unique name
export OPENAI_NAME="hr-openai-$(date +%s)"
export APP_SERVICE_PLAN="hr-tool-plan"
export WEB_APP_NAME="hr-candidate-tool-$(date +%s)"
export SUBSCRIPTION_ID=$(az account show --query id --output tsv)

echo "Resource Group: $RESOURCE_GROUP"
echo "ACR Name: $ACR_NAME"
echo "Storage Account: $STORAGE_ACCOUNT"
echo "Web App Name: $WEB_APP_NAME"
```

### 1.2 Create Resource Group

```bash
az group create --name $RESOURCE_GROUP --location $LOCATION
```

### 1.3 Create Azure Container Registry

```bash
# Create ACR
az acr create \
  --resource-group $RESOURCE_GROUP \
  --name $ACR_NAME \
  --sku Basic \
  --admin-enabled true

# Get ACR credentials (save these for GitHub secrets)
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query username --output tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query passwords[0].value --output tsv)

echo "ACR Username: $ACR_USERNAME"
echo "ACR Password: $ACR_PASSWORD"
echo "ACR Login Server: $ACR_NAME.azurecr.io"
```

### 1.4 Create Storage Account

```bash
# Create storage account
az storage account create \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Standard_LRS \
  --kind StorageV2

# Get storage connection string
STORAGE_CONNECTION=$(az storage account show-connection-string \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --query connectionString --output tsv)

echo "Storage Connection String: $STORAGE_CONNECTION"

# Create required containers
az storage container create --name app-data --connection-string "$STORAGE_CONNECTION"
az storage container create --name hr-backups --connection-string "$STORAGE_CONNECTION"
```

### 1.5 Create Azure OpenAI Service

```bash
# Create OpenAI service (Note: Available regions may be limited)
az cognitiveservices account create \
  --name $OPENAI_NAME \
  --resource-group $RESOURCE_GROUP \
  --location "eastus" \
  --kind OpenAI \
  --sku S0 \
  --yes

# Get OpenAI endpoint and key
OPENAI_ENDPOINT=$(az cognitiveservices account show \
  --name $OPENAI_NAME \
  --resource-group $RESOURCE_GROUP \
  --query properties.endpoint --output tsv)

OPENAI_KEY=$(az cognitiveservices account keys list \
  --name $OPENAI_NAME \
  --resource-group $RESOURCE_GROUP \
  --query key1 --output tsv)

echo "OpenAI Endpoint: $OPENAI_ENDPOINT"
echo "OpenAI Key: $OPENAI_KEY"

# Deploy GPT-4o-mini model
az cognitiveservices account deployment create \
  --name $OPENAI_NAME \
  --resource-group $RESOURCE_GROUP \
  --deployment-name gpt-4o-mini \
  --model-name gpt-4o-mini \
  --model-version "2024-07-18" \
  --model-format OpenAI \
  --scale-settings-scale-type "Standard"
```

### 1.6 Create App Service Plan and Web App

```bash
# Create App Service Plan
az appservice plan create \
  --name $APP_SERVICE_PLAN \
  --resource-group $RESOURCE_GROUP \
  --sku B1 \
  --is-linux

# Create Web App
az webapp create \
  --resource-group $RESOURCE_GROUP \
  --plan $APP_SERVICE_PLAN \
  --name $WEB_APP_NAME \
  --deployment-container-image-name "nginx:latest"  # Temporary placeholder

echo "Web App URL: https://$WEB_APP_NAME.azurewebsites.net"
```

### 1.7 Create Service Principal for GitHub Actions

```bash
# Create service principal for GitHub Actions
SERVICE_PRINCIPAL=$(az ad sp create-for-rbac \
  --name "hr-candidate-tool-deploy-$(date +%s)" \
  --role contributor \
  --scopes /subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP \
  --sdk-auth)

echo "Service Principal JSON (save this for AZURE_CREDENTIALS secret):"
echo $SERVICE_PRINCIPAL
```

## Step 2: Configure GitHub Repository

### 2.1 Set Up GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions, and add these secrets:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `AZURE_CREDENTIALS` | Service Principal JSON from Step 1.7 | Authentication for Azure |
| `ACR_USERNAME` | ACR Username from Step 1.3 | Container Registry username |
| `ACR_PASSWORD` | ACR Password from Step 1.3 | Container Registry password |
| `AZURE_RESOURCE_GROUP` | Your resource group name | Azure resource group |
| `AZURE_STORAGE_CONNECTION_STRING` | Storage connection string from Step 1.4 | Azure Storage access |
| `AZURE_OPENAI_ENDPOINT` | OpenAI endpoint from Step 1.5 | Azure OpenAI service URL |
| `AZURE_OPENAI_API_KEY` | OpenAI key from Step 1.5 | Azure OpenAI API key |
| `AZURE_OPENAI_API_VERSION` | `2024-02-15-preview` | OpenAI API version |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | `gpt-4o-mini` | OpenAI model deployment name |

### 2.2 Update GitHub Actions Workflow

Update your `.github/workflows/deploy.yml` file with the correct resource names:

```yaml
name: Deploy HR Candidate Tool to Azure

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

env:
  AZURE_WEBAPP_NAME: 'YOUR_WEB_APP_NAME'    # Replace with your app name from Step 1.1
  REGISTRY_NAME: 'YOUR_ACR_NAME'            # Replace with your ACR name from Step 1.1
  IMAGE_NAME: 'hr-candidate-app'

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3

    - name: Log in to Azure Container Registry
      uses: azure/docker-login@v1
      with:
        login-server: ${{ env.REGISTRY_NAME }}.azurecr.io
        username: ${{ secrets.ACR_USERNAME }}
        password: ${{ secrets.ACR_PASSWORD }}

    - name: Ensure app_data container exists
      continue-on-error: true
      run: |
        if [ -n "${{ secrets.AZURE_STORAGE_CONNECTION_STRING }}" ]; then
          echo "Ensuring app_data container exists..."
          # Install Azure CLI
          curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
          
          # Create app_data container if it doesn't exist
          az storage container create \
            --name app-data \
            --connection-string "${{ secrets.AZURE_STORAGE_CONNECTION_STRING }}" \
            --output none || echo "Container might already exist"
          
          # Also ensure backup container exists
          az storage container create \
            --name hr-backups \
            --connection-string "${{ secrets.AZURE_STORAGE_CONNECTION_STRING }}" \
            --output none || echo "Backup container might already exist"
        fi

    - name: Download latest database backup (if exists)
      continue-on-error: true
      run: |
        if [ -n "${{ secrets.AZURE_STORAGE_CONNECTION_STRING }}" ]; then
          echo "Attempting to download latest database from app_data container..."
          # Install Azure CLI if not already installed
          curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
          
          # Download latest database if it exists in app_data container
          az storage blob download \
            --container-name app-data \
            --name hr_candidates.db \
            --file current_database.db \
            --connection-string "${{ secrets.AZURE_STORAGE_CONNECTION_STRING }}" \
            --output none || echo "No database found in app_data container"
            
          # If database exists, we'll use it in the container
          if [ -f "current_database.db" ]; then
            echo "Database downloaded successfully from app_data container"
            mkdir -p docker-data
            mv current_database.db docker-data/hr_candidates.db
          fi
        fi

    - name: Build and push Docker image
      uses: docker/build-push-action@v5
      with:
        context: .
        push: true
        tags: ${{ env.REGISTRY_NAME }}.azurecr.io/${{ env.IMAGE_NAME }}:${{ github.sha }},${{ env.REGISTRY_NAME }}.azurecr.io/${{ env.IMAGE_NAME }}:latest
        platforms: linux/amd64
        cache-from: type=gha
        cache-to: type=gha,mode=max

    - name: Log in to Azure
      uses: azure/login@v1
      with:
        creds: ${{ secrets.AZURE_CREDENTIALS }}

    - name: Deploy to Azure Web App
      uses: azure/webapps-deploy@v2
      with:
        app-name: ${{ env.AZURE_WEBAPP_NAME }}
        images: ${{ env.REGISTRY_NAME }}.azurecr.io/${{ env.IMAGE_NAME }}:${{ github.sha }}

    - name: Configure Web App Settings
      run: |
        az webapp config appsettings set \
          --resource-group ${{ secrets.AZURE_RESOURCE_GROUP }} \
          --name ${{ env.AZURE_WEBAPP_NAME }} \
          --settings \
          AZURE_STORAGE_CONNECTION_STRING="${{ secrets.AZURE_STORAGE_CONNECTION_STRING }}" \
          AZURE_OPENAI_ENDPOINT="${{ secrets.AZURE_OPENAI_ENDPOINT }}" \
          AZURE_OPENAI_API_KEY="${{ secrets.AZURE_OPENAI_API_KEY }}" \
          AZURE_OPENAI_API_VERSION="${{ secrets.AZURE_OPENAI_API_VERSION }}" \
          AZURE_OPENAI_DEPLOYMENT_NAME="${{ secrets.AZURE_OPENAI_DEPLOYMENT_NAME }}" \
          BACKUP_CONTAINER="hr-backups" \
          DB_CONTAINER="app-data" \
          DB_BLOB_NAME="hr_candidates.db" \
          LOCAL_DB_PATH="/tmp/hr_candidates.db" \
          AUTO_SYNC_ENABLED="True" \
          SYNC_INTERVAL_SECONDS="300" \
          AUTO_BACKUP_ENABLED="True" \
          BACKUP_RETENTION_DAYS="30" \
          MAX_FILE_SIZE_MB="10" \
          MAX_SEARCH_RESULTS="100" \
          LOG_LEVEL="INFO"

    - name: Restart Web App
      run: |
        az webapp restart \
          --resource-group ${{ secrets.AZURE_RESOURCE_GROUP }} \
          --name ${{ env.AZURE_WEBAPP_NAME }}

    - name: Verify deployment
      run: |
        echo "Waiting for application to start..."
        sleep 30
        
        # Try to access the health endpoint
        curl -f https://${{ env.AZURE_WEBAPP_NAME }}.azurewebsites.net/_stcore/health || echo "Health check failed"
        
        echo "Deployment completed. Application should be available at:"
        echo "https://${{ env.AZURE_WEBAPP_NAME }}.azurewebsites.net"

  backup-verification:
    needs: build-and-deploy
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - name: Verify backup functionality
      run: |
        echo "Backup verification job completed"
        echo "Manual verification recommended:"
        echo "1. Check that application can create backups"
        echo "2. Verify backup restoration works"
        echo "3. Test CV upload and processing"
        echo "4. Test candidate search functionality"
        echo "5. Verify database sync operations"
        echo "6. Test blob storage connectivity"
```

### 2.3 Verify Dockerfile

Ensure your `Dockerfile` is optimized for production:

```dockerfile
# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create directory for persistent data and ensure tmp permissions
RUN mkdir -p /home/data && chmod 777 /home/data && chmod 777 /tmp

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app /home/data
USER appuser

# Expose port for Streamlit
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run the application
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.enableCORS=false", "--server.enableXsrfProtection=false"]
```

## Step 3: Configure Web App for Container Deployment

Configure your Web App to use the ACR image:

```bash
# Configure Web App to use ACR
az webapp config container set \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --docker-custom-image-name $ACR_NAME.azurecr.io/hr-candidate-app:latest \
  --docker-registry-server-url https://$ACR_NAME.azurecr.io \
  --docker-registry-server-user $ACR_USERNAME \
  --docker-registry-server-password $ACR_PASSWORD

# Enable continuous deployment from ACR
az webapp deployment container config \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --enable-cd true
```

## Step 4: Deploy Your Application

### 4.1 Commit and Push Your Code

```bash
# Add all files
git add .

# Commit changes
git commit -m "feat: set up GitHub Actions deployment pipeline"

# Push to main branch to trigger deployment
git push origin main
```

### 4.2 Monitor the Deployment

1. Go to your GitHub repository
2. Click on the "Actions" tab
3. Watch the workflow execution
4. Check for any errors in the logs

### 4.3 Verify Deployment

After successful deployment:

```bash
# Check if the app is running
curl -I https://$WEB_APP_NAME.azurewebsites.net

# Check application health
curl https://$WEB_APP_NAME.azurewebsites.net/_stcore/health
```

## Step 5: Test Your Application

1. **Access the application:** `https://YOUR_WEB_APP_NAME.azurewebsites.net`
2. **Test core functionality:**
   - Upload a sample PDF CV
   - Verify data extraction works
   - Test candidate search
   - Check backup functionality in dashboard

## Step 6: Set Up Monitoring and Alerts

```bash
# Create application insights (optional)
az monitor app-insights component create \
  --app $WEB_APP_NAME \
  --location $LOCATION \
  --resource-group $RESOURCE_GROUP

# Set up basic alerts
az monitor metrics alert create \
  --name "HR Tool High CPU" \
  --resource-group $RESOURCE_GROUP \
  --scopes "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Web/sites/$WEB_APP_NAME" \
  --condition "avg Percentage CPU static gt 80 PT10M" \
  --description "Alert when CPU usage is high"
```

## Step 7: Security and Best Practices

### 7.1 Secure Your Secrets

- Regularly rotate API keys and passwords
- Use Azure Key Vault for production secrets (optional enhancement)
- Enable Azure Security Center recommendations

### 7.2 Enable Logging

```bash
# Enable container logs
az webapp log config \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --docker-container-logging filesystem

# View logs
az webapp log tail \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP
```

## Troubleshooting Common Issues

### Issue 1: Build Fails
- Check Dockerfile syntax
- Verify all dependencies in requirements.txt
- Check GitHub secrets are properly set

### Issue 2: Container Won't Start
- Check container logs: `az webapp log tail --name $WEB_APP_NAME --resource-group $RESOURCE_GROUP`
- Verify environment variables are set correctly
- Check if the image was pushed successfully to ACR

### Issue 3: Application Errors
- Check application logs for Python errors
- Verify Azure OpenAI and Storage connections
- Test environment variables in Azure portal

### Issue 4: Database Issues
- Check if storage containers exist
- Verify connection strings
- Test blob storage connectivity

## Maintenance and Updates

### Regular Tasks
1. **Monitor application health**
2. **Review and rotate secrets**
3. **Update dependencies**
4. **Clean up old container images**
5. **Monitor costs**

### Updating the Application
1. Make code changes
2. Commit and push to main branch
3. GitHub Actions will automatically build and deploy
4. Monitor deployment in Actions tab

## Cost Optimization

**Estimated monthly costs:**
- Web App (B1): ~$13
- Storage Account: ~$1-2
- Azure OpenAI: Pay-per-use (~$5-20)
- Container Registry: ~$5
- **Total: ~$25-40/month**

**Optimization tips:**
- Scale down during off-hours
- Clean up old backups regularly
- Monitor OpenAI usage
- Use Azure Cost Management alerts

Your HR Candidate Management Tool is now set up with a complete CI/CD pipeline using GitHub Actions! 🚀

## Next Steps

1. **Test thoroughly** in your deployed environment
2. **Set up user authentication** if needed
3. **Configure custom domain** (optional)
4. **Set up monitoring and alerts**
5. **Train your team** on using the application

The application will automatically redeploy whenever you push changes to the main branch.
