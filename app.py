"""
Educational LLM Chatbot with Streamlit

This is a minimal example demonstrating how to:
1. Create a chat interface using Streamlit
2. Integrate with OpenAI's API
3. Manage conversation state
4. Handle API authentication

Key Learning Concepts:
- Streamlit session state for maintaining conversation history
- OpenAI API integration for LLM responses
- Environment variable management for API keys
- Chat UI patterns with message roles (user/assistant)
"""

import os
from typing import List, Dict

import streamlit as st
from openai import OpenAI

# Set the page title and configuration
st.set_page_config(
    page_title="Educational LLM Chatbot",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Educational LLM Chatbot")
st.markdown("*Learn how to build a ChatGPT-like interface with Streamlit and OpenAI*")

# Initialize chat history in session state
# Session state persists data across reruns of the app
# This is crucial for maintaining conversation history
if "messages" not in st.session_state:
    st.session_state.messages: List[Dict[str, str]] = []


def get_client() -> OpenAI:
    """
    Create an OpenAI client using an API key from environment or Streamlit secrets.
    
    This function demonstrates two common ways to handle API keys:
    1. Environment variables (recommended for local development)
    2. Streamlit secrets (recommended for deployed apps)
    
    Returns:
        OpenAI: Configured OpenAI client ready to make API calls
        
    Raises:
        SystemExit: If no API key is found, stops the app with an error message
    """
    # Try to get API key from Streamlit secrets first, then environment variables
    # This order allows for easy deployment while supporting local development
    api_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        st.error("""
        🔑 **API Key Required**
        
        To use this chatbot, you need an OpenAI API key. Set it using one of these methods:
        
        **Option 1: Environment Variable (Recommended for local development)**
        ```bash
        export OPENAI_API_KEY="your-api-key-here"
        ```
        
        **Option 2: Streamlit Secrets (For deployed apps)**
        Create `.streamlit/secrets.toml` with:
        ```toml
        OPENAI_API_KEY = "your-api-key-here"
        ```
        
        Get your API key from: https://platform.openai.com/api-keys
        """)
        st.stop()
    
    return OpenAI(api_key=api_key)


# Display chat messages from history on app rerun
# This loop renders all previous messages when the app refreshes
# Each message is displayed with the appropriate role (user/assistant)
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Accept user input using Streamlit's chat input widget
# The walrus operator (:=) assigns and checks the prompt in one line
if prompt := st.chat_input("Ask the bot anything..."):
    # Add user message to conversation history
    # This maintains the full conversation context for the API
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display the user's message immediately for better UX
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get the OpenAI client (handles API key validation)
    client = get_client()
    
    # Make API call to OpenAI's Chat Completions endpoint
    # This is the core of LLM integration - sending messages and getting responses
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Using GPT-4o-mini for cost efficiency
            messages=[
                {"role": m["role"], "content": m["content"]} 
                for m in st.session_state.messages
            ],
            # Optional parameters you can experiment with:
            # temperature=0.7,  # Controls randomness (0.0 = deterministic, 1.0 = very random)
            # max_tokens=1000,  # Maximum length of response
            # top_p=1.0,       # Nucleus sampling parameter
        )
        
        # Extract the response content from the API response
        reply = response.choices[0].message.content
        
        # Add assistant's response to conversation history
        st.session_state.messages.append({"role": "assistant", "content": reply})
        
        # Display the assistant's response
        with st.chat_message("assistant"):
            st.markdown(reply)
            
    except Exception as e:
        # Handle API errors gracefully
        error_msg = f"❌ **API Error**: {str(e)}"
        st.session_state.messages.append({"role": "assistant", "content": error_msg})
        with st.chat_message("assistant"):
            st.markdown(error_msg)

# Add educational sidebar with learning resources
with st.sidebar:
    st.header("📚 Learning Resources")
    
    st.markdown("""
    **Key Concepts Demonstrated:**
    
    🔄 **Session State**: Maintains conversation across app reruns
    
    🔌 **API Integration**: Direct connection to OpenAI's API
    
    💬 **Chat UI**: Streamlit's chat components for modern interface
    
    🔐 **Authentication**: Secure API key management
    
    **Next Steps to Explore:**
    - Try different models (gpt-3.5-turbo, gpt-4)
    - Experiment with temperature and other parameters
    - Add conversation export/import
    - Implement custom system prompts
    - Add conversation memory persistence
    """)
    
    # Show current conversation stats
    if st.session_state.messages:
        st.metric("Messages in Conversation", len(st.session_state.messages))
        
        # Clear conversation button
        if st.button("🗑️ Clear Conversation"):
            st.session_state.messages = []
            st.rerun()
