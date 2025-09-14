# 🤖 Educational LLM Chatbot

A clean, modular ChatGPT-like interface built with Streamlit and OpenAI. Perfect for learning LLM integration, chat interfaces, and software architecture patterns.

## 🎯 What You'll Learn

- **Modular Architecture**: Clean separation of concerns
- **Configuration Management**: API keys and settings handling
- **Provider Pattern**: Abstracted LLM service integration
- **Storage Interfaces**: Pluggable chat history implementations
- **Error Handling**: User-friendly error messages
- **Streamlit Integration**: Real-time UI with custom packages

## 🏗️ Architecture

```
+---------------------+    +---------------------+    +---------------------+
|   Streamlit UI      |<-->|     chat_core/      |<-->|     OpenAI API      |
|                     |    |                     |    |                     |
| • Chat Input        |    | • config.py         |    | • GPT-4o-mini       |
| • Messages          |    | • provider.py       |    | • Streaming         |
| • Sidebar           |    | • history.py        |    | • Completions       |
|                     |    | • errors.py         |    |                     |
+---------------------+    +---------------------+    +---------------------+
```

## 📁 Project Structure

```
sandbox-vanilla/
├── app.py             # Main Streamlit app
├── chat_core/         # Core chat package
│   ├── config.py      # Configuration management
│   ├── provider.py    # OpenAI integration
│   ├── history.py     # Chat storage interfaces
│   ├── errors.py      # Error handling
│   └── session.py     # Session management
├── requirements.txt   # Dependencies
├── compose.yaml       # Redis setup
├── Makefile           # Development commands
└── .env.sample        # Environment template
``````

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- OpenAI API key
- Docker (optional, for Redis)

### Setup
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure API key
cp .env.sample .env
# Edit .env with your OpenAI API key

# 3. Run the app
make dev  # Starts Redis + Streamlit
# OR
streamlit run app.py  # Streamlit only
```

Open `http://localhost:8501` in your browser.

## ⚙️ Configuration

### Environment Variables
```bash
OPENAI_API_KEY=your_key_here     # Required
OPENAI_TEMPERATURE=0.7           # AI creativity (0.0-2.0)
REDIS_URL=redis://localhost:6379/0  # Optional, for persistence
HISTORY_MAX_TURNS=20             # Max conversation length
```

### Temperature Control
- **Range**: 0.0 (deterministic) to 2.0 (very creative)
- **Default**: 0.7 (balanced)
- **Usage**: Set via environment variable or .env file
- **Logging**: Temperature logged at startup in dev mode

## 🛠️ Development

### Makefile Commands
| Command | Description |
|---------|-------------|
| `make dev` | Start Redis + Streamlit |
| `make app` | Streamlit only |
| `make redis-up` | Start Redis |
| `make redis-down` | Stop Redis |
| `make lint` | Code linting |
| `make fmt` | Code formatting |

### Key Features
- **Always-on streaming** with stop button
- **Redis persistence** with graceful fallback
- **Export conversations** (Markdown/JSON)
- **Theme-aware UI** (light/dark)
- **Error handling** with user-friendly messages

## 📚 Core Modules

### `chat_core/config.py`
Manages configuration with precedence: env vars > .env > Streamlit secrets > defaults.

```python
from chat_core.config import load_config
config = load_config()
```

### `chat_core/provider.py`
OpenAI integration with streaming support.

```python
from chat_core.provider import OpenAIProvider
provider = OpenAIProvider(config)
# Streaming
for chunk in provider.stream_complete(messages):
    print(chunk, end='')
```

### `chat_core/history.py`
Storage interfaces for chat persistence.

```python
from chat_core.history import StreamlitStore
store = StreamlitStore()
store.add_message("user", "Hello")
messages = store.get_messages()
```

### `chat_core/errors.py`
User-friendly error messages.

```python
from chat_core.errors import humanize_error
try:
    # API call
except Exception as e:
    error_msg = humanize_error(e)
```

## 🔧 Troubleshooting

### Common Issues
- **API Key**: Ensure `OPENAI_API_KEY` is set correctly
- **Redis**: App falls back to in-memory storage if Redis unavailable
- **Header Clipping**: Try hard refresh if title appears cut off
- **Streaming**: Check internet connection and OpenAI status

### Debug Mode
Set `DEBUG_UI=1` to see UI diagnostics in the sidebar.

## 🚀 Future Enhancements

- FastAPI sidecar for REST API
- Multiple LLM provider support
- Advanced conversation features
- User authentication

## 📄 License

MIT License - feel free to use for learning and development.

---

**Happy Learning! 🎉** Start with the basic setup and explore the modular architecture patterns.