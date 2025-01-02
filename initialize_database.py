from session_database import create_database, create_chat_history, create_document_store

if __name__ == "__main__":
    create_database()
    create_chat_history()
    create_document_store()