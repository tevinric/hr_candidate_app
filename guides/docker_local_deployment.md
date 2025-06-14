# QUICK START - HR Candidate Management Tool

# 1. Build the image
docker build -t hr-candidate-app .

# 2. Export your environment variables (replace with actual values)
export AZURE_STORAGE_CONNECTION_STRING="your_storage_connection_string_here"
export AZURE_OPENAI_ENDPOINT="https://your-openai-service.openai.azure.com"
export AZURE_OPENAI_API_KEY="your_openai_api_key_here"
export AZURE_OPENAI_API_VERSION="2024-02-15-preview"
export AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4o-mini"
export DB_CONTAINER="app-data"
export DB_BLOB_NAME="hr_candidates.db"
export LOCAL_DB_PATH="/tmp/hr_candidates.db"
export BACKUP_CONTAINER="hr-backups"
export AUTO_BACKUP_ENABLED="True"
export LOG_LEVEL="INFO"

# 3. Verify your exports (optional)
echo "Storage: ${AZURE_STORAGE_CONNECTION_STRING:0:50}..."
echo "OpenAI Endpoint: $AZURE_OPENAI_ENDPOINT"

# 4. Run the container
docker run -d \
  --name hr-candidate-tool \
  -e AZURE_STORAGE_CONNECTION_STRING="$AZURE_STORAGE_CONNECTION_STRING" \
  -e AZURE_OPENAI_ENDPOINT="$AZURE_OPENAI_ENDPOINT" \
  -e AZURE_OPENAI_API_KEY="$AZURE_OPENAI_API_KEY" \
  -e AZURE_OPENAI_API_VERSION="$AZURE_OPENAI_API_VERSION" \
  -e AZURE_OPENAI_DEPLOYMENT_NAME="$AZURE_OPENAI_DEPLOYMENT_NAME" \
  -e DB_CONTAINER="$DB_CONTAINER" \
  -e DB_BLOB_NAME="$DB_BLOB_NAME" \
  -e LOCAL_DB_PATH="$LOCAL_DB_PATH" \
  -e BACKUP_CONTAINER="$BACKUP_CONTAINER" \
  -e AUTO_BACKUP_ENABLED="$AUTO_BACKUP_ENABLED" \
  -e LOG_LEVEL="$LOG_LEVEL" \
  -p 8501:8501 \
  -v hr-data:/home/data \
  --restart unless-stopped \
  hr-candidate-app

# 5. Check if it's running
docker logs hr-candidate-tool

# 6. Access the application
echo "Application available at: http://localhost:8501"

# 7. Optional: View environment variables in container
docker exec hr-candidate-tool env | grep AZURE
