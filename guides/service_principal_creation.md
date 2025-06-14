# Complete Service Principal Creation Guide

This guide covers three methods to create a service principal for GitHub Actions deployment: Azure Portal, Azure CLI, and Terraform.

## What is a Service Principal?

A service principal is an identity created for applications, hosted services, and automated tools to access Azure resources. For GitHub Actions, it provides the authentication credentials needed to deploy your application to Azure.

## Prerequisites

- Azure subscription with sufficient permissions
- Resource group already created (from previous deployment guide)
- For Terraform: Terraform installed locally

---

## Method 1: Azure Portal (GUI)

### Step 1: Navigate to Azure Active Directory

1. **Login to Azure Portal**: Go to https://portal.azure.com
2. **Search for "Azure Active Directory"** in the top search bar. This may also be called EntraID
3. **Click on "Azure Active Directory"** from the results

### Step 2: Create App Registration

1. **In the left sidebar, click "App registrations"**
2. **Click "+ New registration"** at the top
3. **Fill in the details:**
   - **Name**: `hr-candidate-tool-github-actions`
   - **Supported account types**: Select "Accounts in this organizational directory only"
   - **Redirect URI**: Leave blank (not needed for service principals)
4. **Click "Register"**

### Step 3: Note the Application Details

After registration, you'll see the overview page. **Copy and save these values:**
- **Application (client) ID**: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
- **Directory (tenant) ID**: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

### Step 4: Create Client Secret

1. **In the left sidebar, click "Certificates & secrets"**
2. **Click "Client secrets" tab**
3. **Click "+ New client secret"**
4. **Fill in the details:**
   - **Description**: `GitHub Actions Deployment`
   - **Expires**: Select "24 months" (or your preferred duration)
5. **Click "Add"**
6. **⚠️ IMPORTANT**: Copy the **Value** immediately - it won't be shown again!

### Step 5: Assign Permissions to Resource Group

1. **Navigate to your Resource Group:**
   - Search for "Resource groups" in the top search bar
   - Click on your resource group (e.g., `hr-candidate-tool-rg`)

2. **Go to Access Control (IAM):**
   - Click "Access control (IAM)" in the left sidebar
   - Click "+ Add" → "Add role assignment"

3. **Configure Role Assignment:**
   - **Role**: Select "Contributor"
   - **Assign access to**: Select "User, group, or service principal"
   - **Select**: Search for your app name `hr-candidate-tool-github-actions`
   - Click on it when it appears
   - Click "Save"

### Step 6: Create JSON for GitHub Actions

Create the JSON format needed for GitHub Actions using the values you copied:

```json
{
  "clientId": "YOUR_APPLICATION_CLIENT_ID",
  "clientSecret": "YOUR_CLIENT_SECRET_VALUE", 
  "subscriptionId": "YOUR_SUBSCRIPTION_ID",
  "tenantId": "YOUR_DIRECTORY_TENANT_ID"
}
```

**To get your Subscription ID:**
1. Search for "Subscriptions" in Azure Portal
2. Click on your subscription
3. Copy the "Subscription ID" from the overview page

---

## Method 2: Azure CLI (Command Line)

### Step 1: Login and Set Variables

```bash
# Login to Azure
az login

# Set variables (replace with your values)
export SUBSCRIPTION_ID=$(az account show --query id --output tsv)
export RESOURCE_GROUP="hr-candidate-tool-rg"
export SP_NAME="hr-candidate-tool-github-actions"

echo "Subscription ID: $SUBSCRIPTION_ID"
echo "Resource Group: $RESOURCE_GROUP"
echo "Service Principal Name: $SP_NAME"
```

### Step 2: Create Service Principal with Resource Group Scope

```bash
# Create service principal with contributor role on resource group
SERVICE_PRINCIPAL=$(az ad sp create-for-rbac \
  --name $SP_NAME \
  --role contributor \
  --scopes /subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP \
  --sdk-auth)

echo "Service Principal JSON:"
echo $SERVICE_PRINCIPAL
```

