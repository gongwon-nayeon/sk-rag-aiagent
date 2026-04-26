from langgraph.graph import END, StateGraph, START
from langgraph.prebuilt import tools_condition

from state import State, InputState, OutputState
from nodes import (
    agent,
    retrieve,
    grade_documents,
    generate,
    transform_query,
    decide_to_generate,
    grade_generation_v_documents_and_question,
)


def create_agent_graph():
    graph_builder = StateGraph(State, input_schema=InputState, output_schema=OutputState)

    # 노드 추가
    graph_builder.add_node("agent", agent)
    graph_builder.add_node("retrieve", retrieve)
    graph_builder.add_node("grade_documents", grade_documents)
    graph_builder.add_node("generate", generate)
    graph_builder.add_node("transform_query", transform_query)

    # 엣지 연결
    graph_builder.add_edge(START, "agent")

    # Agent 조건부 엣지: Tool 호출 또는 일반 응답
    graph_builder.add_conditional_edges(
        "agent",
        tools_condition,
        {
            "tools": "retrieve",
            END: END,
        },
    )

    # Retrieve -> Grade Documents
    graph_builder.add_edge("retrieve", "grade_documents")

    # Grade Documents 조건부 엣지
    graph_builder.add_conditional_edges(
        "grade_documents",
        decide_to_generate,
        {
            "transform_query": "transform_query",
            "generate": "generate",
        },
    )

    # Transform Query -> Retrieve (재검색)
    graph_builder.add_edge("transform_query", "retrieve")

    # Generate 조건부 엣지: 환각 및 유용성 평가
    graph_builder.add_conditional_edges(
        "generate",
        grade_generation_v_documents_and_question,
        {
            "not supported": "generate",  # 환각 발생 -> 재생성
            "useful": END,  # 유용함 -> 종료
            "not useful": "transform_query",  # 유용하지 않음 -> 쿼리 재작성
        },
    )

    # 그래프 컴파일
    graph = graph_builder.compile()

    return graph


def create_graph():
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

    except Exception as e:
        print(f"시각화 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
