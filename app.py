import streamlit as st
import pandas as pd
import json
import time
import logging
from datetime import datetime
import tempfile
import os
from database import DatabaseManager
from cv_processor import CVProcessor
from utils import validate_candidate_data, format_search_results
from pathlib import Path

# Configure Streamlit page
st.set_page_config(
    page_title="HR Candidate Management Tool",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    /* Main container styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    
    /* Section headers */
    .section-header {
        background: linear-gradient(90deg, #f8fafc 0%, #e2e8f0 100%);
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #3b82f6;
        margin: 1rem 0;
        font-weight: 600;
    }
    
    /* Form container */
    .form-container {
        background: #ffffff;
        padding: 2rem;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
        margin: 1rem 0;
    }
    
    /* Success message styling */
    .success-message {
        background: #dcfce7;
        border: 1px solid #bbf7d0;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        color: #166534;
    }
    
    /* Warning message styling */
    .warning-message {
        background: #fef3c7;
        border: 1px solid #fcd34d;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        color: #92400e;
    }
    
    /* Error message styling */
    .error-message {
        background: #fee2e2;
        border: 1px solid #fca5a5;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        color: #991b1b;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(90deg, #3b82f6 0%, #1d4ed8 100%);
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    /* Delete button styling */
    div[data-testid="stButton"] > button[key="delete_candidate_btn"] {
        background: linear-gradient(90deg, #dc2626 0%, #b91c1c 100%) !important;
        color: white !important;
        border: none !important;
    }
    
    div[data-testid="stButton"] > button[key="delete_candidate_btn"]:hover {
        background: linear-gradient(90deg, #b91c1c 0%, #991b1b 100%) !important;
    }
    
    /* Enhanced form section */
    .form-section {
        background: #f8fafc;
        padding: 1.5rem;
        border-radius: 8px;
        margin: 1rem 0;
        border: 1px solid #e2e8f0;
    }
    
    /* Candidate card styling */
    .candidate-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        margin: 1rem 0;
    }
    
    /* Navigation styling */
    .nav-button {
        margin: 0.5rem;
    }
    
    /* Sync status styling */
    .sync-status {
        background: #f0f9ff;
        border: 1px solid #0ea5e9;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    /* Entry method styling */
    .entry-method {
        background: #f8fafc;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
        margin: 1rem 0;
    }
    
    /* Bullet point styling for experience details */
    .experience-bullet {
        margin-left: 1rem;
        margin-bottom: 0.5rem;
    }
    
    .experience-section {
        background: #fafafa;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 3px solid #3b82f6;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state with database error handling
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
    if 'show_delete_confirmation' not in st.session_state:
        st.session_state.show_delete_confirmation = False
    
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
    """Initialize database with retry logic and FORCE cloud refresh on login"""
    from session_management import initialize_database_with_retry as session_init_db
    return session_init_db()


def main():
    # Import authentication modules
    from auth import init_auth_session_state, is_authenticated
    from landing_page import show_landing_page, show_user_profile
    from session_management import force_database_refresh
    
    # Initialize session state FIRST - CRITICAL
    initialize_session_state()
    
    # Initialize authentication session state
    init_auth_session_state()
    
    # Check authentication status
    if not is_authenticated():
        # Show landing page with authentication
        show_landing_page()
        return
    
    # User is authenticated, show main application
    show_main_application()

def show_main_application():
    """Show the main application for authenticated users"""
    from landing_page import show_user_profile
    from session_management import force_database_refresh

    # Professional header
    st.markdown(f"""
    <div class="main-header">
        <h1>Key Talent Solutions</h1>
        <p>Candidate Management System</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Show user profile in sidebar
    show_user_profile()
    
    # Initialize database with error handling and FORCE refresh for new sessions
    if not initialize_database_with_retry():
        st.error("❌ Failed to initialize database. Please check your Azure Storage configuration.")
        st.markdown(f"**Error Details:** {st.session_state.db_error}")
        st.info("💡 **Troubleshooting Tips:**")
        st.markdown("""
        1. Verify your Azure Storage connection string is correct
        2. Ensure the storage account exists and is accessible
        3. Check that the app_data container exists in your storage account
        4. Verify network connectivity to Azure Storage
        5. Try refreshing the page
        """)
        
        if st.button("🔄 Retry Database Connection"):
            st.session_state.db_initialized = False
            if 'db_manager' in st.session_state:
                del st.session_state['db_manager']
            st.rerun()
        
        st.stop()
    
    # Show cloud sync status ONLY if user session is not initialized
    if not getattr(st.session_state, 'user_session_initialized', True):
        with st.spinner("🔄 Syncing with cloud database..."):
            time.sleep(1)  # Brief pause to show the message
        st.success("✅ Database synchronized with cloud")
        time.sleep(1)  # Brief pause to show success
        st.rerun()  # Refresh to clear the message
    
    # PAGE ROUTING - Check current page and display accordingly
    if st.session_state.current_page == 'candidate_details':
        candidate_details_page()
    else:
        main_application_page()

def main_application_page():
    """Main application page with navigation"""
    # Sidebar navigation
    st.sidebar.markdown("""
    <div style="text-align: left; padding: 1rem;">
        <h2>🚀 Navigation</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Database status indicator
    try:
        sync_status = st.session_state.db_manager.get_sync_status()
        if sync_status['last_sync_time']:
            last_sync = sync_status['last_sync_time'].strftime('%H:%M:%S')
            st.sidebar.success(f"🔗 DB Connected (Last sync: {last_sync})")
        else:
            st.sidebar.warning("⚠️ DB Connected (No sync yet)")
        
        if sync_status['is_syncing']:
            st.sidebar.info("🔄 Syncing...")
            
    except Exception as e:
        st.sidebar.error("❌ DB Connection Error")
        st.sidebar.caption(f"Error: {str(e)}")
    
    tab = st.sidebar.radio(
        "Select Function", 
        ["📄 Add Candidate", "🔍 Search Candidates", "📊 Dashboard"],
        key="main_nav"
    )
    
    if tab == "📄 Add Candidate":
        upload_cv_tab()
    elif tab == "🔍 Search Candidates":
        search_candidates_tab()
    elif tab == "📊 Dashboard":
        dashboard_tab()

def candidate_details_page():
    """Candidate details page - looks like CV form but for editing existing candidate"""
    if not st.session_state.selected_candidate:
        st.error("No candidate selected!")
        st.session_state.current_page = 'main'
        st.rerun()
        return
    
    candidate = st.session_state.selected_candidate
    
    # Header with navigation
    st.markdown(f"""
    <div style="background: linear-gradient(90deg, #059669 0%, #10b981 100%); 
                padding: 1.5rem; border-radius: 10px; margin-bottom: 1rem;">
        <h2 style="color: white; margin: 0; text-align: center;">
            ✏️ Edit Candidate: {candidate.get('name', 'Unknown')}
        </h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Navigation buttons
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        if st.button("⬅️ Back to Search", key="back_to_search", help="Return to search results"):
            st.session_state.current_page = 'main'
            # Set the sidebar to Search Candidates tab
            st.session_state.main_nav = "🔍 Search Candidates"
            st.rerun()
    
    with col3:
        st.markdown("") # Spacer
    
    st.markdown("---")
    
    # Show the candidate editing form (same format as CV form)
    show_candidate_edit_form()

def show_candidate_edit_form():
    """Show candidate editing form - similar to CV upload form"""
    candidate = st.session_state.selected_candidate
    
    st.markdown('<div class="section-header"><h2>📝 Edit Candidate Information</h2></div>', unsafe_allow_html=True)
    st.markdown('<p style="color: #64748b; font-style: italic;">Edit candidate information and click Update to save changes to the database.</p>', unsafe_allow_html=True)
    
    # Handle delete confirmation dialog
    if st.session_state.show_delete_confirmation:
        show_delete_confirmation_dialog()
        return
    
    # Personal Information Section
    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    st.markdown("### 👤 Personal Information")
    col1, col2 = st.columns(2)
    
    with col1:
        st.session_state.edit_name = st.text_input(
            "Full Name *", 
            value=st.session_state.edit_name, 
            key="edit_name_input"
        )
        st.session_state.edit_email = st.text_input(
            "Email Address *", 
            value=st.session_state.edit_email, 
            key="edit_email_input"
        )
        st.session_state.edit_phone = st.text_input(
            "Phone Number", 
            value=st.session_state.edit_phone, 
            key="edit_phone_input"
        )
        
    with col2:
        st.session_state.edit_current_role = st.text_input(
            "Current Role", 
            value=st.session_state.edit_current_role, 
            key="edit_role_input"
        )
        st.session_state.edit_industry = st.text_input(
            "Industry", 
            value=st.session_state.edit_industry, 
            key="edit_industry_input"
        )
        st.session_state.edit_notice_period = st.text_input(
            "Notice Period", 
            value=st.session_state.edit_notice_period, 
            key="edit_notice_input"
        )
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Salary Information
    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    st.markdown("### 💰 Salary Information")
    col3, col4 = st.columns(2)
    with col3:
        st.session_state.edit_current_salary = st.text_input(
            "Current Salary", 
            value=st.session_state.edit_current_salary, 
            key="edit_current_sal"
        )
    with col4:
        st.session_state.edit_desired_salary = st.text_input(
            "Desired Salary", 
            value=st.session_state.edit_desired_salary, 
            key="edit_desired_sal"
        )
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Education
    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    st.markdown("### 🎓 Education")
    st.session_state.edit_highest_qualification = st.text_input(
        "Highest Qualification", 
        value=st.session_state.edit_highest_qualification, 
        key="edit_highest_qual"
    )
    
    # Handle Qualifications
    st.markdown("**Detailed Qualifications:**")
    
    # Display existing qualifications
    for i, qual in enumerate(st.session_state.edit_qualifications_list):
        col_qual1, col_qual2, col_qual3, col_qual4 = st.columns([3, 3, 2, 1])
        with col_qual1:
            qual['qualification'] = st.text_input(
                f"Qualification {i+1}", 
                value=qual.get('qualification', ''),
                key=f"edit_qual_{i}"
            )
        with col_qual2:
            qual['institution'] = st.text_input(
                f"Institution {i+1}", 
                value=qual.get('institution', ''),
                key=f"edit_inst_{i}"
            )
        with col_qual3:
            qual['year'] = st.text_input(
                f"Year {i+1}", 
                value=qual.get('year', ''),
                key=f"edit_year_{i}"
            )
        with col_qual4:
            if st.button("🗑️", key=f"edit_del_qual_{i}", help="Delete qualification"):
                st.session_state.edit_qualifications_list.pop(i)
                st.rerun()
    
    if st.button("➕ Add Qualification", key="edit_add_qualification_btn"):
        st.session_state.edit_qualifications_list.append({'qualification': '', 'institution': '', 'year': '', 'grade': ''})
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Skills Section
    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    st.markdown("### 🛠️ Skills")
    
    # Display skills
    for i, skill in enumerate(st.session_state.edit_skills_list):
        col_skill1, col_skill2, col_skill3 = st.columns([4, 2, 1])
        with col_skill1:
            skill['skill'] = st.text_input(
                f"Skill {i+1}", 
                value=skill.get('skill', ''),
                key=f"edit_skill_{i}"
            )
        with col_skill2:
            skill['proficiency'] = st.selectbox(
                f"Level {i+1}",
                options=[1, 2, 3, 4, 5],
                index=min(skill.get('proficiency', 3) - 1, 4),
                format_func=lambda x: f"{x} - {'Beginner' if x==1 else 'Basic' if x==2 else 'Intermediate' if x==3 else 'Advanced' if x==4 else 'Expert'}",
                key=f"edit_prof_{i}"
            )
        with col_skill3:
            if st.button("🗑️", key=f"edit_del_skill_{i}", help="Delete skill"):
                st.session_state.edit_skills_list.pop(i)
                st.rerun()
    
    if st.button("➕ Add Skill", key="edit_add_skill_btn"):
        st.session_state.edit_skills_list.append({'skill': '', 'proficiency': 3})
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Enhanced Experience Section
    show_enhanced_experience_section("edit")
    
    # Achievements Section
    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    st.markdown("### 🏆 Achievements")
    
    for i, achievement in enumerate(st.session_state.edit_achievements_list):
        col_ach1, col_ach2 = st.columns([5, 1])
        with col_ach1:
            st.session_state.edit_achievements_list[i] = st.text_area(
                f"Achievement {i+1}", 
                value=achievement,
                height=68,
                key=f"edit_ach_{i}"
            )
        with col_ach2:
            st.write("")  # Empty space for alignment
            if st.button("🗑️", key=f"edit_del_ach_{i}", help="Delete achievement"):
                st.session_state.edit_achievements_list.pop(i)
                st.rerun()
    
    if st.button("➕ Add Achievement", key="edit_add_achievement_btn"):
        st.session_state.edit_achievements_list.append('')
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Special Skills
    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    st.markdown("### ⭐ Special Skills & Certifications")
    st.session_state.edit_special_skills = st.text_area(
        "Special Skills", 
        value=st.session_state.edit_special_skills, 
        height=100, 
        key="edit_special_skills_input"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Update and Delete buttons
    st.markdown("---")
    col_submit1, col_submit2, col_submit3, col_submit4 = st.columns([2, 1, 1, 1])
    with col_submit1:
        st.markdown("*Fields marked with * are required")
    with col_submit2:
        if st.button("💾 Update Candidate", type="primary", use_container_width=True, key="update_candidate_btn"):
            if st.session_state.edit_name and st.session_state.edit_email:
                handle_candidate_update()
            else:
                st.error("❌ Please fill in at least Name and Email fields.")
    with col_submit3:
        if st.button("🗑️ Delete Candidate", use_container_width=True, key="delete_candidate_btn", help="Permanently delete this candidate from the database"):
            st.session_state.show_delete_confirmation = True
            st.rerun()

def show_delete_confirmation_dialog():
    """Show delete confirmation dialog"""
    candidate = st.session_state.selected_candidate
    
    st.markdown('<div class="error-message">', unsafe_allow_html=True)
    st.markdown("### ⚠️ Confirm Delete")
    st.markdown(f"Are you sure you want to **permanently delete** the candidate **{candidate.get('name', 'Unknown')}** ({candidate.get('email', 'N/A')})?")
    st.markdown("**This action cannot be undone!**")
    st.markdown("</div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col2:
        if st.button("✅ Yes, Delete", type="primary", use_container_width=True, key="confirm_delete_btn"):
            handle_candidate_delete()
    
    with col3:
        if st.button("❌ Cancel", use_container_width=True, key="cancel_delete_btn"):
            st.session_state.show_delete_confirmation = False
            st.rerun()

def handle_candidate_delete():
    """Handle candidate deletion with FORCED cloud sync"""
    try:
        candidate = st.session_state.selected_candidate
        email = candidate.get('email')
        
        if not email:
            st.error("❌ Cannot delete candidate: Email not found")
            return
        
        # Delete from database with forced cloud sync
        result, message = st.session_state.db_manager.delete_candidate(email)
        
        if result:
            st.success("✅ Candidate deleted successfully!")
            
            # Clear session state
            st.session_state.selected_candidate = None
            st.session_state.show_delete_confirmation = False
            st.session_state.current_page = 'main'
            
            # Clear cached search results so they refresh
            st.session_state.cached_search_results = []
            st.session_state.search_performed = False
            
            # Navigate back to search page
            st.session_state.main_nav = "🔍 Search Candidates"
            
            # Show success message and auto-redirect
            st.markdown("### ✅ Deletion Complete!")
            st.info("Returning to search page...")
            
            # Use a delay to show the success message before redirecting
            time.sleep(1)
            st.rerun()
        else:
            st.error(f"❌ Failed to delete candidate: {message}")
            st.session_state.show_delete_confirmation = False
            st.rerun()
            
    except Exception as e:
        st.error(f"❌ Error deleting candidate: {str(e)}")
        st.session_state.show_delete_confirmation = False
        st.rerun()

def show_enhanced_experience_section(prefix=""):
    """Display enhanced work experience section with bullet points"""
    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    st.markdown("### 💼 Work Experience")
    
    # Determine which experience list to use
    if prefix == "edit":
        experience_list = st.session_state.edit_experience_list
    else:
        experience_list = st.session_state.experience_list
    
    # Display experience in expandable sections
    for i, exp in enumerate(experience_list):
        position_title = exp.get('position', 'New Position')
        company_name = exp.get('company', '')
        display_title = f"Position {i+1}: {position_title}"
        if company_name:
            display_title += f" at {company_name}"
            
        with st.expander(display_title):
            # Basic information in columns
            col_exp1, col_exp2 = st.columns(2)
            with col_exp1:
                exp['position'] = st.text_input(
                    "Job Title", 
                    value=exp.get('position', ''),
                    key=f"{prefix}pos_{i}"
                )
                exp['company'] = st.text_input(
                    "Company", 
                    value=exp.get('company', ''),
                    key=f"{prefix}comp_{i}"
                )
                exp['years'] = st.text_input(
                    "Duration", 
                    value=exp.get('years', ''),
                    key=f"{prefix}duration_{i}"
                )
                
            with col_exp2:
                exp['location'] = st.text_input(
                    "Location", 
                    value=exp.get('location', ''),
                    key=f"{prefix}location_{i}"
                )
                exp['employment_type'] = st.selectbox(
                    "Employment Type",
                    options=['', 'Full-time', 'Part-time', 'Contract', 'Internship', 'Freelance', 'Consultant'],
                    index=0 if not exp.get('employment_type') else 
                          ['', 'Full-time', 'Part-time', 'Contract', 'Internship', 'Freelance', 'Consultant'].index(exp.get('employment_type')) 
                          if exp.get('employment_type') in ['', 'Full-time', 'Part-time', 'Contract', 'Internship', 'Freelance', 'Consultant'] else 0,
                    key=f"{prefix}emp_type_{i}"
                )
                
                # Additional details in a single row
                col_team, col_reporting = st.columns(2)
                with col_team:
                    exp['team_size'] = st.text_input(
                        "Team Size", 
                        value=exp.get('team_size', ''),
                        key=f"{prefix}team_size_{i}"
                    )
                with col_reporting:
                    exp['reporting_to'] = st.text_input(
                        "Reporting To", 
                        value=exp.get('reporting_to', ''),
                        key=f"{prefix}reporting_{i}"
                    )
            
            # Responsibilities Section
            st.markdown("**📋 Key Responsibilities:**")
            responsibilities = exp.get('responsibilities', [])
            
            if not responsibilities:
                exp['responsibilities'] = ['']
                responsibilities = exp['responsibilities']
            
            # Display responsibilities with bullet point styling
            for j, resp in enumerate(responsibilities):
                col_resp1, col_resp2 = st.columns([5, 1])
                with col_resp1:
                    responsibilities[j] = st.text_area(
                        f"Responsibility {j+1}", 
                        value=resp,
                        height=70,
                        key=f"{prefix}resp_{i}_{j}",
                        help="Enter a specific responsibility or duty"
                    )
                with col_resp2:
                    st.write("")  # Spacing
                    if st.button("🗑️", key=f"{prefix}del_resp_{i}_{j}", help="Delete responsibility"):
                        responsibilities.pop(j)
                        st.rerun()
            
            col_add_resp = st.columns(1)[0]
            with col_add_resp:
                if st.button(f"➕ Add Responsibility", key=f"{prefix}add_resp_{i}"):
                    responsibilities.append('')
                    st.rerun()
            
            # Achievements Section
            st.markdown("**🏆 Key Achievements:**")
            achievements = exp.get('achievements', [])
            
            if not achievements:
                exp['achievements'] = []
                achievements = exp['achievements']
            
            for j, achievement in enumerate(achievements):
                col_ach1, col_ach2 = st.columns([5, 1])
                with col_ach1:
                    achievements[j] = st.text_area(
                        f"Achievement {j+1}", 
                        value=achievement,
                        height=70,
                        key=f"{prefix}ach_{i}_{j}",
                        help="Enter a specific achievement, award, or measurable result"
                    )
                with col_ach2:
                    st.write("")  # Spacing
                    if st.button("🗑️", key=f"{prefix}del_ach_{i}_{j}", help="Delete achievement"):
                        achievements.pop(j)
                        st.rerun()
            
            col_add_ach = st.columns(1)[0]
            with col_add_ach:
                if st.button(f"➕ Add Achievement", key=f"{prefix}add_ach_{i}"):
                    achievements.append('')
                    st.rerun()
            
            # Technologies Section
            st.markdown("**💻 Technologies & Tools:**")
            technologies = exp.get('technologies', [])
            
            if not technologies:
                exp['technologies'] = []
                technologies = exp['technologies']
            
            for j, tech in enumerate(technologies):
                col_tech1, col_tech2 = st.columns([5, 1])
                with col_tech1:
                    technologies[j] = st.text_input(
                        f"Technology {j+1}", 
                        value=tech,
                        key=f"{prefix}tech_{i}_{j}",
                        help="Enter a technology, tool, or software used"
                    )
                with col_tech2:
                    if st.button("🗑️", key=f"{prefix}del_tech_{i}_{j}", help="Delete technology"):
                        technologies.pop(j)
                        st.rerun()
            
            col_add_tech = st.columns(1)[0]
            with col_add_tech:
                if st.button(f"➕ Add Technology", key=f"{prefix}add_tech_{i}"):
                    technologies.append('')
                    st.rerun()
            
            # Delete position button
            st.markdown("---")
            col_del_exp = st.columns(1)[0]
            with col_del_exp:
                if st.button(f"🗑️ Delete Position", key=f"{prefix}del_exp_{i}", type="secondary"):
                    experience_list.pop(i)
                    st.rerun()
    
    # Add new experience button
    if st.button("➕ Add Work Experience", key=f"{prefix}add_experience_btn"):
        new_experience = {
            'position': '', 
            'company': '', 
            'years': '', 
            'location': '',
            'employment_type': '',
            'team_size': '',
            'reporting_to': '',
            'responsibilities': [''],
            'achievements': [],
            'technologies': []
        }
        experience_list.append(new_experience)
        st.rerun()
        
    st.markdown('</div>', unsafe_allow_html=True)

def handle_candidate_update():
    """Handle candidate update with FORCED cloud sync"""
    try:
        # Clean up empty entries
        clean_qualifications = [q for q in st.session_state.edit_qualifications_list if q.get('qualification')]
        clean_skills = [s for s in st.session_state.edit_skills_list if s.get('skill')]
        clean_experience = []
        
        for exp in st.session_state.edit_experience_list:
            if exp.get('position') or exp.get('company'):
                clean_resp = [r for r in exp.get('responsibilities', []) if r.strip()]
                clean_ach = [a for a in exp.get('achievements', []) if a.strip()]
                clean_tech = [t for t in exp.get('technologies', []) if t.strip()]
                
                cleaned_exp = exp.copy()
                cleaned_exp['responsibilities'] = clean_resp
                cleaned_exp['achievements'] = clean_ach
                cleaned_exp['technologies'] = clean_tech
                clean_experience.append(cleaned_exp)
        
        clean_achievements = [a for a in st.session_state.edit_achievements_list if a.strip()]
        
        candidate_data = {
            'name': st.session_state.edit_name,
            'current_role': st.session_state.edit_current_role,
            'email': st.session_state.edit_email,
            'phone': st.session_state.edit_phone,
            'notice_period': st.session_state.edit_notice_period,
            'current_salary': st.session_state.edit_current_salary,
            'industry': st.session_state.edit_industry,
            'desired_salary': st.session_state.edit_desired_salary,
            'highest_qualification': st.session_state.edit_highest_qualification,
            'experience': clean_experience,
            'skills': clean_skills,
            'qualifications': clean_qualifications,
            'achievements': clean_achievements,
            'special_skills': st.session_state.edit_special_skills
        }
        
        # Update candidate in database with forced cloud sync
        result, message = st.session_state.db_manager.update_candidate(candidate_data)
        
        if result:
            st.success("✅ Candidate updated successfully and synced to cloud!")
            
            # Update the selected candidate data
            st.session_state.selected_candidate.update(candidate_data)
            
            # Clear the cached search results so they refresh with updated data
            st.session_state.cached_search_results = []
            st.session_state.search_performed = False
            
            # Show success and provide navigation option
            st.markdown("### ✅ Update Complete!")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("⬅️ Back to Search Results", type="primary"):
                    st.session_state.current_page = 'main'
                    st.rerun()
            with col2:
                st.info("Changes have been saved to the database and synced to cloud.")
        else:
            st.error(f"❌ Failed to update candidate: {message}")
            
    except Exception as e:
        st.error(f"❌ Error updating candidate: {str(e)}")

def initialize_edit_form_data(candidate):
    """Initialize edit form with candidate data"""
    st.session_state.edit_name = candidate.get('name', '')
    st.session_state.edit_email = candidate.get('email', '')
    st.session_state.edit_phone = candidate.get('phone', '')
    st.session_state.edit_current_role = candidate.get('current_role', '')
    st.session_state.edit_industry = candidate.get('industry', '')
    st.session_state.edit_notice_period = candidate.get('notice_period', '')
    st.session_state.edit_current_salary = candidate.get('current_salary', '')
    st.session_state.edit_desired_salary = candidate.get('desired_salary', '')
    st.session_state.edit_highest_qualification = candidate.get('highest_qualification', '')
    st.session_state.edit_special_skills = candidate.get('special_skills', '')
    
    # Initialize lists - make copies to avoid reference issues
    st.session_state.edit_qualifications_list = [qual.copy() for qual in candidate.get('qualifications', [])]
    st.session_state.edit_skills_list = [skill.copy() for skill in candidate.get('skills', [])]
    
    # Initialize enhanced experience list with all fields
    edit_experience_list = []
    for exp in candidate.get('experience', []):
        enhanced_exp = {
            'position': exp.get('position', ''),
            'company': exp.get('company', ''),
            'years': exp.get('years', ''),
            'location': exp.get('location', ''),
            'employment_type': exp.get('employment_type', ''),
            'team_size': exp.get('team_size', ''),
            'reporting_to': exp.get('reporting_to', ''),
            'responsibilities': exp.get('responsibilities', []).copy(),
            'achievements': exp.get('achievements', []).copy(),
            'technologies': exp.get('technologies', []).copy()
        }
        edit_experience_list.append(enhanced_exp)
    
    st.session_state.edit_experience_list = edit_experience_list
    st.session_state.edit_achievements_list = candidate.get('achievements', []).copy()

def view_candidate_details(candidate):
    """Navigate to candidate details page"""
    st.session_state.selected_candidate = candidate
    st.session_state.current_page = 'candidate_details'
    # Initialize edit form with candidate data
    initialize_edit_form_data(candidate)
    st.rerun()

# ========== CV UPLOAD TAB ==========
def upload_cv_tab():
    from candidate_forms import upload_cv_tab
    upload_cv_tab()

# ========== SEARCH CANDIDATES TAB ==========
def search_candidates_tab():
    from search_functions import search_candidates_tab
    search_candidates_tab()

# ========== DASHBOARD TAB ==========
def dashboard_tab():
    from dashboard_functions import dashboard_tab
    dashboard_tab()

# Enhanced match score calculation function - this is the same as in search_functions.py
def calculate_match_score(candidate, requirements):
    """Enhanced comprehensive match score calculation with better flexibility"""
    from search_functions import calculate_enhanced_match_score
    return calculate_enhanced_match_score(candidate, requirements)

if __name__ == "__main__":
    main()