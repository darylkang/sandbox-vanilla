"""
Chat history storage interfaces and implementations.

Provides abstraction for storing and retrieving chat messages with
Streamlit session state as the initial implementation.

Note: RedisStore lives in chat_core/store and shares the same interface
for persistent storage that survives browser refreshes and server restarts.
"""

from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod


class ChatStore(ABC):
    """Abstract interface for chat history storage."""
    
    @abstractmethod
    def get_messages(self) -> List[Dict[str, str]]:
        """Get all stored messages."""
        pass
    
    @abstractmethod
    def add_message(self, role: str, content: str) -> None:
        """Add a message to storage."""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all stored messages."""
        pass
    
    @abstractmethod
    def get_message_count(self) -> int:
        """Get the number of stored messages."""
        pass


class StreamlitStore(ChatStore):
    """Streamlit session state implementation of ChatStore."""
    
    def __init__(self, session_key: str = "messages"):
        """
        Initialize Streamlit store.
        
        Args:
            session_key: Key to use in st.session_state for storing messages.
        """
        self.session_key = session_key
        self._ensure_initialized()
    
    def _ensure_initialized(self) -> None:
        """Ensure the session state is initialized with an empty message list."""
        import streamlit as st
        
        if self.session_key not in st.session_state:
            st.session_state[self.session_key] = []
    
    def get_messages(self) -> List[Dict[str, str]]:
        """Get all stored messages from Streamlit session state."""
        import streamlit as st
        return st.session_state[self.session_key]
    
    def add_message(self, role: str, content: str) -> None:
        """Add a message to Streamlit session state."""
        import streamlit as st
        st.session_state[self.session_key].append({
            "role": role,
            "content": content
        })
    
    def clear(self) -> None:
        """Clear all messages from Streamlit session state."""
        import streamlit as st
        st.session_state[self.session_key] = []
    
    def get_message_count(self) -> int:
        """Get the number of stored messages."""
        return len(self.get_messages())
