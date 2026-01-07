from fastapi import FastAPI, UploadFile, File, HTTPException
import shutil
import os
from typing import Dict

from .schemas import IngestResponse, ChatRequest, ChatResponse, ClearHistoryRequest, ClearHistoryResponse
from .ingestion import ingest_pdf
from .retrieval import answer_question
from .memory import clear_history, CHAT_MEMORY

app = FastAPI(title="Manufacturing Manual RAG API")

@app.post("/ingest", response_model=IngestResponse)
async def ingest_endpoint(file: UploadFile = File(...)):
    """Ingest a manufacturing manual PDF"""
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    os.makedirs("data/uploads", exist_ok=True)
    file_path = f"data/uploads/{file.filename}"

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        chunks, chunk_types = ingest_pdf(file_path)
        
        return {
            "status": "success", 
            "chunks_added": chunks,
            "chunk_types": chunk_types,
            "message": f"Successfully processed {file.filename}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    """Ask questions about manufacturing manuals"""
    try:
        answer, sources = answer_question(
            session_id=request.session_id,
            question=request.question
        )

        return {
            "answer": answer, 
            "sources": sources,
            "context_used": len(sources)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process question: {str(e)}")

@app.post("/clear_history", response_model=ClearHistoryResponse)
def clear_history_endpoint(request: ClearHistoryRequest):
    """Clear conversation history for a session"""
    success = clear_history(request.session_id)
    
    if success:
        return {
            "status": "success",
            "message": f"History cleared for session {request.session_id}"
        }
    else:
        return {
            "status": "not_found",
            "message": f"No history found for session {request.session_id}"
        }

@app.get("/session_info/{session_id}")
def get_session_info(session_id: str):
    """Get information about a session"""
    from .memory import get_history
    
    history = get_history(session_id)
    
    return {
        "session_id": session_id,
        "message_count": len(history),
        "exchange_count": len(history) // 2,
        "active": len(history) > 0
    }

@app.get("/stats")
def get_stats():
    """Get system statistics"""
    total_sessions = len(CHAT_MEMORY)
    total_messages = sum(len(msgs) for msgs in CHAT_MEMORY.values())
    
    # Check vector store
    from .vectorstore import get_vectorstore
    try:
        db = get_vectorstore()
        collection = db.get()
        doc_count = len(collection['ids']) if collection['ids'] else 0
    except:
        doc_count = 0
    
    return {
        "active_sessions": total_sessions,
        "total_messages": total_messages,
        "documents_in_db": doc_count,
        "memory_size": sum(len(str(msgs)) for msgs in CHAT_MEMORY.values())
    }