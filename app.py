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
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'extracted_data' not in st.session_state:
    st.session_state.extracted_data = None
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

def main():
    # Professional header
    st.markdown("""
    <div class="main-header">
        <h1>🎯 HR Candidate Management Tool</h1>
        <p>AI-Powered CV Processing and Intelligent Candidate Matching</p>
    </div>
    """, unsafe_allow_html=True)
    
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
    
    if uploaded_file is not None:
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
                    
                    # Process with OpenAI
                    with st.spinner("🤖 Analyzing CV with AI..."):
                        candidate_data = st.session_state.cv_processor.process_cv_with_openai(extracted_text)
                        
                        if candidate_data:
                            st.session_state.extracted_data = candidate_data
                            st.markdown('<div class="success-message">✅ CV processed successfully with AI!</div>', unsafe_allow_html=True)
                            show_candidate_form(candidate_data)
                        else:
                            st.markdown('<div class="error-message">❌ Failed to process CV with AI. Please try again.</div>', unsafe_allow_html=True)
                
                # Clean up temp file
                os.unlink(tmp_file_path)
                
            except Exception as e:
                st.markdown(f'<div class="error-message">❌ Error processing CV: {str(e)}</div>', unsafe_allow_html=True)

def show_candidate_form(data):
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
        name = st.text_input("Full Name *", value=data.get('name', ''), key="name_input")
        email = st.text_input("Email Address *", value=data.get('email', ''), key="email_input")
        phone = st.text_input("Phone Number", value=data.get('phone', ''), key="phone_input")
        
    with col2:
        current_role = st.text_input("Current Role", value=data.get('current_role', ''), key="role_input")
        industry = st.text_input("Industry", value=data.get('industry', ''), key="industry_input")
        notice_period = st.text_input("Notice Period", value=data.get('notice_period', ''), key="notice_input")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Salary Information
    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    st.markdown("### 💰 Salary Information")
    col3, col4 = st.columns(2)
    with col3:
        current_salary = st.text_input("Current Salary", value=data.get('current_salary', ''), key="current_sal")
    with col4:
        desired_salary = st.text_input("Desired Salary", value=data.get('desired_salary', ''), key="desired_sal")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Education
    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    st.markdown("### 🎓 Education")
    highest_qualification = st.text_input("Highest Qualification", value=data.get('highest_qualification', ''), key="highest_qual")
    
    # Handle Qualifications with dynamic UI
    st.markdown("**Detailed Qualifications:**")
    qualifications_data = data.get('qualifications', [])
    
    # Initialize session state for qualifications if not exists
    if 'qualifications_list' not in st.session_state:
        st.session_state.qualifications_list = qualifications_data.copy() if qualifications_data else []
    
    # Display existing qualifications
    for i, qual in enumerate(st.session_state.qualifications_list):
        with st.container():
            col_qual1, col_qual2, col_qual3, col_qual4 = st.columns([3, 3, 2, 1])
            with col_qual1:
                st.session_state.qualifications_list[i]['qualification'] = st.text_input(
                    f"Qualification {i+1}", 
                    value=qual.get('qualification', ''),
                    key=f"qual_{i}"
                )
            with col_qual2:
                st.session_state.qualifications_list[i]['institution'] = st.text_input(
                    f"Institution {i+1}", 
                    value=qual.get('institution', ''),
                    key=f"inst_{i}"
                )
            with col_qual3:
                st.session_state.qualifications_list[i]['year'] = st.text_input(
                    f"Year {i+1}", 
                    value=qual.get('year', ''),
                    key=f"year_{i}"
                )
            with col_qual4:
                if st.button("🗑️", key=f"del_qual_{i}", help="Delete qualification"):
                    st.session_state.qualifications_list.pop(i)
                    st.rerun()
    
    if st.button("➕ Add Qualification"):
        st.session_state.qualifications_list.append({'qualification': '', 'institution': '', 'year': '', 'grade': ''})
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Skills Section
    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    st.markdown("### 🛠️ Skills")
    skills_data = data.get('skills', [])
    
    # Initialize session state for skills
    if 'skills_list' not in st.session_state:
        st.session_state.skills_list = skills_data.copy() if skills_data else []
    
    # Display skills in a more user-friendly way
    for i, skill in enumerate(st.session_state.skills_list):
        with st.container():
            col_skill1, col_skill2, col_skill3 = st.columns([4, 2, 1])
            with col_skill1:
                st.session_state.skills_list[i]['skill'] = st.text_input(
                    f"Skill {i+1}", 
                    value=skill.get('skill', ''),
                    key=f"skill_{i}"
                )
            with col_skill2:
                st.session_state.skills_list[i]['proficiency'] = st.selectbox(
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
    
    if st.button("➕ Add Skill"):
        st.session_state.skills_list.append({'skill': '', 'proficiency': 3})
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Experience Section
    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    st.markdown("### 💼 Work Experience")
    experience_data = data.get('experience', [])
    
    # Initialize session state for experience
    if 'experience_list' not in st.session_state:
        st.session_state.experience_list = experience_data.copy() if experience_data else []
    
    # Display experience in expandable sections
    for i, exp in enumerate(st.session_state.experience_list):
        with st.expander(f"Position {i+1}: {exp.get('position', 'New Position')}"):
            col_exp1, col_exp2 = st.columns(2)
            with col_exp1:
                st.session_state.experience_list[i]['position'] = st.text_input(
                    "Job Title", 
                    value=exp.get('position', ''),
                    key=f"pos_{i}"
                )
                st.session_state.experience_list[i]['company'] = st.text_input(
                    "Company", 
                    value=exp.get('company', ''),
                    key=f"comp_{i}"
                )
            with col_exp2:
                st.session_state.experience_list[i]['years'] = st.text_input(
                    "Duration", 
                    value=exp.get('years', ''),
                    key=f"duration_{i}"
                )
            
            # Responsibilities
            st.markdown("**Key Responsibilities:**")
            responsibilities = exp.get('responsibilities', [])
            
            # Initialize responsibilities in session state
            if f'resp_list_{i}' not in st.session_state:
                st.session_state[f'resp_list_{i}'] = responsibilities.copy() if responsibilities else ['']
            
            for j, resp in enumerate(st.session_state[f'resp_list_{i}']):
                col_resp1, col_resp2 = st.columns([5, 1])
                with col_resp1:
                    st.session_state[f'resp_list_{i}'][j] = st.text_input(
                        f"Responsibility {j+1}", 
                        value=resp,
                        key=f"resp_{i}_{j}"
                    )
                with col_resp2:
                    if st.button("🗑️", key=f"del_resp_{i}_{j}", help="Delete responsibility"):
                        st.session_state[f'resp_list_{i}'].pop(j)
                        st.rerun()
            
            col_add_resp, col_del_exp = st.columns(2)
            with col_add_resp:
                if st.button(f"➕ Add Responsibility", key=f"add_resp_{i}"):
                    st.session_state[f'resp_list_{i}'].append('')
                    st.rerun()
            
            with col_del_exp:
                if st.button(f"🗑️ Delete Position", key=f"del_exp_{i}"):
                    st.session_state.experience_list.pop(i)
                    # Clean up responsibilities session state
                    if f'resp_list_{i}' in st.session_state:
                        del st.session_state[f'resp_list_{i}']
                    st.rerun()
            
            # Update the experience with responsibilities
            st.session_state.experience_list[i]['responsibilities'] = st.session_state[f'resp_list_{i}']
    
    if st.button("➕ Add Work Experience"):
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
    achievements_data = data.get('achievements', [])
    
    # Initialize session state for achievements
    if 'achievements_list' not in st.session_state:
        st.session_state.achievements_list = achievements_data.copy() if achievements_data else []
    
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
    
    if st.button("➕ Add Achievement"):
        st.session_state.achievements_list.append('')
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Special Skills
    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    st.markdown("### ⭐ Special Skills & Certifications")
    special_skills = st.text_area("Special Skills", value=data.get('special_skills', ''), height=100, key="special_skills_input")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Form submission with enhanced styling
    st.markdown("---")
    st.markdown('<div class="professional-spacing">', unsafe_allow_html=True)
    col_submit1, col_submit2 = st.columns([3, 1])
    with col_submit1:
        st.markdown("*Fields marked with * are required")
    with col_submit2:
        if st.button("💾 Save to Database", type="primary", use_container_width=True):
            if name and email:  # Basic validation
                handle_candidate_save(name, current_role, email, phone, notice_period, current_salary, 
                                    industry, desired_salary, highest_qualification, special_skills)
            else:
                st.markdown('<div class="error-message">❌ Please fill in at least Name and Email fields.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def handle_candidate_save(name, current_role, email, phone, notice_period, current_salary, 
                         industry, desired_salary, highest_qualification, special_skills):
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
            'name': name,
            'current_role': current_role,
            'email': email,
            'phone': phone,
            'notice_period': notice_period,
            'current_salary': current_salary,
            'industry': industry,
            'desired_salary': desired_salary,
            'highest_qualification': highest_qualification,
            'experience': clean_experience,
            'skills': clean_skills,
            'qualifications': clean_qualifications,
            'achievements': clean_achievements,
            'special_skills': special_skills
        }
        
        # Check if candidate already exists
        existing_candidate = st.session_state.db_manager.get_candidate_by_email(email)
        
        if existing_candidate:
            # Store the candidate data for potential overwrite
            st.session_state.pending_candidate_data = candidate_data
            st.session_state.existing_candidate_email = email
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
        if st.button("✅ Overwrite Record", type="primary", use_container_width=True):
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
        if st.button("❌ Cancel", use_container_width=True):
            clear_overwrite_dialog_state()
            st.markdown('<div class="warning-message">ℹ️ The candidate already exists. Please modify the email address or update the existing record.</div>', unsafe_allow_html=True)
            st.rerun()
    
    with col3:
        st.markdown("*Choose 'Overwrite' to update the existing record with new data, or 'Cancel' to return to the form.*")

