from langgraph.graph import MessagesState
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
from typing_extensions import TypedDict
from typing import Optional

load_dotenv()


def _get_llm():
    return init_chat_model("gpt-5.4-mini")


class InputState(TypedDict):
    question: str


class OutputState(TypedDict):
    generation: str


class State(MessagesState):
    question: Optional[str]
    generation: Optional[str]
    document: Optional[str]
    intent: Optional[str]  # 'simple' or 'rag' or 'web' (from query_analysis)
    source: Optional[str]  # 'rag' or 'web' - document를 만들어낸 노드 (재시도 라우팅용)
    retry_num: Optional[int]  # RAG/웹 검색 재시도(쿼리 재작성) 횟수
    hallucination_retry: Optional[int]  # 환각으로 인한 답변 재생성 횟수
