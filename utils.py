import re
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
import logging

def validate_candidate_data(candidate_data: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    Validate candidate data before database insertion with enhanced experience validation and comments
    Returns (is_valid, error_messages)
    """
    errors = []
    
    # Required fields validation
    required_fields = ['name', 'email']
    for field in required_fields:
        if not candidate_data.get(field, '').strip():
            errors.append(f"{field.replace('_', ' ').title()} is required")
    
    # Email validation
    email = candidate_data.get('email', '').strip()
    if email and not is_valid_email(email):
        errors.append("Invalid email format")
    
    # Phone validation
    phone = candidate_data.get('phone', '').strip()
    if phone and not is_valid_phone(phone):
        errors.append("Invalid phone number format")
    
    # Comments validation (optional field, just check length if provided)
    comments = candidate_data.get('comments', '')
    if comments and len(comments) > 5000:  # Reasonable limit for comments
        errors.append("Comments field is too long (maximum 5000 characters)")
    
    # Enhanced Experience validation
    experience = candidate_data.get('experience', [])
    if not isinstance(experience, list):
        errors.append("Experience must be a list")
    else:
        for i, exp in enumerate(experience):
            if not isinstance(exp, dict):
                errors.append(f"Experience {i+1} must be an object")
                continue
            
            # Validate basic experience fields
            if not exp.get('position') and not exp.get('company'):
                errors.append(f"Experience {i+1} must have either position or company")
            
            # Validate responsibilities
            responsibilities = exp.get('responsibilities', [])
            if not isinstance(responsibilities, list):
                errors.append(f"Experience {i+1} responsibilities must be a list")
            
            # Validate achievements
            achievements = exp.get('achievements', [])
            if not isinstance(achievements, list):
                errors.append(f"Experience {i+1} achievements must be a list")
            
            # Validate technologies
            technologies = exp.get('technologies', [])
            if not isinstance(technologies, list):
                errors.append(f"Experience {i+1} technologies must be a list")
    
    # Skills validation
    skills = candidate_data.get('skills', [])
    if not isinstance(skills, list):
        errors.append("Skills must be a list")
    else:
        for i, skill in enumerate(skills):
            if not isinstance(skill, dict):
                errors.append(f"Skill {i+1} must be an object with 'skill' and 'proficiency' fields")
            elif not skill.get('skill'):
                errors.append(f"Skill {i+1} is missing skill name")
            elif skill.get('proficiency') and not isinstance(skill.get('proficiency'), int):
                errors.append(f"Skill {i+1} proficiency must be an integer between 1-5")
    
    # Qualifications validation
    qualifications = candidate_data.get('qualifications', [])
    if not isinstance(qualifications, list):
        errors.append("Qualifications must be a list")
    
    # Achievements validation
    achievements = candidate_data.get('achievements', [])
    if not isinstance(achievements, list):
        errors.append("Achievements must be a list")
    
    return len(errors) == 0, errors

def is_valid_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def is_valid_phone(phone: str) -> bool:
    """Validate phone number format"""
    # Remove common separators
    cleaned_phone = re.sub(r'[\s\-\(\)\+]', '', phone)
    
    # Check if it's a valid phone number (8-15 digits)
    pattern = r'^\d{8,15}$'
    return re.match(pattern, cleaned_phone) is not None

def format_search_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Format search results for display with enhanced experience summary"""
    formatted_results = []
    
    for result in results:
        formatted_result = {
            'id': result.get('id'),
            'name': result.get('name', 'N/A'),
            'current_role': result.get('current_role', 'N/A'),
            'email': result.get('email', 'N/A'),
            'phone': format_phone_display(result.get('phone', '')),
            'industry': result.get('industry', 'N/A'),
            'experience_count': len(result.get('experience', [])),
            'skills_count': len(result.get('skills', [])),
            'highest_qualification': result.get('highest_qualification', 'N/A'),
            'notice_period': result.get('notice_period', 'N/A'),
            'created_at': format_datetime(result.get('created_at')),
        }
        
        # Enhanced experience summary
        experience_summary = get_experience_summary(result.get('experience', []))
        formatted_result.update(experience_summary)
        
        # Add match score if available
        if 'match_score' in result:
            formatted_result['match_score'] = result['match_score']
        
        formatted_results.append(formatted_result)
    
    return formatted_results

def get_experience_summary(experience_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Get enhanced summary of candidate's experience"""
    if not experience_list:
        return {
            'total_positions': 0,
            'companies': [],
            'technologies': [],
            'employment_types': []
        }
    
    try:
        companies = []
        technologies = []
        employment_types = []
        total_responsibilities = 0
        total_achievements = 0
        
        for exp in experience_list:
            if exp.get('company'):
                companies.append(exp['company'])
            
            if exp.get('employment_type'):
                employment_types.append(exp['employment_type'])
            
            # Collect technologies
            exp_technologies = exp.get('technologies', [])
            technologies.extend(exp_technologies)
            
            # Count responsibilities and achievements
            total_responsibilities += len(exp.get('responsibilities', []))
            total_achievements += len(exp.get('achievements', []))
        
        # Remove duplicates
        unique_companies = list(set([comp for comp in companies if comp]))
        unique_technologies = list(set([tech for tech in technologies if tech]))
        unique_employment_types = list(set([emp_type for emp_type in employment_types if emp_type]))
        
        return {
            'total_positions': len(experience_list),
            'companies': unique_companies,
            'technologies': unique_technologies,
            'employment_types': unique_employment_types,
            'total_responsibilities': total_responsibilities,
            'total_achievements': total_achievements
        }
        
    except Exception as e:
        logging.error(f"Error getting experience summary: {str(e)}")
        return {
            'total_positions': len(experience_list),
            'companies': [],
            'technologies': [],
            'employment_types': []
        }

def format_phone_display(phone: str) -> str:
    """Format phone number for display"""
    if not phone:
        return 'N/A'
    
    # Remove non-digit characters
    cleaned = re.sub(r'\D', '', phone)
    
    # Format based on length
    if len(cleaned) == 10:
        return f"({cleaned[:3]}) {cleaned[3:6]}-{cleaned[6:]}"
    elif len(cleaned) == 11:
        return f"{cleaned[0]}-({cleaned[1:4]}) {cleaned[4:7]}-{cleaned[7:]}"
    else:
        return phone

def format_datetime(dt_str: Optional[str]) -> str:
    """Format datetime string for display - FIXED VERSION"""
    if not dt_str:
        return 'N/A'
    
    try:
        if isinstance(dt_str, datetime):
            dt = dt_str
        elif isinstance(dt_str, str):
            dt = safe_datetime_parse(dt_str)
            if dt is None:
                return str(dt_str)[:16]  # Return truncated if parsing fails
        else:
            return str(dt_str)
        
        return dt.strftime('%Y-%m-%d %H:%M')
        
    except Exception as e:
        logging.debug(f"Error formatting datetime '{dt_str}': {str(e)}")
        # Return cleaned version
        if isinstance(dt_str, str):
            return dt_str.replace('.000000', '').replace('T', ' ')[:16]
        return str(dt_str)
    
def calculate_experience_years(experience: List[Dict[str, Any]]) -> float:
    """Calculate total years of experience from enhanced experience list"""
    total_years = 0.0
    
    for exp in experience:
        years_str = exp.get('years', '').lower()
        
        if not years_str:
            continue
        
        # Extract numbers from years string
        numbers = re.findall(r'\d+(?:\.\d+)?', years_str)
        
        if numbers:
            if 'month' in years_str:
                # Convert months to years
                total_years += float(numbers[0]) / 12
            else:
                # Assume years
                total_years += float(numbers[0])
    
    return round(total_years, 1)

def extract_skills_list(skills: List[Dict[str, Any]]) -> List[str]:
    """Extract skill names from skills data"""
    return [skill.get('skill', '') for skill in skills if skill.get('skill')]

def extract_technologies_from_experience(experience: List[Dict[str, Any]]) -> List[str]:
    """Extract all technologies from experience list"""
    all_technologies = []
    
    for exp in experience:
        technologies = exp.get('technologies', [])
        all_technologies.extend(technologies)
    
    # Remove duplicates and empty values
    return list(set([tech for tech in all_technologies if tech]))

def get_highest_skill_proficiency(skills: List[Dict[str, Any]]) -> int:
    """Get the highest skill proficiency level"""
    max_proficiency = 0
    
    for skill in skills:
        proficiency = skill.get('proficiency', 0)
        try:
            prof_int = int(proficiency)
            max_proficiency = max(max_proficiency, prof_int)
        except (ValueError, TypeError):
            continue
    
    return max_proficiency

def format_experience_bullet_points(experience: List[Dict[str, Any]]) -> str:
    """Format experience data into readable bullet points"""
    if not experience:
        return "No experience data available"
    
    formatted_text = ""
    
    for i, exp in enumerate(experience, 1):
        position = exp.get('position', 'N/A')
        company = exp.get('company', 'N/A')
        duration = exp.get('years', 'N/A')
        location = exp.get('location', '')
        employment_type = exp.get('employment_type', '')
        
        # Header for each position
        formatted_text += f"\n{i}. **{position}** at **{company}**\n"
        formatted_text += f"   Duration: {duration}"
        
        if location:
            formatted_text += f" | Location: {location}"
        if employment_type:
            formatted_text += f" | Type: {employment_type}"
        
        formatted_text += "\n"
        
        # Responsibilities
        responsibilities = exp.get('responsibilities', [])
        if responsibilities:
            formatted_text += "   **Key Responsibilities:**\n"
            for resp in responsibilities:
                if resp.strip():
                    formatted_text += f"   • {resp}\n"
        
        # Achievements
        achievements = exp.get('achievements', [])
        if achievements:
            formatted_text += "   **Achievements:**\n"
            for ach in achievements:
                if ach.strip():
                    formatted_text += f"   ★ {ach}\n"
        
        # Technologies
        technologies = exp.get('technologies', [])
        if technologies:
            formatted_text += f"   **Technologies Used:** {', '.join(technologies)}\n"
        
        # Additional details
        additional_details = []
        if exp.get('team_size'):
            additional_details.append(f"Team Size: {exp['team_size']}")
        if exp.get('reporting_to'):
            additional_details.append(f"Reported to: {exp['reporting_to']}")
        
        if additional_details:
            formatted_text += f"   **Additional Details:** {' | '.join(additional_details)}\n"
        
        formatted_text += "\n"
    
    return formatted_text

def format_salary(salary_str: str) -> str:
    """Format salary string for display"""
    if not salary_str:
        return 'N/A'
    
    # Extract numbers from salary string
    numbers = re.findall(r'\d+(?:,\d+)*(?:\.\d+)?', salary_str)
    
    if numbers:
        # Remove commas and convert to float
        try:
            amount = float(numbers[0].replace(',', ''))
            
            # Format based on amount
            if amount >= 1000000:
                return f"${amount/1000000:.1f}M"
            elif amount >= 1000:
                return f"${amount/1000:.0f}K"
            else:
                return f"${amount:.0f}"
        except ValueError:
            pass
    
    return salary_str

def generate_candidate_id(name: str, email: str) -> str:
    """Generate a unique candidate identifier"""
    import hashlib
    
    # Create hash from name and email
    data = f"{name.lower().strip()}{email.lower().strip()}"
    return hashlib.md5(data.encode()).hexdigest()[:8]

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    # Remove or replace unsafe characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove extra spaces and dots
    filename = re.sub(r'\.+', '.', filename)
    filename = re.sub(r'\s+', '_', filename)
    
    # Ensure filename is not too long
    if len(filename) > 100:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:95] + ('.' + ext if ext else '')
    
    return filename

def parse_notice_period(notice_period_str: str) -> Optional[int]:
    """Parse notice period string and return days"""
    if not notice_period_str:
        return None
    
    notice_lower = notice_period_str.lower()
    
    # Extract numbers
    numbers = re.findall(r'\d+', notice_lower)
    
    if not numbers:
        return None
    
    days = int(numbers[0])
    
    # Convert based on unit
    if 'week' in notice_lower:
        return days * 7
    elif 'month' in notice_lower:
        return days * 30
    elif 'day' in notice_lower:
        return days
    else:
        # Default to days
        return days

def highlight_search_terms(text: str, search_terms: List[str]) -> str:
    """Highlight search terms in text (for display purposes)"""
    if not text or not search_terms:
        return text
    
    highlighted_text = text
    
    for term in search_terms:
        if term.strip():
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            highlighted_text = pattern.sub(f"**{term}**", highlighted_text)
    
    return highlighted_text

def validate_enhanced_experience(experience: Dict[str, Any]) -> tuple[bool, List[str]]:
    """Validate enhanced experience entry"""
    errors = []
    
    # Basic validation
    if not experience.get('position') and not experience.get('company'):
        errors.append("Experience must have either position or company")
    
    # Validate lists
    list_fields = ['responsibilities', 'achievements', 'technologies']
    for field in list_fields:
        field_value = experience.get(field, [])
        if not isinstance(field_value, list):
            errors.append(f"{field.replace('_', ' ').title()} must be a list")
    
    # Validate employment type if provided
    valid_employment_types = ['Full-time', 'Part-time', 'Contract', 'Internship', 'Freelance', 'Consultant']
    employment_type = experience.get('employment_type', '')
    if employment_type and employment_type not in valid_employment_types:
        errors.append(f"Employment type must be one of: {', '.join(valid_employment_types)}")
    
    return len(errors) == 0, errors

def extract_keywords_from_experience(experience_list: List[Dict[str, Any]]) -> List[str]:
    """Extract keywords from experience for search indexing"""
    keywords = []
    
    for exp in experience_list:
        # Add position and company
        if exp.get('position'):
            keywords.append(exp['position'])
        if exp.get('company'):
            keywords.append(exp['company'])
        
        # Add technologies
        technologies = exp.get('technologies', [])
        keywords.extend(technologies)
        
        # Extract key words from responsibilities and achievements
        responsibilities = exp.get('responsibilities', [])
        achievements = exp.get('achievements', [])
        
        all_text = ' '.join(responsibilities + achievements)
        
        # Extract meaningful words (more than 3 characters)
        words = re.findall(r'\b\w{4,}\b', all_text.lower())
        keywords.extend(words)
    
    # Remove duplicates and common words
    common_words = {'with', 'using', 'this', 'that', 'have', 'been', 'were', 'will', 'from', 'they', 'would', 'could', 'should'}
    unique_keywords = list(set([kw for kw in keywords if kw.lower() not in common_words]))
    
    return unique_keywords

def setup_logging():
    """Setup logging configuration"""
    from config import Config
    
    logging.basicConfig(
        level=getattr(logging, Config.LOG_LEVEL.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
        ]
    )
    
    # Reduce noise from external libraries
    logging.getLogger('azure').setLevel(logging.WARNING)
    logging.getLogger('openai').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)

