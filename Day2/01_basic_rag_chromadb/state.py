from langgraph.graph import MessagesState
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
from typing_extensions import TypedDict
from typing import Optional

load_dotenv()

def _get_llm():
    return init_chat_model("gpt-4o-mini")

class InputState(TypedDict):
    query: str

class OutputState(TypedDict):
    answer: str

class State(MessagesState):
    query: Optional[str]
    context: Optional[str]
    answer: Optional[str]
