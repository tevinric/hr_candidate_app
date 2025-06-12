import sqlite3
import json
import os
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from azure.storage.blob import BlobServiceClient
from config import Config

class DatabaseManager:
    def __init__(self):
        self.db_path = Config.DB_PATH
        self.blob_service_client = None
        self.last_backup_time = None
        
        # Initialize blob storage client if configured
        if Config.AZURE_STORAGE_CONNECTION_STRING:
            try:
                self.blob_service_client = BlobServiceClient.from_connection_string(
                    Config.AZURE_STORAGE_CONNECTION_STRING
                )
                self._ensure_container_exists()
            except Exception as e:
                logging.error(f"Failed to initialize blob storage: {str(e)}")
        
        # Ensure database directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Try to restore from backup if database doesn't exist
        if not os.path.exists(self.db_path):
            self.restore_from_backup()
        
        # Initialize database
        self._init_database()
    
    def _ensure_container_exists(self):
        """Ensure backup container exists in blob storage"""
        try:
            container_client = self.blob_service_client.get_container_client(Config.BACKUP_CONTAINER)
            if not container_client.exists():
                container_client.create_container()
                logging.info(f"Created backup container: {Config.BACKUP_CONTAINER}")
        except Exception as e:
            logging.error(f"Failed to ensure container exists: {str(e)}")
    
    def _init_database(self):
        """Initialize database with required tables"""
        conn = sqlite3.connect(self.db_path)
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
        
        conn.commit()
        conn.close()
        logging.info("Database initialized successfully")
    
    def insert_candidate(self, candidate_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Insert a new candidate into the database
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # First check if email already exists
            existing_candidate = self.get_candidate_by_email(candidate_data.get('email'))
            if existing_candidate:
                logging.warning(f"Candidate with email {candidate_data.get('email')} already exists")
                return False, "A candidate with this email already exists"
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO candidates (
                    name, current_role, email, phone, notice_period, current_salary,
                    industry, desired_salary, highest_qualification, experience,
                    skills, qualifications, achievements, special_skills,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                candidate_data.get('name'),
                candidate_data.get('current_role'),
                candidate_data.get('email'),
                candidate_data.get('phone'),
                candidate_data.get('notice_period'),
                candidate_data.get('current_salary'),
                candidate_data.get('industry'),
                candidate_data.get('desired_salary'),
                candidate_data.get('highest_qualification'),
                json.dumps(candidate_data.get('experience', [])),
                json.dumps(candidate_data.get('skills', [])),
                json.dumps(candidate_data.get('qualifications', [])),
                json.dumps(candidate_data.get('achievements', [])),
                candidate_data.get('special_skills'),
                datetime.now(),
                datetime.now()
            ))
            
            conn.commit()
            conn.close()
            
            # Schedule backup
            self._schedule_backup()
            
            return True, "Candidate saved successfully"
            
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed: candidates.email" in str(e):
                logging.error(f"Integrity error: Email already exists - {candidate_data.get('email')}")
                return False, "A candidate with this email address already exists"
            else:
                logging.error(f"Integrity error inserting candidate: {str(e)}")
                return False, f"Database integrity error: {str(e)}"
        except Exception as e:
            logging.error(f"Error inserting candidate: {str(e)}")
            return False, f"Error saving candidate: {str(e)}"

    def update_candidate(self, candidate_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Update an existing candidate in the database
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # Check if candidate exists
            email = candidate_data.get('email')
            existing_candidate = self.get_candidate_by_email(email)
            
            if not existing_candidate:
                return False, f"Candidate with email {email} not found"
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE candidates SET
                    name = ?, current_role = ?, phone = ?, notice_period = ?,
                    current_salary = ?, industry = ?, desired_salary = ?,
                    highest_qualification = ?, experience = ?, skills = ?,
                    qualifications = ?, achievements = ?, special_skills = ?,
                    updated_at = ?
                WHERE email = ?
            """, (
                candidate_data.get('name'),
                candidate_data.get('current_role'),
                candidate_data.get('phone'),
                candidate_data.get('notice_period'),
                candidate_data.get('current_salary'),
                candidate_data.get('industry'),
                candidate_data.get('desired_salary'),
                candidate_data.get('highest_qualification'),
                json.dumps(candidate_data.get('experience', [])),
                json.dumps(candidate_data.get('skills', [])),
                json.dumps(candidate_data.get('qualifications', [])),
                json.dumps(candidate_data.get('achievements', [])),
                candidate_data.get('special_skills'),
                datetime.now(),
                email
            ))
            
            conn.commit()
            conn.close()
            
            # Schedule backup after update
            self._schedule_backup()
            
            return True, "Candidate updated successfully"
            
        except Exception as e:
            logging.error(f"Error updating candidate: {str(e)}")
            return False, f"Error updating candidate: {str(e)}"

    def search_candidates(self, search_criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search candidates based on criteria"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Build dynamic query
            where_clauses = []
            params = []
            
            for field, value in search_criteria.items():
                if value and value != "":
                    if field == 'experience_years':
                        # For experience years, we need to count experience entries
                        continue  # Handle separately
                    else:
                        where_clauses.append(f"{field} LIKE ?")
                        params.append(f"%{value}%")
            
            query = "SELECT * FROM candidates"
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            candidates = []
            for row in rows:
                candidate = dict(row)
                
                # Parse JSON fields
                candidate['experience'] = json.loads(candidate.get('experience', '[]'))
                candidate['skills'] = json.loads(candidate.get('skills', '[]'))
                candidate['qualifications'] = json.loads(candidate.get('qualifications', '[]'))
                candidate['achievements'] = json.loads(candidate.get('achievements', '[]'))
                
                # Filter by experience years if specified
                if search_criteria.get('experience_years', 0) > 0:
                    if len(candidate['experience']) < search_criteria['experience_years']:
                        continue
                
                candidates.append(candidate)
            
            conn.close()
            return candidates
            
        except Exception as e:
            logging.error(f"Error searching candidates: {str(e)}")
            return []
    
    def search_candidates_by_job_requirements(self, requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search candidates based on job requirements"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get all candidates for scoring
            cursor.execute("SELECT * FROM candidates")
            rows = cursor.fetchall()
            
            candidates = []
            for row in rows:
                candidate = dict(row)
                
                # Parse JSON fields
                candidate['experience'] = json.loads(candidate.get('experience', '[]'))
                candidate['skills'] = json.loads(candidate.get('skills', '[]'))
                candidate['qualifications'] = json.loads(candidate.get('qualifications', '[]'))
                candidate['achievements'] = json.loads(candidate.get('achievements', '[]'))
                
                candidates.append(candidate)
            
            conn.close()
            return candidates
            
        except Exception as e:
            logging.error(f"Error searching candidates by job requirements: {str(e)}")
            return []
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get dashboard statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total candidates
            cursor.execute("SELECT COUNT(*) FROM candidates")
            total_candidates = cursor.fetchone()[0]
            
            # Unique industries
            cursor.execute("SELECT COUNT(DISTINCT industry) FROM candidates WHERE industry IS NOT NULL AND industry != ''")
            unique_industries = cursor.fetchone()[0]
            
            # Average experience (based on number of experience entries)
            cursor.execute("SELECT experience FROM candidates WHERE experience IS NOT NULL")
            experience_data = cursor.fetchall()
            
            total_experience = 0
            candidate_count = 0
            for exp_row in experience_data:
                try:
                    exp_list = json.loads(exp_row[0])
                    if exp_list:
                        total_experience += len(exp_list)
                        candidate_count += 1
                except:
                    continue
            
            avg_experience = total_experience / candidate_count if candidate_count > 0 else 0
            
            conn.close()
            
            return {
                'total_candidates': total_candidates,
                'unique_industries': unique_industries,
                'avg_experience': avg_experience
            }
            
        except Exception as e:
            logging.error(f"Error getting dashboard stats: {str(e)}")
            return {
                'total_candidates': 0,
                'unique_industries': 0,
                'avg_experience': 0
            }
    
    def backup_to_blob(self) -> bool:
        """Backup database to Azure Blob Storage"""
        if not self.blob_service_client:
            logging.error("Blob storage client not configured")
            return False
        
        try:
            # Generate backup filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"backup_{timestamp}.db"
            
            # Upload database file
            with open(self.db_path, "rb") as data:
                blob_client = self.blob_service_client.get_blob_client(
                    container=Config.BACKUP_CONTAINER,
                    blob=backup_name
                )
                blob_client.upload_blob(data, overwrite=True)
            
            # Also upload as latest backup
            with open(self.db_path, "rb") as data:
                blob_client = self.blob_service_client.get_blob_client(
                    container=Config.BACKUP_CONTAINER,
                    blob="latest.db"
                )
                blob_client.upload_blob(data, overwrite=True)
            
            # Log backup
            file_size = os.path.getsize(self.db_path)
            self._log_backup(backup_name, "SUCCESS", file_size)
            self.last_backup_time = datetime.now()
            
            logging.info(f"Database backed up successfully as {backup_name}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to backup database: {str(e)}")
            self._log_backup(f"backup_{timestamp}.db", "FAILED", 0)
            return False
    
    def restore_from_backup(self, backup_name: str = "latest.db") -> bool:
        """Restore database from Azure Blob Storage"""
        if not self.blob_service_client:
            logging.warning("Blob storage client not configured, creating new database")
            return False
        
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=Config.BACKUP_CONTAINER,
                blob=backup_name
            )
            
            # Check if backup exists
            if not blob_client.exists():
                logging.warning(f"Backup {backup_name} does not exist")
                return False
            
            # Download backup
            with open(self.db_path, "wb") as download_file:
                download_file.write(blob_client.download_blob().readall())
            
            logging.info(f"Database restored from {backup_name}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to restore database: {str(e)}")
            return False
    
    def _log_backup(self, backup_name: str, status: str, file_size: int):
        """Log backup operation"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO backup_log (backup_name, status, file_size)
                VALUES (?, ?, ?)
            ''', (backup_name, status, file_size))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logging.error(f"Failed to log backup: {str(e)}")
    
    def _schedule_backup(self):
        """Schedule automatic backup (every 10 inserts or hourly)"""
        try:
            # Simple backup strategy - backup after every 5 new candidates
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM candidates")
            total_candidates = cursor.fetchone()[0]
            
            # Check last backup time
            cursor.execute("SELECT MAX(backup_time) FROM backup_log WHERE status = 'SUCCESS'")
            last_backup = cursor.fetchone()[0]
            
            conn.close()
            
            # Backup every 5 candidates or if no backup in last hour
            should_backup = False
            
            if total_candidates % 5 == 0:  # Every 5 candidates
                should_backup = True
            elif last_backup:
                last_backup_time = datetime.fromisoformat(last_backup.replace('Z', '+00:00'))
                if (datetime.now() - last_backup_time).total_seconds() > 3600:  # 1 hour
                    should_backup = True
            else:  # No previous backup
                should_backup = True
            
            if should_backup:
                self.backup_to_blob()
                
        except Exception as e:
            logging.error(f"Failed to schedule backup: {str(e)}")
    
    def get_backup_history(self) -> List[Dict[str, Any]]:
        """Get backup history"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM backup_log 
                ORDER BY backup_time DESC 
                LIMIT 20
            ''')
            
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            logging.error(f"Error getting backup history: {str(e)}")
            return []
    
    def cleanup_old_backups(self, keep_days: int = 30):
        """Clean up old backups from blob storage"""
        if not self.blob_service_client:
            return
        
        try:
            container_client = self.blob_service_client.get_container_client(Config.BACKUP_CONTAINER)
            cutoff_date = datetime.now() - datetime.timedelta(days=keep_days)
            
            blobs_to_delete = []
            for blob in container_client.list_blobs():
                if blob.name != "latest.db" and blob.last_modified < cutoff_date:
                    blobs_to_delete.append(blob.name)
            
            for blob_name in blobs_to_delete:
                container_client.delete_blob(blob_name)
                logging.info(f"Deleted old backup: {blob_name}")
            
        except Exception as e:
            logging.error(f"Failed to cleanup old backups: {str(e)}")
    
    def get_candidate_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get a candidate by email address"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM candidates WHERE email = ?", (email,))
            row = cursor.fetchone()
            
            if not row:
                conn.close()
                return None
            
            candidate = dict(row)
            
            # Parse JSON fields
            candidate['experience'] = json.loads(candidate.get('experience', '[]'))
            candidate['skills'] = json.loads(candidate.get('skills', '[]'))
            candidate['qualifications'] = json.loads(candidate.get('qualifications', '[]'))
            candidate['achievements'] = json.loads(candidate.get('achievements', '[]'))
            
            conn.close()
            return candidate
            
        except Exception as e:
            logging.error(f"Error getting candidate by email: {str(e)}")
            return None
