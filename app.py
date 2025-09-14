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

import html
import json
import logging
import os
import uuid
from datetime import datetime
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

# Inject refined theme-aware CSS
st.markdown(
    """
<style>
/* System font stack for Apple-esque typography */
* {
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}

/* Container & typography */
.block-container {
  max-width: 900px;
  padding-top: 2rem;
  padding-bottom: 2rem;
}

h1, h2, h3 {
  margin: .25rem 0;
  line-height: 1.25;
  letter-spacing: .01em;
}

/* Chat bubbles with refined styling */
.bubble {
  padding: .75rem 1rem;
  border-radius: 14px;
  margin: .25rem 0 .9rem;
  border: 1px solid rgba(0,0,0,0.06);
  position: relative;
}

.bubble.user {
  background: rgba(10,132,255,0.10);
}

.bubble.assistant {
  background: rgba(127,127,127,0.10);
}

/* Dark mode adjustments */
@media (prefers-color-scheme: dark) {
  .bubble {
    border-color: rgba(255,255,255,0.12);
  }
  .bubble.user {
    background: rgba(10,132,255,0.18);
  }
  .bubble.assistant {
    background: rgba(255,255,255,0.06);
  }
}

/* Message row with avatar and content */
.row {
  display: flex;
  gap: .6rem;
  align-items: flex-start;
  margin-bottom: .5rem;
}

.avatar {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  background: transparent;
  flex-shrink: 0;
  margin-top: .2rem;
}

.meta {
  font-size: 12px;
  opacity: .7;
  margin-top: .35rem;
  color: var(--text-color, inherit);
}

/* Markdown styling inside assistant bubbles */
.bubble.assistant h1 {
  font-size: 1.25rem;
  margin: .5rem 0 .25rem 0;
}

.bubble.assistant h2 {
  font-size: 1.15rem;
  margin: .4rem 0 .2rem 0;
}

.bubble.assistant h3 {
  font-size: 1.05rem;
  margin: .3rem 0 .15rem 0;
}

.bubble.assistant pre {
  padding: .6rem .8rem;
  border-radius: 10px;
  border: 1px solid rgba(0,0,0,0.06);
  overflow: auto;
  background: rgba(0,0,0,0.02);
  margin: .5rem 0;
}

.bubble.assistant code {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace;
  font-size: .9em;
  background: rgba(0,0,0,0.05);
  padding: .1rem .3rem;
  border-radius: 4px;
}

.bubble.assistant blockquote {
  margin: .5rem 0;
  padding-left: .8rem;
  border-left: 3px solid rgba(127,127,127,0.4);
  opacity: .9;
}

.bubble.assistant ul, .bubble.assistant ol {
  margin: .5rem 0;
  padding-left: 1.2rem;
}

.bubble.assistant li {
  margin: .2rem 0;
}

.bubble.assistant table {
  border-collapse: collapse;
  width: 100%;
  margin: .5rem 0;
}

.bubble.assistant th, .bubble.assistant td {
  border: 1px solid rgba(0,0,0,0.1);
  padding: .4rem .6rem;
  text-align: left;
}

.bubble.assistant th {
  background: rgba(0,0,0,0.05);
  font-weight: 600;
}

/* Dark mode for code blocks */
@media (prefers-color-scheme: dark) {
  .bubble.assistant pre {
    border-color: rgba(255,255,255,0.12);
    background: rgba(255,255,255,0.05);
  }
  .bubble.assistant code {
    background: rgba(255,255,255,0.1);
  }
  .bubble.assistant th {
    background: rgba(255,255,255,0.1);
  }
  .bubble.assistant th, .bubble.assistant td {
    border-color: rgba(255,255,255,0.15);
  }
}

/* Copy affordance */
.actions {
  display: flex;
  gap: .5rem;
  justify-content: flex-end;
  margin-top: .25rem;
  opacity: 0;
  transition: opacity .15s ease;
}

.bubble:hover + .actions, .bubble:hover .actions, .row:hover .actions {
  opacity: .9;
}

/* Typing indicator */
.typing {
  display: inline-flex;
  align-items: center;
  gap: .35rem;
  opacity: .75;
}

.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
  display: inline-block;
  animation: blink 1.2s infinite ease-in-out;
}

.dot:nth-child(2) { animation-delay: .2s; }
.dot:nth-child(3) { animation-delay: .4s; }

@keyframes blink {
  0%, 80%, 100% { opacity: .2 }
  40% { opacity: 1 }
}

/* Input area styling */
.stChatInput > div > div > div {
  border-radius: 12px;
}

/* Subtle divider above input */
.stChatInput {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid rgba(0,0,0,0.08);
}

@media (prefers-color-scheme: dark) {
  .stChatInput {
    border-top-color: rgba(255,255,255,0.12);
  }
}
</style>
""",
    unsafe_allow_html=True,
)


