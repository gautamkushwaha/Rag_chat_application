from langchain_core.messages import HumanMessage, AIMessage
from typing import List, Dict

# session_id → messages
CHAT_MEMORY = {}
MAX_HISTORY_LENGTH = 10  # Keep last 5 exchanges

def get_history(session_id: str) -> List:
    """Get conversation history with automatic pruning"""
    history = CHAT_MEMORY.setdefault(session_id, [])
    
    # Automatically prune if too long
    if len(history) > MAX_HISTORY_LENGTH * 2:  # *2 for user+assistant pairs
        history = history[-MAX_HISTORY_LENGTH*2:]
        CHAT_MEMORY[session_id] = history
    
    return history

def add_to_history(session_id: str, user: str, ai: str):
    """Add to history with automatic summarization for long conversations"""
    history = get_history(session_id)
    
    # Add new messages
    history.append(HumanMessage(content=user))
    history.append(AIMessage(content=ai))
    
    # Keep within limit
    if len(history) > MAX_HISTORY_LENGTH * 2:
        CHAT_MEMORY[session_id] = history[-MAX_HISTORY_LENGTH*2:]

def clear_history(session_id: str):
    """Clear conversation history for a session"""
    if session_id in CHAT_MEMORY:
        del CHAT_MEMORY[session_id]
        return True
    return False

def get_recent_history(session_id: str, num_exchanges: int = 3) -> List:
    """Get recent conversation history (last N exchanges)"""
    history = get_history(session_id)
    return history[-num_exchanges*2:] if history else []