The output will be in the exact format needed for GitHub Actions:

```json
{
  "clientId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "clientSecret": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "subscriptionId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "tenantId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
}
```

### Step 3: Verify Service Principal Creation

```bash
# List service principals to verify creation
az ad sp list --display-name $SP_NAME --output table

# Check role assignments
az role assignment list --assignee $(echo $SERVICE_PRINCIPAL | jq -r '.clientId') --output table
```

### Step 4: Test Service Principal (Optional)

```bash
# Extract values for testing
CLIENT_ID=$(echo $SERVICE_PRINCIPAL | jq -r '.clientId')
CLIENT_SECRET=$(echo $SERVICE_PRINCIPAL | jq -r '.clientSecret')
TENANT_ID=$(echo $SERVICE_PRINCIPAL | jq -r '.tenantId')

# Test login with service principal
az login --service-principal \
  --username $CLIENT_ID \
  --password $CLIENT_SECRET \
  --tenant $TENANT_ID

# Test access to resource group
az group show --name $RESOURCE_GROUP

# Logout and login back with your account
az logout
az login
```

### Step 5: Additional Permissions (If Needed)

If you need additional permissions beyond the resource group:

```bash
# Add permission to manage container registries across subscription
az role assignment create \
  --assignee $CLIENT_ID \
  --role "AcrPush" \
  --scope /subscriptions/$SUBSCRIPTION_ID

# Add permission to manage web apps across subscription  
az role assignment create \
  --assignee $CLIENT_ID \
  --role "Website Contributor" \
  --scope /subscriptions/$SUBSCRIPTION_ID
```

### Step 6: GitHub Actions Integration

**Add to GitHub Secrets:**

```bash
# The SERVICE_PRINCIPAL variable already contains the JSON format for GitHub Actions
echo "Add this JSON to GitHub secrets as AZURE_CREDENTIALS:"
echo $SERVICE_PRINCIPAL | jq .

# Extract individual values if needed
CLIENT_ID=$(echo $SERVICE_PRINCIPAL | jq -r '.clientId')
CLIENT_SECRET=$(echo $SERVICE_PRINCIPAL | jq -r '.clientSecret')
TENANT_ID=$(echo $SERVICE_PRINCIPAL | jq -r '.tenantId')
SUBSCRIPTION_ID=$(echo $SERVICE_PRINCIPAL | jq -r '.subscriptionId')

echo "Individual values for reference:"
echo "CLIENT_ID: $CLIENT_ID"
echo "TENANT_ID: $TENANT_ID"
echo "SUBSCRIPTION_ID: $SUBSCRIPTION_ID"
```

**Add these GitHub repository secrets:**

1. Go to your GitHub repository → Settings → Secrets and variables → Actions
2. Add the following secrets:

| Secret Name | Value | Command to get value |
|-------------|-------|---------------------|
| `AZURE_CREDENTIALS` | Complete JSON | `echo $SERVICE_PRINCIPAL` |
| `AZURE_SUBSCRIPTION_ID` | Subscription ID | `echo $SERVICE_PRINCIPAL \| jq -r '.subscriptionId'` |
| `AZURE_TENANT_ID` | Tenant ID | `echo $SERVICE_PRINCIPAL \| jq -r '.tenantId'` |

**Test GitHub Actions workflow:**

```bash
# Create a test workflow file
cat > .github/workflows/test-azure-login.yml << 'EOF'
name: Test Azure Service Principal
on: [workflow_dispatch]

jobs:
  test-azure:
    runs-on: ubuntu-latest
    steps:
    - name: Azure Login
      uses: azure/login@v1
      with:
        creds: ${{ secrets.AZURE_CREDENTIALS }}
    
    - name: Test Resource Group Access
      run: |
        az group show --name ${{ env.RESOURCE_GROUP }}
        az resource list --resource-group ${{ env.RESOURCE_GROUP }} --output table
    
    env:
      RESOURCE_GROUP: hr-candidate-tool-rg  # Replace with your RG name
EOF
```