# Helper functions
def render_message(msg: Dict[str, str]):
    """Render a chat message with refined styling, avatar, and metadata."""
    role = msg.get("role", "user")
    content = msg.get("content", "")
    timestamp = msg.get("timestamp", "")

    # Avatar emoji based on role
    avatar = "👤" if role == "user" else "🤖"

    # Create message row with avatar and bubble
    with st.chat_message(role):
        # Use st.markdown for proper Markdown rendering in assistant messages
        if role == "assistant":
            # For assistant messages, render as Markdown for proper formatting
            st.markdown(
                f'''
                <div class="row">
                    <div class="avatar">{avatar}</div>
                    <div class="bubble assistant">{content}</div>
                </div>
                {f'<div class="meta">{timestamp}</div>' if timestamp else ''}
                ''',
                unsafe_allow_html=True
            )
        else:
            # For user messages, escape HTML and use simple div
            safe_content = html.escape(content)
            st.markdown(
                f'''
                <div class="row">
                    <div class="avatar">{avatar}</div>
                    <div class="bubble user">{safe_content}</div>
                </div>
                {f'<div class="meta">{timestamp}</div>' if timestamp else ''}
                ''',
                unsafe_allow_html=True
            )


def message_actions(msg: Dict[str, str]):
    """Add copy button and other message actions."""
    content = msg.get("content", "")
    if content:
        # Use st.code with copy functionality for code blocks
        if "```" in content:
            # Extract and display code blocks with copy functionality
            import re
            code_blocks = re.findall(r'```(\w+)?\n(.*?)\n```', content, re.DOTALL)
            for lang, code in code_blocks:
                st.code(code, language=lang or "text")

        # Add a subtle copy hint
        st.caption("💡 Hover over messages to see copy options")


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

# Input area with refined placeholder
if prompt := st.chat_input("Ask anything... Enter to send • Shift+Enter for newline"):
    # Add user message to conversation history with timestamp
    timestamp = datetime.now().strftime("%H:%M")
    chat_store.add_message("user", prompt)

    # Display the user's message immediately
    render_message({"role": "user", "content": prompt, "timestamp": timestamp})

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
                # Render partial content with new styling
                partial_content = "".join(accumulator)
                placeholder.markdown(
                    f'''
                    <div class="row">
                        <div class="avatar">🤖</div>
                        <div class="bubble assistant">{partial_content}</div>
                    </div>
                    ''',
                    unsafe_allow_html=True,
                )

            # Finalize
            final_text = "".join(accumulator)

            # Add assistant's response to conversation history (once)
            if final_text.strip():
                chat_store.add_message("assistant", final_text)

            # Update placeholder with final text and timestamp
            final_timestamp = datetime.now().strftime("%H:%M")
            placeholder.markdown(
                f'''
                <div class="row">
                    <div class="avatar">🤖</div>
                    <div class="bubble assistant">{final_text}</div>
                </div>
                <div class="meta">{final_timestamp}</div>
                ''',
                unsafe_allow_html=True,
            )

    except Exception:
        # Attempt non-streaming fallback before humanizing the error
        try:
            fallback_text = provider.complete(
                chat_store.get_messages(), temperature=st.session_state["temperature"]
            )
            chat_store.add_message("assistant", fallback_text)
            fallback_timestamp = datetime.now().strftime("%H:%M")
            render_message({"role": "assistant", "content": fallback_text, "timestamp": fallback_timestamp})
        except Exception as inner:
            # Handle errors with humanized messages (single path)
            error_msg = humanize_error(inner)
            chat_store.add_message("assistant", error_msg)
            error_timestamp = datetime.now().strftime("%H:%M")
            render_message({"role": "assistant", "content": error_msg, "timestamp": error_timestamp})

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
