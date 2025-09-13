"""
Educational LLM Chatbot with Streamlit

Stage 1: Modularized chat application demonstrating:
1. Clean separation of concerns with chat_core package
2. Configuration management for API keys and models
3. Provider abstraction for LLM services
4. Chat history storage interfaces
5. User-friendly error handling

Key Learning Concepts:
- Modular architecture patterns
- Dependency injection and abstraction
- Error handling and user experience
- Streamlit integration with custom packages
"""

import streamlit as st
from chat_core.config import load_config
from chat_core.provider import OpenAIProvider
from chat_core.history import StreamlitStore
from chat_core.errors import humanize_error

# Set the page title and configuration
st.set_page_config(
    page_title="Educational LLM Chatbot",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Educational LLM Chatbot")
st.markdown("*Stage 1: Modularized architecture with chat_core package*")

# Initialize chat history store
chat_store = StreamlitStore()


# Display chat messages from history on app rerun
for msg in chat_store.get_messages():
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Accept user input using Streamlit's chat input widget
if prompt := st.chat_input("Ask the bot anything..."):
    # Add user message to conversation history
    chat_store.add_message("user", prompt)
    
    # Display the user's message immediately
    with st.chat_message("user"):
        st.markdown(prompt)

    # Load configuration and initialize provider
    try:
        config = load_config()
        provider = OpenAIProvider(config)
        
        # Generate response using the provider
        with st.spinner("🤔 Thinking..."):
            reply = provider.complete(chat_store.get_messages())
        
        # Add assistant's response to conversation history
        chat_store.add_message("assistant", reply)
        
        # Display the assistant's response
        with st.chat_message("assistant"):
            st.markdown(reply)
            
    except Exception as e:
        # Handle errors with humanized messages
        error_msg = humanize_error(e)
        chat_store.add_message("assistant", error_msg)
        with st.chat_message("assistant"):
            st.markdown(error_msg)

# Add educational sidebar with learning resources
with st.sidebar:
    st.header("📚 Stage 1: Modular Architecture")
    
    st.markdown("""
    **Key Concepts Demonstrated:**
    
    🏗️ **Modular Design**: Clean separation of concerns
    
    ⚙️ **Configuration**: Centralized config management
    
    🔌 **Provider Pattern**: Abstracted LLM integration
    
    💾 **Storage Interface**: Pluggable chat history
    
    🛡️ **Error Handling**: User-friendly error messages
    
    **Architecture Components:**
    - `config.py`: API key and model configuration
    - `provider.py`: OpenAI provider implementation
    - `history.py`: Streamlit storage implementation
    - `errors.py`: Error message humanization
    """)
    
    # Show current conversation stats
    message_count = chat_store.get_message_count()
    if message_count > 0:
        st.metric("Messages in Conversation", message_count)
        
        # Clear conversation button
        if st.button("🗑️ Clear Conversation"):
            chat_store.clear()
            st.rerun()
    
    st.markdown("""
    **Future Stages:**
    - Stage 2: FastAPI sidecar for API endpoints
    - Stage 3: Redis streaming and persistence
    - Stage 4: Multiple provider support
    """)
