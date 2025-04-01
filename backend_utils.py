import boto3
import json
import os
import random
import shutil

from backend_config import (
    AWS_DEFAULT_REGION,
    DOCUMENT_EMBEDDING_MODEL_ID,
    DYNAMODB_STUDENT_TABLE_CONFIG,
    DYNAMODB_STUDENT_TABLE_NAME,
    MAIN_S3_BUCKET_NAME,
    RESPONSE_GENERATION_MODEL_ID,
    RESPONSE_GENERATION_MODEL_MAX_TOKENS,
    RESPONSE_GENERATION_MODEL_TEMPERATURE,
    STUDENT_METADATA_FILE_NAME,
    STUDENT_METADATA_FOLDER_PATH,
    STUDENT_VECTORSTORE_FOLDER_PATH,
    TEMPORARY_VECTORSTORES_DIRECTORY,
)
from backend_prompts import SYSTEM_PROMPT_CONTEXTUALIZED_QUESTION, SYSTEM_PROMPT_MAIN
from backend_session_database import (
    create_chat_message_table,
    create_main_database,
)
from botocore.exceptions import ClientError
from configure_logger import backend_logger
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.base import Chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_chroma import Chroma
from langchain_community.document_loaders import (
    Docx2txtLoader,
    PyPDFLoader,
    UnstructuredHTMLLoader,
)
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import Dict, List, Optional, Tuple

