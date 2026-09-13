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
