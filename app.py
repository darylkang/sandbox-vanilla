"""
Educational LLM Chatbot with Streamlit

Stage 1: Modularized chat application demonstrating:
1. Clean separation of concerns with chat_core package
2. Configuration management for API keys and models
3. Provider abstraction for LLM services
4. Chat history storage interfaces
5. User-friendly error handling
6. Modern UI with streaming and persistence

Key Learning Concepts:
- Modular architecture patterns
- Dependency injection and abstraction
- Error handling and user experience
- Streamlit integration with custom packages
- Real-time streaming with user controls
- Modern UI design and state management
"""

import json
import logging
import os
import uuid
from typing import Dict, List

import streamlit as st

from chat_core.config import load_config
from chat_core.errors import humanize_error
from chat_core.history import StreamlitStore
from chat_core.provider import OpenAIProvider
from chat_core.session import get_or_create_sid
from chat_core.store import RedisStore

# Initialize logging once
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Debug mode for UI diagnostics
DEBUG_UI = bool(int(os.getenv("DEBUG_UI", "0")))

# Set the page title and configuration
st.set_page_config(page_title="Cyber Chat", page_icon="🌴", layout="wide")

# Header section
st.title("🌴 CYBER CHAT ⚡")
st.caption("Neural streaming • Redis-persistent sessions • Tropical vibes")

# Load configuration and initialize provider once
try:
    config = load_config()
    provider = OpenAIProvider(config)

    # Set logging level based on environment
    if config.env == "dev":
        logging.getLogger().setLevel(logging.INFO)
    else:
        logging.getLogger().setLevel(logging.WARNING)
except Exception as e:
    st.error(f"Configuration error: {str(e)}")
    st.stop()

# Get stable session ID for Redis persistence
sid = get_or_create_sid(st)

# Select storage backend with graceful fallback
if config.redis_url:
    try:
        chat_store = RedisStore(
            sid=sid,
            url=config.redis_url,
            max_turns=config.history_max_turns,
            ttl_seconds=config.history_ttl_seconds,
            key_prefix=config.key_prefix,
        )
        if not chat_store.is_healthy():
            raise RuntimeError("Redis ping failed")
        backend_label = "Redis"
    except Exception:
        # Redis misconfigured/unavailable → safe fallback
        chat_store = StreamlitStore(max_turns=config.history_max_turns)
        backend_label = "Streamlit (fallback)"
        st.warning(
            "Redis is configured but unreachable; using in-memory history for this session."
        )
else:
    chat_store = StreamlitStore(max_turns=config.history_max_turns)
    backend_label = "Streamlit"

# Initialize session state defaults
st.session_state.setdefault("generating", False)
st.session_state.setdefault("stop_requested", False)
st.session_state.setdefault("temperature", 0.7)

# Log startup information
logging.info(
    f"Env: {config.env} | Store: {backend_label} | Key prefix: {config.key_prefix} | Model: {config.openai_model} | Temperature: {config.openai_temperature}"
)

