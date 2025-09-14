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

/* Cyberpunk tropical background */
.stApp {
  background: linear-gradient(135deg, var(--bg0) 0%, #1a1a1a 50%, var(--bg1) 100%);
  background-attachment: fixed;
}

/* Main container with neon glow */
.block-container {
  max-width: 900px;
  padding: 2rem 1rem;
  background: rgba(40, 40, 40, 0.95);
  border-radius: 20px;
  border: 2px solid var(--bright-aqua);
  box-shadow:
    0 0 30px rgba(139, 233, 253, 0.3),
    inset 0 0 30px rgba(139, 233, 253, 0.1);
  backdrop-filter: blur(10px);
}

/* Cyberpunk title styling */
h1 {
  color: var(--bright-aqua);
  text-shadow: 0 0 10px var(--bright-aqua);
  font-family: 'Courier New', monospace;
  font-weight: bold;
  text-transform: uppercase;
  letter-spacing: 2px;
  margin-bottom: 0.5rem;
}

/* Tropical caption */
.stCaption {
  color: var(--bright-green);
  font-family: 'Courier New', monospace;
  font-size: 0.9rem;
  text-shadow: 0 0 5px var(--bright-green);
}

/* Chat message styling */
.stChatMessage {
  background: rgba(60, 56, 54, 0.8);
  border-radius: 15px;
  border: 1px solid var(--bright-purple);
  margin: 1rem 0;
  padding: 1rem;
  box-shadow: 0 0 15px rgba(177, 98, 134, 0.2);
}

/* User messages - tropical blue */
.stChatMessage[data-testid="user"] {
  background: linear-gradient(135deg, rgba(69, 133, 136, 0.3), rgba(131, 165, 152, 0.2));
  border-color: var(--bright-blue);
  box-shadow: 0 0 15px rgba(131, 165, 152, 0.3);
}

/* Assistant messages - cyberpunk purple */
.stChatMessage[data-testid="assistant"] {
  background: linear-gradient(135deg, rgba(177, 98, 134, 0.3), rgba(211, 134, 155, 0.2));
  border-color: var(--bright-purple);
  box-shadow: 0 0 15px rgba(211, 134, 155, 0.3);
}

/* Text styling */
.stMarkdown {
  color: var(--fg);
  font-family: 'Courier New', monospace;
  line-height: 1.6;
}

/* Code blocks - gruvbox style */
.stMarkdown pre {
  background: var(--bg1);
  border: 1px solid var(--bright-orange);
  border-radius: 10px;
  padding: 1rem;
  color: var(--bright-yellow);
  font-family: 'Courier New', monospace;
  box-shadow: 0 0 10px rgba(215, 153, 33, 0.3);
}

.stMarkdown code {
  background: var(--bg2);
  color: var(--bright-green);
  padding: 0.2rem 0.4rem;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  border: 1px solid var(--green);
}

/* Links - tropical aqua */
.stMarkdown a {
  color: var(--bright-aqua);
  text-decoration: none;
  text-shadow: 0 0 5px var(--bright-aqua);
}

.stMarkdown a:hover {
  color: var(--bright-blue);
  text-shadow: 0 0 10px var(--bright-blue);
}

/* Input styling */
.stChatInput > div > div > div {
  background: var(--bg1);
  border: 2px solid var(--bright-green);
  border-radius: 15px;
  color: var(--fg);
  font-family: 'Courier New', monospace;
  box-shadow: 0 0 15px rgba(184, 187, 38, 0.3);
}

.stChatInput > div > div > div:focus {
  border-color: var(--bright-aqua);
  box-shadow: 0 0 20px rgba(139, 233, 253, 0.5);
}

/* Sidebar styling */
.stSidebar {
  background: linear-gradient(180deg, var(--bg0), var(--bg1));
  border-right: 2px solid var(--bright-purple);
}

.stSidebar .stMarkdown {
  color: var(--fg);
}

/* Buttons - cyberpunk style */
.stButton > button {
  background: linear-gradient(45deg, var(--bright-purple), var(--bright-blue));
  color: var(--bg0);
  border: none;
  border-radius: 10px;
  font-family: 'Courier New', monospace;
  font-weight: bold;
  text-transform: uppercase;
  letter-spacing: 1px;
  box-shadow: 0 0 15px rgba(211, 134, 155, 0.4);
  transition: all 0.3s ease;
}

.stButton > button:hover {
  background: linear-gradient(45deg, var(--bright-blue), var(--bright-aqua));
  box-shadow: 0 0 25px rgba(139, 233, 253, 0.6);
  transform: translateY(-2px);
}

/* Slider styling */
.stSlider > div > div > div > div {
  background: var(--bright-aqua);
  box-shadow: 0 0 10px var(--bright-aqua);
}

/* Typing indicator - cyberpunk style */
.typing {
  display: inline-flex;
  align-items: center;
  gap: .5rem;
  color: var(--bright-aqua);
  font-family: 'Courier New', monospace;
  text-shadow: 0 0 5px var(--bright-aqua);
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--bright-aqua);
  display: inline-block;
  animation: cyberpunk-blink 1.5s infinite ease-in-out;
  box-shadow: 0 0 10px var(--bright-aqua);
}

.dot:nth-child(2) { animation-delay: .3s; }
.dot:nth-child(3) { animation-delay: .6s; }

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

/* Scrollbar styling */
::-webkit-scrollbar {
  width: 8px;
}

::-webkit-scrollbar-track {
  background: var(--bg1);
}

::-webkit-scrollbar-thumb {
  background: var(--bright-purple);
  border-radius: 4px;
  box-shadow: 0 0 5px var(--bright-purple);
}

::-webkit-scrollbar-thumb:hover {
  background: var(--bright-aqua);
  box-shadow: 0 0 10px var(--bright-aqua);
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
