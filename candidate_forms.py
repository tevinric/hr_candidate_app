import streamlit as st
import tempfile
import os
from session_management import clear_form_session_state, clear_overwrite_dialog_state

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
                        height=68,
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
                        height=68,
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

def handle_candidate_save():
    """Handle the candidate save process with overwrite logic and FORCED cloud sync"""
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
            # New candidate, proceed with insert (includes FORCED cloud sync)
            try:
                db_result = st.session_state.db_manager.insert_candidate(candidate_data)
                
                # Handle both tuple and boolean returns for backward compatibility
                if isinstance(db_result, tuple):
                    result, message = db_result
                else:
                    result = db_result
                    message = "Operation completed" if result else "Operation failed"
                
                if result:
                    st.markdown('<div class="success-message">✅ Candidate saved successfully and synced to cloud!</div>', unsafe_allow_html=True)
                    
                    # CRITICAL: Additional sync confirmation
                    import logging
                    logging.info("✅ Candidate save completed with forced cloud sync")
                    
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
            # Update the existing candidate (includes FORCED cloud sync)
            try:
                result, message = st.session_state.db_manager.update_candidate(st.session_state.pending_candidate_data)
                
                if result:
                    st.markdown('<div class="success-message">✅ Candidate record updated successfully and synced to cloud!</div>', unsafe_allow_html=True)
                    
                    # CRITICAL: Additional sync confirmation
                    import logging
                    logging.info("✅ Candidate overwrite completed with forced cloud sync")
                    
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