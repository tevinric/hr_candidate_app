# Azure App Registration Setup for HR Candidate Management Tool

This guide will walk you through setting up Microsoft Entra ID (Azure Active Directory) authentication for your HR Candidate Management Tool.

## Prerequisites

- Azure subscription with appropriate permissions
- Global Administrator or Application Administrator role in Azure AD
- Your web application URL (e.g., `https://your-app-name.azurewebsites.net`)

## Step 1: Create App Registration

### 1.1 Navigate to Azure Portal
1. Go to [Azure Portal](https://portal.azure.com)
2. Search for and select **"Azure Active Directory"** (or **"Microsoft Entra ID"**)
3. In the left sidebar, click **"App registrations"**
4. Click **"+ New registration"**

### 1.2 Configure App Registration
Fill in the following details:

**Name:** `HR Candidate Management Tool`

**Supported account types:** 
- Select **"Accounts in this organizational directory only (Single tenant)"**

**Redirect URI:**
- Platform: **Web**
- URI: `https://YOUR-APP-NAME.azurewebsites.net` (replace with your actual app URL)

Click **"Register"**

### 1.3 Note Important Values
After registration, copy and save these values from the **Overview** page:
- **Application (client) ID** → This is your `AZURE_AD_CLIENT_ID`
- **Directory (tenant) ID** → This is your `AZURE_AD_TENANT_ID`

## Step 2: Create Client Secret

### 2.1 Generate Client Secret
1. In your app registration, click **"Certificates & secrets"** in the left sidebar
2. Click the **"Client secrets"** tab
3. Click **"+ New client secret"**
4. Add description: `HR Tool Authentication Secret`
5. Set expiration: **24 months** (or your preference)
6. Click **"Add"**

### 2.2 Copy Secret Value
⚠️ **IMPORTANT:** Copy the **Value** immediately and save it securely. This is your `AZURE_AD_CLIENT_SECRET`. You cannot view it again!

## Step 3: Configure API Permissions

### 3.1 Add Required Permissions
1. In your app registration, click **"API permissions"** in the left sidebar
2. Click **"+ Add a permission"**
3. Select **"Microsoft Graph"**
4. Select **"Delegated permissions"**
5. Add the following permissions:
   - `User.Read` (should already be present)
   - `GroupMember.Read.All`

### 3.2 Grant Admin Consent
1. Click **"Grant admin consent for [Your Organization]"**
2. Confirm by clicking **"Yes"**
3. Verify that the **Status** shows **"Granted for [Your Organization]"** with green checkmarks

## Step 4: Create Security Group

### 4.1 Create New Group
1. In Azure AD, click **"Groups"** in the left sidebar
2. Click **"+ New group"**
3. Configure the group:
   - **Group type:** Security
   - **Group name:** `HR-Tool-Users`
   - **Group description:** `Users authorized to access HR Candidate Management Tool`
   - **Membership type:** Assigned
4. Click **"Create"**

### 4.2 Add Members to Group
1. Open the newly created group
2. Click **"Members"** in the left sidebar
3. Click **"+ Add members"**
4. Search for and select users who should have access to the HR tool
5. Click **"Select"**

### 4.3 Get Group ID
1. In the group overview page, copy the **Object ID**
2. This is your `AZURE_AD_AUTHORIZED_GROUP_ID`

## Step 5: Configure Redirect URIs

### 5.1 Add Production URI
1. In your app registration, click **"Authentication"** in the left sidebar
2. Under **Web** → **Redirect URIs**, ensure you have:
   - `https://YOUR-APP-NAME.azurewebsites.net`

### 5.2 Add Development URI (Optional)
For local development, you can also add:
- `http://localhost:8501`

### 5.3 Configure Advanced Settings
In the **Authentication** section:
1. **Access tokens:** ✅ Check this box
2. **ID tokens:** ✅ Check this box
3. Click **"Save"**

## Step 6: Set Environment Variables

Add these secrets to your GitHub repository or Azure App Service:

| Variable Name | Value | Source |
|---------------|-------|---------|
| `AZURE_AD_CLIENT_ID` | Application (client) ID | From Step 1.3 |
| `AZURE_AD_CLIENT_SECRET` | Client secret value | From Step 2.2 |
| `AZURE_AD_TENANT_ID` | Directory (tenant) ID | From Step 1.3 |
| `AZURE_AD_REDIRECT_URI` | Your app URL | `https://your-app-name.azurewebsites.net` |
| `AZURE_AD_AUTHORIZED_GROUP_ID` | Group Object ID | From Step 4.3 |

### 6.1 For GitHub Actions
Add these as repository secrets in GitHub:
1. Go to your repository → **Settings** → **Secrets and variables** → **Actions**
2. Click **"New repository secret"** for each variable

### 6.2 For Azure App Service
Configure directly in Azure:
```bash
az webapp config appsettings set \
  --resource-group YOUR_RESOURCE_GROUP \
  --name YOUR_APP_NAME \
  --settings \
  AZURE_AD_CLIENT_ID="your-client-id" \
  AZURE_AD_CLIENT_SECRET="your-client-secret" \
  AZURE_AD_TENANT_ID="your-tenant-id" \
  AZURE_AD_REDIRECT_URI="https://your-app-name.azurewebsites.net" \
  AZURE_AD_AUTHORIZED_GROUP_ID="your-group-id"
```

## Step 7: Test Authentication

### 7.1 Deploy and Test
1. Deploy your application with the new authentication code
2. Navigate to your application URL
3. You should see the new landing page with "Sign in with Microsoft" button

### 7.2 Verify Authentication Flow
1. Click **"Sign in with Microsoft"**
2. Enter your organizational credentials
3. If you're in the authorized group, you should be redirected to the main application
4. If not in the group, you should see an "Unauthorized Access" message

### 7.3 Test Group Authorization
1. Remove a test user from the `HR-Tool-Users` group
2. Have them try to authenticate
3. They should see the unauthorized access message
4. Add them back to the group and verify they can access the application

## Step 8: Optional Configuration

### 8.1 Custom Branding (Optional)
1. In your app registration, click **"Branding & properties"**
2. Add your organization's logo and branding
3. Set **Home page URL** to your application URL

### 8.2 Token Configuration (Optional)
1. Click **"Token configuration"**
2. Add optional claims if needed for additional user information

### 8.3 Conditional Access (Advanced)
Consider setting up conditional access policies for additional security:
1. Go to **Azure AD** → **Security** → **Conditional Access**
2. Create policies based on your organization's requirements

## Troubleshooting

### Common Issues

#### 1. "AADSTS50011: The reply URL specified in the request does not match..."
**Solution:** Ensure the redirect URI in your app registration exactly matches your application URL.

#### 2. "Insufficient privileges to complete the operation"
**Solution:** Ensure you have admin consent for the required API permissions.

#### 3. User sees "Unauthorized Access" but is in the group
**Solution:** 
- Verify the group Object ID is correct
- Check that admin consent was granted
- Ensure the user is directly in the group (not nested)

#### 4. Authentication not working locally
**Solution:** Add `http://localhost:8501` to redirect URIs for development.

### Verification Commands

Test your configuration:

```bash
# Test if app registration exists
az ad app list --display-name "HR Candidate Management Tool"

# Check group members
az ad group member list --group "HR-Tool-Users" --output table

# Verify app permissions
az ad app permission list --id YOUR_CLIENT_ID
```

## Security Best Practices

1. **Regular Secret Rotation:** Rotate client secrets every 12-24 months
2. **Group Management:** Regularly review group membership
3. **Audit Logs:** Monitor authentication logs in Azure AD
4. **Conditional Access:** Implement appropriate conditional access policies
5. **Privileged Access:** Use Privileged Identity Management (PIM) for admin roles

## Next Steps

After successful setup:

1. **User Training:** Train authorized users on the new authentication process
2. **Documentation:** Update your internal documentation with the new login process
3. **Monitoring:** Set up alerts for authentication failures
4. **Backup Access:** Ensure multiple users have access to manage the app registration

Your HR Candidate Management Tool now has enterprise-grade authentication with Microsoft Entra ID! 🎉

## Support

If you encounter issues:
1. Check Azure AD sign-in logs for detailed error information
2. Review the application logs for authentication errors
3. Consult Microsoft's [Azure AD documentation](https://docs.microsoft.com/en-us/azure/active-directory/)
4. Contact your Azure administrator for assistance