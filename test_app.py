import unittest
import tempfile
import os
import json
import sqlite3
from unittest.mock import Mock, patch, MagicMock
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager
from cv_processor import CVProcessor
from utils import (
    validate_candidate_data, 
    is_valid_email, 
    is_valid_phone,
    calculate_experience_years,
    parse_notice_period
)

class TestDatabaseManager(unittest.TestCase):
    """Test cases for DatabaseManager class"""
    
    def setUp(self):
        """Set up test database"""
        self.test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.test_db.close()
        
        # Mock configuration
        with patch('database.Config') as mock_config:
            mock_config.DB_PATH = self.test_db.name
            mock_config.AZURE_STORAGE_CONNECTION_STRING = None
            mock_config.BACKUP_CONTAINER = 'test-backups'
            
            self.db_manager = DatabaseManager()
    
    def tearDown(self):
        """Clean up test database"""
        if os.path.exists(self.test_db.name):
            os.unlink(self.test_db.name)
    
    def test_database_initialization(self):
        """Test database is properly initialized"""
        self.assertTrue(os.path.exists(self.test_db.name))
        
        # Check if tables exist
        conn = sqlite3.connect(self.test_db.name)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        self.assertIn('candidates', tables)
        self.assertIn('backup_log', tables)
        
        conn.close()
    
    def test_insert_candidate(self):
        """Test candidate insertion"""
        candidate_data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'current_role': 'Software Engineer',
            'phone': '+1234567890',
            'experience': [
                {
                    'position': 'Senior Developer',
                    'company': 'Tech Corp',
                    'years': '3 years',
                    'responsibilities': ['Coding', 'Code Review']
                }
            ],
            'skills': [
                {'skill': 'Python', 'proficiency': 4},
                {'skill': 'JavaScript', 'proficiency': 3}
            ],
            'qualifications': [],
            'achievements': []
        }
        
        result = self.db_manager.insert_candidate(candidate_data)
        self.assertTrue(result)
        
        # Verify insertion
        conn = sqlite3.connect(self.test_db.name)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM candidates WHERE email = ?", ('john@example.com',))
        row = cursor.fetchone()
        
        self.assertIsNotNone(row)
        self.assertEqual(row[1], 'John Doe')  # name
        self.assertEqual(row[3], 'john@example.com')  # email
        
        conn.close()
    
    def test_search_candidates(self):
        """Test candidate search functionality"""
        # Insert test data
        candidate_data = {
            'name': 'Jane Smith',
            'email': 'jane@example.com',
            'current_role': 'Data Scientist',
            'industry': 'Technology',
            'experience': [],
            'skills': [],
            'qualifications': [],
            'achievements': []
        }
        
        self.db_manager.insert_candidate(candidate_data)
        
        # Test search
        search_criteria = {
            'name': 'Jane',
            'industry': 'Technology'
        }
        
        results = self.db_manager.search_candidates(search_criteria)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], 'Jane Smith')
        self.assertEqual(results[0]['industry'], 'Technology')
    
    def test_dashboard_stats(self):
        """Test dashboard statistics"""
        # Insert test candidates
        for i in range(3):
            candidate_data = {
                'name': f'Test User {i}',
                'email': f'test{i}@example.com',
                'industry': 'Technology' if i < 2 else 'Finance',
                'experience': [{'position': 'Developer', 'years': '2 years'}] * (i + 1),
                'skills': [],
                'qualifications': [],
                'achievements': []
            }
            self.db_manager.insert_candidate(candidate_data)
        
        stats = self.db_manager.get_dashboard_stats()
        
        self.assertEqual(stats['total_candidates'], 3)
        self.assertEqual(stats['unique_industries'], 2)
        self.assertGreater(stats['avg_experience'], 0)

