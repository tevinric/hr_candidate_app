# Complete Terraform Infrastructure for HR Candidate Management Tool

This Terraform configuration creates all the Azure resources needed for your HR Candidate Management Tool application.

## File Structure

Create the following directory structure:

```
terraform/
├── main.tf                 # Main infrastructure resources
├── variables.tf           # Input variables
├── outputs.tf            # Output values
├── providers.tf          # Provider configurations
├── service-principal.tf  # Service principal for GitHub Actions
├── terraform.tfvars     # Variable values (gitignored)
├── versions.tf          # Terraform and provider version constraints
└── .gitignore           # Git ignore file
```

## 1. versions.tf

```hcl
terraform {
  required_version = ">= 1.0"
  
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~>3.80.0"
    }
    azuread = {
      source  = "hashicorp/azuread"
      version = "~>2.45.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~>3.4.0"
    }
  }
}
```

## 2. providers.tf

```hcl
# Configure the Azure Provider
provider "azurerm" {
  features {
    cognitive_account {
      purge_soft_delete_on_destroy = true
    }
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
  }
}

# Configure the Azure Active Directory Provider
provider "azuread" {
}

# Get current Azure configuration
data "azurerm_client_config" "current" {}
```

## 3. variables.tf

```hcl
# General Configuration
variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"
  
  validation {
    condition     = can(regex("^(dev|staging|prod)$", var.environment))
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "location" {
  description = "Azure region for resources"
  type        = string
  default     = "East US"
}

variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
  default     = ""
}

variable "project_name" {
  description = "Name of the project (used for resource naming)"
  type        = string
  default     = "hr-candidate-tool"
}

# Naming Configuration
variable "use_random_suffix" {
  description = "Whether to add random suffix to resource names for uniqueness"
  type        = bool
  default     = true
}

# Azure Container Registry
variable "acr_sku" {
  description = "SKU for Azure Container Registry"
  type        = string
  default     = "Basic"
  
  validation {
    condition     = can(regex("^(Basic|Standard|Premium)$", var.acr_sku))
    error_message = "ACR SKU must be Basic, Standard, or Premium."
  }
}

variable "acr_admin_enabled" {
  description = "Enable admin user for ACR"
  type        = bool
  default     = true
}

# Storage Account
variable "storage_account_tier" {
  description = "Storage account tier"
  type        = string
  default     = "Standard"
}

variable "storage_account_replication" {
  description = "Storage account replication type"
  type        = string
  default     = "LRS"
}

# Azure OpenAI
variable "openai_sku" {
  description = "SKU for Azure OpenAI service"
  type        = string
  default     = "S0"
}

variable "openai_location" {
  description = "Location for Azure OpenAI service (limited availability)"
  type        = string
  default     = "East US"
}

variable "openai_model_deployment" {
  description = "OpenAI model deployment configuration"
  type = object({
    name         = string
    model_name   = string
    model_version = string
  })
  default = {
    name         = "gpt-4o-mini"
    model_name   = "gpt-4o-mini"
    model_version = "2024-07-18"
  }
}

# App Service
variable "app_service_plan_sku" {
  description = "SKU for App Service Plan"
  type        = string
  default     = "B1"
}

variable "app_service_plan_os" {
  description = "Operating system for App Service Plan"
  type        = string
  default     = "Linux"
}

# Application Configuration
variable "app_settings" {
  description = "Application settings for the web app"
  type        = map(string)
  default = {
    BACKUP_RETENTION_DAYS     = "30"
    MAX_FILE_SIZE_MB         = "10"
    MAX_SEARCH_RESULTS       = "100"
    LOG_LEVEL               = "INFO"
    AUTO_BACKUP_ENABLED     = "True"
    AUTO_SYNC_ENABLED       = "True"
    SYNC_INTERVAL_SECONDS   = "300"
    DB_CONTAINER            = "app-data"
    DB_BLOB_NAME           = "hr_candidates.db"
    LOCAL_DB_PATH          = "/tmp/hr_candidates.db"
    AZURE_OPENAI_API_VERSION = "2024-02-15-preview"
  }
}

# Tags
variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default = {
    Project     = "HR Candidate Management Tool"
    Environment = "Production"
    ManagedBy   = "Terraform"
  }
}

# Service Principal Configuration
variable "create_service_principal" {
  description = "Whether to create service principal for GitHub Actions"
  type        = bool
  default     = true
}

variable "service_principal_name" {
  description = "Name for the GitHub Actions service principal"
  type        = string
  default     = ""
}
```

