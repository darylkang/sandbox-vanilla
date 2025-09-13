"""
Error handling and user-friendly error messages.

Maps common exceptions to human-readable error messages
for better user experience.
"""

from typing import Optional


def humanize_error(error: Exception) -> str:
    """
    Convert technical exceptions to user-friendly error messages.
    
    Args:
        error: The exception to humanize.
        
    Returns:
        Human-readable error message.
    """
    error_type = type(error).__name__
    error_str = str(error).lower()
    
    # Authentication errors
    if "AuthenticationError" in error_type or "InvalidApiKey" in error_str:
        return """
        🔑 **Authentication Error**
        
        Your OpenAI API key appears to be invalid or expired. Please:
        1. Check your API key is correct
        2. Verify it has sufficient credits
        3. Ensure it's properly set as an environment variable
        
        Get a new key at: https://platform.openai.com/api-keys
        """
    
    # Rate limiting errors
    elif "RateLimitError" in error_type or "rate limit" in error_str:
        return """
        ⏰ **Rate Limit Exceeded**
        
        You've hit OpenAI's rate limit. Please:
        1. Wait a few minutes before trying again
        2. Check your usage in the OpenAI dashboard
        3. Consider upgrading your plan if needed
        """
    
    # Connection errors
    elif "APIConnectionError" in error_type or "connection" in error_str:
        return """
        🌐 **Connection Error**
        
        Unable to connect to OpenAI's servers. Please:
        1. Check your internet connection
        2. Try again in a few moments
        3. Verify OpenAI's service status
        """
    
    # Permission errors
    elif "PermissionError" in error_type or "permission" in error_str:
        return """
        🚫 **Permission Error**
        
        You don't have permission to access this resource. Please:
        1. Check your API key permissions
        2. Verify your OpenAI account status
        3. Contact OpenAI support if needed
        """
    
    # Timeout errors
    elif "TimeoutError" in error_type or "timeout" in error_str:
        return """
        ⏱️ **Timeout Error**
        
        The request took too long to complete. Please:
        1. Check your internet connection
        2. Try again with a shorter message
        3. Contact support if the issue persists
        """
    
    # Generic error fallback
    else:
        return f"❌ **Error ({error_type})**: {str(error)}"
