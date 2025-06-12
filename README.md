# HR Candidate Management Tool

A comprehensive web application for HR recruiters to manage candidate CVs using AI-powered data extraction and intelligent search capabilities.

## 🌟 Features

- **AI-Powered CV Processing**: Extract structured data from PDF CVs using Azure OpenAI GPT-4o-mini
- **Intelligent Search**: Find candidates using manual criteria or job description matching
- **Automatic Backups**: SQLite database with Azure Blob Storage backups
- **Dark Theme UI**: Modern, responsive Streamlit interface
- **Candidate Ranking**: Score and rank candidates based on job requirements
- **Data Validation**: Comprehensive data validation and cleaning
- **Real-time Processing**: Instant CV processing and candidate search

## 🔧 Technology Stack

- **Frontend**: Streamlit with custom CSS (Dark Theme)
- **Backend**: Python 3.11
- **Database**: SQLite with Azure Blob Storage backups
- **AI/ML**: Azure OpenAI GPT-4o-mini
- **PDF Processing**: PyMuPDF
- **Cloud**: Azure Web Apps, Azure Container Registry, Azure Blob Storage
- **CI/CD**: GitHub Actions
- **Containerization**: Docker

## 📋 Prerequisites

- Azure subscription
- GitHub account
- Azure CLI installed
- Docker (for local development)
- Python 3.11+ (for local development)

## 🚀 Quick Start

### Local Development

1. **Clone the repository**
```bash
git clone https://github.com/YOUR_USERNAME/hr-candidate-tool.git
cd hr-candidate-tool
```

2. **Set up environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your Azure credentials
```

4. **Run the application**
```bash
streamlit run app.py
```

5. **Access the application**
Open your browser to `http://localhost:8501`

### Production Deployment

Follow the complete [Setup Guide](SETUP.md) for production deployment to Azure.

## 📁 Project Structure

```
hr-candidate-tool/
├── app.py                    # Main Streamlit application
├── database.py              # Database management and backup operations
├── cv_processor.py          # CV processing and OpenAI integration
├── config.py               # Configuration management
├── utils.py                # Utility functions and validation
├── requirements.txt        # Python dependencies
├── Dockerfile              # Container configuration
├── .env.example           # Environment variables template
├── .github/
│   └── workflows/
│       └── deploy.yml      # GitHub Actions CI/CD pipeline
├── tests/                 # Unit tests (future implementation)
├── docs/                  # Additional documentation
│   ├── SETUP.md          # Complete setup guide
│   ├── API.md            # API documentation
│   └── TROUBLESHOOTING.md # Common issues and solutions
└── README.md             # This file
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `AZURE_STORAGE_CONNECTION_STRING` | Azure Blob Storage connection | Yes | - |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI service endpoint | Yes | - |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key | Yes | - |
| `AZURE_OPENAI_API_VERSION` | OpenAI API version | No | `2024-02-15-preview` |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | OpenAI model deployment name | No | `gpt-4o-mini` |
| `DB_PATH` | SQLite database file path | No | `/home/data/hr_candidates.db` |
| `BACKUP_CONTAINER` | Blob storage container name | No | `hr-backups` |
| `AUTO_BACKUP_ENABLED` | Enable automatic backups | No | `True` |
| `BACKUP_RETENTION_DAYS` | Days to retain backups | No | `30` |
| `MAX_FILE_SIZE_MB` | Maximum CV file size in MB | No | `10` |
| `MAX_SEARCH_RESULTS` | Maximum search results to return | No | `100` |
| `LOG_LEVEL` | Application log level | No | `INFO` |

### Database Schema

The application uses SQLite with the following main table:

```sql
candidates (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    current_role TEXT,
    email TEXT UNIQUE,
    phone TEXT,
    notice_period TEXT,
    current_salary TEXT,
    industry TEXT,
    desired_salary TEXT,
    highest_qualification TEXT,
    experience TEXT,        -- JSON array
    skills TEXT,           -- JSON array
    qualifications TEXT,   -- JSON array
    achievements TEXT,     -- JSON array
    special_skills TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)