### Step 7: Azure DevOps Integration

**Method 1: Service Connection (Recommended)**

```bash
# Print service connection details
echo "=== Azure DevOps Service Connection Details ==="
echo "Connection Type: Azure Resource Manager"
echo "Authentication: Service principal (manual)"
echo "Subscription ID: $(echo $SERVICE_PRINCIPAL | jq -r '.subscriptionId')"
echo "Service Principal ID: $(echo $SERVICE_PRINCIPAL | jq -r '.clientId')"
echo "Service Principal Key: $(echo $SERVICE_PRINCIPAL | jq -r '.clientSecret')"
echo "Tenant ID: $(echo $SERVICE_PRINCIPAL | jq -r '.tenantId')"
```

**Setup in Azure DevOps:**
1. Go to Project Settings → Service connections
2. Click "New service connection" → "Azure Resource Manager"
3. Choose "Service principal (manual)"
4. Use the values printed above
5. Name it: `hr-candidate-tool-azure`

**Method 2: Variable Groups**

```bash
# Create Azure DevOps pipeline variables
cat > azure-devops-variables.yml << EOF
variables:
  AZURE_CLIENT_ID: $(echo $SERVICE_PRINCIPAL | jq -r '.clientId')
  AZURE_CLIENT_SECRET: $(echo $SERVICE_PRINCIPAL | jq -r '.clientSecret')  # Mark as secret
  AZURE_TENANT_ID: $(echo $SERVICE_PRINCIPAL | jq -r '.tenantId')
  AZURE_SUBSCRIPTION_ID: $(echo $SERVICE_PRINCIPAL | jq -r '.subscriptionId')
  AZURE_RESOURCE_GROUP: $RESOURCE_GROUP
EOF

echo "Variable group values for Azure DevOps:"
cat azure-devops-variables.yml
```

**Test Azure DevOps Pipeline:**

```bash
# Create test pipeline
cat > azure-pipelines-test.yml << 'EOF'
trigger:
- main

pool:
  vmImage: 'ubuntu-latest'

steps:
- task: AzureCLI@2
  displayName: 'Test Service Principal Login'
  inputs:
    azureSubscription: 'hr-candidate-tool-azure'  # Your service connection name
    scriptType: 'bash'
    scriptLocation: 'inlineScript'
    inlineScript: |
      echo "Testing Azure connection..."
      az account show
      az group list --output table
      echo "Testing resource group access..."
      az group show --name $(AZURE_RESOURCE_GROUP)

# Alternative: Direct service principal login
- task: AzureCLI@2
  displayName: 'Direct Service Principal Login'
  inputs:
    scriptType: 'bash'
    scriptLocation: 'inlineScript'
    inlineScript: |
      az login --service-principal \
        --username $(AZURE_CLIENT_ID) \
        --password $(AZURE_CLIENT_SECRET) \
        --tenant $(AZURE_TENANT_ID)
      az account set --subscription $(AZURE_SUBSCRIPTION_ID)
      az account show
  env:
    AZURE_CLIENT_ID: $(AZURE_CLIENT_ID)
    AZURE_CLIENT_SECRET: $(AZURE_CLIENT_SECRET)
    AZURE_TENANT_ID: $(AZURE_TENANT_ID)
    AZURE_SUBSCRIPTION_ID: $(AZURE_SUBSCRIPTION_ID)
EOF
```

**Deploy to Azure DevOps:**

```bash
# If you're using Azure DevOps, commit the pipeline file
git add azure-pipelines-test.yml
git commit -m "Add Azure DevOps test pipeline"
git push origin main
```

---

## Method 3: Terraform

### Step 1: Create Terraform Configuration

Create a file named `service-principal.tf`:

