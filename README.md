# Agastya Connect: AI-Powered Instructor Training Platform

![Agastya International Foundation](https://img.shields.io/badge/Agastya-Training_Platform-orange)
![Status](https://img.shields.io/badge/Status-Production-green)
![Frontend](https://img.shields.io/badge/Frontend-Streamlit-red)
![Backend](https://img.shields.io/badge/Backend-FastAPI-blue)
![AWS](https://img.shields.io/badge/Cloud-AWS-orange)
![RAG](https://img.shields.io/badge/AI-RAG_Architecture-green)

## Table of Contents
- [Introduction](#introduction)
- [Features](#features)
- [Technical Architecture](#technical-architecture)
- [Live Environment](#live-environment)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Installation & Setup](#installation--setup)
- [Configuration](#configuration)
- [Deployment](#deployment)
- [Usage Guide](#usage-guide)
- [Security](#security)
- [Support](#support)

## Introduction

Agastya Connect is an innovative AI-powered training platform developed for Agastya International Foundation, recognized as India's largest "Creativity Laboratory." The platform empowers instructors to enhance their teaching skills through realistic conversations with AI-simulated students, providing a safe environment to practice educational techniques before entering real classrooms.

Our platform leverages advanced Retrieval-Augmented Generation (RAG) technology to create authentic student personas with diverse backgrounds, learning styles, and personalities. Each AI student responds contextually based on detailed background information, creating meaningful and realistic training scenarios for instructors.

### Key Benefits
- **Risk-free practice environment** for developing teaching strategies
- **Personalized AI students** with unique characteristics and backgrounds
- **Real-time feedback** through natural conversations
- **Multilingual support** including Kannada language capabilities
- **Comprehensive session tracking** for progress monitoring

## Features

### Core Functionality
- **Interactive Chat Interface**: Intuitive design for natural conversation flow between instructors and AI students
- **Diverse Student Profiles**: Multiple AI-simulated students with unique personalities, academic backgrounds, and learning preferences
- **Context-Aware Responses**: AI maintains conversation continuity and responds based on each student's documented characteristics
- **Smart Question Suggestions**: AI-generated follow-up questions to guide meaningful educational conversations
- **Multilingual Support**: Automatic Kannada language detection and translation for regional accessibility
- **Session Management**: Start new conversations, pause ongoing sessions, and resume previous chats seamlessly
- **Progress Tracking**: All conversations are securely stored for review and improvement analysis

### Technical Capabilities
- **RAG Architecture**: Knowledge-enhanced responses grounded in factual student information
- **Secure Authentication**: Google OAuth integration with email-based access control
- **Cloud-Native Design**: Fully deployed on AWS with auto-scaling capabilities
- **Real-time Processing**: Optimized response generation with intelligent retrieval algorithms
- **Comprehensive Logging**: Detailed activity tracking for monitoring and troubleshooting
- **Concurrent Sessions**: Support for multiple active chat sessions with different students

## Technical Architecture

Agastya Connect implements a modern, scalable architecture designed for reliability and performance:

```
┌─────────────────┐     ┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   CloudFront    │────▶│ Route 53 DNS    │────▶│ Application      │────▶│    EC2          │
│  (Static Pages) │     │                 │     │ Load Balancer    │     │  Instance       │
└─────────────────┘     └─────────────────┘     └──────────────────┘     └─────────────────┘
                                                           │                         │
                                                           ▼                         ▼
┌─────────────────┐     ┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Lambda        │◀────│   DynamoDB      │◀────│   Streamlit      │     │   FastAPI       │
│  Functions      │     │   Tables        │     │   Frontend       │     │   Backend       │
└─────────────────┘     └─────────────────┘     └──────────────────┘     └─────────────────┘
         │                                                                           │
         ▼                                                                           ▼
┌─────────────────┐                                                       ┌─────────────────┐
│   S3 Bucket     │                                                       │   Google AI     │
│  (Storage)      │                                                       │   Services      │
└─────────────────┘                                                       └─────────────────┘
```

### Frontend (Streamlit)
- **Authentication**: Secure Google OAuth integration
- **Session Management**: Persistent state across page refreshes
- **Responsive UI**: Optimized for desktop and tablet devices
- **Real-time Updates**: Dynamic content rendering during conversations

### Backend (FastAPI)
- **RESTful API**: Well-documented endpoints for all operations
- **Security Layer**: API key authentication for all requests
- **RAG Pipeline**: Advanced retrieval and generation system
- **Translation Service**: Integrated Google Cloud Translation

### Serverless Components (AWS Lambda)
- **Session Management**: Handles chat session lifecycle operations
- **Data Export**: Automated chat transcript generation
- **Profile Management**: Student profile retrieval and caching
- **History Retrieval**: Efficient chat history access

### Infrastructure
- **CloudFront**: CDN for static content delivery (privacy policy, terms of service)
- **Route 53**: DNS management with health checks
- **Application Load Balancer**: HTTPS termination and traffic distribution
- **EC2**: Hosts containerized application services
- **DynamoDB**: NoSQL database for all application data
- **S3**: Object storage for vectorstores and chat exports
- **GitHub Actions**: Automated CI/CD pipeline

## Live Environment

**Production URL**: [https://agastyaconnect.com](https://agastyaconnect.com)

- **Protocol**: HTTPS only (automatic HTTP redirection)
- **Authentication**: Google account required with email verification
- **Static Pages**: Privacy policy and terms of service via CloudFront
- **API Endpoints**: Secured with API key authentication
- **Monitoring**: 24/7 uptime monitoring with alerts

## Technology Stack

### Frontend
- **Framework**: Streamlit 1.32+
- **Authentication**: Google OAuth 2.0 via Authlib
- **Language**: Python 3.9+
- **Async Support**: AsyncIO for concurrent operations

### Backend
- **Framework**: FastAPI 0.104+
- **Server**: Uvicorn ASGI
- **Validation**: Pydantic v2
- **Language**: Python 3.9+

### AI & Machine Learning
- **LLM Framework**: LangChain with modular architecture
- **Vector Store**: ChromaDB for embeddings
- **LLM Provider**: Google Generative AI (Gemini)
- **Translation**: Google Cloud Translation API
- **Document Processing**: Docx2txt for content extraction

### Cloud Infrastructure
- **Compute**: AWS EC2 (t3.medium or larger)
- **CDN**: CloudFront for static content
- **DNS**: Route 53 with health checks
- **Load Balancing**: Application Load Balancer
- **Database**: DynamoDB (3 tables)
- **Storage**: S3 for vectorstores and exports
- **Serverless**: Lambda functions for async operations
- **Monitoring**: CloudWatch logs and metrics

### Development & Operations
- **Version Control**: Git with GitHub
- **CI/CD**: GitHub Actions
- **Package Management**: pip with requirements.txt
- **Environment Management**: python-dotenv
- **Logging**: Python logging with rotation

## Project Structure

```
agastya-connect/
├── .github/
│   └── workflows/
│       └── deploy.yml         # CI/CD pipeline
├── .streamlit/
│   ├── config.toml           # UI configuration
│   └── secrets.toml          # Frontend secrets (gitignored)
├── api/
│   └── models.py             # Pydantic models
├── config/                   # Configuration modules
│   ├── backend/
│   ├── frontend/
│   └── shared/
├── pages/                    # Streamlit pages
│   ├── chat.py              # Chat interface
│   ├── home.py              # Dashboard
│   ├── loading.py           # Loading screens
│   ├── login.py             # Authentication
│   └── students.py          # Student selection
├── prompts/                 # AI prompt templates
│   ├── backend.py
│   └── frontend.py
├── services/
│   ├── ec2-linux/           # Systemd service files
│   └── lambda/              # Lambda function code
├── static/                  # Static assets
│   ├── privacy.html
│   ├── terms-of-service.html
│   └── images/
├── utils/                   # Utility modules
│   ├── backend/
│   ├── frontend/
│   └── shared/
├── .env                     # Environment variables (gitignored)
├── .gitignore
├── app.py                   # Streamlit entry point
├── requirements.txt         # Python dependencies
├── server.py               # FastAPI entry point
└── setup_db.py             # Database initialization
```

## Installation & Setup

### Prerequisites
- Python 3.9 or higher
- AWS CLI configured with appropriate credentials
- Google Cloud account with Translation API enabled
- Google OAuth 2.0 client credentials

### Local Development Setup

1. **Clone the Repository**
   ```bash
git clone https://github.com/projectagastya/agastya-connect.git
cd agastya-connect
```

2. **Create Virtual Environment**
   ```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install Dependencies**
   ```bash
pip install -r requirements.txt
```

4. **Create Required Directories**
   ```bash
mkdir -p logs/backend_logs logs/frontend_logs
mkdir -p local-student-vectorstores
```

5. **Configure Environment Variables**
   Create `.env` file with required variables (see Configuration section)

6. **Configure Streamlit Secrets**
   Create `.streamlit/secrets.toml` with frontend configuration

7. **Initialize Database**
   ```bash
   python setup_db.py
   ```

8. **Start Services**
   ```bash
   # Terminal 1 - Backend
   uvicorn server:app --reload --host 0.0.0.0 --port 8000
   
   # Terminal 2 - Frontend
   streamlit run app.py
   ```

9. **Access Application**
   Navigate to `http://localhost:8501`

## Configuration

### Environment Variables (.env)

```bash
# AWS Configuration
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_DEFAULT_REGION=us-east-1
AWS_REGION=us-east-1
MAIN_S3_BUCKET_NAME=your-s3-bucket

# API Configuration
BACKEND_API_KEY=your-secure-api-key

# DynamoDB Tables
DYNAMODB_STUDENT_TABLE_NAME=agastya-students
DYNAMODB_CHAT_SESSIONS_TABLE_NAME=agastya-chat-sessions
DYNAMODB_CHAT_MESSAGES_TABLE_NAME=agastya-chat-messages

# Google AI Configuration
GOOGLE_API_KEY=your-google-api-key
DOCUMENT_EMBEDDING_MODEL_ID=models/embedding-001
RESPONSE_GENERATION_MODEL_ID=gemini-pro
RESPONSE_GENERATION_MODEL_TEMPERATURE=0.7
RESPONSE_GENERATION_MODEL_MAX_TOKENS=512
RAG_MAX_DOC_RETRIEVE=5

# Google Cloud Translation
GCP_TYPE=service_account
GCP_PROJECT_ID=your-project-id
GCP_PRIVATE_KEY_ID=your-key-id
GCP_PRIVATE_KEY=your-private-key
GCP_CLIENT_EMAIL=your-service-account@project.iam.gserviceaccount.com
GCP_CLIENT_ID=your-client-id
GCP_AUTH_URI=https://accounts.google.com/o/oauth2/auth
GCP_TOKEN_URI=https://oauth2.googleapis.com/token
GCP_AUTH_PROVIDER_X509_CERT_URL=https://www.googleapis.com/oauth2/v1/certs
GCP_CLIENT_X509_CERT_URL=your-cert-url
GCP_UNIVERSE_DOMAIN=googleapis.com

# Application Paths
LOGS_FOLDER_PATH=logs
LOCAL_VECTORSTORES_DIRECTORY=local-student-vectorstores
STUDENT_METADATA_FILE_NAME=students.json
STUDENT_METADATA_FOLDER_PATH=metadata/students
STUDENT_VECTORSTORE_FOLDER_PATH=vectorstores
CHAT_TRANSCRIPTS_FOLDER_PATH=chat-transcripts

# Application Configuration
TIMEZONE=UTC
APP_LOGO_URL=https://{domain}/static/logo.png
DEFAULT_PROFILE_IMAGE_URL=https://{domain}/static/silhouette.png
STUDENT_IMAGE_URL=https://{domain}/static/students/{student_name}.png

# Frontend LLM Configuration
QUESTIONS_GENERATION_MODEL_ID=gemini-pro
QUESTIONS_GENERATION_MODEL_TEMPERATURE=0.8
QUESTIONS_GENERATION_MODEL_MAX_TOKENS=256
```

### Streamlit Configuration (.streamlit/secrets.toml)

```toml
[auth]
redirect_uri = "https://agastyaconnect.com/app"
cookie_secret = "your-cookie-secret"
client_id = "your-google-oauth-client-id"
client_secret = "your-google-oauth-client-secret"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"

[BACKEND]
API_URL = "http://localhost:8000"
API_KEY = "your-backend-api-key"

[SERVERLESS]
API_URL = "https://api.agastyaconnect.com"

[SECURITY]
ALLOWED_EMAILS = ["instructor1@agastya.org", "instructor2@agastya.org"]

[LLM]
API_KEY = "your-google-api-key"
QUESTIONS_GENERATION_MODEL_ID = "gemini-pro"
QUESTIONS_GENERATION_MODEL_TEMPERATURE = 0.8
QUESTIONS_GENERATION_MODEL_MAX_TOKENS = 256

[LOGS]
FOLDER_PATH = "./logs/frontend_logs"
```

## Deployment

### Infrastructure Components

1. **CloudFront Distribution**
   - Origin: S3 bucket for static content
   - Behaviors: Configured for privacy.html and terms-of-service.html
   - Caching: Optimized TTL settings

2. **Route 53 Configuration**
   - Hosted Zone: agastyaconnect.com
   - A Record: Alias to Application Load Balancer
   - Health Checks: Configured for high availability

3. **Application Load Balancer**
   - Listeners: HTTPS (443) with SSL certificate
   - Target Group: EC2 instance on port 8000
   - Health Check: /health endpoint

4. **EC2 Instance**
   - OS: Ubuntu 22.04 LTS
   - Instance Type: t3.medium or larger
   - Security Group: Restricted inbound from ALB only
   - Services: FastAPI (port 8000) and Streamlit (port 8501)

5. **Lambda Functions**
   - get-student-profiles: Retrieves student data
   - start-chat: Initializes chat sessions
   - get-chat-history: Fetches conversation history
   - end-all-chats: Closes active sessions
   - export-chat: Generates Excel transcripts

6. **DynamoDB Tables**
   - agastya-students: Student profile data
   - agastya-chat-sessions: Session metadata
   - agastya-chat-messages: Conversation history

7. **S3 Bucket**
   - /vectorstores: Preprocessed student data
   - /chat-transcripts: Exported conversations
   - /static: Static website content

### Deployment Process

The application uses GitHub Actions for continuous deployment:

1. **Trigger**: Push to main branch
2. **Process**:
   - SSH connection to EC2 instance
   - Git pull latest changes
   - Update dependencies if requirements.txt changed
   - Update systemd service files
   - Restart FastAPI and Streamlit services
3. **Validation**: Health check verification

### Service Configuration

Create systemd service files on EC2:

**FastAPI Service** (`/etc/systemd/system/fastapi.service`):
```ini
[Unit]
Description=Agastya Backend FastAPI Service
After=network.target

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/agastya-connect
Environment="PATH=/home/ubuntu/agastya-connect/venv/bin"
ExecStart=/home/ubuntu/agastya-connect/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

**Streamlit Service** (`/etc/systemd/system/streamlit.service`):
```ini
[Unit]
Description=Agastya Frontend Streamlit Service
After=network.target

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/agastya-connect
Environment="PATH=/home/ubuntu/agastya-connect/venv/bin"
ExecStart=/home/ubuntu/agastya-connect/venv/bin/streamlit run app.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start services:
```bash
sudo systemctl daemon-reload
sudo systemctl enable fastapi streamlit
sudo systemctl start fastapi streamlit
```

## Usage Guide

### For Instructors

1. **Getting Started**
   - Visit https://agastyaconnect.com
   - Click "Sign in with Google"
   - Use your authorized email address

2. **Selecting a Student**
   - Browse available student profiles
   - Review student details (age, location, background)
   - Click "Start Chat" to begin conversation

3. **Engaging in Conversation**
   - Type questions in the chat interface
   - Use suggested questions for guidance
   - Switch between English and Kannada as needed
   - Practice various teaching scenarios

4. **Managing Sessions**
   - Resume previous conversations
   - Start new sessions with different students
   - Review chat history
   - Export transcripts for analysis

### For Administrators

1. **User Management**
   - Add authorized emails in `.streamlit/secrets.toml`
   - Monitor active sessions via CloudWatch
   - Review usage metrics in DynamoDB

2. **Content Management**
   - Update student profiles in S3
   - Modify vectorstores for new content
   - Adjust AI prompts in configuration

3. **System Monitoring**
   - Check application logs in CloudWatch
   - Monitor Lambda function performance
   - Review DynamoDB capacity metrics
   - Track S3 storage usage

## Security

### Implementation Details

- **Authentication**: Google OAuth 2.0 with email allowlist
- **API Security**: API key required for all backend endpoints
- **Data Encryption**: TLS 1.3 for all communications
- **Access Control**: IAM roles with least privilege principle
- **Input Validation**: Pydantic models for all API requests
- **Session Management**: Secure session tokens with expiration
- **Error Handling**: Sanitized error messages for users
- **Logging**: Comprehensive audit trails without sensitive data

### Best Practices

- Regular security updates for all dependencies
- Rotating API keys and secrets periodically
- Monitoring for unusual access patterns
- Regular backups of critical data
- Incident response plan documentation

## Support

### Contact Information
- **Email**: info@agastya.org
- **Phone**: +91-8041124132
- **Website**: [https://www.agastya.org](https://www.agastya.org)
- **Technical Support**: projectagastya2024@gmail.com

### Resources
- **Documentation**: Available in project repository
- **Issue Tracking**: Contact technical support
- **Feature Requests**: Email project team
- **Security Issues**: Report to projectagastya2024@gmail.com

---

**© 2025 Agastya International Foundation. All rights reserved.**

*This platform is proprietary software developed exclusively for Agastya International Foundation's instructor training program. Unauthorized access, use, or distribution is strictly prohibited.*