class TestCVProcessor(unittest.TestCase):
    """Test cases for CVProcessor class"""
    
    def setUp(self):
        """Set up CV processor with mocked OpenAI client"""
        with patch('cv_processor.Config') as mock_config:
            mock_config.AZURE_OPENAI_ENDPOINT = 'https://test.openai.azure.com'
            mock_config.AZURE_OPENAI_API_KEY = 'test-key'
            mock_config.AZURE_OPENAI_API_VERSION = '2024-02-15-preview'
            mock_config.AZURE_OPENAI_DEPLOYMENT_NAME = 'gpt-4o-mini'
            
            with patch('cv_processor.AzureOpenAI') as mock_openai:
                self.cv_processor = CVProcessor()
                self.cv_processor.client = Mock()
    
    def test_clean_text(self):
        """Test text cleaning functionality"""
        dirty_text = "This   is    a\n\ntest   with\n  extra   spaces"
        clean_text = self.cv_processor._clean_text(dirty_text)
        
        expected = "This is a test with extra spaces"
        self.assertEqual(clean_text, expected)
    
    def test_validate_and_clean_data(self):
        """Test data validation and cleaning"""
        raw_data = {
            'name': '  John Doe  ',
            'email': 'john@example.com',
            'experience': [
                {
                    'position': 'Developer',
                    'company': 'Tech Corp',
                    'years': '2 years',
                    'responsibilities': ['Coding', 'Testing', '']
                }
            ],
            'skills': [
                {'skill': 'Python', 'proficiency': 4},
                {'skill': '', 'proficiency': 3},  # Should be filtered out
                'JavaScript'  # String format, should be converted
            ]
        }
        
        clean_data = self.cv_processor._validate_and_clean_data(raw_data)
        
        self.assertEqual(clean_data['name'], 'John Doe')
        self.assertEqual(len(clean_data['experience']), 1)
        self.assertEqual(len(clean_data['experience'][0]['responsibilities']), 2)
        self.assertEqual(len(clean_data['skills']), 2)  # Empty skill filtered out
    
    def test_validate_proficiency(self):
        """Test proficiency level validation"""
        # Test valid values
        self.assertEqual(self.cv_processor._validate_proficiency(3), 3)
        self.assertEqual(self.cv_processor._validate_proficiency('4'), 4)
        
        # Test boundary values
        self.assertEqual(self.cv_processor._validate_proficiency(0), 1)  # Min clamp
        self.assertEqual(self.cv_processor._validate_proficiency(6), 5)  # Max clamp
        
        # Test invalid values
        self.assertEqual(self.cv_processor._validate_proficiency('invalid'), 3)  # Default
        self.assertEqual(self.cv_processor._validate_proficiency(None), 3)  # Default
    
    @patch('cv_processor.pymupdf')
    def test_extract_text_from_pdf(self, mock_pymupdf):
        """Test PDF text extraction"""
        # Mock PyMuPDF
        mock_doc = Mock()
        mock_page = Mock()
        mock_page.get_text.return_value = "Sample CV text content"
        mock_doc.load_page.return_value = mock_page
        mock_doc.__len__.return_value = 1
        mock_pymupdf.open.return_value = mock_doc
        
        text = self.cv_processor.extract_text_from_pdf('test.pdf')
        
        self.assertEqual(text, "Sample CV text content")
        mock_pymupdf.open.assert_called_once_with('test.pdf')
        mock_doc.close.assert_called_once()