```

## 📊 Data Extraction

### CV Data Fields

The application extracts the following information from PDF CVs:

- **Personal Information**: Name, email, phone number
- **Professional**: Current role, industry, notice period, salary information
- **Experience**: Previous positions with responsibilities and duration
- **Skills**: Technical and soft skills with proficiency levels (1-5)
- **Education**: Qualifications, institutions, years, grades
- **Achievements**: Professional accomplishments
- **Special Skills**: Certifications and specialized abilities

### Job Matching

When using job description matching, the system extracts:

- Required skills and experience levels
- Educational requirements
- Industry preferences
- Minimum experience years
- Job responsibilities

## 🔍 Search Capabilities

### Manual Search
- Filter by any combination of fields
- Partial text matching
- Experience years filtering
- Skills-based search

### AI-Powered Job Matching
- Paste job description for automatic requirement extraction
- Intelligent candidate scoring and ranking
- Match percentage calculation based on:
  - Skills alignment (40% weight)
  - Experience level (30% weight)
  - Education match (20% weight)
  - Industry relevance (10% weight)

## 💾 Backup Strategy

### Automatic Backups
- **Frequency**: After every 5 candidate additions or hourly
- **Storage**: Azure Blob Storage
- **Retention**: Configurable (default 30 days)
- **Format**: Full SQLite database file

### Manual Backups
- On-demand backup creation through dashboard
- Immediate backup to blob storage
- Backup verification and status tracking

### Disaster Recovery
- Automatic restore from latest backup on startup
- Manual restore from specific backup points
- Backup integrity verification

## 🧪 Testing

### Unit Tests
```bash
# Run unit tests (when implemented)
python -m pytest tests/ -v
```

### Manual Testing Checklist

**CV Processing:**
- [ ] Upload PDF CV successfully
- [ ] Text extraction works correctly
- [ ] AI data extraction populates form
- [ ] Form validation works
- [ ] Data saves to database

**Search Functionality:**
- [ ] Manual search returns results
- [ ] Job description search works
- [ ] Candidate ranking is logical
- [ ] Results display correctly

**Backup Operations:**
- [ ] Manual backup creates file in blob storage
- [ ] Automatic backup triggers work
- [ ] Restore from backup functions
- [ ] Old backups are cleaned up

## 📈 Performance Considerations

### Optimization Tips

1. **Database**: 
   - Regular backup cleanup
   - Index optimization for search queries
   - Connection pooling for high load

2. **AI Processing**:
   - Implement request caching
   - Batch processing for multiple CVs
   - Fallback handling for API failures

3. **File Processing**:
   - File size limits
   - Virus scanning for uploads
   - Temporary file cleanup

4. **UI/UX**:
   - Progress indicators for long operations
   - Pagination for large result sets
   - Responsive design for mobile

## 🛡️ Security

### Data Protection
- Environment variables for sensitive data
- No hardcoded credentials
- Secure file upload validation
- SQL injection prevention

### Access Control
- Consider implementing authentication
- Role-based access control
- Audit logging for data changes

### Azure Security
- Use managed identities where possible
- Enable Azure Security Center recommendations
- Regular security updates

## 🚀 Deployment

### GitHub Actions CI/CD

The deployment pipeline includes:

1. **Build Phase**:
   - Code checkout
   - Docker image build
   - Security scanning
   - Unit tests execution

2. **Deploy Phase**:
   - Push to Azure Container Registry
   - Deploy to Azure Web App
   - Configuration update
   - Health checks

3. **Post-Deploy**:
   - Backup verification
   - Performance testing
   - Notification sending

### Manual Deployment

```bash
# Build and push manually
docker build -t hr-candidate-app .
docker tag hr-candidate-app:latest YOUR_ACR.azurecr.io/hr-candidate-app:latest
docker push YOUR_ACR.azurecr.io/hr-candidate-app:latest
```

## 🐛 Troubleshooting

### Common Issues

**Application won't start:**
- Check environment variables are set
- Verify Azure resource connectivity
- Review application logs

**CV processing fails:**
- Verify OpenAI API quota and limits
- Check PDF file format and size
- Review API endpoint configuration

**Search returns no results:**
- Check database has candidate data
- Verify search criteria format
- Review database connection

**Backup failures:**
- Confirm blob storage permissions
- Check connection string format
- Verify container exists

For detailed troubleshooting, see [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md).

## 📖 API Documentation

For detailed API information, see [API.md](docs/API.md).

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### Development Guidelines

- Follow PEP 8 style guidelines
- Add docstrings to all functions
- Include type hints where possible
- Update documentation for new features
- Test thoroughly before submitting

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Support

For support and questions:

1. Check the [troubleshooting guide](docs/TROUBLESHOOTING.md)
2. Review existing GitHub issues
3. Create a new issue with detailed information
4. Contact the development team

## 🗺️ Roadmap

### Version 1.1 (Planned)
- [ ] User authentication and authorization
- [ ] Candidate interview scheduling
- [ ] Email integration for candidate communication
- [ ] Advanced analytics and reporting
- [ ] Bulk CV processing
- [ ] Integration with popular HR systems

### Version 1.2 (Future)
- [ ] Machine learning model for better candidate matching
- [ ] Video interview analysis
- [ ] Integration with LinkedIn and job boards
- [ ] Mobile application
- [ ] Advanced workflow automation

## 📊 Metrics and Analytics

The application tracks:
- CV processing success rates
- Search query patterns
- User engagement metrics
- System performance data
- Backup success rates

Access metrics through the dashboard or Azure Application Insights.

## 🙏 Acknowledgments

- Azure OpenAI team for the powerful GPT-4o-mini model
- Streamlit community for the excellent framework
- PyMuPDF developers for PDF processing capabilities
- Open source community for various supporting libraries

---

**Built with ❤️ for HR professionals to streamline candidate management**
