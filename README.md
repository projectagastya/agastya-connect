# Agastya AI: Instructor Training Platform

![Agastya International Foundation](https://img.shields.io/badge/Agastya-Training_Platform-orange)
![Status](https://img.shields.io/badge/Status-Production-green)
![Frontend](https://img.shields.io/badge/Frontend-Streamlit-red)
![Backend](https://img.shields.io/badge/Backend-FastAPI-blue)
![AWS](https://img.shields.io/badge/Cloud-AWS-orange)
![RAG](https://img.shields.io/badge/AI-RAG_Architecture-green)

## 📚 Table of Contents
- [Introduction](#-introduction)
- [Features](#-features)
- [Technical Architecture](#-technical-architecture)
- [Live Environment](#-live-environment)
- [Technology Stack](#-technology-stack)
- [Project Structure](#-project-structure)
- [Installation & Setup (Local)](#-installation--setup-local)
- [Configuration](#-configuration)
- [Deployment (AWS)](#-deployment-aws)
- [Usage Guide](#-usage-guide)
- [Security Considerations](#-security-considerations)
- [Contributing](#-contributing)
- [Contact Information](#-contact-information)

## 🌟 Introduction

Agastya AI is an innovative training platform developed for the Agastya International Foundation, India's "largest creativity laboratory." The platform enables instructors to practice their teaching and engagement skills through realistic conversations with AI-simulated students, helping them prepare for real-world classroom scenarios.

Unlike generic chatbots, the platform uses advanced Retrieval Augmented Generation (RAG) technology to create authentic and context-aware student personas that respond based on detailed background information, creating meaningful training experiences for instructors.

## 🔍 Features

### Core Functionality
- **Interactive Chat Interface**: Clean, intuitive interface for natural conversation flow
- **AI-Simulated Students**: Diverse student profiles with unique personalities, backgrounds, and learning styles
- **Context-Aware Responses**: AI responses maintain conversation continuity and reflect each student's unique character
- **Suggested Questions**: AI-generated follow-up questions to facilitate meaningful conversations
- **Multilingual Support**: Built-in Kannada language detection and translation capabilities
- **Advanced Session Management**: Start, pause, resume, and end chat sessions with automatic history tracking
- **Session Persistence**: All conversations are securely stored and can be resumed later

### Technical Capabilities
- **RAG Architecture**: Knowledge-enhanced AI responses grounded in factual student information
- **Secure Authentication**: Google OAuth integration with role-based access control
- **Cloud-Native**: Fully deployed on AWS with scalable infrastructure
- **Real-time Processing**: Fast response generation with optimized retrieval algorithms
- **Comprehensive Logging**: Detailed activity tracking for monitoring and debugging
- **Multi-Session Support**: Manage multiple concurrent chat sessions with different student profiles

## 🏗️ Technical Architecture

Agastya AI implements a modern client-server architecture:

```
┌───────────────────┐     ┌─────────────────┐     ┌─────────────────────┐
│                   │     │                 │     │                     │
│  Streamlit UI     │────▶│  FastAPI API    │────▶│  AWS Infrastructure │
│  (Frontend)       │◀────│  (Backend)      │◀────│  (Cloud Services)   │
│                   │     │                 │     │                     │
└───────────────────┘     └─────────────────┘     └─────────────────────┘
```

### Frontend Architecture (Streamlit)
- **User Authentication**: Google OAuth integration for secure login
- **Stateful UI**: Session management across page refreshes using Streamlit's session state
- **Page Structure**:
  - Home dashboard with welcome information
  - Student selection gallery showing available student profiles
  - Interactive chat interface with suggested question prompts
  - Loading screens for asynchronous operations
  - Authentication management

### Backend Architecture (FastAPI)
- **API Endpoints**: RESTful API for all operations including student profiles, chat sessions, and message handling
- **Security Layer**: API key authentication for all endpoints
- **RAG System**: Retrieval-Augmented Generation pipeline for contextual student responses
- **Multilingual Support**: Kannada language detection and translation capabilities
- **Session Management**: Robust handling of concurrent chat sessions

### AWS Infrastructure
- **EC2**: Hosts the FastAPI backend and Streamlit frontend services
- **Application Load Balancer**: Routes traffic and handles HTTPS termination
- **DynamoDB**: Stores student profiles, chat sessions, and messages
- **S3**: Stores vectorstores and exported chat transcripts
- **Lambda**: Processes chat exports asynchronously when sessions end
- **Route 53**: DNS management for the agastyaconnect.com domain
- **GitHub Actions**: CI/CD pipeline for automated deployment

## 🌐 Live Environment

The production environment is currently deployed and accessible:

- **Domain**: agastyaconnect.com
- **Protocol**: HTTPS (with automatic HTTP to HTTPS redirection)
- **Authentication**: Google account login required
- **Hosting**: AWS EC2 with Application Load Balancer
- **Services**: FastAPI and Streamlit running as systemd services
- **Monitoring**: CloudWatch logs and metrics

## 🔧 Technology Stack

### Frontend
- **Streamlit**: Interactive web application framework
- **AsyncIO**: For asynchronous operations
- **Google OAuth**: Authentication provider

### Backend
- **FastAPI**: High-performance API framework
- **Uvicorn**: ASGI server
- **Pydantic**: Data validation and settings management

### AI Components
- **LangChain**: Framework for creating LLM applications
  - `langchain-core`: Core components
  - `langchain-chroma`: Vector store integration
  - `langchain-community`: Document loaders
  - `langchain-google-genai`: Google AI integration
- **Google Generative AI**: LLM provider for RAG responses
- **Google Cloud Translate**: Translation for Kannada support
- **ChromaDB**: Vector database for embeddings

### AWS Services
- **EC2**: Compute service for backend and frontend
- **Application Load Balancer**: Traffic management and HTTPS handling
- **DynamoDB**: NoSQL database for all application data
- **S3**: Object storage for vectorstores and exports
- **Lambda**: Serverless functions for asynchronous processing
- **Route 53**: DNS management
- **CloudWatch**: Monitoring and logging

### Development Tools
- **Python 3.9+**: Core programming language
- **Boto3**: AWS SDK for Python
- **Openpyxl**: Excel file generation for chat exports
- **GitHub Actions**: CI/CD automation

## 📂 Project Structure

```
app/
├── .github/
│   └── workflows/             # CI/CD pipelines
│       └── deploy.yml         # AWS deployment workflow
├── .streamlit/                # Streamlit configuration
│   └── config.toml            # UI settings and theme
├── backend/                   # Backend API code
│   ├── api/                   # API models and schemas
│   │   └── models.py          # Pydantic schemas
│   ├── core/                  # Core backend functionality
│   │   └── config.py          # Backend configuration
│   ├── prompts.py             # System prompts for RAG
│   └── utils.py               # Backend utilities
├── frontend/                  # Frontend application code
│   ├── api_calls.py           # Backend API communication
│   ├── prompts.py             # Frontend LLM prompts
│   └── utils.py               # Frontend utilities
├── lambda-functions/          # AWS Lambda functions
│   └── agastya-main-export-chat-lambda.py  # Chat export handler
├── pages/                     # Streamlit pages
│   ├── chat.py                # Chat interface
│   ├── home.py                # Dashboard
│   ├── loading.py             # Loading screen
│   ├── login.py               # Authentication page
│   └── selection.py           # Student selection
├── shared/                    # Shared modules
│   ├── config.py              # Shared configuration
│   ├── logger.py              # Logging setup
│   ├── translate.py           # Translation utilities
│   └── utils.py               # Shared utilities
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore patterns
├── backend_initialize_database.py  # Database initialization
├── backend_server.py          # FastAPI entry point
├── frontend_server.py         # Streamlit entry point
├── README.md                  # Project documentation
└── requirements.txt           # Python dependencies
```

## 📥 Installation & Setup (Local)

### Prerequisites
- Python 3.9 or higher
- AWS account with configured credentials
- Google AI Platform API key
- Google Cloud Platform account with Translation API enabled
- Google OAuth client ID and secret

### Step-by-Step Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/app.git
   cd app
   ```

2. **Create and Activate Virtual Environment**
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
   Create a `.env` file based on the configuration section below.

6. **Configure Streamlit Secrets**
   Create `.streamlit/secrets.toml` based on the configuration section below.

7. **Initialize the Database**
   ```bash
   python backend_initialize_database.py
   ```

8. **Start the Backend Server**
   ```bash
   uvicorn backend_server:app --reload --host 0.0.0.0 --port 8000
   ```

9. **Start the Frontend Server**
   ```bash
   streamlit run frontend_server.py
   ```

10. **Access the Application**
    Open your browser and navigate to `http://localhost:8501`

## ⚙️ Configuration

### Environment Variables (`.env`)

```
# AWS Configuration
AWS_ACCESS_KEY_ID=<your-aws-access-key-id>
AWS_SECRET_ACCESS_KEY=<your-aws-secret-access-key>
AWS_DEFAULT_REGION=<your-aws-region>
AWS_REGION=<your-aws-region>
MAIN_S3_BUCKET_NAME=<your-s3-bucket-name>

# Backend API
BACKEND_API_KEY=<your-secure-backend-api-key>
BACKEND_ORIGINS=<comma-separated-allowed-origins>

# DynamoDB Configuration
DYNAMODB_STUDENT_TABLE_BILLING_MODE=PAY_PER_REQUEST
DYNAMODB_STUDENT_TABLE_NAME=<your-choice-of-student-table-name>
DYNAMODB_CHAT_SESSIONS_TABLE_NAME=<your-choice-of-chat-sessions-table-name>
DYNAMODB_CHAT_MESSAGES_TABLE_NAME=<your-choice-of-chat-messages-table-name>

# Google AI Configuration
GOOGLE_API_KEY=<your-google-api-key>
DOCUMENT_EMBEDDING_MODEL_ID=<your-choice-of-embedding-model>
RESPONSE_GENERATION_MODEL_ID=<your-choice-of-generation-model>
RESPONSE_GENERATION_MODEL_TEMPERATURE=<your-choice-of-model-temperature>
RESPONSE_GENERATION_MODEL_MAX_TOKENS=<your-choice-of-max-tokens>
RAG_MAX_DOC_RETRIEVE=<number-of-docs-to-retrieve>

# Google Cloud Translation
GCP_TYPE=service_account
GCP_PROJECT_ID=<your-gcp-project-id>
GCP_PRIVATE_KEY_ID=<your-gcp-private-key-id>
GCP_PRIVATE_KEY=<your-gcp-private-key>
GCP_CLIENT_EMAIL=<your-gcp-client-email>
GCP_CLIENT_ID=<your-gcp-client-id>
GCP_AUTH_URI=<your-gcp-auth-uri>
GCP_TOKEN_URI=<your-gcp-token-uri>
GCP_AUTH_PROVIDER_X509_CERT_URL=<your-gcp-auth-provider-url>
GCP_CLIENT_X509_CERT_URL=<your-gcp-client-cert-url>
GCP_UNIVERSE_DOMAIN=<your-gcp-universe-domain>

# Storage Paths
LOGS_FOLDER_PATH=logs
LOCAL_VECTORSTORES_DIRECTORY=local-student-vectorstores
STUDENT_METADATA_FILE_NAME=students.json
STUDENT_METADATA_FOLDER_PATH=metadata/students
STUDENT_VECTORSTORE_FOLDER_PATH=vectorstores
CHAT_TRANSCRIPTS_FOLDER_PATH=chat-transcripts
```

### Streamlit Secrets (`.streamlit/secrets.toml`)

```toml
[auth]
redirect_uri = "<your-redirect-uri>"
cookie_secret = "<your-cookie-secret>"
client_id = "<your-google-oauth-client-id>"
client_secret = "<your-google-oauth-client-secret>"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"

[BACKEND]
API_URL = "http://localhost:8000"  # Local development
API_KEY = "<your-backend-api-key>"  # Must match BACKEND_API_KEY in .env

[SECURITY]
ALLOWED_EMAILS = ["user1@example.com", "user2@example.com"]

[LLM]
API_KEY = "<your-google-ai-api-key>"
QUESTIONS_GENERATION_MODEL_ID = "<your-choice-of-model>"
QUESTIONS_GENERATION_MODEL_TEMPERATURE = <your-choice-of-temperature>
QUESTIONS_GENERATION_MODEL_MAX_TOKENS = <your-choice-of-max-tokens>

[LOGS]
FOLDER_PATH = "./logs/frontend_logs"
```

### Student Profile Format
Student profiles in the metadata file should follow this structure:
```json
[
  {
    "student_name": "student-name",
    "student_sex": "male",
    "student_age": 14,
    "student_state": "karnataka",
    "student_image": "https://path-to-image.jpg"
  }
]
```

## 🚀 Deployment (AWS)

The application is deployed on AWS using a combination of EC2, DynamoDB, S3, and Lambda services with GitHub Actions for CI/CD.

### Infrastructure Setup

1. **EC2 Instance**:
   - Ubuntu Server 20.04 LTS
   - t2.medium or larger recommended
   - Security group allowing inbound traffic from ALB only

2. **Application Load Balancer**:
   - HTTP (port 80) → HTTPS (port 443) redirection
   - Target group pointing to EC2 instance on port 8000
   - Health check path: `/health`

3. **DynamoDB Tables**:
   - `students`: For student profile data
   - `chat-sessions`: For session metadata
   - `chat-messages`: For conversation history

4. **S3 Bucket**:
   - Used for storing vectorstores and exported chat transcripts
   - Properly configured IAM permissions for EC2 and Lambda access

5. **Lambda Function**:
   - Triggers from DynamoDB stream to process chat exports when sessions end
   - Environment variables configured for S3 and DynamoDB access

6. **Route 53**:
   - DNS management for agastyaconnect.com
   - A record pointing to the ALB

### Deployment Process

The application uses GitHub Actions for CI/CD. The workflow in `.github/workflows/deploy.yml` automatically:

1. Connects to EC2 via SSH
2. Pulls the latest code from the main branch
3. Updates dependencies if requirements.txt has changed
4. Restarts the FastAPI and Streamlit services

### Setting Up Services

Create systemd service files for both backend and frontend:

**FastAPI Service** (`/etc/systemd/system/fastapi.service`):
```ini
[Unit]
Description=Agastya Backend FastAPI Service
After=network.target

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/app
Environment="PATH=/home/ubuntu/app/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=/home/ubuntu/app/venv/bin/uvicorn backend_server:app --host 0.0.0.0 --port 8000
Restart=always

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
WorkingDirectory=/home/ubuntu/app
Environment="PATH=/home/ubuntu/app/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=/home/ubuntu/app/venv/bin/streamlit run frontend_server.py --server.port 8501 --server.address 0.0.0.0 --server.headless true
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start the services:
```bash
sudo systemctl daemon-reload
sudo systemctl enable fastapi.service streamlit.service
sudo systemctl start fastapi.service streamlit.service
```

## 📖 Usage Guide

### For Instructors

#### Getting Started
1. **Access the Platform**: Navigate to agastyaconnect.com
2. **Sign In**: Click "Sign in with Google" and authenticate
3. **Home Page**: View the welcome screen with information about the platform
4. **Select a Student**: Click "Get Started" and choose a student profile
5. **Start Chatting**: Engage in conversation with the AI-simulated student

#### Chat Interface
- **Student Responses**: Appear as messages with the student's avatar
- **Suggested Questions**: Available in the sidebar for quick selection
- **Input Box**: Type your own questions or select from suggestions
- **Resume Chats**: Continue previous conversations with students
- **Multilingual Support**: Type in Kannada if preferred

#### Best Practices
- Ask open-ended questions to encourage detailed responses
- Follow up on interesting points to explore student perspectives
- Use suggested questions when unsure what to ask next
- Try different approaches with multiple students
- Keep conversations focused on educational topics and student experiences

### For Administrators

#### Accessing Logs
- Backend logs: Located in `/home/ubuntu/app/logs/backend_logs/`
- Frontend logs: Located in `/home/ubuntu/app/logs/frontend_logs/`

#### Managing Users
- Add allowed email addresses in `.streamlit/secrets.toml` for access control
- Update the application by pushing to the main branch on GitHub
- Monitor active sessions through AWS CloudWatch

## 🔒 Security Considerations

The application implements several security measures:

- **API Authentication**: All backend endpoints are protected with API key authentication
- **User Authentication**: Frontend uses Google OAuth with email allowlist
- **HTTPS**: All traffic is encrypted using SSL/TLS
- **Input Validation**: All user inputs are validated with Pydantic models
- **Environment Variables**: Sensitive configuration is stored in environment variables
- **AWS IAM**: Least privilege principle for all AWS service access
- **CORS Protection**: Backend restricts cross-origin requests to allowed origins
- **Error Handling**: Errors are logged but not exposed to users in detail

## 🤝 Contributing

We welcome contributions to the Agastya AI platform! Here's how you can contribute:

1. **Fork the Repository**: Create your own copy of the project
2. **Create a Feature Branch**: Make your changes in a new branch
3. **Follow Coding Standards**: Ensure code adheres to PEP 8 style guidelines
4. **Write Meaningful Commit Messages**: Clearly describe your changes
5. **Submit a Pull Request**: For review and integration into the main branch

### Development Guidelines
- Follow PEP 8 style guidelines for Python code
- Write meaningful commit messages
- Update documentation to reflect your changes
- Test your changes thoroughly before submitting

## 📞 Contact Information

For questions, support, or feedback:

- **Email**: info@agastya.org
- **Phone**: +91-8041124132
- **Website**: [agastya.org](https://agastya.org)

---

*This platform is developed exclusively for Agastya International Foundation. Unauthorized access or use is prohibited.*