## 4. main.tf

```hcl
# Random suffix for unique naming
resource "random_string" "suffix" {
  count   = var.use_random_suffix ? 1 : 0
  length  = 6
  special = false
  upper   = false
}

locals {
  # Generate unique names
  suffix = var.use_random_suffix ? random_string.suffix[0].result : ""
  
  # Resource names
  resource_group_name = var.resource_group_name != "" ? var.resource_group_name : "${var.project_name}-rg"
  acr_name           = "${replace(var.project_name, "-", "")}acr${local.suffix}"
  storage_name       = "${replace(var.project_name, "-", "")}store${local.suffix}"
  openai_name        = "${var.project_name}-openai-${local.suffix}"
  app_plan_name      = "${var.project_name}-plan-${local.suffix}"
  web_app_name       = "${var.project_name}-app-${local.suffix}"
  
  # Merge tags with default values
  common_tags = merge(var.tags, {
    Environment = var.environment
    CreatedBy   = "Terraform"
    CreatedOn   = timestamp()
  })
}

# Resource Group
resource "azurerm_resource_group" "main" {
  name     = local.resource_group_name
  location = var.location
  tags     = local.common_tags
}

# Azure Container Registry
resource "azurerm_container_registry" "main" {
  name                = local.acr_name
  resource_group_name = azurerm_resource_group.main.name
  location           = azurerm_resource_group.main.location
  sku                = var.acr_sku
  admin_enabled      = var.acr_admin_enabled
  
  tags = local.common_tags
}

# Storage Account
resource "azurerm_storage_account" "main" {
  name                     = local.storage_name
  resource_group_name      = azurerm_resource_group.main.name
  location                = azurerm_resource_group.main.location
  account_tier            = var.storage_account_tier
  account_replication_type = var.storage_account_replication
  account_kind            = "StorageV2"
  
  # Security settings
  min_tls_version                = "TLS1_2"
  allow_nested_items_to_be_public = false
  
  # Enable blob versioning and soft delete
  blob_properties {
    versioning_enabled  = true
    change_feed_enabled = true
    
    delete_retention_policy {
      days = 7
    }
    
    container_delete_retention_policy {
      days = 7
    }
  }
  
  tags = local.common_tags
}

# Storage Containers
resource "azurerm_storage_container" "app_data" {
  name                  = "app-data"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "backups" {
  name                  = "hr-backups"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}

# Azure OpenAI Service
resource "azurerm_cognitive_account" "openai" {
  name                = local.openai_name
  location           = var.openai_location
  resource_group_name = azurerm_resource_group.main.name
  kind               = "OpenAI"
  sku_name           = var.openai_sku
  
  # Security settings
  public_network_access_enabled = true
  custom_question_answering_search_service_id = null
  
  tags = local.common_tags
}

# Azure OpenAI Model Deployment
resource "azurerm_cognitive_deployment" "gpt4o_mini" {
  name                 = var.openai_model_deployment.name
  cognitive_account_id = azurerm_cognitive_account.openai.id
  
  model {
    format  = "OpenAI"
    name    = var.openai_model_deployment.model_name
    version = var.openai_model_deployment.model_version
  }
  
  scale {
    type = "Standard"
  }
  
  depends_on = [azurerm_cognitive_account.openai]
}

# App Service Plan
resource "azurerm_service_plan" "main" {
  name                = local.app_plan_name
  resource_group_name = azurerm_resource_group.main.name
  location           = azurerm_resource_group.main.location
  os_type            = var.app_service_plan_os
  sku_name           = var.app_service_plan_sku
  
  tags = local.common_tags
}

# Web App
resource "azurerm_linux_web_app" "main" {
  name                = local.web_app_name
  resource_group_name = azurerm_resource_group.main.name
  location           = azurerm_service_plan.main.location
  service_plan_id    = azurerm_service_plan.main.id
  
  # Container configuration
  site_config {
    always_on = false  # Set to true for production with higher SKU
    
    application_stack {
      docker_image     = "${azurerm_container_registry.main.login_server}/hr-candidate-app"
      docker_image_tag = "latest"
    }
    
    container_registry_url               = "https://${azurerm_container_registry.main.login_server}"
    container_registry_username          = azurerm_container_registry.main.admin_username
    container_registry_password          = azurerm_container_registry.main.admin_password
    container_registry_use_managed_identity = false
  }
  
  # Application settings
  app_settings = merge(var.app_settings, {
    # Azure services configuration
    AZURE_STORAGE_CONNECTION_STRING = azurerm_storage_account.main.primary_connection_string
    AZURE_OPENAI_ENDPOINT          = azurerm_cognitive_account.openai.endpoint
    AZURE_OPENAI_API_KEY           = azurerm_cognitive_account.openai.primary_access_key
    AZURE_OPENAI_DEPLOYMENT_NAME   = azurerm_cognitive_deployment.gpt4o_mini.name
    
    # Container and backup configuration
    BACKUP_CONTAINER = azurerm_storage_container.backups.name
    
    # Docker configuration
    DOCKER_REGISTRY_SERVER_URL      = "https://${azurerm_container_registry.main.login_server}"
    DOCKER_REGISTRY_SERVER_USERNAME = azurerm_container_registry.main.admin_username
    DOCKER_REGISTRY_SERVER_PASSWORD = azurerm_container_registry.main.admin_password
    
    # Streamlit configuration
    STREAMLIT_SERVER_PORT           = "8501"
    STREAMLIT_SERVER_ADDRESS        = "0.0.0.0"
    STREAMLIT_SERVER_ENABLE_CORS    = "false"
    STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION = "false"
  })
  
  # Connection strings
  connection_string {
    name  = "DefaultConnection"
    type  = "Custom"
    value = azurerm_storage_account.main.primary_connection_string
  }
  
  # Identity for managed identity access (optional)
  identity {
    type = "SystemAssigned"
  }
  
  tags = local.common_tags
  
  depends_on = [
    azurerm_container_registry.main,
    azurerm_storage_account.main,
    azurerm_cognitive_account.openai
  ]
}

# Application Insights (Optional but recommended)
resource "azurerm_application_insights" "main" {
  name                = "${local.web_app_name}-insights"
  location           = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  application_type   = "web"
  
  tags = local.common_tags
}

# Configure Application Insights for Web App
resource "azurerm_linux_web_app_slot" "staging" {
  count          = var.environment == "prod" ? 1 : 0
  name           = "staging"
  app_service_id = azurerm_linux_web_app.main.id
  
  site_config {
    application_stack {
      docker_image     = "${azurerm_container_registry.main.login_server}/hr-candidate-app"
      docker_image_tag = "staging"
    }
  }
  
  app_settings = azurerm_linux_web_app.main.app_settings
  
  tags = local.common_tags
}
```

