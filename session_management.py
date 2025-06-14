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
    
    # Form data session states for candidate editing
    edit_fields = [
        'edit_name', 'edit_email', 'edit_phone', 'edit_current_role', 'edit_industry',
        'edit_notice_period', 'edit_current_salary', 'edit_desired_salary',
        'edit_highest_qualification', 'edit_special_skills'
    ]
    
    for field in edit_fields:
        if field not in st.session_state:
            st.session_state[field] = ""
    
    # List fields for editing
    list_fields = ['edit_qualifications_list', 'edit_skills_list', 'edit_experience_list', 'edit_achievements_list']
    for field in list_fields:
        if field not in st.session_state:
            st.session_state[field] = []
    
    # Form data session states for CV upload
    form_fields = [
        'form_name', 'form_email', 'form_phone', 'form_current_role', 'form_industry',
        'form_notice_period', 'form_current_salary', 'form_desired_salary',
        'form_highest_qualification', 'form_special_skills'
    ]
    
    for field in form_fields:
        if field not in st.session_state:
            st.session_state[field] = ""

def initialize_database_with_retry():
    """Initialize database with retry logic and error handling"""
    if st.session_state.db_initialized and 'db_manager' in st.session_state:
        # If user just logged in, force refresh from cloud
        if not st.session_state.user_session_initialized:
            try:
                logging.info("New user session detected, forcing database refresh from cloud")
                st.session_state.db_manager.force_refresh_from_cloud()
                st.session_state.user_session_initialized = True
                logging.info("Database refreshed from cloud for new user session")
            except Exception as e:
                logging.error(f"Failed to refresh database from cloud: {str(e)}")
                # Continue anyway, use local version
        
        return True
    
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            st.session_state.db_manager = DatabaseManager()
            st.session_state.db_initialized = True
            st.session_state.db_error = None
            
            # Mark that we need to initialize user session
            st.session_state.user_session_initialized = False
            
            return True
        except Exception as e:
            retry_count += 1
            st.session_state.db_error = str(e)
            if retry_count >= max_retries:
                return False
            else:
                time.sleep(2)  # Wait before retry
    
    return False

def force_database_refresh():
    """Force refresh database from cloud - call this when user logs in"""
    try:
        if 'db_manager' in st.session_state and st.session_state.db_manager:
            logging.info("Forcing database refresh from cloud storage")
            success = st.session_state.db_manager.force_refresh_from_cloud()
            
            if success:
                # Clear cached search results since we have fresh data
                clear_search_state()
                logging.info("Database successfully refreshed from cloud")
                return True
            else:
                logging.error("Failed to refresh database from cloud")
                return False
        else:
            logging.warning("Database manager not initialized, cannot refresh")
            return False
            
    except Exception as e:
        logging.error(f"Error forcing database refresh: {str(e)}")
        return False

def ensure_database_sync():
    """Ensure database is synced to cloud after operations"""
    try:
        if 'db_manager' in st.session_state and st.session_state.db_manager:
            success = st.session_state.db_manager.ensure_cloud_sync()
            if success:
                logging.info("Database sync to cloud completed")
            else:
                logging.warning("Database sync to cloud failed")
            return success
        return False
    except Exception as e:
        logging.error(f"Error ensuring database sync: {str(e)}")
        return False

def reset_user_session():
    """Reset user session state when user logs out"""
    st.session_state.user_session_initialized = False
    st.session_state.db_initialized = False
    
    # Clear database manager to force re-initialization on next login
    if 'db_manager' in st.session_state:
        del st.session_state['db_manager']
    
    # Clear all cached data
    clear_search_state()
    clear_form_session_state()
    
    logging.info("User session reset - database will refresh from cloud on next login")

def clear_form_session_state():
    """Clear form-related session state"""
    keys_to_clear = [
        'qualifications_list', 'skills_list', 'experience_list', 'achievements_list',
        'extracted_data', 'cv_processed', 'form_name', 'form_email', 'form_phone',
        'form_current_role', 'form_industry', 'form_notice_period', 'form_current_salary',
        'form_desired_salary', 'form_highest_qualification', 'form_special_skills',
        'manual_entry_mode'
    ]
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

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