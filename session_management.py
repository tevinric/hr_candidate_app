import streamlit as st
import time
import logging
from database import DatabaseManager
from cv_processor import CVProcessor

def initialize_session_state():
    """Initialize all session state variables with database error handling"""
    # Core application state
    if 'extracted_data' not in st.session_state:
        st.session_state.extracted_data = None
    if 'cv_processed' not in st.session_state:
        st.session_state.cv_processed = False
    if 'cv_processor' not in st.session_state:
        st.session_state.cv_processor = CVProcessor()
    if 'show_overwrite_dialog' not in st.session_state:
        st.session_state.show_overwrite_dialog = False
    if 'pending_candidate_data' not in st.session_state:
        st.session_state.pending_candidate_data = None
    if 'existing_candidate_email' not in st.session_state:
        st.session_state.existing_candidate_email = None
    if 'db_initialized' not in st.session_state:
        st.session_state.db_initialized = False
    if 'db_error' not in st.session_state:
        st.session_state.db_error = None
    if 'manual_entry_mode' not in st.session_state:
        st.session_state.manual_entry_mode = False
    if 'user_session_initialized' not in st.session_state:
        st.session_state.user_session_initialized = False
    
    # PAGE NAVIGATION STATE
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'main'  # 'main', 'candidate_details'
    
    # SEARCH STATE - Cache search criteria and results
    if 'cached_search_criteria' not in st.session_state:
        st.session_state.cached_search_criteria = {}
    if 'cached_search_results' not in st.session_state:
        st.session_state.cached_search_results = []
    if 'search_performed' not in st.session_state:
        st.session_state.search_performed = False
    
    # CANDIDATE DETAILS STATE
    if 'selected_candidate' not in st.session_state:
        st.session_state.selected_candidate = None
    
    # Form data session states for candidate editing (including comments)
    edit_fields = [
        'edit_name', 'edit_email', 'edit_phone', 'edit_current_role', 'edit_industry',
        'edit_notice_period', 'edit_current_salary', 'edit_desired_salary',
        'edit_highest_qualification', 'edit_special_skills', 'edit_comments'  # Added comments
    ]
    
    for field in edit_fields:
        if field not in st.session_state:
            st.session_state[field] = ""
    
    # List fields for editing
    list_fields = ['edit_qualifications_list', 'edit_skills_list', 'edit_experience_list', 'edit_achievements_list']
    for field in list_fields:
        if field not in st.session_state:
            st.session_state[field] = []
    
    # Form data session states for CV upload (including comments)
    form_fields = [
        'form_name', 'form_email', 'form_phone', 'form_current_role', 'form_industry',
        'form_notice_period', 'form_current_salary', 'form_desired_salary',
        'form_highest_qualification', 'form_special_skills', 'form_comments'  # Added comments
    ]
    
    for field in form_fields:
        if field not in st.session_state:
            st.session_state[field] = ""

def initialize_database_with_retry():
    """Initialize database with retry logic and FORCE cloud refresh on new sessions"""
    # Check if database is already initialized
    if st.session_state.db_initialized and 'db_manager' in st.session_state:
        # CRITICAL: If user just logged in, FORCE refresh from cloud
        if not st.session_state.user_session_initialized:
            try:
                logging.info("NEW USER SESSION DETECTED - FORCING DATABASE REFRESH FROM CLOUD")
                success = st.session_state.db_manager.force_refresh_from_cloud()
                if success:
                    st.session_state.user_session_initialized = True
                    logging.info("✅ Database successfully refreshed from cloud for new user session")
                    # Clear any cached search data since we have fresh data
                    clear_search_state()
                else:
                    logging.error("❌ Failed to refresh database from cloud, but continuing with local version")
                    # Still mark as initialized to avoid repeated attempts
                    st.session_state.user_session_initialized = True
            except Exception as e:
                logging.error(f"❌ Error during forced cloud refresh: {str(e)}")
                # Still mark as initialized to avoid repeated attempts
                st.session_state.user_session_initialized = True
        
        return True
    
    # Database not initialized, create new instance with retries
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            logging.info("Initializing new database manager...")
            st.session_state.db_manager = DatabaseManager()
            st.session_state.db_initialized = True
            st.session_state.db_error = None
            
            # Mark that we need to initialize user session (force cloud refresh)
            st.session_state.user_session_initialized = False
            
            logging.info("✅ Database manager initialized successfully")
            return True
            
        except Exception as e:
            retry_count += 1
            st.session_state.db_error = str(e)
            logging.error(f"❌ Database initialization attempt {retry_count} failed: {str(e)}")
            
            if retry_count >= max_retries:
                logging.error(f"❌ Database initialization failed after {max_retries} attempts")
                return False
            else:
                logging.info(f"⏳ Retrying database initialization in 2 seconds...")
                time.sleep(2)  # Wait before retry
    
    return False