class TestUtils(unittest.TestCase):
    """Test cases for utility functions"""
    
    def test_validate_candidate_data(self):
        """Test candidate data validation"""
        # Valid data
        valid_data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'phone': '+1234567890',
            'experience': [],
            'skills': []
        }
        
        is_valid, errors = validate_candidate_data(valid_data)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
        
        # Invalid data - missing required fields
        invalid_data = {
            'name': '',
            'email': 'invalid-email',
            'phone': 'abc123',
            'experience': 'not-a-list',
            'skills': [
                {'missing_skill_name': True}
            ]
        }
        
        is_valid, errors = validate_candidate_data(invalid_data)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)
    
    def test_email_validation(self):
        """Test email validation"""
        valid_emails = [
            'test@example.com',
            'user.name@domain.co.uk',
            'user+tag@example.org'
        ]
        
        invalid_emails = [
            'invalid-email',
            '@domain.com',
            'user@',
            'user space@domain.com'
        ]
        
        for email in valid_emails:
            self.assertTrue(is_valid_email(email), f"Should be valid: {email}")
        
        for email in invalid_emails:
            self.assertFalse(is_valid_email(email), f"Should be invalid: {email}")
    
    def test_phone_validation(self):
        """Test phone number validation"""
        valid_phones = [
            '+1234567890',
            '(123) 456-7890',
            '123-456-7890',
            '1234567890'
        ]
        
        invalid_phones = [
            '123',  # Too short
            'abc123def',  # Contains letters
            '+1 234',  # Too short
        ]
        
        for phone in valid_phones:
            self.assertTrue(is_valid_phone(phone), f"Should be valid: {phone}")
        
        for phone in invalid_phones:
            self.assertFalse(is_valid_phone(phone), f"Should be invalid: {phone}")
    
    def test_calculate_experience_years(self):
        """Test experience years calculation"""
        experience = [
            {'years': '2 years'},
            {'years': '18 months'},
            {'years': '6 months'},
            {'years': ''}  # Should be ignored
        ]
        
        total_years = calculate_experience_years(experience)
        expected = 2 + 1.5 + 0.5  # 4.0 years
        self.assertEqual(total_years, expected)
    
    def test_parse_notice_period(self):
        """Test notice period parsing"""
        test_cases = [
            ('2 weeks', 14),
            ('1 month', 30),
            ('30 days', 30),
            ('3 months', 90),
            ('immediate', None),
            ('', None)
        ]
        
        for notice_str, expected_days in test_cases:
            result = parse_notice_period(notice_str)
            if expected_days is None:
                self.assertIsNone(result, f"Failed for: {notice_str}")
            else:
                self.assertEqual(result, expected_days, f"Failed for: {notice_str}")