## 5. service-principal.tf

```hcl
# Service Principal for GitHub Actions (conditional creation)
resource "azuread_application" "github_actions" {
  count        = var.create_service_principal ? 1 : 0
  display_name = var.service_principal_name != "" ? var.service_principal_name : "${var.project_name}-github-actions"
  description  = "Service Principal for GitHub Actions deployment of ${var.project_name}"
  
  owners = [data.azurerm_client_config.current.object_id]
  
  tags = ["github-actions", var.project_name, "deployment"]
}

resource "azuread_service_principal" "github_actions" {
  count                            = var.create_service_principal ? 1 : 0
  application_id                   = azuread_application.github_actions[0].application_id
  app_role_assignment_required     = false
  owners                          = [data.azurerm_client_config.current.object_id]

  tags = ["github-actions", var.project_name, "deployment"]
}

resource "azuread_service_principal_password" "github_actions" {
  count                = var.create_service_principal ? 1 : 0
  service_principal_id = azuread_service_principal.github_actions[0].object_id
  display_name        = "GitHub Actions Secret"
  end_date_relative   = "8760h" # 1 year
}

# Role assignments for service principal
resource "azurerm_role_assignment" "contributor" {
  count                = var.create_service_principal ? 1 : 0
  scope                = azurerm_resource_group.main.id
  role_definition_name = "Contributor"
  principal_id         = azuread_service_principal.github_actions[0].object_id
}

resource "azurerm_role_assignment" "acr_push" {
  count                = var.create_service_principal ? 1 : 0
  scope                = azurerm_container_registry.main.id
  role_definition_name = "AcrPush"
  principal_id         = azuread_service_principal.github_actions[0].object_id
}

resource "azurerm_role_assignment" "acr_pull" {
  count                = var.create_service_principal ? 1 : 0
  scope                = azurerm_container_registry.main.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_service_principal.github_actions[0].object_id
}
```

