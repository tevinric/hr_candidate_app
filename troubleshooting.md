# HR Candidate Management Tool - Troubleshooting Guide

This guide covers common issues and their solutions for the HR Candidate Management Tool.

## 🔧 General Troubleshooting Steps

### 1. Check Application Status
```bash
# Check if the web app is running
az webapp show --name YOUR_APP_NAME --resource-group YOUR_RESOURCE_GROUP --query state

# Check application logs
az webapp log tail --name YOUR_APP_NAME --resource-group YOUR_RESOURCE_GROUP

# Download logs for analysis
az webapp log download --name YOUR_APP_NAME --resource-group YOUR_RESOURCE_GROUP
```

### 2. Verify Configuration
```bash
# Check app settings
az webapp config appsettings list --name YOUR_APP_NAME --resource-group YOUR_RESOURCE_GROUP

# Test connectivity to storage
az storage container list --connection-string "YOUR_CONNECTION_STRING"

# Test OpenAI endpoint
curl -H "api-key: YOUR_API_KEY" "YOUR_OPENAI_ENDPOINT/openai/deployments?api-version=2024-02-15-preview"
```

## 🚨 Common Issues and Solutions

### Issue 1: Application Won't Start

**Symptoms:**
- Web app shows "Application Error" or "Service Unavailable"
- Container fails to start
- 502/503 HTTP errors

**Possible Causes & Solutions:**

#### A. Missing Environment Variables
```bash
# Check if required variables are set
az webapp config appsettings list --name YOUR_APP_NAME --resource-group YOUR_RESOURCE_GROUP | grep -E "(AZURE_STORAGE|AZURE_OPENAI)"

# Add missing variables
az webapp config appsettings set \
  --name YOUR_APP_NAME \
  --resource-group YOUR_RESOURCE_GROUP \
  --settings AZURE_STORAGE_CONNECTION_STRING="your_connection_string"
```

#### B. Container Registry Authentication
```bash
# Verify ACR credentials
az acr credential show --name YOUR_ACR_NAME

# Update web app with correct credentials
az webapp config container set \
  --name YOUR_APP_NAME \
  --resource-group YOUR_RESOURCE_GROUP \
  --docker-registry-server-user YOUR_ACR_USERNAME \
  --docker-registry-server-password YOUR_ACR_PASSWORD
```

#### C. Invalid Container Image
```bash
# Check if image exists in ACR
az acr repository list --name YOUR_ACR_NAME

# Pull latest image
az acr repository show-tags --name YOUR_ACR_NAME --repository hr-candidate-app

# Force restart with latest image
az webapp restart --name YOUR_APP_NAME --resource-group YOUR_RESOURCE_GROUP
```

**Fix Steps:**
1. Check application logs for specific error messages
2. Verify all environment variables are correctly set
3. Ensure container image is accessible
4. Restart the application

### Issue 2: CV Processing Fails

**Symptoms:**
- "Failed to process CV with AI" error
- OpenAI API errors
- CV upload completes but extraction fails

**Possible Causes & Solutions:**

#### A. OpenAI API Issues
```bash
# Test OpenAI endpoint manually
curl -X POST "YOUR_OPENAI_ENDPOINT/openai/deployments/gpt-4o-mini/chat/completions?api-version=2024-02-15-preview" \
  -H "api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Hello"}],"max_tokens":10}'
```

**Common fixes:**
- Verify API key is correct and not expired
- Check if the deployment name matches exactly
- Ensure sufficient quota in OpenAI service
- Verify the model is deployed and available

#### B. PDF Processing Issues
**Common fixes:**
- Ensure PDF is not password-protected
- Check file size (should be under 10MB)
- Verify PDF is not corrupted
- Try with a different PDF file

#### C. Rate Limiting
**Symptoms:** HTTP 429 errors
**Fix:** Implement retry logic or increase OpenAI quota

```python
# Add to cv_processor.py for retry logic
import time
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def process_cv_with_openai(self, cv_text):
    # Existing processing code
    pass
```

### Issue 3: Database Issues

**Symptoms:**
- "Failed to save candidate" errors
- Search returns no results
- Data corruption

**Possible Causes & Solutions:**

#### A. Write Permission Issues
```bash
# Check file system permissions in container
# Add to Dockerfile:
RUN chmod 777 /home/data
```

#### B. Database Corruption
**Fix Steps:**
1. Create manual backup of current database
2. Restore from latest backup
3. Test application functionality

