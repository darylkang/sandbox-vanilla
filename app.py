import os
from typing import List, Dict

import streamlit as st
from openai import OpenAI


st.title("ChatGPT-like Chatbot")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages: List[Dict[str, str]] = []


def get_client() -> OpenAI:
    """Create an OpenAI client using an API key from env or Streamlit secrets."""
    api_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("OPENAI_API_KEY is not set.\n\nSet it via environment variable or Streamlit secrets.")
        st.stop()
    return OpenAI(api_key=api_key)


# Display chat messages from history on app rerun
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Accept user input
if prompt := st.chat_input("Ask the bot..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    client = get_client()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
    )
    reply = response.choices[0].message.content
    st.session_state.messages.append({"role": "assistant", "content": reply})
    with st.chat_message("assistant"):
        st.markdown(reply)
