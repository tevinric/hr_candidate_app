import sqlite3
import json
import os
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from azure.storage.blob import BlobServiceClient
from config import Config
from blob_database import BlobDatabaseManager

class DatabaseManager:
    def __init__(self):
        # Initialize blob database manager
        self.blob_db = BlobDatabaseManager()
        
        # Keep backup functionality for the backup container
        self.backup_blob_service_client = None
        self.last_backup_time = None
        
        if Config.AZURE_STORAGE_CONNECTION_STRING:
            try:
                self.backup_blob_service_client = BlobServiceClient.from_connection_string(
                    Config.AZURE_STORAGE_CONNECTION_STRING
                )
                self._ensure_backup_container_exists()
            except Exception as e:
                logging.error(f"Failed to initialize backup blob storage: {str(e)}")
    
    def _ensure_backup_container_exists(self):
        """Ensure backup container exists in blob storage"""
        try:
            container_client = self.backup_blob_service_client.get_container_client(Config.BACKUP_CONTAINER)
            if not container_client.exists():
                container_client.create_container()
                logging.info(f"Created backup container: {Config.BACKUP_CONTAINER}")
        except Exception as e:
            logging.error(f"Failed to ensure backup container exists: {str(e)}")
    
    def insert_candidate(self, candidate_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Insert a new candidate into the database"""
        try:
            # Check if email already exists
            existing_candidate = self.get_candidate_by_email(candidate_data.get('email'))
            if existing_candidate:
                logging.warning(f"Candidate with email {candidate_data.get('email')} already exists")
                return False, "A candidate with this email already exists"
            
            conn = self.blob_db.get_connection()
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
            
            # Sync to blob storage
            self.blob_db.sync_to_blob()
            
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
        """Update an existing candidate in the database"""
        try:
            email = candidate_data.get('email')
            existing_candidate = self.get_candidate_by_email(email)
            
            if not existing_candidate:
                return False, f"Candidate with email {email} not found"
            
            conn = self.blob_db.get_connection()
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
            
            # Sync to blob storage
            self.blob_db.sync_to_blob()
            
            return True, "Candidate updated successfully"
            
        except Exception as e:
            logging.error(f"Error updating candidate: {str(e)}")
            return False, f"Error updating candidate: {str(e)}"

    def search_candidates(self, search_criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search candidates based on criteria"""
        try:
            conn = self.blob_db.get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Build dynamic query
            where_clauses = []
            params = []
            
            for field, value in search_criteria.items():
                if value and value != "":
                    if field == 'experience_years':
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
            conn = self.blob_db.get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
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
            conn = self.blob_db.get_connection()
            cursor = conn.cursor()
            
            # Total candidates
            cursor.execute("SELECT COUNT(*) FROM candidates")
            total_candidates = cursor.fetchone()[0]
            
            # Unique industries
            cursor.execute("SELECT COUNT(DISTINCT industry) FROM candidates WHERE industry IS NOT NULL AND industry != ''")
            unique_industries = cursor.fetchone()[0]
            
            # Average experience
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
            
            # Get sync status
            sync_status = self.blob_db.get_sync_status()
            
            return {
                'total_candidates': total_candidates,
                'unique_industries': unique_industries,
                'avg_experience': avg_experience,
                'last_sync_time': sync_status['last_sync_time'],
                'database_size_mb': sync_status['local_db_size'] / (1024 * 1024) if sync_status['local_db_size'] else 0
            }
            
        except Exception as e:
            logging.error(f"Error getting dashboard stats: {str(e)}")
            return {
                'total_candidates': 0,
                'unique_industries': 0,
                'avg_experience': 0,
                'last_sync_time': None,
                'database_size_mb': 0
            }
    
    def get_candidate_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get a candidate by email address"""
        try:
            conn = self.blob_db.get_connection()
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
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get sync status information"""
        return self.blob_db.get_sync_status()
    
    # Keep existing backup methods but modify to work with blob database
    def backup_to_blob(self) -> bool:
        """Backup database to Azure Blob Storage (separate from main db storage)"""
        if not self.backup_blob_service_client:
            logging.error("Backup blob storage client not configured")
            return False
        
        try:
            # First sync to blob storage
            self.blob_db.sync_to_blob()
            
            # Then create backup copy
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"backup_{timestamp}.db"
            
            # Copy from main database blob to backup container
            source_blob_client = self.blob_db.blob_service_client.get_blob_client(
                container=self.blob_db.db_container,
                blob=self.blob_db.db_blob_name
            )
            
            backup_blob_client = self.backup_blob_service_client.get_blob_client(
                container=Config.BACKUP_CONTAINER,
                blob=backup_name
            )
            
            # Copy blob
            copy_source = source_blob_client.url
            backup_blob_client.start_copy_from_url(copy_source)
            
            # Also create latest backup
            latest_blob_client = self.backup_blob_service_client.get_blob_client(
                container=Config.BACKUP_CONTAINER,
                blob="latest.db"
            )
            latest_blob_client.start_copy_from_url(copy_source)
            
            self.last_backup_time = datetime.now()
            logging.info(f"Database backed up successfully as {backup_name}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to backup database: {str(e)}")
            return False
    
    def restore_from_backup(self, backup_name: str = "latest.db") -> bool:
        """Restore database from backup"""
        if not self.backup_blob_service_client:
            logging.warning("Backup blob storage client not configured")
            return False
        
        try:
            backup_blob_client = self.backup_blob_service_client.get_blob_client(
                container=Config.BACKUP_CONTAINER,
                blob=backup_name
            )
            
            if not backup_blob_client.exists():
                logging.warning(f"Backup {backup_name} does not exist")
                return False
            
            # Download backup and upload to main database location
            backup_data = backup_blob_client.download_blob().readall()
            
            main_blob_client = self.blob_db.blob_service_client.get_blob_client(
                container=self.blob_db.db_container,
                blob=self.blob_db.db_blob_name
            )
            
            main_blob_client.upload_blob(backup_data, overwrite=True)
            
            # Force refresh local database
            self.blob_db.force_refresh()
            
            logging.info(f"Database restored from {backup_name}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to restore database: {str(e)}")
            return False
    
    def _log_backup(self, backup_name: str, status: str, file_size: int):
        """Log backup operation"""
        try:
            conn = self.blob_db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO backup_log (backup_name, status, file_size)
                VALUES (?, ?, ?)
            ''', (backup_name, status, file_size))
            
            conn.commit()
            conn.close()
            
            # Sync after logging
            self.blob_db.sync_to_blob()
            
        except Exception as e:
            logging.error(f"Failed to log backup: {str(e)}")
    
    def _schedule_backup(self):
        """Schedule automatic backup"""
        try:
            conn = self.blob_db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM candidates")
            total_candidates = cursor.fetchone()[0]
            conn.close()
            
            # Backup every 5 candidates
            if total_candidates % 5 == 0:
                self.backup_to_blob()
                
        except Exception as e:
            logging.error(f"Failed to schedule backup: {str(e)}")
    
    def sync_database(self) -> bool:
        """Manually sync database to blob storage"""
        return self.blob_db.sync_to_blob()
    
    def refresh_database(self) -> bool:
        """Refresh database from blob storage"""
        return self.blob_db.sync_from_blob()