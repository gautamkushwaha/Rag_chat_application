from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class IngestResponse(BaseModel):
    status: str
    chunks_added: int
    chunk_types: Dict[str, int] = {}
    message: Optional[str] = None

class ChatRequest(BaseModel):
    session_id: str
    question: str
    question_type: Optional[str] = None  # Optional override

class ChatResponse(BaseModel):
    answer: str
    sources: List[str]
    question_type: Optional[str] = None  # For debugging
    context_used: Optional[int] = None   # Number of chunks used
    
class ClearHistoryRequest(BaseModel):
    session_id: str

class ClearHistoryResponse(BaseModel):
    status: str
    message: str