"""
LLM provider abstraction and OpenAI implementation.

Provides a unified interface for different LLM services with OpenAI
as the initial implementation.
"""

from typing import List, Dict, Any, Optional
from openai import OpenAI
from .config import ChatConfig


class LLMProvider:
    """Abstract base class for LLM providers."""
    
    def complete(self, messages: List[Dict[str, str]]) -> str:
        """
        Generate a completion for the given messages.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys.
            
        Returns:
            Generated response text.
            
        Raises:
            Exception: If the completion fails.
        """
        raise NotImplementedError


class OpenAIProvider(LLMProvider):
    """OpenAI Chat Completions API provider."""
    
    def __init__(self, config: ChatConfig):
        """
        Initialize OpenAI provider with configuration.
        
        Args:
            config: ChatConfig containing API key and model settings.
        """
        self.client = OpenAI(api_key=config.api_key)
        self.config = config
    
    def complete(self, messages: List[Dict[str, str]]) -> str:
        """
        Generate a completion using OpenAI's Chat Completions API.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys.
            
        Returns:
            Generated response text.
            
        Raises:
            Exception: If the API call fails.
        """
        response = self.client.chat.completions.create(
            messages=messages,
            **self.config.to_dict()
        )
        
        return response.choices[0].message.content
