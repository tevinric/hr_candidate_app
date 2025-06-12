# HR Candidate Management Tool - Complete Setup Guide

This guide will walk you through setting up the HR Candidate Management Tool from scratch, including all Azure resources and deployment.

## Prerequisites

- Azure subscription
- GitHub account
- Basic knowledge of Azure CLI and Docker

## Step 1: Set Up Azure Resources

### 1.1 Install Azure CLI
```bash
# On Windows (using PowerShell)
Invoke-WebRequest -Uri https://aka.ms/installazurecliwindows -OutFile .\AzureCLI.msi
Start-Process msiexec.exe -Wait -ArgumentList '/I AzureCLI.msi /quiet'

# On macOS
brew install azure-cli

# On Linux
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
```

### 1.2 Login to Azure
```bash
az login
az account set --subscription "Your-Subscription-Name"
```

### 1.3 Create Resource Group
```bash
# Replace with your preferred location
RESOURCE_GROUP="hr-candidate-tool-rg"
LOCATION="East US"

az group create --name $RESOURCE_GROUP --location "$LOCATION"
```

### 1.4 Create Azure Container Registry (ACR)
```bash
ACR_NAME="hrtools$(date +%s)"  # Unique name
az acr create --resource-group $RESOURCE_GROUP --name $ACR_NAME --sku Basic --admin-enabled true

# Get ACR credentials
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query username --output tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query passwords[0].value --output tsv)

echo "ACR Username: $ACR_USERNAME"
echo "ACR Password: $ACR_PASSWORD"
```

### 1.5 Create Storage Account for Backups
```bash
STORAGE_ACCOUNT="hrcandidatestore$(date +%s)"
az storage account create \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --location "$LOCATION" \
  --sku Standard_LRS

# Get storage connection string
STORAGE_CONNECTION=$(az storage account show-connection-string \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --query connectionString --output tsv)

echo "Storage Connection String: $STORAGE_CONNECTION"

# Create backup container
az storage container create \
  --name hr-backups \
  --connection-string "$STORAGE_CONNECTION"
```

### 1.6 Create Azure OpenAI Service
```bash
OPENAI_NAME="hr-openai-$(date +%s)"
az cognitiveservices account create \
  --name $OPENAI_NAME \
  --resource-group $RESOURCE_GROUP \
  --location "East US" \
  --kind OpenAI \
  --sku S0

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
```

### 1.7 Deploy GPT-4o-mini Model
```bash
# Deploy the model (this might take a few minutes)
az cognitiveservices account deployment create \
  --name $OPENAI_NAME \
  --resource-group $RESOURCE_GROUP \
  --deployment-name gpt-4o-mini \
  --model-name gpt-4o-mini \
  --model-version "2024-07-18" \
  --model-format OpenAI \
  --scale-settings-scale-type "Standard"
```

### 1.8 Create Azure Web App
```bash
APP_SERVICE_PLAN="hr-candidate-plan"
WEB_APP_NAME="hr-candidate-tool-$(date +%s)"

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
  --deployment-container-image-name $ACR_NAME.azurecr.io/hr-candidate-app:latest

echo "Web App Name: $WEB_APP_NAME"
echo "Web App URL: https://$WEB_APP_NAME.azurewebsites.net"
```

### 1.9 Configure Web App to Use ACR
```bash
az webapp config container set \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --docker-custom-image-name $ACR_NAME.azurecr.io/hr-candidate-app:latest \
  --docker-registry-server-url https://$ACR_NAME.azurecr.io \
  --docker-registry-server-user $ACR_USERNAME \
  --docker-registry-server-password $ACR_PASSWORD
```

## Step 2: Set Up GitHub Repository

### 2.1 Create GitHub Repository
1. Go to GitHub and create a new repository named `hr-candidate-tool`
2. Clone the repository locally:
```bash
git clone https://github.com/YOUR_USERNAME/hr-candidate-tool.git
cd hr-candidate-tool
```

### 2.2 Add Application Files
Create the following files in your repository with the provided code:

```
hr-candidate-tool/
├── app.py                    # Main Streamlit application
├── database.py              # Database management
├── cv_processor.py          # CV processing and OpenAI integration
├── config.py               # Configuration management
├── utils.py                # Utility functions
├── requirements.txt        # Python dependencies
├── Dockerfile              # Container configuration
├── .github/
│   └── workflows/
│       └── deploy.yml      # GitHub Actions workflow
├── .gitignore              # Git ignore file
└── README.md               # Project documentation
```

