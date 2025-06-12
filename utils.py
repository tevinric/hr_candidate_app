import re
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

def validate_candidate_data(candidate_data: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    Validate candidate data before database insertion
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
    
    # Experience validation
    experience = candidate_data.get('experience', [])
    if not isinstance(experience, list):
        errors.append("Experience must be a list")
    
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
    """Format search results for display"""
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
        
        # Add match score if available
        if 'match_score' in result:
            formatted_result['match_score'] = result['match_score']
        
        formatted_results.append(formatted_result)
    
    return formatted_results

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
    """Format datetime string for display"""
    if not dt_str:
        return 'N/A'
    
    try:
        # Parse ISO format datetime
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M')
    except (ValueError, AttributeError):
        return dt_str

def calculate_experience_years(experience: List[Dict[str, Any]]) -> float:
    """Calculate total years of experience from experience list"""
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
