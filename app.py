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
st.set_page_config(page_title="Cyber Chat", page_icon="🌴", layout="wide", initial_sidebar_state="expanded")

# Header section
st.title("Cyber Chat")
st.caption("Neural streaming • Redis-persistent sessions • Professional AI interface")

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

# Gruvbox theme enhancements (working with Streamlit's built-in theme)
st.markdown("""
<style>
/* Gruvbox color palette */
:root {
    --gruvbox-bg0: #282828;
    --gruvbox-bg1: #3c3836;
    --gruvbox-bg2: #504945;
    --gruvbox-fg0: #fbf1c7;
    --gruvbox-fg1: #ebdbb2;
    --gruvbox-fg2: #d5c4a1;
    --gruvbox-red: #cc241d;
    --gruvbox-green: #98971a;
    --gruvbox-yellow: #d79921;
    --gruvbox-blue: #458588;
    --gruvbox-purple: #b16286;
    --gruvbox-aqua: #689d6a;
    --gruvbox-orange: #d65d0e;
    --gruvbox-bright-green: #b8bb26;
    --gruvbox-bright-yellow: #fabd2f;
    --gruvbox-bright-blue: #83a598;
    --gruvbox-bright-purple: #d3869b;
    --gruvbox-bright-aqua: #8ec07c;
    --gruvbox-bright-orange: #fe8019;
}

/* Enhance chat messages with gruvbox styling */
.stChatMessage {
    border-radius: 12px !important;
    margin: 1rem 0 !important;
    padding: 1rem !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
}

.stChatMessage[data-testid="user"] {
    border-left: 4px solid var(--gruvbox-bright-blue) !important;
}

.stChatMessage[data-testid="assistant"] {
    border-left: 4px solid var(--gruvbox-bright-purple) !important;
}

/* Enhance sidebar with gruvbox accents */
.stSidebar {
    border-right: 3px solid var(--gruvbox-bright-purple) !important;
}

.stSidebar h3 {
    color: var(--gruvbox-bright-aqua) !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
    margin-bottom: 1rem !important;
}

/* Gruvbox-style buttons */
.stButton > button {
    background: linear-gradient(135deg, var(--gruvbox-bright-green), var(--gruvbox-green)) !important;
    color: var(--gruvbox-bg0) !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    padding: 0.5rem 1rem !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
}

.stButton > button:hover {
    background: linear-gradient(135deg, var(--gruvbox-green), var(--gruvbox-bright-green)) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15) !important;
}

/* Download buttons with gruvbox orange */
.stDownloadButton > button {
    background: linear-gradient(135deg, var(--gruvbox-bright-orange), var(--gruvbox-orange)) !important;
    color: var(--gruvbox-bg0) !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    padding: 0.5rem 1rem !important;
    transition: all 0.2s ease !important;
}

.stDownloadButton > button:hover {
    background: linear-gradient(135deg, var(--gruvbox-orange), var(--gruvbox-bright-orange)) !important;
    transform: translateY(-1px) !important;
}

/* Gruvbox-style metrics */
.stMetric {
    background: var(--gruvbox-bg1) !important;
    border: 2px solid var(--gruvbox-bright-aqua) !important;
    border-radius: 12px !important;
    padding: 1rem !important;
    margin: 0.5rem 0 !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
}

.stMetric label {
    color: var(--gruvbox-bright-yellow) !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
}

/* Gruvbox-style slider */
.stSlider {
    margin: 1rem 0 !important;
}

.stSlider > div > div > div {
    background: var(--gruvbox-bg1) !important;
    border-radius: 8px !important;
    border: 1px solid var(--gruvbox-bg2) !important;
}

.stSlider > div > div > div > div {
    background: var(--gruvbox-bright-green) !important;
    border-radius: 4px !important;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
}

.stSlider label {
    color: var(--gruvbox-fg1) !important;
    font-weight: 600 !important;
}

/* Gruvbox-style code blocks */
.stMarkdown pre {
    background: var(--gruvbox-bg1) !important;
    border: 2px solid var(--gruvbox-bright-yellow) !important;
    border-radius: 8px !important;
    color: var(--gruvbox-bright-yellow) !important;
    font-family: 'Courier New', monospace !important;
    padding: 1rem !important;
}

.stMarkdown code {
    background: var(--gruvbox-bg2) !important;
    color: var(--gruvbox-bright-green) !important;
    padding: 0.2rem 0.4rem !important;
    border-radius: 4px !important;
    font-family: 'Courier New', monospace !important;
    border: 1px solid var(--gruvbox-green) !important;
}

/* Gruvbox-style links */
.stMarkdown a {
    color: var(--gruvbox-bright-aqua) !important;
    text-decoration: none !important;
    font-weight: 600 !important;
}

.stMarkdown a:hover {
    color: var(--gruvbox-bright-blue) !important;
    text-decoration: underline !important;
}

/* Typing indicator with gruvbox colors */
.typing {
    display: inline-flex !important;
    align-items: center !important;
    gap: 0.5rem !important;
    color: var(--gruvbox-bright-aqua) !important;
    font-weight: 600 !important;
}

.dot {
    width: 8px !important;
    height: 8px !important;
    border-radius: 50% !important;
    background: var(--gruvbox-bright-aqua) !important;
    display: inline-block !important;
    animation: gruvbox-blink 1.5s infinite ease-in-out !important;
}

.dot:nth-child(2) { animation-delay: 0.3s !important; }
.dot:nth-child(3) { animation-delay: 0.6s !important; }

@keyframes gruvbox-blink {
    0%, 80%, 100% {
        opacity: 0.3;
        transform: scale(0.8);
    }
    40% {
        opacity: 1;
        transform: scale(1.2);
    }
}

/* Enhance the main title */
h1 {
    color: var(--gruvbox-bright-aqua) !important;
    text-shadow: 0 0 10px rgba(142, 192, 124, 0.3) !important;
    font-weight: 700 !important;
    margin-bottom: 0.5rem !important;
}

.stCaption {
    color: var(--gruvbox-bright-yellow) !important;
    font-weight: 500 !important;
    opacity: 0.9 !important;
}

/* Scrollbar styling */
::-webkit-scrollbar {
    width: 8px;
}

::-webkit-scrollbar-track {
    background: var(--gruvbox-bg1);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb {
    background: var(--gruvbox-bright-purple);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: var(--gruvbox-bright-aqua);
}
</style>
""", unsafe_allow_html=True)

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