def validate_file_upload(file_content: bytes, filename: str) -> tuple[bool, str]:
    """Validate uploaded file"""
    from config import Config
    
    # Check file size
    file_size_mb = len(file_content) / (1024 * 1024)
    if file_size_mb > Config.MAX_FILE_SIZE_MB:
        return False, f"File size ({file_size_mb:.1f}MB) exceeds maximum allowed size ({Config.MAX_FILE_SIZE_MB}MB)"
    
    # Check file extension
    file_extension = filename.lower().split('.')[-1] if '.' in filename else ''
    if file_extension not in Config.ALLOWED_EXTENSIONS:
        return False, f"File type '{file_extension}' not allowed. Allowed types: {', '.join(Config.ALLOWED_EXTENSIONS)}"
    
    # Check if file is actually a PDF (basic check)
    if not file_content.startswith(b'%PDF'):
        return False, "File does not appear to be a valid PDF"
    
    return True, "File validation passed"

def get_file_info(file_content: bytes, filename: str) -> Dict[str, Any]:
    """Get information about uploaded file"""
    return {
        'filename': filename,
        'size_bytes': len(file_content),
        'size_mb': round(len(file_content) / (1024 * 1024), 2),
        'extension': filename.lower().split('.')[-1] if '.' in filename else '',
        'is_pdf': file_content.startswith(b'%PDF')
    }

