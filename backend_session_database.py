import json
import mariadb
import random

from backend_config import DB_CONFIG, STUDENT_PROFILES_FILE_PATH
from configure_logger import backend_logger
from langchain_core.messages import AIMessage, HumanMessage
from typing import Optional, Tuple

def create_main_database() -> Tuple[bool, str]:
    success = False
    message = ""

    try:
        with mariadb.connect(user=DB_CONFIG["user"], password=DB_CONFIG["password"], host=DB_CONFIG["host"]) as db_conn:
            with db_conn.cursor() as cursor:
                cursor.execute(f"DROP DATABASE IF EXISTS {DB_CONFIG['database']}")
                cursor.execute(f"CREATE DATABASE {DB_CONFIG['database']}")
        success = True
        message = "Database creation successful"
        backend_logger.info(f"create_main_database | {message}")
    except mariadb.Error as e:
        message = f"Error creating main database: {e}"
        backend_logger.error(f"create_main_database | {message}")

    return success, message

def get_db_connection() -> Tuple[bool, str, Optional[mariadb.Connection]]:
    success = False
    message = ""
    conn = None

    try:
        conn = mariadb.connect(**DB_CONFIG)
        success = True
        message = "Database connection successful"
        backend_logger.info(f"get_db_connection | {message}")
        return success, message, conn
    except mariadb.Error as e:
        if conn:
            conn.close()
        message = f"Database connection error: {e}"
        backend_logger.error(f"get_db_connection | {message}")
        return success, message, conn

def create_student_profile_table() -> Tuple[bool, str]:
    success = False
    message = ""
    get_db_conn_success, get_db_conn_message, conn = get_db_connection()
    if not get_db_conn_success:
        message = f"Error creating student profile table: {get_db_conn_message}"
        backend_logger.error(f"create_student_profile_table | {message}")
        return success, message
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    '''
                        CREATE TABLE IF NOT EXISTS student_profile
                        (
                            id SERIAL PRIMARY KEY,
                            name VARCHAR(100) NOT NULL,
                            sex ENUM('male','female') NOT NULL,
                            age INT DEFAULT NULL,
                            state VARCHAR(50) NOT NULL,
                            image VARCHAR(255) DEFAULT NULL
                        )
                    '''
                )
        success = True
        message = "Student profile table created successfully"
        backend_logger.info(f"create_student_profile_table | {message}")
    except mariadb.Error as e:
        message = f"Error creating student profile table: {e}"
        backend_logger.error(f"create_student_profile_table | {message}")
    return success, message

def create_chat_message_table() -> Tuple[bool, str]:
    success = False
    message = ""
    get_db_conn_success, get_db_conn_message, conn = get_db_connection()
    if not get_db_conn_success:
        message = f"Error creating chat message table: {get_db_conn_message}"
        backend_logger.error(f"create_chat_message_table | {message}")
        return success, message
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    '''
                        CREATE TABLE IF NOT EXISTS chat_message
                        (
                            id SERIAL PRIMARY KEY,
                            login_session_id CHAR(64) NOT NULL,
                            chat_session_id CHAR(64) NOT NULL,
                            role ENUM('user','assistant') NOT NULL,
                            message TEXT NOT NULL,
                            input_type ENUM('manual','button','default') DEFAULT 'default',
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    '''
                )
        success = True
        message = "Chat message table created successfully"
        backend_logger.info(f"create_chat_message_table | {message}")
    except mariadb.Error as e:
        message = f"Error creating chat history table: {e}"
        backend_logger.error(f"create_chat_message_table | {message}")
    return success, message

def get_single_student_profile(name: str) -> Tuple[bool, str, Optional[bool], dict]:
    success = False
    message = ""
    result = False
    data = {}
    
    get_db_conn_success, get_db_conn_message, conn = get_db_connection()
    if not get_db_conn_success:
        message = f"Error getting student profile for name: {name}: {get_db_conn_message}"
        backend_logger.error(f"get_single_student_profile | {message}")
        return success, message, result, data
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    '''
                        SELECT name, sex, age, state, image
                        FROM student_profile
                        WHERE name = %s
                    ''',
                    (name,)
                )
                fetch_result = cursor.fetchone()
                if fetch_result:
                    success = True
                    message = f"Student profile found for name: {name}"
                    result = True
                    data = {
                        "name": fetch_result[0],
                        "sex": fetch_result[1],
                        "age": fetch_result[2],
                        "state": fetch_result[3],
                        "image": fetch_result[4]
                    }
                    backend_logger.info(f"get_single_student_profile | {message}")
                else:
                    success = True
                    message = f"Student profile not found for name: {name}"
                    backend_logger.info(f"get_single_student_profile | {message}")
    except mariadb.Error as e:
        message = f"Error getting student profile for name: {name}: {e}"
        backend_logger.error(f"get_single_student_profile | {message}")
    return success, message, result, data