# Gruvbox Cyberpunk Tropical Theme
st.markdown(
    """
<style>
/* Gruvbox color palette */
:root {
  --bg: #282828;
  --bg0: #282828;
  --bg1: #3c3836;
  --bg2: #504945;
  --fg: #ebdbb2;
  --fg0: #fbf1c7;
  --fg1: #ebdbb2;
  --fg2: #d5c4a1;
  --red: #cc241d;
  --green: #98971a;
  --yellow: #d79921;
  --blue: #458588;
  --purple: #b16286;
  --aqua: #689d6a;
  --orange: #d65d0e;
  --gray: #928374;
  --bright-red: #fb4934;
  --bright-green: #b8bb26;
  --bright-yellow: #fabd2f;
  --bright-blue: #83a598;
  --bright-purple: #d3869b;
  --bright-aqua: #8ec07c;
  --bright-orange: #fe8019;
  --bright-gray: #a89984;
}

/* Force override Streamlit defaults */
.stApp {
  background: linear-gradient(135deg, #282828 0%, #1a1a1a 50%, #3c3836 100%) !important;
  background-attachment: fixed !important;
  font-family: 'Courier New', monospace !important;
  padding: 0 !important;
  margin: 0 !important;
}

/* Remove white bars and fix container */
.main .block-container {
  max-width: 900px !important;
  padding: 1rem !important;
  margin: 0 auto !important;
  background: rgba(40, 40, 40, 0.95) !important;
  border-radius: 20px !important;
  border: 2px solid #8ec07c !important;
  box-shadow: 0 0 30px rgba(139, 233, 253, 0.3), inset 0 0 30px rgba(139, 233, 253, 0.1) !important;
  backdrop-filter: blur(10px) !important;
}

/* Fix main content area */
.main {
  padding: 0 !important;
  margin: 0 !important;
}

/* Remove default Streamlit padding */
.stApp > div {
  padding: 0 !important;
}

/* Fix header area */
.stApp header {
  background: transparent !important;
  border: none !important;
}

/* Fix footer area */
.stApp footer {
  display: none !important;
}

/* Cyberpunk title styling */
h1 {
  color: #8ec07c !important;
  text-shadow: 0 0 10px #8ec07c !important;
  font-family: 'Courier New', monospace !important;
  font-weight: bold !important;
  text-transform: uppercase !important;
  letter-spacing: 2px !important;
  margin-bottom: 0.5rem !important;
}

/* Tropical caption */
.stCaption {
  color: #b8bb26 !important;
  font-family: 'Courier New', monospace !important;
  font-size: 0.9rem !important;
  text-shadow: 0 0 5px #b8bb26 !important;
}

/* Chat message styling - force override */
.stChatMessage {
  background: rgba(60, 56, 54, 0.8) !important;
  border-radius: 15px !important;
  border: 1px solid #d3869b !important;
  margin: 1rem 0 !important;
  padding: 1rem !important;
  box-shadow: 0 0 15px rgba(177, 98, 134, 0.2) !important;
}

/* User messages - tropical blue */
.stChatMessage[data-testid="user"] {
  background: linear-gradient(135deg, rgba(69, 133, 136, 0.3), rgba(131, 165, 152, 0.2)) !important;
  border-color: #83a598 !important;
  box-shadow: 0 0 15px rgba(131, 165, 152, 0.3) !important;
}

/* Assistant messages - cyberpunk purple */
.stChatMessage[data-testid="assistant"] {
  background: linear-gradient(135deg, rgba(177, 98, 134, 0.3), rgba(211, 134, 155, 0.2)) !important;
  border-color: #d3869b !important;
  box-shadow: 0 0 15px rgba(211, 134, 155, 0.3) !important;
}

/* Text styling - force override */
.stMarkdown {
  color: #ebdbb2 !important;
  font-family: 'Courier New', monospace !important;
  line-height: 1.6 !important;
}

.stMarkdown p {
  color: #ebdbb2 !important;
  font-family: 'Courier New', monospace !important;
}

/* Fix all text elements to be light colored */
.stApp * {
  color: #ebdbb2 !important;
}

/* Override specific dark text elements */
.stApp .stText {
  color: #ebdbb2 !important;
}

.stApp .stTextInput > div > div > input {
  color: #ebdbb2 !important;
}

.stApp .stSelectbox > div > div > div {
  color: #ebdbb2 !important;
}

.stApp .stSlider > div > div > div > div {
  color: #ebdbb2 !important;
}

/* Fix button text */
.stButton > button {
  color: #282828 !important;
}

/* Fix metric text */
.stMetric > div > div {
  color: #ebdbb2 !important;
}

.stMetric > div > div > div {
  color: #ebdbb2 !important;
}

/* Code blocks - gruvbox style */
.stMarkdown pre {
  background: #3c3836 !important;
  border: 1px solid #fe8019 !important;
  border-radius: 10px !important;
  padding: 1rem !important;
  color: #fabd2f !important;
  font-family: 'Courier New', monospace !important;
  box-shadow: 0 0 10px rgba(215, 153, 33, 0.3) !important;
}

.stMarkdown code {
  background: #504945 !important;
  color: #b8bb26 !important;
  padding: 0.2rem 0.4rem !important;
  border-radius: 4px !important;
  font-family: 'Courier New', monospace !important;
  border: 1px solid #98971a !important;
}

/* Links - tropical aqua */
.stMarkdown a {
  color: #8ec07c !important;
  text-decoration: none !important;
  text-shadow: 0 0 5px #8ec07c !important;
}

.stMarkdown a:hover {
  color: #83a598 !important;
  text-shadow: 0 0 10px #83a598 !important;
}

/* Input styling - force override */
.stChatInput > div > div > div {
  background: #3c3836 !important;
  border: 2px solid #b8bb26 !important;
  border-radius: 15px !important;
  color: #ebdbb2 !important;
  font-family: 'Courier New', monospace !important;
  box-shadow: 0 0 15px rgba(184, 187, 38, 0.3) !important;
}

.stChatInput > div > div > div:focus {
  border-color: #8ec07c !important;
  box-shadow: 0 0 20px rgba(139, 233, 253, 0.5) !important;
}

/* Sidebar styling - force override */
.stSidebar {
  background: linear-gradient(180deg, #282828, #3c3836) !important;
  border-right: 2px solid #d3869b !important;
}

.stSidebar .stMarkdown {
  color: #ebdbb2 !important;
}

.stSidebar .stMarkdown p {
  color: #ebdbb2 !important;
}

/* Sidebar headers */
.stSidebar h3 {
  color: #8ec07c !important;
  font-family: 'Courier New', monospace !important;
  text-shadow: 0 0 5px #8ec07c !important;
  text-transform: uppercase !important;
  letter-spacing: 1px !important;
}

/* Buttons - cyberpunk style */
.stButton > button {
  background: linear-gradient(45deg, #d3869b, #83a598) !important;
  color: #282828 !important;
  border: none !important;
  border-radius: 10px !important;
  font-family: 'Courier New', monospace !important;
  font-weight: bold !important;
  text-transform: uppercase !important;
  letter-spacing: 1px !important;
  box-shadow: 0 0 15px rgba(211, 134, 155, 0.4) !important;
  transition: all 0.3s ease !important;
}

.stButton > button:hover {
  background: linear-gradient(45deg, #83a598, #8ec07c) !important;
  box-shadow: 0 0 25px rgba(139, 233, 253, 0.6) !important;
  transform: translateY(-2px) !important;
}

/* Slider styling */
.stSlider > div > div > div > div {
  background: #8ec07c !important;
  box-shadow: 0 0 10px #8ec07c !important;
}

/* Metric styling */
.stMetric {
  color: #ebdbb2 !important;
  font-family: 'Courier New', monospace !important;
}

.stMetric > div > div {
  color: #ebdbb2 !important;
  font-family: 'Courier New', monospace !important;
}

/* Typing indicator - cyberpunk style */
.typing {
  display: inline-flex !important;
  align-items: center !important;
  gap: .5rem !important;
  color: #8ec07c !important;
  font-family: 'Courier New', monospace !important;
  text-shadow: 0 0 5px #8ec07c !important;
}

.dot {
  width: 8px !important;
  height: 8px !important;
  border-radius: 50% !important;
  background: #8ec07c !important;
  display: inline-block !important;
  animation: cyberpunk-blink 1.5s infinite ease-in-out !important;
  box-shadow: 0 0 10px #8ec07c !important;
}

.dot:nth-child(2) { animation-delay: .3s !important; }
.dot:nth-child(3) { animation-delay: .6s !important; }

@keyframes cyberpunk-blink {
  0%, 80%, 100% {
    opacity: .3;
    transform: scale(0.8);
  }
  40% {
    opacity: 1;
    transform: scale(1.2);
  }
}

/* Tropical accent elements */
.stApp::before {
  content: "🌴";
  position: fixed;
  top: 20px;
  right: 20px;
  font-size: 2rem;
  opacity: 0.3;
  z-index: -1;
  animation: float 3s ease-in-out infinite;
}

.stApp::after {
  content: "⚡";
  position: fixed;
  bottom: 20px;
  left: 20px;
  font-size: 1.5rem;
  opacity: 0.3;
  z-index: -1;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-10px); }
}

@keyframes pulse {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 0.8; }
}

/* Fix body and html to remove white bars */
html, body {
  margin: 0 !important;
  padding: 0 !important;
  background: #282828 !important;
  overflow-x: hidden !important;
}

/* Fix Streamlit's main container */
#root {
  background: #282828 !important;
}

/* Fix sidebar positioning */
.stSidebar {
  background: linear-gradient(180deg, #282828, #3c3836) !important;
  border-right: 2px solid #d3869b !important;
  top: 0 !important;
  height: 100vh !important;
}

/* Fix main content area positioning */
.main {
  background: transparent !important;
  padding: 0 !important;
  margin: 0 !important;
}

/* Ensure full height coverage */
.stApp > div {
  min-height: 100vh !important;
  background: linear-gradient(135deg, #282828 0%, #1a1a1a 50%, #3c3836 100%) !important;
}

/* Fix chat input positioning */
.stChatInput {
  background: transparent !important;
  padding: 1rem !important;
  margin: 0 !important;
}

/* Scrollbar styling */
::-webkit-scrollbar {
  width: 8px;
}

::-webkit-scrollbar-track {
  background: #3c3836;
}

::-webkit-scrollbar-thumb {
  background: #d3869b;
  border-radius: 4px;
  box-shadow: 0 0 5px #d3869b;
}

::-webkit-scrollbar-thumb:hover {
  background: #8ec07c;
  box-shadow: 0 0 10px #8ec07c;
}
</style>
""",
    unsafe_allow_html=True,
)


