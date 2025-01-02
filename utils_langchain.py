import os

from dotenv import load_dotenv
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from utils_vectorstore import rag_vectorstore

load_dotenv()

temperature = float(os.getenv("LLM_TEMPERATURE", 0.5))
max_tokens = int(os.getenv("LLM_MAX_TOKENS", 200))
documents_to_retrieve = int(os.getenv("RAG_MAX_DOC_RETRIEVE", 3))
model = os.getenv("GENERATION_MODEL_ID", "gpt-4o-mini")

retriever = rag_vectorstore.as_retriever(search_kwargs={"k": documents_to_retrieve})

output_parser = StrOutputParser()

contextualize_q_system_prompt = """
Given a chat history and the latest user question, it is important that you formulate a standalone question that can be understood without relying on the chat history.
Do not make up facts or assumptions when reformulating the question—stay true to the context provided.
You must not answer the question itself. If reformulation is not needed, simply return the question as is.
Always ensure the reformulated question is clear, self-contained, and accurately represents the original intent.
"""

contextualize_q_prompt = ChatPromptTemplate.from_messages([("system", contextualize_q_system_prompt), MessagesPlaceholder("chat_history"),("human", "{input}")])

qa_prompt = ChatPromptTemplate.from_messages([
    ("system", """
     You are a student at Agastya International Foundation. It is important that you remain polite and respectful in all your responses. Keep your answers concise and focus strictly on what is asked—do not add unnecessary information or make up facts.
     You must only respond to questions about yourself and your experience as a student at Agastya International Foundation. If you don’t know the answer, say so politely. If a question is inappropriate, respond respectfully but make it clear that you cannot answer it.
     Refer to previous conversational messages when answering repeated questions. Answer in an innocent and optimistic tone, like a child would.
     Remember to follow these instructions carefully in every response."""),
    ("system", "Context: {context}"),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}")
])

def get_rag_chain(model, retriever):
    llm = ChatOpenAI(model=model, temperature=temperature, max_tokens=max_tokens)
    retriever = retriever
    history_aware_retriever = create_history_aware_retriever(llm, retriever, contextualize_q_prompt)
    question_answer_chain = create_stuff_documents_chain(llm=llm, prompt=qa_prompt)
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
    return rag_chain