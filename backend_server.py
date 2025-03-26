import os
import shutil

from collections import defaultdict
from backend_config import (
    BACKEND_API_KEY,
    BACKEND_ORIGINS,
    MAX_DOCS_TO_RETRIEVE,
    TEMPORARY_VECTORSTORES_DIRECTORY,
)
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, Security, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader
from configure_logger import backend_logger

from backend_pydantic_models import (
    ChatMessageRequest,
    ChatMessageResponse,
    EndChatResponse,
    GetStudentProfilesRequest,
    GetStudentProfilesResponse,
    StartEndChatRequest,
    StartChatResponse,
    StudentProfileSchema,
)
from backend_session_database import (
    get_chat_history,
    get_student_profiles,
    insert_chat_message
)
from backend_utils import (
    formatted_name,
    fetch_vectorstore_from_s3,
    get_rag_chain,
    load_vectorstore_from_path
)

if BACKEND_API_KEY is None:
    backend_logger.error("BACKEND_API_KEY is not set")
    raise HTTPException(status_code=500, detail="BACKEND_API_KEY is not set")

vectorstore_map = defaultdict(dict)

app = FastAPI(title="Agastya API", description="API for the Agastya application")

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin for origin in BACKEND_ORIGINS],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["X-API-Key"]
)

def get_api_key(api_key: str = Security(api_key_header)):
    if not api_key:
        backend_logger.error("API key not provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key header missing"
        )
    if api_key != BACKEND_API_KEY:
        backend_logger.error("Invalid BACKEND API key")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid BACKEND API Key"
        )
    return api_key

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
                name=student["name"],
                sex=student["sex"],
                age=student["age"],
                state=student["state"],
                image=student["image"]
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

@app.post("/start-chat", summary="Initialize chat session with vectorstore", response_model=StartChatResponse, dependencies=[Depends(get_api_key)])
def start_chat_endpoint(api_request: StartEndChatRequest):
    try:
        user_first_name = api_request.user_first_name.strip()
        user_last_name = api_request.user_last_name.strip()
        email = api_request.email.strip()
        login_session_id = api_request.login_session_id.strip()
        chat_session_id = api_request.chat_session_id.strip()
        student_name = api_request.student_name.strip()
        user_full_name = f"{user_first_name} {user_last_name}"
        
        if login_session_id in vectorstore_map:
            if chat_session_id in vectorstore_map[login_session_id]:
                backend_logger.info(f"Chat session already exists for login_session_id={login_session_id}, chat_session_id={chat_session_id}")
                raise HTTPException(status_code=400, detail=f"Chat session {chat_session_id} already exists for login_session_id={login_session_id}")

        fetch_vectorstore_from_s3_success, fetch_vectorstore_from_s3_message, fetch_vectorstore_from_s3_result, fetch_vectorstore_from_s3_data = fetch_vectorstore_from_s3(
            email=email,
            login_session_id=login_session_id,
            chat_session_id=chat_session_id,
            student_name=student_name
        )
        if not fetch_vectorstore_from_s3_success:
            backend_logger.error(f"Error in fetching vectorstore from S3: {fetch_vectorstore_from_s3_message}")
            raise HTTPException(status_code=500, detail="Failed to fetch vectorstore from S3. Please try again.")
        if not fetch_vectorstore_from_s3_result:
            backend_logger.error(f"Vectorstore not found for email={email}, student_name={student_name}, login_session_id={login_session_id}, chat_session_id={chat_session_id}")
            raise HTTPException(status_code=404, detail="Vectorstore not found. Please try again.")
        
        if not fetch_vectorstore_from_s3_success or not fetch_vectorstore_from_s3_result:
            if os.path.exists(os.path.join(TEMPORARY_VECTORSTORES_DIRECTORY, f"{email}_{student_name}_{login_session_id}_{chat_session_id}")):
                shutil.rmtree(os.path.join(TEMPORARY_VECTORSTORES_DIRECTORY, f"{email}_{student_name}_{login_session_id}_{chat_session_id}"))
                backend_logger.info(f"Roll back folder creation for email={email}, student_name={student_name}, login_session_id={login_session_id}, chat_session_id={chat_session_id}.")

        load_vectorstore_from_path_success, load_vectorstore_from_path_message, rag_vectorstore = load_vectorstore_from_path(local_dir=fetch_vectorstore_from_s3_data)
        if not load_vectorstore_from_path_success:
            backend_logger.error(f"Error in loading vectorstore from path: {load_vectorstore_from_path_message}")
            raise HTTPException(status_code=500, detail="Failed to load vectorstore from path. Please try again.")

        vectorstore_map[login_session_id][chat_session_id] = rag_vectorstore
        backend_logger.info(f"Initialized chat session vectorstore for login_session_id={login_session_id}, chat_session_id={chat_session_id}")

        first_user_message = f"Hi {formatted_name(student_name=student_name).split()[0]}, I'm {user_full_name}, your instructor. I would like to chat with you."
        first_assistant_message = f"Hi {user_full_name}, I'm {formatted_name(student_name=student_name).split()[0]} from Agastya International Foundation. What would you like to know about me?"
    
        insert_chat_message_success, insert_chat_message_message = insert_chat_message(
            login_session_id=login_session_id,
            chat_session_id=chat_session_id,
            user_input=first_user_message,
            input_type="default",
            assistant_output=first_assistant_message
        )
        if not insert_chat_message_success:
            backend_logger.error(f"Error inserting chat history: {insert_chat_message_message}")
            raise HTTPException(status_code=500, detail="Unexpected error. Please try again.")
        backend_logger.info(f"First message inserted for login_session_id={login_session_id}, chat_session_id={chat_session_id}")

        return StartChatResponse(
            success=True,
            message=f"Chat session initialized successfully for email={email}",
            result=True,
            data=first_assistant_message,
            timestamp=datetime.now().isoformat()
        )
    except HTTPException as http_e:
        backend_logger.error(f"HTTP exception in initializing chat session: {http_e}")
        raise http_e
    except Exception as e:
        backend_logger.error(f"Init chat session endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Failed to initialize chat session. Please try again.")

