"""
Configuration management for chat applications.

Handles loading of API keys and model settings from Streamlit secrets
or environment variables with proper fallback mechanisms.
"""

import os
from typing import Optional, Dict, Any
import streamlit as st


class ChatConfig:
    """Configuration container for chat application settings."""
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini", **kwargs):
        self.api_key = api_key
        self.model = model
        self.extra_params = kwargs
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for API calls."""
        return {
            "model": self.model,
            **self.extra_params
        }


def load_config_from_streamlit() -> Optional[ChatConfig]:
    """
    Load configuration from Streamlit secrets.
    
    Returns:
        ChatConfig if secrets are available and contain required keys, None otherwise.
    """
    try:
        if hasattr(st, 'secrets') and st.secrets:
            api_key = st.secrets.get("OPENAI_API_KEY")
            model = st.secrets.get("OPENAI_MODEL", "gpt-4o-mini")
            
            if api_key:
                return ChatConfig(api_key=api_key, model=model)
    except Exception:
        # Secrets system not available or failed
        pass
    
    return None


def load_config_from_env() -> Optional[ChatConfig]:
    """
    Load configuration from environment variables.
    
    Returns:
        ChatConfig if environment variables are set, None otherwise.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    if api_key:
        return ChatConfig(api_key=api_key, model=model)
    
    return None


def load_config() -> ChatConfig:
    """
    Load configuration with fallback: Streamlit secrets -> environment variables.
    
    Returns:
        ChatConfig with loaded settings.
        
    Raises:
        RuntimeError: If no valid configuration is found.
    """
    # Try Streamlit secrets first (for deployed apps)
    config = load_config_from_streamlit()
    
    # Fallback to environment variables (for local development)
    if not config:
        config = load_config_from_env()
    
    if not config:
        raise RuntimeError(
            "No valid configuration found. Please set OPENAI_API_KEY via "
            "environment variable or Streamlit secrets."
        )
    
    return config
