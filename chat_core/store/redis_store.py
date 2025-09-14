"""
Redis-backed chat history storage with TTL and message trimming.

Provides persistent storage for chat messages that survives browser refreshes
and server restarts. Uses Redis lists with automatic trimming and expiration.
"""

import json
import time
from functools import lru_cache
from typing import List, Dict, Optional
from redis import Redis


@lru_cache(maxsize=8)
def _get_client(url: str) -> Redis:
    """
    Memoized Redis client factory to avoid reconnecting on every rerun.
    
    Args:
        url: Redis connection URL
        
    Returns:
        Redis client instance
    """
    return Redis.from_url(url, decode_responses=True)


class RedisStore:
    """
    Redis-backed chat history storage with TTL and message trimming.
    
    Stores messages as JSON in Redis lists with automatic trimming to keep
    only the last N conversation turns and TTL for automatic expiration.
    """
    
    def __init__(self, sid: str, url: str, max_turns: int = 20, ttl_seconds: int = 30*24*3600):
        """
        Initialize Redis store for a specific session.
        
        Args:
            sid: Session ID for this conversation
            url: Redis connection URL
            max_turns: Maximum conversation turns to keep (user+assistant pairs)
            ttl_seconds: Time-to-live for the session data (default: 30 days)
        """
        self.sid = sid
        self.url = url
        self.max_turns = max_turns
        self.ttl_seconds = ttl_seconds
        
        # Create Redis client and test connection
        self._redis = _get_client(url)
        try:
            self._redis.ping()
            self._healthy = True
        except Exception:
            self._healthy = False
    
    def _key_msgs(self) -> str:
        """Get Redis key for this session's messages."""
        return f"session:{self.sid}:messages"
    
    def add_message(self, role: str, content: str) -> None:
        """
        Add a message to the conversation history.
        
        Args:
            role: Message role (user, assistant, system)
            content: Message content
        """
        # Normalize role to valid values
        if role not in {"user", "assistant", "system"}:
            role = "user"
        
        # Create message with timestamp
        message = {
            "role": role,
            "content": content,
            "ts": int(time.time())
        }
        
        key = self._key_msgs()
        
        # Add message to Redis list
        self._redis.rpush(key, json.dumps(message))
        
        # Trim to keep only last max_turns*2 items (user+assistant pairs)
        maxlen = self.max_turns * 2
        self._redis.ltrim(key, -maxlen, -1)
        
        # Reset TTL on each write
        self._redis.expire(key, self.ttl_seconds)
    
    def get_messages(self) -> List[Dict[str, str]]:
        """
        Get all messages for this session.
        
        Returns:
            List of message dictionaries with 'role' and 'content' keys
        """
        key = self._key_msgs()
        items = self._redis.lrange(key, 0, -1)
        
        messages = []
        for item in items:
            try:
                data = json.loads(item)
                # Return only role and content for compatibility
                messages.append({
                    "role": data["role"],
                    "content": data["content"]
                })
            except (json.JSONDecodeError, KeyError):
                # Skip malformed messages
                continue
        
        return messages
    
    def get_message_count(self) -> int:
        """
        Get the number of messages in this session.
        
        Returns:
            Number of stored messages
        """
        key = self._key_msgs()
        return self._redis.llen(key)
    
    def clear(self) -> None:
        """Clear all messages for this session."""
        key = self._key_msgs()
        self._redis.delete(key)
    
    def is_healthy(self) -> bool:
        """
        Check if Redis connection is healthy.
        
        Returns:
            True if Redis is reachable, False otherwise
        """
        return self._healthy