```bash
# Using Streamlit dashboard:
# 1. Go to Dashboard tab
# 2. Click "Restore from Latest Backup"
# 3. Verify data integrity
```

#### C. SQLite Lock Issues
**Symptoms:** "Database is locked" errors
**Fix:** Restart the application to release locks

### Issue 4: Backup Failures

**Symptoms:**
- "Backup failed" messages
- No recent backups in blob storage
- Restore operations fail

**Possible Causes & Solutions:**

#### A. Storage Account Issues
```bash
# Test storage connectivity
az storage blob list --container-name hr-backups --connection-string "YOUR_CONNECTION_STRING"

# Verify container exists
az storage container exists --name hr-backups --connection-string "YOUR_CONNECTION_STRING"

# Create container if missing
az storage container create --name hr-backups --connection-string "YOUR_CONNECTION_STRING"
```

#### B. Incorrect Connection String
**Fix:** Verify connection string format and regenerate if needed

```bash
# Get correct connection string
az storage account show-connection-string --name YOUR_STORAGE_ACCOUNT --resource-group YOUR_RESOURCE_GROUP
```

#### C. Storage Account Access
**Fix:** Ensure storage account allows blob access

```bash
# Check storage account properties
az storage account show --name YOUR_STORAGE_ACCOUNT --resource-group YOUR_RESOURCE_GROUP
```

### Issue 5: Search Functionality Issues

**Symptoms:**
- Search returns no results when data exists
- Job description matching doesn't work
- Slow search performance

**Possible Causes & Solutions:**

#### A. Data Format Issues
**Fix:** Check if candidate data is properly formatted in database

```sql
-- Connect to database and check data
SELECT name, skills, experience FROM candidates LIMIT 5;
```

#### B. OpenAI Processing for Job Descriptions
**Fix:** Same as CV processing issues - check OpenAI connectivity

#### C. Search Logic Issues
**Fix:** Check search criteria formatting and case sensitivity

### Issue 6: GitHub Actions Deployment Fails

**Symptoms:**
- Build fails in GitHub Actions
- Deployment fails
- Container doesn't update

**Possible Causes & Solutions:**

#### A. Missing GitHub Secrets
**Fix:** Ensure all required secrets are set:
- AZURE_CREDENTIALS
- ACR_USERNAME
- ACR_PASSWORD
- AZURE_RESOURCE_GROUP
- AZURE_STORAGE_CONNECTION_STRING
- AZURE_OPENAI_ENDPOINT
- AZURE_OPENAI_API_KEY

#### B. Service Principal Issues
```bash
# Recreate service principal
az ad sp create-for-rbac --name "hr-tool-deploy" --role contributor --scopes /subscriptions/SUBSCRIPTION_ID/resourceGroups/RESOURCE_GROUP --sdk-auth
```

#### C. Docker Build Issues
**Fix:** Check Dockerfile and requirements.txt for syntax errors

### Issue 7: Performance Issues

**Symptoms:**
- Slow page loading
- CV processing takes too long
- Search results delayed

**Possible Causes & Solutions:**

#### A. Insufficient Resources
```bash
# Scale up App Service Plan
az appservice plan update --name YOUR_PLAN --resource-group YOUR_RESOURCE_GROUP --sku B2
```

#### B. Database Size
**Fix:** Archive old candidate records or optimize queries

#### C. Large PDF Files
**Fix:** Implement file size limits and compression

## 🔍 Diagnostic Commands

### Check Application Health
```bash
# Application health endpoint
curl -f https://YOUR_APP_NAME.azurewebsites.net/_stcore/health

# Check response time
curl -w "@curl-format.txt" -o /dev/null -s "https://YOUR_APP_NAME.azurewebsites.net"
```

### Monitor Resource Usage
```bash
# Check App Service metrics
az monitor metrics list --resource /subscriptions/SUBSCRIPTION_ID/resourceGroups/RESOURCE_GROUP/providers/Microsoft.Web/sites/YOUR_APP_NAME --metric "CpuPercentage,MemoryPercentage"

# Check storage usage
az storage account show-usage --name YOUR_STORAGE_ACCOUNT
```

### Debug Database Issues
```python
# Connect to database and run diagnostics
import sqlite3

conn = sqlite3.connect('/path/to/database.db')
cursor = conn.cursor()

# Check table structure
cursor.execute("PRAGMA table_info(candidates)")
print("Table structure:", cursor.fetchall())

# Check data count
cursor.execute("SELECT COUNT(*) FROM candidates")
print("Total candidates:", cursor.fetchone()[0])

# Check for corrupted data
cursor.execute("PRAGMA integrity_check")
print("Integrity check:", cursor.fetchall())

conn.close()
```

