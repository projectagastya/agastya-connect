import mariadb
import os

from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {"user": os.getenv("DB_USERNAME"), "password": os.getenv("DB_PASSWORD"), "host": os.getenv("DB_HOST"), "database": os.getenv("DB_NAME")}

def get_db_connection():
    conn = mariadb.connect(**DB_CONFIG)
    return conn

def create_database():
    conn = mariadb.connect(user=DB_CONFIG["user"], password=DB_CONFIG["password"], host=DB_CONFIG["host"])
    cursor = conn.cursor()
    cursor.execute(f"DROP DATABASE IF EXISTS {DB_CONFIG['database']}")
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
    conn.close()

def create_chat_history():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS chat_history (
                        serial_number INT AUTO_INCREMENT PRIMARY KEY,
                        chat_session_id VARCHAR(255) NOT NULL,
                        user_input TEXT,
                        ai_output TEXT,
                        model VARCHAR(50),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )''')
    
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_chat_session_id ON chat_history(chat_session_id)')
    conn.commit()
    conn.close()

def insert_chat_history(chat_session_id, user_input, ai_output, model="gpt-4o-mini"):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO chat_history (chat_session_id, user_input, ai_output, model) VALUES (%s, %s, %s, %s)',
                       (chat_session_id, user_input, ai_output, model))
        conn.commit()
    finally:
        conn.close()

def get_chat_history(chat_session_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT user_input, ai_output FROM chat_history WHERE chat_session_id = %s ORDER BY created_at', 
                        (chat_session_id,))
        messages = []
        for row in cursor.fetchall():
            messages.extend([
                {"role": "human", "content": row[0]},
                {"role": "ai", "content": row[1]}
            ])
        return messages
    finally:
        conn.close()

def create_document_store():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS document_store (
                        document_id INT AUTO_INCREMENT PRIMARY KEY,
                        chat_session_id VARCHAR(255) UNIQUE,
                        filename VARCHAR(255),
                        upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_chat_session_id ON document_store(chat_session_id)')
    conn.commit()
    conn.close()

def insert_session_document(chat_session_id, filename):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO document_store (chat_session_id, filename) VALUES (%s, %s)',
                       (chat_session_id, filename))
        conn.commit()
        return cursor.lastrowid
    except mariadb.Error as e:
        print(f"Error indexing document: {e}")
        return None
    finally:
        conn.close()

def get_session_document(chat_session_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT document_id, chat_session_id, filename, upload_timestamp FROM document_store WHERE chat_session_id = %s ORDER BY upload_timestamp DESC', 
                    (chat_session_id,))
        return [{"document_id": row[0], "chat_session_id": row[1], "filename": row[2], "upload_timestamp": row[3]} for row in cursor.fetchall()]
    finally:
        conn.close()

def get_all_documents(limit=100, offset=0):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT document_id, chat_session_id, filename, upload_timestamp FROM document_store ORDER BY upload_timestamp DESC LIMIT %s OFFSET %s', 
                       (limit, offset))
        return [{"document_id": row[0], "chat_session_id": row[1], "filename": row[2], "upload_timestamp": row[3]} for row in cursor.fetchall()]
    finally:
        conn.close()

def delete_session_document(chat_session_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM document_store WHERE chat_session_id = %s', (chat_session_id,))
        conn.commit()
        return True
    finally:
        conn.close()

def delete_all_documents():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM document_store')
        conn.commit()
        return True
    finally:
        conn.close()