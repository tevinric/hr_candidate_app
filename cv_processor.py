import pymupdf
import json
import logging
import re
from typing import Dict, List, Optional, Any
from openai import AzureOpenAI
from config import Config

class CVProcessor:
    def __init__(self):
        self.client = None
        
        # Initialize OpenAI client if configured
        if all([Config.AZURE_OPENAI_ENDPOINT, Config.AZURE_OPENAI_API_KEY, Config.AZURE_OPENAI_API_VERSION]):
            try:
                self.client = AzureOpenAI(
                    azure_endpoint=Config.AZURE_OPENAI_ENDPOINT,
                    api_key=Config.AZURE_OPENAI_API_KEY,
                    api_version=Config.AZURE_OPENAI_API_VERSION
                )
                logging.info("Azure OpenAI client initialized successfully")
            except Exception as e:
                logging.error(f"Failed to initialize Azure OpenAI client: {str(e)}")
        else:
            logging.warning("Azure OpenAI configuration missing")
    
    def extract_text_from_pdf(self, pdf_path: str) -> Optional[str]:
        """Extract text from PDF using PyMuPDF"""
        try:
            doc = pymupdf.open(pdf_path)
            text = ""
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text += page.get_text()
            
            doc.close()
            
            # Clean up the text
            text = self._clean_text(text)
            
            logging.info(f"Successfully extracted text from PDF: {len(text)} characters")
            return text
            
        except Exception as e:
            logging.error(f"Error extracting text from PDF: {str(e)}")
            return None
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters that might cause issues
        text = re.sub(r'[^\w\s@.,;:()\-+/]', '', text)
        
        # Normalize line breaks
        text = text.replace('\n', ' ')
        
        return text.strip()
    
    def process_cv_with_openai(self, cv_text: str) -> Optional[Dict[str, Any]]:
        """Process CV text with Azure OpenAI to extract structured data"""
        if not self.client:
            logging.error("OpenAI client not initialized")
            return None
        
        try:
            prompt = self._create_enhanced_extraction_prompt(cv_text)
            
            response = self.client.chat.completions.create(
                model=Config.AZURE_OPENAI_DEPLOYMENT_NAME,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert HR assistant that extracts comprehensive structured information from CV/resume text. You must extract ALL available information and return complete, valid JSON. Be thorough and extract every detail mentioned in the CV."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1
            )
            
            # Parse the response
            content = response.choices[0].message.content
            logging.info(f"OpenAI response received: {len(content)} characters")
            
            # Extract JSON from response (in case there's extra text)
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                candidate_data = json.loads(json_str)
                
                # Enhanced validation and cleaning
                cleaned_data = self._enhanced_validate_and_clean_data(candidate_data)
                
                logging.info("Successfully processed CV with OpenAI")
                logging.info(f"Extracted fields: {list(cleaned_data.keys())}")
                
                # Log extraction summary for debugging
                self._log_extraction_summary(cleaned_data)
                
                return cleaned_data
            else:
                logging.error("No valid JSON found in OpenAI response")
                logging.debug(f"OpenAI response content: {content}")
                return None
                
        except json.JSONDecodeError as e:
            logging.error(f"JSON decode error: {str(e)}")
            logging.debug(f"Failed JSON content: {content}")
            return None
        except Exception as e:
            logging.error(f"Error processing CV with OpenAI: {str(e)}")
            return None
    
    def _create_enhanced_extraction_prompt(self, cv_text: str) -> str:
        """Create enhanced prompt for comprehensive CV data extraction"""
        return f"""
Extract ALL information from this CV/resume and return it as a comprehensive JSON object. 
Extract EVERY detail mentioned, no matter how small. Be thorough and complete.

CRITICAL: You must extract information for ALL these fields. If a field is not explicitly mentioned, try to infer it from context or set it as empty string/array.

Required JSON structure:
{{
    "name": "Full name of the candidate",
    "current_role": "Current job title/position",
    "email": "Email address", 
    "phone": "Phone number (with country code if available)",
    "notice_period": "Notice period (extract any mention of availability, notice period, or when they can start)",
    "current_salary": "Current salary (extract any salary information mentioned)",
    "industry": "Industry/sector (infer from experience if not explicitly stated)",
    "desired_salary": "Desired/expected salary (extract any salary expectations)",
    "highest_qualification": "Highest educational qualification achieved",
    "special_skills": "Any special skills, certifications, languages, or unique abilities mentioned",
    
    "experience": [
        {{
            "position": "Job title/role name",
            "company": "Company/organization name", 
            "years": "Duration in role (e.g., '2020-2023', '3 years', 'Jan 2020 - Present')",
            "location": "Work location if mentioned",
            "employment_type": "Full-time/Part-time/Contract/Internship/Freelance/Consultant",
            "team_size": "Team size managed or worked with",
            "reporting_to": "Who they reported to (manager title/name)",
            "responsibilities": [
                "Detailed responsibility 1 - extract EXACT text from CV",
                "Detailed responsibility 2 - include specific tools, processes, methodologies", 
                "Detailed responsibility 3 - capture quantified results and scope"
            ],
            "achievements": [
                "Specific achievement 1 with measurable results",
                "Awards, recognitions, or accomplishments in this role"
            ],
            "technologies": [
                "Technology 1", "Tool 1", "Software 1", "Programming language 1"
            ]
        }}
    ],
    
    "skills": [
        {{
            "skill": "Skill name",
            "proficiency": 1-5 (1=Beginner, 2=Basic, 3=Intermediate, 4=Advanced, 5=Expert)
        }}
    ],
    
    "qualifications": [
        {{
            "qualification": "Degree/certification name",
            "institution": "Educational institution/university",
            "year": "Year of completion", 
            "grade": "Grade/GPA/result if mentioned"
        }}
    ],
    
    "achievements": [
        "General achievement/award/recognition 1",
        "Publication, patent, or significant accomplishment 2",
        "Professional certification or notable project 3"
    ]
}}

EXTRACTION GUIDELINES:
1. EXTRACT ALL WORK EXPERIENCE - scan the entire CV for every job, internship, project role
2. CAPTURE COMPLETE DETAILS - for each role, extract every responsibility, achievement, and technology mentioned
3. INFER MISSING INFORMATION - if industry isn't stated, infer from job titles/companies
4. EXTRACT ALL SKILLS - from dedicated skills sections AND from job descriptions
5. GET ALL EDUCATION - degrees, certifications, courses, training programs
6. FIND ALL ACHIEVEMENTS - awards, recognitions, publications, patents, notable projects
7. EXTRACT CONTACT INFO - phone numbers, email addresses, LinkedIn profiles
8. CAPTURE SALARY INFO - any mention of current salary, expectations, or compensation
9. GET AVAILABILITY INFO - notice periods, availability dates, visa status

PROFICIENCY SCORING GUIDE:
- 5 (Expert): 5+ years experience, leading others, architectural decisions
- 4 (Advanced): 3-5 years experience, complex projects, mentoring others  
- 3 (Intermediate): 1-3 years experience, independent work
- 2 (Basic): <1 year experience, guided work
- 1 (Beginner): Learning or just started

IMPORTANT: 
- Extract responsibilities EXACTLY as written in the CV
- Include ALL technologies, tools, frameworks, languages mentioned
- Capture quantified achievements (percentages, amounts, timeframes)
- If multiple roles at same company, create separate experience entries
- Extract soft skills, technical skills, and domain expertise
- Include internships, part-time work, freelance projects
- Capture all educational background including certifications

CV Text:
{cv_text}

Return ONLY the JSON object, no additional text:
"""
    
    def _enhanced_validate_and_clean_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced validation and cleaning of extracted candidate data"""
        cleaned_data = {}
        
        # String fields - more lenient cleaning
        string_fields = [
            'name', 'current_role', 'email', 'phone', 'notice_period',
            'current_salary', 'industry', 'desired_salary', 'highest_qualification',
            'special_skills'
        ]
        
        for field in string_fields:
            value = data.get(field, '')
            if isinstance(value, (str, int, float)):
                cleaned_data[field] = str(value).strip()
            else:
                cleaned_data[field] = ''
        
        # Enhanced experience validation
        cleaned_data['experience'] = self._enhanced_validate_experience(data.get('experience', []))
        
        # Enhanced skills validation  
        cleaned_data['skills'] = self._enhanced_validate_skills(data.get('skills', []))
        
        # Enhanced qualifications validation
        cleaned_data['qualifications'] = self._enhanced_validate_qualifications(data.get('qualifications', []))
        
        # Enhanced achievements validation
        cleaned_data['achievements'] = self._enhanced_validate_achievements(data.get('achievements', []))
        
        return cleaned_data
    
    def _enhanced_validate_experience(self, experience: List[Any]) -> List[Dict[str, Any]]:
        """Enhanced validation and cleaning of experience data"""
        validated_exp = []
        
        if not isinstance(experience, list):
            logging.warning("Experience is not a list, attempting to convert")
            if isinstance(experience, dict):
                experience = [experience]
            else:
                return []
        
        for i, exp in enumerate(experience):
            if not isinstance(exp, dict):
                logging.warning(f"Experience entry {i} is not a dict: {type(exp)}")
                continue
                
            clean_exp = {
                'position': self._safe_string_extract(exp.get('position', '')),
                'company': self._safe_string_extract(exp.get('company', '')),
                'years': self._safe_string_extract(exp.get('years', '')),
                'location': self._safe_string_extract(exp.get('location', '')),
                'employment_type': self._safe_string_extract(exp.get('employment_type', '')),
                'team_size': self._safe_string_extract(exp.get('team_size', '')),
                'reporting_to': self._safe_string_extract(exp.get('reporting_to', '')),
                'responsibilities': [],
                'achievements': [],
                'technologies': []
            }
            
            # Enhanced responsibility cleaning
            responsibilities = exp.get('responsibilities', [])
            if isinstance(responsibilities, list):
                clean_exp['responsibilities'] = [
                    self._safe_string_extract(r) for r in responsibilities 
                    if self._safe_string_extract(r)
                ]
            elif isinstance(responsibilities, str):
                # Handle case where responsibilities is a single string
                clean_exp['responsibilities'] = [self._safe_string_extract(responsibilities)] if responsibilities.strip() else []
            
            # Enhanced achievements cleaning
            achievements = exp.get('achievements', [])
            if isinstance(achievements, list):
                clean_exp['achievements'] = [
                    self._safe_string_extract(a) for a in achievements 
                    if self._safe_string_extract(a)
                ]
            elif isinstance(achievements, str):
                clean_exp['achievements'] = [self._safe_string_extract(achievements)] if achievements.strip() else []
            
            # Enhanced technologies cleaning
            technologies = exp.get('technologies', [])
            if isinstance(technologies, list):
                clean_exp['technologies'] = [
                    self._safe_string_extract(t) for t in technologies 
                    if self._safe_string_extract(t)
                ]
            elif isinstance(technologies, str):
                # Handle comma-separated technologies string
                tech_list = [t.strip() for t in technologies.split(',') if t.strip()]
                clean_exp['technologies'] = tech_list
            
            # Only add if has meaningful content
            if (clean_exp['position'] or clean_exp['company'] or 
                clean_exp['responsibilities'] or clean_exp['achievements']):
                validated_exp.append(clean_exp)
                logging.info(f"Added experience: {clean_exp['position']} at {clean_exp['company']}")
        
        logging.info(f"Validated {len(validated_exp)} experience entries")
        return validated_exp
    
    def _enhanced_validate_skills(self, skills: List[Any]) -> List[Dict[str, Any]]:
        """Enhanced validation and cleaning of skills data"""
        validated_skills = []
        
        if not isinstance(skills, list):
            logging.warning("Skills is not a list, attempting to convert")
            return []
        
        for i, skill in enumerate(skills):
            if isinstance(skill, dict):
                skill_name = self._safe_string_extract(skill.get('skill', ''))
                if skill_name:
                    clean_skill = {
                        'skill': skill_name,
                        'proficiency': self._enhanced_validate_proficiency(skill.get('proficiency', 3))
                    }
                    validated_skills.append(clean_skill)
                    
            elif isinstance(skill, str) and skill.strip():
                # Handle case where skills are just strings
                validated_skills.append({
                    'skill': skill.strip(),
                    'proficiency': 3  # Default proficiency
                })
            else:
                logging.warning(f"Skipping invalid skill entry {i}: {skill}")
        
        logging.info(f"Validated {len(validated_skills)} skills")
        return validated_skills
    
    def _enhanced_validate_qualifications(self, qualifications: List[Any]) -> List[Dict[str, Any]]:
        """Enhanced validation and cleaning of qualifications data"""
        validated_quals = []
        
        if not isinstance(qualifications, list):
            logging.warning("Qualifications is not a list, attempting to convert")
            return []
        
        for i, qual in enumerate(qualifications):
            if isinstance(qual, dict):
                qualification_name = self._safe_string_extract(qual.get('qualification', ''))
                if qualification_name:
                    clean_qual = {
                        'qualification': qualification_name,
                        'institution': self._safe_string_extract(qual.get('institution', '')),
                        'year': self._safe_string_extract(qual.get('year', '')),
                        'grade': self._safe_string_extract(qual.get('grade', ''))
                    }
                    validated_quals.append(clean_qual)
            else:
                logging.warning(f"Skipping invalid qualification entry {i}: {qual}")
        
        logging.info(f"Validated {len(validated_quals)} qualifications")
        return validated_quals
    
    def _enhanced_validate_achievements(self, achievements: List[Any]) -> List[str]:
        """Enhanced validation and cleaning of achievements data"""
        validated_achievements = []
        
        if not isinstance(achievements, list):
            logging.warning("Achievements is not a list, attempting to convert")
            if isinstance(achievements, str):
                return [achievements.strip()] if achievements.strip() else []
            return []
        
        for achievement in achievements:
            if isinstance(achievement, str) and achievement.strip():
                validated_achievements.append(achievement.strip())
            elif isinstance(achievement, dict) and achievement.get('achievement'):
                validated_achievements.append(str(achievement['achievement']).strip())
            else:
                # Try to convert to string
                try:
                    ach_str = str(achievement).strip()
                    if ach_str and ach_str != 'None':
                        validated_achievements.append(ach_str)
                except:
                    continue
        
        logging.info(f"Validated {len(validated_achievements)} achievements")
        return validated_achievements
    
    def _safe_string_extract(self, value: Any) -> str:
        """Safely extract string value from any input"""
        if value is None:
            return ''
        if isinstance(value, str):
            return value.strip()
        try:
            return str(value).strip()
        except:
            return ''
    
    def _enhanced_validate_proficiency(self, proficiency: Any) -> int:
        """Enhanced proficiency level validation (1-5)"""
        try:
            if isinstance(proficiency, str):
                # Try to extract number from string
                numbers = re.findall(r'\d+', proficiency)
                if numbers:
                    level = int(numbers[0])
                else:
                    # Try to map common proficiency words
                    proficiency_lower = proficiency.lower()
                    if any(word in proficiency_lower for word in ['expert', 'advanced', 'senior']):
                        level = 5
                    elif any(word in proficiency_lower for word in ['intermediate', 'moderate']):
                        level = 3
                    elif any(word in proficiency_lower for word in ['basic', 'beginner', 'junior']):
                        level = 2
                    else:
                        level = 3
            else:
                level = int(proficiency)
            
            return max(1, min(5, level))  # Clamp between 1 and 5
        except (ValueError, TypeError):
            return 3  # Default to intermediate
    
    def _log_extraction_summary(self, candidate_data: Dict[str, Any]):
        """Log summary of extracted data for debugging"""
        logging.info("=== CV EXTRACTION SUMMARY ===")
        logging.info(f"Name: {candidate_data.get('name', 'N/A')}")
        logging.info(f"Email: {candidate_data.get('email', 'N/A')}")
        logging.info(f"Current Role: {candidate_data.get('current_role', 'N/A')}")
        logging.info(f"Industry: {candidate_data.get('industry', 'N/A')}")
        logging.info(f"Experience Entries: {len(candidate_data.get('experience', []))}")
        logging.info(f"Skills Count: {len(candidate_data.get('skills', []))}")
        logging.info(f"Qualifications Count: {len(candidate_data.get('qualifications', []))}")
        logging.info(f"Achievements Count: {len(candidate_data.get('achievements', []))}")
        
        # Log experience details
        for i, exp in enumerate(candidate_data.get('experience', [])):
            logging.info(f"Experience {i+1}: {exp.get('position', 'N/A')} at {exp.get('company', 'N/A')}")
            logging.info(f"  - Responsibilities: {len(exp.get('responsibilities', []))}")
            logging.info(f"  - Achievements: {len(exp.get('achievements', []))}")
            logging.info(f"  - Technologies: {len(exp.get('technologies', []))}")
        
        # Log skills
        skills = candidate_data.get('skills', [])
        if skills:
            skill_names = [skill.get('skill', 'N/A') for skill in skills[:5]]
            logging.info(f"Top 5 Skills: {', '.join(skill_names)}")
        
        logging.info("=== END EXTRACTION SUMMARY ===")
    
    def extract_job_requirements(self, job_description: str) -> Optional[Dict[str, Any]]:
        """Extract requirements from job description using OpenAI"""
        if not self.client:
            logging.error("OpenAI client not initialized")
            return None
        
        try:
            prompt = self._create_job_extraction_prompt(job_description)
            
            response = self.client.chat.completions.create(
                model=Config.AZURE_OPENAI_DEPLOYMENT_NAME,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert HR assistant that extracts job requirements from job descriptions. Always respond with valid JSON format."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                requirements = json.loads(json_str)
                
                logging.info("Successfully extracted job requirements")
                return requirements
            else:
                logging.error("No valid JSON found in job requirements response")
                return None
                
        except json.JSONDecodeError as e:
            logging.error(f"JSON decode error in job requirements: {str(e)}")
            return None
        except Exception as e:
            logging.error(f"Error extracting job requirements: {str(e)}")
            return None
    
    def _create_job_extraction_prompt(self, job_description: str) -> str:
        """Create prompt for job requirements extraction"""
        return f"""
        Extract the following information from this job description and return it as a JSON object:

        Required fields:
        - job_title: Job title/position
        - industry: Industry/sector
        - min_experience_years: Minimum years of experience required (as integer)
        - required_skills: Array of required skills (strings)
        - preferred_skills: Array of preferred/nice-to-have skills (strings)
        - required_qualifications: Array of required educational qualifications (strings)
        - job_type: Employment type (full-time, part-time, contract, etc.)
        - location: Job location
        - salary_range: Salary range if mentioned
        - key_responsibilities: Array of main job responsibilities (strings)
        - technologies: Array of specific technologies/tools mentioned (strings)
        - seniority_level: Seniority level (entry, junior, mid, senior, lead, etc.)

        Instructions:
        1. Extract only explicit requirements, don't assume
        2. For skills, include both technical and soft skills mentioned
        3. If minimum experience is not clearly stated, estimate based on role level
        4. Return valid JSON only, no additional text
        5. Use empty string or empty array if information is not available

        Job Description:
        {job_description}

        JSON Response:
        """
    
    def extract_candidate_summary(self, candidate_data: Dict[str, Any]) -> str:
        """Generate a summary of candidate profile"""
        try:
            summary_parts = []
            
            name = candidate_data.get('name', 'Unknown')
            role = candidate_data.get('current_role', 'N/A')
            summary_parts.append(f"{name} - {role}")
            
            # Experience summary
            experience = candidate_data.get('experience', [])
            if experience:
                summary_parts.append(f"Experience: {len(experience)} positions")
            
            # Skills summary
            skills = candidate_data.get('skills', [])
            if skills:
                skill_names = [skill.get('skill', '') for skill in skills[:5]]  # Top 5 skills
                summary_parts.append(f"Key skills: {', '.join(skill_names)}")
            
            # Qualification
            highest_qual = candidate_data.get('highest_qualification', '')
            if highest_qual:
                summary_parts.append(f"Education: {highest_qual}")
            
            return " | ".join(summary_parts)
            
        except Exception as e:
            logging.error(f"Error generating candidate summary: {str(e)}")
            return f"{candidate_data.get('name', 'Unknown')} - Profile available"