## 6. outputs.tf

```hcl
# Resource Group
output "resource_group_name" {
  description = "Name of the created resource group"
  value       = azurerm_resource_group.main.name
}

output "resource_group_location" {
  description = "Location of the resource group"
  value       = azurerm_resource_group.main.location
}

# Container Registry
output "acr_name" {
  description = "Name of the Azure Container Registry"
  value       = azurerm_container_registry.main.name
}

output "acr_login_server" {
  description = "Login server for the Azure Container Registry"
  value       = azurerm_container_registry.main.login_server
}

output "acr_username" {
  description = "Admin username for ACR"
  value       = azurerm_container_registry.main.admin_username
  sensitive   = true
}

output "acr_password" {
  description = "Admin password for ACR"
  value       = azurerm_container_registry.main.admin_password
  sensitive   = true
}

# Storage Account
output "storage_account_name" {
  description = "Name of the storage account"
  value       = azurerm_storage_account.main.name
}

output "storage_connection_string" {
  description = "Connection string for the storage account"
  value       = azurerm_storage_account.main.primary_connection_string
  sensitive   = true
}

output "storage_containers" {
  description = "Names of created storage containers"
  value = {
    app_data = azurerm_storage_container.app_data.name
    backups  = azurerm_storage_container.backups.name
  }
}

# Azure OpenAI
output "openai_name" {
  description = "Name of the Azure OpenAI service"
  value       = azurerm_cognitive_account.openai.name
}

output "openai_endpoint" {
  description = "Endpoint for the Azure OpenAI service"
  value       = azurerm_cognitive_account.openai.endpoint
}

output "openai_api_key" {
  description = "API key for the Azure OpenAI service"
  value       = azurerm_cognitive_account.openai.primary_access_key
  sensitive   = true
}

output "openai_deployment_name" {
  description = "Name of the OpenAI model deployment"
  value       = azurerm_cognitive_deployment.gpt4o_mini.name
}

# Web App
output "web_app_name" {
  description = "Name of the web app"
  value       = azurerm_linux_web_app.main.name
}

output "web_app_url" {
  description = "URL of the web app"
  value       = "https://${azurerm_linux_web_app.main.default_hostname}"
}

output "web_app_default_hostname" {
  description = "Default hostname of the web app"
  value       = azurerm_linux_web_app.main.default_hostname
}

# App Service Plan
output "app_service_plan_name" {
  description = "Name of the App Service Plan"
  value       = azurerm_service_plan.main.name
}

# Application Insights
output "application_insights_name" {
  description = "Name of Application Insights"
  value       = azurerm_application_insights.main.name
}

output "application_insights_instrumentation_key" {
  description = "Instrumentation key for Application Insights"
  value       = azurerm_application_insights.main.instrumentation_key
  sensitive   = true
}

# Service Principal (if created)
output "service_principal_client_id" {
  description = "Client ID of the service principal"
  value       = var.create_service_principal ? azuread_application.github_actions[0].application_id : null
}

output "service_principal_tenant_id" {
  description = "Tenant ID for the service principal"
  value       = data.azurerm_client_config.current.tenant_id
}

output "service_principal_subscription_id" {
  description = "Subscription ID for the service principal"
  value       = data.azurerm_client_config.current.subscription_id
}

# GitHub Actions Credentials
output "github_actions_credentials" {
  description = "JSON credentials for GitHub Actions (AZURE_CREDENTIALS secret)"
  value = var.create_service_principal ? jsonencode({
    clientId       = azuread_application.github_actions[0].application_id
    clientSecret   = azuread_service_principal_password.github_actions[0].value
    subscriptionId = data.azurerm_client_config.current.subscription_id
    tenantId       = data.azurerm_client_config.current.tenant_id
  }) : null
  sensitive = true
}

# Summary of key values for GitHub Actions
output "github_secrets_summary" {
  description = "Summary of values needed for GitHub secrets"
  value = {
    AZURE_RESOURCE_GROUP              = azurerm_resource_group.main.name
    AZURE_WEBAPP_NAME                = azurerm_linux_web_app.main.name
    REGISTRY_NAME                    = azurerm_container_registry.main.name
    AZURE_OPENAI_API_VERSION         = var.app_settings.AZURE_OPENAI_API_VERSION
    AZURE_OPENAI_DEPLOYMENT_NAME     = azurerm_cognitive_deployment.gpt4o_mini.name
  }
}

# Environment Configuration
output "app_settings_summary" {
  description = "Summary of application configuration"
  value = {
    web_app_url        = "https://${azurerm_linux_web_app.main.default_hostname}"
    container_registry = azurerm_container_registry.main.login_server
    storage_containers = {
      app_data = azurerm_storage_container.app_data.name
      backups  = azurerm_storage_container.backups.name
    }
    openai_deployment = azurerm_cognitive_deployment.gpt4o_mini.name
  }
}
```

