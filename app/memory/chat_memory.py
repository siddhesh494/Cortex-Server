from langchain_core.messages import HumanMessage, AIMessage

chat_history = []

def add_human_message(content: str):
    chat_history.append(HumanMessage(content=content))

def add_ai_message(content: str):
    chat_history.append(AIMessage(content=content))

def get_history():
    return chat_history[-10:]  # keep last 10 exchanges

def clear_history():
    chat_history.clear()