```hcl
# Configure the Azure Provider
terraform {
  required_providers {
    azuread = {
      source  = "hashicorp/azuread"
      version = "~>2.15.0"
    }
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~>3.0"
    }
  }
}

# Configure the Azure Provider features
provider "azurerm" {
  features {}
}

# Get current Azure configuration
data "azurerm_client_config" "current" {}

# Get the resource group
data "azurerm_resource_group" "main" {
  name = var.resource_group_name
}

# Create Azure AD Application
resource "azuread_application" "github_actions" {
  display_name = var.application_name
  description  = "Service Principal for GitHub Actions deployment of HR Candidate Tool"
  
  owners = [data.azurerm_client_config.current.object_id]
}

# Create Service Principal
resource "azuread_service_principal" "github_actions" {
  application_id               = azuread_application.github_actions.application_id
  app_role_assignment_required = false
  owners                       = [data.azurerm_client_config.current.object_id]

  tags = ["github-actions", "hr-candidate-tool", "deployment"]
}

# Create Service Principal Password
resource "azuread_service_principal_password" "github_actions" {
  service_principal_id = azuread_service_principal.github_actions.object_id
  display_name        = "GitHub Actions Secret"
  end_date_relative   = "8760h" # 1 year
}

# Assign Contributor role to Resource Group
resource "azurerm_role_assignment" "contributor" {
  scope                = data.azurerm_resource_group.main.id
  role_definition_name = "Contributor"
  principal_id         = azuread_service_principal.github_actions.object_id
}

# Optional: Assign additional roles if needed
resource "azurerm_role_assignment" "acr_push" {
  count                = var.enable_acr_permissions ? 1 : 0
  scope                = "/subscriptions/${data.azurerm_client_config.current.subscription_id}"
  role_definition_name = "AcrPush"
  principal_id         = azuread_service_principal.github_actions.object_id
}

resource "azurerm_role_assignment" "website_contributor" {
  count                = var.enable_webapp_permissions ? 1 : 0
  scope                = "/subscriptions/${data.azurerm_client_config.current.subscription_id}"
  role_definition_name = "Website Contributor"
  principal_id         = azuread_service_principal.github_actions.object_id
}
```

### Step 2: Create Variables File

Create `variables.tf`:

```hcl
variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
  default     = "hr-candidate-tool-rg"
}

variable "application_name" {
  description = "Name of the Azure AD application"
  type        = string
  default     = "hr-candidate-tool-github-actions"
}

variable "enable_acr_permissions" {
  description = "Enable ACR push permissions"
  type        = bool
  default     = true
}

variable "enable_webapp_permissions" {
  description = "Enable Web App contributor permissions"
  type        = bool
  default     = true
}
```

### Step 3: Create Outputs File

Create `outputs.tf`:

```hcl
# Output for GitHub Actions secret
output "github_actions_secret" {
  description = "JSON credentials for GitHub Actions"
  value = jsonencode({
    clientId       = azuread_application.github_actions.application_id
    clientSecret   = azuread_service_principal_password.github_actions.value
    subscriptionId = data.azurerm_client_config.current.subscription_id
    tenantId       = data.azurerm_client_config.current.tenant_id
  })
  sensitive = true
}

# Individual outputs for reference
output "client_id" {
  description = "Service Principal Client ID"
  value       = azuread_application.github_actions.application_id
}

output "tenant_id" {
  description = "Azure Tenant ID"
  value       = data.azurerm_client_config.current.tenant_id
}

output "subscription_id" {
  description = "Azure Subscription ID"
  value       = data.azurerm_client_config.current.subscription_id
}

output "resource_group_scope" {
  description = "Resource Group scope for role assignment"
  value       = data.azurerm_resource_group.main.id
}
```

### Step 4: Create Terraform Values File (Optional)

Create `terraform.tfvars`:

```hcl
resource_group_name = "hr-candidate-tool-rg"
application_name = "hr-candidate-tool-github-actions"
enable_acr_permissions = true
enable_webapp_permissions = true
```

### Step 5: Deploy with Terraform

