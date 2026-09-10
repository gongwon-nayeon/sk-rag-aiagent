from typing import Literal, Union
from datetime import date
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.types import Send
from pydantic import BaseModel, Field

from .state import State, _get_llm
from .prompts import (
    QUERY_ANALYSIS_PROMPT,
    PLANNER_PROMPT,
    REPLANNER_PROMPT,
    EXECUTE_STEP_SYSTEM_PROMPT,
    SIMPLE_RESPONSE_SYSTEM_PROMPT,
)
from .retriever import setup_retriever

# 모듈 레벨에서 한 번만 초기화
retriever, retriever_tool = setup_retriever()

from dotenv import load_dotenv

load_dotenv()

# 아래 값은 "설계상의 제약"이 아니라, 실수로 인한 무한 루프만 막기 위한 안전장치(safety net)다.
# 정상적인 흐름에서는 replan_step이 내용을 보고 스스로 멈추므로 거의 도달하지 않는다.
# 별도의 카운터 필드 없이, 누적된 messages 개수 하나로 step 반복과 tool-calling 루프를 동시에 제한한다.
SAFETY_MAX_MESSAGES = 40


def _web_search(query: str) -> str:
    """Tavily로 웹 검색을 수행하고 결과를 문자열로 포맷팅합니다."""
    from langchain_tavily import TavilySearch  # type: ignore

    search_tool = TavilySearch(max_results=3, topic="general")
    results = search_tool.invoke(query)

    context = ""
    if isinstance(results, list):
        for idx, result in enumerate(results):
            if isinstance(result, dict):
                context += f"\n[웹 검색 결과 {idx + 1}]\n"
                context += f"제목: {result.get('title', 'N/A')}\n"
                context += f"내용: {result.get('content', 'N/A')}\n"
                context += f"출처: {result.get('url', 'N/A')}\n"
            else:
                context += f"\n[웹 검색 결과 {idx + 1}]: {result}\n"
    else:
        context = str(results)

    return context


@tool
def web_search_tool(query: str) -> str:
    """웹에서 최신 정보나 각 항목의 공식 문서를 검색합니다."""
    return _web_search(query)


# ===============================
# Pydantic Models
# ===============================

class RouteQuery(BaseModel):
    """질문 의도 분류"""
    intent: str = Field(
        description="질문의 의도: 'simple' (간단한 대화) 또는 'complex' (검색/조사가 필요한 질문)"
    )


class Plan(BaseModel):
    """앞으로 실행할 계획 (단계 개수에 고정 상한 없음 - 필요한 만큼)"""
    steps: list[str] = Field(description="수행할 단계들의 순서 있는 목록. 각 단계는 하나의 구체적인 하위 작업")


class Response(BaseModel):
    """사용자에게 그대로 보여줄 최종 응답"""
    response: str = Field(
        description=(
            "사용자에게 그대로 보여줄 최종 답변 본문만 작성. "
            "'왜 최종 응답으로 진행하는지', '판단 근거' 같은 내부 사고 과정은 절대 포함하지 않고, "
            "질문에 대한 완결된 답변만 작성한다."
        )
    )


class Act(BaseModel):
    """재계획자의 행동: 계획을 계속 진행(Plan)할지 최종 응답(Response)할지 결정"""
    reasoning: str = Field(
        description="이 행동을 선택한 이유에 대한 간단한 내부 판단 근거 (로그용이며 사용자에게는 노출되지 않음)"
    )
    action: Union[Plan, Response] = Field(
        description="다음 행동. 이미 충분한 정보가 모였으면 Response, 아직 더 필요하면 Plan"
    )


# ===============================
# Helpers
# ===============================

def _format_transcript(messages: list) -> str:
    """messages(System 제외)를 replan_step이 읽기 쉫은 텍스트로 변환합니다.
    요약/압축 없이 실제 tool 결과(URL 등 세부사항 포함)를 그대로 보존한다."""
    lines = []
    for m in messages:
        if isinstance(m, SystemMessage):
            continue
        if isinstance(m, ToolMessage):
            lines.append(f"[도구 결과]\n{m.content}")
        elif isinstance(m, AIMessage):
            if m.tool_calls:
                calls = ", ".join(f"{c['name']}({c['args']})" for c in m.tool_calls)
                lines.append(f"[AI가 도구 호출] {calls}")
            elif m.content:
                lines.append(f"[AI] {m.content}")
        elif isinstance(m, HumanMessage):
            lines.append(f"[질문/작업] {m.content}")
    return "\n".join(lines) if lines else "(아직 진행된 내용 없음)"


def _today() -> str:
    """프롬프트에 넣을 오늘 날짜(년-월-일)를 반환합니다."""
    return date.today().isoformat()


# ===============================
# Nodes
# ===============================

