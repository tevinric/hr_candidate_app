import streamlit as st
from candidate_forms import show_enhanced_experience_section

def main_application_page():
    """Main application page with navigation"""
    from candidate_forms import upload_cv_tab
    from search_functions import search_candidates_tab
    from dashboard_functions import dashboard_tab
    
    # Sidebar navigation
    st.sidebar.markdown("""
    <div style="text-align: center; padding: 1rem;">
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
    
    # Update button
    st.markdown("---")
    col_submit1, col_submit2, col_submit3 = st.columns([2, 1, 2])
    with col_submit1:
        st.markdown("*Fields marked with * are required")
    with col_submit2:
        if st.button("💾 Update Candidate", type="primary", use_container_width=True, key="update_candidate_btn"):
            if st.session_state.edit_name and st.session_state.edit_email:
                handle_candidate_update()
            else:
                st.error("❌ Please fill in at least Name and Email fields.")

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