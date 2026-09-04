import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, HTTPException, Form, status
from pydantic import BaseModel, Field

from app.config import RAW_DIR
from app.db import init_db, list_papers, get_paper
from app.rag.ingestion import ingest_pdf_paper
from app.rag.rag_qa import ask
from app.agents.research_agent import run_full_pipeline
from app.agents.agent_executor import run_agent


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    init_db()
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    yield
    # Shutdown logic


app = FastAPI(
    title="ResearchPilot API",
    description="Local AI Research Assistant web backend with Multi-Paper RAG & Pipeline support",
    version="1.0.0",
    lifespan=lifespan,
)


class AskRequest(BaseModel):
    paper_id: str = Field(..., description="ID of the paper collection to query")
    question: str = Field(..., description="User question about the paper")
    mode: str = Field("rag", description="Mode: 'rag' or 'pipeline'")


class AgentAskRequest(BaseModel):
    paper_id: str = Field(..., description="ID of the paper collection to query")
    question: str = Field(..., description="User question for the native agent")


@app.get("/")
def read_root():
    return {"message": "Welcome to ResearchPilot API", "status": "online", "docs": "/docs"}


@app.post("/papers/upload", status_code=status.HTTP_201_CREATED)
async def upload_paper(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported.",
        )

    paper_id = str(uuid.uuid4())
    save_path = RAW_DIR / file.filename

    # Save PDF locally
    with open(save_path, "wb") as buffer:
        shutil_content = await file.read()
        buffer.write(shutil_content)

    # Ingest and store chunks
    try:
        paper_id, chunk_count = ingest_pdf_paper(save_path, paper_id=paper_id, title=title)
        paper_meta = get_paper(paper_id)
        return {
            "message": "Paper uploaded and ingested successfully",
            "paper_id": paper_id,
            "filename": file.filename,
            "title": paper_meta["title"] if paper_meta else title or file.filename,
            "chunk_count": chunk_count,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest paper: {str(e)}",
        )


@app.get("/papers", response_model=List[Dict[str, Any]])
def get_papers():
    return list_papers()


@app.post("/ask")
def ask_question(request: AskRequest):
    paper = get_paper(request.paper_id)
    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paper with ID '{request.paper_id}' not found.",
        )

    if request.mode not in {"rag", "pipeline"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid mode. Must be 'rag' or 'pipeline'.",
        )

    if request.mode == "pipeline":
        pipeline_output = run_full_pipeline(request.question, paper_id=request.paper_id)
        return {
            "paper_id": request.paper_id,
            "question": request.question,
            "mode": "pipeline",
            "result": pipeline_output,
        }
    else:
        answer = ask(request.question, paper_id=request.paper_id)
        return {
            "paper_id": request.paper_id,
            "question": request.question,
            "mode": "rag",
            "answer": answer,
        }


@app.post("/ask-agent")
def ask_agent(request: AgentAskRequest):
    paper = get_paper(request.paper_id)
    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paper with ID '{request.paper_id}' not found.",
        )

    agent_output = run_agent(request.question, paper_id=request.paper_id)
    return {
        "paper_id": request.paper_id,
        "question": request.question,
        "mode": "agent",
        "answer": agent_output.get("answer", ""),
        "steps": agent_output.get("steps", []),
    }
