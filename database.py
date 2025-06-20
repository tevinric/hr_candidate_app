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

    def _match_responsibilities(self, experience_list: List[Dict[str, Any]], search_responsibilities: str) -> bool:
        """
        Check if any of the candidate's experience responsibilities match the search terms
        """
        if not search_responsibilities or not search_responsibilities.strip():
            return True  # No responsibilities filter means match all
        
        # Get all responsibilities text from all experience entries
        all_responsibilities_text = ""
        for exp in experience_list:
            responsibilities = exp.get('responsibilities', [])
            if isinstance(responsibilities, list):
                all_responsibilities_text += " " + " ".join(responsibilities)
        
        all_responsibilities_text = all_responsibilities_text.lower()
        
        # Parse search terms (comma-separated or space-separated)
        search_terms = []
        if ',' in search_responsibilities:
            search_terms = [term.strip().lower() for term in search_responsibilities.split(',') if term.strip()]
        else:
            search_terms = [term.strip().lower() for term in search_responsibilities.split() if len(term.strip()) > 2]
        
        if not search_terms:
            return True
        
        # Check if ANY search term appears in responsibilities
        for term in search_terms:
            if term in all_responsibilities_text:
                return True
        
        return False

    def _match_qualifications(self, candidate: Dict[str, Any], search_qualifications: str) -> bool:
        """
        Check if candidate's qualifications match the search terms
        """
        if not search_qualifications or not search_qualifications.strip():
            return True  # No qualifications filter means match all
        
        search_lower = search_qualifications.lower()
        
        # Check highest qualification field
        highest_qual = candidate.get('highest_qualification', '').lower()
        if search_lower in highest_qual:
            return True
        
        # Check detailed qualifications JSON
        qualifications = candidate.get('qualifications', [])
        for qual in qualifications:
            if isinstance(qual, dict):
                qual_text = f"{qual.get('qualification', '')} {qual.get('institution', '')}".lower()
                if search_lower in qual_text:
                    return True
        
        return False

    def _match_company(self, experience_list: List[Dict[str, Any]], search_company: str) -> Tuple[bool, float]:
        """
        Check if any of the candidate's experience companies match the search terms
        Returns (matches, recency_score) where recency_score is higher for more recent positions
        """
        if not search_company or not search_company.strip():
            return True, 1.0  # No company filter means match all with neutral score
        
        search_company_lower = search_company.lower()
        best_recency_score = 0.0
        
        for i, exp in enumerate(experience_list):
            company = exp.get('company', '').lower()
            
            # Check if company matches (flexible matching)
            if (search_company_lower in company or 
                company in search_company_lower or
                any(word in company for word in search_company_lower.split() if len(word) > 2)):
                
                # Calculate recency score (most recent gets highest score)
                # First position (index 0) gets 1.0, second gets 0.8, third gets 0.6, etc.
                recency_score = max(0.1, 1.0 - (i * 0.2))
                
                # Give extra bonus for current position (index 0)
                if i == 0:
                    recency_score += 0.5
                
                best_recency_score = max(best_recency_score, recency_score)
        
        return best_recency_score > 0, best_recency_score

    def _match_comments(self, candidate: Dict[str, Any], search_comments: str) -> bool:
        """
        Check if candidate's comments match the search terms
        """
        if not search_comments or not search_comments.strip():
            return True  # No comments filter means match all
        
        search_lower = search_comments.lower()
        candidate_comments = candidate.get('comments', '').lower()
        
        # Parse search terms (comma-separated or space-separated)
        search_terms = []
        if ',' in search_comments:
            search_terms = [term.strip().lower() for term in search_comments.split(',') if term.strip()]
        else:
            search_terms = [term.strip().lower() for term in search_comments.split() if len(term.strip()) > 2]
        
        if not search_terms:
            return search_lower in candidate_comments
        
        # Check if ANY search term appears in comments
        for term in search_terms:
            if term in candidate_comments:
                return True
        
        return False

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
        """Insert a new candidate into the database with FORCED cloud sync"""
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
                    skills, qualifications, achievements, special_skills, comments,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                candidate_data.get('comments', ''),  # New comments field
                datetime.now(),
                datetime.now()
            ))
            
            conn.commit()
            conn.close()
            
            # CRITICAL: FORCE immediate sync to cloud - BLOCKING OPERATION
            logging.info("🔄 FORCING IMMEDIATE CLOUD SYNC after candidate insertion")
            sync_success = self.blob_db.sync_to_blob(force=True)
            if sync_success:
                logging.info("✅ Candidate insertion synced to cloud successfully")
            else:
                logging.error("❌ FAILED to sync candidate insertion to cloud!")
                # Don't fail the operation, but log the error
            
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
        """Update an existing candidate in the database with FORCED cloud sync"""
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
                    comments = ?, updated_at = ?
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
                candidate_data.get('comments', ''),  # New comments field
                datetime.now(),
                email
            ))
            
            conn.commit()
            conn.close()
            
            # CRITICAL: FORCE immediate sync to cloud - BLOCKING OPERATION
            logging.info("🔄 FORCING IMMEDIATE CLOUD SYNC after candidate update")
            sync_success = self.blob_db.sync_to_blob(force=True)
            if sync_success:
                logging.info("✅ Candidate update synced to cloud successfully")
            else:
                logging.error("❌ FAILED to sync candidate update to cloud!")
                # Don't fail the operation, but log the error
            
            return True, "Candidate updated successfully"
            
        except Exception as e:
            logging.error(f"Error updating candidate: {str(e)}")
            return False, f"Error updating candidate: {str(e)}"

    def delete_candidate(self, email: str) -> Tuple[bool, str]:
        """Delete a candidate by email address with FORCED cloud sync"""
        try:
            # Check if candidate exists
            existing_candidate = self.get_candidate_by_email(email)
            if not existing_candidate:
                return False, f"Candidate with email {email} not found"
            
            conn = self.blob_db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM candidates WHERE email = ?", (email,))
            
            if cursor.rowcount == 0:
                conn.close()
                return False, f"No candidate found with email {email}"
            
            conn.commit()
            conn.close()
            
            # CRITICAL: FORCE immediate sync to cloud - BLOCKING OPERATION
            logging.info("🔄 FORCING IMMEDIATE CLOUD SYNC after candidate deletion")
            sync_success = self.blob_db.sync_to_blob(force=True)
            if sync_success:
                logging.info("✅ Candidate deletion synced to cloud successfully")
            else:
                logging.error("❌ FAILED to sync candidate deletion to cloud!")
                # Don't fail the operation, but log the error
            
            logging.info(f"Candidate with email {email} deleted successfully")
            return True, "Candidate deleted successfully"
            
        except Exception as e:
            logging.error(f"Error deleting candidate: {str(e)}")
            return False, f"Error deleting candidate: {str(e)}"

    def _match_skills(self, candidate_skills: List[Dict[str, Any]], search_skills: str) -> bool:
        """
        Check if any of the candidate's skills match any of the search skills (case-insensitive)
        """
        if not search_skills or not search_skills.strip():
            return True  # No skills filter means match all
        
        # Parse comma-separated skills from search input
        query_skills = [skill.strip().lower() for skill in search_skills.split(',') if skill.strip()]
        
        if not query_skills:
            return True
        
        # Get candidate skill names (case-insensitive)
        candidate_skill_names = [skill.get('skill', '').lower() for skill in candidate_skills if skill.get('skill')]
        
        # Check for ANY skill match (OR logic)
        for query_skill in query_skills:
            for candidate_skill in candidate_skill_names:
                # Flexible matching: exact match, contains, or word overlap
                if (query_skill in candidate_skill or 
                    candidate_skill in query_skill or
                    any(word in candidate_skill for word in query_skill.split() if len(word) > 2)):
                    return True
        
        return False

    def search_candidates(self, search_criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search candidates based on criteria with enhanced skills search, company matching, and comments search"""
        try:
            conn = self.blob_db.get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Build dynamic query (excluding fields that need special handling)
            where_clauses = []
            params = []
            
            # Fields that can be directly queried from database columns
            direct_search_fields = ['name', 'current_role', 'industry', 'notice_period', 
                                'highest_qualification', 'phone', 'email']
            
            for field, value in search_criteria.items():
                if value and value != "":
                    # Skip fields that need special handling
                    if field in ['experience_years', 'skills', 'responsibilities', 'qualifications', 'company', 'comments']:
                        continue  # Handle these separately after getting all candidates
                    elif field in direct_search_fields:
                        # Make searches case-insensitive for direct database columns
                        where_clauses.append(f"LOWER({field}) LIKE LOWER(?)")
                        params.append(f"%{value}%")
            
            # Base query to get all candidates (or filtered by direct fields)
            query = "SELECT * FROM candidates"
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            candidates = []
            skills_search = search_criteria.get('skills', '')
            responsibilities_search = search_criteria.get('responsibilities', '')
            qualifications_search = search_criteria.get('qualifications', '')
            company_search = search_criteria.get('company', '')
            comments_search = search_criteria.get('comments', '')  # New comments search
            
            # Store company match scores for sorting
            candidates_with_scores = []
            
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
                
                # Enhanced skills filtering with case-insensitive comma-separated search
                if not self._match_skills(candidate['skills'], skills_search):
                    continue
                
                # Handle responsibilities search (search within experience JSON)
                if responsibilities_search and not self._match_responsibilities(candidate['experience'], responsibilities_search):
                    continue
                
                # Handle qualifications search (search within qualifications JSON and highest_qualification)
                if qualifications_search and not self._match_qualifications(candidate, qualifications_search):
                    continue
                
                # Handle comments search
                if comments_search and not self._match_comments(candidate, comments_search):
                    continue
                
                # NEW: Handle company search with recency scoring
                company_matches = True
                company_score = 1.0  # Default score for no company filter
                
                if company_search:
                    company_matches, company_score = self._match_company(candidate['experience'], company_search)
                    if not company_matches:
                        continue
                
                # Add company score to candidate for sorting
                candidate['company_recency_score'] = company_score
                candidates_with_scores.append(candidate)
            
            # Sort by company recency score if company search was performed
            if company_search:
                candidates_with_scores.sort(key=lambda x: x.get('company_recency_score', 0), reverse=True)
                logging.info(f"Company search performed for '{company_search}' - results sorted by recency")
            
            conn.close()
            return candidates_with_scores
            
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
    
    def force_refresh_from_cloud(self) -> bool:
        """Force refresh database from cloud storage - used when user logs in"""
        try:
            logging.info("🔄 FORCING REFRESH FROM CLOUD STORAGE")
            # Force download from blob storage
            success = self.blob_db.sync_from_blob(force=True)
            
            if success:
                # Clear any cached connections
                self.blob_db.force_download_on_next_connection_flag()
                logging.info("✅ Successfully refreshed database from cloud")
            else:
                logging.error("❌ Failed to refresh database from cloud")
            
            return success
        except Exception as e:
            logging.error(f"❌ Error in force_refresh_from_cloud: {str(e)}")
            return False
    
    def ensure_cloud_sync(self) -> bool:
        """Ensure database changes are synced to cloud - BLOCKING OPERATION with verification"""
        try:
            logging.info("🔄 ENSURING DATABASE SYNC TO CLOUD")
            
            # Check if database exists locally first
            if not hasattr(self, 'blob_db') or not self.blob_db:
                logging.error("❌ Blob database manager not available")
                return False
            
            # Force sync to cloud with blocking operation
            logging.info("🔄 Starting forced sync to blob storage...")
            success = self.blob_db.sync_to_blob(force=True)
            
            if success:
                logging.info("✅ Database successfully synced to cloud")
                
                # Additional verification - check sync timestamp
                sync_status = self.blob_db.get_sync_status()
                if sync_status.get('last_sync_time'):
                    logging.info(f"✅ Sync timestamp verified: {sync_status['last_sync_time']}")
                else:
                    logging.warning("⚠️ Sync completed but no timestamp found")
                
                return True
            else:
                logging.error("❌ Failed to sync database to cloud")
                return False
                
        except Exception as e:
            logging.error(f"❌ Error in ensure_cloud_sync: {str(e)}")
            return False