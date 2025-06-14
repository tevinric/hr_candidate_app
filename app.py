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
        padding: 2rem;
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
    """Initialize database with retry logic and error handling"""
    if st.session_state.db_initialized and 'db_manager' in st.session_state:
        return True
    
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            st.session_state.db_manager = DatabaseManager()
            st.session_state.db_initialized = True
            st.session_state.db_error = None
            return True
        except Exception as e:
            retry_count += 1
            st.session_state.db_error = str(e)
            if retry_count >= max_retries:
                return False
            else:
                time.sleep(2)  # Wait before retry
    
    return False

# Initialize session state
initialize_session_state()

def main():
    # Import authentication modules - NEW IMPORTS
    from auth import init_auth_session_state, is_authenticated
    from landing_page import show_landing_page, show_user_profile
    
    # Initialize authentication session state - NEW
    init_auth_session_state()
    
    # Check authentication status - NEW AUTHENTICATION CHECK
    if not is_authenticated():
        # Show landing page with authentication
        show_landing_page()
        return
    
    # User is authenticated, show main application - NEW FUNCTION CALL
    show_main_application()

def show_main_application():
    """Show the main application for authenticated users - NEW FUNCTION"""
    from landing_page import show_user_profile
    
    # Professional header
    st.markdown("""
    <div class="main-header">
        <h1>🎯 HR Candidate Management Tool</h1>
        <p>AI-Powered CV Processing and Intelligent Candidate Matching</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Show user profile in sidebar - NEW FEATURE
    show_user_profile()
    
    # Initialize database with error handling
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
                del st.session_state.db_manager
            st.rerun()
        
        st.stop()
    
    # PAGE ROUTING - Check current page and display accordingly
    if st.session_state.current_page == 'candidate_details':
        candidate_details_page()
    else:
        main_application_page()

def main_application_page():
    """Main application page with navigation"""
    # Sidebar navigation
    st.sidebar.markdown("""
    <div style="text-align: center; padding: 1rem; color: white;">
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
    """Handle candidate deletion"""
    try:
        candidate = st.session_state.selected_candidate
        email = candidate.get('email')
        
        if not email:
            st.error("❌ Cannot delete candidate: Email not found")
            return
        
        # Delete from database
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
    """Handle candidate update"""
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
        
        # Update candidate in database
        result, message = st.session_state.db_manager.update_candidate(candidate_data)
        
        if result:
            st.success("✅ Candidate updated successfully!")
            
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
                st.info("Changes have been saved to the database.")
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
    st.markdown('<div class="section-header"><h2>📄 Add New Candidate</h2></div>', unsafe_allow_html=True)
    
    # Entry method selection
    st.markdown('<div class="entry-method">', unsafe_allow_html=True)
    entry_method = st.radio(
        "How would you like to add the candidate?",
        ["📄 Upload CV and Process", "✏️ Manual Entry"],
        key="entry_method",
        help="Choose between uploading a CV for AI processing or manually entering candidate details"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    if entry_method == "📄 Upload CV and Process":
        cv_upload_section()
    else:
        manual_entry_section()

def cv_upload_section():
    """CV Upload and Processing Section"""
    # Professional upload container
    with st.container():
        st.markdown('<div class="form-container">', unsafe_allow_html=True)
        st.markdown("### 📄 Upload CV File")
        uploaded_file = st.file_uploader(
            "Choose a PDF CV file", 
            type="pdf",
            help="Upload a PDF resume/CV file for AI-powered data extraction"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Process CV only if file is uploaded and not already processed
    if uploaded_file is not None and not st.session_state.cv_processed:
        with st.spinner("🔄 Processing CV... Please wait"):
            try:
                # Save uploaded file temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    tmp_file.write(uploaded_file.read())
                    tmp_file_path = tmp_file.name
                
                # Extract text from PDF
                extracted_text = st.session_state.cv_processor.extract_text_from_pdf(tmp_file_path)
                
                if extracted_text:
                    st.markdown('<div class="success-message">✅ CV text extracted successfully!</div>', unsafe_allow_html=True)
                    
                    # Show extracted text in expander with professional styling
                    with st.expander("📄 View Extracted Text", expanded=False):
                        st.text_area("Raw CV Text", extracted_text, height=200, disabled=True)
                    
                    # Process with OpenAI - THIS ONLY RUNS ONCE
                    with st.spinner("🤖 Analyzing CV with AI..."):
                        candidate_data = st.session_state.cv_processor.process_cv_with_openai(extracted_text)
                        
                        if candidate_data:
                            st.session_state.extracted_data = candidate_data
                            st.session_state.cv_processed = True
                            st.session_state.manual_entry_mode = False
                            
                            # Initialize form data from extracted data
                            initialize_form_data(candidate_data)
                            
                            st.markdown('<div class="success-message">✅ CV processed successfully with AI!</div>', unsafe_allow_html=True)
                        else:
                            st.markdown('<div class="error-message">❌ Failed to process CV with AI. Please try again.</div>', unsafe_allow_html=True)
                
                # Clean up temp file
                os.unlink(tmp_file_path)
                
            except Exception as e:
                st.markdown(f'<div class="error-message">❌ Error processing CV: {str(e)}</div>', unsafe_allow_html=True)
    
    # Show form if CV has been processed
    if st.session_state.cv_processed and st.session_state.extracted_data:
        show_candidate_form()

def manual_entry_section():
    """Manual Entry Section"""
    # Initialize manual entry mode if not already set
    if not st.session_state.manual_entry_mode:
        initialize_manual_entry_form()
        st.session_state.manual_entry_mode = True
        st.session_state.cv_processed = False
        st.session_state.extracted_data = None
    
    # Show the candidate form for manual entry
    show_candidate_form()

def initialize_manual_entry_form():
    """Initialize form for manual entry with empty data"""
    # Initialize dynamic lists first
    st.session_state.qualifications_list = []
    st.session_state.skills_list = []
    st.session_state.experience_list = []
    st.session_state.achievements_list = []
    
    # Initialize form fields with empty values
    st.session_state.form_name = ""
    st.session_state.form_email = ""
    st.session_state.form_phone = ""
    st.session_state.form_current_role = ""
    st.session_state.form_industry = ""
    st.session_state.form_notice_period = ""
    st.session_state.form_current_salary = ""
    st.session_state.form_desired_salary = ""
    st.session_state.form_highest_qualification = ""
    st.session_state.form_special_skills = ""

def initialize_form_data(data):
    """Initialize form data from extracted CV data with enhanced experience structure"""
    # Initialize dynamic lists first
    if 'qualifications_list' not in st.session_state:
        st.session_state.qualifications_list = data.get('qualifications', [])
    if 'skills_list' not in st.session_state:
        st.session_state.skills_list = data.get('skills', [])
    if 'achievements_list' not in st.session_state:
        st.session_state.achievements_list = data.get('achievements', [])
    
    # Initialize enhanced experience list
    if 'experience_list' not in st.session_state:
        experience_list = []
        for exp in data.get('experience', []):
            enhanced_exp = {
                'position': exp.get('position', ''),
                'company': exp.get('company', ''),
                'years': exp.get('years', ''),
                'location': exp.get('location', ''),
                'employment_type': exp.get('employment_type', ''),
                'team_size': exp.get('team_size', ''),
                'reporting_to': exp.get('reporting_to', ''),
                'responsibilities': exp.get('responsibilities', []),
                'achievements': exp.get('achievements', []),
                'technologies': exp.get('technologies', [])
            }
            experience_list.append(enhanced_exp)
        st.session_state.experience_list = experience_list
    
    # Initialize form fields
    st.session_state.form_name = data.get('name', '')
    st.session_state.form_email = data.get('email', '')
    st.session_state.form_phone = data.get('phone', '')
    st.session_state.form_current_role = data.get('current_role', '')
    st.session_state.form_industry = data.get('industry', '')
    st.session_state.form_notice_period = data.get('notice_period', '')
    st.session_state.form_current_salary = data.get('current_salary', '')
    st.session_state.form_desired_salary = data.get('desired_salary', '')
    st.session_state.form_highest_qualification = data.get('highest_qualification', '')
    st.session_state.form_special_skills = data.get('special_skills', '')

def show_candidate_form():
    if st.session_state.manual_entry_mode:
        st.markdown('<div class="section-header"><h2>📝 Enter Candidate Information</h2></div>', unsafe_allow_html=True)
        st.markdown('<p style="color: #64748b; font-style: italic;">Please enter the candidate information manually and save to the database.</p>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="section-header"><h2>📝 Review and Edit Candidate Information</h2></div>', unsafe_allow_html=True)
        st.markdown('<p style="color: #64748b; font-style: italic;">Please review the extracted information and make any necessary corrections before saving.</p>', unsafe_allow_html=True)
    
    # Handle overwrite confirmation dialog
    if st.session_state.show_overwrite_dialog:
        show_overwrite_confirmation_dialog()
        return
    
    # Personal Information Section
    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    st.markdown("### 👤 Personal Information")
    col1, col2 = st.columns(2)
    
    with col1:
        st.session_state.form_name = st.text_input(
            "Full Name *", 
            value=st.session_state.form_name, 
            key="name_input"
        )
        st.session_state.form_email = st.text_input(
            "Email Address *", 
            value=st.session_state.form_email, 
            key="email_input"
        )
        st.session_state.form_phone = st.text_input(
            "Phone Number", 
            value=st.session_state.form_phone, 
            key="phone_input"
        )
        
    with col2:
        st.session_state.form_current_role = st.text_input(
            "Current Role", 
            value=st.session_state.form_current_role, 
            key="role_input"
        )
        st.session_state.form_industry = st.text_input(
            "Industry", 
            value=st.session_state.form_industry, 
            key="industry_input"
        )
        st.session_state.form_notice_period = st.text_input(
            "Notice Period", 
            value=st.session_state.form_notice_period, 
            key="notice_input"
        )
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Salary Information
    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    st.markdown("### 💰 Salary Information")
    col3, col4 = st.columns(2)
    with col3:
        st.session_state.form_current_salary = st.text_input(
            "Current Salary", 
            value=st.session_state.form_current_salary, 
            key="current_sal"
        )
    with col4:
        st.session_state.form_desired_salary = st.text_input(
            "Desired Salary", 
            value=st.session_state.form_desired_salary, 
            key="desired_sal"
        )
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Education
    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    st.markdown("### 🎓 Education")
    st.session_state.form_highest_qualification = st.text_input(
        "Highest Qualification", 
        value=st.session_state.form_highest_qualification, 
        key="highest_qual"
    )
    
    # Handle Qualifications with NO REFRESH
    st.markdown("**Detailed Qualifications:**")
    
    # Display existing qualifications
    for i, qual in enumerate(st.session_state.qualifications_list):
        col_qual1, col_qual2, col_qual3, col_qual4 = st.columns([3, 3, 2, 1])
        with col_qual1:
            qual['qualification'] = st.text_input(
                f"Qualification {i+1}", 
                value=qual.get('qualification', ''),
                key=f"qual_{i}"
            )
        with col_qual2:
            qual['institution'] = st.text_input(
                f"Institution {i+1}", 
                value=qual.get('institution', ''),
                key=f"inst_{i}"
            )
        with col_qual3:
            qual['year'] = st.text_input(
                f"Year {i+1}", 
                value=qual.get('year', ''),
                key=f"year_{i}"
            )
        with col_qual4:
            if st.button("🗑️", key=f"del_qual_{i}", help="Delete qualification"):
                st.session_state.qualifications_list.pop(i)
                st.rerun()
    
    if st.button("➕ Add Qualification", key="add_qualification_btn"):
        st.session_state.qualifications_list.append({'qualification': '', 'institution': '', 'year': '', 'grade': ''})
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Skills Section
    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    st.markdown("### 🛠️ Skills")
    
    # Display skills with NO REFRESH
    for i, skill in enumerate(st.session_state.skills_list):
        col_skill1, col_skill2, col_skill3 = st.columns([4, 2, 1])
        with col_skill1:
            skill['skill'] = st.text_input(
                f"Skill {i+1}", 
                value=skill.get('skill', ''),
                key=f"skill_{i}"
            )
        with col_skill2:
            skill['proficiency'] = st.selectbox(
                f"Level {i+1}",
                options=[1, 2, 3, 4, 5],
                index=min(skill.get('proficiency', 3) - 1, 4),
                format_func=lambda x: f"{x} - {'Beginner' if x==1 else 'Basic' if x==2 else 'Intermediate' if x==3 else 'Advanced' if x==4 else 'Expert'}",
                key=f"prof_{i}"
            )
        with col_skill3:
            if st.button("🗑️", key=f"del_skill_{i}", help="Delete skill"):
                st.session_state.skills_list.pop(i)
                st.rerun()
    
    if st.button("➕ Add Skill", key="add_skill_btn"):
        st.session_state.skills_list.append({'skill': '', 'proficiency': 3})
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Enhanced Experience Section
    show_enhanced_experience_section()
    
    # Achievements Section
    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    st.markdown("### 🏆 Achievements")
    
    for i, achievement in enumerate(st.session_state.achievements_list):
        col_ach1, col_ach2 = st.columns([5, 1])
        with col_ach1:
            st.session_state.achievements_list[i] = st.text_area(
                f"Achievement {i+1}", 
                value=achievement,
                height=68,
                key=f"ach_{i}"
            )
        with col_ach2:
            st.write("")  # Empty space for alignment
            if st.button("🗑️", key=f"del_ach_{i}", help="Delete achievement"):
                st.session_state.achievements_list.pop(i)
                st.rerun()
    
    if st.button("➕ Add Achievement", key="add_achievement_btn"):
        st.session_state.achievements_list.append('')
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Special Skills
    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    st.markdown("### ⭐ Special Skills & Certifications")
    st.session_state.form_special_skills = st.text_area(
        "Special Skills", 
        value=st.session_state.form_special_skills, 
        height=100, 
        key="special_skills_input"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Form submission with enhanced styling
    st.markdown("---")
    st.markdown('<div class="professional-spacing">', unsafe_allow_html=True)
    col_submit1, col_submit2 = st.columns([3, 1])
    with col_submit1:
        st.markdown("*Fields marked with * are required")
    with col_submit2:
        if st.button("💾 Save to Database", type="primary", use_container_width=True, key="save_candidate_btn"):
            if st.session_state.form_name and st.session_state.form_email:  # Basic validation
                handle_candidate_save()
            else:
                st.markdown('<div class="error-message">❌ Please fill in at least Name and Email fields.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def handle_candidate_save():
    """Handle the candidate save process with overwrite logic"""
    try:
        # Clean up empty entries
        clean_qualifications = [q for q in st.session_state.qualifications_list if q.get('qualification')]
        clean_skills = [s for s in st.session_state.skills_list if s.get('skill')]
        clean_experience = []
        
        for exp in st.session_state.experience_list:
            if exp.get('position') or exp.get('company'):
                # Clean up empty arrays
                clean_resp = [r for r in exp.get('responsibilities', []) if r.strip()]
                clean_ach = [a for a in exp.get('achievements', []) if a.strip()]
                clean_tech = [t for t in exp.get('technologies', []) if t.strip()]
                
                cleaned_exp = exp.copy()
                cleaned_exp['responsibilities'] = clean_resp
                cleaned_exp['achievements'] = clean_ach
                cleaned_exp['technologies'] = clean_tech
                clean_experience.append(cleaned_exp)
        
        clean_achievements = [a for a in st.session_state.achievements_list if a.strip()]
        
        candidate_data = {
            'name': st.session_state.form_name,
            'current_role': st.session_state.form_current_role,
            'email': st.session_state.form_email,
            'phone': st.session_state.form_phone,
            'notice_period': st.session_state.form_notice_period,
            'current_salary': st.session_state.form_current_salary,
            'industry': st.session_state.form_industry,
            'desired_salary': st.session_state.form_desired_salary,
            'highest_qualification': st.session_state.form_highest_qualification,
            'experience': clean_experience,
            'skills': clean_skills,
            'qualifications': clean_qualifications,
            'achievements': clean_achievements,
            'special_skills': st.session_state.form_special_skills
        }
        
        # Check if candidate already exists
        existing_candidate = st.session_state.db_manager.get_candidate_by_email(st.session_state.form_email)
        
        if existing_candidate:
            # Store the candidate data for potential overwrite
            st.session_state.pending_candidate_data = candidate_data
            st.session_state.existing_candidate_email = st.session_state.form_email
            st.session_state.show_overwrite_dialog = True
            st.rerun()
        else:
            # New candidate, proceed with insert
            try:
                db_result = st.session_state.db_manager.insert_candidate(candidate_data)
                
                # Handle both tuple and boolean returns for backward compatibility
                if isinstance(db_result, tuple):
                    result, message = db_result
                else:
                    result = db_result
                    message = "Operation completed" if result else "Operation failed"
                
                if result:
                    st.markdown('<div class="success-message">✅ Candidate saved successfully!</div>', unsafe_allow_html=True)
                    clear_form_session_state()
                    st.rerun()
                else:
                    st.markdown(f'<div class="error-message">❌ Failed to save candidate: {message}</div>', unsafe_allow_html=True)
                    
            except Exception as db_error:
                st.markdown(f'<div class="error-message">❌ Database error: {str(db_error)}</div>', unsafe_allow_html=True)
                
    except Exception as e:
        st.markdown(f'<div class="error-message">❌ Error saving candidate: {str(e)}</div>', unsafe_allow_html=True)

def show_overwrite_confirmation_dialog():
    """Show the overwrite confirmation dialog"""
    st.markdown('<div class="warning-message">', unsafe_allow_html=True)
    st.markdown("### ⚠️ Candidate Already Exists")
    st.markdown(f"A candidate with email **{st.session_state.existing_candidate_email}** already exists in the database.")
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("**What would you like to do?**")
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("✅ Overwrite Record", type="primary", use_container_width=True, key="overwrite_btn"):
            # Update the existing candidate
            try:
                result, message = st.session_state.db_manager.update_candidate(st.session_state.pending_candidate_data)
                
                if result:
                    st.markdown('<div class="success-message">✅ Candidate record updated successfully!</div>', unsafe_allow_html=True)
                    clear_form_session_state()
                    clear_overwrite_dialog_state()
                    st.rerun()
                else:
                    st.markdown(f'<div class="error-message">❌ Failed to update candidate: {message}</div>', unsafe_allow_html=True)
                    clear_overwrite_dialog_state()
                    st.rerun()
                    
            except Exception as e:
                st.markdown(f'<div class="error-message">❌ Error updating candidate: {str(e)}</div>', unsafe_allow_html=True)
                clear_overwrite_dialog_state()
                st.rerun()
    
    with col2:
        if st.button("❌ Cancel", use_container_width=True, key="cancel_overwrite_btn"):
            clear_overwrite_dialog_state()
            st.markdown('<div class="warning-message">ℹ️ The candidate already exists. Please modify the email address or update the existing record.</div>', unsafe_allow_html=True)
            st.rerun()
    
    with col3:
        st.markdown("*Choose 'Overwrite' to update the existing record with new data, or 'Cancel' to return to the form.*")

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

# ========== SEARCH CANDIDATES TAB ==========
def search_candidates_tab():
    st.markdown('<div class="section-header"><h2>🔍 Search Candidates</h2></div>', unsafe_allow_html=True)
    
    # Clear Search button at the top
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🗑️ Clear Search", type="secondary", use_container_width=True, help="Clear search criteria and results"):
            clear_search_state()
            st.rerun()
    
    search_method = st.radio("Search Method", ["Manual Search", "Job Description Match"])
    
    if search_method == "Manual Search":
        manual_search()
    else:
        job_description_search()
    
    # Display cached search results if available
    if st.session_state.search_performed and st.session_state.cached_search_results:
        display_search_results(st.session_state.cached_search_results)
    elif st.session_state.search_performed and not st.session_state.cached_search_results:
        st.markdown('<div class="warning-message">🔍 No candidates found matching your criteria.</div>', unsafe_allow_html=True)

def clear_search_state():
    """Clear search-related session state"""
    st.session_state.cached_search_criteria = {}
    st.session_state.cached_search_results = []
    st.session_state.search_performed = False

def manual_search():
    st.markdown('<div class="form-container">', unsafe_allow_html=True)
    st.subheader("🔍 Manual Search")
    
    # Pre-populate with cached criteria if available
    cached = st.session_state.cached_search_criteria
    
    with st.form("search_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name_search = st.text_input("Name (contains)", value=cached.get('name', ''))
            role_search = st.text_input("Current Role (contains)", value=cached.get('current_role', ''))
            industry_search = st.text_input("Industry (contains)", value=cached.get('industry', ''))
            skills_search = st.text_input("Skills (contains)", value=cached.get('skills', ''))
            
        with col2:
            qualification_search = st.text_input("Qualifications (contains)", value=cached.get('qualifications', ''))
            experience_years = st.number_input("Minimum Experience Years", min_value=0, value=cached.get('experience_years', 0))
            notice_period_search = st.text_input("Notice Period (contains)", value=cached.get('notice_period', ''))
            
        search_submitted = st.form_submit_button("🔍 Search", type="primary")
    st.markdown('</div>', unsafe_allow_html=True)
    
    if search_submitted:
        search_criteria = {
            'name': name_search,
            'current_role': role_search,
            'industry': industry_search,
            'skills': skills_search,
            'qualifications': qualification_search,
            'experience_years': experience_years,
            'notice_period': notice_period_search
        }
        
        # Cache search criteria
        st.session_state.cached_search_criteria = search_criteria
        
        # Perform search
        results = st.session_state.db_manager.search_candidates(search_criteria)
        
        # Add relevance scores to results
        for candidate in results:
            relevance_score = calculate_manual_search_relevance(candidate, search_criteria)
            candidate['relevance_score'] = relevance_score
        
        # Sort by relevance score (highest first)
        results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        # Cache results
        st.session_state.cached_search_results = results
        st.session_state.search_performed = True
        
        st.rerun()

def job_description_search():
    st.markdown('<div class="form-container">', unsafe_allow_html=True)
    st.subheader("📋 Job Description Match")
    
    job_description = st.text_area("Paste Job Description", height=200, 
                                  placeholder="Paste the job description here...")
    
    if st.button("🎯 Find Matching Candidates", type="primary"):
        if job_description:
            with st.spinner("🤖 Analyzing job description..."):
                try:
                    # Extract requirements from job description using OpenAI
                    requirements = st.session_state.cv_processor.extract_job_requirements(job_description)
                    
                    if requirements:
                        st.subheader("🎯 Extracted Requirements:")
                        st.json(requirements)
                        
                        # Search for matching candidates
                        with st.spinner("🔍 Searching for matching candidates..."):
                            results = st.session_state.db_manager.search_candidates_by_job_requirements(requirements)
                            ranked_results = rank_candidates_by_job_match(results, requirements)
                            
                            # Cache results
                            st.session_state.cached_search_results = ranked_results
                            st.session_state.search_performed = True
                            st.session_state.cached_search_criteria = {'job_description': job_description}
                            
                            st.rerun()
                    else:
                        st.markdown('<div class="error-message">❌ Failed to extract requirements from job description.</div>', unsafe_allow_html=True)
                        
                except Exception as e:
                    st.markdown(f'<div class="error-message">❌ Error processing job description: {str(e)}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="error-message">❌ Please provide a job description.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def calculate_manual_search_relevance(candidate, search_criteria):
    """Calculate relevance score for manual search criteria"""
    score = 0
    total_criteria = 0
    
    try:
        # Name matching
        if search_criteria.get('name'):
            total_criteria += 1
            candidate_name = candidate.get('name', '').lower()
            search_name = search_criteria['name'].lower()
            if search_name in candidate_name:
                score += 1
        
        # Current role matching
        if search_criteria.get('current_role'):
            total_criteria += 1
            candidate_role = candidate.get('current_role', '').lower()
            search_role = search_criteria['current_role'].lower()
            if search_role in candidate_role:
                score += 1
        
        # Industry matching
        if search_criteria.get('industry'):
            total_criteria += 1
            candidate_industry = candidate.get('industry', '').lower()
            search_industry = search_criteria['industry'].lower()
            if search_industry in candidate_industry:
                score += 1
        
        # Skills matching
        if search_criteria.get('skills'):
            total_criteria += 1
            candidate_skills = [skill.get('skill', '').lower() for skill in candidate.get('skills', [])]
            search_skills = search_criteria['skills'].lower()
            skills_match = any(search_skills in skill for skill in candidate_skills)
            if skills_match:
                score += 1
        
        # Qualifications matching
        if search_criteria.get('qualifications'):
            total_criteria += 1
            candidate_quals = [qual.get('qualification', '').lower() for qual in candidate.get('qualifications', [])]
            candidate_highest = candidate.get('highest_qualification', '').lower()
            search_quals = search_criteria['qualifications'].lower()
            quals_match = any(search_quals in qual for qual in candidate_quals) or search_quals in candidate_highest
            if quals_match:
                score += 1
        
        # Notice period matching
        if search_criteria.get('notice_period'):
            total_criteria += 1
            candidate_notice = candidate.get('notice_period', '').lower()
            search_notice = search_criteria['notice_period'].lower()
            if search_notice in candidate_notice:
                score += 1
        
        # Experience years matching
        if search_criteria.get('experience_years', 0) > 0:
            total_criteria += 1
            candidate_exp_years = len(candidate.get('experience', []))
            required_years = search_criteria['experience_years']
            if candidate_exp_years >= required_years:
                score += 1
        
        # Calculate percentage
        if total_criteria > 0:
            return round((score / total_criteria) * 100, 1)
        else:
            return 100  # If no criteria specified, consider it a 100% match
            
    except Exception as e:
        return 0

def rank_candidates_by_job_match(candidates, requirements):
    """Rank candidates based on job requirements match"""
    ranked_candidates = []
    
    for candidate in candidates:
        score = calculate_match_score(candidate, requirements)
        candidate['match_score'] = score
        candidate['relevance_score'] = score  # Also set as relevance_score for consistency
        ranked_candidates.append(candidate)
    
    # Sort by match score (highest first)
    return sorted(ranked_candidates, key=lambda x: x.get('match_score', 0), reverse=True)

def calculate_match_score(candidate, requirements):
    """Enhanced comprehensive match score calculation between candidate and job requirements"""
    score = 0
    max_score = 0
    
    try:
        # 1. Required Skills Matching (25% weight)
        required_skills = requirements.get('required_skills', [])
        if required_skills:
            max_score += 25
            candidate_skills = [skill.get('skill', '').lower() for skill in candidate.get('skills', [])]
            
            # Also collect skills from experience technologies and special skills
            candidate_technologies = []
            for exp in candidate.get('experience', []):
                candidate_technologies.extend([tech.lower() for tech in exp.get('technologies', [])])
            
            special_skills = candidate.get('special_skills', '').lower().split()
            all_candidate_skills = set(candidate_skills + candidate_technologies + special_skills)
            
            matched_skills = 0
            for req_skill in required_skills:
                skill_lower = req_skill.lower()
                if any(skill_lower in candidate_skill or candidate_skill in skill_lower for candidate_skill in all_candidate_skills):
                    matched_skills += 1
            
            if required_skills:
                score += (matched_skills / len(required_skills)) * 25
        
        # 2. Technology Matching (20% weight)
        required_technologies = requirements.get('technologies', [])
        if required_technologies:
            max_score += 20
            candidate_technologies = []
            candidate_skills = [skill.get('skill', '').lower() for skill in candidate.get('skills', [])]
            
            # Collect technologies from experience
            for exp in candidate.get('experience', []):
                candidate_technologies.extend([tech.lower() for tech in exp.get('technologies', [])])
            
            all_candidate_tech = set(candidate_technologies + candidate_skills)
            
            matched_tech = 0
            for req_tech in required_technologies:
                tech_lower = req_tech.lower()
                if any(tech_lower in candidate_tech or candidate_tech in tech_lower for candidate_tech in all_candidate_tech):
                    matched_tech += 1
            
            if required_technologies:
                score += (matched_tech / len(required_technologies)) * 20
        
        # 3. Experience Years Matching (15% weight)
        min_experience = requirements.get('min_experience_years', 0)
        preferred_experience = requirements.get('preferred_experience_years', 0)
        if min_experience > 0 or preferred_experience > 0:
            max_score += 15
            candidate_exp_years = len(candidate.get('experience', []))
            target_years = preferred_experience if preferred_experience > 0 else min_experience
            
            if candidate_exp_years >= target_years:
                score += 15
            elif candidate_exp_years >= min_experience:
                # Partial score for meeting minimum but not preferred
                score += (candidate_exp_years / target_years) * 15
            else:
                # Reduced score for not meeting minimum
                score += (candidate_exp_years / min_experience) * 7.5 if min_experience > 0 else 0
        
        # 4. Experience Area Matching (15% weight)
        required_experience_areas = requirements.get('required_experience_areas', [])
        if required_experience_areas:
            max_score += 15
            candidate_experience_text = ""
            candidate_roles = []
            
            for exp in candidate.get('experience', []):
                candidate_experience_text += f" {exp.get('position', '')} {' '.join(exp.get('responsibilities', []))}"
                candidate_roles.append(exp.get('position', '').lower())
            
            candidate_experience_text = candidate_experience_text.lower()
            
            matched_areas = 0
            for area in required_experience_areas:
                area_lower = area.lower()
                # Check in experience text and role titles
                if (area_lower in candidate_experience_text or 
                    any(area_lower in role for role in candidate_roles)):
                    matched_areas += 1
            
            if required_experience_areas:
                score += (matched_areas / len(required_experience_areas)) * 15
        
        # 5. Qualification Matching (10% weight)
        required_qualifications = requirements.get('required_qualifications', [])
        if required_qualifications:
            max_score += 10
            candidate_quals = [qual.get('qualification', '').lower() for qual in candidate.get('qualifications', [])]
            candidate_highest = candidate.get('highest_qualification', '').lower()
            
            matched_quals = 0
            for req_qual in required_qualifications:
                qual_lower = req_qual.lower()
                if (qual_lower in candidate_highest or
                    any(qual_lower in cand_qual or cand_qual in qual_lower for cand_qual in candidate_quals)):
                    matched_quals += 1
            
            if required_qualifications:
                score += (matched_quals / len(required_qualifications)) * 10
        
        # 6. Industry Matching (5% weight)
        required_industry = requirements.get('industry', '')
        if required_industry:
            max_score += 5
            candidate_industry = candidate.get('industry', '').lower()
            required_industry_lower = required_industry.lower()
            
            if candidate_industry:
                # Exact match
                if candidate_industry == required_industry_lower:
                    score += 5
                # Partial match (contains keywords)
                elif (required_industry_lower in candidate_industry or 
                      candidate_industry in required_industry_lower):
                    score += 3
                # Keyword overlap
                else:
                    industry_keywords = required_industry_lower.split()
                    matches = sum(1 for keyword in industry_keywords if keyword in candidate_industry)
                    if matches > 0:
                        score += (matches / len(industry_keywords)) * 2
        
        # 7. Seniority Level Matching (5% weight)
        required_seniority = requirements.get('seniority_level', '')
        if required_seniority:
            max_score += 5
            candidate_role = candidate.get('current_role', '').lower()
            required_seniority_lower = required_seniority.lower()
            candidate_exp_count = len(candidate.get('experience', []))
            
            # Check role title for seniority indicators
            seniority_match = False
            if required_seniority_lower in candidate_role:
                seniority_match = True
                score += 5
            elif 'senior' in required_seniority_lower and ('lead' in candidate_role or 'principal' in candidate_role):
                seniority_match = True
                score += 4
            elif 'lead' in required_seniority_lower and 'senior' in candidate_role and candidate_exp_count >= 4:
                seniority_match = True
                score += 3
            
            # If no direct match, check experience count alignment
            if not seniority_match:
                if 'entry' in required_seniority_lower and candidate_exp_count <= 2:
                    score += 3
                elif 'junior' in required_seniority_lower and candidate_exp_count <= 3:
                    score += 3
                elif 'mid' in required_seniority_lower and 2 <= candidate_exp_count <= 5:
                    score += 3
                elif 'senior' in required_seniority_lower and candidate_exp_count >= 4:
                    score += 2
        
        # 8. Responsibilities Matching (5% weight)
        key_responsibilities = requirements.get('key_responsibilities', [])
        if key_responsibilities:
            max_score += 5
            candidate_responsibilities_text = ""
            
            for exp in candidate.get('experience', []):
                candidate_responsibilities_text += " " + " ".join(exp.get('responsibilities', []))
            
            candidate_responsibilities_text = candidate_responsibilities_text.lower()
            
            matched_responsibilities = 0
            for responsibility in key_responsibilities:
                resp_lower = responsibility.lower()
                # Look for keywords from the responsibility in candidate's experience
                resp_keywords = resp_lower.split()
                keyword_matches = sum(1 for keyword in resp_keywords if len(keyword) > 3 and keyword in candidate_responsibilities_text)
                if keyword_matches >= len(resp_keywords) // 2:  # At least half the keywords match
                    matched_responsibilities += 1
            
            if key_responsibilities:
                score += (matched_responsibilities / len(key_responsibilities)) * 5
        
        # 9. Leadership/Management Experience (bonus weight if required)
        if requirements.get('team_leadership', False):
            max_score += 3
            candidate_experience_text = ""
            
            for exp in candidate.get('experience', []):
                candidate_experience_text += f" {exp.get('position', '')} {' '.join(exp.get('responsibilities', []))}"
                if exp.get('team_size'):
                    score += 3  # Has managed a team
                    break
            
            # Look for leadership keywords in experience
            leadership_keywords = ['manage', 'lead', 'supervise', 'mentor', 'team', 'direct', 'coordinate']
            candidate_text_lower = candidate_experience_text.lower()
            leadership_matches = sum(1 for keyword in leadership_keywords if keyword in candidate_text_lower)
            
            if leadership_matches >= 2:
                score += min(3, leadership_matches)
        
        # 10. Special Requirements Bonus
        special_requirements = requirements.get('special_requirements', [])
        if special_requirements:
            max_score += 2
            candidate_special_skills = candidate.get('special_skills', '').lower()
            candidate_achievements = [ach.lower() for ach in candidate.get('achievements', [])]
            
            matched_special = 0
            for special_req in special_requirements:
                special_lower = special_req.lower()
                if (special_lower in candidate_special_skills or
                    any(special_lower in ach for ach in candidate_achievements)):
                    matched_special += 1
            
            if special_requirements:
                score += (matched_special / len(special_requirements)) * 2
        
        # Ensure max_score is at least 100 for percentage calculation
        if max_score == 0:
            max_score = 100
            # Basic fallback scoring if no specific requirements
            if candidate.get('skills'):
                score += 30
            if candidate.get('experience'):
                score += 40
            if candidate.get('qualifications'):
                score += 20
            if candidate.get('industry'):
                score += 10
        
        # Calculate percentage and apply bonuses
        final_score = (score / max_score) * 100
        
        # Bonus for preferred skills
        preferred_skills = requirements.get('preferred_skills', [])
        if preferred_skills:
            candidate_skills = [skill.get('skill', '').lower() for skill in candidate.get('skills', [])]
            preferred_matches = sum(1 for pref_skill in preferred_skills 
                                 if any(pref_skill.lower() in cand_skill for cand_skill in candidate_skills))
            if preferred_matches > 0:
                final_score += min(5, (preferred_matches / len(preferred_skills)) * 5)  # Up to 5% bonus
        
        # Cap at 100%
        final_score = min(100, final_score)
        
        return round(final_score, 1)
            
    except Exception as e:
        logging.error(f"Error calculating match score: {str(e)}")
        return 0

def display_search_results(results, show_match_score=None):
    """Display search results with View Details buttons"""
    if results:
        # Determine if we should show match scores
        if show_match_score is None:
            show_match_score = any(candidate.get('match_score') is not None for candidate in results)
        
        st.markdown('<div class="section-header">', unsafe_allow_html=True)
        st.subheader(f"📊 Search Results ({len(results)} candidates found)")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("💡 **Click 'View Details' to see and edit full candidate information**")
        st.markdown("---")
        
        # Display candidates
        for idx, candidate in enumerate(results):
            with st.container():
                st.markdown('<div class="candidate-card">', unsafe_allow_html=True)
                
                # Candidate summary row
                col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 1])
                
                with col1:
                    st.markdown(f"**👤 {candidate.get('name', 'N/A')}**")
                    st.write(f"📧 {candidate.get('email', 'N/A')}")
                
                with col2:
                    st.write(f"**Role:** {candidate.get('current_role', 'N/A')}")
                    st.write(f"**Industry:** {candidate.get('industry', 'N/A')}")
                
                with col3:
                    st.write(f"**Phone:** {candidate.get('phone', 'N/A')}")
                    st.write(f"**Notice:** {candidate.get('notice_period', 'N/A')}")
                
                with col4:
                    st.write(f"**Education:** {candidate.get('highest_qualification', 'N/A')}")
                    
                    # Show relevance score (either from manual search or job matching)
                    relevance_score = candidate.get('relevance_score') or candidate.get('match_score')
                    if relevance_score is not None:
                        if relevance_score >= 80:
                            st.markdown(f"**Relevance:** 🟢 {relevance_score}%")
                        elif relevance_score >= 60:
                            st.markdown(f"**Relevance:** 🟡 {relevance_score}%")
                        else:
                            st.markdown(f"**Relevance:** 🔴 {relevance_score}%")
                
                with col5:
                    # View Details button - this navigates to the candidate details page
                    button_key = f"view_details_{idx}_{candidate.get('email', 'unknown')}"
                    if st.button("👁️ View Details", key=button_key, type="primary", help="View and edit candidate details"):
                        view_candidate_details(candidate)
                
                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown("")  # Add space between cards
    else:
        st.markdown('<div class="warning-message">🔍 No candidates found matching your criteria.</div>', unsafe_allow_html=True)

# ========== DASHBOARD TAB ==========
def dashboard_tab():
    st.markdown('<div class="section-header"><h2>📊 Dashboard</h2></div>', unsafe_allow_html=True)
    
    # Get statistics
    stats = st.session_state.db_manager.get_dashboard_stats()
    sync_status = st.session_state.db_manager.get_sync_status()
    
    # Professional metrics display
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Candidates", stats.get('total_candidates', 0))
    
    with col2:
        st.metric("Industries", stats.get('unique_industries', 0))
    
    with col3:
        st.metric("Avg Experience", f"{stats.get('avg_experience', 0):.1f} years")
    
    with col4:
        backup_status = "✅ Active" if st.session_state.db_manager.last_backup_time else "❌ Never"
        st.metric("Backup Status", backup_status)
    
    with col5:
        db_size = f"{stats.get('database_size_mb', 0):.1f} MB"
        st.metric("DB Size", db_size)
    
    # Sync Status Section
    st.markdown("---")
    st.markdown('<div class="form-container">', unsafe_allow_html=True)
    st.subheader("🔄 Database Sync Status")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if sync_status['last_sync_time']:
            st.success(f"✅ Last sync: {sync_status['last_sync_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            st.warning("⚠️ No sync performed yet")
        
        if sync_status['is_syncing']:
            st.info("🔄 Sync in progress...")
        
        # Show local database info
        if sync_status['local_db_exists']:
            st.info(f"📁 Local DB size: {sync_status['local_db_size'] / (1024*1024):.1f} MB")
        else:
            st.warning("⚠️ Local database not found")
    
    with col2:
        sync_col1, sync_col2 = st.columns(2)
        
        with sync_col1:
            if st.button("📤 Sync to Cloud", type="primary", help="Upload local changes to blob storage"):
                with st.spinner("Syncing to cloud..."):
                    result = st.session_state.db_manager.sync_database()
                    if result:
                        st.success("✅ Sync successful!")
                        st.rerun()
                    else:
                        st.error("❌ Sync failed!")
        
        with sync_col2:
            if st.button("📥 Refresh from Cloud", help="Download latest from blob storage"):
                with st.spinner("Refreshing from cloud..."):
                    result = st.session_state.db_manager.refresh_database()
                    if result:
                        st.success("✅ Refresh successful!")
                        st.rerun()
                    else:
                        st.error("❌ Refresh failed!")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Backup controls with professional styling
    st.markdown('<div class="form-container">', unsafe_allow_html=True)
    st.subheader("🔄 Database Backup")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💾 Create Backup Now", type="primary"):
            with st.spinner("Creating backup..."):
                result = st.session_state.db_manager.backup_to_blob()
                if result:
                    st.markdown('<div class="success-message">✅ Backup created successfully!</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="error-message">❌ Backup failed!</div>', unsafe_allow_html=True)
    
    with col2:
        if st.button("📥 Restore from Latest Backup"):
            with st.spinner("Restoring from backup..."):
                result = st.session_state.db_manager.restore_from_backup()
                if result:
                    st.markdown('<div class="success-message">✅ Database restored successfully!</div>', unsafe_allow_html=True)
                    st.rerun()
                else:
                    st.markdown('<div class="error-message">❌ Restore failed!</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()