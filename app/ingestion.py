import os
import re
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv
from typing import List, Dict, Tuple

load_dotenv()

UPLOAD_DIR = "data/uploads"
PERSIST_DIR = "data/chroma_db"

def manufacturing_manual_chunking(documents: List[Document]) -> List[Document]:
    """Specialized chunking for manufacturing/automation manuals"""
    final_chunks = []
    
    for doc in documents:
        text = doc.page_content
        metadata = doc.metadata.copy()
        
        # Extract safety sections first (CRITICAL!)
        safety_pattern = r'(\n(?:WARNING|CAUTION|DANGER)[:\s][^\n]+(?:\n[^\n]+)*)'
        safety_matches = re.finditer(safety_pattern, text, flags=re.IGNORECASE)
        
        for match in safety_matches:
            safety_text = match.group(0).strip()
            if len(safety_text) > 50:
                safety_metadata = metadata.copy()
                safety_metadata.update({
                    "chunk_type": "safety",
                    "priority": "high",
                    "has_safety": True
                })
                final_chunks.append(Document(
                    page_content=safety_text,
                    metadata=safety_metadata
                ))
        
        # Remove safety sections
        text = re.sub(safety_pattern, '', text, flags=re.IGNORECASE)
        
        # Extract numbered procedures
        step_pattern = r'(\n\d+\.\s+[^\n]+(?:\n[^\n]+){0,3})'
        steps = re.findall(step_pattern, text)
        
        if steps:
            for step in steps:
                step_text = step.strip()
                if len(step_text) > 60:
                    step_metadata = metadata.copy()
                    step_metadata.update({
                        "chunk_type": "procedure_step",
                        "priority": "medium"
                    })
                    final_chunks.append(Document(
                        page_content=step_text,
                        metadata=step_metadata
                    ))
            # Remove processed steps
            text = re.sub(step_pattern, '', text)
        
        # Process remaining content with smart splitting
        if text.strip():
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=650,
                chunk_overlap=130,
                separators=[
                    "\n\n## ",
                    "\n\n",
                    "\n• ",
                    "\n- ",
                    "\n",
                    ". ",
                    "; ",
                    ", ",
                    " "
                ],
                keep_separator=True
            )
            
            remaining_chunks = splitter.split_text(text.strip())
            for chunk in remaining_chunks:
                chunk_text = chunk.strip()
                if len(chunk_text) > 80:
                    chunk_metadata = metadata.copy()
                    
                    # Auto-classify
                    if re.search(r'(figure|diagram|table)\s+\d+', chunk_text, re.IGNORECASE):
                        chunk_metadata["chunk_type"] = "reference"
                    elif re.search(r'(\d+\s*mm|\d+\s*°C|\d+\s*rpm|\d+\s*psi)', chunk_text):
                        chunk_metadata["chunk_type"] = "specification"
                    else:
                        chunk_metadata["chunk_type"] = "content"
                    
                    final_chunks.append(Document(
                        page_content=chunk_text,
                        metadata=chunk_metadata
                    ))
    
    return final_chunks

def ingest_pdf(file_path: str) -> Tuple[int, Dict[str, int]]:
    """Ingest manufacturing manual PDF with optimized chunking"""
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(PERSIST_DIR, exist_ok=True)
    
    # Use PyMuPDF for better text extraction
    loader = PyMuPDFLoader(file_path)
    documents = loader.load()
    
    print(f"📄 Loaded {len(documents)} pages from {os.path.basename(file_path)}")
    
    # Apply manufacturing-optimized chunking
    chunks = manufacturing_manual_chunking(documents)
    
    # Statistics
    chunk_types = {}
    for chunk in chunks:
        chunk_type = chunk.metadata.get("chunk_type", "unknown")
        chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
    
    print(f"✂️  Created {len(chunks)} chunks")
    print(f"📊 Chunk distribution: {chunk_types}")
    
    # Create embeddings and vector store
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    
    db = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=PERSIST_DIR,
        collection_name="manufacturing_manuals"
    )
    
    # Persistence is automatic in newer Chroma versions
    # No need to call db.persist()
    
    return len(chunks), chunk_types