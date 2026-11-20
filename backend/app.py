from dotenv import load_dotenv
from langchain_ollama import OllamaEmbeddings
from langchain_openai import ChatOpenAI
from langchain_chroma import Chroma
from langchain_classic.chains import RetrievalQA
from langchain_classic.prompts import PromptTemplate

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import os
from pypdf import PdfReader

DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "downloads")
CHROMA_DIR = os.getenv("CHROMA_DIR", "chromadb")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

load_dotenv()

app = FastAPI(title="Document Library Chat API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)


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
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL, base_url=OLLAMA_BASE_URL)

    vector_db = Chroma(
        persist_directory="CHROMA_DIR",
        embedding_function=embeddings,
    )

    retriever = vector_db.as_retriever(
        search_kwargs={"k": 8}
    )

    prompt = PromptTemplate(
        input_variables=["context", "question"],
        template="""You are a helpful assistant. Use ONLY the context below.

Context:
{context}

Question:
{question}

Answer:""",
    )

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
    )

    return RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type="stuff",
        return_source_documents=True,
        chain_type_kwargs={"prompt": prompt},
    )

chain = get_qa_chain()

class ChatRequest(BaseModel):
    question: str


# all of retrieval and response
@app.post("/api/chat")
def chat(request: ChatRequest):
    question = request.question.strip()

    if not question:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty",
        )

    response = chain.invoke({"query": question})

    sources = []

    for doc in response["source_documents"]:
        source_path = doc.metadata.get("source", "Unknown")
        filename = os.path.basename(source_path)

        file_path = find_file_in_downloads(source_path)
        display_name = filename

        if file_path and file_path.lower().endswith(".pdf"):
            display_name = get_pdf_title(file_path)

        sources.append({
            "source": source_path,
            "filename": filename,
            "title": display_name,
            "page": doc.metadata.get("page"),
            "snippet": doc.page_content,
            "file_path": file_path,
        })

    return {
        "answer": response["result"],
        "sources": sources,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
