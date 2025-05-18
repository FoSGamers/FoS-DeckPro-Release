# chatbot_logic.py

def process_user_message(message: str) -> str:
    # Simple reply logic; replace this with AI/NLP later
    if "hello" in message.lower():
        return "Hi there! How can I help you today?"
    return f"You said: {message}"