## 7. terraform.tfvars

```hcl
# General Configuration
environment         = "prod"
location           = "East US"
project_name       = "hr-candidate-tool"
use_random_suffix  = true

# Resource Configuration
acr_sku                    = "Basic"
storage_account_tier       = "Standard"
storage_account_replication = "LRS"
openai_sku                = "S0"
openai_location           = "East US"
app_service_plan_sku      = "B1"

# OpenAI Model Configuration
openai_model_deployment = {
  name         = "gpt-4o-mini"
  model_name   = "gpt-4o-mini"
  model_version = "2024-07-18"
}

# Service Principal
create_service_principal = true

# Tags
tags = {
  Project     = "HR Candidate Management Tool"
  Environment = "Production"
  Owner       = "DevOps Team"
  CostCenter  = "IT"
  ManagedBy   = "Terraform"
}

# Application Settings (customize as needed)
app_settings = {
  BACKUP_RETENTION_DAYS     = "30"
  MAX_FILE_SIZE_MB         = "10"
  MAX_SEARCH_RESULTS       = "100"
  LOG_LEVEL               = "INFO"
  AUTO_BACKUP_ENABLED     = "True"
  AUTO_SYNC_ENABLED       = "True"
  SYNC_INTERVAL_SECONDS   = "300"
  DB_CONTAINER            = "app-data"
  DB_BLOB_NAME           = "hr_candidates.db"
  LOCAL_DB_PATH          = "/tmp/hr_candidates.db"
  AZURE_OPENAI_API_VERSION = "2024-02-15-preview"
}
```

