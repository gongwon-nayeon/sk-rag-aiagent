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

    plan: Optional[list]        # 남은 계획. 각 원소는 {"tool": "retrieve_AI_brief"|"web_search_tool", "goal": str} 형태

    # replan_step은 "그만해도 되는지"만 판단하고 여기에 결과를 남긴다 - 실제 답변 텍스트는
    # 담지 않는다 (그건 respond 노드가 raw transcript를 보고 직접 작성한다).
    should_respond: Optional[bool]

    # plan은 execute_step<->rag_node/websearch_node 루프 도중에는 갱신되지 않고(현재 step이
    # 끝나야 finalize_step->replan_step에서 갱신됨), 그 루프가 몇 라운드째인지는 아무도 세지
    # 않으면 LLM 판단에만 의존하게 되어 한 step 안에서도 무한정 반복될 수 있다. step_rounds가
    # 그 라운드 수를 세는 카운터로, 새 step이 시작될 때(plan_step/replan_step)마다 0으로
    # 리셋되고, execute_step이 호출될 때마다 1씩 늘어난다.
    step_rounds: Optional[int]

    # RAG/웹 검색 tool call과 그 결과(ToolMessage)는 별도 필드로 요약/보관하지 않고
    # 전부 messages(MessagesState 기본 필드, add_messages 리듀서로 누적/병렬 병합)에 그대로 남긴다.
    # -> 도중에 요약하며 정보(URL 등 구체적인 세부사항)가 유실되는 것을 방지한다.
    pending_tool_call: Optional[dict]  # rag_node/websearch_node에 배정된 단일 tool call (Send로 전달됨)