# Main content area with proper container
with st.container():
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

            # Show animated typing indicator with gruvbox styling
            typing_placeholder = st.empty()
            typing_placeholder.markdown(
                '<div class="typing">Generating response <span class="dot"></span><span class="dot"></span><span class="dot"></span></div>',
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
    st.subheader("System Status")
    st.caption(f"Environment: {config.env} • Session: {sid[:8]}… • Store: {backend_label}")

    # History
    st.subheader("Message History")
    message_count = chat_store.get_message_count()
    if message_count > 0:
        st.metric("Messages", message_count)

        # Clear conversation button
        if st.button("Clear Chat"):
            chat_store.clear()
            st.rerun()

        # New Chat button
        if st.button("New Session"):
            new_sid = uuid.uuid4().hex
            st.query_params["sid"] = new_sid
            chat_store.clear()
            st.rerun()
    else:
        st.text("No messages yet")

    # Export
    st.subheader("Export Data")
    msgs = chat_store.get_messages()
    if msgs:
        md_bytes = transcript_to_markdown(msgs).encode("utf-8")
        json_bytes = json.dumps(msgs, ensure_ascii=False, indent=2).encode("utf-8")

        st.download_button(
            "Markdown", data=md_bytes, file_name="cyber_chat.md", mime="text/markdown"
        )
        st.download_button(
            "JSON", data=json_bytes, file_name="cyber_chat.json", mime="application/json"
        )
    else:
        st.text("No data to export")

    # Controls
    st.subheader("Controls")

    # Stop button (only visible during generation)
    if st.session_state.get("generating", False):
        if st.button("Stop Generation", help="Stop the current response generation"):
            st.session_state["stop_requested"] = True
            st.rerun()

    # Model & behavior
    st.subheader("AI Configuration")
    st.text(f"Model: {config.openai_model}")

    # Temperature slider
    temp = st.slider(
        "Creativity Level",
        0.0,
        1.0,
        value=st.session_state["temperature"],
        step=0.05,
        help="Higher values produce more creative responses",
    )
    st.session_state["temperature"] = temp

    # Features info
    st.subheader("Features")
    st.markdown("""
    **Capabilities:**
    - Real-time streaming
    - Persistent memory
    - Error resilience
    - Professional interface
    - Modern design
    """)

    # Debug diagnostics (only when DEBUG_UI=1)
    if DEBUG_UI:
        st.subheader("Debug Mode")
        st.text("System Diagnostics:")
        st.text("• Container: Responsive")
        st.text("• Font: System fonts")
        st.text("• Theme: Professional")
        st.text("• Style: Modern")
        st.text("")
        st.text("Troubleshooting:")
        st.text("• Check configuration")
        st.text("• Verify connections")
        st.text("• Restart application")
