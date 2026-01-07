import os
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

load_dotenv()
PERSIST_DIR = "data/chroma_db"

def get_vectorstore(collection_name: str = "manufacturing_manuals"):
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    
    os.makedirs(PERSIST_DIR, exist_ok=True)
    
    try:
        # Try to load existing collection
        db = Chroma(
            persist_directory=PERSIST_DIR,
            embedding_function=embeddings,
            collection_name=collection_name
        )
        
        # Verify it has documents
        collection_info = db.get()
        if not collection_info['ids']:
            print(f"Collection '{collection_name}' exists but is empty")
        
    except Exception as e:
        print(f"Creating new collection '{collection_name}': {e}")
        # If it doesn't exist, create a new empty one
        db = Chroma(
            persist_directory=PERSIST_DIR,
            embedding_function=embeddings,
            collection_name=collection_name
        )
    
    return db