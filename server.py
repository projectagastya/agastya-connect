import os

from config.backend.api import (
    BACKEND_API_KEY,
    BACKEND_ORIGINS
)
from config.backend.vectorstores import (
    LOCAL_VECTORSTORES_DIRECTORY,
    MAX_DOCS_TO_RETRIEVE
)
from api.models import (
    ChatMessageRequest,
    ChatMessageResponse,
    EndChatResponse,
    GetStudentProfilesRequest,
    GetStudentProfilesResponse,
    StartChatResponse,
    GetActiveSessionsRequest,
    GetActiveSessionsResponse,
    GetChatHistoryRequest,
    GetChatHistoryResponse,
    ChatSessionInfo,
    ChatMessageInfo,
    StartEndChatRequest,
    StudentProfileSchema
)
from utils.backend.all import (
    fetch_vectorstore_from_s3,
    formatted,
    get_chat_history,
    get_rag_chain,
    initialize_chat_session,
    insert_chat_message,
    load_vectorstore_from_path
)
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, Request, Security, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.security.api_key import APIKeyHeader
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from utils.shared.errors import get_user_error
from utils.shared.logger import backend_logger

# Check if BACKEND_API_KEY is set. If not, raise an HTTP exception.
if BACKEND_API_KEY is None:
    backend_logger.error("BACKEND_API_KEY is not set")
    raise HTTPException(status_code=500, detail=get_user_error())

app = FastAPI(title="Agastya API", description="API for the Agastya application")

# Define the API key header.
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Add CORS middleware to allow cross-origin requests.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin for origin in BACKEND_ORIGINS],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["X-API-Key"]
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    backend_logger.error(f"Unhandled exception: {str(exc)} | Path: {request.url.path}")
    return JSONResponse(
        status_code=500,
        content={"detail": get_user_error()}
    )

# Function to validate the provided API key from the X-API-Key header.
def get_api_key(api_key: str = Security(api_key_header)):
    # Check if the API key is provided. If not, raise an HTTP exception.
    if not api_key:
        backend_logger.error("API key not provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=get_user_error()
        )
    # Check if the API key is valid. If not, raise an HTTP exception.
    if api_key != BACKEND_API_KEY:
        backend_logger.error("Invalid BACKEND API key")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=get_user_error()
        )
    return api_key

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=FileResponse, summary="Serve the welcome page")
async def get_welcome_page():
    return 'static/welcome.html'

@app.get("/privacy", response_class=FileResponse, summary="Serve the privacy policy")
async def get_privacy_page():
    return 'static/privacy.html'

@app.get("/terms-of-service", response_class=FileResponse, summary="Serve the terms of service")
async def get_terms_of_service_page():
    return 'static/terms-of-service.html'

