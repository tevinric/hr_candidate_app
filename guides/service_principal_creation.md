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
2. **Search for "Azure Active Directory"** in the top search bar
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

---

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

1. **Copy the JSON output** and add it as `AZURE_CREDENTIALS` secret in GitHub
2. **Test the service principal** by running a simple GitHub Actions workflow
3. **Document the service principal details** for your team
4. **Set up monitoring** for service principal usage
5. **Plan for credential rotation** (recommended every 6-12 months)

The service principal is now ready to be used in your GitHub Actions workflow for automated deployment of the HR Candidate Management Tool!
