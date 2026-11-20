from dotenv import load_dotenv
from langchain_ollama import OllamaEmbeddings
from langchain_openai import ChatOpenAI
from langchain_chroma import Chroma
from langchain_classic.chains import RetrievalQA
from langchain_classic.prompts import PromptTemplate
import os
import uuid
import subprocess
from pypdf import PdfReader

DOWNLOAD_DIR = "/Users/kyesteele/dev/document-library-cag/Downloads"

def find_file_in_downloads(filename):
    base = os.path.splitext(filename)[0]
    if not os.path.exists(DOWNLOAD_DIR):
        return None
    for f in os.listdir(DOWNLOAD_DIR):
        if os.path.splitext(f)[0] == base:
            return os.path.join(DOWNLOAD_DIR, f)
    return None

def get_pdf_title(file_path):
    try:
        reader = PdfReader(file_path)
        meta = reader.metadata
        if meta and meta.title:
            return meta.title.strip()
        return os.path.splitext(os.path.basename(file_path))[0]
    except Exception:
        return os.path.splitext(os.path.basename(file_path))[0]

def get_qa_chain():
    load_dotenv()
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    vector_db = Chroma(
        persist_directory='chromadb',
        embedding_function=embeddings
    )
    retriever = vector_db.as_retriever(search_kwargs={"k": 8})
    prompt = PromptTemplate(
        input_variables=["context", "question"],
        template="""You are a helpful assistant. Use ONLY the context below.\n\nContext:\n{context}\n\nQuestion:\n{question}\n\nAnswer:"""
    )
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    return RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type="stuff",
        chain_type_kwargs={"prompt": prompt}
    )

load_dotenv()
chain = get_qa_chain()