```bash
# Initialize Terraform
terraform init

# Plan the deployment
terraform plan

# Apply the configuration
terraform apply

# Get the GitHub Actions secret (this is sensitive data)
terraform output -raw github_actions_secret

# Pretty print the JSON
terraform output -raw github_actions_secret | jq .
```

### Step 6: Verify Terraform Deployment

```bash
# Show all outputs
terraform output

# List the created resources
terraform state list

# Show detailed information about the service principal
terraform show
```

### Step 7: Destroy Resources (When No Longer Needed)

```bash
# Remove the service principal and related resources
terraform destroy
```

### Step 6: GitHub Actions Integration

**Add the JSON as a GitHub Secret:**

1. **Go to your GitHub repository**
2. **Navigate to Settings → Secrets and variables → Actions**
3. **Click "New repository secret"**
4. **Add the following secrets:**

| Secret Name | Value | Source |
|-------------|-------|---------|
| `AZURE_CREDENTIALS` | The complete JSON from Step 6 | Service principal JSON |
| `AZURE_SUBSCRIPTION_ID` | Your subscription ID | From JSON or Azure Portal |
| `AZURE_TENANT_ID` | Your tenant ID | From JSON or Azure Portal |

5. **Click "Add secret" for each one**

**Test in GitHub Actions workflow:**

```yaml
name: Test Azure Login
on: [workflow_dispatch]

jobs:
  test-login:
    runs-on: ubuntu-latest
    steps:
    - name: Azure Login
      uses: azure/login@v1
      with:
        creds: ${{ secrets.AZURE_CREDENTIALS }}
    
    - name: Test Azure CLI
      run: |
        az account show
        az group list --output table
```

### Step 7: Azure DevOps Integration

**Method 1: Azure DevOps Service Connection (Recommended)**

1. **Go to your Azure DevOps project**
2. **Navigate to Project Settings → Service connections**
3. **Click "New service connection"**
4. **Select "Azure Resource Manager"**
5. **Choose "Service principal (manual)"**
6. **Fill in the details:**
   - **Subscription ID**: From your JSON
   - **Subscription Name**: Your subscription name
   - **Service Principal Id**: The `clientId` from JSON
   - **Service principal key**: The `clientSecret` from JSON
   - **Tenant ID**: The `tenantId` from JSON
7. **Click "Verify and save"**

**Method 2: Azure DevOps Variable Groups**

1. **Go to Pipelines → Library**
2. **Click "+ Variable group"**
3. **Name it "Azure-Credentials"**
4. **Add variables:**
   - `AZURE_CLIENT_ID` = clientId from JSON
   - `AZURE_CLIENT_SECRET` = clientSecret from JSON (mark as secret)
   - `AZURE_TENANT_ID` = tenantId from JSON
   - `AZURE_SUBSCRIPTION_ID` = subscriptionId from JSON

**Test in Azure DevOps Pipeline:**

```yaml
# azure-pipelines.yml
trigger:
- main

pool:
  vmImage: 'ubuntu-latest'

variables:
- group: Azure-Credentials

steps:
- task: AzureCLI@2
  displayName: 'Test Azure Connection'
  inputs:
    azureSubscription: 'your-service-connection-name'  # If using service connection
    scriptType: 'bash'
    scriptLocation: 'inlineScript'
    inlineScript: |
      az account show
      az group list --output table

# Or using service principal directly:
- task: AzureCLI@2
  displayName: 'Login with Service Principal'
  inputs:
    scriptType: 'bash'
    scriptLocation: 'inlineScript'
    inlineScript: |
      az login --service-principal \
        --username $(AZURE_CLIENT_ID) \
        --password $(AZURE_CLIENT_SECRET) \
        --tenant $(AZURE_TENANT_ID)
      az account set --subscription $(AZURE_SUBSCRIPTION_ID)
      az account show
```

---

## CI/CD Platform Integration Summary

### GitHub Actions Integration Summary

**Required GitHub Secrets for HR Candidate Tool:**