# Endpoint for simple health check.
@app.get("/health", summary="Check API health")
def health_endpoint():
    try:
        return {"success": True, "message": "Backend is healthy", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        backend_logger.error(f"Health check error: {str(e)}")
        raise HTTPException(status_code=500, detail=get_user_error())

# Endpoint to initialize a new chat session for a user and student, loading the vectorstore.
@app.post("/start-chat", summary="Initialize chat session with vectorstore", response_model=StartChatResponse, dependencies=[Depends(get_api_key)])
def start_chat_endpoint(api_request: StartEndChatRequest):
    try:
        user_first_name = api_request.user_first_name.strip()
        user_last_name = api_request.user_last_name.strip()
        user_email = api_request.user_email.strip()
        login_session_id = api_request.login_session_id.strip()
        chat_session_id = api_request.chat_session_id.strip()
        student_name = api_request.student_name.strip()
        user_full_name = f"{user_first_name} {user_last_name}"
        
        global_session_id = f"{login_session_id}#{chat_session_id}"
        
        init_chat_success, init_chat_message = initialize_chat_session(
            user_email=user_email,
            login_session_id=login_session_id,
            chat_session_id=chat_session_id,
            user_first_name=user_first_name,
            user_last_name=user_last_name,
            student_name=student_name
        )
        
        if not init_chat_success:
            backend_logger.error(f"Error initializing chat session in DynamoDB: {init_chat_message} | global_session_id={global_session_id}")
            raise HTTPException(status_code=500, detail=get_user_error())

        first_user_message = f"Hi {formatted(text=student_name).split()[0]}, I'm {user_full_name}, your instructor. I would like to chat with you."
        first_assistant_message = f"Hi, I'm {formatted(text=student_name).split()[0]} from Agastya International Foundation. What would you like to know about me?"
    
        insert_chat_message_success, insert_chat_message_message = insert_chat_message(
            login_session_id=login_session_id,
            chat_session_id=chat_session_id,
            user_input=first_user_message,
            user_input_kannada=None,
            input_type="system",
            assistant_output=first_assistant_message
        )
        if not insert_chat_message_success:
            backend_logger.error(f"Error inserting chat history: {insert_chat_message_message} | global_session_id={global_session_id}")
            raise HTTPException(status_code=500, detail=get_user_error())
        backend_logger.info(f"First message inserted for global_session_id={global_session_id}")

        return StartChatResponse(
            success=True,
            message=f"Chat session initialized successfully for email={user_email}",
            result=True,
            data=first_assistant_message,
            timestamp=datetime.now().isoformat()
        )
    except HTTPException as http_e:
        raise http_e
    except Exception as e:
        backend_logger.error(f"Start chat session endpoint error: {e} | global_session_id={api_request.login_session_id}#{api_request.chat_session_id}")
        raise HTTPException(status_code=500, detail=get_user_error())

# Endpoint to handle a user's chat message, generate a response using RAG, and store the interaction.
@app.post(path="/chat", summary="Chat with student", response_model=ChatMessageResponse, dependencies=[Depends(get_api_key)])
def chat_endpoint(api_request: ChatMessageRequest):
    try:
        login_session_id = api_request.login_session_id.strip()
        chat_session_id = api_request.chat_session_id.strip()
        question = api_request.question.strip()
        if api_request.question_kannada:
            question_kannada = api_request.question_kannada.strip()
        else:
            question_kannada = None
        input_type = api_request.input_type.strip()
        student_name = api_request.student_name.strip()
        user_full_name = api_request.user_full_name.strip()

        global_session_id = f"{login_session_id}#{chat_session_id}"
        
        local_dir = os.path.join(LOCAL_VECTORSTORES_DIRECTORY, student_name)
        load_vectorstore_success, load_vectorstore_message, rag_vectorstore = load_vectorstore_from_path(local_dir)
        if not load_vectorstore_success:
            backend_logger.error(f"Error in loading {student_name} vectorstore from path: {load_vectorstore_message} | global_session_id={global_session_id}")
            raise HTTPException(status_code=500, detail=get_user_error())
        
        get_chat_history_success, get_chat_history_message, get_chat_history_result, chat_history = get_chat_history(login_session_id=login_session_id, chat_session_id=chat_session_id)
        if not get_chat_history_success:
            backend_logger.error(f"Database error in getting chat history for global_session_id={global_session_id}: {get_chat_history_message}")
            raise HTTPException(status_code=500, detail=get_user_error())
        if not get_chat_history_result:
            backend_logger.error(f"Chat history not found for global_session_id={global_session_id}")
            raise HTTPException(status_code=404, detail=get_user_error())

        retriever = rag_vectorstore.as_retriever(
            search_kwargs={
                "k": MAX_DOCS_TO_RETRIEVE
            }
        )
        if not retriever:
            backend_logger.error(f"Error in creating session retriever for global_session_id={global_session_id}")
            raise HTTPException(status_code=500, detail=get_user_error())
        
        get_rag_chain_success, get_rag_chain_message, rag_chain = get_rag_chain(retriever=retriever)
        if not get_rag_chain_success:
            backend_logger.error(f"Error in getting RAG chain for global_session_id={global_session_id}: {get_rag_chain_message}")
            raise HTTPException(status_code=500, detail=get_user_error())
        
        rag_response = rag_chain.invoke({
            "input": question,
            "chat_history": chat_history,
            "user_full_name": user_full_name,
            "student_name": formatted(student_name)
        })
        
        answer = rag_response.get("answer", None)

        if answer is None:
            backend_logger.error(f"Error in getting RAG chain answer for global_session_id={global_session_id} with question: {question}, question_kannada: {question_kannada}")
            raise HTTPException(status_code=500, detail=get_user_error())
        
        insert_chat_message_success, insert_chat_message_message = insert_chat_message(
            login_session_id=login_session_id,
            chat_session_id=chat_session_id,
            user_input=question,
            user_input_kannada=question_kannada,
            input_type=input_type,
            assistant_output=answer
        )
        if not insert_chat_message_success:
            backend_logger.error(f"Failed to insert chat history for global_session_id={global_session_id}: {insert_chat_message_message}")
            raise HTTPException(status_code=500, detail=get_user_error())

        backend_logger.info(f"Chat history inserted for global_session_id={global_session_id}")
        return ChatMessageResponse(success=True, message=f"Chat history inserted successfully for global_session_id={global_session_id}", result=True, data=answer, timestamp=datetime.now().isoformat())
    except HTTPException as http_e:
        raise http_e
    except Exception as e:
        backend_logger.error(f"Chat endpoint error: {str(e)} | global_session_id={api_request.login_session_id}#{api_request.chat_session_id}")
        raise HTTPException(status_code=500, detail=get_user_error())

# Endpoint to resume a specific chat session by reloading its vectorstore.
@app.post("/resume-chat", summary="Resume a specific chat session", response_model=StartChatResponse, dependencies=[Depends(get_api_key)])
def resume_chat_endpoint(api_request: StartEndChatRequest):
    try:
        user_email = api_request.user_email.strip()

        return StartChatResponse(
            success=True,
            message=f"Chat session resumed successfully for email={user_email}",
            result=True,
            data="",
            timestamp=datetime.now().isoformat()
        )
    except HTTPException as http_e:
        raise http_e
    except Exception as e:
        backend_logger.error(f"Resume chat session with student {api_request.student_name} for user {api_request.user_email} endpoint error: {e} | global_session_id={api_request.login_session_id}#{api_request.chat_session_id}")
        raise HTTPException(status_code=500, detail=get_user_error())

@app.get("/{full_path:path}", include_in_schema=False)
async def catch_all(full_path: str):
    streamlit_pages = ["home", "login", "chat", "students", "loading"]
    
    if any(full_path.startswith(page) for page in streamlit_pages):
        backend_logger.info(f"Redirecting {full_path} to /app/{full_path}")
        return RedirectResponse(url=f"/app/{full_path}", status_code=301)
    
    backend_logger.warning(f"Undefined path accessed: {full_path}")
    return FileResponse('static/404.html', status_code=404)