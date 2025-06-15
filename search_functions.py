import streamlit as st
import logging
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
    st.subheader("🔍 Enhanced Manual Search")
    
    # Add help text
    st.info("""
    **Enhanced Search Features:**
    - **Smart Role Matching**: "Data Scientist" will find "Data Science Manager", "Senior Data Scientist", etc.
    - **Flexible Skills Search**: Enter multiple skills separated by commas - finds candidates with ANY of the specified skills
    - **Fuzzy Matching**: Finds similar terms and variations automatically
    """)
    
    # Pre-populate with cached criteria if available
    cached = st.session_state.cached_search_criteria
    
    with st.form("search_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name_search = st.text_input(
                "Name (contains)", 
                value=cached.get('name', ''),
                help="Search for candidates by name (partial matches supported)"
            )
            role_search = st.text_input(
                "Current Role (smart matching)", 
                value=cached.get('current_role', ''),
                help="e.g., 'Data Scientist' will also find 'Data Science Manager', 'Senior Data Scientist'"
            )
            industry_search = st.text_input(
                "Industry (contains)", 
                value=cached.get('industry', ''),
                help="e.g., 'Tech' will find 'Technology', 'IT', 'Software'"
            )
            skills_search = st.text_area(
                "Skills (comma-separated for ANY match)", 
                value=cached.get('skills', ''),
                height=80,
                help="Enter multiple skills separated by commas. Finds candidates with ANY of these skills.\nExample: 'Python, JavaScript, React' will find candidates with Python OR JavaScript OR React"
            )
            
        with col2:
            qualification_search = st.text_input(
                "Qualifications (contains)", 
                value=cached.get('qualifications', ''),
                help="Search in education background and qualifications"
            )
            experience_years = st.number_input(
                "Minimum Experience Years", 
                min_value=0, 
                value=cached.get('experience_years', 0),
                help="Minimum number of positions/years of experience"
            )
            notice_period_search = st.text_input(
                "Notice Period (contains)", 
                value=cached.get('notice_period', ''),
                help="Search by notice period requirements"
            )
            
            # Advanced filters
            st.markdown("**Advanced Filters:**")
            min_skill_proficiency = st.selectbox(
                "Minimum Skill Proficiency Level",
                options=[0, 1, 2, 3, 4, 5],
                index=0,
                format_func=lambda x: "Any" if x == 0 else f"{x} - {'Beginner' if x==1 else 'Basic' if x==2 else 'Intermediate' if x==3 else 'Advanced' if x==4 else 'Expert'}",
                help="Filter candidates by minimum skill proficiency level"
            )
            
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
            'notice_period': notice_period_search,
            'min_skill_proficiency': min_skill_proficiency
        }
        
        # Cache search criteria
        st.session_state.cached_search_criteria = search_criteria
        
        # Show search info
        with st.spinner("🔍 Searching candidates with enhanced matching..."):
            # Perform enhanced search
            results = st.session_state.db_manager.search_candidates(search_criteria)
            
            # Add relevance scores to results
            for candidate in results:
                relevance_score = calculate_enhanced_manual_search_relevance(candidate, search_criteria)
                candidate['relevance_score'] = relevance_score
            
            # Sort by relevance score (highest first)
            results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
            
            # Cache results
            st.session_state.cached_search_results = results
            st.session_state.search_performed = True
            
            # Show search summary
            if results:
                st.success(f"✅ Found {len(results)} matching candidates with enhanced search!")
                if skills_search:
                    skills_list = [s.strip() for s in skills_search.split(',') if s.strip()]
                    if len(skills_list) > 1:
                        st.info(f"📋 Searched for candidates with ANY of these skills: {', '.join(skills_list)}")
            else:
                st.warning("⚠️ No candidates found. Try broader search terms or check spelling.")
                # Provide search suggestions
                show_search_suggestions(search_criteria)
            
            st.rerun()

