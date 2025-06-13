import os
import sqlite3
import logging
import threading
import time
import gzip
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from azure.storage.blob import BlobServiceClient, BlobClient
from azure.core.exceptions import ResourceNotFoundError
from config import Config

@dataclass
class BackupInfo:
    """Information about a backup"""
    name: str
    timestamp: datetime
    size_bytes: int
    backup_type: str  # 'auto', 'manual', 'scheduled'
    status: str  # 'completed', 'failed', 'in_progress'
    compressed: bool
    metadata: Dict[str, Any]

class BackupManager:
    """Comprehensive backup manager for HR Candidate Management Tool"""
    
    def __init__(self, db_manager=None):
        self.db_manager = db_manager
        self.blob_service_client = None
        self.backup_container = Config.BACKUP_CONTAINER
        self.retention_days = Config.BACKUP_RETENTION_DAYS
        self.auto_backup_enabled = Config.AUTO_BACKUP_ENABLED
        
        # Backup state
        self.is_backup_in_progress = False
        self.last_backup_time = None
        self.backup_thread = None
        self.backup_lock = threading.Lock()
        
        # Statistics
        self.backup_stats = {
            'total_backups': 0,
            'successful_backups': 0,
            'failed_backups': 0,
            'last_backup_size': 0,
            'total_backup_size': 0
        }
        
        # Initialize blob storage client
        self._initialize_blob_client()
        
        # Start automatic backup scheduler if enabled
        if self.auto_backup_enabled:
            self._start_backup_scheduler()
    
    def _initialize_blob_client(self):
        """Initialize Azure Blob Storage client"""
        if Config.AZURE_STORAGE_CONNECTION_STRING:
            try:
                self.blob_service_client = BlobServiceClient.from_connection_string(
                    Config.AZURE_STORAGE_CONNECTION_STRING
                )
                self._ensure_backup_container_exists()
                logging.info("Backup manager initialized with Azure Blob Storage")
            except Exception as e:
                logging.error(f"Failed to initialize backup blob storage: {str(e)}")
                raise
        else:
            raise ValueError("AZURE_STORAGE_CONNECTION_STRING is required for backup operations")
    
    def _ensure_backup_container_exists(self):
        """Ensure backup container exists"""
        try:
            container_client = self.blob_service_client.get_container_client(self.backup_container)
            if not container_client.exists():
                container_client.create_container()
                logging.info(f"Created backup container: {self.backup_container}")
        except Exception as e:
            logging.error(f"Failed to ensure backup container exists: {str(e)}")
            raise
    
    def create_backup(self, backup_type: str = 'manual', compress: bool = True, 
                     include_metadata: bool = True) -> Tuple[bool, str, Optional[BackupInfo]]:
        """
        Create a backup of the database
        
        Args:
            backup_type: Type of backup ('manual', 'auto', 'scheduled')
            compress: Whether to compress the backup
            include_metadata: Whether to include metadata
            
        Returns:
            (success, message, backup_info)
        """
        if self.is_backup_in_progress:
            return False, "Backup already in progress", None
        
        with self.backup_lock:
            self.is_backup_in_progress = True
            
            try:
                # Generate backup name
                timestamp = datetime.now()
                backup_name = self._generate_backup_name(timestamp, backup_type, compress)
                
                logging.info(f"Starting {backup_type} backup: {backup_name}")
                
                # Get database path
                if self.db_manager and hasattr(self.db_manager, 'blob_db'):
                    db_path = self.db_manager.blob_db.local_db_path
                else:
                    db_path = Config.DB_PATH
                
                if not os.path.exists(db_path):
                    return False, f"Database file not found: {db_path}", None
                
                # Create backup data
                backup_data = self._create_backup_data(db_path, compress, include_metadata)
                
                if not backup_data:
                    return False, "Failed to create backup data", None
                
                # Upload to blob storage
                success, message = self._upload_backup_to_blob(backup_name, backup_data)
                
                if success:
                    # Create backup info
                    backup_info = BackupInfo(
                        name=backup_name,
                        timestamp=timestamp,
                        size_bytes=len(backup_data),
                        backup_type=backup_type,
                        status='completed',
                        compressed=compress,
                        metadata=self._get_backup_metadata() if include_metadata else {}
                    )
                    
                    # Log backup
                    self._log_backup_operation(backup_info, 'success')
                    
                    # Update statistics
                    self._update_backup_stats(backup_info, True)
                    
                    # Also create/update latest backup
                    self._create_latest_backup(backup_data)
                    
                    self.last_backup_time = timestamp
                    
                    logging.info(f"Backup completed successfully: {backup_name}")
                    return True, f"Backup created successfully: {backup_name}", backup_info
                else:
                    self._log_backup_operation(None, 'failed', message)
                    self._update_backup_stats(None, False)
                    return False, message, None
                    
            except Exception as e:
                error_msg = f"Backup failed: {str(e)}"
                logging.error(error_msg)
                self._log_backup_operation(None, 'failed', error_msg)
                self._update_backup_stats(None, False)
                return False, error_msg, None
            
            finally:
                self.is_backup_in_progress = False
    
    def _generate_backup_name(self, timestamp: datetime, backup_type: str, compress: bool) -> str:
        """Generate backup file name"""
        timestamp_str = timestamp.strftime('%Y%m%d_%H%M%S')
        extension = '.gz' if compress else '.db'
        return f"backup_{backup_type}_{timestamp_str}{extension}"
    
    def _create_backup_data(self, db_path: str, compress: bool, include_metadata: bool) -> Optional[bytes]:
        """Create backup data with optional compression and metadata"""
        try:
            # Read database file
            with open(db_path, 'rb') as db_file:
                db_data = db_file.read()
            
            if include_metadata:
                # Create metadata
                metadata = self._get_backup_metadata()
                
                # Combine metadata and database
                backup_content = {
                    'metadata': metadata,
                    'database': db_data.hex()  # Convert to hex for JSON serialization
                }
                
                # Convert to JSON bytes
                backup_data = json.dumps(backup_content).encode('utf-8')
            else:
                backup_data = db_data
            
            # Compress if requested
            if compress:
                backup_data = gzip.compress(backup_data)
            
            return backup_data
            
        except Exception as e:
            logging.error(f"Failed to create backup data: {str(e)}")
            return None
    
    def _get_backup_metadata(self) -> Dict[str, Any]:
        """Get metadata for the backup"""
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'app_version': Config.APP_VERSION,
            'database_version': '1.0',
            'backup_tool': 'hr_backup_manager'
        }
        
        # Add database statistics if available
        try:
            if self.db_manager:
                stats = self.db_manager.get_dashboard_stats()
                metadata.update({
                    'total_candidates': stats.get('total_candidates', 0),
                    'unique_industries': stats.get('unique_industries', 0),
                    'database_size_mb': stats.get('database_size_mb', 0)
                })
        except Exception as e:
            logging.warning(f"Failed to get database stats for metadata: {str(e)}")
        
        return metadata
    
    def _upload_backup_to_blob(self, backup_name: str, backup_data: bytes) -> Tuple[bool, str]:
        """Upload backup data to blob storage"""
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.backup_container,
                blob=backup_name
            )
            
            # Upload with metadata
            blob_client.upload_blob(
                backup_data, 
                overwrite=True,
                metadata={
                    'backup_type': 'database',
                    'created_at': datetime.now().isoformat(),
                    'size_bytes': str(len(backup_data))
                }
            )
            
            return True, "Backup uploaded successfully"
            
        except Exception as e:
            error_msg = f"Failed to upload backup: {str(e)}"
            logging.error(error_msg)
            return False, error_msg
    
    def _create_latest_backup(self, backup_data: bytes):
        """Create/update the latest backup file"""
        try:
            latest_blob_client = self.blob_service_client.get_blob_client(
                container=self.backup_container,
                blob="latest.db"
            )
            
            # If compressed, decompress for latest backup
            if backup_data.startswith(b'\x1f\x8b'):  # gzip magic number
                try:
                    decompressed_data = gzip.decompress(backup_data)
                    
                    # If it's JSON with metadata, extract database
                    try:
                        content = json.loads(decompressed_data.decode('utf-8'))
                        if 'database' in content:
                            latest_data = bytes.fromhex(content['database'])
                        else:
                            latest_data = decompressed_data
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        latest_data = decompressed_data
                        
                except gzip.BadGzipFile:
                    latest_data = backup_data
            else:
                latest_data = backup_data
            
            latest_blob_client.upload_blob(latest_data, overwrite=True)
            
        except Exception as e:
            logging.warning(f"Failed to create latest backup: {str(e)}")
    
    def restore_from_backup(self, backup_name: Optional[str] = None) -> Tuple[bool, str]:
        """
        Restore database from backup
        
        Args:
            backup_name: Name of backup to restore from. If None, uses latest backup.
            
        Returns:
            (success, message)
        """
        try:
            if backup_name is None:
                backup_name = "latest.db"
            
            logging.info(f"Starting restore from backup: {backup_name}")
            
            # Download backup from blob storage
            backup_data = self._download_backup_from_blob(backup_name)
            
            if not backup_data:
                return False, f"Failed to download backup: {backup_name}"
            
            # Process backup data
            db_data = self._process_backup_data(backup_data)
            
            if not db_data:
                return False, "Failed to process backup data"
            
            # Restore database
            success, message = self._restore_database(db_data)
            
            if success:
                logging.info(f"Database restored successfully from {backup_name}")
                # Force sync if using blob database
                if self.db_manager and hasattr(self.db_manager, 'blob_db'):
                    self.db_manager.blob_db.sync_to_blob()
            
            return success, message
            
        except Exception as e:
            error_msg = f"Restore failed: {str(e)}"
            logging.error(error_msg)
            return False, error_msg
    
    def _download_backup_from_blob(self, backup_name: str) -> Optional[bytes]:
        """Download backup data from blob storage"""
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.backup_container,
                blob=backup_name
            )
            
            if not blob_client.exists():
                logging.error(f"Backup not found: {backup_name}")
                return None
            
            return blob_client.download_blob().readall()
            
        except Exception as e:
            logging.error(f"Failed to download backup {backup_name}: {str(e)}")
            return None
    
    def _process_backup_data(self, backup_data: bytes) -> Optional[bytes]:
        """Process backup data (decompress, extract database)"""
        try:
            # Check if compressed
            if backup_data.startswith(b'\x1f\x8b'):  # gzip magic number
                backup_data = gzip.decompress(backup_data)
            
            # Check if it's JSON with metadata
            try:
                content = json.loads(backup_data.decode('utf-8'))
                if 'database' in content:
                    # Extract database from metadata structure
                    return bytes.fromhex(content['database'])
                else:
                    # Fallback to raw data
                    return backup_data
            except (json.JSONDecodeError, UnicodeDecodeError):
                # Not JSON, treat as raw database
                return backup_data
                
        except Exception as e:
            logging.error(f"Failed to process backup data: {str(e)}")
            return None
    
    def _restore_database(self, db_data: bytes) -> Tuple[bool, str]:
        """Restore database from raw database bytes"""
        try:
            # Determine database path
            if self.db_manager and hasattr(self.db_manager, 'blob_db'):
                db_path = self.db_manager.blob_db.local_db_path
            else:
                db_path = Config.DB_PATH
            
            # Create backup of current database
            if os.path.exists(db_path):
                backup_path = f"{db_path}.restore_backup_{int(time.time())}"
                try:
                    os.rename(db_path, backup_path)
                except Exception as e:
                    logging.warning(f"Failed to backup current database: {str(e)}")
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
            # Write restored database
            with open(db_path, 'wb') as db_file:
                db_file.write(db_data)
            
            # Verify database integrity
            if self._verify_database_integrity(db_path):
                return True, "Database restored successfully"
            else:
                return False, "Restored database failed integrity check"
                
        except Exception as e:
            error_msg = f"Failed to restore database: {str(e)}"
            logging.error(error_msg)
            return False, error_msg
    
    def _verify_database_integrity(self, db_path: str) -> bool:
        """Verify database integrity after restore"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Run integrity check
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            
            conn.close()
            
            return result and result[0] == 'ok'
            
        except Exception as e:
            logging.error(f"Database integrity check failed: {str(e)}")
            return False
    
    def list_backups(self, limit: Optional[int] = None) -> List[BackupInfo]:
        """List available backups"""
        try:
            container_client = self.blob_service_client.get_container_client(self.backup_container)
            
            backups = []
            blob_list = container_client.list_blobs()
            
            for blob in blob_list:
                if blob.name.startswith('backup_') and blob.name != 'latest.db':
                    try:
                        # Parse backup info from blob
                        backup_info = self._parse_backup_info(blob)
                        if backup_info:
                            backups.append(backup_info)
                    except Exception as e:
                        logging.warning(f"Failed to parse backup info for {blob.name}: {str(e)}")
            
            # Sort by timestamp (newest first)
            backups.sort(key=lambda x: x.timestamp, reverse=True)
            
            # Apply limit if specified
            if limit:
                backups = backups[:limit]
            
            return backups
            
        except Exception as e:
            logging.error(f"Failed to list backups: {str(e)}")
            return []
    
    def _parse_backup_info(self, blob) -> Optional[BackupInfo]:
        """Parse backup information from blob metadata"""
        try:
            name_parts = blob.name.split('_')
            if len(name_parts) >= 3:
                backup_type = name_parts[1]
                timestamp_str = '_'.join(name_parts[2:]).split('.')[0]
                timestamp = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
            else:
                backup_type = 'unknown'
                timestamp = blob.last_modified.replace(tzinfo=None)
            
            return BackupInfo(
                name=blob.name,
                timestamp=timestamp,
                size_bytes=blob.size,
                backup_type=backup_type,
                status='completed',
                compressed=blob.name.endswith('.gz'),
                metadata=blob.metadata or {}
            )
            
        except Exception as e:
            logging.warning(f"Failed to parse backup info for {blob.name}: {str(e)}")
            return None
    
    def delete_backup(self, backup_name: str) -> Tuple[bool, str]:
        """Delete a specific backup"""
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.backup_container,
                blob=backup_name
            )
            
            if not blob_client.exists():
                return False, f"Backup not found: {backup_name}"
            
            blob_client.delete_blob()
            logging.info(f"Backup deleted: {backup_name}")
            return True, f"Backup deleted successfully: {backup_name}"
            
        except Exception as e:
            error_msg = f"Failed to delete backup {backup_name}: {str(e)}"
            logging.error(error_msg)
            return False, error_msg
    
    def cleanup_old_backups(self) -> Tuple[int, List[str]]:
        """Clean up backups older than retention period"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            backups = self.list_backups()
            
            deleted_backups = []
            deleted_count = 0
            
            for backup in backups:
                if backup.timestamp < cutoff_date and backup.name != 'latest.db':
                    success, message = self.delete_backup(backup.name)
                    if success:
                        deleted_backups.append(backup.name)
                        deleted_count += 1
                    else:
                        logging.warning(f"Failed to delete old backup {backup.name}: {message}")
            
            logging.info(f"Cleaned up {deleted_count} old backups")
            return deleted_count, deleted_backups
            
        except Exception as e:
            logging.error(f"Failed to cleanup old backups: {str(e)}")
            return 0, []
    
    def get_backup_stats(self) -> Dict[str, Any]:
        """Get backup statistics and status"""
        try:
            backups = self.list_backups()
            
            # Calculate statistics
            total_backups = len(backups)
            total_size = sum(backup.size_bytes for backup in backups)
            
            # Get latest backup info
            latest_backup = backups[0] if backups else None
            
            # Calculate backup frequency
            if len(backups) >= 2:
                time_diff = backups[0].timestamp - backups[-1].timestamp
                avg_interval_hours = time_diff.total_seconds() / 3600 / (len(backups) - 1)
            else:
                avg_interval_hours = 0
            
            stats = {
                'total_backups': total_backups,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'latest_backup': {
                    'name': latest_backup.name if latest_backup else None,
                    'timestamp': latest_backup.timestamp.isoformat() if latest_backup else None,
                    'size_mb': round(latest_backup.size_bytes / (1024 * 1024), 2) if latest_backup else 0,
                    'type': latest_backup.backup_type if latest_backup else None
                } if latest_backup else None,
                'avg_backup_interval_hours': round(avg_interval_hours, 1),
                'retention_days': self.retention_days,
                'auto_backup_enabled': self.auto_backup_enabled,
                'backup_in_progress': self.is_backup_in_progress,
                'last_backup_time': self.last_backup_time.isoformat() if self.last_backup_time else None
            }
            
            # Add backup type breakdown
            type_counts = {}
            for backup in backups:
                backup_type = backup.backup_type
                type_counts[backup_type] = type_counts.get(backup_type, 0) + 1
            
            stats['backup_types'] = type_counts
            
            return stats
            
        except Exception as e:
            logging.error(f"Failed to get backup stats: {str(e)}")
            return {
                'total_backups': 0,
                'total_size_bytes': 0,
                'total_size_mb': 0,
                'latest_backup': None,
                'avg_backup_interval_hours': 0,
                'retention_days': self.retention_days,
                'auto_backup_enabled': self.auto_backup_enabled,
                'backup_in_progress': self.is_backup_in_progress,
                'last_backup_time': None,
                'backup_types': {}
            }
    
    def _log_backup_operation(self, backup_info: Optional[BackupInfo], status: str, message: str = ""):
        """Log backup operation to database"""
        try:
            if self.db_manager:
                conn = self.db_manager.get_connection() if hasattr(self.db_manager, 'get_connection') else None
                
                if not conn and hasattr(self.db_manager, 'blob_db'):
                    conn = self.db_manager.blob_db.get_connection()
                
                if conn:
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        INSERT INTO backup_log (backup_name, status, file_size, backup_time)
                        VALUES (?, ?, ?, ?)
                    ''', (
                        backup_info.name if backup_info else 'unknown',
                        status,
                        backup_info.size_bytes if backup_info else 0,
                        datetime.now()
                    ))
                    
                    conn.commit()
                    conn.close()
                    
        except Exception as e:
            logging.warning(f"Failed to log backup operation: {str(e)}")
    
    def _update_backup_stats(self, backup_info: Optional[BackupInfo], success: bool):
        """Update backup statistics"""
        self.backup_stats['total_backups'] += 1
        
        if success and backup_info:
            self.backup_stats['successful_backups'] += 1
            self.backup_stats['last_backup_size'] = backup_info.size_bytes
            self.backup_stats['total_backup_size'] += backup_info.size_bytes
        else:
            self.backup_stats['failed_backups'] += 1
    
    def _start_backup_scheduler(self):
        """Start automatic backup scheduler"""
        def backup_scheduler():
            while True:
                try:
                    # Sleep for 1 hour between checks
                    time.sleep(3600)
                    
                    # Check if we need to create an automatic backup
                    if self._should_create_auto_backup():
                        logging.info("Creating scheduled automatic backup")
                        self.create_backup(backup_type='auto', compress=True)
                        
                        # Cleanup old backups
                        self.cleanup_old_backups()
                        
                except Exception as e:
                    logging.error(f"Error in backup scheduler: {str(e)}")
                    time.sleep(300)  # Wait 5 minutes before retrying
        
        if self.auto_backup_enabled:
            self.backup_thread = threading.Thread(target=backup_scheduler, daemon=True)
            self.backup_thread.start()
            logging.info("Automatic backup scheduler started")
    
    def _should_create_auto_backup(self) -> bool:
        """Check if an automatic backup should be created"""
        try:
            # Create backup if no backup exists or last backup is older than 24 hours
            if not self.last_backup_time:
                return True
            
            time_since_last_backup = datetime.now() - self.last_backup_time
            return time_since_last_backup.total_seconds() > (24 * 3600)  # 24 hours
            
        except Exception as e:
            logging.error(f"Error checking backup schedule: {str(e)}")
            return False
    
    def force_backup_now(self) -> Tuple[bool, str, Optional[BackupInfo]]:
        """Force an immediate backup (for manual triggers)"""
        return self.create_backup(backup_type='manual', compress=True, include_metadata=True)
    
    def get_backup_health(self) -> Dict[str, Any]:
        """Get backup system health status"""
        try:
            health = {
                'status': 'healthy',
                'issues': [],
                'last_check': datetime.now().isoformat()
            }
            
            # Check blob storage connectivity
            try:
                container_client = self.blob_service_client.get_container_client(self.backup_container)
                container_client.get_container_properties()
            except Exception as e:
                health['status'] = 'unhealthy'
                health['issues'].append(f"Blob storage connectivity issue: {str(e)}")
            
            # Check if backups are recent
            if self.last_backup_time:
                hours_since_backup = (datetime.now() - self.last_backup_time).total_seconds() / 3600
                if hours_since_backup > 48:  # More than 48 hours
                    health['status'] = 'warning'
                    health['issues'].append(f"Last backup was {hours_since_backup:.1f} hours ago")
            else:
                health['status'] = 'warning'
                health['issues'].append("No backups found")
            
            # Check backup space usage
            stats = self.get_backup_stats()
            if stats['total_size_mb'] > 1000:  # More than 1GB
                health['issues'].append(f"Backup storage usage is high: {stats['total_size_mb']:.1f} MB")
            
            return health
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'issues': [f"Health check failed: {str(e)}"],
                'last_check': datetime.now().isoformat()
            }