## 8. .gitignore

```gitignore
# Terraform files
*.tfstate
*.tfstate.*
*.tfplan
*.tfplan.*
.terraform/
.terraform.lock.hcl
override.tf
override.tf.json
*_override.tf
*_override.tf.json

# Sensitive files
terraform.tfvars
*.auto.tfvars
*.auto.tfvars.json

# IDE files
.vscode/
.idea/
*.swp
*.swo

# OS files
.DS_Store
Thumbs.db

# Logs
*.log
crash.log
crash.*.log

# Backup files
*.backup
*.bak
```

## Deployment Instructions

### 1. Initialize Terraform

```bash
# Create terraform directory
mkdir terraform
cd terraform

# Copy all the above files to this directory
# Make sure to customize terraform.tfvars with your values

# Initialize Terraform
terraform init
```

### 2. Plan and Apply

```bash
# See what will be created
terraform plan

# Apply the configuration
terraform apply

# Confirm with 'yes' when prompted
```

### 3. Get GitHub Secrets

```bash
# Get all the values you need for GitHub secrets
terraform output github_secrets_summary

# Get the service principal credentials (sensitive)
terraform output -raw github_actions_credentials | jq .

# Get ACR credentials
terraform output acr_username
terraform output -raw acr_password

# Get storage connection string
terraform output -raw storage_connection_string

# Get OpenAI credentials
terraform output -raw openai_api_key
```

### 4. Update GitHub Actions Workflow

Update your `.github/workflows/deploy.yml` with the values from the outputs:

```yaml
env:
  AZURE_WEBAPP_NAME: 'your-actual-web-app-name'    # From terraform output
  REGISTRY_NAME: 'your-actual-acr-name'            # From terraform output
  IMAGE_NAME: 'hr-candidate-app'
```

### 5. Add GitHub Secrets

Add these secrets to your GitHub repository:

| Secret Name | Terraform Output Command |
|-------------|-------------------------|
| `AZURE_CREDENTIALS` | `terraform output -raw github_actions_credentials` |
| `ACR_USERNAME` | `terraform output -raw acr_username` |
| `ACR_PASSWORD` | `terraform output -raw acr_password` |
| `AZURE_RESOURCE_GROUP` | `terraform output -raw resource_group_name` |
| `AZURE_STORAGE_CONNECTION_STRING` | `terraform output -raw storage_connection_string` |
| `AZURE_OPENAI_ENDPOINT` | `terraform output -raw openai_endpoint` |
| `AZURE_OPENAI_API_KEY` | `terraform output -raw openai_api_key` |
| `AZURE_OPENAI_API_VERSION` | `2024-02-15-preview` |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | `terraform output -raw openai_deployment_name` |

## Features Included

✅ **Resource Group** with proper naming and tagging
✅ **Azure Container Registry** with admin access enabled
✅ **Storage Account** with app-data and hr-backups containers
✅ **Azure OpenAI Service** with GPT-4o-mini deployment
✅ **App Service Plan** and **Linux Web App** with container configuration
✅ **Service Principal** for GitHub Actions with appropriate permissions
✅ **Application Insights** for monitoring
✅ **Staging Slot** for production environments
✅ **Security configurations** (TLS, private containers, etc.)
✅ **Proper dependencies** between resources
✅ **Comprehensive outputs** for easy integration

## Cost Estimation

With default settings (B1 App Service Plan):
- **App Service Plan (B1)**: ~$13/month
- **Storage Account**: ~$1-2/month
- **Container Registry (Basic)**: ~$5/month
- **Azure OpenAI**: Pay-per-use (~$5-20/month)
- **Application Insights**: Free tier included

**Total estimated cost**: ~$25-40/month

## Cleanup

To destroy all resources:

```bash
terraform destroy
```

This Terraform configuration provides a production-ready infrastructure for your HR Candidate Management Tool with proper security, monitoring, and deployment capabilities.
