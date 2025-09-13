# Sandbox Vanilla Chatbot

A minimal Streamlit interface that connects to the OpenAI API. It mimics a basic ChatGPT-style chat where conversation history is preserved in the session.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Provide your OpenAI API key via the `OPENAI_API_KEY` environment variable or Streamlit secrets.
3. Start the app:
   ```bash
   streamlit run app.py
   ```

## Notes

- Conversation is stored only in your current browser session.
- This project is intentionally minimal to serve as a starting point for further customization.
