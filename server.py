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
    end_all_chat_sessions,
    fetch_vectorstore_from_s3,
    formatted,
    get_chat_history,
    get_rag_chain,
    get_student_profiles,
    get_chat_history_for_ui,
    get_active_chat_sessions,
    initialize_chat_session,
    insert_chat_message,
    load_vectorstore_from_path
)
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, Security, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader
from utils.shared.logger import backend_logger

# Check if BACKEND_API_KEY is set. If not, raise an HTTP exception.
if BACKEND_API_KEY is None:
    backend_logger.error("BACKEND_API_KEY is not set")
    raise HTTPException(status_code=500, detail="BACKEND_API_KEY is not set")

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

# Function to validate the provided API key from the X-API-Key header.
def get_api_key(api_key: str = Security(api_key_header)):
    # Check if the API key is provided. If not, raise an HTTP exception.
    if not api_key:
        backend_logger.error("API key not provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key header missing"
        )
    # Check if the API key is valid. If not, raise an HTTP exception.
    if api_key != BACKEND_API_KEY:
        backend_logger.error("Invalid BACKEND API key")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid BACKEND API Key"
        )
    return api_key

# Endpoint for simple health check.
@app.get("/health", summary="Check API health")
def health_endpoint():
    try:
        return {"success": True, "message": "Backend is healthy", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        backend_logger.error(f"Health check error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to check API health. Please try again.")

@app.post("/get-student-profiles", summary="Get student profiles", response_model=GetStudentProfilesResponse, dependencies=[Depends(get_api_key)])
def get_student_profiles_endpoint(api_request: GetStudentProfilesRequest):
    try:
        count = api_request.count

        get_student_profiles_success, get_student_profiles_message, get_student_profiles_result, students = get_student_profiles(count=count)
        if not get_student_profiles_success:
            backend_logger.error(f"Database error in getting {count} student profiles: {get_student_profiles_message}")
            raise HTTPException(status_code=500, detail=f"Failed to retrieve {count} student profiles from the database.")
        students = students[:min(count, len(students))]
        
        student_profiles = [
            StudentProfileSchema(
                student_name=student["student_name"],
                student_sex=student["student_sex"],
                student_age=student["student_age"],
                student_state=student["student_state"],
                student_image=student["student_image"]
            ) for student in students
        ]
        backend_logger.info(f"Retrieved {len(student_profiles)} student profiles successfully for a request to get {count} student profiles")
        return GetStudentProfilesResponse(
            success=get_student_profiles_success,
            message=get_student_profiles_message,
            result=get_student_profiles_result,
            data=student_profiles,
            timestamp=datetime.now().isoformat()
        )
    
    except HTTPException as http_e:
        backend_logger.error(f"HTTP exception in getting {count} student profiles: {http_e}")
        raise http_e
    except Exception as e:
        backend_logger.error(f"Get student profiles endpoint error for {count} student profiles: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve {count} student profiles. Please try again.")

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
        
        fetch_vectorstore_from_s3_success, fetch_vectorstore_from_s3_message, fetch_vectorstore_from_s3_result, fetch_vectorstore_from_s3_data = fetch_vectorstore_from_s3(
            user_email=user_email,
            login_session_id=login_session_id,
            chat_session_id=chat_session_id,
            student_name=student_name
        )
        if not fetch_vectorstore_from_s3_success:
            backend_logger.error(f"Error in fetching vectorstore from S3: {fetch_vectorstore_from_s3_message}")
            raise HTTPException(status_code=500, detail="Failed to fetch vectorstore from S3. Please try again.")
        if not fetch_vectorstore_from_s3_result:
            backend_logger.error(f"Vectorstore not found for email={user_email}, student_name={student_name}, global_session_id={global_session_id}")
            raise HTTPException(status_code=404, detail="Vectorstore not found. Please try again.")
        
        load_vectorstore_from_path_success, load_vectorstore_from_path_message, rag_vectorstore = load_vectorstore_from_path(local_dir=fetch_vectorstore_from_s3_data)
        if not load_vectorstore_from_path_success:
            backend_logger.error(f"Error in loading vectorstore from path: {load_vectorstore_from_path_message}")
            raise HTTPException(status_code=500, detail="Failed to load vectorstore from path. Please try again.")

        init_chat_success, init_chat_message = initialize_chat_session(
            user_email=user_email,
            login_session_id=login_session_id,
            chat_session_id=chat_session_id,
            user_first_name=user_first_name,
            user_last_name=user_last_name,
            student_name=student_name
        )
        
        if not init_chat_success:
            backend_logger.error(f"Error initializing chat session in DynamoDB: {init_chat_message}")
            raise HTTPException(status_code=500, detail="Failed to initialize chat session in database. Please try again.")

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
            backend_logger.error(f"Error inserting chat history: {insert_chat_message_message}")
            raise HTTPException(status_code=500, detail="Unexpected error. Please try again.")
        backend_logger.info(f"First message inserted for global_session_id={global_session_id}")

        return StartChatResponse(
            success=True,
            message=f"Chat session initialized successfully for email={user_email}",
            result=True,
            data=first_assistant_message,
            timestamp=datetime.now().isoformat()
        )
    except HTTPException as http_e:
        backend_logger.error(f"HTTP exception in initializing chat session: {http_e}")
        raise http_e
    except Exception as e:
        backend_logger.error(f"Start chat session endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Failed to initialize chat session. Please try again.")

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
            backend_logger.error(f"Error in loading vectorstore from path: {load_vectorstore_message}")
            raise HTTPException(status_code=500, detail="Failed to load vectorstore from path. Please try again.")
        
        get_chat_history_success, get_chat_history_message, get_chat_history_result, chat_history = get_chat_history(login_session_id=login_session_id, chat_session_id=chat_session_id)
        if not get_chat_history_success:
            backend_logger.error(f"Database error in getting chat history for global_session_id={global_session_id}: {get_chat_history_message}")
            raise HTTPException(status_code=500, detail="Failed to retrieve chat history. Please try again.")
        if not get_chat_history_result:
            backend_logger.error(f"Chat history not found for global_session_id={global_session_id}")
            raise HTTPException(status_code=404, detail="Chat history not found. Please try again.")

        retriever = rag_vectorstore.as_retriever(search_kwargs={"k": MAX_DOCS_TO_RETRIEVE})
        if not retriever:
            backend_logger.error(f"Error in creating session retriever for global_session_id={global_session_id}")
            raise HTTPException(status_code=500, detail="Failed to create session retriever. Please try again.")
        
        get_rag_chain_success, get_rag_chain_message, rag_chain = get_rag_chain(retriever=retriever)
        if not get_rag_chain_success:
            backend_logger.error(f"Error in getting RAG chain for global_session_id={global_session_id}: {get_rag_chain_message}")
            raise HTTPException(status_code=500, detail="Failed to get RAG chain. Please try again.")
        
        answer = rag_chain.invoke({"input": question, "chat_history": chat_history, "user_full_name": user_full_name, "student_name": formatted(student_name)}).get("answer", None)
        if answer is None:
            backend_logger.error(f"Error in getting RAG chain answer for global_session_id={global_session_id} with question: {question}, question_kannada: {question_kannada}")
            raise HTTPException(status_code=500, detail="Failed to get RAG chain answer. Please try again.")
        
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
            raise HTTPException(status_code=500, detail="Failed to insert chat history. Please try again.")

        backend_logger.info(f"Chat history inserted for global_session_id={global_session_id}")
        return ChatMessageResponse(success=True, message=f"Chat history inserted successfully for global_session_id={global_session_id}", result=True, data=answer, timestamp=datetime.now().isoformat())
    except HTTPException as http_e:
        backend_logger.error(f"HTTP exception in chat endpoint: {http_e}")
        raise http_e
    except Exception as e:
        backend_logger.error(f"Chat endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve chat response. Please try again.")

# Endpoint to retrieve all active chat sessions for a specific user login.
@app.post("/get-active-sessions", summary="Get active chat sessions for a user", response_model=GetActiveSessionsResponse, dependencies=[Depends(get_api_key)])
def get_active_sessions_endpoint(api_request: GetActiveSessionsRequest):
    try:
        user_email = api_request.user_email.strip()
        login_session_id = api_request.login_session_id.strip()
        
        get_active_sessions_success, get_active_sessions_message, get_active_sessions_result, sessions = get_active_chat_sessions(
            user_email=user_email,
            login_session_id=login_session_id
        )
        
        if not get_active_sessions_success:
            backend_logger.error(f"Database error in getting active sessions for user {user_email}: {get_active_sessions_message}")
            raise HTTPException(status_code=500, detail=f"Failed to retrieve active sessions for user {user_email} from the database.")
        
        session_infos = [
            ChatSessionInfo(
                student_name=session["student_name"],
                chat_session_id=session["chat_session_id"],
                global_session_id=session["global_session_id"],
                started_at=session["started_at"],
                last_updated_at=session["last_updated_at"]
            ) for session in sessions
        ]
        
        backend_logger.info(f"Retrieved {len(session_infos)} active chat sessions for user {user_email}")
        return GetActiveSessionsResponse(
            success=get_active_sessions_success,
            message=get_active_sessions_message,
            result=get_active_sessions_result,
            data=session_infos,
            timestamp=datetime.now().isoformat()
        )
    
    except HTTPException as http_e:
        backend_logger.error(f"HTTP exception in getting active sessions for user {api_request.user_email}: {http_e}")
        raise http_e
    except Exception as e:
        backend_logger.error(f"Get active sessions endpoint error for user {api_request.user_email}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve active sessions. Please try again.")

# Endpoint to retrieve the complete chat history for a specific chat session.
@app.post("/get-chat-history", summary="Get chat history for a session", response_model=GetChatHistoryResponse, dependencies=[Depends(get_api_key)])
def get_chat_history_endpoint(api_request: GetChatHistoryRequest):
    try:
        login_session_id = api_request.login_session_id.strip()
        chat_session_id = api_request.chat_session_id.strip()
        
        global_session_id = f"{login_session_id}#{chat_session_id}"
        
        get_chat_history_success, get_chat_history_message, get_chat_history_result, messages = get_chat_history_for_ui(
            login_session_id=login_session_id,
            chat_session_id=chat_session_id
        )
        
        if not get_chat_history_success:
            backend_logger.error(f"Database error in getting chat history for session {global_session_id}: {get_chat_history_message}")
            raise HTTPException(status_code=500, detail=f"Failed to retrieve chat history from the database.")
        
        if not get_chat_history_result:
            backend_logger.info(f"No chat history found for session {global_session_id}")
            return GetChatHistoryResponse(
                success=True,
                message="No chat history found",
                result=False,
                data=[],
                timestamp=datetime.now().isoformat()
            )
        
        message_infos = [
            ChatMessageInfo(
                role=message["role"],
                content=message["content"],
                created_at=message["created_at"]
            ) for message in messages
        ]
        
        backend_logger.info(f"Retrieved {len(message_infos)} messages for session {global_session_id}")
        return GetChatHistoryResponse(
            success=True,
            message=f"Retrieved {len(message_infos)} messages",
            result=True,
            data=message_infos,
            timestamp=datetime.now().isoformat()
        )
    
    except HTTPException as http_e:
        backend_logger.error(f"HTTP exception in getting chat history: {http_e}")
        raise http_e
    except Exception as e:
        backend_logger.error(f"Get chat history endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve chat history. Please try again.")

# Endpoint to mark all chat sessions associated with a specific user login as inactive.
@app.post("/end-all-chats", summary="End all chat sessions for a login", response_model=EndChatResponse, dependencies=[Depends(get_api_key)])
def end_all_chats_endpoint(api_request: GetActiveSessionsRequest):
    try:
        user_email = api_request.user_email.strip()
        login_session_id = api_request.login_session_id.strip()
        
        end_all_chat_success, end_all_chat_message = end_all_chat_sessions(
            user_email=user_email,
            login_session_id=login_session_id
        )
        
        if not end_all_chat_success:
            backend_logger.error(f"Error ending all chat sessions for user {user_email}: {end_all_chat_message}")
            raise HTTPException(status_code=500, detail="Failed to end all chat sessions. Please try again.")
        
        return EndChatResponse(
            success=True,
            message=f"Chat sessions ended successfully for user {user_email}",
            timestamp=datetime.now().isoformat()
        )
    except HTTPException as http_e:
        backend_logger.error(f"HTTP exception in ending all chat sessions for user {user_email}: {http_e}")
        raise http_e
    except Exception as e:
        backend_logger.error(f"End all chats endpoint error for user {user_email}: {e}")
        raise HTTPException(status_code=500, detail="Failed to end all chat sessions. Please try again.")

# Endpoint to resume a specific chat session by reloading its vectorstore.
@app.post("/resume-chat", summary="Resume a specific chat session", response_model=StartChatResponse, dependencies=[Depends(get_api_key)])
def resume_chat_endpoint(api_request: StartEndChatRequest):
    try:
        user_email = api_request.user_email.strip()
        login_session_id = api_request.login_session_id.strip()
        chat_session_id = api_request.chat_session_id.strip()
        student_name = api_request.student_name.strip()
        
        global_session_id = f"{login_session_id}#{chat_session_id}"
        
        fetch_vectorstore_from_s3_success, fetch_vectorstore_from_s3_message, fetch_vectorstore_from_s3_result, fetch_vectorstore_from_s3_data = fetch_vectorstore_from_s3(
            user_email=user_email,
            login_session_id=login_session_id,
            chat_session_id=chat_session_id,
            student_name=student_name
        )
        
        if not fetch_vectorstore_from_s3_success:
            backend_logger.error(f"Error in fetching vectorstore from S3: {fetch_vectorstore_from_s3_message}")
            raise HTTPException(status_code=500, detail="Failed to fetch vectorstore from S3. Please try again.")
        if not fetch_vectorstore_from_s3_result:
            backend_logger.error(f"Vectorstore not found for email={user_email}, student_name={student_name}, global_session_id={global_session_id}")
            raise HTTPException(status_code=404, detail="Vectorstore not found. Please try again.")
        
        load_vectorstore_from_path_success, load_vectorstore_from_path_message, rag_vectorstore = load_vectorstore_from_path(local_dir=fetch_vectorstore_from_s3_data)
        if not load_vectorstore_from_path_success:
            backend_logger.error(f"Error in loading vectorstore from path: {load_vectorstore_from_path_message}")
            raise HTTPException(status_code=500, detail="Failed to load vectorstore from path. Please try again.")

        return StartChatResponse(
            success=True,
            message=f"Chat session resumed successfully for email={user_email}",
            result=True,
            data="",
            timestamp=datetime.now().isoformat()
        )
    except HTTPException as http_e:
        backend_logger.error(f"HTTP exception in resuming chat session: {http_e}")
        raise http_e
    except Exception as e:
        backend_logger.error(f"Resume chat session endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Failed to resume chat session. Please try again.")