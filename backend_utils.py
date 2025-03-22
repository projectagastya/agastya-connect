import boto3
import os
import shutil

from backend_config import (
    DOCUMENT_EMBEDDING_MODEL_ID,
    RESPONSE_GENERATION_MODEL_ID,
    RESPONSE_GENERATION_MODEL_MAX_TOKENS,
    RESPONSE_GENERATION_MODEL_TEMPERATURE,
    STUDENT_NARRATIVES_BUCKET_NAME,
    STUDENT_NARRATIVES_BUCKET_PREFIX,
    TEMPORARY_VECTORSTORES_DIRECTORY,
)
from backend_prompts import SYSTEM_PROMPT_CONTEXTUALIZED_QUESTION, SYSTEM_PROMPT_MAIN
from backend_session_database import (
    create_chat_history_table,
    create_chat_session_table,
    create_login_session_table,
    create_main_database,
    create_student_profile_table,
    create_user_profile_table,
    populate_student_profile_table,
)
from configure_logger import backend_logger
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.base import Chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_chroma import Chroma
from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader, UnstructuredHTMLLoader
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List, Optional, Tuple

def initialize_database():
    steps = [
        create_main_database,
        create_user_profile_table,
        create_student_profile_table,
        create_login_session_table,
        create_chat_session_table,
        create_chat_history_table,
        populate_student_profile_table
    ]
    
    for step in steps:
        success, message = step()
        if not success:
            backend_logger.error(f"Database initialization failed at {step.__name__}: {message}")
            return False
    backend_logger.info("Database initialization completed successfully.")
    return True

def formatted_name(student_name: str):
    return student_name.replace('-', ' ').title()

def fetch_vectorstore_from_s3(email: str, login_session_id: str, chat_session_id: str, student_name: str) -> Tuple[bool, str, bool, Optional[str]]:
    success = False
    message = ""
    result = False
    data = None

    local_dir = os.path.join(
        TEMPORARY_VECTORSTORES_DIRECTORY,
        f"{email}_{student_name}_{login_session_id}_{chat_session_id}"
    )
    created_dir = False
    try:
        if os.path.exists(local_dir):
            backend_logger.info(f"fetch_vectorstore_from_s3 | Removing existing directory {local_dir}")
            shutil.rmtree(local_dir)

        os.makedirs(local_dir, exist_ok=True)
        created_dir = True
        backend_logger.info(f"fetch_vectorstore_from_s3 | Created directory {local_dir}")
        s3_client = boto3.client("s3")
        bucket_name = STUDENT_NARRATIVES_BUCKET_NAME
        s3_prefix = f"{STUDENT_NARRATIVES_BUCKET_PREFIX}/{student_name}/"
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=s3_prefix)

        if 'Contents' not in response:
            backend_logger.error(f"fetch_vectorstore_from_s3 | No objects found in S3 under prefix: {s3_prefix}")
            success = True
            message = "No objects found in S3 under prefix"
            backend_logger.info(f"fetch_vectorstore_from_s3 | {message}")
            return success, message, result, data
    
        for obj in response['Contents']:
            key = obj['Key']
            relative_path = key[len(s3_prefix):]
            if '..' in relative_path:
                backend_logger.warning(f"fetch_vectorstore_from_s3 | Suspicious path detected: {relative_path}")
                continue
            local_file_path = os.path.join(local_dir, relative_path)
            os.makedirs(os.path.dirname(local_file_path), exist_ok=True)        
            s3_client.download_file(bucket_name, key, local_file_path)
            backend_logger.info(f"fetch_vectorstore_from_s3 | Downloaded file {key} to {local_file_path}")
        success = True
        result = True
        message = "Vectorstore fetched from S3 successfully"
        data = local_dir
        backend_logger.info(f"fetch_vectorstore_from_s3 | {message}")
        return success, message, result, data
    except Exception as e:
        backend_logger.error(f"fetch_vectorstore_from_s3 | Error fetching vectorstore from S3: {e}")
        if created_dir and os.path.exists(local_dir):
            try:
                shutil.rmtree(local_dir)
                backend_logger.info(f"fetch_vectorstore_from_s3 | Cleaned up directory {local_dir} after error")
            except Exception as ce:
                backend_logger.error(f"fetch_vectorstore_from_s3 | Failed to clean up directory {local_dir}: {ce}")
        message = f"Error fetching vectorstore from S3: {e}"
        return success, message, result, data

def load_vectorstore_from_path(local_dir: str) -> Tuple[bool, str, Optional[Chroma]]:
    success = False
    message = ""
    data = None
    try:
        embedding_function = GoogleGenerativeAIEmbeddings(model=DOCUMENT_EMBEDDING_MODEL_ID)
        vectorstore = Chroma(persist_directory=local_dir, embedding_function=embedding_function)
        success = True
        message = "Vectorstore loaded successfully"
        data = vectorstore
        backend_logger.info(f"load_vectorstore_from_path | {message}")
        return success, message, data
    except Exception as e:
        message = f"Error in loading vectorstore: {e}"
        backend_logger.error(f"load_vectorstore_from_path | {message}")
        return success, message, data

def load_and_split_document(file_path: str) -> Tuple[bool, str, List[Document]]:
    success = False
    message = ""
    data = None
    try:
        if file_path.endswith('.pdf'):
            loader = PyPDFLoader(file_path)
        elif file_path.endswith('.docx'):
            loader = Docx2txtLoader(file_path)
        elif file_path.endswith('.html'):
            loader = UnstructuredHTMLLoader(file_path)
        else:
            message = f"Unsupported file type: {file_path}"
            backend_logger.error(f"load_and_split_document | {message}")
            return success, message, data
        documents = loader.load()
        success = True
        message = "Documents loaded successfully"
        data = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200, length_function=len).split_documents(documents)
        backend_logger.info(f"load_and_split_document | {message}")
        return success, message, data
    except Exception as e:
        message = f"Error in loading and splitting document: {e}"
        backend_logger.error(f"load_and_split_document | {message}")
        return success, message, data

def get_rag_chain(retriever: Chroma) -> Tuple[bool, str, Optional[Chain]]:
    success = False
    message = ""
    data = None
    try:
        llm = ChatGoogleGenerativeAI(
            model=RESPONSE_GENERATION_MODEL_ID,
            temperature=RESPONSE_GENERATION_MODEL_TEMPERATURE,
            max_tokens=RESPONSE_GENERATION_MODEL_MAX_TOKENS
        )
        contextualize_question_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SYSTEM_PROMPT_CONTEXTUALIZED_QUESTION),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}")
            ]
        )
        final_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SYSTEM_PROMPT_MAIN),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}")
            ]
        )
        history_aware_retriever = create_history_aware_retriever(llm, retriever, contextualize_question_prompt)
        question_answer_chain = create_stuff_documents_chain(llm=llm, prompt=final_prompt)
        rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
        success = True
        message = "RAG chain created successfully"
        data = rag_chain
    except Exception as e:
        backend_logger.error(f"Error in getting RAG chain: {e}")
        message = f"Error in getting RAG chain: {e}"
    return success, message, data

if __name__ == "__main__":
    pass