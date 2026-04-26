from langgraph.graph import MessagesState
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
from typing_extensions import TypedDict
from typing import Optional

load_dotenv()


def _get_llm():
    return init_chat_model("gpt-4o-mini")


class InputState(TypedDict):
    question: str


class OutputState(TypedDict):
    generation: str


class State(MessagesState):
    question: Optional[str]
    generation: Optional[str]
    document: Optional[str]
    intent: Optional[str]  # 'simple' or 'rag' or 'web' (from query_analysis)
    retry_num: int = 0
