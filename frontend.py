import streamlit as st
import requests
import time
import json
from datetime import datetime

# Configuration
BACKEND_URL = "http://localhost:8000"  # Update to your FastAPI port (8000 or 8001)

# Page config
st.set_page_config(
    page_title="Manufacturing Manual RAG Assistant",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for manufacturing theme
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .safety-warning {
        background-color: #fff3cd;
        border: 2px solid #ffeaa7;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        color: #856404;
    }
    .procedure-step {
        background-color: #d1ecf1;
        border: 2px solid #bee5eb;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        color: #0c5460;
    }
    .specification-box {
        background-color: #d4edda;
        border: 2px solid #c3e6cb;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        color: #155724;
    }
    .chat-user {
        background-color: #2b313e;
        padding: 15px;
        border-radius: 10px 10px 0 10px;
        margin: 10px 0;
        margin-left: 10%;
        border-left: 4px solid #667eea;
    }
    .chat-assistant {
        background-color: #262730;
        padding: 15px;
        border-radius: 10px 10px 10px 0;
        margin: 10px 0;
        margin-right: 10%;
        border-left: 4px solid #764ba2;
    }
    .source-badge {
        background-color: #4a5568;
        color: white;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 0.8rem;
        margin: 2px;
        display: inline-block;
    }
    .upload-box {
        border: 2px dashed #667eea;
        border-radius: 10px;
        padding: 30px;
        text-align: center;
        margin: 20px 0;
        background-color: rgba(102, 126, 234, 0.05);
    }
    .stats-box {
        background-color: #2d3748;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .stButton button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
    }
    .stButton button:hover {
        background: linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%);
        color: white;
        border: none;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []
if "current_session" not in st.session_state:
    st.session_state.current_session = f"session_{int(time.time())}"
if "backend_connected" not in st.session_state:
    st.session_state.backend_connected = False
if "system_stats" not in st.session_state:
    st.session_state.system_stats = {}

def check_backend_connection():
    """Check if backend is available"""
    try:
        response = requests.get(f"{BACKEND_URL}/stats", timeout=2)
        if response.status_code == 200:
            st.session_state.backend_connected = True
            st.session_state.system_stats = response.json()
            return True
        else:
            st.session_state.backend_connected = False
            return False
    except:
        st.session_state.backend_connected = False
        return False

def upload_pdf(file):
    """Upload PDF to backend with enhanced feedback"""
    try:
        with st.spinner(f"📄 Processing {file.name}..."):
            # Create a progress bar
            progress_bar = st.progress(0)
            
            # Prepare file for upload
            files = {"file": (file.name, file.getvalue(), "application/pdf")}
            
            # Send to backend
            progress_bar.progress(30)
            response = requests.post(f"{BACKEND_URL}/ingest", files=files, timeout=60)
            progress_bar.progress(70)
            
            if response.status_code == 200:
                result = response.json()
                progress_bar.progress(100)
                
                # Add to uploaded files list
                st.session_state.uploaded_files.append({
                    "name": file.name,
                    "chunks": result.get('chunks_added', 0),
                    "chunk_types": result.get('chunk_types', {}),
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "status": "success"
                })
                
                # Show success message with details
                st.success(f"✅ **{file.name}** processed successfully!")
                
                # Show chunk statistics
                if 'chunk_types' in result:
                    st.info(f"""
                    **Chunk Statistics:**
                    - Total chunks: {result['chunks_added']}
                    - Safety chunks: {result['chunk_types'].get('safety', 0)}
                    - Procedure steps: {result['chunk_types'].get('procedure_step', 0)}
                    - Specifications: {result['chunk_types'].get('specification', 0)}
                    - Content chunks: {result['chunk_types'].get('content', 0)}
                    """)
                
                # Update system stats
                check_backend_connection()
                return True
                
            elif response.status_code == 400:
                error_data = response.json()
                st.error(f"❌ Upload failed: {error_data.get('detail', 'Bad request')}")
            else:
                st.error(f"❌ Upload failed with status {response.status_code}")
                return False
                
    except requests.exceptions.Timeout:
        st.error("⏰ Request timeout. The PDF might be too large or server is busy.")
        return False
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        return False
    finally:
        time.sleep(0.5)  # Small delay for UI

def send_message(message):
    """Send message to backend with enhanced features"""
    if not message.strip():
        return
    
    # Add user message to chat
    st.session_state.messages.append({
        "role": "user", 
        "content": message,
        "timestamp": datetime.now().strftime("%H:%M:%S")
    })
    
    try:
        # Call backend
        payload = {
            "session_id": st.session_state.current_session,
            "question": message
        }
        
        # Create a container for the streaming-like effect
        with st.spinner("🔍 **Analyzing manufacturing manual...**"):
            response = requests.post(f"{BACKEND_URL}/chat", json=payload, timeout=90)
        
        if response.status_code == 200:
            result = response.json()
            
            # Determine message type based on content
            message_type = "general"
            if "⚠️" in result["answer"] or "safety" in result["answer"].lower():
                message_type = "safety"
            elif any(word in result["answer"].lower() for word in ["step", "procedure", "install", "assembly"]):
                message_type = "procedure"
            elif any(word in result["answer"].lower() for word in ["spec", "parameter", "torque", "rpm", "mm"]):
                message_type = "specification"
            
            st.session_state.messages.append({
                "role": "assistant",
                "content": result["answer"],
                "sources": result.get("sources", []),
                "context_used": result.get("context_used", 0),
                "message_type": message_type,
                "timestamp": datetime.now().strftime("%H:%M:%S")
            })
            
        elif response.status_code == 500:
            error_data = response.json()
            st.error(f"❌ Server error: {error_data.get('detail', 'Internal server error')}")
            
    except requests.exceptions.Timeout:
        st.error("⏰ Request timeout. Please try a simpler question.")
    except Exception as e:
        st.error(f"❌ Connection error: {str(e)}")

def clear_chat_history():
    """Clear chat history via API"""
    try:
        payload = {"session_id": st.session_state.current_session}
        response = requests.post(f"{BACKEND_URL}/clear_history", json=payload)
        
        if response.status_code == 200:
            st.session_state.messages = []
            st.success("✅ Chat history cleared")
            st.rerun()
        else:
            st.error("Failed to clear history")
    except:
        st.session_state.messages = []
        st.success("✅ Chat history cleared locally")
        st.rerun()

def format_chat_message(message, role):
    """Format chat message with styling based on type"""
    if role == "user":
        return f'<div class="chat-user"><b>👤 You</b> <small style="color: #888; float: right;">{message.get("timestamp", "")}</small><br>{message["content"]}</div>'
    
    elif role == "assistant":
        content = f'<div class="chat-assistant"><b>🏭 Assistant</b> <small style="color: #888; float: right;">{message.get("timestamp", "")}</small><br>'
        
        # Add type-specific styling
        if message.get("message_type") == "safety":
            content = content.replace('class="chat-assistant"', 'class="chat-assistant safety-warning"')
        elif message.get("message_type") == "procedure":
            content = content.replace('class="chat-assistant"', 'class="chat-assistant procedure-step"')
        elif message.get("message_type") == "specification":
            content = content.replace('class="chat-assistant"', 'class="chat-assistant specification-box"')
        
        content += message["content"]
        
        # Add sources if available
        if message.get("sources"):
            content += '<br><br><small><b>📚 Sources:</b><br>'
            for source in message["sources"]:
                if source:
                    content += f'<span class="source-badge">{source}</span> '
            content += '</small>'
        
        # Add context usage info
        if message.get("context_used"):
            content += f'<br><small><i>📖 Used {message["context_used"]} document sections</i></small>'
        
        content += '</div>'
        return content

# Sidebar
with st.sidebar:
    st.markdown('<div class="main-header"><h1 style="color: white;">🏭 Manufacturing RAG</h1></div>', unsafe_allow_html=True)
    
    # Backend status
    if check_backend_connection():
        st.success("✅ **Backend Connected**")
        
        # Display system stats
        with st.expander("📊 **System Statistics**", expanded=True):
            st.markdown(f"""
            <div class="stats-box">
            📚 **Documents in DB:** {st.session_state.system_stats.get('documents_in_db', 0)}<br>
            💬 **Active Sessions:** {st.session_state.system_stats.get('active_sessions', 0)}<br>
            🗣️ **Total Messages:** {st.session_state.system_stats.get('total_messages', 0)}<br>
            💾 **Memory Usage:** {st.session_state.system_stats.get('memory_size', 0):,} chars
            </div>
            """, unsafe_allow_html=True)
    else:
        st.error("❌ **Backend Not Connected**")
        st.info(f"Make sure FastAPI is running at: {BACKEND_URL}")
    
    st.divider()
    
    # Session management
    st.subheader("💬 **Chat Session**")
    session_name = st.text_input(
        "Session ID",
        value=st.session_state.current_session,
        help="Change session ID to start a new conversation context"
    )
    
    if session_name != st.session_state.current_session:
        st.session_state.current_session = session_name
        st.session_state.messages = []
        st.success(f"🆕 New session: {session_name}")
        st.rerun()
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🆕 New Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    with col2:
        if st.button("🗑️ Clear History", use_container_width=True):
            clear_chat_history()
    
    st.divider()
    
    # File upload section
    st.subheader("📁 **Upload Manufacturing Manuals**")
    
    # Upload box
    st.markdown('<div class="upload-box">', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Drag and drop or click to upload",
        type="pdf",
        label_visibility="collapsed",
        help="Upload manufacturing manuals, technical documents, or automation guides"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    if uploaded_file is not None:
        if st.button("🚀 Upload & Process PDF", type="primary", use_container_width=True):
            if upload_pdf(uploaded_file):
                st.rerun()
    
    # Show uploaded files
    if st.session_state.uploaded_files:
        st.divider()
        st.subheader("📋 **Uploaded Files**")
        for file in reversed(st.session_state.uploaded_files[-3:]):  # Show last 3
            with st.expander(f"📄 {file['name']}"):
                st.markdown(f"""
                **Time:** {file['timestamp']}<br>
                **Chunks:** {file['chunks']}<br>
                **Status:** ✅ Success
                """)
    
    st.divider()
    
    # Quick questions
    st.subheader("💡 **Quick Questions**")
    
    quick_questions = [
        "What safety warnings are in the manual?",
        "What are the installation procedures?",
        "List maintenance requirements",
        "What are the technical specifications?",
        "How do I troubleshoot errors?"
    ]
    
    for question in quick_questions:
        if st.button(question, use_container_width=True):
            send_message(question)
            st.rerun()
    
    st.divider()
    
    # Info
    st.markdown("""
    <small>
    **🏭 Manufacturing RAG Assistant**<br>
    • Specialized for technical manuals<br>
    • Safety-first retrieval<br>
    • Procedure-aware chunking<br>
    • Source attribution<br>
    • Session management
    </small>
    """, unsafe_allow_html=True)

# Main area - Chat interface
st.title("💬 Manufacturing RAG Chat Assistant")

# Display connection status
if not st.session_state.backend_connected:
    st.warning("⚠️ **Backend not connected**. Please ensure FastAPI is running.")
    if st.button("🔄 Retry Connection"):
        check_backend_connection()
        st.rerun()
else:
    # Display chat history
    chat_container = st.container()
    
    with chat_container:
        for message in st.session_state.messages:
            if message["role"] == "user":
                st.markdown(format_chat_message(message, "user"), unsafe_allow_html=True)
            else:
                st.markdown(format_chat_message(message, "assistant"), unsafe_allow_html=True)
    
    # Empty state
    if not st.session_state.messages:
        st.markdown("""
        <div style="text-align: center; padding: 40px; color: #666;">
            <h3>🏭 Welcome to Manufacturing RAG Assistant</h3>
            <p>Upload manufacturing manuals and ask questions about:</p>
            <p>
                <span class="source-badge">Safety Procedures</span>
                <span class="source-badge">Installation Steps</span>
                <span class="source-badge">Technical Specs</span>
                <span class="source-badge">Troubleshooting</span>
                <span class="source-badge">Maintenance</span>
            </p>
            <p>Use the sidebar to upload PDFs and try quick questions!</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Chat input at bottom
    st.divider()
    
    # Multi-line text input for better question entry
    with st.form(key="chat_form", clear_on_submit=True):
        col1, col2 = st.columns([5, 1])
        with col1:
            user_input = st.text_area(
                "Your question:",
                placeholder="Ask about safety procedures, installation steps, technical specifications, troubleshooting...",
                label_visibility="collapsed",
                height=80,
                key="question_input"
            )
        with col2:
            submit_button = st.form_submit_button(
                "🚀 Send",
                use_container_width=True,
                type="primary"
            )
    
    if submit_button and user_input:
        send_message(user_input)
        st.rerun()
    
    # Bottom info bar
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.caption(f"**Session:** {st.session_state.current_session}")
    with col2:
        st.caption(f"**Messages:** {len(st.session_state.messages)}")
    with col3:
        if st.session_state.uploaded_files:
            total_chunks = sum(f["chunks"] for f in st.session_state.uploaded_files)
            st.caption(f"**Total Chunks:** {total_chunks}")

# Auto-refresh for new messages (optional)
# st.rerun() is already called when needed