# Agastya AI: Instructor Training Platform

![Agastya International Foundation](https://img.shields.io/badge/Agastya-Training_Platform-orange)
![Status](https://img.shields.io/badge/Status-Under_Development-yellow)
![Frontend](https://img.shields.io/badge/Frontend-Streamlit-red)
![Backend](https://img.shields.io/badge/Backend-FastAPI-blue)
![AWS](https://img.shields.io/badge/Cloud-AWS-orange)
![RAG](https://img.shields.io/badge/AI-RAG_Architecture-green)

## 📚 Table of Contents
- [Introduction](#-introduction)
- [Features](#-features)
- [Technical Architecture](#-technical-architecture)
- [Technology Stack](#-technology-stack)
- [Data Flow](#-data-flow)
- [Installation & Setup](#-installation--setup)
- [Configuration](#-configuration)
- [Deployment](#-deployment)
- [Usage Guide](#-usage-guide)
- [FAQ](#-faq)
- [Contributing](#-contributing)
- [Security Considerations](#-security-considerations)
- [Contact Information](#-contact-information)

## 🌟 Introduction

Agastya AI is an innovative training platform developed for the Agastya International Foundation, self-described as "the world's largest creativity laboratory." This application enables instructors to practice their teaching and engagement skills through realistic conversations with AI-simulated students, helping them prepare for real-world classroom scenarios.

The platform uses advanced artificial intelligence techniques, specifically Retrieval Augmented Generation (RAG), to create authentic and context-aware student personas. Unlike generic chatbots, these AI students respond based on detailed background information, creating meaningful training experiences for instructors.

**Current Status**: Under active development with core functionality implemented and deployed. Additional features are being added iteratively.

## 🔍 Features

### Core Functionality
- **Interactive Chat Interface**: Clean, intuitive interface for natural conversation flow
- **AI-Simulated Students**: Diverse student profiles with unique personalities, backgrounds, and learning styles
- **Context-Aware Responses**: AI responses that maintain conversation continuity and reflect the student's character
- **Suggested Questions**: AI-generated follow-up questions to facilitate meaningful conversations
- **Session Management**: Start, pause, and end chat sessions with automatic history tracking

### Technical Capabilities
- **Retrieval Augmented Generation (RAG)**: Knowledge-enhanced AI responses grounded in factual student information
- **Secure Authentication**: Google OAuth integration with role-based access control
- **Cloud-Based Architecture**: Scalable AWS infrastructure with DynamoDB and S3 storage
- **Real-time Processing**: Fast response generation with optimized retrieval algorithms
- **Comprehensive Logging**: Detailed activity tracking for monitoring and debugging

### Administrative Features
- **User Management**: Control access through email allowlists
- **Conversation Persistence**: All chats are securely stored for future reference
- **Stateful Session Handling**: Robust session management across page refreshes or disconnections

## 🏗️ Technical Architecture

Agastya AI implements a modern client-server architecture with several interconnected components:

### System Overview
```
┌─────────────────┐     ┌───────────────────┐     ┌─────────────────────┐
│                 │     │                   │     │                     │
│  Streamlit UI   │────▶│  FastAPI Backend  │────▶│  AWS Infrastructure │
│  (Frontend)     │◀────│  (Application)    │◀────│  (Data Services)    │
│                 │     │                   │     │                     │
└─────────────────┘     └───────────────────┘     └─────────────────────┘
```

### Frontend Architecture (Streamlit)
The frontend is built with Streamlit, a Python framework for creating web applications with minimal UI code:

- **Page Structure**:
  - `frontend_server.py`: Entry point that manages authentication and routing
  - `pages/`: Directory containing modular page components:
    - `home.py`: Dashboard and welcome screen
    - `selection.py`: Student profile browsing and selection
    - `loading.py`: Intermediary page during session setup
    - `chat.py`: Main conversation interface
    - `login.py`: Authentication handling

- **State Management**:
  - Uses Streamlit's session state for persistent data storage
  - Manages user authentication state via `st.experimental_user`
  - Implements custom state reset and initialization functions

- **API Integration**:
  - `frontend_api_calls.py`: Handles all communication with the backend
  - Implements error handling and response parsing
  - Uses caching for performance optimization

### Backend Architecture (FastAPI)
The backend server is developed with FastAPI, a high-performance Python web framework:

- **API Endpoints**:
  - `/health`: System health check endpoint
  - `/get-student-profiles`: Fetch available student profiles
  - `/start-chat`: Initialize chat sessions and prepare vectorstores
  - `/chat`: Process user inputs and generate contextual responses
  - `/end-chat`: Terminate sessions and clean up resources

- **Security Layer**:
  - API key authentication via `X-API-Key` header
  - Input validation with Pydantic models
  - Origin restrictions and CORS configuration

- **Core Processing Components**:
  - RAG chain assembly and execution
  - Vectorstore management and optimization
  - Chat history tracking and retrieval
  - Student profile handling

### Data Storage Architecture (AWS)
The application leverages AWS services for robust, scalable data management:

- **DynamoDB Tables**:
  - `student`: Stores student profile information
  - `chat-sessions`: Tracks active and historical chat session metadata
  - `chat-messages`: Stores individual messages from conversations

- **S3 Storage**:
  - `vectorstores/`: Contains pre-computed document embeddings for RAG
  - `metadata/`: Stores configuration files and source documents

- **Local Storage**:
  - `logs/`: Directory for application logs
  - `temporary-student-vectorstores/`: Working directory for active vectorstores

### AI Architecture (RAG System)
The intelligence layer uses a sophisticated Retrieval Augmented Generation approach:

- **Components**:
  - Document loaders for various file formats (PDF, DOCX, HTML)
  - Text splitters for optimal chunking
  - Embedding models for semantic representation
  - Retrieval algorithms for finding relevant context
  - LLM integration for response generation

- **Process Flow**:
  1. Documents about student personas are embedded and stored
  2. User questions trigger contextual retrieval
  3. Retrieved information enriches the prompt
  4. The LLM generates a personalized response
  5. Conversation history provides additional context

## 🔧 Technology Stack

### Frontend Technologies
- **Streamlit** (v1.27+): Web application framework
- **Python** (v3.9+): Core programming language
- **AsyncIO**: For asynchronous operations
- **Google OAuth**: Authentication provider

### Backend Technologies
- **FastAPI** (v0.103+): API framework
- **Uvicorn**: ASGI server
- **Pydantic**: Data validation and settings management
- **Python** (v3.9+): Core programming language

### AI & Machine Learning
- **LangChain** (v0.0.310+): Framework for LLM applications
  - `langchain-core`: Core components
  - `langchain-chroma`: Vector store integration
  - `langchain-community`: Document loaders and utilities
  - `langchain-google-genai`: Google AI integration
- **Google Generative AI**: LLM provider
  - Embedding model: `models/text-embedding-004`
  - Response model: `gemini-2.0-flash`
- **ChromaDB**: Vector database for embeddings

### AWS Services
- **DynamoDB**: NoSQL database service
  - Global Secondary Indexes for efficient queries
  - On-demand capacity mode for cost optimization
- **S3**: Object storage service
  - Bucket organization for vectorstores and metadata
  - Prefix-based data organization
- **Elastic Load Balancing**: Load balancer for routing traffic
  - HTTP ingress from the internet
  - TCP routing to EC2 instances

### Development & Operations
- **Python-dotenv**: Environment variable management
- **Logging**: Comprehensive logging with rotation
- **Boto3**: AWS SDK for Python
- **UUID**: Unique identifier generation

## 🔄 Data Flow

The system implements a sophisticated data flow architecture to handle conversations:

### Authentication Flow
1. User accesses the Streamlit application
2. Google OAuth authentication is triggered via `st.login()`
3. Upon successful authentication, user information is stored in `st.experimental_user`
4. Email verification against allowlist in `st.secrets.SECURITY.ALLOWED_EMAILS`
5. User is directed to the home page or login page based on authentication status

### Conversation Initialization Flow
1. User selects a student profile from the selection page
2. Frontend generates a unique chat session ID via `uuid4()`
3. Backend fetches vectorstore from S3 and loads it into memory
4. Chat session is registered in DynamoDB with initial metadata
5. First greeting messages are inserted into the chat history
6. Frontend initializes the chat interface with session context

### Message Processing Flow
1. User inputs a question or selects a suggested question
2. Frontend sends the message to the backend along with session context
3. Backend retrieves chat history from DynamoDB
4. RAG system processes the query:
   - Contextualizes the question based on chat history
   - Retrieves relevant documents from vectorstore
   - Generates a response using the LLM with context
5. Response is stored in DynamoDB and returned to frontend
6. Frontend updates the chat interface and generates new suggested questions

### Session Termination Flow
1. User clicks "End Chat Session" button
2. Frontend confirms the action via dialog
3. Backend marks the session as ended in DynamoDB
4. In-memory vectorstore is removed and temporary files are cleaned up
5. Frontend returns user to the home page
6. Session state is reset for potential new sessions

## 📥 Installation & Setup

### Prerequisites
- Python 3.9 or higher
- AWS account with configured credentials
- Google AI Platform access with API key
- S3 bucket for storing vectorstores
- DynamoDB provisioned tables or on-demand capacity

### Local Development Setup

1. **Clone the Repository**
   ```bash
   git clone <repository_url>
   cd agastya-ai
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
   mkdir -p temporary-student-vectorstores
   ```

5. **Configure Environment Variables**
   Create a `secrets.env` file as specified in the Configuration section.

6. **Configure Streamlit Secrets**
   Create a `.streamlit/secrets.toml` file as specified in the Configuration section.

7. **Initialize the Database**
   ```bash
   python backend_initialize_database.py
   ```

8. **Start the Backend Server**
   ```bash
   uvicorn backend_server:app --reload --port 8000
   ```

9. **Start the Frontend Server**
   ```bash
   streamlit run frontend_server.py
   ```

## ⚙️ Configuration

### Environment Variables (`secrets.env`)
```
# AWS Configuration
AWS_ACCESS_KEY_ID=<your-aws-access-key-id>
AWS_SECRET_ACCESS_KEY=<your-aws-secret-access-key>
AWS_DEFAULT_REGION=<your-aws-region>
MAIN_S3_BUCKET_NAME=<your-s3-bucket-name>

# Backend API
BACKEND_API_KEY=<your-secure-backend-api-key>
BACKEND_ORIGINS=<comma-separated-allowed-origins>

# DynamoDB Configuration
DYNAMODB_STUDENT_TABLE_BILLING_MODE=PAY_PER_REQUEST
DYNAMODB_STUDENT_TABLE_NAME=<your-choice-of-student-table-name-on-dynamodb>
DYNAMODB_CHAT_SESSIONS_TABLE_NAME=<your-choice-of-chat-sessions-table-name-on-dynamodb>
DYNAMODB_CHAT_MESSAGES_TABLE_NAME=<your-choice-of-chat-messages-table-name-on-dynamodb>

# Google AI Configuration
DOCUMENT_EMBEDDING_MODEL_ID=<your-choice-of-gemini-embedding-model>
RESPONSE_GENERATION_MODEL_ID=<your-choice-of-gemini-generation-model>
RESPONSE_GENERATION_MODEL_TEMPERATURE=<your-choice-of-model-temperature>
RESPONSE_GENERATION_MODEL_MAX_TOKENS=<your-choice-of-number-of-output-tokens>

# Storage Paths
LOGS_FOLDER_PATH=<your-choice-of-logs-folder-path-on-local>
TEMPORARY_VECTORSTORES_DIRECTORY=<your-choice-of-temporary-student-vectorstores-folder-path-on-local>
STUDENT_METADATA_FILE_NAME=<your-metadata-filename-on-s3>
STUDENT_METADATA_FOLDER_PATH=<your-metadata-folder-path-on-s3>
STUDENT_VECTORSTORE_FOLDER_PATH=<your-vectorstore-folder-path-on-s3>
```

### Streamlit Secrets (`.streamlit/secrets.toml`)
```toml
[BACKEND]
API_URL = "http://localhost:8000"  # Local development
API_KEY = "your-backend-api-key"   # Must match BACKEND_API_KEY in secrets.env

[SECURITY]
ALLOWED_EMAILS = ["user1@example.com", "user2@example.com"]

[LLM]
API_KEY = "your-google-ai-api-key"
QUESTIONS_GENERATION_MODEL_ID = <your-choice-of-gemini-generation-model>
QUESTIONS_GENERATION_MODEL_TEMPERATURE = <your-choice-of-model-temperature>
QUESTIONS_GENERATION_MODEL_MAX_TOKENS = <your-choice-of-number-of-output-tokens>
```

### Student Profile Format
Student profiles in the metadata file should follow this structure:
```json
[
  {
    "name": "student-name",
    "sex": "male",
    "age": 14,
    "state": "karnataka",
    "image": "https://path-to-image.jpg"
  }
]
```

## 🚀 Deployment

### AWS Deployment
The application is currently deployed with the frontend on Streamlit Community Cloud and the backend on AWS:

#### Backend Deployment on AWS
1. **EC2 Instance Setup**:
   - Ubuntu Server 20.04 LTS (or newer)
   - t2.medium or larger recommended
   - Security group configured to allow TCP port 8000 only from the load balancer

2. **Load Balancer Setup**:
   - AWS Elastic Load Balancer configured to:
     - Accept HTTP traffic from the internet (including from the Streamlit frontend)
     - Route TCP traffic on port 8000 to the EC2 instance

3. **Environment Configuration**:
   ```bash
   sudo apt update && sudo apt upgrade -y
   sudo apt install python3-pip python3-venv -y
   ```

4. **Application Setup**:
   ```bash
   git clone https://<your_personal_access_token>@github.com/<username>/<repository_name>.git # Create a personal access token on GitHub
   cd <repository_directory_name>
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   # Ensure uvicorn is in requirements.txt as it's used in the systemd service
   ```

5. **Systemd Service**:
   ```
   [Unit]
    Description=FastAPI Service using Uvicorn with Reload
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

#### Frontend Deployment on Streamlit Community Cloud
1. Create a GitHub repository with your Streamlit application
2. Log in to [Streamlit Community Cloud](https://streamlit.io/cloud)
3. Deploy your application by connecting to the GitHub repository
4. Configure your secrets in the Streamlit dashboard
5. Set the main file to `frontend_server.py`

## 📖 Usage Guide

### For Non-Technical Users

#### Getting Started
1. **Access the Platform**: Navigate to the application URL provided by your administrator
2. **Sign In**: Click "Sign in with Google" and authenticate with your email
3. **Home Page**: You'll see the welcome screen with options to start a new chat
4. **Select a Student**: Click "Get Started" and choose a student profile from the gallery
5. **Wait for Setup**: The system will prepare the chat environment
6. **Start Chatting**: Type your questions in the chat input or use the suggested questions

#### Chat Interface
- **Your Messages**: Appear on the main section with your profile picture
- **Student Responses**: Appear on the main section with the student's profile picture
- **Suggested Questions**: Available in the sidebar for quick selection
- **End Chat**: Click "End Chat Session" in the sidebar when finished

#### Best Practices
- Ask open-ended questions to encourage detailed responses
- Follow up on interesting points to explore student perspectives
- Use suggested questions when unsure what to ask next
- Try different approaches with multiple students
- Keep conversations focused on educational topics and student experiences

### For Technical Users

#### Debugging
The application generates detailed logs for troubleshooting:

- **Backend Logs**: Located in `logs/backend_logs/backend_logs.log`
- **Frontend Logs**: Located in `logs/frontend_logs/frontend_logs.log`

Each log entry includes a timestamp, component identifier, severity level, and detailed message. Most function calls log their success/failure status and relevant metadata.

## ❓ FAQ

### General Questions

**Q: What is Agastya AI?**  
A: Agastya AI is a training platform that allows instructors to practice their teaching skills by having conversations with AI-simulated students.

**Q: How realistic are the AI students?**  
A: The AI students are designed to respond contextually based on detailed background information, creating an authentic conversational experience. The RAG architecture ensures responses are grounded in each student's unique profile.

**Q: Who can access the platform?**  
A: Access is controlled through an email allowlist configured by administrators. Currently, the platform is intended for instructors at Agastya International Foundation.

### Technical Questions

**Q: What is RAG and how does it work?**  
A: Retrieval Augmented Generation (RAG) is a hybrid AI approach that combines information retrieval with text generation. It works by:
1. Converting student profile information into embeddings (numerical representations)
2. Storing these embeddings in a vector database
3. Finding relevant information based on user questions
4. Providing this information as context to the language model
5. Generating responses that are grounded in factual student information

**Q: How is data stored in the application?**  
A: The application uses AWS DynamoDB for structured data (student profiles, chat sessions, messages) and S3 for storing vectorstores containing pre-computed embeddings.

**Q: Is the conversation data stored securely?**  
A: Yes, all conversation data is stored in AWS DynamoDB with appropriate security measures. API access is protected by API key authentication, and the frontend implements secure Google OAuth.

**Q: Can I run the application locally?**  
A: Yes, the README provides detailed instructions for setting up the application on your local machine for development or testing.

## 🤝 Contributing

We welcome contributions to the Agastya AI platform! Here's how you can contribute:

### Setup for Development
1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/agastya-ai.git`
3. Create a feature branch: `git checkout -b feature/amazing-feature`
4. Set up your development environment following the installation instructions

### Development Guidelines
- Follow PEP 8 style guidelines for Python code
- Write meaningful commit messages
- Add or update tests for new features
- Document any new functions, classes, or modules
- Keep performance in mind, especially for RAG operations

### Pull Request Process
1. Update documentation to reflect your changes
2. Make sure all tests pass
3. Ensure code quality with linting tools
4. Submit a pull request with a clear description of your changes
5. Address any review comments promptly

## 🔒 Security Considerations

The application implements several security measures:

- **API Authentication**: Backend endpoints are protected by API key authentication
- **User Authentication**: Frontend uses Google OAuth with email verification
- **Input Validation**: All user inputs are validated with Pydantic models
- **CORS Protection**: Backend limits cross-origin requests
- **Path Traversal Prevention**: S3 and file paths are checked for security issues
- **Error Handling**: Errors are logged but not exposed to users in detail
- **Environment Variables**: Sensitive configuration is stored in environment variables
- **AWS Security**: AWS resources follow least privilege principle

### Security Best Practices for Deployment
- Regularly update dependencies to patch vulnerabilities
- Use HTTPS for all communications
- Implement WAF for production deployments
- Enable CloudTrail for AWS operations logging
- Regularly backup DynamoDB tables
- Monitor for unusual activity patterns

## 📞 Contact Information

For questions, support, or feedback:

- **Email**: info@agastya.org
- **Phone**: +91-8041124132
- **Website**: [agastya.org](https://agastya.org)

### Reporting Issues
If you encounter bugs or have feature requests, please open an issue on the project repository with detailed information about the problem and steps to reproduce it.

---

*This platform is developed exclusively for Agastya International Foundation. Unauthorized access or use is prohibited.*