def clear_form_session_state():
    """Clear form-related session state"""
    keys_to_clear = [
        'qualifications_list', 'skills_list', 'experience_list', 'achievements_list',
        'extracted_data'
    ]
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    # Clear responsibility lists
    for key in list(st.session_state.keys()):
        if key.startswith('resp_list_'):
            del st.session_state[key]

def clear_overwrite_dialog_state():
    """Clear overwrite dialog state"""
    st.session_state.show_overwrite_dialog = False
    st.session_state.pending_candidate_data = None
    st.session_state.existing_candidate_email = None

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
        
        # Prepare data for display
        display_data = []
        for candidate in results:
            row = {
                'Name': candidate.get('name', 'N/A'),
                'Current Role': candidate.get('current_role', 'N/A'),
                'Industry': candidate.get('industry', 'N/A'),
                'Email': candidate.get('email', 'N/A'),
                'Phone': candidate.get('phone', 'N/A'),
                'Notice Period': candidate.get('notice_period', 'N/A'),
                'Highest Qualification': candidate.get('highest_qualification', 'N/A')
            }
            
            if show_match_score:
                row['Match Score %'] = candidate.get('match_score', 0)
            
            display_data.append(row)
        
        # Display as dataframe with professional styling
        df = pd.DataFrame(display_data)
        st.dataframe(df, use_container_width=True)
        
        # Use checkbox instead of button for detailed view
        show_details = st.checkbox("📄 Show Detailed Results")
        
        if show_details:
            for i, candidate in enumerate(results):
                with st.expander(f"👤 {candidate.get('name', 'Unknown')} - Detailed View"):
                    st.markdown('<div class="professional-card">', unsafe_allow_html=True)
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Email:** {candidate.get('email', 'N/A')}")
                        st.write(f"**Phone:** {candidate.get('phone', 'N/A')}")
                        st.write(f"**Current Role:** {candidate.get('current_role', 'N/A')}")
                        st.write(f"**Industry:** {candidate.get('industry', 'N/A')}")
                        st.write(f"**Notice Period:** {candidate.get('notice_period', 'N/A')}")
                        
                    with col2:
                        st.write(f"**Current Salary:** {candidate.get('current_salary', 'N/A')}")
                        st.write(f"**Desired Salary:** {candidate.get('desired_salary', 'N/A')}")
                        st.write(f"**Highest Qualification:** {candidate.get('highest_qualification', 'N/A')}")
                        if show_match_score:
                            st.write(f"**Match Score:** {candidate.get('match_score', 0)}%")
                    
                    # Skills
                    if candidate.get('skills'):
                        st.write("**Skills:**")
                        skills_df = pd.DataFrame(candidate['skills'])
                        st.dataframe(skills_df, use_container_width=True)
                    
                    # Experience
                    if candidate.get('experience'):
                        st.write("**Experience:**")
                        exp_df = pd.DataFrame(candidate['experience'])
                        st.dataframe(exp_df, use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
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