| Secret Name | Description | Used In |
|-------------|-------------|---------|
| `AZURE_CREDENTIALS` | Complete service principal JSON | azure/login@v1 action |
| `ACR_USERNAME` | Container Registry username | Docker login |
| `ACR_PASSWORD` | Container Registry password | Docker login |
| `AZURE_RESOURCE_GROUP` | Resource group name | Deployment scripts |
| `AZURE_STORAGE_CONNECTION_STRING` | Storage account connection | App configuration |
| `AZURE_OPENAI_ENDPOINT` | OpenAI service endpoint | App configuration |
| `AZURE_OPENAI_API_KEY` | OpenAI API key | App configuration |
| `AZURE_OPENAI_API_VERSION` | OpenAI API version | App configuration |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | OpenAI model deployment name | App configuration |

**Complete GitHub Actions Workflow for HR Candidate Tool:**

```yaml
name: Deploy HR Candidate Tool
on:
  push:
    branches: [main]
  workflow_dispatch:

env:
  AZURE_WEBAPP_NAME: 'your-web-app-name'
  REGISTRY_NAME: 'your-acr-name'
  IMAGE_NAME: 'hr-candidate-app'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - name: Checkout
      uses: actions/checkout@v4

    - name: Azure Login
      uses: azure/login@v1
      with:
        creds: ${{ secrets.AZURE_CREDENTIALS }}

    - name: Login to ACR
      uses: azure/docker-login@v1
      with:
        login-server: ${{ env.REGISTRY_NAME }}.azurecr.io
        username: ${{ secrets.ACR_USERNAME }}
        password: ${{ secrets.ACR_PASSWORD }}

    - name: Build and Push Docker Image
      run: |
        docker build -t ${{ env.REGISTRY_NAME }}.azurecr.io/${{ env.IMAGE_NAME }}:${{ github.sha }} .
        docker push ${{ env.REGISTRY_NAME }}.azurecr.io/${{ env.IMAGE_NAME }}:${{ github.sha }}

    - name: Deploy to Azure Web App
      uses: azure/webapps-deploy@v2
      with:
        app-name: ${{ env.AZURE_WEBAPP_NAME }}
        images: ${{ env.REGISTRY_NAME }}.azurecr.io/${{ env.IMAGE_NAME }}:${{ github.sha }}

    - name: Configure App Settings
      run: |
        az webapp config appsettings set \
          --resource-group ${{ secrets.AZURE_RESOURCE_GROUP }} \
          --name ${{ env.AZURE_WEBAPP_NAME }} \
          --settings \
          AZURE_STORAGE_CONNECTION_STRING="${{ secrets.AZURE_STORAGE_CONNECTION_STRING }}" \
          AZURE_OPENAI_ENDPOINT="${{ secrets.AZURE_OPENAI_ENDPOINT }}" \
          AZURE_OPENAI_API_KEY="${{ secrets.AZURE_OPENAI_API_KEY }}" \
          AZURE_OPENAI_API_VERSION="${{ secrets.AZURE_OPENAI_API_VERSION }}" \
          AZURE_OPENAI_DEPLOYMENT_NAME="${{ secrets.AZURE_OPENAI_DEPLOYMENT_NAME }}"
```

### Azure DevOps Integration Summary

**Service Connection Setup (Recommended):**

1. **Create Service Connection:**
   - Go to Project Settings → Service connections
   - New service connection → Azure Resource Manager
   - Choose "Service principal (manual)"
   - Use service principal details from any method above

2. **Variable Groups for App Configuration:**
   - Go to Pipelines → Library
   - Create variable group: `hr-candidate-app-config`
   - Add all application configuration variables

**Complete Azure DevOps Pipeline for HR Candidate Tool:**

