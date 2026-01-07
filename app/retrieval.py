from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from .vectorstore import get_vectorstore
from .memory import get_history, add_to_history
from dotenv import load_dotenv
from typing import List, Tuple
import re

load_dotenv()

# Initialize LLM with manufacturing-appropriate settings
llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0.1,  # Low temperature for precise, factual answers
    max_tokens=1000
)

def classify_question(question: str) -> str:
    """Classify manufacturing questions for better retrieval"""
    question_lower = question.lower()
    
    if any(word in question_lower for word in ['safety', 'warning', 'caution', 'danger', 'risk', 'hazard']):
        return "safety"
    elif any(word in question_lower for word in ['step', 'procedure', 'how to', 'install', 'assemble', 'maintenance', 'operation']):
        return "procedure"
    elif any(word in question_lower for word in ['error', 'fault', 'troubleshoot', 'fix', 'problem', 'alarm', 'diagnose']):
        return "troubleshooting"
    elif any(word in question_lower for word in ['spec', 'parameter', 'setting', 'value', 'torque', 'rpm', 'pressure', 'temperature', 'voltage']):
        return "specification"
    elif any(word in question_lower for word in ['what is', 'define', 'explain', 'meaning', 'purpose']):
        return "definition"
    else:
        return "general"

def answer_question(session_id: str, question: str) -> Tuple[str, List[str]]:
    """Enhanced Q&A for manufacturing manuals"""
    # Get vector store
    db = get_vectorstore("manufacturing_manuals")
    
    # Enhanced retriever with manufacturing focus
    retriever = db.as_retriever(
        search_type="mmr",  # Maximal Marginal Relevance
        search_kwargs={
            "k": 6,
            "score_threshold": 0.5,
            "fetch_k": 15,
            "lambda_mult": 0.7
        }
    )
    
    # Get conversation history
    history = get_history(session_id)
    
    # Classify question
    question_type = classify_question(question)
    print(f"🔍 Question type: {question_type}")
    
    # Query rewriting for better retrieval
    if history and len(history) > 0:
        rewrite_prompt = f"""
        Rewrite this manufacturing question to be standalone and optimized for search.
        
        Conversation context (last 2 exchanges):
        {format_history(history[-4:]) if len(history) >= 4 else "No relevant history"}
        
        Current question: {question}
        
        Question type: {question_type}
        
        Rewrite to include relevant manufacturing keywords for better document retrieval.
        Keep it concise and clear.
        
        Rewritten question:"""
        
        enhanced_question = llm.invoke([HumanMessage(content=rewrite_prompt)]).content
    else:
        enhanced_question = question
    
    print(f"🔍 Searching for: {enhanced_question}")
    
    # Retrieve documents
    docs = retriever.invoke(enhanced_question)
    
    # Priority filtering for manufacturing
    filtered_docs = []
    for doc in docs:
        doc_type = doc.metadata.get("chunk_type", "")
        doc_priority = doc.metadata.get("priority", "medium")
        
        # Safety questions: prioritize safety chunks
        if question_type == "safety" and doc_type == "safety":
            filtered_docs.insert(0, doc)
        # Procedure questions: prioritize procedure steps
        elif question_type == "procedure" and "procedure" in doc_type:
            filtered_docs.insert(0, doc)
        # High priority safety content always important
        elif doc_priority == "high":
            filtered_docs.insert(min(1, len(filtered_docs)), doc)
        else:
            filtered_docs.append(doc)
    
    # Take top 4 most relevant
    filtered_docs = filtered_docs[:4]
    
    # Build context
    context_parts = []
    for i, doc in enumerate(filtered_docs):
        source_info = []
        if "source" in doc.metadata:
            source_info.append(f"Source: {doc.metadata['source']}")
        if "page" in doc.metadata:
            source_info.append(f"Page: {doc.metadata['page']}")
        
        source_str = f"[{', '.join(source_info)}]" if source_info else ""
        
        context_parts.append(f"""
        DOCUMENT {i+1} {source_str}:
        {doc.page_content}
        """)
    
    context = "\n---\n".join(context_parts)
    
    # Build manufacturing-specific prompt
    prompt = build_manufacturing_prompt(context, enhanced_question, question_type)
    
    # Generate answer
    answer = llm.invoke([HumanMessage(content=prompt)]).content
    
    # Extract sources
    sources = []
    seen = set()
    for doc in filtered_docs:
        source = doc.metadata.get("source", "")
        page = doc.metadata.get("page", "")
        if source:
            source_str = f"{source} (page {page})" if page else source
            if source_str not in seen:
                sources.append(source_str)
                seen.add(source_str)
    
    # Update history
    add_to_history(session_id, enhanced_question, answer)
    
    return answer, sources[:3]  # Return top 3 unique sources

def format_history(history: List) -> str:
    """Format conversation history"""
    formatted = []
    for i, msg in enumerate(history):
        if i % 2 == 0:
            formatted.append(f"User: {msg.content}")
        else:
            formatted.append(f"Assistant: {msg.content}")
    return "\n".join(formatted)

def build_manufacturing_prompt(context: str, question: str, q_type: str) -> str:
    """Build specialized prompt for manufacturing Q&A"""
    
    # Type-specific instructions
    instructions = {
        "safety": """
        CRITICAL SAFETY INSTRUCTIONS:
        - Always start with safety warnings if present
        - List ALL safety precautions mentioned
        - Use clear warning symbols ⚠️ for dangers
        - Be explicit about risks and consequences
        - Never omit or minimize safety information
        """,
        "procedure": """
        PROCEDURE INSTRUCTIONS:
        - List steps in exact numerical order
        - Include required tools and materials
        - Mention safety steps before procedure steps
        - Include verification/check steps
        - Be precise with measurements and settings
        """,
        "troubleshooting": """
        TROUBLESHOOTING INSTRUCTIONS:
        - List possible causes from most to least likely
        - Include diagnostic steps to identify the issue
        - Provide clear resolution steps
        - Mention any required tools or parts
        - State when professional help is needed
        """,
        "specification": """
        SPECIFICATION INSTRUCTIONS:
        - Provide exact values with units
        - Include acceptable ranges if specified
        - Mention measurement conditions if relevant
        - Reference the exact source document
        """,
        "definition": """
        DEFINITION INSTRUCTIONS:
        - Provide clear, concise definitions
        - Include context from the manual
        - Mention related terms if applicable
        - Reference the source document
        """
    }
    
    type_instructions = instructions.get(q_type, """
    GENERAL INSTRUCTIONS:
    - Be precise and technical
    - Include specific values when available
    - Cite the source document for key information
    - If information is incomplete, state what's missing
    """)
    
    prompt = f"""You are a manufacturing automation expert answering questions from technical manuals.

{type_instructions}

CONTEXT FROM TECHNICAL MANUALS:
{context}

QUESTION: {question}

ANSWER GUIDELINES:
1. Answer based ONLY on the context provided
2. If the context doesn't contain the answer, say: "I don't have that specific information in the available manuals."
3. For safety questions, always start with safety warnings
4. For procedures, use numbered lists
5. Be concise but complete
6. Reference which document(s) you're using (e.g., "Based on Document 1...")

ANSWER:"""
    
    return prompt