def show_search_suggestions(search_criteria):
    """Show search suggestions when no results found"""
    st.markdown("### 💡 Search Suggestions:")
    suggestions = []
    
    if search_criteria.get('current_role'):
        suggestions.append("• Try using broader role terms (e.g., 'Developer' instead of 'Senior Full Stack Developer')")
    
    if search_criteria.get('skills'):
        suggestions.append("• Try individual skill names instead of multiple skills")
        suggestions.append("• Check spelling of skill names")
    
    if search_criteria.get('experience_years', 0) > 5:
        suggestions.append("• Try reducing the minimum experience years requirement")
    
    if search_criteria.get('industry'):
        suggestions.append("• Try broader industry terms (e.g., 'Tech' instead of 'Financial Technology')")
    
    if not suggestions:
        suggestions.append("• Try using fewer search criteria")
        suggestions.append("• Use broader search terms")
    
    for suggestion in suggestions:
        st.markdown(suggestion)

def job_description_search():
    st.markdown('<div class="form-container">', unsafe_allow_html=True)
    st.subheader("📋 AI-Powered Job Description Match")
    
    st.info("""
    **Enhanced Job Matching:**
    - Paste any job description and our AI will extract requirements automatically
    - Finds candidates with similar skills and experience, not just exact matches
    - Scores candidates based on overall fit, including skill variations and related experience
    """)
    
    job_description = st.text_area(
        "Paste Job Description", 
        height=250, 
        placeholder="""Paste the complete job description here...

Example: We are looking for a Senior Data Scientist with experience in Python, machine learning, and SQL. The ideal candidate should have 3+ years of experience in data analysis and be familiar with cloud platforms like AWS or Azure...""",
        help="Paste the full job description - the more detail, the better the matching"
    )
    
    # Advanced job matching options
    with st.expander("🔧 Advanced Matching Options"):
        col1, col2 = st.columns(2)
        
        with col1:
            strict_skills_matching = st.checkbox(
                "Strict Skills Matching", 
                value=False,
                help="If enabled, candidates must have most of the required skills"
            )
            
            min_match_threshold = st.slider(
                "Minimum Match Threshold (%)",
                min_value=0,
                max_value=100,
                value=20,
                help="Minimum percentage match to include candidates in results"
            )
        
        with col2:
            include_related_skills = st.checkbox(
                "Include Related Skills", 
                value=True,
                help="Include candidates with related/similar skills (recommended)"
            )
            
            prioritize_recent_experience = st.checkbox(
                "Prioritize Recent Experience",
                value=True,
                help="Give higher scores to candidates with recent relevant experience"
            )
    
    if st.button("🎯 Find Matching Candidates", type="primary"):
        if job_description and len(job_description.strip()) > 50:
            with st.spinner("🤖 Analyzing job description with AI..."):
                try:
                    # Extract requirements from job description using enhanced OpenAI
                    requirements = st.session_state.cv_processor.extract_job_requirements(job_description)
                    
                    if requirements:
                        # Display extracted requirements
                        st.subheader("🎯 Extracted Job Requirements:")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if requirements.get('required_skills'):
                                st.markdown("**Required Skills:**")
                                for skill in requirements.get('required_skills', [])[:10]:  # Show top 10
                                    st.markdown(f"• {skill}")
                            
                            if requirements.get('min_experience_years'):
                                st.markdown(f"**Minimum Experience:** {requirements.get('min_experience_years')} years")
                            
                            if requirements.get('seniority_level'):
                                st.markdown(f"**Seniority Level:** {requirements.get('seniority_level')}")
                        
                        with col2:
                            if requirements.get('required_qualifications'):
                                st.markdown("**Required Qualifications:**")
                                for qual in requirements.get('required_qualifications', []):
                                    st.markdown(f"• {qual}")
                            
                            if requirements.get('industry'):
                                st.markdown(f"**Industry:** {requirements.get('industry')}")
                            
                            if requirements.get('technologies'):
                                st.markdown("**Technologies:**")
                                for tech in requirements.get('technologies', [])[:8]:  # Show top 8
                                    st.markdown(f"• {tech}")
                        
                        # Apply advanced options to requirements
                        requirements['strict_skills_matching'] = strict_skills_matching
                        requirements['min_match_threshold'] = min_match_threshold
                        requirements['include_related_skills'] = include_related_skills
                        requirements['prioritize_recent_experience'] = prioritize_recent_experience
                        
                        # Search for matching candidates
                        with st.spinner("🔍 Searching and ranking candidates..."):
                            results = st.session_state.db_manager.search_candidates_by_job_requirements(requirements)
                            ranked_results = rank_candidates_by_enhanced_job_match(results, requirements)
                            
                            # Apply minimum threshold filter
                            filtered_results = [
                                candidate for candidate in ranked_results 
                                if candidate.get('match_score', 0) >= min_match_threshold
                            ]
                            
                            # Cache results
                            st.session_state.cached_search_results = filtered_results
                            st.session_state.search_performed = True
                            st.session_state.cached_search_criteria = {
                                'job_description': job_description,
                                'requirements': requirements
                            }
                            
                            # Show matching summary
                            if filtered_results:
                                st.success(f"✅ Found {len(filtered_results)} candidates matching the job requirements!")
                                
                                # Show match distribution
                                high_match = len([c for c in filtered_results if c.get('match_score', 0) >= 80])
                                medium_match = len([c for c in filtered_results if 60 <= c.get('match_score', 0) < 80])
                                low_match = len([c for c in filtered_results if c.get('match_score', 0) < 60])
                                
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("🟢 High Match (80%+)", high_match)
                                with col2:
                                    st.metric("🟡 Medium Match (60-79%)", medium_match)
                                with col3:
                                    st.metric("🔴 Lower Match (<60%)", low_match)
                                
                            else:
                                st.warning(f"⚠️ No candidates found meeting the {min_match_threshold}% threshold.")
                                st.info("💡 Try lowering the minimum match threshold or using broader job requirements.")
                            
                            st.rerun()
                    else:
                        st.markdown('<div class="error-message">❌ Failed to extract requirements from job description. Please check the content and try again.</div>', unsafe_allow_html=True)
                        
                except Exception as e:
                    logging.error(f"Error in job description search: {str(e)}")
                    st.markdown(f'<div class="error-message">❌ Error processing job description: {str(e)}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="error-message">❌ Please provide a detailed job description (at least 50 characters).</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def calculate_enhanced_manual_search_relevance(candidate, search_criteria):
    """Enhanced relevance calculation for manual search with better matching"""
    score = 0
    total_criteria = 0
    
    try:
        # Name matching with fuzzy logic
        if search_criteria.get('name'):
            total_criteria += 1
            candidate_name = candidate.get('name', '').lower()
            search_name = search_criteria['name'].lower()
            
            # Word-level matching
            search_words = search_name.split()
            name_match = any(word in candidate_name for word in search_words if len(word) > 2)
            if name_match:
                score += 1
        
        # Enhanced role matching
        if search_criteria.get('current_role'):
            total_criteria += 1
            role_query = search_criteria['current_role'].lower()
            candidate_role = candidate.get('current_role', '').lower()
            
            # Check current role and experience roles
            role_match = False
            
            # Check current role with variations
            if (role_query in candidate_role or candidate_role in role_query or
                any(word in candidate_role for word in role_query.split() if len(word) > 3)):
                role_match = True
            
            # Check experience positions
            if not role_match:
                for exp in candidate.get('experience', []):
                    exp_position = exp.get('position', '').lower()
                    if (role_query in exp_position or exp_position in role_query or
                        any(word in exp_position for word in role_query.split() if len(word) > 3)):
                        role_match = True
                        break
            
            if role_match:
                score += 1
        
        # Industry matching with variations
        if search_criteria.get('industry'):
            total_criteria += 1
            industry_query = search_criteria['industry'].lower()
            candidate_industry = candidate.get('industry', '').lower()
            
            if (industry_query in candidate_industry or candidate_industry in industry_query or
                any(word in candidate_industry for word in industry_query.split() if len(word) > 3)):
                score += 1
        
        # Enhanced skills matching - ANY of the specified skills
        if search_criteria.get('skills'):
            total_criteria += 1
            skills_input = search_criteria['skills']
            
            # Parse multiple skills
            query_skills = [s.strip().lower() for s in skills_input.split(',') if s.strip()]
            
            if query_skills:
                # Get all candidate skills
                candidate_skill_names = [skill.get('skill', '').lower() for skill in candidate.get('skills', [])]
                
                # Get skills from experience technologies
                experience_technologies = []
                for exp in candidate.get('experience', []):
                    experience_technologies.extend([tech.lower() for tech in exp.get('technologies', [])])
                
                # Get skills from special skills
                special_skills = candidate.get('special_skills', '').lower()
                special_skills_list = [s.strip() for s in special_skills.replace(',', ' ').split() if len(s.strip()) > 2]
                
                all_candidate_skills = candidate_skill_names + experience_technologies + special_skills_list
                
                # Check for ANY skill match
                skills_match = False
                matched_skills_count = 0
                
                for query_skill in query_skills:
                    for candidate_skill in all_candidate_skills:
                        if (query_skill in candidate_skill or candidate_skill in query_skill or
                            any(word in candidate_skill for word in query_skill.split() if len(word) > 2)):
                            skills_match = True
                            matched_skills_count += 1
                            break
                    if skills_match:
                        break
                
                if skills_match:
                    # Bonus for matching multiple skills
                    skill_bonus = min(1.0, matched_skills_count / len(query_skills))
                    score += skill_bonus
        
        # Qualifications matching
        if search_criteria.get('qualifications'):
            total_criteria += 1
            quals_query = search_criteria['qualifications'].lower()
            candidate_quals = candidate.get('qualifications', [])
            candidate_highest = candidate.get('highest_qualification', '').lower()
            
            # Check qualifications
            quals_text = candidate_highest + ' ' + ' '.join([qual.get('qualification', '').lower() for qual in candidate_quals])
            
            if (quals_query in quals_text or
                any(word in quals_text for word in quals_query.split() if len(word) > 3)):
                score += 1
        
        # Notice period matching
        if search_criteria.get('notice_period'):
            total_criteria += 1
            notice_query = search_criteria['notice_period'].lower()
            candidate_notice = candidate.get('notice_period', '').lower()
            
            if notice_query in candidate_notice:
                score += 1
        
        # Experience years matching
        if search_criteria.get('experience_years', 0) > 0:
            total_criteria += 1
            required_years = search_criteria['experience_years']
            candidate_exp_years = len(candidate.get('experience', []))
            
            if candidate_exp_years >= required_years:
                score += 1
            elif candidate_exp_years >= required_years - 1:  # Allow 1 year flexibility
                score += 0.7
        
        # Skill proficiency filter
        if search_criteria.get('min_skill_proficiency', 0) > 0:
            total_criteria += 1
            min_proficiency = search_criteria['min_skill_proficiency']
            candidate_skills = candidate.get('skills', [])
            
            has_high_proficiency = any(
                skill.get('proficiency', 0) >= min_proficiency 
                for skill in candidate_skills
            )
            
            if has_high_proficiency:
                score += 1
        
        # Calculate percentage
        if total_criteria > 0:
            relevance = (score / total_criteria) * 100
            return round(relevance, 1)
        else:
            return 100  # If no criteria specified, consider it a 100% match
            
    except Exception as e:
        logging.error(f"Error calculating manual search relevance: {str(e)}")
        return 0

def rank_candidates_by_enhanced_job_match(candidates, requirements):
    """Enhanced ranking of candidates based on job requirements"""
    ranked_candidates = []
    
    for candidate in candidates:
        score = calculate_enhanced_match_score(candidate, requirements)
        candidate['match_score'] = score
        candidate['relevance_score'] = score  # Also set as relevance_score for consistency
        ranked_candidates.append(candidate)
    
    # Sort by match score (highest first)
    return sorted(ranked_candidates, key=lambda x: x.get('match_score', 0), reverse=True)

def calculate_enhanced_match_score(candidate, requirements):
    """Enhanced comprehensive match score calculation with better flexibility"""
    score = 0
    max_score = 0
    
    try:
        # 1. Required Skills Matching (30% weight)
        required_skills = requirements.get('required_skills', [])
        if required_skills:
            max_score += 30
            candidate_skills = [skill.get('skill', '').lower() for skill in candidate.get('skills', [])]
            
            # Also collect skills from experience technologies and special skills
            candidate_technologies = []
            for exp in candidate.get('experience', []):
                candidate_technologies.extend([tech.lower() for tech in exp.get('technologies', [])])
            
            special_skills = candidate.get('special_skills', '').lower()
            special_skills_list = [s.strip() for s in special_skills.replace(',', ' ').split() if len(s.strip()) > 2]
            
            all_candidate_skills = set(candidate_skills + candidate_technologies + special_skills_list)
            
            matched_skills = 0
            for req_skill in required_skills[:10]:  # Limit to top 10 to avoid over-weighting
                skill_lower = req_skill.lower()
                skill_found = False
                
                for candidate_skill in all_candidate_skills:
                    # Flexible matching: exact match, contains, or word overlap
                    if (skill_lower in candidate_skill or candidate_skill in skill_lower or
                        any(word in candidate_skill for word in skill_lower.split() if len(word) > 2) or
                        any(word in skill_lower for word in candidate_skill.split() if len(word) > 2)):
                        skill_found = True
                        break
                
                if skill_found:
                    matched_skills += 1
            
            # Calculate skills score with flexibility
            if required_skills:
                skills_score = (matched_skills / min(len(required_skills), 10)) * 30
                # Apply strict matching penalty if enabled
                if requirements.get('strict_skills_matching') and matched_skills < len(required_skills) * 0.7:
                    skills_score *= 0.6
                score += skills_score
        
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
                tech_found = any(
                    tech_lower in candidate_tech or candidate_tech in tech_lower or
                    any(word in candidate_tech for word in tech_lower.split() if len(word) > 2)
                    for candidate_tech in all_candidate_tech
                )
                if tech_found:
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
            elif candidate_exp_years >= max(1, min_experience - 1):  # 1 year flexibility
                # Partial score for being close to requirement
                flexibility_score = (candidate_exp_years / target_years) * 15
                score += min(12, flexibility_score)  # Cap at 12 out of 15
            else:
                # Reduced score for not meeting minimum
                if min_experience > 0:
                    score += (candidate_exp_years / min_experience) * 7.5
        
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
                # More flexible area matching
                area_found = (
                    area_lower in candidate_experience_text or
                    any(area_lower in role for role in candidate_roles) or
                    any(word in candidate_experience_text for word in area_lower.split() if len(word) > 3)
                )
                if area_found:
                    matched_areas += 1
            
            if required_experience_areas:
                score += (matched_areas / len(required_experience_areas)) * 15
        
        # 5. Qualification Matching (8% weight)
        required_qualifications = requirements.get('required_qualifications', [])
        if required_qualifications:
            max_score += 8
            candidate_quals = [qual.get('qualification', '').lower() for qual in candidate.get('qualifications', [])]
            candidate_highest = candidate.get('highest_qualification', '').lower()
            
            matched_quals = 0
            for req_qual in required_qualifications:
                qual_lower = req_qual.lower()
                qual_found = (
                    qual_lower in candidate_highest or
                    any(qual_lower in cand_qual or cand_qual in qual_lower for cand_qual in candidate_quals) or
                    any(word in candidate_highest for word in qual_lower.split() if len(word) > 3)
                )
                if qual_found:
                    matched_quals += 1
            
            if required_qualifications:
                score += (matched_quals / len(required_qualifications)) * 8
        
        # 6. Industry Matching (4% weight)
        required_industry = requirements.get('industry', '')
        if required_industry:
            max_score += 4
            candidate_industry = candidate.get('industry', '').lower()
            required_industry_lower = required_industry.lower()
            
            if candidate_industry:
                if candidate_industry == required_industry_lower:
                    score += 4
                elif (required_industry_lower in candidate_industry or 
                      candidate_industry in required_industry_lower):
                    score += 3
                else:
                    # Keyword overlap
                    industry_keywords = required_industry_lower.split()
                    matches = sum(1 for keyword in industry_keywords if keyword in candidate_industry)
                    if matches > 0:
                        score += (matches / len(industry_keywords)) * 2
        
        # 7. Seniority Level Matching (4% weight)
        required_seniority = requirements.get('seniority_level', '')
        if required_seniority:
            max_score += 4
            candidate_role = candidate.get('current_role', '').lower()
            required_seniority_lower = required_seniority.lower()
            candidate_exp_count = len(candidate.get('experience', []))
            
            # Check role title for seniority indicators
            if required_seniority_lower in candidate_role:
                score += 4
            elif 'senior' in required_seniority_lower and ('lead' in candidate_role or 'principal' in candidate_role):
                score += 3
            elif 'lead' in required_seniority_lower and 'senior' in candidate_role and candidate_exp_count >= 4:
                score += 3
            else:
                # Experience-based seniority matching
                if 'entry' in required_seniority_lower and candidate_exp_count <= 2:
                    score += 2
                elif 'junior' in required_seniority_lower and candidate_exp_count <= 3:
                    score += 2
                elif 'mid' in required_seniority_lower and 2 <= candidate_exp_count <= 5:
                    score += 2
                elif 'senior' in required_seniority_lower and candidate_exp_count >= 4:
                    score += 2
        
        # 8. Key Responsibilities Matching (4% weight)
        key_responsibilities = requirements.get('key_responsibilities', [])
        if key_responsibilities:
            max_score += 4
            candidate_responsibilities_text = ""
            
            for exp in candidate.get('experience', []):
                candidate_responsibilities_text += " " + " ".join(exp.get('responsibilities', []))
            
            candidate_responsibilities_text = candidate_responsibilities_text.lower()
            
            matched_responsibilities = 0
            for responsibility in key_responsibilities:
                resp_lower = responsibility.lower()
                # Look for keywords from the responsibility
                resp_keywords = [word for word in resp_lower.split() if len(word) > 3]
                keyword_matches = sum(1 for keyword in resp_keywords if keyword in candidate_responsibilities_text)
                
                if keyword_matches >= max(1, len(resp_keywords) // 3):  # At least 1/3 of keywords match
                    matched_responsibilities += 1
            
            if key_responsibilities:
                score += (matched_responsibilities / len(key_responsibilities)) * 4
        
        # Ensure max_score is reasonable
        if max_score == 0:
            max_score = 100
            # Basic scoring for cases with minimal requirements
            if candidate.get('skills'):
                score += 30
            if candidate.get('experience'):
                score += 40
            if candidate.get('qualifications'):
                score += 20
            if candidate.get('industry'):
                score += 10
        
        # Calculate percentage
        final_score = (score / max_score) * 100
        
        # Apply bonuses for preferred skills and recent experience
        preferred_skills = requirements.get('preferred_skills', [])
        if preferred_skills:
            candidate_skills = [skill.get('skill', '').lower() for skill in candidate.get('skills', [])]
            preferred_matches = sum(1 for pref_skill in preferred_skills 
                                 if any(pref_skill.lower() in cand_skill for cand_skill in candidate_skills))
            if preferred_matches > 0:
                final_score += min(5, (preferred_matches / len(preferred_skills)) * 5)
        
        # Recent experience bonus
        if requirements.get('prioritize_recent_experience') and candidate.get('experience'):
            # Simple bonus for having experience (could be enhanced with date parsing)
            if len(candidate.get('experience', [])) > 0:
                final_score += 2
        
        # Cap at 100%
        final_score = min(100, final_score)
        
        return round(final_score, 1)
            
    except Exception as e:
        logging.error(f"Error calculating enhanced match score: {str(e)}")
        return 0

def display_search_results(results, show_match_score=None):
    """Display search results with enhanced information and View Details buttons"""
    from navigation import view_candidate_details
    
    if results:
        # Determine if we should show match scores
        if show_match_score is None:
            show_match_score = any(candidate.get('match_score') is not None for candidate in results)
        
        st.markdown('<div class="section-header">', unsafe_allow_html=True)
        st.subheader(f"📊 Search Results ({len(results)} candidates found)")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Show result summary
        if show_match_score:
            high_match = len([c for c in results if c.get('match_score', 0) >= 80])
            medium_match = len([c for c in results if 60 <= c.get('match_score', 0) < 80])
            low_match = len([c for c in results if c.get('match_score', 0) < 60])
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("🟢 High Match (80%+)", high_match)
            with col2:
                st.metric("🟡 Medium Match (60-79%)", medium_match)
            with col3:
                st.metric("🔴 Lower Match (<60%)", low_match)
            with col4:
                avg_score = sum(c.get('match_score', 0) for c in results) / len(results)
                st.metric("📈 Average Match", f"{avg_score:.1f}%")
        
        st.markdown("💡 **Click 'View Details' to see and edit full candidate information**")
        st.markdown("---")
        
        # Display candidates with enhanced info
        for idx, candidate in enumerate(results):
            with st.container():
                st.markdown('<div class="candidate-card">', unsafe_allow_html=True)
                
                # Enhanced candidate summary
                col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 1])
                
                with col1:
                    st.markdown(f"**👤 {candidate.get('name', 'N/A')}**")
                    st.write(f"📧 {candidate.get('email', 'N/A')}")
                    
                    # Show top skills
                    candidate_skills = candidate.get('skills', [])
                    if candidate_skills:
                        top_skills = [skill.get('skill', '') for skill in candidate_skills[:3]]
                        if top_skills:
                            st.caption(f"🛠️ {', '.join(top_skills)}")
                
                with col2:
                    st.write(f"**Role:** {candidate.get('current_role', 'N/A')}")
                    st.write(f"**Industry:** {candidate.get('industry', 'N/A')}")
                    
                    # Show experience count
                    exp_count = len(candidate.get('experience', []))
                    st.caption(f"💼 {exp_count} position{'s' if exp_count != 1 else ''}")
                
                with col3:
                    st.write(f"**Phone:** {candidate.get('phone', 'N/A')}")
                    st.write(f"**Notice:** {candidate.get('notice_period', 'N/A')}")
                    
                    # Show recent company
                    recent_exp = candidate.get('experience', [])
                    if recent_exp:
                        recent_company = recent_exp[0].get('company', 'N/A')
                        st.caption(f"🏢 {recent_company}")
                
                with col4:
                    st.write(f"**Education:** {candidate.get('highest_qualification', 'N/A')}")
                    
                    # Enhanced relevance score display
                    relevance_score = candidate.get('relevance_score') or candidate.get('match_score')
                    if relevance_score is not None:
                        if relevance_score >= 80:
                            st.markdown(f"**Match:** 🟢 {relevance_score}%")
                        elif relevance_score >= 60:
                            st.markdown(f"**Match:** 🟡 {relevance_score}%")
                        elif relevance_score >= 40:
                            st.markdown(f"**Match:** 🟠 {relevance_score}%")
                        else:
                            st.markdown(f"**Match:** 🔴 {relevance_score}%")
                    
                    # Show skill count
                    skill_count = len(candidate.get('skills', []))
                    st.caption(f"🎯 {skill_count} skills")
                
                with col5:
                    # View Details button
                    button_key = f"view_details_{idx}_{candidate.get('email', 'unknown')}"
                    if st.button("👁️ View Details", key=button_key, type="primary", help="View and edit candidate details"):
                        view_candidate_details(candidate)
                
                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown("")  # Add space between cards
    else:
        st.markdown('<div class="warning-message">🔍 No candidates found matching your criteria.</div>', unsafe_allow_html=True)
        st.markdown("### 💡 Try These Tips:")
        st.markdown("""
        - **Use broader search terms** (e.g., 'Developer' instead of 'Senior Full Stack Developer')
        - **Try individual skills** instead of multiple skills at once
        - **Check spelling** of role names and skills
        - **Reduce experience requirements** or other filters
        - **Use the AI Job Description Search** for better matching
        """)