### 2.3 Create .gitignore
```bash
cat > .gitignore << EOF
# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/
pip-log.txt
pip-delete-this-directory.txt
.tox/
.coverage
.coverage.*
.pytest_cache/
nosetests.xml
coverage.xml
*.cover
*.log
.git
.mypy_cache
.pytest_cache
.hypothesis

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Application
*.db
*.sqlite
*.sqlite3
backup_*.db
temp/
logs/
data/

# Environment
.env
.env.local
.env.development
.env.test
.env.production

# Azure
.azure/
EOF
```

## Step 3: Configure GitHub Secrets

### 3.1 Create Service Principal for GitHub Actions
```bash
# Create service principal
SUBSCRIPTION_ID=$(az account show --query id --output tsv)
SERVICE_PRINCIPAL=$(az ad sp create-for-rbac \
  --name "hr-candidate-tool-deploy" \
  --role contributor \
  --scopes /subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP \
  --sdk-auth)

echo "Service Principal JSON (save this for GitHub secrets):"
echo $SERVICE_PRINCIPAL
```

### 3.2 Add GitHub Secrets
In your GitHub repository, go to Settings → Secrets and variables → Actions, and add:

| Secret Name | Value |
|-------------|-------|
| `AZURE_CREDENTIALS` | The JSON output from service principal creation |
| `ACR_USERNAME` | ACR username from step 1.4 |
| `ACR_PASSWORD` | ACR password from step 1.4 |
| `AZURE_RESOURCE_GROUP` | Your resource group name |
| `AZURE_STORAGE_CONNECTION_STRING` | Storage connection string from step 1.5 |
| `AZURE_OPENAI_ENDPOINT` | OpenAI endpoint from step 1.6 |
| `AZURE_OPENAI_API_KEY` | OpenAI key from step 1.6 |
| `AZURE_OPENAI_API_VERSION` | `2024-02-15-preview` |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | `gpt-4o-mini` |

### 3.3 Update Deployment Configuration
Edit the `.github/workflows/deploy.yml` file and update these values:
- `AZURE_WEBAPP_NAME`: Your web app name from step 1.8
- `REGISTRY_NAME`: Your ACR name from step 1.4

## Step 4: Deploy the Application

### 4.1 Commit and Push Code
```bash
git add .
git commit -m "Initial commit: HR Candidate Management Tool"
git push origin main
```

### 4.2 Monitor Deployment
1. Go to your GitHub repository
2. Click on the "Actions" tab
3. Watch the deployment process
4. Check for any errors and resolve them

### 4.3 Verify Deployment
After successful deployment:
1. Visit your web app URL: `https://YOUR_WEB_APP_NAME.azurewebsites.net`
2. Test the application functionality:
   - Upload a sample PDF CV
   - Check if data extraction works
   - Test candidate search
   - Verify backup functionality

## Step 5: Database Backup Configuration

### 5.1 Manual Backup Test
```bash
# Test backup creation through the application dashboard
# Or create a manual backup using Azure CLI

# List existing backups
az storage blob list \
  --container-name hr-backups \
  --connection-string "$STORAGE_CONNECTION" \
  --output table
```

### 5.2 Set Up Backup Monitoring
```bash
# Create a simple monitoring script (optional)
cat > backup_monitor.sh << 'EOF'
#!/bin/bash
# Check if backup was created today
STORAGE_CONNECTION="YOUR_CONNECTION_STRING"
TODAY=$(date +%Y%m%d)

BACKUP_EXISTS=$(az storage blob list \
  --container-name hr-backups \
  --connection-string "$STORAGE_CONNECTION" \
  --query "[?contains(name, '$TODAY')]" \
  --output tsv)

if [ -z "$BACKUP_EXISTS" ]; then
  echo "No backup found for today: $TODAY"
  # Send alert (email, Teams, etc.)
else
  echo "Backup found for today: $TODAY"
fi
EOF

chmod +x backup_monitor.sh
```

## Step 6: Application Configuration

### 6.1 Configure Web App Settings
```bash
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
```

### 6.2 Enable Continuous Deployment
```bash
# Configure continuous deployment
az webapp deployment source config \
  --resource-group $RESOURCE_GROUP \
  --name $WEB_APP_NAME \
  --repo-url https://github.com/YOUR_USERNAME/hr-candidate-tool \
  --branch main \
  --manual-integration
```

