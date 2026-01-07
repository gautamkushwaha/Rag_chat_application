# 🏭 Manufacturing RAG Assistant

A specialized Retrieval-Augmented Generation (RAG) system for manufacturing and automation manuals. This system provides intelligent Q&A capabilities for technical documents with safety-first prioritization.

## ✨ Features

- **Manufacturing-Optimized Chunking**: Specialized text splitting for technical manuals
- **Safety-First Retrieval**: Prioritizes safety warnings and cautions
- **Procedure-Aware Q&A**: Maintains step-by-step instructions integrity
- **Multi-Format Support**: PDF document processing
- **Conversational Memory**: Maintains context across questions
- **Streamlit Frontend**: User-friendly interface
- **FastAPI Backend**: RESTful API with Swagger documentation

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- OpenAI API key

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/manufacturing-rag-app.git
   cd manufacturing-rag-app


   2. Set up virtual environment

   python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\

3. Install dependencies
pip install -r requirements.txt

4. configure environment variables
cp .env.example .env
# Edit .env and add your OpenAI API key


Usage
   1. Start the backend server
   # From project root
python -m uvicorn app.main:app --reload --port 8000


Start the frontend


# In a new terminal
cd frontend
streamlit run streamlit_app

Access the applications

Backend API: http://localhost:8000/docs

Frontend UI: http://localhost:8501manufacturing-rag-app/
├── app/                    # FastAPI backend
│   ├── main.py            # Main application
│   ├── ingestion.py       # PDF processing & chunking
│   ├── retrieval.py       # Q&A system
│   ├── vectorstore.py     # Vector database
│   ├── memory.py          # Conversation memory
│   └── schemas.py         # Data models
├── frontend/              # Streamlit UI
├── data/                  # Data storage
├── tests/                 # Test suite
└── scripts/               # Utility scripts🔧 Configuration
Environment Variables
Create a .env file with:OPENAI_API_KEY=your_openai_api_key_here
EMBEDDING_MODEL=text-embedding-3-small
LLM_MODEL=gpt-4o