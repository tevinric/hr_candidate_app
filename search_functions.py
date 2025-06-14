
import streamlit as st
from session_management import clear_search_state

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

def display_search_results(results, show_match_score=None):
    """Display search results with View Details buttons"""
    from navigation import view_candidate_details
    
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