def get_student_profiles(count: int = 8) -> Tuple[bool, str, Optional[bool], list]:
    success = False
    message = ""
    result = False
    data = []

    get_db_conn_success, get_db_conn_message, conn = get_db_connection()
    if not get_db_conn_success:
        message = f"Error connecting to database to get {count} student profiles: {get_db_conn_message}"
        backend_logger.error(f"get_student_profiles | {message}")
        return success, message, result, data
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f'''
                        SELECT name, sex, age, state, image
                        FROM student_profile
                        LIMIT %s
                    ''',
                    (count,)
                )
                data = []
                for name, sex, age, state, image in cursor.fetchall():
                    data.append({
                        "name": name,
                        "sex": sex,
                        "age": age,
                        "state": state,
                        "image": image
                    })
                random.shuffle(data)
                result = len(data) > 0
                success = True
                message = f"Retrieved {len(data)} student profiles successfully"
                if not result:
                    message = f"No student profiles found for a request to get {count} student profiles"
                    backend_logger.info(f"get_student_profiles | {message}")
                else:
                    backend_logger.info(f"get_student_profiles | {message}")
    except mariadb.Error as e:
        message = f"Error getting {count} student profiles: {e}"
        backend_logger.error(f"get_student_profiles | {message}")
    return success, message, result, data

def insert_student_profile(name: str, sex: str, age: int, state: str, image: str) -> Tuple[bool, str, Optional[bool], Optional[int]]:
    success = False
    message = ""
    result = False
    data = None
    valid_sexes = ['male', 'female']
    if sex.lower() not in valid_sexes:
        message = f"Invalid sex: '{sex}' for student: '{name}'. Must be one of: {', '.join(valid_sexes)}"
        backend_logger.error(f"insert_student_profile | {message}")
        return success, message, result, data
    
    if age < 0:
        message = f"Invalid age: '{age}' for student: '{name}'. Must be greater than 0"
        backend_logger.error(f"insert_student_profile | {message}")
        return success, message, result, data
    
    valid_states = [
        "andhra-pradesh",
        "arunachal-pradesh",
        "assam",
        "bihar",
        "chhattisgarh",
        "goa",
        "gujarat",
        "haryana",
        "himachal-pradesh",
        "jammu-kashmir",
        "jharkhand",
        "karnataka",
        "kerala",
        "madhya-pradesh",
        "maharashtra",
        "manipur",
        "meghalaya",
        "mizoram",
        "nagaland",
        "odisha",
        "punjab",
        "rajasthan",
        "sikkim",
        "tamil-nadu",
        "telangana",
        "tripura",
        "uttar-pradesh",
        "uttarakhand",
        "west-bengal"
    ]

    if state.lower().replace(' ', '-') not in valid_states:
        message = f"Invalid state: '{state}' for student: '{name}'. Must be one of: {', '.join(valid_states)}"
        backend_logger.error(f"insert_student_profile | {message}")
        return success, message, result, data
    
    get_db_conn_success, get_db_conn_message, conn = get_db_connection()
    if not get_db_conn_success:
        message = f"Error inserting student profile for name: {name}: {get_db_conn_message}"
        backend_logger.error(f"insert_student_profile | {message}")
        return success, message, result, data
    
    try:
        get_student_success, get_student_message, get_student_result, _ = get_single_student_profile(name)
        if not get_student_success:
            message = f"Error getting student profile for name: {name}: {get_student_message}"
            backend_logger.error(f"insert_student_profile | {message}")
            return success, message, result, data
        if get_student_result:
            success = True
            message = f"Student profile already exists for name: {name}"
            backend_logger.info(f"insert_student_profile | {message}")
            return success, message, result, data
        with conn.cursor() as cursor:
            cursor.execute(
                '''
                    INSERT INTO student_profile (name, sex, age, state, image)
                    VALUES (%s, %s, %s, %s, %s)
                ''',
                (name, sex, age, state, image)
            )
            conn.commit()
            data = cursor.lastrowid
            if data:
                success = True
                message = f"Student profile {name} inserted successfully"
                result = True
                backend_logger.info(f"insert_student_profile | {message}")
            else:
                success = False
                message = f"Error inserting student profile for name: {name}"
                backend_logger.error(f"insert_student_profile | {message}")
    except mariadb.Error as e:
        conn.rollback()
        message = f"Error inserting student profile for name: {name}: {e}"
        backend_logger.error(f"insert_student_profile | {message}")
    return success, message, result, data
    
