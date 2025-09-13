# 🤖 Educational LLM Chatbot

**Stage 1: Modularized Architecture**

A comprehensive learning example demonstrating how to build a ChatGPT-like interface using Streamlit and OpenAI's API with clean modular architecture. This project is designed for educational purposes to help you understand the fundamentals of LLM integration, chat interface development, and software architecture patterns.

## 🎯 Learning Objectives

By working through this project, you will learn:

- **Modular Architecture**: Clean separation of concerns with package structure
- **Configuration Management**: Centralized handling of API keys and settings
- **Provider Pattern**: Abstracted LLM service integration
- **Storage Interfaces**: Pluggable chat history implementations
- **Error Handling**: User-friendly error message mapping
- **Streamlit Integration**: Building apps with custom packages
- **Dependency Injection**: Loose coupling through interfaces

## 🏗️ Stage 1 Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit UI  │    │   chat_core/     │    │   OpenAI API    │
│                 │    │                  │    │                 │
│ • Chat Input    │◄──►│ • config.py      │◄──►│ • GPT-4o-mini   │
│ • Message Display│    │ • provider.py    │    │ • Chat Completions│
│ • Sidebar Info  │    │ • history.py     │    │ • Response Handling│
│                 │    │ • errors.py      │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 📁 Project Structure

```
sandbox-vanilla/
├── app.py                 # Main Streamlit application
├── chat_core/            # Core chat functionality package
│   ├── __init__.py       # Package initialization
│   ├── config.py         # Configuration management
│   ├── provider.py       # LLM provider abstraction
│   ├── history.py        # Chat history storage interfaces
│   └── errors.py         # Error handling and humanization
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

### Installation

1. **Clone or download this project**
   ```bash
   git clone <your-repo-url>
   cd sandbox-vanilla
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your API key** (choose one method):

   **Option A: Environment Variable (Recommended for local development)**
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```

   **Option B: Streamlit Secrets (For deployed apps)**
   Create `.streamlit/secrets.toml`:
   ```toml
   OPENAI_API_KEY = "your-api-key-here"
   ```

4. **Run the application**
   ```bash
   streamlit run app.py
   ```

5. **Open your browser** to `http://localhost:8501`

## 📚 Module Documentation

### **chat_core/config.py** - Configuration Management
```python
from chat_core.config import load_config

# Loads configuration with fallback: Streamlit secrets -> environment variables
config = load_config()
```
- **ChatConfig**: Container for API key, model, and parameters
- **load_config_from_streamlit()**: Load from Streamlit secrets
- **load_config_from_env()**: Load from environment variables
- **load_config()**: Main function with automatic fallback

### **chat_core/provider.py** - LLM Provider Abstraction
```python
from chat_core.provider import OpenAIProvider

provider = OpenAIProvider(config)
response = provider.complete(messages)
```
- **LLMProvider**: Abstract base class for LLM services
- **OpenAIProvider**: OpenAI Chat Completions implementation
- **complete()**: Unified interface for generating responses

### **chat_core/history.py** - Chat History Storage
```python
from chat_core.history import StreamlitStore

chat_store = StreamlitStore()
chat_store.add_message("user", "Hello")
messages = chat_store.get_messages()
```
- **ChatStore**: Abstract interface for message storage
- **StreamlitStore**: Streamlit session state implementation
- **add_message()**, **get_messages()**, **clear()**: Storage operations

### **chat_core/errors.py** - Error Handling
```python
from chat_core.errors import humanize_error

try:
    # API call
except Exception as e:
    error_msg = humanize_error(e)
```
- **humanize_error()**: Converts technical errors to user-friendly messages
- Handles authentication, rate limiting, connection, and other errors

## 🔧 Customization Ideas

### Experiment with Different Models
```python
# Try different OpenAI models
model="gpt-3.5-turbo"  # Faster, cheaper
model="gpt-4"          # More capable, expensive
model="gpt-4o-mini"    # Balanced option (current)
```

### Adjust Response Parameters
```python
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=messages,
    temperature=0.7,    # 0.0 = deterministic, 1.0 = very random
    max_tokens=1000,    # Limit response length
    top_p=0.9,         # Nucleus sampling
)
```

### Add System Prompts
```python
# Add a system message to guide the AI's behavior
system_message = {"role": "system", "content": "You are a helpful coding assistant."}
messages = [system_message] + st.session_state.messages
```

## 🎓 Educational Features

### Built-in Learning Resources
- **Sidebar Information**: Key concepts and next steps
- **Inline Comments**: Detailed explanations throughout the code
- **Error Handling**: Examples of robust API error management
- **Conversation Stats**: Real-time metrics about your chat

### Interactive Elements
- **Clear Conversation**: Reset chat history
- **Message Counter**: Track conversation length
- **Error Display**: Learn from API failures

## 🔍 Understanding the Code

### Message Flow
1. User types message → Added to session state
2. Message displayed immediately → Better UX
3. API call made with full conversation context
4. Response received and added to session state
5. Response displayed to user

### Session State Benefits
- **Persistence**: Data survives app reruns
- **Efficiency**: No need to reload conversation
- **User Experience**: Seamless chat experience

### API Integration Patterns
- **Context Preservation**: Full conversation sent to API
- **Error Handling**: Graceful failure management
- **Response Processing**: Extract content from API response

## 🚨 Common Issues & Solutions

### API Key Not Found
- Ensure your API key is set correctly
- Check environment variable or secrets file
- Verify the key is valid and has credits

### Rate Limiting
- OpenAI has rate limits based on your plan
- Consider adding delays or retry logic
- Monitor your usage in the OpenAI dashboard

### Memory Issues
- Long conversations consume more tokens
- Consider implementing conversation length limits
- Add conversation export/import functionality

## 🚀 Future Stages

### **Stage 2: FastAPI Sidecar**
- REST API endpoints for chat functionality
- WebSocket support for real-time streaming
- API documentation with OpenAPI/Swagger
- Authentication and rate limiting

### **Stage 3: Redis Streaming & Persistence**
- Redis-based message streaming
- Persistent conversation storage
- Real-time collaboration features
- Message queuing and processing

### **Stage 4: Multiple Provider Support**
- Anthropic Claude integration
- Google Gemini support
- Local model support (Ollama)
- Provider switching and load balancing

### **Stage 5: Advanced Features**
- Conversation search and filtering
- User authentication and sessions
- Conversation analytics and insights
- File upload and document processing

## 📖 Additional Resources

- [Streamlit Documentation](https://docs.streamlit.io/)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Streamlit Chat Components](https://docs.streamlit.io/library/api-reference/chat)
- [OpenAI Python Library](https://github.com/openai/openai-python)

## 🤝 Contributing

This is an educational project! Feel free to:
- Add more educational comments
- Implement new features
- Create additional examples
- Improve documentation

## 📄 License

This project is open source and available under the MIT License.

---

**Happy Learning! 🎉** Start with the basic setup and gradually explore the advanced features. Each component is designed to teach you something new about building AI-powered applications.
