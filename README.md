# 🤖 Educational LLM Chatbot

A comprehensive learning example demonstrating how to build a ChatGPT-like interface using Streamlit and OpenAI's API. This project is designed for educational purposes to help you understand the fundamentals of LLM integration and chat interface development.

## 🎯 Learning Objectives

By working through this project, you will learn:

- **Streamlit Basics**: How to create interactive web apps with Python
- **Session State Management**: Maintaining conversation history across app interactions
- **OpenAI API Integration**: Connecting to and using large language models
- **Chat UI Patterns**: Building modern conversational interfaces
- **Error Handling**: Graceful handling of API failures and edge cases
- **Environment Configuration**: Secure API key management

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit UI  │    │   Session State  │    │   OpenAI API    │
│                 │    │                  │    │                 │
│ • Chat Input    │◄──►│ • Message History│◄──►│ • GPT-4o-mini   │
│ • Message Display│    │ • Conversation   │    │ • Chat Completions│
│ • Sidebar Info  │    │ • State Persistence│   │ • Response Handling│
└─────────────────┘    └──────────────────┘    └─────────────────┘
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

## 📚 Code Walkthrough

### Key Components

#### 1. **Session State Management**
```python
if "messages" not in st.session_state:
    st.session_state.messages: List[Dict[str, str]] = []
```
- Maintains conversation history across app reruns
- Essential for chat applications to remember context

#### 2. **API Client Configuration**
```python
def get_client() -> OpenAI:
    api_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
    return OpenAI(api_key=api_key)
```
- Handles API key retrieval from multiple sources
- Provides clear error messages for missing keys

#### 3. **Message Processing Loop**
```python
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
```
- Renders conversation history on each app refresh
- Uses Streamlit's chat components for modern UI

#### 4. **API Integration**
```python
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
)
```
- Sends entire conversation context to the API
- Maintains conversation continuity

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

## 🎯 Next Steps

### Beginner Level
- [ ] Try different models and compare responses
- [ ] Experiment with temperature settings
- [ ] Add conversation export functionality

### Intermediate Level
- [ ] Implement conversation persistence (database)
- [ ] Add custom system prompts
- [ ] Create conversation templates
- [ ] Add file upload capabilities

### Advanced Level
- [ ] Implement streaming responses
- [ ] Add conversation search and filtering
- [ ] Create user authentication
- [ ] Add conversation analytics
- [ ] Implement conversation sharing

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