```yaml
trigger:
- main

pool:
  vmImage: 'ubuntu-latest'

variables:
- group: hr-candidate-app-config
- name: acrName
  value: 'your-acr-name'
- name: webAppName
  value: 'your-web-app-name'
- name: resourceGroup
  value: 'your-resource-group'

stages:
- stage: Build
  displayName: 'Build and Push Container'
  jobs:
  - job: BuildPush
    displayName: 'Build and Push to ACR'
    steps:
    - task: Docker@2
      displayName: 'Build Docker Image'
      inputs:
        containerRegistry: 'your-acr-service-connection'
        repository: 'hr-candidate-app'
        command: 'buildAndPush'
        Dockerfile: '**/Dockerfile'
        tags: |
          $(Build.BuildNumber)
          latest

- stage: Deploy
  displayName: 'Deploy to Azure'
  dependsOn: Build
  jobs:
  - deployment: DeployToAzure
    displayName: 'Deploy to Azure Web App'
    environment: 'production'
    strategy:
      runOnce:
        deploy:
          steps:
          - task: AzureWebAppContainer@1
            displayName: 'Deploy Container to Web App'
            inputs:
              azureSubscription: 'your-azure-service-connection'
              appName: $(webAppName)
              resourceGroupName: $(resourceGroup)
              imageName: '$(acrName).azurecr.io/hr-candidate-app:$(Build.BuildNumber)'

          - task: AzureCLI@2
            displayName: 'Configure App Settings'
            inputs:
              azureSubscription: 'your-azure-service-connection'
              scriptType: 'bash'
              scriptLocation: 'inlineScript'
              inlineScript: |
                az webapp config appsettings set \
                  --resource-group $(resourceGroup) \
                  --name $(webAppName) \
                  --settings \
                  AZURE_STORAGE_CONNECTION_STRING="$(AZURE_STORAGE_CONNECTION_STRING)" \
                  AZURE_OPENAI_ENDPOINT="$(AZURE_OPENAI_ENDPOINT)" \
                  AZURE_OPENAI_API_KEY="$(AZURE_OPENAI_API_KEY)" \
                  AZURE_OPENAI_API_VERSION="$(AZURE_OPENAI_API_VERSION)" \
                  AZURE_OPENAI_DEPLOYMENT_NAME="$(AZURE_OPENAI_DEPLOYMENT_NAME)"
```

### Platform Comparison for HR Candidate Tool

| Feature | GitHub Actions | Azure DevOps | Recommendation |
|---------|----------------|---------------|----------------|
| **Setup Complexity** | Simple (secrets in repo) | Moderate (service connections) | GitHub for simplicity |
| **Security** | Good (repo-level secrets) | Excellent (project-level connections) | Azure DevOps for enterprise |
| **Integration** | Native GitHub integration | Native Azure integration | Depends on your ecosystem |
| **Cost** | Free for public repos | Free tier available | Both cost-effective |
| **Features** | Rich marketplace | Enterprise features | Azure DevOps for complex workflows |

### Best Practices for Both Platforms

**1. Security:**
```bash
# Rotate service principal credentials regularly
az ad sp credential reset --name "your-service-principal-name"

# Use least privilege principle
az role assignment create \
  --assignee $CLIENT_ID \
  --role "Contributor" \
  --scope "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP"
```

**2. Monitoring:**
```bash
# Monitor service principal usage
az monitor activity-log list \
  --caller $CLIENT_ID \
  --start-time 2024-01-01 \
  --output table
```

**3. Environment Management:**
```yaml
# Use different service principals for different environments
environments:
  dev:
    service_principal: "hr-tool-dev-sp"
  staging:
    service_principal: "hr-tool-staging-sp"
  prod:
    service_principal: "hr-tool-prod-sp"
```

**4. Backup and Recovery:**
```bash
# Export service principal configuration
az ad sp show --id $CLIENT_ID > service-principal-backup.json

# Document role assignments
az role assignment list --assignee $CLIENT_ID > role-assignments-backup.json
```

## Comparison of Methods

