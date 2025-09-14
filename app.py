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

# Minimal dark theme
st.markdown("""
<style>
/* Simple dark theme */
.stApp {
    background-color: #0e1117;
    color: #fafafa;
}

.stApp .main .block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}

/* Chat messages */
.stChatMessage {
    background-color: #262730;
    border: 1px solid #3a3a4a;
    border-radius: 10px;
    margin: 1rem 0;
    padding: 1rem;
}

/* Sidebar */
.stSidebar {
    background-color: #1a1a2e;
}

/* Buttons */
.stButton > button {
    background-color: #ff6b6b;
    color: white;
    border: none;
    border-radius: 5px;
    padding: 0.5rem 1rem;
    font-weight: 600;
}

.stButton > button:hover {
    background-color: #ff5252;
}

/* Input */
.stChatInput > div > div > div {
    background-color: #262730;
    border: 1px solid #3a3a4a;
    border-radius: 10px;
    color: #fafafa;
}

.stChatInput > div > div > div:focus {
    border-color: #ff6b6b;
    box-shadow: 0 0 0 2px rgba(255, 107, 107, 0.2);
}

/* Metrics */
.stMetric {
    background-color: #262730;
    border: 1px solid #3a3a4a;
    border-radius: 10px;
    padding: 1rem;
}

/* Slider */
.stSlider > div > div > div {
    background-color: #262730;
    border-radius: 5px;
}

.stSlider > div > div > div > div {
    background-color: #ff6b6b;
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

            # Show animated typing indicator
            typing_placeholder = st.empty()
            typing_placeholder.markdown(
                '<div style="display: inline-flex; align-items: center; gap: 0.5rem; color: #ff6b6b;">Generating response <span style="width: 8px; height: 8px; border-radius: 50%; background: #ff6b6b; display: inline-block; animation: blink 1.5s infinite;"></span><span style="width: 8px; height: 8px; border-radius: 50%; background: #ff6b6b; display: inline-block; animation: blink 1.5s infinite; animation-delay: 0.3s;"></span><span style="width: 8px; height: 8px; border-radius: 50%; background: #ff6b6b; display: inline-block; animation: blink 1.5s infinite; animation-delay: 0.6s;"></span></div>',
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