@app.post(path="/chat", summary="Chat with student", response_model=ChatMessageResponse, dependencies=[Depends(get_api_key)])
def chat_endpoint(api_request: ChatMessageRequest):
    try:
        login_session_id = api_request.login_session_id.strip()
        chat_session_id = api_request.chat_session_id.strip()
        question = api_request.question.strip()
        input_type = api_request.input_type.strip()
        student_name = formatted_name(api_request.student_name.strip())
        instructor_name = api_request.instructor_name.strip()

        if login_session_id not in vectorstore_map:
            backend_logger.error(f"Login session not found for login_session_id={login_session_id}")
            raise HTTPException(status_code=404, detail="Login session not found in vectorstore map. Please try again.")
        if chat_session_id not in vectorstore_map[login_session_id]:
            backend_logger.error(f"Chat session not found for login_session_id={login_session_id}, chat_session_id={chat_session_id}")
            raise HTTPException(status_code=404, detail="Chat session not found in vectorstore map. Please try again.")
        
        rag_vectorstore = vectorstore_map[login_session_id][chat_session_id]
        
        get_chat_history_success, get_chat_history_message, get_chat_history_result, chat_history = get_chat_history(login_session_id=login_session_id, chat_session_id=chat_session_id)
        if not get_chat_history_success:
            backend_logger.error(f"Database error in getting chat history for login_session_id={login_session_id}, chat_session_id={chat_session_id}: {get_chat_history_message}")
            raise HTTPException(status_code=500, detail="Failed to retrieve chat history. Please try again.")
        if not get_chat_history_result:
            backend_logger.error(f"Chat history not found for login_session_id={login_session_id}, chat_session_id={chat_session_id}")
            raise HTTPException(status_code=404, detail="Chat history not found. Please try again.")

        retriever = rag_vectorstore.as_retriever(search_kwargs={"k": MAX_DOCS_TO_RETRIEVE})
        if not retriever:
            backend_logger.error(f"Error in creating session retriever for login_session_id={login_session_id}, chat_session_id={chat_session_id}")
            raise HTTPException(status_code=500, detail="Failed to create session retriever. Please try again.")
        
        get_rag_chain_success, get_rag_chain_message, rag_chain = get_rag_chain(retriever=retriever)
        if not get_rag_chain_success:
            backend_logger.error(f"Error in getting RAG chain for login_session_id={login_session_id}, chat_session_id={chat_session_id}: {get_rag_chain_message}")
            raise HTTPException(status_code=500, detail="Failed to get RAG chain. Please try again.")
        
        answer = rag_chain.invoke({"input": question, "chat_history": chat_history, "instructor_name": instructor_name, "student_name": student_name}).get("answer", None)
        if answer is None:
            backend_logger.error(f"Error in getting RAG chain answer for login_session_id={login_session_id}, chat_session_id={chat_session_id} with question: {question}")
            raise HTTPException(status_code=500, detail="Failed to get RAG chain answer. Please try again.")
        
        insert_chat_message_success, insert_chat_message_message = insert_chat_message(login_session_id=login_session_id, chat_session_id=chat_session_id, user_input=question, input_type=input_type, assistant_output=answer)
        if not insert_chat_message_success:
            backend_logger.error(f"Failed to insert chat history for login_session_id={login_session_id}, chat_session_id={chat_session_id}: {insert_chat_message_message}")
            raise HTTPException(status_code=500, detail="Failed to insert chat history. Please try again.")

        backend_logger.info(f"Chat history inserted for login_session_id={login_session_id}, chat_session_id={chat_session_id}")
        return ChatMessageResponse(success=True, message=f"Chat history inserted successfully for login_session_id={login_session_id}, chat_session_id={chat_session_id}", result=True, data=answer, timestamp=datetime.now().isoformat())
    except HTTPException as http_e:
        backend_logger.error(f"HTTP exception in chat endpoint: {http_e}")
        raise http_e
    except Exception as e:
        backend_logger.error(f"Chat endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve chat response. Please try again.")