def force_database_refresh():
    """Force refresh database from cloud - call this when user logs in"""
    try:
        if 'db_manager' in st.session_state and st.session_state.db_manager:
            logging.info("🔄 FORCING DATABASE REFRESH FROM CLOUD STORAGE")
            success = st.session_state.db_manager.force_refresh_from_cloud()
            
            if success:
                # Clear cached search results since we have fresh data
                clear_search_state()
                logging.info("✅ Database successfully refreshed from cloud")
                return True
            else:
                logging.error("❌ Failed to refresh database from cloud")
                return False
        else:
            logging.warning("⚠️ Database manager not initialized, cannot refresh")
            return False
            
    except Exception as e:
        logging.error(f"❌ Error forcing database refresh: {str(e)}")
        return False

def ensure_database_sync():
    """Ensure database is synced to cloud after operations - BLOCKING OPERATION"""
    try:
        if 'db_manager' in st.session_state and st.session_state.db_manager:
            logging.info("🔄 ENSURING DATABASE SYNC TO CLOUD")
            success = st.session_state.db_manager.ensure_cloud_sync()
            if success:
                logging.info("✅ Database sync to cloud completed successfully")
            else:
                logging.warning("⚠️ Database sync to cloud failed")
            return success
        return False
    except Exception as e:
        logging.error(f"❌ Error ensuring database sync: {str(e)}")
        return False

def reset_user_session():
    """Reset user session state when user logs out"""
    logging.info("🔄 Resetting user session - will refresh from cloud on next login")
    
    st.session_state.user_session_initialized = False
    st.session_state.db_initialized = False
    
    # Clear database manager to force re-initialization on next login
    if 'db_manager' in st.session_state:
        del st.session_state['db_manager']
    
    # Clear all cached data
    clear_search_state()
    clear_form_session_state()
    
    logging.info("✅ User session reset - database will refresh from cloud on next login")

def clear_form_session_state():
    """Clear form-related session state including comments"""
    keys_to_clear = [
        'qualifications_list', 'skills_list', 'experience_list', 'achievements_list',
        'extracted_data', 'cv_processed', 'form_name', 'form_email', 'form_phone',
        'form_current_role', 'form_industry', 'form_notice_period', 'form_current_salary',
        'form_desired_salary', 'form_highest_qualification', 'form_special_skills',
        'form_comments', 'manual_entry_mode'  # Added form_comments
    ]
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

def clear_all_candidate_state():
    """Clear all candidate-related session state for adding a new candidate"""
    logging.info("🗑️ Clearing all candidate state for new candidate")
    
    # Clear form data
    clear_form_session_state()
    
    # Clear overwrite dialog state
    clear_overwrite_dialog_state()
    
    # Clear CV processing state
    st.session_state.cv_processed = False
    st.session_state.extracted_data = None
    st.session_state.manual_entry_mode = False
    
    # Reset lists to empty
    st.session_state.qualifications_list = []
    st.session_state.skills_list = []
    st.session_state.experience_list = []
    st.session_state.achievements_list = []
    
    # Reset form fields to empty (including comments)
    form_fields = [
        'form_name', 'form_email', 'form_phone', 'form_current_role', 'form_industry',
        'form_notice_period', 'form_current_salary', 'form_desired_salary',
        'form_highest_qualification', 'form_special_skills', 'form_comments'  # Added form_comments
    ]
    
    for field in form_fields:
        st.session_state[field] = ""
    
    logging.info("✅ All candidate state cleared - ready for new candidate")

def clear_overwrite_dialog_state():
    """Clear overwrite dialog state"""
    st.session_state.show_overwrite_dialog = False
    st.session_state.pending_candidate_data = None
    st.session_state.existing_candidate_email = None

def clear_search_state():
    """Clear search-related session state"""
    st.session_state.cached_search_criteria = {}
    st.session_state.cached_search_results = []
    st.session_state.search_performed = False
    logging.info("🗑️ Search state cleared")