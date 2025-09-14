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
st.set_page_config(page_title="Educational LLM Chatbot", page_icon="🤖", layout="wide")

# Header section
st.title("Personal Chatbot")
st.caption("Streaming by default • Optional Redis-backed session history")

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
        chat_store = StreamlitStore()
        backend_label = "Streamlit (fallback)"
        st.warning(
            "Redis is configured but unreachable; using in-memory history for this session."
        )
else:
    chat_store = StreamlitStore()
    backend_label = "Streamlit"

# Initialize session state defaults
st.session_state.setdefault("generating", False)
st.session_state.setdefault("stop_requested", False)
st.session_state.setdefault("temperature", 0.7)

# Log startup information
logging.info(
    f"Env: {config.env} | Store: {backend_label} | Key prefix: {config.key_prefix} | Model: {config.openai_model}"
)

# Inject minimal theme-aware CSS
st.markdown(
    """
<style>
/* Typography and layout */
.block-container {
  padding-top: 2rem;
  padding-bottom: 2rem;
  max-width: 900px;
}
h1, h2, h3 {
  letter-spacing: 0.01em;
  line-height: 1.25;
  margin: 0.25rem 0 0.25rem 0;
}

/* Chat bubbles (theme-friendly) */
.chat-bubble {
  padding: .75rem 1rem;
  border-radius: 14px;
  margin: .25rem 0 .8rem 0;
  border: 1px solid rgba(0,0,0,0.06);
}
/* Improve border contrast in dark mode using media query */
@media (prefers-color-scheme: dark) {
  .chat-bubble { border-color: rgba(255,255,255,0.12); }
}
/* Role-specific backgrounds using translucent fills that adapt in both themes */
.chat-user {
  background: rgba(10,132,255,0.10); /* primary tint, subtle */
}
.chat-assistant {
  background: rgba(127,127,127,0.10); /* neutral tint */
}

/* Typing indicator */
.typing {
  display:inline-flex;
  align-items:center;
  gap:.35rem;
  opacity:.75;
}
.dot {
  width:6px;
  height:6px;
  border-radius:50%;
  background: currentColor;
  display:inline-block;
  animation: blink 1.2s infinite ease-in-out;
}
.dot:nth-child(2){ animation-delay:.2s; }
.dot:nth-child(3){ animation-delay:.4s; }
@keyframes blink { 0%,80%,100% { opacity:.2 } 40% { opacity:1 } }
</style>
""",
    unsafe_allow_html=True,
)


# Helper functions
def render_message(msg: dict):
    """Render a chat message with modern styling."""
    role = msg.get("role", "user")
    content = msg.get("content", "")
    css = "chat-bubble chat-user" if role == "user" else "chat-bubble chat-assistant"
    with st.chat_message(role):
        st.markdown(f'<div class="{css}">{content}</div>', unsafe_allow_html=True)


def transcript_to_markdown(messages: list[dict]) -> str:
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
if prompt := st.chat_input("Ask anything... Press Enter to send"):
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
            for chunk in provider.stream_complete(chat_store.get_messages()):
                if st.session_state.get("stop_requested", False):
                    break
                accumulator.append(chunk)
                placeholder.markdown(
                    f'<div class="chat-bubble chat-assistant">{"".join(accumulator)}</div>',
                    unsafe_allow_html=True,
                )

            # Finalize
            final_text = "".join(accumulator)

            # Add assistant's response to conversation history (once)
            chat_store.add_message("assistant", final_text)

            # Update placeholder with final text
            placeholder.markdown(
                f'<div class="chat-bubble chat-assistant">{final_text}</div>',
                unsafe_allow_html=True,
            )

    except Exception as e:
        # Handle errors with humanized messages (single path)
        error_msg = humanize_error(e)
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
    st.subheader("📋 Session")
    st.caption(f"Env: {config.env} • Session: {sid[:8]}… • Store: {backend_label}")

    # History
    st.subheader("💬 History")
    message_count = chat_store.get_message_count()
    if message_count > 0:
        st.metric("Messages", message_count)

        # Clear conversation button
        if st.button("🗑️ Clear Conversation"):
            chat_store.clear()
            st.rerun()

        # New Chat button
        if st.button("🆕 New Chat"):
            new_sid = uuid.uuid4().hex
            st.query_params["sid"] = new_sid
            chat_store.clear()
            st.rerun()
    else:
        st.text("No messages yet")

    # Export
    st.subheader("📤 Export")
    msgs = chat_store.get_messages()
    if msgs:
        md_bytes = transcript_to_markdown(msgs).encode("utf-8")
        json_bytes = json.dumps(msgs, ensure_ascii=False, indent=2).encode("utf-8")

        st.download_button(
            "📄 Markdown", data=md_bytes, file_name="chat.md", mime="text/markdown"
        )
        st.download_button(
            "📋 JSON", data=json_bytes, file_name="chat.json", mime="application/json"
        )
    else:
        st.text("No conversation to export")

    # Controls
    st.subheader("🎮 Controls")

    # Stop button (only visible during generation)
    if st.session_state.get("generating", False):
        if st.button("🛑 Stop", help="Stop the current response generation"):
            st.session_state["stop_requested"] = True
            st.rerun()

    # Model & behavior
    st.subheader("🤖 Model & Behavior")
    st.text(f"Model: {config.openai_model}")

    # Temperature slider (educational)
    temp = st.slider(
        "Creativity (temperature)",
        0.0,
        1.0,
        value=st.session_state["temperature"],
        step=0.05,
        help="Higher = more creative. Kept for learning; provider may ignore for now.",
    )
    st.session_state["temperature"] = temp

    # Learning info
    st.subheader("📚 Learning")
    st.markdown("""
    **Key Concepts:**
    - Always-on streaming
    - Built-in theme system
    - Persistent history
    - Error handling
    - Clean UI design
    """)

    # Debug diagnostics (only when DEBUG_UI=1)
    if DEBUG_UI:
        st.subheader("🔧 Debug")
        st.text("UI Diagnostics:")
        st.text("• Block container padding-top: 2rem")
        st.text("• Heading line-height: 1.25")
        st.text("• Heading margins: 0.25rem 0")
        st.text("• Letter spacing: 0.01em")
        st.text("")
        st.text("If header still clips:")
        st.text("• Check browser DevTools")
        st.text("• Look for CSS overrides")
        st.text("• Try hard refresh")