class TestIntegration(unittest.TestCase):
    """Integration tests"""
    
    def setUp(self):
        """Set up integration test environment"""
        self.test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.test_db.close()
        
        with patch('database.Config') as mock_config:
            mock_config.DB_PATH = self.test_db.name
            mock_config.AZURE_STORAGE_CONNECTION_STRING = None
            mock_config.BACKUP_CONTAINER = 'test-backups'
            
            self.db_manager = DatabaseManager()
    
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.test_db.name):
            os.unlink(self.test_db.name)
    
    def test_full_candidate_workflow(self):
        """Test complete candidate processing workflow"""
        # Sample candidate data (as would come from OpenAI processing)
        candidate_data = {
            'name': 'Sarah Johnson',
            'email': 'sarah.johnson@email.com',
            'current_role': 'Senior Data Scientist',
            'phone': '+1-555-0123',
            'notice_period': '4 weeks',
            'current_salary': '$95,000',
            'industry': 'Technology',
            'desired_salary': '$110,000',
            'highest_qualification': 'PhD in Computer Science',
            'experience': [
                {
                    'position': 'Data Scientist',
                    'company': 'Tech Innovations Inc',
                    'years': '3 years',
                    'responsibilities': [
                        'Machine learning model development',
                        'Data pipeline optimization',
                        'Statistical analysis and reporting'
                    ]
                },
                {
                    'position': 'Junior Data Analyst',
                    'company': 'Analytics Corp',
                    'years': '2 years',
                    'responsibilities': [
                        'Data visualization',
                        'Database management',
                        'Report generation'
                    ]
                }
            ],
            'skills': [
                {'skill': 'Python', 'proficiency': 5},
                {'skill': 'R', 'proficiency': 4},
                {'skill': 'SQL', 'proficiency': 5},
                {'skill': 'Machine Learning', 'proficiency': 4},
                {'skill': 'Tableau', 'proficiency': 3}
            ],
            'qualifications': [
                {
                    'qualification': 'PhD in Computer Science',
                    'institution': 'MIT',
                    'year': '2018',
                    'grade': 'Summa Cum Laude'
                },
                {
                    'qualification': 'MSc in Statistics',
                    'institution': 'Stanford University',
                    'year': '2015',
                    'grade': '3.9 GPA'
                }
            ],
            'achievements': [
                'Published 12 research papers in peer-reviewed journals',
                'Led team that increased model accuracy by 23%',
                'Received "Employee of the Year" award in 2022'
            ],
            'special_skills': 'Deep Learning, Natural Language Processing, Cloud Computing (AWS, Azure)'
        }
        
        # Test data validation
        is_valid, errors = validate_candidate_data(candidate_data)
        self.assertTrue(is_valid, f"Validation errors: {errors}")
        
        # Test database insertion
        result = self.db_manager.insert_candidate(candidate_data)
        self.assertTrue(result)
        
        # Test search functionality
        search_results = self.db_manager.search_candidates({'name': 'Sarah'})
        self.assertEqual(len(search_results), 1)
        self.assertEqual(search_results[0]['name'], 'Sarah Johnson')
        
        # Test skills search
        skills_search = self.db_manager.search_candidates({'skills': 'Python'})
        self.assertEqual(len(skills_search), 1)
        
        # Test experience filtering
        exp_search = self.db_manager.search_candidates({'experience_years': 3})
        self.assertEqual(len(exp_search), 1)
        
        # Test industry search
        industry_search = self.db_manager.search_candidates({'industry': 'Technology'})
        self.assertEqual(len(industry_search), 1)
    
    def test_job_matching_scenario(self):
        """Test job matching functionality"""
        # Insert multiple candidates
        candidates = [
            {
                'name': 'Alice Python',
                'email': 'alice@example.com',
                'current_role': 'Python Developer',
                'industry': 'Technology',
                'experience': [{'position': 'Developer', 'years': '5 years'}] * 5,
                'skills': [
                    {'skill': 'Python', 'proficiency': 5},
                    {'skill': 'Django', 'proficiency': 4}
                ],
                'qualifications': [
                    {'qualification': 'BSc Computer Science', 'year': '2018'}
                ],
                'achievements': []
            },
            {
                'name': 'Bob Java',
                'email': 'bob@example.com',
                'current_role': 'Java Developer',
                'industry': 'Finance',
                'experience': [{'position': 'Developer', 'years': '3 years'}] * 3,
                'skills': [
                    {'skill': 'Java', 'proficiency': 5},
                    {'skill': 'Spring', 'proficiency': 4}
                ],
                'qualifications': [
                    {'qualification': 'BSc Software Engineering', 'year': '2020'}
                ],
                'achievements': []
            }
        ]
        
        for candidate in candidates:
            self.db_manager.insert_candidate(candidate)
        
        # Simulate job requirements
        job_requirements = {
            'required_skills': ['Python', 'Django'],
            'min_experience_years': 3,
            'industry': 'Technology',
            'required_qualifications': ['Computer Science']
        }
        
        # Get all candidates for matching
        all_candidates = self.db_manager.search_candidates_by_job_requirements(job_requirements)
        
        # Calculate match scores (this would be done in the main app)
        from app import calculate_match_score
        
        scored_candidates = []
        for candidate in all_candidates:
            score = calculate_match_score(candidate, job_requirements)
            candidate['match_score'] = score
            scored_candidates.append(candidate)
        
        # Sort by score
        scored_candidates.sort(key=lambda x: x['match_score'], reverse=True)
        
        # Alice should have higher score than Bob
        self.assertGreater(scored_candidates[0]['match_score'], scored_candidates[1]['match_score'])
        self.assertEqual(scored_candidates[0]['name'], 'Alice Python')

def create_test_suite():
    """Create and return test suite"""
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTest(unittest.makeSuite(TestDatabaseManager))
    suite.addTest(unittest.makeSuite(TestCVProcessor))
    suite.addTest(unittest.makeSuite(TestUtils))
    suite.addTest(unittest.makeSuite(TestIntegration))
    
    return suite

def run_tests():
    """Run all tests"""
    # Create test suite
    suite = create_test_suite()
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print(f"{'='*50}")
    
    return result.wasSuccessful()

if __name__ == '__main__':
    # Set up test environment
    os.environ['AZURE_STORAGE_CONNECTION_STRING'] = ''
    os.environ['AZURE_OPENAI_ENDPOINT'] = ''
    os.environ['AZURE_OPENAI_API_KEY'] = ''
    
    # Run tests
    success = run_tests()
    sys.exit(0 if success else 1)
