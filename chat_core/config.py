"""
Configuration management for chat applications.

Handles loading of API keys, model settings, and Redis configuration
from environment variables, .env files, and Streamlit secrets with proper precedence.
"""

import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

import streamlit as st
from dotenv import load_dotenv

# Load .env file if present (env vars take precedence)
load_dotenv()


@dataclass(frozen=True)
class AppConfig:
    """Frozen configuration container for all application settings."""

    env: str
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    redis_url: Optional[str] = None
    history_max_turns: int = 20
    history_ttl_seconds: int = 3600  # 1 hour (dev default)
    key_prefix: str = ""

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
        return {"model": self.model, **self.extra_params}


def _get_env_aware_defaults(env: str) -> Dict[str, Any]:
    """Get environment-aware default values."""
    defaults = {
        "dev": {
            "history_ttl_seconds": 3600,  # 1 hour
        },
        "staging": {
            "history_ttl_seconds": 30 * 24 * 3600,  # 30 days
        },
        "prod": {
            "history_ttl_seconds": 30 * 24 * 3600,  # 30 days
        },
    }
    return defaults.get(env, defaults["dev"])


def load_config() -> AppConfig:
    """
    Load configuration with precedence: env vars > .env > Streamlit secrets > defaults.

    Returns:
        AppConfig with loaded settings.

    Raises:
        RuntimeError: If no valid configuration is found.
    """
    # Determine environment
    env = os.getenv("APP_ENV", "dev")
    env_defaults = _get_env_aware_defaults(env)

    # Try Streamlit secrets first (for deployed apps)
    api_key = None
    model = "gpt-4o-mini"
    redis_url = None
    max_turns = 20
    ttl_seconds = env_defaults["history_ttl_seconds"]
    key_prefix = f"{env}:"

    try:
        if hasattr(st, "secrets") and st.secrets:
            api_key = st.secrets.get("OPENAI_API_KEY")
            model = st.secrets.get("OPENAI_MODEL", model)
            redis_url = st.secrets.get("REDIS_URL")
            max_turns = int(st.secrets.get("HISTORY_MAX_TURNS", str(max_turns)))
            ttl_seconds = int(st.secrets.get("HISTORY_TTL_SECONDS", str(ttl_seconds)))
            key_prefix = st.secrets.get("REDIS_KEY_PREFIX", key_prefix)
    except Exception:
        # Secrets system not available or failed
        pass

    # Override with environment variables (highest precedence)
    api_key = os.getenv("OPENAI_API_KEY", api_key)
    model = os.getenv("OPENAI_MODEL", model)
    redis_url = os.getenv("REDIS_URL", redis_url)
    max_turns = int(os.getenv("HISTORY_MAX_TURNS", str(max_turns)))
    ttl_seconds = int(os.getenv("HISTORY_TTL_SECONDS", str(ttl_seconds)))
    key_prefix = os.getenv("REDIS_KEY_PREFIX", key_prefix)

    if not api_key:
        raise RuntimeError(
            "No valid configuration found. Please set OPENAI_API_KEY via "
            "environment variable, .env file, or Streamlit secrets."
        )

    return AppConfig(
        env=env,
        openai_api_key=api_key,
        openai_model=model,
        redis_url=redis_url,
        history_max_turns=max_turns,
        history_ttl_seconds=ttl_seconds,
        key_prefix=key_prefix,
    )