## Step 7: Testing and Validation

### 7.1 Functional Testing
1. **CV Upload Test:**
   - Upload a sample PDF CV
   - Verify text extraction
   - Check AI data extraction accuracy
   - Validate form pre-population

2. **Database Operations:**
   - Save candidate data
   - Edit and update records
   - Test search functionality

3. **Backup Operations:**
   - Create manual backup
   - Verify backup in blob storage
   - Test restore functionality

### 7.2 Performance Testing
```bash
# Test application response time
curl -w "@curl-format.txt" -o /dev/null -s "https://$WEB_APP_NAME.azurewebsites.net"

# Create curl-format.txt
cat > curl-format.txt << 'EOF'
     time_namelookup:  %{time_namelookup}\n
        time_connect:  %{time_connect}\n
     time_appconnect:  %{time_appconnect}\n
    time_pretransfer:  %{time_pretransfer}\n
       time_redirect:  %{time_redirect}\n
  time_starttransfer:  %{time_starttransfer}\n
                     ----------\n
          time_total:  %{time_total}\n
EOF
```

## Step 8: Maintenance and Monitoring

### 8.1 Set Up Alerts
```bash
# Create alert rule for application failures
az monitor metrics alert create \
  --name "HR Tool App Failures" \
  --resource-group $RESOURCE_GROUP \
  --scopes "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Web/sites/$WEB_APP_NAME" \
  --condition "count static gt 5 PT5M" \
  --description "Alert when app has more than 5 failures in 5 minutes"
```

### 8.2 Monitor Costs
```bash
# Check resource costs
az consumption usage list \
  --start-date $(date -d "1 month ago" +%Y-%m-%d) \
  --end-date $(date +%Y-%m-%d) \
  --output table
```

### 8.3 Regular Maintenance Tasks

**Weekly:**
- Check application logs
- Verify backup creation
- Review storage usage
- Test core functionality

**Monthly:**
- Clean up old backups
- Review and optimize costs
- Update dependencies if needed
- Security review

**Quarterly:**
- Review and update documentation
- Performance optimization
- User feedback review
- Disaster recovery testing

## Troubleshooting

### Common Issues

1. **Deployment Fails:**
   - Check GitHub Actions logs
   - Verify all secrets are set correctly
   - Ensure Azure resources are properly configured

2. **Application Won't Start:**
   - Check Web App logs: `az webapp log tail --name $WEB_APP_NAME --resource-group $RESOURCE_GROUP`
   - Verify environment variables
   - Check container image is accessible

3. **OpenAI API Errors:**
   - Verify API key and endpoint
   - Check model deployment status
   - Review quota limits

4. **Database Issues:**
   - Check write permissions to `/home/data`
   - Verify backup storage connection
   - Review database file corruption

5. **Backup Failures:**
   - Check storage account access
   - Verify container exists
   - Review connection string format

### Log Analysis
```bash
# Download application logs
az webapp log download --resource-group $RESOURCE_GROUP --name $WEB_APP_NAME

# Stream live logs
az webapp log tail --resource-group $RESOURCE_GROUP --name $WEB_APP_NAME
```

## Security Considerations

1. **API Keys:** Stored securely in Azure Key Vault or App Settings
2. **Database:** Encrypted at rest and in transit
3. **File Uploads:** Validated and size-limited
4. **Access Control:** Consider implementing authentication
5. **Network Security:** Use Azure Private Endpoints for production

## Cost Optimization

**Current estimated monthly costs:**
- Web App (B1): ~$13
- Storage Account: ~$1-2
- Azure OpenAI: Pay-per-use (~$5-20 depending on usage)
- Container Registry: ~$5
- **Total: ~$25-40/month**

**Optimization tips:**
- Use serverless Azure Functions for processing (if low usage)
- Enable auto-scaling down during off-hours
- Clean up old backups regularly
- Monitor and set spending alerts

## Support and Maintenance

For ongoing support:
1. Monitor application health through Azure Portal
2. Set up automated alerts for failures
3. Regular backup verification
4. Keep dependencies updated
5. Review security best practices

## Next Steps

After successful deployment:
1. Train users on the application
2. Set up user authentication if needed
3. Consider implementing additional features
4. Set up monitoring and alerting
5. Plan for scaling based on usage

Your HR Candidate Management Tool is now fully deployed and ready to use!
