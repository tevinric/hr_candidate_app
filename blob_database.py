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
        self.force_download_on_next_connection = False
        
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
        
        # Download initial database - FORCE DOWNLOAD FROM CLOUD
        self._download_database(force=True)
        
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
    
    def _download_database(self, force: bool = False) -> bool:
        """Download database from blob storage to local path"""
        try:
            # If force is True, always download. Otherwise check if local exists and is recent
            if not force and os.path.exists(self.local_db_path):
                # Check if local database is recent (less than 5 minutes old)
                local_age = time.time() - os.path.getmtime(self.local_db_path)
                if local_age < 300:  # 5 minutes
                    logging.info("Using recent local database copy")
                    return True
            
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
            
            # Download to a temporary file first, then move to final location
            temp_path = self.local_db_path + ".tmp"
            
            with open(temp_path, "wb") as download_file:
                download_file.write(blob_client.download_blob().readall())
            
            # Move temp file to final location
            if os.path.exists(self.local_db_path):
                os.remove(self.local_db_path)
            os.rename(temp_path, self.local_db_path)
            
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
            if not os.path.exists(self.local_db_path):
                self._create_initial_database()
            return False
    
    def _upload_database(self, force: bool = False) -> bool:
        """Upload local database to blob storage"""
        if self.is_syncing and not force:
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
                
                # Upload database file with retry logic
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        with open(self.local_db_path, "rb") as data:
                            blob_client.upload_blob(data, overwrite=True)
                        break
                    except Exception as e:
                        if attempt == max_retries - 1:
                            raise e
                        logging.warning(f"Upload attempt {attempt + 1} failed, retrying: {str(e)}")
                        time.sleep(1)
                
                self.last_sync_time = datetime.now()
                logging.info("Database uploaded successfully to blob storage")
                return True
                
        except Exception as e:
            logging.error(f"Failed to upload database: {str(e)}")
            return False
        finally:
            self.is_syncing = False
    
    def _create_initial_database(self):
        """Create initial database with required tables including comments field"""
        os.makedirs(os.path.dirname(self.local_db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.local_db_path)
        cursor = conn.cursor()
        
        # Create candidates table with comments field
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
                comments TEXT,    -- New comments field
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
        self._upload_database(force=True)
        logging.info("Initial database created and uploaded with comments field")
    
    def _start_auto_sync(self):
        """Start automatic sync in background thread"""
        def sync_worker():
            while True:
                try:
                    time.sleep(Config.SYNC_INTERVAL_SECONDS)
                    if not self.is_syncing:
                        success = self._upload_database()
                        self._log_sync_operation('upload', 'success' if success else 'failed')
                except Exception as e:
                    logging.error(f"Auto-sync error: {str(e)}")
                    self._log_sync_operation('upload', 'failed', str(e))
        
        sync_thread = threading.Thread(target=sync_worker, daemon=True)
        sync_thread.start()
        logging.info("Auto-sync started")
    
    def _log_sync_operation(self, sync_type: str, status: str, message: str = ""):
        """Log sync operation to database"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO sync_log (sync_type, status, message)
                VALUES (?, ?, ?)
            ''', (sync_type, status, message))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logging.error(f"Failed to log sync operation: {str(e)}")
    
    def get_connection(self) -> sqlite3.Connection:
        """Get SQLite connection to local database"""
        # Force download if flagged or if local database doesn't exist
        if self.force_download_on_next_connection or not os.path.exists(self.local_db_path):
            self._download_database(force=True)
            self.force_download_on_next_connection = False
        
        return sqlite3.connect(self.local_db_path)
    
    def sync_to_blob(self, force: bool = False) -> bool:
        """Manually sync local database to blob storage - BLOCKING operation"""
        success = self._upload_database(force=force)
        
        # Wait for completion and verify
        if success:
            self._log_sync_operation('upload', 'success')
            logging.info("Sync to blob completed successfully")
        else:
            self._log_sync_operation('upload', 'failed')
            logging.error("Sync to blob failed")
        
        return success
    
    def sync_from_blob(self, force: bool = True) -> bool:
        """Manually sync database from blob storage"""
        success = self._download_database(force=force)
        
        if success:
            self._log_sync_operation('download', 'success')
            logging.info("Sync from blob completed successfully")
        else:
            self._log_sync_operation('download', 'failed')
            logging.error("Sync from blob failed")
        
        return success
    
    def force_refresh(self) -> bool:
        """Force refresh database from blob storage (lose local changes)"""
        try:
            if os.path.exists(self.local_db_path):
                os.remove(self.local_db_path)
            return self._download_database(force=True)
        except Exception as e:
            logging.error(f"Failed to force refresh: {str(e)}")
            return False
    
    def force_download_on_next_connection_flag(self):
        """Flag to force download from cloud on next database connection"""
        self.force_download_on_next_connection = True
        logging.info("Flagged for forced download on next connection")
    
    def get_sync_status(self) -> dict:
        """Get sync status information"""
        return {
            'last_sync_time': self.last_sync_time,
            'is_syncing': self.is_syncing,
            'local_db_exists': os.path.exists(self.local_db_path),
            'local_db_size': os.path.getsize(self.local_db_path) if os.path.exists(self.local_db_path) else 0,
            'force_download_flagged': self.force_download_on_next_connection
        }
    
    def get_recent_sync_logs(self, limit: int = 10) -> list:
        """Get recent sync operation logs"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT sync_time, sync_type, status, message 
                FROM sync_log 
                ORDER BY sync_time DESC 
                LIMIT ?
            ''', (limit,))
            
            logs = cursor.fetchall()
            conn.close()
            
            return [
                {
                    'sync_time': log[0],
                    'sync_type': log[1],
                    'status': log[2],
                    'message': log[3]
                }
                for log in logs
            ]
            
        except Exception as e:
            logging.error(f"Failed to get sync logs: {str(e)}")
            return []
    
    def cleanup(self):
        """Cleanup local database file"""
        try:
            # Final sync before cleanup
            self._upload_database(force=True)
            
            if os.path.exists(self.local_db_path):
                os.remove(self.local_db_path)
                logging.info("Local database cleaned up")
        except Exception as e:
            logging.error(f"Failed to cleanup: {str(e)}")