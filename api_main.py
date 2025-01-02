import os
import shutil

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic_models import DeleteFileRequest, DocumentInfo, QueryInput, QueryResponse
from session_database import (
    delete_all_documents,
    delete_session_document,
    get_all_documents,
    get_chat_history,
    get_session_document,
    insert_chat_history,
    insert_session_document,
)
from utils_langchain import get_rag_chain
from utils_vectorstore import delete_doc_from_vectorstore, index_document_to_vectorstore, rag_vectorstore

load_dotenv()

MAX_DOCS_TO_RETRIEVE = int(os.getenv("RAG_MAX_DOC_RETRIEVE",3))

app = FastAPI()

@app.post(path="/chat", response_model=QueryResponse, summary="Send input prompts to the LLM")
def chat_endpoint(query_input: QueryInput):
    chat_session_id = query_input.chat_session_id

    try:
        chat_history = get_chat_history(chat_session_id)
        session_retriever = rag_vectorstore.as_retriever(search_kwargs={"k": MAX_DOCS_TO_RETRIEVE, "filter": {"chat_session_id": chat_session_id}})
        rag_chain = get_rag_chain(query_input.model.value, retriever=session_retriever)
        answer = rag_chain.invoke({"input": query_input.question, "chat_history": chat_history})['answer']
        insert_chat_history(chat_session_id, query_input.question, answer, query_input.model.value)
        return QueryResponse(answer=answer, chat_session_id=chat_session_id, model=query_input.model)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error during RAG chain invocation: {str(e)}")

@app.post(path="/upload-session-doc", summary="Upload chat session document for RAG")
def upload_and_index_document_endpoint(chat_session_id: str, file: UploadFile = File(...)):
    allowed_extensions = ['.pdf', '.docx', '.html']
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Invalid file extension. Valid types: {', '.join(allowed_extensions)}")
    temp_file_path = f"temp_{file.filename}"
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        file_id = insert_session_document(chat_session_id, file.filename)
        success = index_document_to_vectorstore(temp_file_path, file_id, chat_session_id)
        if success:
            return {
                "message": f"File {file.filename} has been successfully uploaded and indexed", 
                "file_id": file_id, 
                "chat_session_id": chat_session_id
            }
        else:
            try:
                delete_session_document(chat_session_id)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to index {file.filename}.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred during file upload and indexing: {str(e)}")
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@app.get(path="/list-session-doc", response_model=list[DocumentInfo], summary="List the documents used in the chat session")
def list_session_documents_endpoint(chat_session_id: str):
    try:
        documents = get_session_document(chat_session_id)
        if documents:
            return documents
        else:
            raise HTTPException(status_code=404, detail=f"No documents found for session ID: {chat_session_id}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while fetching session documents: {str(e)}")

@app.get(path="/list-all-docs", response_model=list[DocumentInfo], summary="List all documents in all chat sessions")
def list_all_documents_endpoint():
    try:
        documents = get_all_documents()
        if documents:
            return documents
        else:
            raise HTTPException(status_code=404, detail="No documents found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while fetching all documents: {str(e)}")

@app.post(path="/delete-session-doc", summary="Delete chat session's documents")
def delete_session_documents_endpoint(request: DeleteFileRequest):
    try:
        vectorstore_delete_success = delete_doc_from_vectorstore(request.chat_session_id)
        if vectorstore_delete_success:
            db_delete_success = delete_session_document(request.chat_session_id)
            if db_delete_success:
                return {"message": f"Successfully deleted the document for chat session id {request.chat_session_id}"}
            else:
                return {"error": f"Document deleted from vectorstore successfully but failed to delete document for chat session id {request.chat_session_id} from the database"}
        else:
            return {"error": f"Failed to delete document for chat session id {request.chat_session_id} from vectorstore."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while deleting session documents: {str(e)}")

@app.post(path="/delete-all-docs", summary="Delete all documents in all chat sessions")
def delete_all_documents_endpoint():
    try:
        delete_all_documents()
        return {"message": "All documents have been successfully deleted from both vectorstore and the database."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while deleting all documents: {str(e)}")
