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
    intent: Optional[str]  # 'simple' or 'complex' (from query_analysis)

    plan: Optional[list]        # 남은 계획(문자열 단계 목록). 개수에 고정 상한 없음 - 필요한 만큼 존재
    response: Optional[str]     # replan_step이 "충분하다"고 판단하면 설정되는 최종 응답 (설정되면 종료)

    # RAG/웹 검색 tool call과 그 결과(ToolMessage)는 별도 필드로 요약/보관하지 않고
    # 전부 messages(MessagesState 기본 필드, add_messages 리듀서로 누적/병렬 병합)에 그대로 남긴다.
    # -> 도중에 요약하며 정보(URL 등 구체적인 세부사항)가 유실되는 것을 방지한다.
    pending_tool_call: Optional[dict]  # rag_node/websearch_node에 배정된 단일 tool call (Send로 전달됨)