def format_experience_for_display(experience: Dict[str, Any]) -> str:
    """Format a single experience entry for clean display"""
    position = experience.get('position', 'N/A')
    company = experience.get('company', 'N/A')
    duration = experience.get('years', 'N/A')
    
    display_text = f"{position} at {company} ({duration})"
    
    # Add location if available
    location = experience.get('location', '')
    if location:
        display_text += f" - {location}"
    
    return display_text



from datetime import datetime, timezone, timedelta

def format_datetime_gmt_plus_2(dt_str: Optional[str]) -> str:
    """Format datetime string for display in GMT+2 timezone - FIXED VERSION"""
    if not dt_str:
        return 'N/A'
    
    try:
        if isinstance(dt_str, str):
            if 'T' in dt_str:
                # ISO format
                dt_str = dt_str.replace('Z', '+00:00')
                if '+' not in dt_str and dt_str.endswith(':00'):
                    dt_str += '+00:00'
                dt = datetime.fromisoformat(dt_str)
            else:
                # SQLite format - Remove microseconds if present
                clean_dt_str = re.sub(r'\.\d+$', '', dt_str)
                
                try:
                    # Try parsing without microseconds first
                    dt = datetime.strptime(clean_dt_str, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    try:
                        # Try with microseconds
                        dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S.%f')
                    except ValueError:
                        # Fallback
                        dt = datetime.fromisoformat(dt_str.replace(' ', 'T'))
                
                dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt_str
        
        # Convert to GMT+2
        gmt_plus_2 = timezone(timedelta(hours=2))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        
        dt_gmt_plus_2 = dt.astimezone(gmt_plus_2)
        return dt_gmt_plus_2.strftime('%Y-%m-%d %H:%M SAST')
        
    except (ValueError, AttributeError) as e:
        logging.debug(f"Failed to parse datetime '{dt_str}': {str(e)}")
        # Return cleaned version
        return str(dt_str).replace('.000000', '').replace('T', ' ')[:16]

def get_current_time_gmt_plus_2() -> datetime:
    """Get current time in GMT+2 timezone"""
    gmt_plus_2 = timezone(timedelta(hours=2))
    return datetime.now(gmt_plus_2)

def format_current_time_gmt_plus_2() -> str:
    """Get current time formatted in GMT+2"""
    current_time = get_current_time_gmt_plus_2()
    return current_time.strftime('%Y-%m-%d %H:%M:%S SAST')

def safe_datetime_parse(dt_str: str) -> Optional[datetime]:
    """Safely parse datetime string with multiple format support"""
    if not dt_str:
        return None
    
    formats = [
        '%Y-%m-%d %H:%M:%S.%f',      # SQLite with microseconds
        '%Y-%m-%d %H:%M:%S',         # SQLite without microseconds
        '%Y-%m-%dT%H:%M:%S.%fZ',     # ISO with microseconds
        '%Y-%m-%dT%H:%M:%SZ',        # ISO without microseconds
        '%Y-%m-%dT%H:%M:%S.%f',      # ISO with microseconds
        '%Y-%m-%dT%H:%M:%S',         # ISO without microseconds
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            continue
    
    # Fallback
    try:
        clean_str = dt_str.replace(' ', 'T')
        if not clean_str.endswith('Z') and '+' not in clean_str[-6:]:
            clean_str += 'Z'
        return datetime.fromisoformat(clean_str.replace('Z', '+00:00'))
    except ValueError:
        logging.warning(f"Could not parse datetime: {dt_str}")
        return None
    

# Helper function to validate comments specifically (can be used separately)
def validate_comments(comments: str) -> tuple[bool, str]:
    """
    Validate comments field specifically
    Returns (is_valid, error_message)
    """
    if not comments:
        return True, ""  # Comments are optional
    
    if not isinstance(comments, str):
        return False, "Comments must be text"
    
    # Check length
    max_length = 5000
    if len(comments) > max_length:
        return False, f"Comments field is too long (maximum {max_length} characters, current: {len(comments)})"
    
    # Check for potentially harmful content (basic check)
    if any(char in comments for char in ['<script', '<iframe', 'javascript:']):
        return False, "Comments contain potentially harmful content"
    
    return True, ""

# Helper function to sanitize comments for safe storage
def sanitize_comments(comments: str) -> str:
    """
    Sanitize comments for safe storage and display
    """
    if not comments:
        return ""
    
    # Remove potentially harmful content
    import re
    
    # Remove HTML tags
    comments = re.sub(r'<[^>]+>', '', comments)
    
    # Remove script-like content
    comments = re.sub(r'javascript:', '', comments, flags=re.IGNORECASE)
    
    # Clean up extra whitespace
    comments = re.sub(r'\s+', ' ', comments).strip()
    
    # Truncate if too long
    max_length = 5000
    if len(comments) > max_length:
        comments = comments[:max_length] + "..."
    
    return comments
