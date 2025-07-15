# MyCG AI Service

🤖 AI-powered document processing and chatbot service for MyCG accounting platform.

## Features

### 🔍 Document Processing
- **Multi-OCR Support**: Tesseract, EasyOCR, Google Vision
- **Smart Document Detection**: Auto-identify bank statements, invoices, notices
- **AI Enhancement**: Transaction categorization and GST analysis

### 🤖 AI Services
- **GST Query Chat**: Answer tax and compliance questions
- **Notice Analysis**: Government notice analysis with response suggestions
- **Recurring Detection**: AI-powered recurring transaction suggestions

### 📱 WhatsApp Integration
- **Smart Bot**: Handle commands, queries, and document uploads
- **Real-time Processing**: Live updates on document processing
- **Rich Notifications**: GST reminders and compliance alerts

## Quick Start

### Prerequisites
- Python 3.11+
- Redis
- Tesseract OCR
- Docker (optional)

### Installation

1. **Clone and setup**
   ```bash
   git clone <repo-url>
   cd mycg-ai
   chmod +x scripts/*.sh
   ./scripts/setup.sh
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Run development server**
   ```bash
   python main.py
   ```

### Docker Deployment

```bash
# Production deployment
./scripts/deploy.sh

# Or manually
docker-compose up -d
```

## API Documentation

### Document Processing
```bash
# Upload and process document
curl -X POST http://localhost:8001/api/v1/document/process \
  -F "file=@statement.pdf" \
  -F "user_id=user123"

# Check processing status
curl http://localhost:8001/api/v1/document/status/{processing_id}
```

### AI Services
```bash
# Ask GST question
curl -X POST http://localhost:8001/api/v1/ai/query \
  -H "Content-Type: application/json" \
  -d '{"query":"What is GST rate for software?","user_id":"user123"}'

# Analyze government notice
curl -X POST http://localhost:8001/api/v1/ai/analyze-notice \
  -H "Content-Type: application/json" \
  -d '{"notice_text":"...","notice_type":"gst","user_id":"user123"}'
```

### WhatsApp Webhook
```bash
# Setup webhook endpoint
POST /api/v1/whatsapp/webhook
```

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   WhatsApp      │    │   FastAPI       │    │   Node.js       │
│   Messages      │───▶│   AI Service    │───▶│   Backend       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   AI Services   │
                       │  • OpenAI       │
                       │  • OCR Engines  │
                       │  • Document AI  │
                       └─────────────────┘
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for AI services | Yes |
| `TWILIO_ACCOUNT_SID` | Twilio SID for WhatsApp | No |
| `NODE_BACKEND_URL` | Node.js backend URL | Yes |
| `REDIS_URL` | Redis connection URL | Yes |

### AI Model Configuration
- **Default Model**: gpt-3.5-turbo
- **Max Tokens**: 1000
- **Temperature**: 0.3

## Monitoring

### Health Checks
```bash
# Basic health
curl http://localhost:8001/api/v1/health

# Detailed health with dependencies
curl http://localhost:8001/api/v1/health/detailed

# AI services status
curl http://localhost:8001/api/v1/health/ai-services
```

### Logs
```bash
# View logs
docker-compose logs -f mycg-ai

# Log files (production)
tail -f logs/app.log
```

## Security

### Rate Limiting
- API: 10 req/sec
- WhatsApp: 50 req/sec
- Document Upload: 10 req/sec

### File Validation
- Max size: 10MB
- Allowed types: PDF, JPEG, PNG
- Virus scanning (TODO)

## Backup & Restore

```bash
# Create backup
./scripts/backup.sh

# Restore from backup
./scripts/restore.sh backups/20241201_143022
```

## Development

### Project Structure
```
mycg_ai/
├── main.py                           # Main FastAPI application entry point
├── requirements.txt                  # Python dependencies
├── .env                             # Environment variables
├── .gitignore                       # Git ignore file
├── Dockerfile                       # Docker container configuration
├── docker-compose.yml               # Multi-container deployment
├── docker-compose.dev.yml           # Multi-container deployment
├── README.md                        # Project documentation
│
├── config/                          # Configuration modules
│   ├── __init__.py
│   └── settings.py                  # Pydantic settings management
│
├── models/                          # Pydantic data models
│   ├── __init__.py
│   ├── ai_models.py                 # AI service request/response models
│   └── document_models.py           # Document processing models
│
├── services/                        # Core business logic services
│   ├── __init__.py
│   ├── ocr_service.py              # OCR processing (Tesseract, EasyOCR, Google Vision)
│   ├── ai_service.py               # OpenAI integration & AI logic
│   ├── document_processor.py       # Document parsing & analysis
│   └── whatsapp_ai.py              # WhatsApp message processing
│
├── api/                            # API route handlers
│   ├── __init__.py
│   └── v1/                         # API version 1
│       ├── __init__.py
│       ├── document.py             # Document processing endpoints
│       ├── ai_chat.py              # AI chat & query endpoints
│       ├── whatsapp.py             # WhatsApp webhook & messaging
│       └── health.py               # Health check endpoints
│
├── core/                           # Core application components
│   ├── __init__.py
│   ├── exceptions.py               # Custom exception classes
│   └── middleware.py               # FastAPI middleware (CORS, timing, logging)
│
├── utils/                          # Utility functions
│   ├── __init__.py
│   ├── file_handler.py             # File upload/download & S3 integration
│   ├── validators.py               # Input validation utilities
│   └── response_models.py          # Common response models
│
├── temp_uploads/                   # Temporary file storage (auto-created)
│   └── .gitkeep
│
├── logs/                           # Application logs (auto-created)
│   └── .gitkeep
│
├── tests/                          # Test files
│   ├── __init__.py
│   ├── test_api/
│   │   ├── __init__.py
│   │   ├── test_document.py
│   │   ├── test_ai_chat.py
│   │   └── test_whatsapp.py
│   ├── test_services/
│   │   ├── __init__.py
│   │   ├── test_ocr_service.py
│   │   ├── test_ai_service.py
│   │   └── test_document_processor.py
│   └── test_utils/
│       ├── __init__.py
│       └── test_file_handler.py
│
├── scripts/                        # Deployment & utility scripts
│   ├── deploy.sh                   # Deployment script
│   ├── setup.sh                    # Environment setup
│   └── backup.sh                   # Backup script
│
├── docs/                           # Documentation
│   ├── api.md                      # API documentation
│   ├── deployment.md               # Deployment guide
│   └── integration.md              # Node.js integration guide
│
└── nginx/                          # Nginx configuration (for production)
    ├── nginx.conf                  # Main nginx config
    └── ssl/                        # SSL certificates
        ├── cert.pem
        └── key.pem
```

### Running Tests
```bash
pytest tests/
```

### Code Quality
```bash
# Format code
black .

# Lint code
flake8 .

# Type checking
mypy .
```

## Contributing

1. Fork the repository
2. Create feature branch
3. Add tests
4. Submit pull request

## Support

- 📧 Email: support@mycg.app
- 📚 Docs: https://docs.mycg.app
- 🐛 Issues: GitHub Issues