## 📝 Log Analysis

### Common Error Messages and Solutions

#### "ModuleNotFoundError"
**Cause:** Missing Python dependencies
**Fix:** Update requirements.txt and rebuild container

#### "Connection refused"
**Cause:** Service endpoint not accessible
**Fix:** Check firewall settings and endpoint URLs

#### "Authentication failed"
**Cause:** Invalid credentials
**Fix:** Regenerate API keys and update configuration

#### "Quota exceeded"
**Cause:** OpenAI API quota limits
**Fix:** Increase quota or implement rate limiting

#### "File not found"
**Cause:** Missing files or incorrect paths
**Fix:** Check file paths and container structure

### Enable Debug Logging
```bash
# Enable debug mode
az webapp config appsettings set \
  --name YOUR_APP_NAME \
  --resource-group YOUR_RESOURCE_GROUP \
  --settings DEBUG=True LOG_LEVEL=DEBUG
```

## 🛠️ Recovery Procedures

### Complete Application Reset
1. **Backup current data:**
   ```bash
   # Download current database backup
   az storage blob download --container-name hr-backups --name latest.db --file local_backup.db --connection-string "YOUR_CONNECTION_STRING"
   ```

2. **Redeploy application:**
   ```bash
   # Trigger GitHub Actions deployment
   git commit --allow-empty -m "Force redeploy"
   git push origin main
   ```

3. **Restore data if needed:**
   - Use Streamlit dashboard to restore from backup
   - Or manually upload backup to blob storage

### Database Recovery
1. **Create backup of current state**
2. **Download latest working backup**
3. **Restore through application dashboard**
4. **Verify data integrity**
5. **Test all functionality**

### Configuration Recovery
1. **Export current settings:**
   ```bash
   az webapp config appsettings list --name YOUR_APP_NAME --resource-group YOUR_RESOURCE_GROUP > current_settings.json
   ```

2. **Restore from known good configuration:**
   ```bash
   az webapp config appsettings set --name YOUR_APP_NAME --resource-group YOUR_RESOURCE_GROUP --settings @good_settings.json
   ```

## 🔧 Preventive Measures

### Regular Maintenance Tasks

**Daily:**
- Check application health endpoint
- Monitor error logs
- Verify backup creation

**Weekly:**
- Review storage usage
- Check API quota consumption
- Test core functionality

**Monthly:**
- Update dependencies
- Review and clean old backups
- Performance optimization review

### Monitoring Setup
```bash
# Create alert for application failures
az monitor metrics alert create \
  --name "HR Tool Failures" \
  --resource-group YOUR_RESOURCE_GROUP \
  --scopes "/subscriptions/SUBSCRIPTION_ID/resourceGroups/RESOURCE_GROUP/providers/Microsoft.Web/sites/YOUR_APP_NAME" \
  --condition "count static gt 5 PT5M" \
  --description "Alert when app has failures"

# Create alert for high CPU usage
az monitor metrics alert create \
  --name "HR Tool High CPU" \
  --resource-group YOUR_RESOURCE_GROUP \
  --scopes "/subscriptions/SUBSCRIPTION_ID/resourceGroups/RESOURCE_GROUP/providers/Microsoft.Web/sites/YOUR_APP_NAME" \
  --condition "avg CpuPercentage static gt 80 PT10M" \
  --description "Alert when CPU usage is high"
```

## 📞 Getting Help

### When to Escalate
- Data corruption or loss
- Security breaches
- Persistent performance issues
- Multiple component failures

### Information to Gather
Before seeking help, collect:
1. Application logs (last 24 hours)
2. Error messages and timestamps
3. Steps to reproduce the issue
4. Current configuration settings
5. Recent changes made to the system

### Support Resources
1. **Azure Support:** For infrastructure issues
2. **OpenAI Support:** For API-related problems
3. **GitHub Issues:** For application bugs
4. **Documentation:** Check setup and API guides

## 🔄 Version Updates

### Updating the Application
1. **Test in development environment**
2. **Create full backup**
3. **Deploy to staging first**
4. **Monitor for issues**
5. **Deploy to production**
6. **Verify functionality**

### Rollback Procedure
1. **Identify last known good deployment**
2. **Revert to previous container image**
3. **Restore database backup if needed**
4. **Verify system stability**

Remember: Always backup before making changes and test thoroughly in a development environment first!
