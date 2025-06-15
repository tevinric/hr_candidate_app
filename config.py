import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file if it exists

class Config:
    """Configuration class for HR Candidate Management Tool"""
    
    # Database Configuration
    DB_PATH: str = os.environ.get('DB_PATH', '/home/data/hr_candidates.db')  # Legacy path for migration
    
    # Database in Blob Storage Configuration
    DB_CONTAINER: str = os.environ.get('DB_CONTAINER', 'appdata')
    DB_BLOB_NAME: str = os.environ.get('DB_BLOB_NAME', 'hr_candidates.db')
    LOCAL_DB_PATH: str = os.environ.get('LOCAL_DB_PATH', '/tmp/hr_candidates.db')
    
    # Database sync settings
    AUTO_SYNC_ENABLED: bool = os.environ.get('AUTO_SYNC_ENABLED', 'True').lower() == 'true'
    SYNC_INTERVAL_SECONDS: int = int(os.environ.get('SYNC_INTERVAL_SECONDS', '300'))  # 5 minutes
    
    # Azure Blob Storage Configuration
    AZURE_STORAGE_CONNECTION_STRING: Optional[str] = os.environ.get('AZURE_STORAGE_CONNECTION_STRING')
    BACKUP_CONTAINER: str = os.environ.get('BACKUP_CONTAINER', 'appdatabackups')

    # Azure OpenAI Configuration
    AZURE_OPENAI_ENDPOINT: Optional[str] = os.environ.get('AZURE_OPENAI_ENDPOINT')
    AZURE_OPENAI_API_KEY: Optional[str] = os.environ.get('AZURE_OPENAI_API_KEY')
    AZURE_OPENAI_API_VERSION: str = os.environ.get('AZURE_OPENAI_API_VERSION', '2024-02-15-preview')
    AZURE_OPENAI_DEPLOYMENT_NAME: str = os.environ.get('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4o-mini')
    
    # Authentication Configuration - NEW SECTION
    AZURE_AD_CLIENT_ID: Optional[str] = os.environ.get('AZURE_AD_CLIENT_ID')
    AZURE_AD_CLIENT_SECRET: Optional[str] = os.environ.get('AZURE_AD_CLIENT_SECRET')
    AZURE_AD_TENANT_ID: Optional[str] = os.environ.get('AZURE_AD_TENANT_ID')
    AZURE_AD_REDIRECT_URI: str = os.environ.get('AZURE_AD_REDIRECT_URI', 'https://your-app-name.azurewebsites.net')
    AZURE_AD_AUTHORIZED_GROUP_ID: Optional[str] = os.environ.get('AZURE_AD_AUTHORIZED_GROUP_ID')
    
    # Application Configuration
    APP_NAME: str = "HR Candidate Management Tool"
    APP_VERSION: str = "1.1.0"  # Updated version for blob storage
    DEBUG: bool = os.environ.get('DEBUG', 'False').lower() == 'true'

    # Logging Configuration
    LOG_LEVEL: str = os.environ.get('LOG_LEVEL', 'INFO')

    # Backup Configuration
    AUTO_BACKUP_ENABLED: bool = os.environ.get('AUTO_BACKUP_ENABLED', 'True').lower() == 'true'
    BACKUP_RETENTION_DAYS: int = int(os.environ.get('BACKUP_RETENTION_DAYS', '30'))

    # File Upload Configuration
    MAX_FILE_SIZE_MB: int = int(os.environ.get('MAX_FILE_SIZE_MB', '10'))
    ALLOWED_EXTENSIONS: list = ['pdf']
    
    # Search Configuration
    MAX_SEARCH_RESULTS: int = int(os.environ.get('MAX_SEARCH_RESULTS', '100'))

    @classmethod
    def validate_configuration(cls) -> bool:
        """Validate that required configuration is present"""
        required_configs = [
            ('AZURE_STORAGE_CONNECTION_STRING', cls.AZURE_STORAGE_CONNECTION_STRING),
            ('AZURE_OPENAI_ENDPOINT', cls.AZURE_OPENAI_ENDPOINT),
            ('AZURE_OPENAI_API_KEY', cls.AZURE_OPENAI_API_KEY),
        ]
        
        # Authentication configs are optional but recommended - UPDATED VALIDATION
        auth_configs = [
            ('AZURE_AD_CLIENT_ID', cls.AZURE_AD_CLIENT_ID),
            ('AZURE_AD_CLIENT_SECRET', cls.AZURE_AD_CLIENT_SECRET),
            ('AZURE_AD_TENANT_ID', cls.AZURE_AD_TENANT_ID),
        ]
        
        missing_configs = []
        for name, value in required_configs:
            if not value:
                missing_configs.append(name)
        
        missing_auth_configs = []
        for name, value in auth_configs:
            if not value:
                missing_auth_configs.append(name)
        
        if missing_configs:
            print(f"Missing required configuration: {', '.join(missing_configs)}")
            
        if missing_auth_configs:
            print(f"Missing authentication configuration (authentication will be disabled): {', '.join(missing_auth_configs)}")
        
        # Only fail validation if core required configs are missing
        return len(missing_configs) == 0
    
    @classmethod
    def get_summary(cls) -> dict:
        """Get configuration summary (without sensitive data)"""
        return {
            'app_name': cls.APP_NAME,
            'app_version': cls.APP_VERSION,
            'debug': cls.DEBUG,
            'legacy_db_path': cls.DB_PATH,
            'db_container': cls.DB_CONTAINER,
            'db_blob_name': cls.DB_BLOB_NAME,
            'local_db_path': cls.LOCAL_DB_PATH,
            'auto_sync_enabled': cls.AUTO_SYNC_ENABLED,
            'sync_interval_seconds': cls.SYNC_INTERVAL_SECONDS,
            'backup_container': cls.BACKUP_CONTAINER,
            'auto_backup_enabled': cls.AUTO_BACKUP_ENABLED,
            'backup_retention_days': cls.BACKUP_RETENTION_DAYS,
            'max_file_size_mb': cls.MAX_FILE_SIZE_MB,
            'max_search_results': cls.MAX_SEARCH_RESULTS,
            'azure_openai_configured': bool(cls.AZURE_OPENAI_ENDPOINT and cls.AZURE_OPENAI_API_KEY),
            'blob_storage_configured': bool(cls.AZURE_STORAGE_CONNECTION_STRING),
            'authentication_configured': bool(cls.AZURE_AD_CLIENT_ID and cls.AZURE_AD_CLIENT_SECRET and cls.AZURE_AD_TENANT_ID),  # NEW
            'azure_ad_redirect_uri': cls.AZURE_AD_REDIRECT_URI  # NEW
        }