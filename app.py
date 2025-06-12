import streamlit as st
import pandas as pd
import json
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
    
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #1e3a8a 0%, #3b82f6 100%);
    }
    
    /* Metrics styling */
    .metric-container {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
        text-align: center;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
    }
    
    /* File uploader styling */
    .uploadedFile {
        border: 2px dashed #3b82f6;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        background: #f8fafc;
    }
    
    /* Table styling */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid #e2e8f0;
    }
    
    /* Professional spacing */
    .professional-spacing {
        margin: 1.5rem 0;
    }
    
    /* Enhanced form section */
    .form-section {
        background: #f8fafc;
        padding: 1.5rem;
        border-radius: 8px;
        margin: 1rem 0;
        border: 1px solid #e2e8f0;
    }
    
    /* Enhanced expander */
    .streamlit-expanderHeader {
        background: #f1f5f9;
        border-radius: 6px;
        font-weight: 600;
    }
    
    /* Professional card styling */
    .professional-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
        margin: 1rem 0;
    }
    
    /* Modal styling */
    .modal-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0, 0, 0, 0.7);
        z-index: 9999;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    
    .modal-content {
        background: white;
        border-radius: 15px;
        padding: 2rem;
        width: 90%;
        max-width: 1200px;
        max-height: 90vh;
        overflow-y: auto;
        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.3);
        position: relative;
    }
    
    .modal-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 2rem;
        padding-bottom: 1rem;
        border-bottom: 2px solid #e2e8f0;
    }
    
    .modal-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: #1e3a8a;
        margin: 0;
    }
    
    .close-button {
        background: #ef4444;
        color: white;
        border: none;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        font-size: 1.2rem;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .close-button:hover {
        background: #dc2626;
    }
    
    /* Clickable table rows */
    .clickable-row {
        cursor: pointer;
        transition: background-color 0.2s ease;
    }
    
    .clickable-row:hover {
        background-color: #f1f5f9 !important;
    }
    
    /* Edit mode styling */
    .edit-mode {
        background: #fef3c7;
        border: 2px solid #f59e0b;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .view-mode {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
def initialize_session_state():
    """Initialize all session state variables"""
    if 'extracted_data' not in st.session_state:
        st.session_state.extracted_data = None
    if 'cv_processed' not in st.session_state:
        st.session_state.cv_processed = False
    if 'db_manager' not in st.session_state:
        st.session_state.db_manager = DatabaseManager()
    if 'cv_processor' not in st.session_state:
        st.session_state.cv_processor = CVProcessor()
    if 'show_overwrite_dialog' not in st.session_state:
        st.session_state.show_overwrite_dialog = False
    if 'pending_candidate_data' not in st.session_state:
        st.session_state.pending_candidate_data = None
    if 'existing_candidate_email' not in st.session_state:
        st.session_state.existing_candidate_email = None
    
    # Modal management
    if 'show_modal' not in st.session_state:
        st.session_state.show_modal = False
    if 'selected_candidate' not in st.session_state:
        st.session_state.selected_candidate = None
    if 'modal_edit_mode' not in st.session_state:
        st.session_state.modal_edit_mode = False
    
    # Modal form data
    if 'modal_name' not in st.session_state:
        st.session_state.modal_name = ""
    if 'modal_email' not in st.session_state:
        st.session_state.modal_email = ""
    if 'modal_phone' not in st.session_state:
        st.session_state.modal_phone = ""
    if 'modal_current_role' not in st.session_state:
        st.session_state.modal_current_role = ""
    if 'modal_industry' not in st.session_state:
        st.session_state.modal_industry = ""
    if 'modal_notice_period' not in st.session_state:
        st.session_state.modal_notice_period = ""
    if 'modal_current_salary' not in st.session_state:
        st.session_state.modal_current_salary = ""
    if 'modal_desired_salary' not in st.session_state:
        st.session_state.modal_desired_salary = ""
    if 'modal_highest_qualification' not in st.session_state:
        st.session_state.modal_highest_qualification = ""
    if 'modal_special_skills' not in st.session_state:
        st.session_state.modal_special_skills = ""
    if 'modal_qualifications_list' not in st.session_state:
        st.session_state.modal_qualifications_list = []
    if 'modal_skills_list' not in st.session_state:
        st.session_state.modal_skills_list = []
    if 'modal_experience_list' not in st.session_state:
        st.session_state.modal_experience_list = []
    if 'modal_achievements_list' not in st.session_state:
        st.session_state.modal_achievements_list = []
    
    # Form data session states
    if 'form_name' not in st.session_state:
        st.session_state.form_name = ""
    if 'form_email' not in st.session_state:
        st.session_state.form_email = ""
    if 'form_phone' not in st.session_state:
        st.session_state.form_phone = ""
    if 'form_current_role' not in st.session_state:
        st.session_state.form_current_role = ""
    if 'form_industry' not in st.session_state:
        st.session_state.form_industry = ""
    if 'form_notice_period' not in st.session_state:
        st.session_state.form_notice_period = ""
    if 'form_current_salary' not in st.session_state:
        st.session_state.form_current_salary = ""
    if 'form_desired_salary' not in st.session_state:
        st.session_state.form_desired_salary = ""
    if 'form_highest_qualification' not in st.session_state:
        st.session_state.form_highest_qualification = ""
    if 'form_special_skills' not in st.session_state:
        st.session_state.form_special_skills = ""

# Initialize session state
initialize_session_state()

def main():
    # Professional header
    st.markdown("""
    <div class="main-header">
        <h1>🎯 HR Candidate Management Tool</h1>
        <p>AI-Powered CV Processing and Intelligent Candidate Matching</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Check if modal should be shown FIRST
    if st.session_state.show_modal and st.session_state.selected_candidate:
        show_candidate_modal()
        return
    
    # Sidebar navigation with enhanced styling
    st.sidebar.markdown("""
    <div style="text-align: center; padding: 1rem; color: white;">
        <h2>🚀 Navigation</h2>
    </div>
    """, unsafe_allow_html=True)
    
    tab = st.sidebar.radio(
        "Select Function", 
        ["📄 Upload CV", "🔍 Search Candidates", "📊 Dashboard"],
        key="main_nav"
    )
    
    if tab == "📄 Upload CV":
        upload_cv_tab()
    elif tab == "🔍 Search Candidates":
        search_candidates_tab()
    elif tab == "📊 Dashboard":
        dashboard_tab()

def upload_cv_tab():
    st.markdown('<div class="section-header"><h2>📄 Upload and Process CV</h2></div>', unsafe_allow_html=True)
    
    # Professional upload container
    with st.container():
        st.markdown('<div class="form-container">', unsafe_allow_html=True)
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

def initialize_form_data(data):
    """Initialize form data from extracted CV data"""
    # Initialize dynamic lists first
    if 'qualifications_list' not in st.session_state:
        st.session_state.qualifications_list = data.get('qualifications', [])
    if 'skills_list' not in st.session_state:
        st.session_state.skills_list = data.get('skills', [])
    if 'experience_list' not in st.session_state:
        st.session_state.experience_list = data.get('experience', [])
    if 'achievements_list' not in st.session_state:
        st.session_state.achievements_list = data.get('achievements', [])
    
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
    
    # Experience Section
    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    st.markdown("### 💼 Work Experience")
    
    # Display experience in expandable sections
    for i, exp in enumerate(st.session_state.experience_list):
        with st.expander(f"Position {i+1}: {exp.get('position', 'New Position')}"):
            col_exp1, col_exp2 = st.columns(2)
            with col_exp1:
                exp['position'] = st.text_input(
                    "Job Title", 
                    value=exp.get('position', ''),
                    key=f"pos_{i}"
                )
                exp['company'] = st.text_input(
                    "Company", 
                    value=exp.get('company', ''),
                    key=f"comp_{i}"
                )
            with col_exp2:
                exp['years'] = st.text_input(
                    "Duration", 
                    value=exp.get('years', ''),
                    key=f"duration_{i}"
                )
            
            # Responsibilities
            st.markdown("**Key Responsibilities:**")
            responsibilities = exp.get('responsibilities', [])
            
            # Initialize responsibilities if not exists
            if not responsibilities:
                exp['responsibilities'] = ['']
                responsibilities = exp['responsibilities']
            
            for j, resp in enumerate(responsibilities):
                col_resp1, col_resp2 = st.columns([5, 1])
                with col_resp1:
                    responsibilities[j] = st.text_input(
                        f"Responsibility {j+1}", 
                        value=resp,
                        key=f"resp_{i}_{j}"
                    )
                with col_resp2:
                    if st.button("🗑️", key=f"del_resp_{i}_{j}", help="Delete responsibility"):
                        responsibilities.pop(j)
                        st.rerun()
            
            col_add_resp, col_del_exp = st.columns(2)
            with col_add_resp:
                if st.button(f"➕ Add Responsibility", key=f"add_resp_{i}"):
                    responsibilities.append('')
                    st.rerun()
            
            with col_del_exp:
                if st.button(f"🗑️ Delete Position", key=f"del_exp_{i}"):
                    st.session_state.experience_list.pop(i)
                    st.rerun()
    
    if st.button("➕ Add Work Experience", key="add_experience_btn"):
        st.session_state.experience_list.append({
            'position': '', 
            'company': '', 
            'years': '', 
            'responsibilities': ['']
        })
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Achievements Section
    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    st.markdown("### 🏆 Achievements")
    
    for i, achievement in enumerate(st.session_state.achievements_list):
        col_ach1, col_ach2 = st.columns([5, 1])
        with col_ach1:
            st.session_state.achievements_list[i] = st.text_area(
                f"Achievement {i+1}", 
                value=achievement,
                height=50,
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
                # Clean up empty responsibilities
                clean_resp = [r for r in exp.get('responsibilities', []) if r.strip()]
                exp['responsibilities'] = clean_resp
                clean_experience.append(exp)
        
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
        'form_desired_salary', 'form_highest_qualification', 'form_special_skills'
    ]
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

def clear_overwrite_dialog_state():
    """Clear overwrite dialog state"""
    st.session_state.show_overwrite_dialog = False
    st.session_state.pending_candidate_data = None
    st.session_state.existing_candidate_email = None

def open_candidate_modal(candidate_data):
    """Open modal with candidate data"""
    # Set modal state
    st.session_state.show_modal = True
    st.session_state.selected_candidate = candidate_data
    st.session_state.modal_edit_mode = False
    
    # Initialize modal form data from candidate
    st.session_state.modal_name = candidate_data.get('name', '')
    st.session_state.modal_email = candidate_data.get('email', '')
    st.session_state.modal_phone = candidate_data.get('phone', '')
    st.session_state.modal_current_role = candidate_data.get('current_role', '')
    st.session_state.modal_industry = candidate_data.get('industry', '')
    st.session_state.modal_notice_period = candidate_data.get('notice_period', '')
    st.session_state.modal_current_salary = candidate_data.get('current_salary', '')
    st.session_state.modal_desired_salary = candidate_data.get('desired_salary', '')
    st.session_state.modal_highest_qualification = candidate_data.get('highest_qualification', '')
    st.session_state.modal_special_skills = candidate_data.get('special_skills', '')
    
    # Initialize lists
    st.session_state.modal_qualifications_list = candidate_data.get('qualifications', []).copy()
    st.session_state.modal_skills_list = candidate_data.get('skills', []).copy()
    st.session_state.modal_experience_list = candidate_data.get('experience', []).copy()
    st.session_state.modal_achievements_list = candidate_data.get('achievements', []).copy()
    
    # CRITICAL: Force page refresh to show modal
    st.rerun()

def close_candidate_modal():
    """Close the modal"""
    st.session_state.show_modal = False
    st.session_state.selected_candidate = None
    st.session_state.modal_edit_mode = False
    # CRITICAL: Force page refresh to hide modal
    st.rerun()

def show_candidate_modal():
    """Display the candidate modal using Streamlit native components"""
    if not st.session_state.selected_candidate:
        return
    
    candidate = st.session_state.selected_candidate
    
    # Create a full-width container for modal
    with st.container():
        # Modal header with professional styling
        st.markdown("""
        <div style="background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%); 
                    padding: 1.5rem; border-radius: 10px; margin-bottom: 1rem;">
            <h2 style="color: white; margin: 0; text-align: center;">
                👤 Candidate Details: {name}
            </h2>
        </div>
        """.format(name=candidate.get('name', 'Unknown')), unsafe_allow_html=True)
        
        # Control buttons
        col1, col2, col3, col4 = st.columns([2, 1, 1, 2])
        
        with col2:
            if st.button("✏️ Edit Mode", key="edit_modal_btn", help="Edit candidate information", use_container_width=True):
                st.session_state.modal_edit_mode = not st.session_state.modal_edit_mode
                st.rerun()
        
        with col3:
            if st.button("❌ Close", key="close_modal_btn", use_container_width=True):
                close_candidate_modal()
        
        st.markdown("---")
        
        # Show form in edit or view mode
        if st.session_state.modal_edit_mode:
            st.markdown('<div style="background: #fef3c7; padding: 1rem; border-radius: 8px; border: 2px solid #f59e0b; margin-bottom: 1rem;">', unsafe_allow_html=True)
            st.markdown("### ✏️ EDIT MODE - Make changes and save to update the database")
            st.markdown('</div>', unsafe_allow_html=True)
            show_modal_edit_form()
        else:
            st.markdown('<div style="background: #f0f9ff; padding: 1rem; border-radius: 8px; border: 2px solid #0ea5e9; margin-bottom: 1rem;">', unsafe_allow_html=True)
            st.markdown("### 👁️ VIEW MODE - Click 'Edit Mode' to make changes")
            st.markdown('</div>', unsafe_allow_html=True)
            show_modal_view_data()

def show_modal_view_data():
    """Show candidate data in view mode"""
    candidate = st.session_state.selected_candidate
    
    # Personal Information
    st.markdown('<div class="view-mode">', unsafe_allow_html=True)
    st.markdown("### 👤 Personal Information")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Name:** {candidate.get('name', 'N/A')}")
        st.write(f"**Email:** {candidate.get('email', 'N/A')}")
        st.write(f"**Phone:** {candidate.get('phone', 'N/A')}")
    
    with col2:
        st.write(f"**Current Role:** {candidate.get('current_role', 'N/A')}")
        st.write(f"**Industry:** {candidate.get('industry', 'N/A')}")
        st.write(f"**Notice Period:** {candidate.get('notice_period', 'N/A')}")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Salary Information
    st.markdown('<div class="view-mode">', unsafe_allow_html=True)
    st.markdown("### 💰 Salary Information")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Current Salary:** {candidate.get('current_salary', 'N/A')}")
    with col2:
        st.write(f"**Desired Salary:** {candidate.get('desired_salary', 'N/A')}")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Education
    st.markdown('<div class="view-mode">', unsafe_allow_html=True)
    st.markdown("### 🎓 Education")
    st.write(f"**Highest Qualification:** {candidate.get('highest_qualification', 'N/A')}")
    
    if candidate.get('qualifications'):
        st.markdown("**Detailed Qualifications:**")
        quals_df = pd.DataFrame(candidate['qualifications'])
        st.dataframe(quals_df, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Skills
    if candidate.get('skills'):
        st.markdown('<div class="view-mode">', unsafe_allow_html=True)
        st.markdown("### 🛠️ Skills")
        skills_df = pd.DataFrame(candidate['skills'])
        st.dataframe(skills_df, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Experience
    if candidate.get('experience'):
        st.markdown('<div class="view-mode">', unsafe_allow_html=True)
        st.markdown("### 💼 Work Experience")
        for i, exp in enumerate(candidate['experience']):
            with st.expander(f"Position {i+1}: {exp.get('position', 'N/A')} at {exp.get('company', 'N/A')}"):
                st.write(f"**Duration:** {exp.get('years', 'N/A')}")
                if exp.get('responsibilities'):
                    st.write("**Responsibilities:**")
                    for resp in exp['responsibilities']:
                        st.write(f"• {resp}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Achievements
    if candidate.get('achievements'):
        st.markdown('<div class="view-mode">', unsafe_allow_html=True)
        st.markdown("### 🏆 Achievements")
        for achievement in candidate['achievements']:
            st.write(f"• {achievement}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Special Skills
    if candidate.get('special_skills'):
        st.markdown('<div class="view-mode">', unsafe_allow_html=True)
        st.markdown("### ⭐ Special Skills & Certifications")
        st.write(candidate.get('special_skills'))
        st.markdown('</div>', unsafe_allow_html=True)

def show_modal_edit_form():
    """Show candidate data in edit mode"""
    st.markdown('<div class="edit-mode">', unsafe_allow_html=True)
    st.markdown("### ✏️ Edit Mode - Make changes and save to update the database")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Personal Information Section
    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    st.markdown("### 👤 Personal Information")
    col1, col2 = st.columns(2)
    
    with col1:
        st.session_state.modal_name = st.text_input(
            "Full Name *", 
            value=st.session_state.modal_name, 
            key="modal_name_input"
        )
        st.session_state.modal_email = st.text_input(
            "Email Address *", 
            value=st.session_state.modal_email, 
            key="modal_email_input"
        )
        st.session_state.modal_phone = st.text_input(
            "Phone Number", 
            value=st.session_state.modal_phone, 
            key="modal_phone_input"
        )
        
    with col2:
        st.session_state.modal_current_role = st.text_input(
            "Current Role", 
            value=st.session_state.modal_current_role, 
            key="modal_role_input"
        )
        st.session_state.modal_industry = st.text_input(
            "Industry", 
            value=st.session_state.modal_industry, 
            key="modal_industry_input"
        )
        st.session_state.modal_notice_period = st.text_input(
            "Notice Period", 
            value=st.session_state.modal_notice_period, 
            key="modal_notice_input"
        )
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Salary Information
    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    st.markdown("### 💰 Salary Information")
    col3, col4 = st.columns(2)
    with col3:
        st.session_state.modal_current_salary = st.text_input(
            "Current Salary", 
            value=st.session_state.modal_current_salary, 
            key="modal_current_sal"
        )
    with col4:
        st.session_state.modal_desired_salary = st.text_input(
            "Desired Salary", 
            value=st.session_state.modal_desired_salary, 
            key="modal_desired_sal"
        )
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Education
    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    st.markdown("### 🎓 Education")
    st.session_state.modal_highest_qualification = st.text_input(
        "Highest Qualification", 
        value=st.session_state.modal_highest_qualification, 
        key="modal_highest_qual"
    )
    
    # Qualifications
    st.markdown("**Detailed Qualifications:**")
    for i, qual in enumerate(st.session_state.modal_qualifications_list):
        col_qual1, col_qual2, col_qual3, col_qual4 = st.columns([3, 3, 2, 1])
        with col_qual1:
            qual['qualification'] = st.text_input(
                f"Qualification {i+1}", 
                value=qual.get('qualification', ''),
                key=f"modal_qual_{i}"
            )
        with col_qual2:
            qual['institution'] = st.text_input(
                f"Institution {i+1}", 
                value=qual.get('institution', ''),
                key=f"modal_inst_{i}"
            )
        with col_qual3:
            qual['year'] = st.text_input(
                f"Year {i+1}", 
                value=qual.get('year', ''),
                key=f"modal_year_{i}"
            )
        with col_qual4:
            if st.button("🗑️", key=f"modal_del_qual_{i}", help="Delete qualification"):
                st.session_state.modal_qualifications_list.pop(i)
                st.rerun()
    
    if st.button("➕ Add Qualification", key="modal_add_qualification_btn"):
        st.session_state.modal_qualifications_list.append({'qualification': '', 'institution': '', 'year': '', 'grade': ''})
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Skills Section
    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    st.markdown("### 🛠️ Skills")
    
    for i, skill in enumerate(st.session_state.modal_skills_list):
        col_skill1, col_skill2, col_skill3 = st.columns([4, 2, 1])
        with col_skill1:
            skill['skill'] = st.text_input(
                f"Skill {i+1}", 
                value=skill.get('skill', ''),
                key=f"modal_skill_{i}"
            )
        with col_skill2:
            skill['proficiency'] = st.selectbox(
                f"Level {i+1}",
                options=[1, 2, 3, 4, 5],
                index=min(skill.get('proficiency', 3) - 1, 4),
                format_func=lambda x: f"{x} - {'Beginner' if x==1 else 'Basic' if x==2 else 'Intermediate' if x==3 else 'Advanced' if x==4 else 'Expert'}",
                key=f"modal_prof_{i}"
            )
        with col_skill3:
            if st.button("🗑️", key=f"modal_del_skill_{i}", help="Delete skill"):
                st.session_state.modal_skills_list.pop(i)
                st.rerun()
    
    if st.button("➕ Add Skill", key="modal_add_skill_btn"):
        st.session_state.modal_skills_list.append({'skill': '', 'proficiency': 3})
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Experience Section
    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    st.markdown("### 💼 Work Experience")
    
    for i, exp in enumerate(st.session_state.modal_experience_list):
        with st.expander(f"Position {i+1}: {exp.get('position', 'New Position')}"):
            col_exp1, col_exp2 = st.columns(2)
            with col_exp1:
                exp['position'] = st.text_input(
                    "Job Title", 
                    value=exp.get('position', ''),
                    key=f"modal_pos_{i}"
                )
                exp['company'] = st.text_input(
                    "Company", 
                    value=exp.get('company', ''),
                    key=f"modal_comp_{i}"
                )
            with col_exp2:
                exp['years'] = st.text_input(
                    "Duration", 
                    value=exp.get('years', ''),
                    key=f"modal_duration_{i}"
                )
            
            # Responsibilities
            st.markdown("**Key Responsibilities:**")
            responsibilities = exp.get('responsibilities', [])
            
            if not responsibilities:
                exp['responsibilities'] = ['']
                responsibilities = exp['responsibilities']
            
            for j, resp in enumerate(responsibilities):
                col_resp1, col_resp2 = st.columns([5, 1])
                with col_resp1:
                    responsibilities[j] = st.text_input(
                        f"Responsibility {j+1}", 
                        value=resp,
                        key=f"modal_resp_{i}_{j}"
                    )
                with col_resp2:
                    if st.button("🗑️", key=f"modal_del_resp_{i}_{j}", help="Delete responsibility"):
                        responsibilities.pop(j)
                        st.rerun()
            
            col_add_resp, col_del_exp = st.columns(2)
            with col_add_resp:
                if st.button(f"➕ Add Responsibility", key=f"modal_add_resp_{i}"):
                    responsibilities.append('')
                    st.rerun()
            
            with col_del_exp:
                if st.button(f"🗑️ Delete Position", key=f"modal_del_exp_{i}"):
                    st.session_state.modal_experience_list.pop(i)
                    st.rerun()
    
    if st.button("➕ Add Work Experience", key="modal_add_experience_btn"):
        st.session_state.modal_experience_list.append({
            'position': '', 
            'company': '', 
            'years': '', 
            'responsibilities': ['']
        })
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Achievements Section
    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    st.markdown("### 🏆 Achievements")
    
    for i, achievement in enumerate(st.session_state.modal_achievements_list):
        col_ach1, col_ach2 = st.columns([5, 1])
        with col_ach1:
            st.session_state.modal_achievements_list[i] = st.text_area(
                f"Achievement {i+1}", 
                value=achievement,
                height=50,
                key=f"modal_ach_{i}"
            )
        with col_ach2:
            st.write("")
            if st.button("🗑️", key=f"modal_del_ach_{i}", help="Delete achievement"):
                st.session_state.modal_achievements_list.pop(i)
                st.rerun()
    
    if st.button("➕ Add Achievement", key="modal_add_achievement_btn"):
        st.session_state.modal_achievements_list.append('')
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Special Skills
    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    st.markdown("### ⭐ Special Skills & Certifications")
    st.session_state.modal_special_skills = st.text_area(
        "Special Skills", 
        value=st.session_state.modal_special_skills, 
        height=100, 
        key="modal_special_skills_input"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Save changes
    st.markdown("---")
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("💾 Save Changes", type="primary", use_container_width=True, key="modal_save_btn"):
            if st.session_state.modal_name and st.session_state.modal_email:
                save_modal_changes()
            else:
                st.error("❌ Please fill in at least Name and Email fields.")
    
    with col2:
        if st.button("🚫 Cancel Edit", use_container_width=True, key="modal_cancel_edit_btn"):
            st.session_state.modal_edit_mode = False
            # Reload original data
            open_candidate_modal(st.session_state.selected_candidate)

def save_modal_changes():
    """Save changes made in modal edit mode"""
    try:
        # Clean up empty entries
        clean_qualifications = [q for q in st.session_state.modal_qualifications_list if q.get('qualification')]
        clean_skills = [s for s in st.session_state.modal_skills_list if s.get('skill')]
        clean_experience = []
        
        for exp in st.session_state.modal_experience_list:
            if exp.get('position') or exp.get('company'):
                clean_resp = [r for r in exp.get('responsibilities', []) if r.strip()]
                exp['responsibilities'] = clean_resp
                clean_experience.append(exp)
        
        clean_achievements = [a for a in st.session_state.modal_achievements_list if a.strip()]
        
        candidate_data = {
            'name': st.session_state.modal_name,
            'current_role': st.session_state.modal_current_role,
            'email': st.session_state.modal_email,
            'phone': st.session_state.modal_phone,
            'notice_period': st.session_state.modal_notice_period,
            'current_salary': st.session_state.modal_current_salary,
            'industry': st.session_state.modal_industry,
            'desired_salary': st.session_state.modal_desired_salary,
            'highest_qualification': st.session_state.modal_highest_qualification,
            'experience': clean_experience,
            'skills': clean_skills,
            'qualifications': clean_qualifications,
            'achievements': clean_achievements,
            'special_skills': st.session_state.modal_special_skills
        }
        
        # Update the candidate in database
        result, message = st.session_state.db_manager.update_candidate(candidate_data)
        
        if result:
            st.success("✅ Candidate updated successfully!")
            st.session_state.modal_edit_mode = False
            # Update the selected candidate data
            st.session_state.selected_candidate.update(candidate_data)
            st.rerun()
        else:
            st.error(f"❌ Failed to update candidate: {message}")
            
    except Exception as e:
        st.error(f"❌ Error updating candidate: {str(e)}")

def search_candidates_tab():
    st.markdown('<div class="section-header"><h2>🔍 Search Candidates</h2></div>', unsafe_allow_html=True)
    
    search_method = st.radio("Search Method", ["Manual Search", "Job Description Match"])
    
    if search_method == "Manual Search":
        manual_search()
    else:
        job_description_search()

def manual_search():
    st.markdown('<div class="form-container">', unsafe_allow_html=True)
    st.subheader("🔍 Manual Search")
    
    with st.form("search_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name_search = st.text_input("Name (contains)")
            role_search = st.text_input("Current Role (contains)")
            industry_search = st.text_input("Industry (contains)")
            skills_search = st.text_input("Skills (contains)")
            
        with col2:
            qualification_search = st.text_input("Qualifications (contains)")
            experience_years = st.number_input("Minimum Experience Years", min_value=0, value=0)
            notice_period_search = st.text_input("Notice Period (contains)")
            
        search_submitted = st.form_submit_button("🔍 Search", type="primary")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Move the results display outside the form
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
        
        results = st.session_state.db_manager.search_candidates(search_criteria)
        display_search_results(results)

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
                            display_search_results(ranked_results, show_match_score=True)
                    else:
                        st.markdown('<div class="error-message">❌ Failed to extract requirements from job description.</div>', unsafe_allow_html=True)
                        
                except Exception as e:
                    st.markdown(f'<div class="error-message">❌ Error processing job description: {str(e)}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="error-message">❌ Please provide a job description.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def rank_candidates_by_job_match(candidates, requirements):
    """Rank candidates based on job requirements match"""
    ranked_candidates = []
    
    for candidate in candidates:
        score = calculate_match_score(candidate, requirements)
        candidate['match_score'] = score
        ranked_candidates.append(candidate)
    
    # Sort by match score (highest first)
    return sorted(ranked_candidates, key=lambda x: x.get('match_score', 0), reverse=True)

def calculate_match_score(candidate, requirements):
    """Calculate match score between candidate and job requirements"""
    score = 0
    max_score = 0
    
    try:
        # Skills matching
        if requirements.get('required_skills'):
            max_score += 40
            candidate_skills = [skill.get('skill', '') for skill in candidate.get('skills', [])]
            required_skills = requirements.get('required_skills', [])
            
            matched_skills = 0
            for req_skill in required_skills:
                for cand_skill in candidate_skills:
                    if req_skill.lower() in cand_skill.lower():
                        matched_skills += 1
                        break
            
            if required_skills:
                score += (matched_skills / len(required_skills)) * 40
        
        # Experience matching
        if requirements.get('min_experience_years'):
            max_score += 30
            candidate_exp_years = len(candidate.get('experience', []))
            required_years = requirements.get('min_experience_years', 0)
            
            if candidate_exp_years >= required_years:
                score += 30
            else:
                score += (candidate_exp_years / required_years) * 30
        
        # Qualification matching
        if requirements.get('required_qualifications'):
            max_score += 20
            candidate_quals = [qual.get('qualification', '') for qual in candidate.get('qualifications', [])]
            required_quals = requirements.get('required_qualifications', [])
            
            matched_quals = 0
            for req_qual in required_quals:
                for cand_qual in candidate_quals:
                    if req_qual.lower() in cand_qual.lower():
                        matched_quals += 1
                        break
            
            if required_quals:
                score += (matched_quals / len(required_quals)) * 20
        
        # Industry matching
        if requirements.get('industry'):
            max_score += 10
            if candidate.get('industry', '').lower() == requirements.get('industry', '').lower():
                score += 10
        
        # Calculate percentage
        if max_score > 0:
            return round((score / max_score) * 100, 1)
        else:
            return 0
            
    except Exception as e:
        st.error(f"Error calculating match score: {str(e)}")
        return 0

def display_search_results(results, show_match_score=False):
    if results:
        st.markdown('<div class="section-header">', unsafe_allow_html=True)
        st.subheader(f"📊 Search Results ({len(results)} candidates found)")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Store results in session state for modal access
        st.session_state.search_results = results
        
        st.markdown("💡 **Click the 'View Details' button to see full candidate information**")
        st.markdown("---")
        
        # Display candidates in a simple, clean format
        for idx, candidate in enumerate(results):
            with st.container():
                # Create a professional card for each candidate
                st.markdown(f"""
                <div style="background: white; padding: 1.5rem; border-radius: 8px; 
                           border: 1px solid #e2e8f0; margin: 1rem 0; 
                           box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);">
                """, unsafe_allow_html=True)
                
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
                    if show_match_score:
                        score = candidate.get('match_score', 0)
                        if score >= 80:
                            st.markdown(f"**Match:** 🟢 {score}%")
                        elif score >= 60:
                            st.markdown(f"**Match:** 🟡 {score}%")
                        else:
                            st.markdown(f"**Match:** 🔴 {score}%")
                
                with col5:
                    # Use a unique key for each button
                    button_key = f"view_candidate_{idx}_{candidate.get('email', '')}"
                    if st.button("👁️ View Details", key=button_key, help="Click to view full candidate details", type="primary"):
                        # Debug: Show button was clicked
                        st.success(f"✅ Opening details for {candidate.get('name', 'Unknown')}")
                        # Open the modal
                        open_candidate_modal(candidate)
                
                st.markdown("</div>", unsafe_allow_html=True)
        
        # Debug info
        st.markdown("---")
        st.markdown("**Debug Info:**")
        st.write(f"Show modal state: {st.session_state.get('show_modal', False)}")
        st.write(f"Selected candidate: {st.session_state.get('selected_candidate', {}).get('name', 'None') if st.session_state.get('selected_candidate') else 'None'}")
        
    else:
        st.markdown('<div class="warning-message">🔍 No candidates found matching your criteria.</div>', unsafe_allow_html=True)

def dashboard_tab():
    st.markdown('<div class="section-header"><h2>📊 Dashboard</h2></div>', unsafe_allow_html=True)
    
    # Get statistics
    stats = st.session_state.db_manager.get_dashboard_stats()
    
    # Professional metrics display
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric("Total Candidates", stats.get('total_candidates', 0))
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric("Industries", stats.get('unique_industries', 0))
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric("Avg Experience", f"{stats.get('avg_experience', 0):.1f} years")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        backup_status = "✅ Active" if st.session_state.db_manager.last_backup_time else "❌ Never"
        st.metric("Backup Status", backup_status)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
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