import sqlite3
import os
import logging
import tempfile
import threading
import time
from datetime import datetime
from typing import Optional, Tuple
from azure.storage.blob import BlobServiceClient, BlobClient
from azure.core.exceptions import ResourceNotFoundError
from config import Config

class BlobDatabaseManager:
    """Manages SQLite database stored in Azure Blob Storage"""
    
    def __init__(self):
        self.blob_service_client = None
        self.local_db_path = Config.LOCAL_DB_PATH
        self.db_container = Config.DB_CONTAINER
        self.db_blob_name = Config.DB_BLOB_NAME
        self.last_sync_time = None
        self.sync_lock = threading.Lock()
        self.is_syncing = False
        
        # Initialize blob storage client
        if Config.AZURE_STORAGE_CONNECTION_STRING:
            try:
                self.blob_service_client = BlobServiceClient.from_connection_string(
                    Config.AZURE_STORAGE_CONNECTION_STRING
                )
                self._ensure_container_exists()
                logging.info("Blob storage client initialized successfully")
            except Exception as e:
                logging.error(f"Failed to initialize blob storage: {str(e)}")
                raise
        else:
            raise ValueError("AZURE_STORAGE_CONNECTION_STRING is required")
        
        # Download initial database
        self._download_database()
        
        # Start auto-sync if enabled
        if Config.AUTO_SYNC_ENABLED:
            self._start_auto_sync()
    
    def _ensure_container_exists(self):
        """Ensure the database container exists"""
        try:
            container_client = self.blob_service_client.get_container_client(self.db_container)
            if not container_client.exists():
                container_client.create_container()
                logging.info(f"Created database container: {self.db_container}")
        except Exception as e:
            logging.error(f"Failed to ensure container exists: {str(e)}")
            raise
    
    def _download_database(self) -> bool:
        """Download database from blob storage to local path"""
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.db_container,
                blob=self.db_blob_name
            )
            
            # Check if blob exists
            if not blob_client.exists():
                logging.info("Database blob doesn't exist, creating new database")
                self._create_initial_database()
                return True
            
            # Download blob to local file
            os.makedirs(os.path.dirname(self.local_db_path), exist_ok=True)
            
            with open(self.local_db_path, "wb") as download_file:
                download_file.write(blob_client.download_blob().readall())
            
            self.last_sync_time = datetime.now()
            logging.info(f"Database downloaded successfully to {self.local_db_path}")
            return True
            
        except ResourceNotFoundError:
            logging.info("Database blob not found, creating new database")
            self._create_initial_database()
            return True
        except Exception as e:
            logging.error(f"Failed to download database: {str(e)}")
            # Create local database if download fails
            self._create_initial_database()
            return False
    
    def _upload_database(self) -> bool:
        """Upload local database to blob storage"""
        if self.is_syncing:
            logging.debug("Sync already in progress, skipping upload")
            return False
            
        try:
            with self.sync_lock:
                self.is_syncing = True
                
                if not os.path.exists(self.local_db_path):
                    logging.error(f"Local database not found: {self.local_db_path}")
                    return False
                
                blob_client = self.blob_service_client.get_blob_client(
                    container=self.db_container,
                    blob=self.db_blob_name
                )
                
                # Upload database file
                with open(self.local_db_path, "rb") as data:
                    blob_client.upload_blob(data, overwrite=True)
                
                self.last_sync_time = datetime.now()
                logging.info("Database uploaded successfully to blob storage")
                return True
                
        except Exception as e:
            logging.error(f"Failed to upload database: {str(e)}")
            return False
        finally:
            self.is_syncing = False
    
    def _create_initial_database(self):
        """Create initial database with required tables"""
        os.makedirs(os.path.dirname(self.local_db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.local_db_path)
        cursor = conn.cursor()
        
        # Create candidates table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                current_role TEXT,
                email TEXT UNIQUE,
                phone TEXT,
                notice_period TEXT,
                current_salary TEXT,
                industry TEXT,
                desired_salary TEXT,
                highest_qualification TEXT,
                experience TEXT,  -- JSON string
                skills TEXT,      -- JSON string
                qualifications TEXT,  -- JSON string
                achievements TEXT,    -- JSON string
                special_skills TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create backup log table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS backup_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                backup_name TEXT NOT NULL,
                backup_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT NOT NULL,
                file_size INTEGER
            )
        ''')
        
        # Create sync log table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sync_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sync_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sync_type TEXT NOT NULL,  -- 'upload' or 'download'
                status TEXT NOT NULL,     -- 'success' or 'failed'
                message TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # Upload initial database
        self._upload_database()
        logging.info("Initial database created and uploaded")
    
    def _start_auto_sync(self):
        """Start automatic sync in background thread"""
        def sync_worker():
            while True:
                try:
                    time.sleep(Config.SYNC_INTERVAL_SECONDS)
                    if not self.is_syncing:
                        self._upload_database()
                except Exception as e:
                    logging.error(f"Auto-sync error: {str(e)}")
        
        sync_thread = threading.Thread(target=sync_worker, daemon=True)
        sync_thread.start()
        logging.info("Auto-sync started")
    
    def get_connection(self) -> sqlite3.Connection:
        """Get SQLite connection to local database"""
        if not os.path.exists(self.local_db_path):
            self._download_database()
        
        return sqlite3.connect(self.local_db_path)
    
    def sync_to_blob(self) -> bool:
        """Manually sync local database to blob storage"""
        return self._upload_database()
    
    def sync_from_blob(self) -> bool:
        """Manually sync database from blob storage"""
        return self._download_database()
    
    def force_refresh(self) -> bool:
        """Force refresh database from blob storage (lose local changes)"""
        try:
            if os.path.exists(self.local_db_path):
                os.remove(self.local_db_path)
            return self._download_database()
        except Exception as e:
            logging.error(f"Failed to force refresh: {str(e)}")
            return False
    
    def get_sync_status(self) -> dict:
        """Get sync status information"""
        return {
            'last_sync_time': self.last_sync_time,
            'is_syncing': self.is_syncing,
            'local_db_exists': os.path.exists(self.local_db_path),
            'local_db_size': os.path.getsize(self.local_db_path) if os.path.exists(self.local_db_path) else 0
        }
    
    def cleanup(self):
        """Cleanup local database file"""
        try:
            # Final sync before cleanup
            self._upload_database()
            
            if os.path.exists(self.local_db_path):
                os.remove(self.local_db_path)
                logging.info("Local database cleaned up")
        except Exception as e:
            logging.error(f"Failed to cleanup: {str(e)}")