# Helper functions
def render_message(msg: Dict[str, str]):
    """Render a chat message using standard Streamlit components."""
    role = msg.get("role", "user")
    content = msg.get("content", "")

    with st.chat_message(role):
        st.markdown(content)


def transcript_to_markdown(messages: List[Dict[str, str]]) -> str:
    """Convert conversation to Markdown format."""
    lines = ["# Chat Transcript", ""]
    for m in messages:
        role = m.get("role", "user").capitalize()
        content = m.get("content", "")
        lines.append(f"**{role}:** {content}")
        lines.append("")
    return "\n".join(lines)


# Transcript rendering area
for msg in chat_store.get_messages():
    render_message(msg)

# Input area
if prompt := st.chat_input("Ask anything..."):
    # Add user message to conversation history
    chat_store.add_message("user", prompt)

    # Display the user's message immediately
    render_message({"role": "user", "content": prompt})

    # Reset streaming state
    st.session_state["stop_requested"] = False
    st.session_state["generating"] = True

    # Generate response using the provider (always streaming)
    typing_placeholder = None
    try:
        with st.chat_message("assistant"):
            placeholder = st.empty()
            accumulator = []

            # Show animated typing indicator
            typing_placeholder = st.empty()
            typing_placeholder.markdown(
                '<div class="typing">Assistant is typing <span class="dot"></span><span class="dot"></span><span class="dot"></span></div>',
                unsafe_allow_html=True,
            )

            # Stream tokens
            for chunk in provider.stream_complete(
                chat_store.get_messages(), temperature=st.session_state["temperature"]
            ):
                if st.session_state.get("stop_requested", False):
                    break
                accumulator.append(chunk)
                placeholder.markdown("".join(accumulator))

            # Finalize
            final_text = "".join(accumulator)

            # Add assistant's response to conversation history (once)
            if final_text.strip():
                chat_store.add_message("assistant", final_text)

            # Update placeholder with final text
            placeholder.markdown(final_text)

    except Exception:
        # Attempt non-streaming fallback before humanizing the error
        try:
            fallback_text = provider.complete(
                chat_store.get_messages(), temperature=st.session_state["temperature"]
            )
            chat_store.add_message("assistant", fallback_text)
            render_message({"role": "assistant", "content": fallback_text})
        except Exception as inner:
            # Handle errors with humanized messages (single path)
            error_msg = humanize_error(inner)
            chat_store.add_message("assistant", error_msg)
            render_message({"role": "assistant", "content": error_msg})

    finally:
        # Reset generation state and clear typing indicator
        st.session_state["generating"] = False
        if typing_placeholder:
            typing_placeholder.empty()

