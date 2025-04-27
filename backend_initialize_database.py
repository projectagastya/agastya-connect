from backend.utils import create_chat_message_table, create_chat_session_table, create_student_table, populate_student_table
from shared.logger import backend_logger

def initialize_all_databases() -> tuple[bool, str]:
    success = False
    message = ""

    create_student_table_success, create_student_table_message = create_student_table()
    if not create_student_table_success:
        message = f"Failed to create DynamoDB tables: {create_student_table_message}"
        backend_logger.error(f"initialize_all_databases | {message}")
        return success, message
    
    populate_student_table_success, populate_student_table_message = populate_student_table()
    if not populate_student_table_success:
        message = f"Failed to populate student profiles: {populate_student_table_message}"
        backend_logger.error(f"initialize_all_databases | {populate_student_table_message}")
        return success, message
    
    create_chat_message_table_success, create_chat_message_table_message = create_chat_message_table()
    if not create_chat_message_table_success:
        message = f"Failed to create chat message table: {create_chat_message_table_message}"
        backend_logger.error(f"initialize_all_databases | {message}")
        return success, message
    
    create_chat_session_table_success, create_chat_session_table_message = create_chat_session_table()
    if not create_chat_session_table_success:
        message = f"Failed to create chat session table: {create_chat_session_table_message}"
        backend_logger.error(f"initialize_all_databases | {message}")
        return success, message
    
    return True, "Database initialization completed successfully"
    
if __name__ == "__main__":
    success, message = initialize_all_databases()
    if success:
        backend_logger.info("All databases have been initialized successfully")
    else:
        backend_logger.error(f"Database initialization failed: {message}")