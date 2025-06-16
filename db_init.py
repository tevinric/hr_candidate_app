#!/usr/bin/env python3
"""
HR Candidate Management Tool - Database Initialization Script
This script creates and initializes the SQLite database with proper schema.
"""

import sqlite3
import os
import json
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class DatabaseInitializer:
    def __init__(self, db_path=None):
        """Initialize database manager"""
        if db_path is None:
            # Default path - same as in config.py
            # Get the workspace root directory (parent of hr_candidate_app)
            workspace_root = Path(__file__).parent.parent.absolute()
            self.db_path = os.path.join(workspace_root, "hr_candidates.db")
        else:
            self.db_path = db_path
        
        # Ensure directory exists
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        
        logging.info(f"Database path: {self.db_path}")
    
    def create_database(self):
        """Create database with all required tables"""
        try:
            # Remove existing database if it exists
            if os.path.exists(self.db_path):
                logging.info(f"Removing existing database: {self.db_path}")
                os.remove(self.db_path)
            
            # Create new database
            logging.info("Creating new database...")
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create candidates table
            logging.info("Creating candidates table...")
            cursor.execute('''
                CREATE TABLE candidates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    current_role TEXT,
                    email TEXT UNIQUE,
                    phone TEXT,
                    notice_period TEXT,
                    current_salary TEXT,
                    industry TEXT,
                    desired_salary TEXT,
                    highest_qualification TEXT,
                    experience TEXT,  -- JSON string containing work experience
                    skills TEXT,      -- JSON string containing skills array
                    qualifications TEXT,  -- JSON string containing qualifications array
                    achievements TEXT,    -- JSON string containing achievements array
                    special_skills TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create backup log table
            logging.info("Creating backup_log table...")
            cursor.execute('''
                CREATE TABLE backup_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    backup_name TEXT NOT NULL,
                    backup_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT NOT NULL,
                    file_size INTEGER
                )
            ''')
            
            # Create sync log table
            logging.info("Creating sync_log table...")
            cursor.execute('''
                CREATE TABLE sync_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sync_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    sync_type TEXT NOT NULL,  -- 'upload' or 'download'
                    status TEXT NOT NULL,     -- 'success' or 'failed'
                    message TEXT
                )
            ''')
            
            # Create indexes for better search performance
            logging.info("Creating indexes...")
            cursor.execute('CREATE INDEX idx_candidates_email ON candidates(email)')
            cursor.execute('CREATE INDEX idx_candidates_name ON candidates(name)')
            cursor.execute('CREATE INDEX idx_candidates_current_role ON candidates(current_role)')
            cursor.execute('CREATE INDEX idx_candidates_industry ON candidates(industry)')
            cursor.execute('CREATE INDEX idx_backup_log_time ON backup_log(backup_time)')
            cursor.execute('CREATE INDEX idx_sync_log_time ON sync_log(sync_time)')
            
            # Add triggers for updated_at timestamp
            logging.info("Creating triggers...")
            cursor.execute('''
                CREATE TRIGGER update_candidates_timestamp 
                AFTER UPDATE ON candidates
                FOR EACH ROW
                BEGIN
                    UPDATE candidates SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
                END
            ''')
            
            conn.commit()
            conn.close()
            
            logging.info("✅ Database created successfully!")
            return True
            
        except Exception as e:
            logging.error(f"❌ Error creating database: {str(e)}")
            return False
    
    def add_sample_data(self):
        """Add sample candidate data for testing"""
        try:
            logging.info("Adding sample data...")
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Sample candidates
            sample_candidates = [
                {
                    'name': 'John Smith',
                    'current_role': 'Senior Software Engineer',
                    'email': 'john.smith@example.com',
                    'phone': '+27123456789',
                    'notice_period': '4 weeks',
                    'current_salary': 'R850,000',
                    'industry': 'Technology',
                    'desired_salary': 'R950,000',
                    'highest_qualification': 'BSc Computer Science',
                    'experience': [
                        {
                            'position': 'Senior Software Engineer',
                            'company': 'TechCorp SA',
                            'years': '3 years',
                            'location': 'Cape Town, South Africa',
                            'employment_type': 'Full-time',
                            'responsibilities': [
                                'Lead development of microservices architecture using Python and Django',
                                'Mentor junior developers and conduct code reviews',
                                'Design and implement RESTful APIs for mobile applications',
                                'Optimize database queries and improve application performance'
                            ],
                            'achievements': [
                                'Reduced API response time by 40% through optimization',
                                'Led team of 5 developers in successful product launch'
                            ],
                            'technologies': ['Python', 'Django', 'PostgreSQL', 'Docker', 'AWS']
                        },
                        {
                            'position': 'Software Developer',
                            'company': 'StartupXYZ',
                            'years': '2 years',
                            'location': 'Johannesburg, South Africa',
                            'employment_type': 'Full-time',
                            'responsibilities': [
                                'Developed full-stack web applications using React and Node.js',
                                'Implemented automated testing and CI/CD pipelines',
                                'Collaborated with product team on feature specifications'
                            ],
                            'achievements': [
                                'Developed MVP that secured R5M funding',
                                'Implemented security features that prevented data breaches'
                            ],
                            'technologies': ['React', 'Node.js', 'MongoDB', 'Jest', 'Jenkins']
                        }
                    ],
                    'skills': [
                        {'skill': 'Python', 'proficiency': 5},
                        {'skill': 'JavaScript', 'proficiency': 4},
                        {'skill': 'React', 'proficiency': 4},
                        {'skill': 'Django', 'proficiency': 5},
                        {'skill': 'PostgreSQL', 'proficiency': 4},
                        {'skill': 'Docker', 'proficiency': 3},
                        {'skill': 'AWS', 'proficiency': 3}
                    ],
                    'qualifications': [
                        {
                            'qualification': 'BSc Computer Science',
                            'institution': 'University of Cape Town',
                            'year': '2018',
                            'grade': 'Cum Laude'
                        }
                    ],
                    'achievements': [
                        'AWS Certified Solutions Architect',
                        'Published research paper on microservices at local conference',
                        'Volunteer coding instructor for underprivileged youth'
                    ],
                    'special_skills': 'Machine Learning, DevOps, Technical Leadership'
                },
                {
                    'name': 'Sarah Johnson',
                    'current_role': 'Data Scientist',
                    'email': 'sarah.johnson@example.com',
                    'phone': '+27987654321',
                    'notice_period': '6 weeks',
                    'current_salary': 'R720,000',
                    'industry': 'Financial Services',
                    'desired_salary': 'R850,000',
                    'highest_qualification': 'MSc Data Science',
                    'experience': [
                        {
                            'position': 'Data Scientist',
                            'company': 'Banking Corp',
                            'years': '2.5 years',
                            'location': 'Sandton, South Africa',
                            'employment_type': 'Full-time',
                            'responsibilities': [
                                'Develop machine learning models for fraud detection',
                                'Analyze customer behavior patterns for marketing campaigns',
                                'Create data visualization dashboards for executive reporting',
                                'Collaborate with risk management team on predictive models'
                            ],
                            'achievements': [
                                'Improved fraud detection accuracy by 25%',
                                'Saved company R12M annually through better risk models'
                            ],
                            'technologies': ['Python', 'R', 'SQL', 'Tableau', 'TensorFlow', 'Apache Spark']
                        },
                        {
                            'position': 'Business Analyst',
                            'company': 'Consulting Firm',
                            'years': '2 years',
                            'location': 'Cape Town, South Africa',
                            'employment_type': 'Full-time',
                            'responsibilities': [
                                'Conducted market research and competitive analysis',
                                'Created financial models and forecasts for clients',
                                'Presented insights to C-level executives'
                            ],
                            'achievements': [
                                'Identified R50M cost-saving opportunity for major client',
                                'Led successful digital transformation project'
                            ],
                            'technologies': ['Excel', 'PowerBI', 'SQL', 'Python']
                        }
                    ],
                    'skills': [
                        {'skill': 'Python', 'proficiency': 5},
                        {'skill': 'R', 'proficiency': 4},
                        {'skill': 'SQL', 'proficiency': 5},
                        {'skill': 'Machine Learning', 'proficiency': 4},
                        {'skill': 'Tableau', 'proficiency': 4},
                        {'skill': 'TensorFlow', 'proficiency': 3},
                        {'skill': 'Statistics', 'proficiency': 5}
                    ],
                    'qualifications': [
                        {
                            'qualification': 'MSc Data Science',
                            'institution': 'University of Witwatersrand',
                            'year': '2020',
                            'grade': 'Distinction'
                        },
                        {
                            'qualification': 'BCom Mathematics',
                            'institution': 'Stellenbosch University',
                            'year': '2018',
                            'grade': 'Magna Cum Laude'
                        }
                    ],
                    'achievements': [
                        'Winner of National Data Science Competition 2021',
                        'Published 3 papers in peer-reviewed journals',
                        'Certified in Advanced Machine Learning (Coursera)'
                    ],
                    'special_skills': 'Deep Learning, Natural Language Processing, Statistical Analysis, Financial Modeling'
                }
            ]
            
            # Insert sample data
            for candidate in sample_candidates:
                cursor.execute("""
                    INSERT INTO candidates (
                        name, current_role, email, phone, notice_period, current_salary,
                        industry, desired_salary, highest_qualification, experience,
                        skills, qualifications, achievements, special_skills,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    candidate['name'],
                    candidate['current_role'],
                    candidate['email'],
                    candidate['phone'],
                    candidate['notice_period'],
                    candidate['current_salary'],
                    candidate['industry'],
                    candidate['desired_salary'],
                    candidate['highest_qualification'],
                    json.dumps(candidate['experience']),
                    json.dumps(candidate['skills']),
                    json.dumps(candidate['qualifications']),
                    json.dumps(candidate['achievements']),
                    candidate['special_skills'],
                    datetime.now(),
                    datetime.now()
                ))
            
            conn.commit()
            conn.close()
            
            logging.info("✅ Sample data added successfully!")
            return True
            
        except Exception as e:
            logging.error(f"❌ Error adding sample data: {str(e)}")
            return False
    
    def verify_database(self):
        """Verify database structure and data"""
        try:
            logging.info("Verifying database...")
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            expected_tables = ['candidates', 'backup_log', 'sync_log']
            
            for table in expected_tables:
                if table in tables:
                    logging.info(f"✅ Table '{table}' exists")
                else:
                    logging.error(f"❌ Table '{table}' missing")
                    return False
            
            # Check data
            cursor.execute("SELECT COUNT(*) FROM candidates")
            candidate_count = cursor.fetchone()[0]
            logging.info(f"📊 Total candidates: {candidate_count}")
            
            # Check indexes
            cursor.execute("PRAGMA index_list(candidates)")
            indexes = cursor.fetchall()
            logging.info(f"📊 Total indexes on candidates table: {len(indexes)}")
            
            # Test integrity
            cursor.execute("PRAGMA integrity_check")
            integrity_result = cursor.fetchone()[0]
            if integrity_result == 'ok':
                logging.info("✅ Database integrity check passed")
            else:
                logging.error(f"❌ Database integrity check failed: {integrity_result}")
                return False
            
            conn.close()
            
            logging.info("✅ Database verification completed successfully!")
            return True
            
        except Exception as e:
            logging.error(f"❌ Error verifying database: {str(e)}")
            return False
    
    def get_database_info(self):
        """Get database information"""
        try:
            if not os.path.exists(self.db_path):
                logging.error("❌ Database file does not exist")
                return
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Database file info
            file_size = os.path.getsize(self.db_path)
            logging.info(f"📁 Database file: {self.db_path}")
            logging.info(f"📏 File size: {file_size / 1024:.2f} KB")
            
            # Table information
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            logging.info(f"📊 Tables: {len(tables)}")
            
            for table_name, in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                logging.info(f"  - {table_name}: {count} records")
            
            # Schema information
            logging.info("\n📋 Candidates table schema:")
            cursor.execute("PRAGMA table_info(candidates)")
            columns = cursor.fetchall()
            for col_info in columns:
                logging.info(f"  - {col_info[1]} ({col_info[2]})")
            
            conn.close()
            
        except Exception as e:
            logging.error(f"❌ Error getting database info: {str(e)}")

def main():
    """Main function to initialize database"""
    print("🚀 HR Candidate Management Tool - Database Initializer")
    print("=" * 60)
    
    # You can specify a custom path here if needed
    # For example: db_init = DatabaseInitializer('/path/to/your/database.db')
    db_init = DatabaseInitializer()
    
    try:
        # Create database
        if not db_init.create_database():
            print("❌ Failed to create database")
            return False
        
        # Add sample data (optional - comment out if you don't want sample data)
        print("\n📝 Would you like to add sample data? (y/n): ", end="")
        add_sample = input().lower().strip()
        
        if add_sample in ['y', 'yes']:
            if not db_init.add_sample_data():
                print("⚠️  Failed to add sample data, but database is still usable")
        
        # Verify database
        if not db_init.verify_database():
            print("❌ Database verification failed")
            return False
        
        # Show database info
        print("\n" + "=" * 60)
        print("📊 Database Information:")
        print("-" * 60)
        db_init.get_database_info()
        
        print("\n" + "=" * 60)
        print("✅ Database initialization completed successfully!")
        print("🎉 Your HR Candidate Management database is ready to use!")
        print("\n💡 To use this database with your application:")
        print(f"   Set LOCAL_DB_PATH environment variable to: {db_init.db_path}")
        print("   Or update your config.py file with the correct path.")
        
        return True
        
    except Exception as e:
        logging.error(f"❌ Fatal error during initialization: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)