from langgraph.graph import END, StateGraph, START

from .state import State, InputState, OutputState
from .nodes import (
    query_analysis,
    simple_response,
    plan_step,
    execute_step,
    rag_node,
    websearch_node,
    finalize_step,
    replan_step,
    respond,
    route_question,
    route_after_execute,
    route_after_replan,
)


def create_agent_graph():
    """
    Plan → (Execute ↔ Tool) → Replan 반복 구조의 Agentic RAG + Web Search 그래프.

    흐름:
    1. query_analysis: LLM이 질문 의도 분류 (simple/complex) - 그래프의 유일한 진입점
       - 사용자 질문을 messages에 HumanMessage로 추가하고, 이전 턴의 상태를 리셋한다.
       - simple → simple_response → END
       - complex → plan_step
    2. plan_step: 질문을 해결하기 위한 초기 계획을 세운다. 계획의 각 단계는 도구 하나
       (retrieve_AI_brief 또는 web_search_tool)와, 그 도구로 조사할 목표(goal)로 구성된다.
       단계 개수에 고정 상한은 없지만, 보통 1~3단계면 충분하다.
    3. execute_step: 계획의 첫 단계에 지정된 도구 하나만 bind해 추론한다. 한 단계 안에서
       두 도구를 섞어 쓰는 것은 구조적으로 불가능하며, 같은 도구로 여러 번(관련된 하위
       질의) 검색하는 것은 자유롭다 (다만 STEP_MAX_ROUNDS 라운드를 넘기면 안전장치로 강제
       종료된다). 도구 호출이 필요하면 요청된 도구 이름에 따라 rag_node 또는 websearch_node로
       라우팅되고(여러 개면 병렬 Send), 필요 없으면 finalize_step으로 이동한다. 두 노드 모두
       결과를 들고 다시 execute_step으로 돌아와, 도구 호출이 필요 없어질 때까지 반복한다.
    4. finalize_step: 완료된 단계를 plan에서 제거한다. 실행 세부사항(RAG/웹 검색 결과)은
       따로 요약하지 않고 messages에 그대로 남기므로(add_messages 리듀서), 정보가 유실되지 않는다.
    5. replan_step: 지금까지의 실행 결과를 보고 "충분한지"를 매번 새로 판단한다.
       - 충분하면 최종 응답(Response)을 만들고 종료로 이동
       - 부족하면 다음 단계(역시 도구 하나 + goal)를 정리(Plan)하고 execute_step으로 돌아간다
       (라운드 수를 미리 정해두지 않고, 매번 내용을 보고 계속할지 멈출지 스스로 결정한다.)
    6. respond: 최종 응답을 기록하고 종료한다.

    설계 원칙:
    - "계획 = 도구를 어떻게 쓸지에 대한 계획"이다. 각 단계는 도구 하나만 지정하므로,
      실행 노드가 그 도구만 bind해 구조적으로 도구 혼용을 막는다 (프롬프트 지시에만
      의존하지 않는다).
    - 계획 길이·반복 횟수에 고정 숫자를 두지 않는다. 대신 매 단계가 끝날 때마다(finalize_step
      직후) replan_step이 실제 진행 상황을 보고 계속할지 멈출지 판단한다. SAFETY_MAX_MESSAGES와
      STEP_MAX_ROUNDS는 설계상 제약이 아니라, plan이 갱신되지 않는 한 step 내부 루프가
      무한정 반복되는 것을 막는 예외적인 안전장치일 뿐이다.
    """
    graph_builder = StateGraph(State, input_schema=InputState, output_schema=OutputState)

    # 노드 추가
    graph_builder.add_node("query_analysis", query_analysis)
    graph_builder.add_node("simple_response", simple_response)
    graph_builder.add_node("plan_step", plan_step)
    graph_builder.add_node("execute_step", execute_step)
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

    # plan_step → execute_step (첫 단계에 대한 추론 시작)
    graph_builder.add_edge("plan_step", "execute_step")

    # execute_step → route_after_execute (도구 호출 필요 여부에 따라 라우팅)
    graph_builder.add_conditional_edges(
        "execute_step",
        route_after_execute,
        ["rag_node", "websearch_node", "finalize_step"],
    )

    # rag_node/websearch_node → execute_step (도구 실행 결과를 들고 다시 추론)
    graph_builder.add_edge("rag_node", "execute_step")
    graph_builder.add_edge("websearch_node", "execute_step")

    # finalize_step → replan_step (완료된 step을 기록한 뒤 계속할지 판단)
    graph_builder.add_edge("finalize_step", "replan_step")

    # replan_step → route_after_replan (계속 실행 또는 최종 응답)
    graph_builder.add_conditional_edges(
        "replan_step",
        route_after_replan,
        {
            "execute_step": "execute_step",  # 아직 부족함 → 다음 단계 실행 (반복)
            "respond": "respond",            # 충분함 → 최종 응답
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