def query_analysis(state: State):
    """
    질문의 의도를 분석합니다.
    simple: 간단한 대화 → 직접 답변
    complex: 검색/조사가 필요 → plan_step 수립

    그래프의 유일한 진입점이므로, 여기서 매 턴마다:
    1) 사용자 질문을 messages에 HumanMessage로 추가하고 (멀티턴 대화 이력 유지)
    2) 이전 턴에서 남은 스크래치 상태를 리셋한다.
    """
    print("##### QUERY ANALYSIS #####")

    question = state["question"]
    print(f"Analyzing question: {question}")

    llm = _get_llm()
    router = llm.with_structured_output(RouteQuery)
    chain = QUERY_ANALYSIS_PROMPT | router

    result = chain.invoke({"question": question, "current_date": _today()})
    intent = result.intent

    print(f"Intent: {intent}")

    return {
        "question": question,
        "intent": intent,
        "messages": [HumanMessage(content=question)],
        # 새 턴 시작이므로 이전 턴의 계획/응답 상태만 초기화 (messages는 대화 이력이므로 유지)
        "plan": [],
        "response": None,
    }


def simple_response(state: State):
    """
    간단한 대화에 대해 직접 답변합니다.
    이전 대화 이력(messages)을 함께 전달하여 멀티턴 맥락을 반영합니다.
    """
    print("##### SIMPLE RESPONSE #####")

    llm = _get_llm()
    system_msg = SystemMessage(SIMPLE_RESPONSE_SYSTEM_PROMPT.format(current_date=_today()))
    history = state["messages"]

    response = llm.invoke([system_msg] + history)

    print(f"Response: {response.content}")

    return {"generation": response.content, "messages": [response]}


def plan_step(state: State):
    """
    질문을 해결하기 위한 초기 계획을 세웁니다. 단계 개수에는 고정된 상한이 없고,
    질문 내용에 따라 LLM이 필요한 만큼 자유롭게 정합니다 (예: 대상이 1개면 1단계,
    대상이 14개면 14단계). 대신 이후 replan_step이 진행 상황을 보고 계속할지
    멈출지를 매번 판단하므로, 부풀려진 계획도 불필요하면 일찍 종료된다.
    """
    print("##### PLAN #####")

    question = state["question"]

    llm = _get_llm()
    planner = llm.with_structured_output(Plan)
    chain = PLANNER_PROMPT | planner
    result = chain.invoke({"question": question, "current_date": _today()})

    steps = result.steps or [question]
    print(f"Plan ({len(steps)} step(s)): {steps}")

    return {"plan": steps}


def agent(state: State):
    """
    현재 step을 해결하기 위해 다음 행동을 결정하는 추론 노드입니다.
    도구 호출이 필요하면 tool_calls를 반환하고(→ route_after_agent가 rag_node/websearch_node로
    라우팅), 필요 없으면 이 step이 끝난 것으로 보고 finalize_step으로 이동합니다.

    현재 작업(task)은 영구 대화 기록(messages)에는 남기지 않고, 매번 이 호출에만 임시로
    덧여서 상기시킨다 (대화 기록이 작업 지시로 도배되지 않도록). 도구 호출과 그 결과(ToolMessage)는
    그대로 messages에 영구 저장되므로, 이후 replan_step/최종 응답에서 요약 없이 원본(URL 등)을
    그대로 참고할 수 있다.
    """
    print("##### AGENT #####")

    plan = state["plan"]
    task = plan[0]
    print(f"Task: {task}")

    llm = _get_llm()
    llm_with_tools = llm.bind_tools([retriever_tool, web_search_tool])

    # 이 step만 단독으로 주지 않고 전체 계획 속 위치를 함께 보여줘, 에이전트가 맥락을 잡기 쉽게 한다
    plan_str = "\n".join(f"{i + 1}. {step}" for i, step in enumerate(plan))
    reminder = HumanMessage(
        f"전체 계획:\n{plan_str}\n\n"
        f"당신은 지금 1번째 단계, 즉 다음 작업을 수행해야 합니다: {task}\n"
        f"필요하면 도구를 사용해 이 작업을 완수하세요."
    )
    response = llm_with_tools.invoke(
        [SystemMessage(EXECUTE_STEP_SYSTEM_PROMPT.format(current_date=_today()))] + state["messages"] + [reminder]
    )

    # reminder는 임시용이므로 저장하지 않고, AI의 응답만 대화 기록에 영구 반영한다
    return {"messages": [response]}


def rag_node(state: State):
    """agent가 요청한 RAG 검색 tool call 하나를 실행합니다."""
    print("##### RAG NODE #####")

    call = state["pending_tool_call"]
    print(f"RAG Query: {call['args']}")
    result = retriever_tool.invoke(call["args"])

    return {"messages": [ToolMessage(content=str(result), tool_call_id=call["id"])]}


def websearch_node(state: State):
    """agent가 요청한 웹 검색 tool call 하나를 실행합니다."""
    print("##### WEBSEARCH NODE #####")

    call = state["pending_tool_call"]
    print(f"Web Query: {call['args']}")
    result = web_search_tool.invoke(call["args"])

    return {"messages": [ToolMessage(content=str(result), tool_call_id=call["id"])]}


