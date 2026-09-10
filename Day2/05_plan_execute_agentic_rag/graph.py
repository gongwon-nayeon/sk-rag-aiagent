from langgraph.graph import END, StateGraph, START

from state import State, InputState, OutputState
from nodes import (
    query_analysis,
    simple_response,
    plan_step,
    agent,
    rag_node,
    websearch_node,
    finalize_step,
    replan_step,
    respond,
    route_question,
    route_after_agent,
    route_after_replan,
)


def create_agent_graph():
    """
    Plan → (Agent ↔ RAG/Websearch) → Replan 반복 구조의 Agentic RAG + Web Search 그래프.

    흐름:
    1. query_analysis: LLM이 질문 의도 분류 (simple/complex) - 그래프의 유일한 진입점
       - 사용자 질문을 messages에 HumanMessage로 추가하고, 이전 턴의 상태를 리셋한다.
       - simple → simple_response → END
       - complex → plan_step
    2. plan_step: 질문을 해결하기 위한 초기 계획(문자열 단계 목록)을 세운다.
       단계 개수에 고정 상한이 없다 - 대상이 1개면 1단계, 14개면 14단계로 스스로 정한다.
    3. agent: 계획의 첫 단계를 어떻게 풀지 추론한다. 도구가 필요 없으면 finalize_step으로,
       필요하면 요청한 도구 이름에 따라 rag_node 또는 websearch_node로 라우팅된다
       (여러 도구를 동시에 요청하면 병렬 Send로 각각 실행). 두 노드 모두 결과를 들고
       다시 agent로 돌아와, 도구 호출이 필요 없어질 때까지 반복한다.
    4. finalize_step: 완료된 단계를 plan에서 제거한다. 실행 세부사항(RAG/웹 검색 결과)은
       따로 요약하지 않고 messages에 그대로 남기므로(add_messages 리듀서), 정보가 유실되지 않는다.
    5. replan_step: 지금까지의 실행 결과를 보고 "충분한지"를 매번 새로 판단한다.
       - 충분하면 최종 응답(Response)을 만들고 종료로 이동
       - 부족하면 남은 계획을 새로 정리(Plan)하고 agent로 돌아간다
       (라운드 수를 미리 정해두지 않고, 매번 내용을 보고 계속할지 멈출지 스스로 결정한다.)
    6. respond: 최종 응답을 기록하고 종료한다.

    자유도를 다루는 방식 (04/이전 버전과의 차이):
    - 04, 이전 05 버전은 "step 개수", "fan-out 개수", "재계획 횟수"에 고정된 숫자 상한을 두어
      자유도를 제한했다. 하지만 실제 상황(예: 신규 모델이 몇 개인지)은 매번 달라서,
      고정 상한은 늘 너무 작거나(정보 누락) 너무 크게(낭비) 어긋나는 문제가 있었다.
    - 이 버전은 계획 길이·반복 횟수에 고정 숫자를 두지 않는다. 대신
      (a) agent는 "이 한 단계"라는 좁은 범위 안에서만 rag/websearch 도구를 자유롭게 쓰고,
      (b) 어떤 도구를 썼는지는 rag_node/websearch_node라는 이름으로 그래프에 명시적으로 드러나며,
      (c) 전체 반복 여부는 매 라운드 replan_step이 실제 진행 상황을 보고 판단하고,
      (d) SAFETY_MAX_MESSAGES는 설계상 제약이 아니라 예외적인
          무한 루프만 막는 안전장치일 뿐이다.
    """
    graph_builder = StateGraph(State, input_schema=InputState, output_schema=OutputState)

    # 노드 추가
    graph_builder.add_node("query_analysis", query_analysis)
    graph_builder.add_node("simple_response", simple_response)
    graph_builder.add_node("plan_step", plan_step)
    graph_builder.add_node("agent", agent)
    graph_builder.add_node("rag_node", rag_node)
    graph_builder.add_node("websearch_node", websearch_node)
    graph_builder.add_node("finalize_step", finalize_step)
    graph_builder.add_node("replan_step", replan_step)
    graph_builder.add_node("respond", respond)

    # 엣지 연결
    # START → query_analysis (질문 의도 분석)
    graph_builder.add_edge(START, "query_analysis")

    # query_analysis → route_question (의도에 따른 라우팅)
    graph_builder.add_conditional_edges(
        "query_analysis",
        route_question,
        {
            "simple_response": "simple_response",  # 간단한 대화 → 직접 답변
            "plan_step": "plan_step",               # 검색/조사 필요 → 계획 수립
        },
    )

    # simple_response → END
    graph_builder.add_edge("simple_response", END)

    # plan_step → agent (첫 단계에 대한 추론 시작)
    graph_builder.add_edge("plan_step", "agent")

    # agent → route_after_agent (도구 호출 필요 여부/종류에 따라 라우팅)
    graph_builder.add_conditional_edges(
        "agent",
        route_after_agent,
        ["rag_node", "websearch_node", "finalize_step"],
    )

    # rag_node/websearch_node → agent (도구 실행 결과를 들고 다시 추론)
    graph_builder.add_edge("rag_node", "agent")
    graph_builder.add_edge("websearch_node", "agent")

    # finalize_step → replan_step (완료된 step을 기록한 뒤 계속할지 판단)
    graph_builder.add_edge("finalize_step", "replan_step")

    # replan_step → route_after_replan (계속 실행 또는 최종 응답)
    graph_builder.add_conditional_edges(
        "replan_step",
        route_after_replan,
        {
            "agent": "agent",        # 아직 부족함 → 다음 단계 실행 (반복)
            "respond": "respond",    # 충분함 → 최종 응답
        },
    )

    # respond → END
    graph_builder.add_edge("respond", END)

    # 그래프 컴파일
    graph = graph_builder.compile()


    return graph


def create_graph():
    """그래프 생성 wrapper 함수"""
    return create_agent_graph()


if __name__ == "__main__":
    # 그래프 생성
    graph = create_graph()

    # 그래프를 mermaid PNG로 그리고 파일로 저장
    try:
        png_data = graph.get_graph().draw_mermaid_png()
        output_file = "graph_visualization.png"

        with open(output_file, "wb") as f:
            f.write(png_data)

        print(f"그래프 시각화 저장 완료: {output_file}")

    except Exception as e:
        print(f"시각화 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