def initialize_sql_database():
    steps = [
        create_main_database,
        create_chat_message_table
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
        bucket_name = MAIN_S3_BUCKET_NAME
        s3_prefix = f"{STUDENT_VECTORSTORE_FOLDER_PATH}/{student_name}/"
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

def get_dynamodb_resource():
    return boto3.resource('dynamodb', region_name=AWS_DEFAULT_REGION)

def create_student_table() -> tuple[bool, str]:
    success = False
    message = ""
    try:
        dynamodb = get_dynamodb_resource()
        table = dynamodb.create_table(**DYNAMODB_STUDENT_TABLE_CONFIG)
        table.meta.client.get_waiter('table_exists').wait(TableName=DYNAMODB_STUDENT_TABLE_NAME)

        success = True
        message = f"Table: '{DYNAMODB_STUDENT_TABLE_NAME}' created successfully"
        backend_logger.info(f"create_students_table | {message}")
        return success, message

    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            success = True
            message = f"Table '{DYNAMODB_STUDENT_TABLE_NAME}' already exists"
            backend_logger.info(f"create_students_table | {message}")
            return success, message

        message = f"Error creating table: {str(e)}"
        backend_logger.error(f"create_students_table | {message}")
        return success, message

    except Exception as e:
        message = f"Unexpected error creating table: {str(e)}"
        backend_logger.error(f"create_students_table | {message}")
        return success, message

def get_student_table():
    dynamodb = get_dynamodb_resource()
    return dynamodb.Table(DYNAMODB_STUDENT_TABLE_NAME)

def load_student_metadata_from_s3() -> Tuple[bool, str, Optional[List[Dict]]]:
    success = False
    message = ""
    data = None
    
    try:
        s3_client = boto3.client('s3', region_name=AWS_DEFAULT_REGION)
        
        s3_key = f"{STUDENT_METADATA_FOLDER_PATH}/{STUDENT_METADATA_FILE_NAME}"
        
        response = s3_client.get_object(
            Bucket=MAIN_S3_BUCKET_NAME,
            Key=s3_key
        )
        
        file_content = response['Body'].read().decode('utf-8')
        data = json.loads(file_content)
        
        success = True
        message = f"Successfully loaded student profiles from S3 bucket {MAIN_S3_BUCKET_NAME}"
        backend_logger.info(f"load_students_from_s3 | Loaded {len(data)} profiles from {MAIN_S3_BUCKET_NAME}")
    except ClientError as e:
        message = f"Error loading student profiles from S3: {str(e)}"
        backend_logger.error(f"load_students_from_s3 | {message}")
    except Exception as e:
        message = f"Unexpected error loading student profiles from S3: {str(e)}"
        backend_logger.error(f"load_students_from_s3 | {message}")
    
    return success, message, data

def validate_student(name: str, sex: str, age: int, state: str) -> Tuple[bool, str]:
    success = False
    message = ""

    valid_sexes = ['male', 'female']
    if sex.lower() not in valid_sexes:
        message = f"Invalid sex: '{sex}' for student: '{name}'. Must be one of: {', '.join(valid_sexes)}"
        return success, message
    
    if age < 0:
        message = f"Invalid age: '{age}' for student: '{name}'. Must be greater than 0"
        return success, message
    
    valid_states = [
        "andhra-pradesh", "arunachal-pradesh", "assam", "bihar", "chhattisgarh",
        "goa", "gujarat", "haryana", "himachal-pradesh", "jammu-kashmir",
        "jharkhand", "karnataka", "kerala", "madhya-pradesh", "maharashtra",
        "manipur", "meghalaya", "mizoram", "nagaland", "odisha", "punjab",
        "rajasthan", "sikkim", "tamil-nadu", "telangana", "tripura",
        "uttar-pradesh", "uttarakhand", "west-bengal"
    ]

    if state.lower().replace(' ', '-') not in valid_states:
        message = f"Invalid state: '{state}' for student: '{name}'. Must be one of: {', '.join(valid_states)}"
        return success, message
    
    success = True
    message = "Student profile data is valid"
    return success, message

def insert_student(name: str, sex: str, age: int, state: str, image: str) -> Tuple[bool, str, Optional[bool], Optional[str]]:
    success = False
    message = ""
    result = False
    data = None
    
    validation_success, validation_message = validate_student(name, sex, age, state)
    if not validation_success:
        backend_logger.error(f"insert_student | Validation error for {name}: {validation_message}")
        return success, validation_message, result, data
    
    get_profile_success, get_profile_message, get_profile_result, _ = get_single_student_profile(name)
    if not get_profile_success:
        message = f"Error getting student profile for name: {name}: {get_profile_message}"
        backend_logger.error(f"insert_student | {message}")
        return success, message, result, data
    
    if get_profile_result:
        success = True
        message = f"Student profile already exists for name: {name}"
        backend_logger.info(f"insert_student | {message}")
        return success, message, result, data
    
    try:
        table = get_student_table()
        
        _ = table.put_item(
            Item={
                'name': name,
                'sex': sex,
                'age': age,
                'state': state,
                'image': image
            }
        )
        success = True
        message = f"Student profile for {name} inserted successfully"
        result = True
        data = name
        backend_logger.info(f"insert_student | {message}")
    except ClientError as e:
        message = f"Error inserting student profile for name: {name}: {e}"
        backend_logger.error(f"insert_student | {message}")
    
    return success, message, result, data

def get_single_student_profile(name: str) -> Tuple[bool, str, Optional[bool], Dict]:
    success = False
    message = ""
    result = False
    data = {}
    
    try:
        table = get_student_table()
        
        response = table.get_item(Key={'name': name})
        
        if 'Item' in response:
            student = response['Item']
            success = True
            message = f"Student profile found for name: {name}"
            result = True
            data = {
                "name": student.get('name'),
                "sex": student.get('sex'),
                "age": student.get('age'),
                "state": student.get('state'),
                "image": student.get('image')
            }
            backend_logger.info(f"get_single_student | {message}")
        else:
            success = True
            message = f"Student profile not found for name: {name}"
            backend_logger.info(f"get_single_student | {message}")
    except ClientError as e:
        message = f"Error getting student profile for name: {name}: {e}"
        backend_logger.error(f"get_single_student | {message}")
    
    return success, message, result, data

def get_student_profiles(count: int = 8) -> Tuple[bool, str, Optional[bool], List[Dict]]:
    success = False
    message = ""
    result = False
    data = []
    
    try:
        table = get_student_table()
        response = table.scan()
        
        if 'Items' in response:
            students = response['Items']
            data = [
                {
                    "name": student.get('name'),
                    "sex": student.get('sex'),
                    "age": student.get('age'),
                    "state": student.get('state'),
                    "image": student.get('image')
                }
                for student in students
            ]
            
            random.shuffle(data)
            
            data = data[:min(count, len(data))]
            
            result = len(data) > 0
            success = True
            message = result and f"Retrieved {len(data)} student profiles successfully" or f"No student profiles found for a request to get {count} student profiles"
            backend_logger.info(f"get_students | {message}")
    except ClientError as e:
        message = f"Error getting {count} student profiles: {e}"
        backend_logger.error(f"get_students | {message}")
    
    return success, message, result, data

def populate_student_table() -> Tuple[bool, str]:
    success = False
    message = ""
    
    s3_success, s3_message, students = load_student_metadata_from_s3()
    
    if not s3_success or not students:
        message = f"Failed to load student profiles from S3: {s3_message}"
        backend_logger.error(f"populate_student_table | {message}")
        return False, message
    
    success_count = 0
    error_count = 0
    already_exists_count = 0
    
    for student in students:
        name = student.get('name')
        sex = student.get('sex')
        age = student.get('age', None)
        state = student.get('state')
        image = student.get('image', None)
        
        insert_success, insert_message, insert_result, _ = insert_student(
            name, sex, age, state, image
        )
        
        if not insert_success:
            backend_logger.error(f"populate_student_table | Error inserting student profile for name: {name}: {insert_message}")
            error_count += 1
        elif not insert_result:
            if "already exists" in insert_message:
                already_exists_count += 1
            else:
                backend_logger.error(f"populate_student_table | Error inserting student profile for name: {name}: {insert_message}")
                error_count += 1
        else:
            success_count += 1
    
    success = True
    message = f"Student table populated successfully from S3 with {len(students)} student profiles"
    backend_logger.info(f"populate_student_table | Completed populating {len(students)} profiles: {success_count} new inserts, {already_exists_count} already existed, {error_count} errors")
    
    return success, message

if __name__ == "__main__":
    pass