# Sidebar controls
with st.sidebar:
    # Session info
    st.subheader("⚡ NEURAL STATUS")
    st.caption(f"Env: {config.env} • Session: {sid[:8]}… • Store: {backend_label}")

    # History
    st.subheader("🌊 MESSAGE STREAM")
    message_count = chat_store.get_message_count()
    if message_count > 0:
        st.metric("Messages", message_count)

        # Clear conversation button
        if st.button("🗑️ PURGE DATA"):
            chat_store.clear()
            st.rerun()

        # New Chat button
        if st.button("🆕 NEW SESSION"):
            new_sid = uuid.uuid4().hex
            st.query_params["sid"] = new_sid
            chat_store.clear()
            st.rerun()
    else:
        st.text("No neural activity detected")

    # Export
    st.subheader("📡 DATA EXPORT")
    msgs = chat_store.get_messages()
    if msgs:
        md_bytes = transcript_to_markdown(msgs).encode("utf-8")
        json_bytes = json.dumps(msgs, ensure_ascii=False, indent=2).encode("utf-8")

        st.download_button(
            "📄 MARKDOWN", data=md_bytes, file_name="cyber_chat.md", mime="text/markdown"
        )
        st.download_button(
            "📋 JSON", data=json_bytes, file_name="cyber_chat.json", mime="application/json"
        )
    else:
        st.text("No data to export")

    # Controls
    st.subheader("🎮 NEURAL CONTROLS")

    # Stop button (only visible during generation)
    if st.session_state.get("generating", False):
        if st.button("🛑 TERMINATE", help="Stop the current response generation"):
            st.session_state["stop_requested"] = True
            st.rerun()

    # Model & behavior
    st.subheader("🤖 AI CONFIG")
    st.text(f"Model: {config.openai_model}")

    # Temperature slider (educational)
    temp = st.slider(
        "CREATIVITY LEVEL",
        0.0,
        1.0,
        value=st.session_state["temperature"],
        step=0.05,
        help="Higher = more creative neural patterns",
    )
    st.session_state["temperature"] = temp

    # Learning info
    st.subheader("📚 CYBER FEATURES")
    st.markdown("""
    **Neural Capabilities:**
    - Real-time streaming
    - Persistent memory
    - Error resilience
    - Tropical vibes
    - Cyberpunk aesthetics
    """)

    # Debug diagnostics (only when DEBUG_UI=1)
    if DEBUG_UI:
        st.subheader("🔧 DEBUG MODE")
        st.text("Neural Diagnostics:")
        st.text("• Container: 900px max")
        st.text("• Font: Courier New")
        st.text("• Theme: Gruvbox")
        st.text("• Style: Cyberpunk")
        st.text("")
        st.text("If issues persist:")
        st.text("• Check neural pathways")
        st.text("• Verify data streams")
        st.text("• Reboot consciousness")