def finalize_step(state: State):
    """
    agent가 더 이상 도구가 필요 없다고 판단하면, 현재 step을 마무리합니다.
    결과를 따로 요약/보관하지 않고 plan에서만 제거한다 - 실제 세부사항은 이미 messages에
    그대로 남아있으므로 유실될 정보가 없다.
    """
    print("##### FINALIZE STEP #####")

    plan = state["plan"]
    print(f"Step complete: {plan[0]}")

    return {"plan": plan[1:]}


def replan_step(state: State):
    """
    지금까지의 대화 기록(messages)을 보고, 계획을 계속 진행할지 최종 응답할지 결정합니다.
    고정된 라운드 수가 아니라 매번 내용을 보고 판단하므로, 필요한 만큼만 반복되고
    충분해지면 즉시 종료된다 (SAFETY_MAX_MESSAGES는 예외적인 무한 루프만 막는 안전장치).
    """
    print("##### REPLAN #####")

    question = state["question"]
    plan = state.get("plan", [])
    messages = state.get("messages", [])

    if len(messages) >= SAFETY_MAX_MESSAGES:
        print(f"---SAFETY: {SAFETY_MAX_MESSAGES} MESSAGES REACHED, FORCE RESPONSE---")
        llm = _get_llm()
        forced = llm.invoke([
            SystemMessage(
                f"오늘 날짜: {_today()}\n\n"
                "지금까지 수집된 정보만으로 질문에 답하세요. 부족한 부분은 정직하게 밝히세요.\n"
                "출처를 사용한 문장/수치 옆에는 [1], [2]처럼 번호를 매긴 인용 표시를 붙이고,\n"
                "답변 맨 마지막에 '## 출처' 섹션을 만들어 RAG 문서는 `[n] 파일명, p.페이지번호`,\n"
                "웹 출처는 `[n] URL` 형식으로 나열하세요."
            ),
            HumanMessage(f"<question>{question}</question>\n<transcript>{_format_transcript(messages)}</transcript>"),
        ])
        return {"response": forced.content, "plan": []}

    llm = _get_llm()
    replanner = llm.with_structured_output(Act)
    chain = REPLANNER_PROMPT | replanner

    output = chain.invoke({
        "question": question,
        "plan": "\n".join(plan) if plan else "(없음)",
        "transcript": _format_transcript(messages),
        "current_date": _today(),
    })

    print(f"Reasoning: {output.reasoning}")

    if isinstance(output.action, Response):
        print("---DECISION: RESPOND---")
        return {"response": output.action.response, "plan": []}

    print(f"---DECISION: CONTINUE ({len(output.action.steps)} step(s) remaining)---")
    return {"plan": output.action.steps}


def respond(state: State):
    """최종 응답을 generation/messages에 기록합니다."""
    print("##### RESPOND #####")

    response_text = state["response"]
    return {
        "generation": response_text,
        "messages": [AIMessage(content=response_text)],
    }


# ===============================
# 엣지 조건 함수
# ===============================

def route_question(state: State) -> Literal["simple_response", "plan_step"]:
    """query_analysis 결과에 따라 라우팅합니다."""
    print("##### ROUTE QUESTION #####")

    if state.get("intent") == "simple":
        print("---ROUTE DECISION: SIMPLE CONVERSATION---")
        return "simple_response"

    print("---ROUTE DECISION: PLAN---")
    return "plan_step"


def route_after_replan(state: State) -> Literal["agent", "respond"]:
    """replan_step 결과에 따라, 다음 단계를 마저 실행할지 최종 응답할지 라우팅합니다."""
    print("##### ROUTE AFTER REPLAN #####")

    if state.get("response"):
        print("---ROUTE DECISION: RESPOND---")
        return "respond"

    print("---ROUTE DECISION: EXECUTE NEXT STEP---")
    return "agent"


def route_after_agent(state: State):
    """
    agent 직후 호출되어, 도구 호출이 필요하면 도구 이름에 따라 rag_node/websearch_node로
    (여러 개면 Send로 병렬) 라우팅하고, 더 이상 도구가 필요 없으면 finalize_step으로 이동합니다.
    누적 messages 개수가 SAFETY_MAX_MESSAGES를 넘으면(안전장치) 강제로 마무리한다.
    """
    print("##### ROUTE AFTER AGENT #####")

    messages = state.get("messages") or []
    last = messages[-1]
    tool_calls = getattr(last, "tool_calls", None) or []

    if tool_calls and len(messages) >= SAFETY_MAX_MESSAGES:
        print(f"---SAFETY: {SAFETY_MAX_MESSAGES} MESSAGES REACHED, FINALIZE STEP---")
        return "finalize_step"

    if not tool_calls:
        print("---ROUTE DECISION: STEP COMPLETE---")
        return "finalize_step"

    sends = []
    for call in tool_calls:
        target = "rag_node" if call["name"] == retriever_tool.name else "websearch_node"
        sends.append(Send(target, {"pending_tool_call": call}))

    print(f"---ROUTE DECISION: {len(sends)} TOOL CALL(S) -> {[s.node for s in sends]}---")
    return sends


