from typing import Literal
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
    RESPOND_SYSTEM_PROMPT,
    SIMPLE_RESPONSE_SYSTEM_PROMPT,
)
from .retriever import setup_retriever

# 모듈 레벨에서 한 번만 초기화
retriever, retriever_tool = setup_retriever()

from dotenv import load_dotenv

load_dotenv()

SAFETY_MAX_MESSAGES = 60

STEP_MAX_ROUNDS = 3


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
    """웹에서 최신 정보나 각 항목의 공식 문서를 검색합니다.
    query 인자는 검색창에 바로 입력할 간결한 키워드/구문으로 작성하세요
    (예: 'OpenAI GPT-5.6 공식 발표'). 검색 방법이나 의도를 설명하는 문장,
    또는 실제 웹 검색어로 쓰기 애매한 파일명/문서 제목만 넣지 마세요."""
    return _web_search(query)


# ===============================
# Pydantic Models
# ===============================

class RouteQuery(BaseModel):
    """질문 의도 분류"""
    intent: str = Field(
        description="질문의 의도: 'simple' (간단한 대화) 또는 'complex' (검색/조사가 필요한 질문)"
    )


class PlanStep(BaseModel):
    """계획의 한 단계: 도구 하나만 지정하고, 그 도구로 조사할 목표를 적는다.
    실행 시점에는 이 도구 하나만 bind되므로, 다른 도구는 호출 자체가 불가능하다."""
    tool: Literal["retrieve_AI_brief", "web_search_tool"] = Field(
        description="이 단계에서 사용할 도구 (사내 문서 검색이면 retrieve_AI_brief, 웹 검색이면 web_search_tool)"
    )
    goal: str = Field(
        description="이 단계에서 이 도구로 조사할 목표. 필요하면 이 도구로 여러 번 검색할 수 있지만, 같은 도구로 수행 가능한 하나의 일관된 범위여야 한다"
    )


class Plan(BaseModel):
    """앞으로 실행할 계획 (단계 개수에 고정 상한 없음 - 필요한 만큼)"""
    steps: list[PlanStep] = Field(description="수행할 단계들의 순서 있는 목록. 각 단계는 도구 하나만 사용하는 하위 작업")


