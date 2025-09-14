"""
LLM provider abstraction and OpenAI implementation.

Provides a unified interface for different LLM services with OpenAI
as the initial implementation, including both batch and streaming completions.
"""

from typing import List, Dict, Any, Optional, Union, Iterator
from openai import OpenAI
from .config import ChatConfig, AppConfig


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
    
    def stream_complete(self, messages: List[Dict[str, str]]) -> Iterator[str]:
        """
        Stream completion tokens as they arrive.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys.
            
        Yields:
            Text chunks as they arrive from the provider.
            
        Raises:
            Exception: If the streaming fails.
        """
        raise NotImplementedError


class OpenAIProvider(LLMProvider):
    """OpenAI Chat Completions API provider."""
    
    def __init__(self, config: Union[ChatConfig, AppConfig]):
        """
        Initialize OpenAI provider with configuration.
        
        Args:
            config: ChatConfig or AppConfig containing API key and model settings.
        """
        # Handle both legacy ChatConfig and new AppConfig
        if hasattr(config, 'openai_api_key'):
            api_key = config.openai_api_key
        else:
            api_key = config.api_key
            
        self.client = OpenAI(api_key=api_key)
        self.config = config
    
    def complete(self, messages: List[Dict[str, str]]) -> str:
        """
        Generate a completion using OpenAI's Chat Completions API (non-streaming).
        
        Returns the complete response text after generation finishes.
        Use this for traditional request-response patterns.
        
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
    
    def stream_complete(self, messages: List[Dict[str, str]]) -> Iterator[str]:
        """
        Stream completion tokens from OpenAI as they arrive (real-time).
        
        Yields text chunks as they're generated, allowing the UI to update
        incrementally. The UI aggregates these chunks into the final response.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys.
            
        Yields:
            Text chunks as they arrive from OpenAI.
            
        Raises:
            Exception: If the streaming API call fails.
        """
        stream = self.client.chat.completions.create(
            messages=messages,
            stream=True,
            **self.config.to_dict()
        )
        
        for event in stream:
            try:
                delta = event.choices[0].delta
                content = getattr(delta, "content", None)
                if content:
                    yield content
            except (AttributeError, IndexError, KeyError):
                # Skip malformed events safely
                continue
