import os

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader, UnstructuredHTMLLoader
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List

load_dotenv()

RAG_VECTORSTORE_PERSIST_DIRECTORY = os.getenv("RAG_VECTORSTORE_PERSIST_DIRECTORY", "vectorstores/rag-documents")
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200, length_function=len)
embedding_function = OpenAIEmbeddings()
rag_vectorstore = Chroma(persist_directory=RAG_VECTORSTORE_PERSIST_DIRECTORY, embedding_function=embedding_function)

def load_and_split_document(file_path: str) -> List[Document]:
    if file_path.endswith('.pdf'):
        loader = PyPDFLoader(file_path)
    elif file_path.endswith('.docx'):
        loader = Docx2txtLoader(file_path)
    elif file_path.endswith('.html'):
        loader = UnstructuredHTMLLoader(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_path}")
    documents = loader.load()
    return text_splitter.split_documents(documents)

def index_document_to_vectorstore(file_path: str, file_id: int, chat_session_id: str) -> bool:
    splits = load_and_split_document(file_path)
    for split in splits:
        split.metadata['chat_session_id'] = chat_session_id
        split.metadata['file_id'] = file_id
    rag_vectorstore.add_documents(splits)
    return True

def delete_doc_from_vectorstore(chat_session_id: str):
    rag_vectorstore._collection.delete(where={"chat_session_id": chat_session_id})
    return True