@app.post(path="/end-chat", summary="End chat session", response_model=EndChatResponse, dependencies=[Depends(get_api_key)])
def end_chat_endpoint(api_request: StartEndChatRequest):
    count = 0
    try:
        email = api_request.email.strip()
        student_name = api_request.student_name.strip()
        login_session_id = api_request.login_session_id.strip()
        chat_session_id = api_request.chat_session_id.strip()
        
        if login_session_id in vectorstore_map:
            if chat_session_id in vectorstore_map[login_session_id]:
                del vectorstore_map[login_session_id][chat_session_id]
                backend_logger.info(f"Removed vectorstore for login_session_id={login_session_id}, chat_session_id={chat_session_id} from in-memory map.")
            else:
                count += 1
                backend_logger.warning(f"Login session found but chat session not found for login_session_id={login_session_id}, chat_session_id={chat_session_id} in in-memory map. Continuing cleanup.")
        else:
            count += 1
            backend_logger.warning(f"Login session not found for login_session_id={login_session_id} in in-memory map. Continuing cleanup.")
        
        session_pattern = f"{email}_{student_name}_{login_session_id}_{chat_session_id}"
        vectorstore_path = os.path.join(TEMPORARY_VECTORSTORES_DIRECTORY, session_pattern)
        if os.path.exists(vectorstore_path):
            shutil.rmtree(vectorstore_path)
            backend_logger.info(f"Deleted chat session vectorstore from path {vectorstore_path} for login_session_id={login_session_id}, chat_session_id={chat_session_id}.")
        else:
            count += 1
            backend_logger.warning(f"Vectorstore directory {vectorstore_path} not found. It may have been already removed for login_session_id={login_session_id}, chat_session_id={chat_session_id}.")
        
        if count == 2:
            raise HTTPException(status_code=500, detail="Failed to end chat session. Please try again.")
        
        return EndChatResponse(
            success=True,
            message=f"Chat session ended successfully for login_session_id={login_session_id}, chat_session_id={chat_session_id}",
            timestamp=datetime.now().isoformat()
        )
    except HTTPException as http_e:
        backend_logger.error(f"HTTP exception in ending chat session: {http_e}")
        raise http_e
    except Exception as e:
        backend_logger.error(f"End chat session endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Failed to end chat session. Please try again.")