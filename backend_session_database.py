import mariadb

from backend_config import DB_CONFIG
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