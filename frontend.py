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
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# DeepSeek-inspired CSS with dark theme
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background-color: #0a0a0a;
    }
    
    /* All text white */
    .stMarkdown, h1, h2, h3, h4, h5, h6, p, div, span, label {
        color: #ffffff !important;
    }
    
    /* Chat containers */
    .chat-container {
        max-width: 800px;
        margin: 0 auto;
        padding: 20px;
    }
    
    /* User message - Dark gray */
    .user-message {
        background-color: #1a1a1a;
        border-radius: 18px 18px 4px 18px;
        padding: 16px 20px;
        margin: 12px 0;
        margin-left: 20%;
        border: 1px solid #2d2d2d;
        color: #ffffff !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }
    
    /* Assistant message - Black background */
    .assistant-message {
        background-color: #0a0a0a !important;
        border-radius: 18px 18px 18px 4px;
        padding: 16px 20px;
        margin: 12px 0;
        margin-right: 20%;
        border: 2px solid #2d2d2d;
        color: #ffffff !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    }
    
    /* Safety warning style */
    .safety-warning {
        background-color: #1a0a0a !important;
        border: 2px solid #ff4444 !important;
        border-left: 6px solid #ff4444 !important;
    }
    
    /* Procedure step style */
    .procedure-step {
        background-color: #0a0a0a !important;
        border: 2px solid #1a73e8 !important;
        border-left: 6px solid #1a73e8 !important;
    }
    
    /* Specification style */
    .specification-box {
        background-color: #0a0a0a !important;
        border: 2px solid #34a853 !important;
        border-left: 6px solid #34a853 !important;
    }
    
    /* Message metadata */
    .message-meta {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
        font-size: 0.9rem;
    }
    
    .message-role {
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 8px;
        color: #ffffff;
    }
    
    .message-time {
        color: #888888;
        font-size: 0.8rem;
    }
    
    /* Message content */
    .message-content {
        color: #ffffff !important;
        line-height: 1.6;
        font-size: 16px;
    }
    
    /* Input area */
    .input-container {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background-color: #0a0a0a;
        padding: 20px;
        border-top: 1px solid #2d2d2d;
        backdrop-filter: blur(10px);
        z-index: 100;
    }
    
    .stTextArea textarea {
        background-color: #1a1a1a !important;
        color: #ffffff !important;
        border: 1px solid #2d2d2d !important;
        border-radius: 12px !important;
        padding: 16px !important;
        font-size: 16px !important;
    }
    
    .stTextArea textarea:focus {
        border-color: #666666 !important;
        box-shadow: 0 0 0 1px #666666 !important;
    }
    
    /* Buttons */
    .stButton button {
        background-color: #2d2d2d !important;
        color: white !important;
        border: 1px solid #3d3d3d !important;
        border-radius: 8px !important;
        padding: 10px 20px !important;
        transition: all 0.2s;
        font-weight: 500;
    }
    
    .stButton button:hover {
        background-color: #3d3d3d !important;
        border-color: #4d4d4d !important;
        transform: translateY(-1px);
    }
    
    .primary-button button {
        background-color: #1a73e8 !important;
        border-color: #1a73e8 !important;
    }
    
    .primary-button button:hover {
        background-color: #1669d6 !important;
        border-color: #1669d6 !important;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #1a1a1a;
        border-right: 1px solid #2d2d2d;
    }
    
    /* Sidebar can be toggled - Streamlit handles this automatically */
    /* Click hamburger menu (≡) in top right to show/hide sidebar */
    
    /* Progress bars */
    .stProgress > div > div > div > div {
        background-color: #1a73e8;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background-color: #2a2a2a !important;
        color: white !important;
        border: 1px solid #3d3d3d !important;
        border-radius: 8px !important;
    }
    
    .streamlit-expanderContent {
        background-color: #2a2a2a !important;
        color: white !important;
        border: 1px solid #3d3d3d !important;
        border-radius: 0 0 8px 8px !important;
    }
    
    /* File uploader */
    .upload-box {
        border: 2px dashed #3d3d3d !important;
        border-radius: 12px !important;
        padding: 30px;
        text-align: center;
        margin: 20px 0;
        background-color: #1a1a1a !important;
    }
    
    /* Stats box */
    .stats-box {
        background-color: #2a2a2a;
        border: 1px solid #3d3d3d;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        color: #ffffff;
    }
    
    /* Status indicators */
    .success-box {
        background-color: #1a3a1a;
        border: 1px solid #2a5a2a;
        border-radius: 8px;
        padding: 12px;
        margin: 8px 0;
        color: #ffffff;
    }
    
    .error-box {
        background-color: #3a1a1a;
        border: 1px solid #5a2a2a;
        border-radius: 8px;
        padding: 12px;
        margin: 8px 0;
        color: #ffffff;
    }
    
    .warning-box {
        background-color: #3a3a1a;
        border: 1px solid #5a5a2a;
        border-radius: 8px;
        padding: 12px;
        margin: 8px 0;
        color: #ffffff;
    }
    
    /* Source badges - FIXED: Properly escaped HTML */
    .source-badge {
        background-color: #2d2d2d;
        color: #cccccc !important;
        padding: 6px 12px;
        border-radius: 16px;
        font-size: 0.85rem;
        margin: 4px 4px 4px 0;
        display: inline-block;
        border: 1px solid #3d3d3d;
        font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
    }
    
    /* Source section */
    .source-section {
        margin-top: 16px;
        padding-top: 12px;
        border-top: 1px solid #3d3d3d;
        color: #888888;
        font-size: 0.9rem;
    }
    
    /* Main header */
    .main-header {
        background: linear-gradient(135deg, #2a2a2a 0%, #1a1a1a 100%);
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
        border: 1px solid #3d3d3d;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Fix for sidebar toggle visibility */
    header {visibility: visible;}
    .st-emotion-cache-1avcm0n {
        background-color: #0a0a0a;
    }
    
    /* Make sure all text in chat is white */
    .stChatMessage {
        color: white !important;
    }
    
    /* Fix for markdown text color */
    .stMarkdown p, .stMarkdown li, .stMarkdown ul, .stMarkdown ol {
        color: #ffffff !important;
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
            answer_lower = result["answer"].lower()
            if "⚠️" in result["answer"] or "safety" in answer_lower or "warning" in answer_lower or "danger" in answer_lower:
                message_type = "safety"
            elif any(word in answer_lower for word in ["step", "procedure", "install", "assembly", "process", "method"]):
                message_type = "procedure"
            elif any(word in answer_lower for word in ["spec", "parameter", "torque", "rpm", "mm", "psi", "bar", "voltage", "current"]):
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
    """Format chat message with styling based on type - FIXED HTML escaping"""
    if role == "user":
        # Escape HTML in user message
        safe_content = message["content"].replace('<', '&lt;').replace('>', '&gt;')
        return f'''
        <div class="user-message">
            <div class="message-meta">
                <div class="message-role">👤 You</div>
                <div class="message-time">{message.get("timestamp", "")}</div>
            </div>
            <div class="message-content">{safe_content}</div>
        </div>
        '''
    
    elif role == "assistant":
        # Escape HTML in assistant message to prevent code rendering
        safe_content = message["content"].replace('<', '&lt;').replace('>', '&gt;')
        
        # Determine CSS class based on message type
        message_class = "assistant-message"
        if message.get("message_type") == "safety":
            message_class += " safety-warning"
        elif message.get("message_type") == "procedure":
            message_class += " procedure-step"
        elif message.get("message_type") == "specification":
            message_class += " specification-box"
        
        html = f'''
        <div class="{message_class}">
            <div class="message-meta">
                <div class="message-role">🤖 Assistant</div>
                <div class="message-time">{message.get("timestamp", "")}</div>
            </div>
            <div class="message-content">{safe_content}</div>
        '''
        
        # Add sources if available
        if message.get("sources"):
            html += '''
            <div class="source-section">
                <div style="margin-bottom: 8px;">📚 Sources:</div>
            '''
            for source in message["sources"]:
                if source:
                    # Escape source text too
                    safe_source = str(source).replace('<', '&lt;').replace('>', '&gt;')
                    html += f'<span class="source-badge">{safe_source}</span> '
            html += '</div>'
        
        # Add context usage info
        if message.get("context_used"):
            html += f'<br><div style="font-size: 0.8rem; color: #666666; margin-top: 8px;"><i>📖 Used {message["context_used"]} document sections</i></div>'
        
        html += '</div>'
        return html

# Sidebar
with st.sidebar:
    st.markdown('<div class="main-header"><h2 style="color: white; margin: 0;">🏭 Manufacturing RAG</h2></div>', unsafe_allow_html=True)
    
    # Backend status
    if check_backend_connection():
        st.markdown('<div class="success-box">✅ **Backend Connected**</div>', unsafe_allow_html=True)
        
        # Display system stats
        with st.expander("📊 **System Statistics**", expanded=True):
            st.markdown(f'''
            <div class="stats-box">
            📚 **Documents in DB:** {st.session_state.system_stats.get('documents_in_db', 0)}<br>
            💬 **Active Sessions:** {st.session_state.system_stats.get('active_sessions', 0)}<br>
            🗣️ **Total Messages:** {st.session_state.system_stats.get('total_messages', 0)}<br>
            💾 **Memory Usage:** {st.session_state.system_stats.get('memory_size', 0):,} chars
            </div>
            ''', unsafe_allow_html=True)
    else:
        st.markdown('<div class="error-box">❌ **Backend Not Connected**</div>', unsafe_allow_html=True)
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
                if 'chunk_types' in file:
                    st.markdown(f"""
                    **Chunk Types:**
                    - Safety: {file['chunk_types'].get('safety', 0)}
                    - Procedures: {file['chunk_types'].get('procedure_step', 0)}
                    - Specs: {file['chunk_types'].get('specification', 0)}
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
    st.markdown('''
    <small style="color: #888;">
    **🏭 Manufacturing RAG Assistant**<br>
    • Specialized for technical manuals<br>
    • Safety-first retrieval<br>
    • Procedure-aware chunking<br>
    • Source attribution<br>
    • Session management
    </small>
    ''', unsafe_allow_html=True)

# Main area - Chat interface
st.markdown('<div class="chat-container">', unsafe_allow_html=True)

# Title
st.markdown('<h1 style="color: white;">💬 Manufacturing RAG Chat Assistant</h1>', unsafe_allow_html=True)

# Display connection status
if not st.session_state.backend_connected:
    st.markdown('<div class="warning-box">⚠️ **Backend not connected**. Please ensure FastAPI is running.</div>', unsafe_allow_html=True)
    if st.button("🔄 Retry Connection"):
        check_backend_connection()
        st.rerun()
else:
    # Display chat history
    if st.session_state.messages:
        for message in st.session_state.messages:
            if message["role"] == "user":
                st.markdown(format_chat_message(message, "user"), unsafe_allow_html=True)
            else:
                st.markdown(format_chat_message(message, "assistant"), unsafe_allow_html=True)
    
    # Empty state
    if not st.session_state.messages:
        st.markdown('''
        <div style="text-align: center; padding: 60px 20px; color: #888;">
            <h3 style="color: white; margin-bottom: 20px;">🏭 Welcome to Manufacturing RAG Assistant</h3>
            <p style="margin-bottom: 20px;">Upload manufacturing manuals and ask questions about:</p>
            <p style="margin-bottom: 30px;">
                <span class="source-badge">Safety Procedures</span>
                <span class="source-badge">Installation Steps</span>
                <span class="source-badge">Technical Specs</span>
                <span class="source-badge">Troubleshooting</span>
                <span class="source-badge">Maintenance</span>
            </p>
            <p style="color: #666; font-size: 0.9rem;">Use the sidebar to upload PDFs and try quick questions!</p>
            <p style="color: #555; font-size: 0.8rem; margin-top: 10px;">💡 <b>Tip:</b> Click the ≡ icon in the top right to show/hide sidebar</p>
        </div>
        ''', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Fixed input area at bottom
st.markdown('<div class="input-container">', unsafe_allow_html=True)

# Chat input with form
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

st.markdown('</div>', unsafe_allow_html=True)

# Add bottom padding for input area
st.markdown("<br><br><br>", unsafe_allow_html=True)

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

# Sidebar toggle instructions
st.markdown("""
<div style="text-align: center; padding: 10px; color: #555; font-size: 0.8rem;">
💡 <b>Tip:</b> Click the ≡ (hamburger) icon in the top right corner to show/hide sidebar
</div>
""", unsafe_allow_html=True)