"""
Configuration management for chat applications.

Handles loading of API keys, model settings, and Redis configuration
from Streamlit secrets or environment variables with proper fallback mechanisms.
"""

import os
from dataclasses import dataclass
from typing import Optional, Dict, Any
import streamlit as st


@dataclass(frozen=True)
class AppConfig:
    """Frozen configuration container for all application settings."""
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    redis_url: Optional[str] = None
    history_max_turns: int = 20
    history_ttl_seconds: int = 30*24*3600  # 30 days
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for API calls."""
        return {
            "model": self.openai_model,
        }


class ChatConfig:
    """Legacy configuration container for backwards compatibility."""
    
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


def load_config_from_streamlit() -> Optional[AppConfig]:
    """
    Load configuration from Streamlit secrets.
    
    Returns:
        AppConfig if secrets are available and contain required keys, None otherwise.
    """
    try:
        if hasattr(st, 'secrets') and st.secrets:
            api_key = st.secrets.get("OPENAI_API_KEY")
            model = st.secrets.get("OPENAI_MODEL", "gpt-4o-mini")
            redis_url = st.secrets.get("REDIS_URL")
            max_turns = int(st.secrets.get("HISTORY_MAX_TURNS", "20"))
            ttl_seconds = int(st.secrets.get("HISTORY_TTL_SECONDS", str(30*24*3600)))
            
            if api_key:
                return AppConfig(
                    openai_api_key=api_key,
                    openai_model=model,
                    redis_url=redis_url,
                    history_max_turns=max_turns,
                    history_ttl_seconds=ttl_seconds
                )
    except Exception:
        # Secrets system not available or failed
        pass
    
    return None


def load_config_from_env() -> Optional[AppConfig]:
    """
    Load configuration from environment variables.
    
    Returns:
        AppConfig if environment variables are set, None otherwise.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    redis_url = os.getenv("REDIS_URL")
    max_turns = int(os.getenv("HISTORY_MAX_TURNS", "20"))
    ttl_seconds = int(os.getenv("HISTORY_TTL_SECONDS", str(30*24*3600)))
    
    if api_key:
        return AppConfig(
            openai_api_key=api_key,
            openai_model=model,
            redis_url=redis_url,
            history_max_turns=max_turns,
            history_ttl_seconds=ttl_seconds
        )
    
    return None


def load_config() -> AppConfig:
    """
    Load configuration with fallback: Streamlit secrets -> environment variables.
    
    Returns:
        AppConfig with loaded settings.
        
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
