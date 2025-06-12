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
            prompt = self._create_extraction_prompt(cv_text)
            
            response = self.client.chat.completions.create(
                model=Config.AZURE_OPENAI_DEPLOYMENT_NAME,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert HR assistant that extracts structured information from CV/resume text. Always respond with valid JSON format."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=2000
            )
            
            # Parse the response
            content = response.choices[0].message.content
            
            # Extract JSON from response (in case there's extra text)
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                candidate_data = json.loads(json_str)
                
                # Validate and clean the data
                cleaned_data = self._validate_and_clean_data(candidate_data)
                
                logging.info("Successfully processed CV with OpenAI")
                return cleaned_data
            else:
                logging.error("No valid JSON found in OpenAI response")
                return None
                
        except json.JSONDecodeError as e:
            logging.error(f"JSON decode error: {str(e)}")
            return None
        except Exception as e:
            logging.error(f"Error processing CV with OpenAI: {str(e)}")
            return None
    
    def _create_extraction_prompt(self, cv_text: str) -> str:
        """Create prompt for CV data extraction"""
        return f"""
        Extract the following information from this CV/resume text and return it as a JSON object:

        Required fields:
        - name: Full name of the candidate
        - current_role: Current job title/position
        - email: Email address
        - phone: Phone number
        - notice_period: Notice period (if mentioned)
        - current_salary: Current salary (if mentioned)
        - industry: Industry/sector
        - desired_salary: Desired salary (if mentioned)
        - highest_qualification: Highest educational qualification
        - special_skills: Any special skills or certifications

        Array fields (return as arrays of objects):
        - experience: Array of work experience objects with fields:
          - position: Job title
          - company: Company name
          - years: Duration or years in role
          - responsibilities: Array of key responsibilities/achievements
        
        - skills: Array of skill objects with fields:
          - skill: Skill name
          - proficiency: Proficiency level (1-5, where 1 is beginner and 5 is expert)
        
        - qualifications: Array of qualification objects with fields:
          - qualification: Degree/certification name
          - institution: Educational institution
          - year: Year of completion
          - grade: Grade/GPA if mentioned
        
        - achievements: Array of achievement strings

        Instructions:
        1. If information is not available, use empty string or empty array
        2. For skills proficiency, make educated guesses based on context (years of experience, project complexity, etc.)
        3. Extract all relevant experience, even part-time or freelance work
        4. Include all educational qualifications, certifications, and courses
        5. Return valid JSON only, no additional text

        CV Text:
        {cv_text}

        JSON Response:
        """
    
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
                temperature=0.1,
                max_tokens=1000
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
    
    def _validate_and_clean_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean extracted candidate data"""
        cleaned_data = {}
        
        # String fields
        string_fields = [
            'name', 'current_role', 'email', 'phone', 'notice_period',
            'current_salary', 'industry', 'desired_salary', 'highest_qualification',
            'special_skills'
        ]
        
        for field in string_fields:
            cleaned_data[field] = str(data.get(field, '')).strip()
        
        # Array fields with validation
        cleaned_data['experience'] = self._validate_experience(data.get('experience', []))
        cleaned_data['skills'] = self._validate_skills(data.get('skills', []))
        cleaned_data['qualifications'] = self._validate_qualifications(data.get('qualifications', []))
        cleaned_data['achievements'] = self._validate_achievements(data.get('achievements', []))
        
        return cleaned_data
    
    def _validate_experience(self, experience: List[Any]) -> List[Dict[str, Any]]:
        """Validate and clean experience data"""
        validated_exp = []
        
        for exp in experience:
            if isinstance(exp, dict):
                clean_exp = {
                    'position': str(exp.get('position', '')).strip(),
                    'company': str(exp.get('company', '')).strip(),
                    'years': str(exp.get('years', '')).strip(),
                    'responsibilities': []
                }
                
                # Clean responsibilities
                responsibilities = exp.get('responsibilities', [])
                if isinstance(responsibilities, list):
                    clean_exp['responsibilities'] = [str(r).strip() for r in responsibilities if str(r).strip()]
                
                if clean_exp['position'] or clean_exp['company']:
                    validated_exp.append(clean_exp)
        
        return validated_exp
    
    def _validate_skills(self, skills: List[Any]) -> List[Dict[str, Any]]:
        """Validate and clean skills data"""
        validated_skills = []
        
        for skill in skills:
            if isinstance(skill, dict):
                clean_skill = {
                    'skill': str(skill.get('skill', '')).strip(),
                    'proficiency': self._validate_proficiency(skill.get('proficiency', 3))
                }
                
                if clean_skill['skill']:
                    validated_skills.append(clean_skill)
            elif isinstance(skill, str) and skill.strip():
                # Handle case where skills are just strings
                validated_skills.append({
                    'skill': skill.strip(),
                    'proficiency': 3  # Default proficiency
                })
        
        return validated_skills
    
    def _validate_proficiency(self, proficiency: Any) -> int:
        """Validate proficiency level (1-5)"""
        try:
            level = int(proficiency)
            return max(1, min(5, level))  # Clamp between 1 and 5
        except (ValueError, TypeError):
            return 3  # Default to intermediate
    
    def _validate_qualifications(self, qualifications: List[Any]) -> List[Dict[str, Any]]:
        """Validate and clean qualifications data"""
        validated_quals = []
        
        for qual in qualifications:
            if isinstance(qual, dict):
                clean_qual = {
                    'qualification': str(qual.get('qualification', '')).strip(),
                    'institution': str(qual.get('institution', '')).strip(),
                    'year': str(qual.get('year', '')).strip(),
                    'grade': str(qual.get('grade', '')).strip()
                }
                
                if clean_qual['qualification']:
                    validated_quals.append(clean_qual)
        
        return validated_quals
    
    def _validate_achievements(self, achievements: List[Any]) -> List[str]:
        """Validate and clean achievements data"""
        validated_achievements = []
        
        for achievement in achievements:
            if isinstance(achievement, str) and achievement.strip():
                validated_achievements.append(achievement.strip())
            elif isinstance(achievement, dict) and achievement.get('achievement'):
                validated_achievements.append(str(achievement['achievement']).strip())
        
        return validated_achievements
    
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