def populate_student_profile_table() -> Tuple[bool, str]:
    success = False
    message = ""
    try:
        with open(STUDENT_PROFILES_FILE_PATH, 'r') as f:
            students_profiles = json.load(f)
            for student_profile in students_profiles:
                name = student_profile.get('name')
                sex = student_profile.get('sex')
                age = student_profile.get('age', None)
                state = student_profile.get('state')
                image = student_profile.get('image', None)
                insert_student_success, insert_student_message, insert_student_result, _ = insert_student_profile(name, sex, age, state, image)
                if not insert_student_success:
                    message = f"Error inserting student profile for name: {name}: {insert_student_message}"
                    backend_logger.error(f"populate_student_profile_table | {message}")
                if not insert_student_result:
                    message = f"Error inserting student profile for name: {name}: {insert_student_message}"
                    backend_logger.error(f"populate_student_profile_table | {message}")
            success = True
            message = f"Student profile table populated successfully with {len(students_profiles)} student profiles"
            backend_logger.info(f"populate_student_profile_table | {message}")
    except FileNotFoundError as e:
        message = f"Error populating student profile table with students.json file: {e}"
        backend_logger.error(f"populate_student_profile_table | {message}")
    except json.JSONDecodeError as e:
        message = f"Error populating student profile table with students.json file: {e}"
        backend_logger.error(f"populate_student_profile_table | {message}")
    except Exception as e:
        message = f"Error populating student profile table with students.json file: {e}"
        backend_logger.error(f"populate_student_profile_table | {message}")
    return success, message

def insert_chat_message(login_session_id: str, chat_session_id: str, user_input: str, input_type: str, assistant_output: str) -> Tuple[bool, str]:
    success = False
    message = ""

    valid_input_types = ['manual', 'button', 'default']
    if input_type not in valid_input_types:
        message = f"Invalid input_type: '{input_type}'. Must be one of: {', '.join(valid_input_types)}"
        backend_logger.error(f"insert_chat_message | {message}")
        return success, message

    get_db_conn_success, get_db_conn_message, conn = get_db_connection()
    if not get_db_conn_success:
        message = f"Error inserting chat message: {get_db_conn_message}"
        backend_logger.error(f"insert_chat_message | {message}")
        return success, message
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                '''
                    INSERT INTO chat_message (login_session_id, chat_session_id, role, message, input_type)
                    VALUES (%s, %s, 'user', %s, %s)
                ''',
                (login_session_id, chat_session_id, user_input, input_type)
            )
            cursor.execute(
                '''
                    INSERT INTO chat_message (login_session_id, chat_session_id, role, message)
                    VALUES (%s, %s, 'assistant', %s)
                ''',
                (login_session_id, chat_session_id, assistant_output)
            )
            conn.commit()
        success = True
        message = "Chat history inserted successfully"
        backend_logger.info(f"insert_chat_message | {message}")
    except mariadb.Error as e:
        conn.rollback()
        message = f"Error inserting chat history: {e}"
        backend_logger.error(f"insert_chat_message | {message}")
    finally:
        conn.close()
    return success, message
    
def get_chat_history(login_session_id: str, chat_session_id: str) -> Tuple[bool, str, Optional[bool], list]:
    success = False
    message = ""
    result = False
    data = []

    if not login_session_id or not chat_session_id:
        message = "Login session id and chat session id are required"
        backend_logger.error(f"get_chat_history | {message}")
        return success, message, result, data
    
    get_db_conn_success, get_db_conn_message, conn = get_db_connection()
    if not get_db_conn_success:
        message = f"Error getting chat history: {get_db_conn_message}"
        backend_logger.error(f"get_chat_history | {message}")
        return success, message, result, data
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    '''
                        SELECT role, message
                        FROM chat_message
                        WHERE login_session_id = %s AND chat_session_id = %s
                        ORDER BY created_at
                    ''',
                    (login_session_id, chat_session_id)
                )
                messages = []
                for role, msg in cursor.fetchall():
                    if msg and msg.strip():
                        if role == 'user':
                            messages.append(HumanMessage(content=msg))
                        elif role == 'assistant':
                            messages.append(AIMessage(content=msg))
                    else:
                        backend_logger.warning(f"get_chat_history | Skipping invalid message with empty content from role: {role} during login session id: {login_session_id} and chat session id: {chat_session_id}")
        if len(messages) == 0:
            success = True
            message = "Chat history not found for the given login session id and chat session id"
            backend_logger.info(f"get_chat_history | {message}")
        else:
            success = True
            message = "Chat history found for the given login session id and chat session id"
            result = True
            data = messages
            backend_logger.info(f"get_chat_history | {message}")
    except mariadb.Error as e:
        message = f"Error getting chat history: {str(e)}"
        backend_logger.error(f"get_chat_history | {message}")
    return success, message, result, data

if __name__ == "__main__":
    pass