| Method | Pros | Cons | Best For |
|--------|------|------|----------|
| **Azure Portal** | Visual interface, step-by-step, good for learning | Manual process, prone to human error | One-time setup, beginners |
| **Azure CLI** | Quick, scriptable, consistent results | Requires CLI knowledge | Automation, experienced users |
| **Terraform** | Infrastructure as Code, versioned, repeatable | Requires Terraform knowledge, more complex setup | Production environments, teams |

---

## Security Best Practices

### 1. Principle of Least Privilege

```bash
# Instead of Contributor on entire subscription, scope to resource group
az ad sp create-for-rbac \
  --name "hr-tool-deploy" \
  --role "Contributor" \
  --scopes "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP"
```

### 2. Short-lived Credentials

```bash
# Create service principal with shorter credential lifetime
az ad sp create-for-rbac \
  --name "hr-tool-deploy" \
  --role "Contributor" \
  --scopes "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP" \
  --years 1  # Instead of default 2 years
```

### 3. Regular Rotation

```bash
# Reset service principal credentials
az ad sp credential reset --name "hr-tool-deploy"
```

### 4. Monitoring and Auditing

```bash
# List all role assignments for the service principal
az role assignment list --assignee $CLIENT_ID --output table

# Check service principal activity (requires audit logs access)
az monitor activity-log list --caller $CLIENT_ID
```

---

## Troubleshooting Common Issues

### Issue 1: Insufficient Permissions

**Error**: `Insufficient privileges to complete the operation`

**Solution**:
```bash
# Check your current permissions
az role assignment list --assignee $(az account show --query user.name --output tsv)

# You need at least "User Access Administrator" or "Owner" role
```

### Issue 2: Service Principal Not Found

**Error**: `Service principal not found`

**Solution**:
```bash
# List all service principals to verify creation
az ad sp list --display-name "hr-tool-deploy" --output table

# If not found, recreate with exact name match
```

### Issue 3: GitHub Actions Authentication Fails

**Error**: `Failed to authenticate with Azure`

**Solution**:
1. Verify the JSON format in GitHub secrets
2. Check that all four values are correct: clientId, clientSecret, subscriptionId, tenantId
3. Ensure the service principal has correct permissions on the resource group

### Issue 4: Role Assignment Fails

**Error**: `Role assignment failed`

**Solution**:
```bash
# Check if the role assignment already exists
az role assignment list --assignee $CLIENT_ID --scope "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP"

# Delete and recreate if needed
az role assignment delete --assignee $CLIENT_ID --role "Contributor" --scope "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP"
az role assignment create --assignee $CLIENT_ID --role "Contributor" --scope "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP"
```

---

## Next Steps

After creating your service principal using any of these methods:

### Immediate Actions:
1. **Save the service principal credentials securely**
2. **Add to your CI/CD platform:**
   - **GitHub Actions**: Add as repository secrets
   - **Azure DevOps**: Create service connection or variable group
3. **Test the service principal** by running a test workflow/pipeline
4. **Document the service principal details** for your team

### GitHub Actions Setup:
```bash
# Quick verification that GitHub secrets are working
curl -H "Authorization: token YOUR_GITHUB_TOKEN" \
  https://api.github.com/repos/YOUR_USERNAME/YOUR_REPO/actions/secrets
```

### Azure DevOps Setup:
```bash
# Test service connection
az devops service-endpoint list \
  --organization https://dev.azure.com/YOUR_ORG \
  --project YOUR_PROJECT
```

### Security and Maintenance:
1. **Set up monitoring** for service principal usage
2. **Plan for credential rotation** (recommended every 6-12 months)
3. **Review permissions** quarterly
4. **Set up alerts** for authentication failures

### For HR Candidate Tool Specifically:
1. **Update your workflow files** with the resource names from your infrastructure
2. **Test the complete deployment pipeline** end-to-end
3. **Verify application configuration** after deployment
4. **Set up monitoring** for the deployed application

The service principal is now ready to be used in your GitHub Actions or Azure DevOps pipeline for automated deployment of the HR Candidate Management Tool!
