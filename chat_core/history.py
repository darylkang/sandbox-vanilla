"""
Chat history storage interfaces and implementations.

StreamlitStore: In-memory storage using st.session_state that persists
across app reruns but not browser refreshes. Good for learning and development.

RedisStore: Server-side persistent storage that survives browser refreshes
and server restarts. Located in chat_core/store with the same interface.
"""

from abc import ABC, abstractmethod
from typing import Dict, List


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

    def __init__(self, session_key: str = "messages", max_turns: int = 20):
        """
        Initialize Streamlit store.

        Args:
            session_key: Key to use in st.session_state for storing messages.
            max_turns: Maximum conversation turns to keep (user+assistant pairs)
        """
        self.session_key = session_key
        self.max_turns = max_turns
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

        st.session_state[self.session_key].append({"role": role, "content": content})
        # Trim to last max_turns*2 messages (user+assistant pairs)
        maxlen = self.max_turns * 2
        if maxlen > 0:
            st.session_state[self.session_key] = st.session_state[self.session_key][-maxlen:]

    def clear(self) -> None:
        """Clear all messages from Streamlit session state."""
        import streamlit as st

        st.session_state[self.session_key] = []

    def get_message_count(self) -> int:
        """Get the number of stored messages."""
        return len(self.get_messages())