class Act(BaseModel):
    """재계획자의 결정: 조사를 계속할지(next_steps) 이대로 끝낼지(is_done)만 판단한다.
    최종 답변 본문은 여기 담지 않는다 - 그건 respond 노드가 raw transcript를 보고 직접 작성한다."""
    reasoning: str = Field(
        description="이 결정을 내린 이유에 대한 간단한 내부 판단 근거 (로그용이며 사용자에게는 노출되지 않음)"
    )
    is_done: bool = Field(
        description="정보가 충분해 조사를 끝내고 최종 응답으로 넘어가도 되면 true, 아직 더 조사가 필요하면 false"
    )
    next_steps: list[PlanStep] = Field(
        default_factory=list,
        description="is_done이 false일 때 다음에 실행할 단계들. is_done이 true면 빈 리스트로 둔다",
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


def _format_plan(plan: list) -> str:
    """plan(딕셔너리 리스트)을 재계획 프롬프트에 넣기 좋은 텍스트로 변환합니다."""
    if not plan:
        return "(없음)"
    return "\n".join(f"{i + 1}. [{s['tool']}] {s['goal']}" for i, s in enumerate(plan))


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
        "should_respond": False,
        "step_rounds": 0,
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
    질문을 해결하기 위한 초기 계획을 세웁니다. 각 단계는 도구 하나(tool) + 그 도구로
    조사할 목표(goal)로 구성되며, 단계 개수에는 고정된 상한이 없습니다. 이후 replan_step이
    진행 상황을 보고 계속할지 멈출지를 매번 판단하므로, 부풀려진 계획도 불필요하면
    일찍 종료된다.
    """
    print("##### PLAN #####")

    question = state["question"]

    llm = _get_llm()
    planner = llm.with_structured_output(Plan)
    chain = PLANNER_PROMPT | planner
    result = chain.invoke({"question": question, "current_date": _today()})

    steps = [s.model_dump() for s in result.steps] or [
        {"tool": "web_search_tool", "goal": question}
    ]
    print(f"Plan ({len(steps)} step(s)):")
    for i, s in enumerate(steps):
        print(f"  {i + 1}. [{s['tool']}] {s['goal']}")

    return {"plan": steps, "step_rounds": 0}


def execute_step(state: State):
    """
    계획의 첫 단계를 실행하는 추론 노드입니다. 이 단계에 지정된 도구 하나만 bind하므로,
    LLM은 구조적으로 그 도구만 호출할 수 있습니다 (한 단계 안에서 두 도구를 섞어 쓰는
    것이 원천적으로 불가능하다). 도구 호출이 필요하면 tool_calls를 반환하고
    (→ route_after_execute가 rag_node/websearch_node로 라우팅), 필요 없으면 이 단계가
    끝난 것으로 보고 finalize_step으로 이동합니다.

    목표(goal)는 영구 대화 기록(messages)에는 남기지 않고, 매번 이 호출에만 임시로 덧붙여
    상기시킨다. 도구 호출과 그 결과(ToolMessage)는 그대로 messages에 영구 저장되므로,
    이후 replan_step/최종 응답에서 요약 없이 원본(URL 등)을 그대로 참고할 수 있다.

    STEP_MAX_ROUNDS/SAFETY_MAX_MESSAGES 상한에 도달하면 도구를 아예 bind하지 않고 텍스트
    응답만 받는다 - 상한 도달 "후"에 나온 tool_calls를 실행하지 않고 버리면, 그 tool_call이
    ToolMessage 짝 없이 messages에 남아 이후 어떤 raw-message LLM 호출(OpenAI 등)에서도
    "tool_calls 뒤에 ToolMessage가 없다"는 오류로 실패한다. 그래서 상한 도달 여부를 도구를
    호출하기 "전"에 먼저 확인해,애초에 tool_calls가 생성되지 않도록 한다.
    """
    print("##### EXECUTE STEP #####")

    plan = state["plan"]
    step = plan[0]
    tool_name = step["tool"]
    goal = step["goal"]
    round_no = state.get("step_rounds", 0) + 1
    messages = state["messages"]

    tool_obj = retriever_tool if tool_name == "retrieve_AI_brief" else web_search_tool
    llm = _get_llm()
    system_msg = SystemMessage(EXECUTE_STEP_SYSTEM_PROMPT.format(current_date=_today(), tool_name=tool_name))

    if round_no > STEP_MAX_ROUNDS or len(messages) >= SAFETY_MAX_MESSAGES:
        print(f"Step (round {round_no}, LIMIT REACHED - NO MORE TOOL CALLS): [{tool_name}] {goal}")
        stop_reminder = HumanMessage(
            f"당신이 지금 수행 중이던 목표: {goal}\n"
            f"이 단계에서 도구를 이미 충분히 호출했습니다. 더 이상 도구를 호출하지 말고, "
            f"지금까지 얻은 결과만으로 이 목표에 대한 답을 간결한 텍스트로 정리하세요."
        )
        response = llm.invoke([system_msg] + messages + [stop_reminder])
        return {"messages": [response], "step_rounds": round_no}

    print(f"Step (round {round_no}/{STEP_MAX_ROUNDS}): [{tool_name}] {goal}")
    llm_with_tool = llm.bind_tools([tool_obj])

    reminder = HumanMessage(
        f"당신이 지금 수행해야 할 목표: {goal}\n"
        f"필요하면 {tool_name}을 (여러 번이라도) 사용해 이 목표를 조사하세요."
    )
    response = llm_with_tool.invoke([system_msg] + messages + [reminder])

    # reminder는 임시용이므로 저장하지 않고, AI의 응답만 대화 기록에 영구 반영한다
    return {"messages": [response], "step_rounds": round_no}


def rag_node(state: State):
    """execute_step이 요청한 RAG 검색 tool call 하나를 실행합니다."""
    print("##### RAG NODE #####")

    call = state["pending_tool_call"]
    print(f"RAG Query: {call['args']}")
    result = retriever_tool.invoke(call["args"])

    return {"messages": [ToolMessage(content=str(result), tool_call_id=call["id"])]}


def websearch_node(state: State):
    """execute_step이 요청한 웹 검색 tool call 하나를 실행합니다."""
    print("##### WEBSEARCH NODE #####")

    call = state["pending_tool_call"]
    print(f"Web Query: {call['args']}")
    result = web_search_tool.invoke(call["args"])

    return {"messages": [ToolMessage(content=str(result), tool_call_id=call["id"])]}


def finalize_step(state: State):
    """
    execute_step이 더 이상 도구가 필요 없다고 판단하면, 현재 단계를 마무리합니다.
    결과를 따로 요약/보관하지 않고 plan에서만 제거한다 - 실제 세부사항은 이미 messages에
    그대로 남아있으므로 유실될 정보가 없다.
    """
    print("##### FINALIZE STEP #####")

    plan = state["plan"]
    step = plan[0]
    print(f"Step complete: [{step['tool']}] {step['goal']}")

    return {"plan": plan[1:], "step_rounds": 0}


def replan_step(state: State):
    """
    지금까지의 대화 기록(messages)을 보고, 조사를 계속할지 이대로 끝낼지만 결정합니다.
    고정된 라운드 수가 아니라 매번 내용을 보고 판단하므로, 필요한 만큼만 반복되고
    충분해지면 즉시 종료된다 (SAFETY_MAX_MESSAGES는 예외적인 무한 루프만 막는 안전장치).
    최종 답변 텍스트는 여기서 쓰지 않는다 - "그만해도 되는지" 판단과 "무엇을 어떻게 답할지"는
    서로 다른 책임이므로, 실제 답변 작성은 raw transcript를 직접 보는 respond 노드가 맡는다.
    """
    print("##### REPLAN #####")

    question = state["question"]
    plan = state.get("plan", [])
    messages = state.get("messages", [])

    if len(messages) >= SAFETY_MAX_MESSAGES:
        print(f"---SAFETY: {SAFETY_MAX_MESSAGES} MESSAGES REACHED, FORCE RESPOND---")
        return {"should_respond": True, "plan": []}

    llm = _get_llm()
    replanner = llm.with_structured_output(Act)
    chain = REPLANNER_PROMPT | replanner

    output = chain.invoke({
        "question": question,
        "plan": _format_plan(plan),
        "transcript": _format_transcript(messages),
        "current_date": _today(),
    })

    print(f"Reasoning: {output.reasoning}")

    if output.is_done:
        print("---DECISION: RESPOND---")
        return {"should_respond": True, "plan": []}

    steps = [s.model_dump() for s in output.next_steps]
    print(f"---DECISION: CONTINUE ({len(steps)} step(s) remaining)---")
    for i, s in enumerate(steps):
        print(f"  {i + 1}. [{s['tool']}] {s['goal']}")
    return {"plan": steps, "step_rounds": 0, "should_respond": False}


def respond(state: State):
    """
    replan_step이 "이제 그만해도 된다"고 판단한 뒤에만 호출됩니다. 요약/가공 없이
    지금까지의 전체 원본 대화 기록(messages, RAG/웹 검색 결과 전부 포함)을 그대로 보고
    사용자에게 보여줄 최종 답변을 직접 작성합니다.
    """
    print("##### RESPOND #####")

    question = state["question"]
    messages = state["messages"]

    llm = _get_llm()
    response = llm.invoke([
        SystemMessage(RESPOND_SYSTEM_PROMPT.format(current_date=_today())),
        HumanMessage(f"<question>{question}</question>\n<transcript>{_format_transcript(messages)}</transcript>"),
    ])

    print(f"Response: {response.content}")

    return {
        "generation": response.content,
        "messages": [AIMessage(content=response.content)],
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


def route_after_replan(state: State) -> Literal["execute_step", "respond"]:
    """replan_step 결과에 따라, 다음 단계를 마저 실행할지 최종 응답할지 라우팅합니다."""
    print("##### ROUTE AFTER REPLAN #####")

    if state.get("should_respond"):
        print("---ROUTE DECISION: RESPOND---")
        return "respond"

    print("---ROUTE DECISION: EXECUTE NEXT STEP---")
    return "execute_step"


def route_after_execute(state: State):
    """
    execute_step 직후 호출되어, 도구 호출이 필요하면 도구 이름에 따라 rag_node/websearch_node로
    (여러 개면 Send로 병렬) 라우팅하고, 더 이상 도구가 필요 없으면 finalize_step으로 이동합니다.
    STEP_MAX_ROUNDS/SAFETY_MAX_MESSAGES 상한 처리는 execute_step이 도구를 bind하기 전에
    이미 끝냈으므로(상한 도달 시 tool_calls 자체가 생성되지 않음), 여기서는 tool_calls 유무만
    보면 된다 - 여기서 tool_calls를 보고도 실행하지 않고 finalize해버리면, 그 tool_call이
    ToolMessage 짝 없이 messages에 남아 이후 LLM 호출이 전부 실패한다.
    """
    print("##### ROUTE AFTER EXECUTE #####")

    messages = state.get("messages") or []
    last = messages[-1]
    tool_calls = getattr(last, "tool_calls", None) or []

    if not tool_calls:
        print("---ROUTE DECISION: STEP COMPLETE---")
        return "finalize_step"

    sends = []
    for call in tool_calls:
        target = "rag_node" if call["name"] == retriever_tool.name else "websearch_node"
        sends.append(Send(target, {"pending_tool_call": call}))

    print(f"---ROUTE DECISION: {len(sends)} TOOL CALL(S) -> {[s.node for s in sends]}---")
    return sends


