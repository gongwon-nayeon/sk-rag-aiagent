from langgraph.graph import END, StateGraph, START

from state import State, InputState, OutputState
from nodes import (
    query_analysis,
    simple_response,
    retrieve,
    web_search,
    grade_documents,
    generate,
    transform_query,
    route_question,
    decide_to_generate,
    route_after_transform_query,
    grade_generation_v_documents_and_question,
)


def create_agent_graph():
    """
    간단한 Query Analysis 기반 RAG + Web Search 에이전트 그래프를 생성합니다.

    흐름:
    1. query_analysis: LLM이 질문 의도 분류 (simple/rag/web)
    2. route_question: 분류 결과에 따라 라우팅
       - simple → simple_response → END
       - rag → retrieve → grade_documents → generate/transform_query/web_search
       - web → web_search → generate
    3. transform_query: 쿼리 재작성 후 원래 문서를 만들어낸 노드(retrieve 또는 web_search)로 루프백 (최대 2회)
       RAG 재작성 후에도 관련 문서를 못 찾으면 web_search로 context 보강 (Corrective RAG)
    4. generate → grade_generation_v_documents_and_question: 환각/유용성 평가
       - not supported → generate (재생성)
       - useful → END (종료)
       - not useful → transform_query (쿼리 재작성 후 source에 따라 retrieve/web_search로 재시도)
    """
    graph_builder = StateGraph(State, input_schema=InputState, output_schema=OutputState)

    # 노드 추가
    graph_builder.add_node("query_analysis", query_analysis)
    graph_builder.add_node("simple_response", simple_response)
    graph_builder.add_node("retrieve", retrieve)
    graph_builder.add_node("web_search", web_search)
    graph_builder.add_node("grade_documents", grade_documents)
    graph_builder.add_node("generate", generate)
    graph_builder.add_node("transform_query", transform_query)

    # 엣지 연결
    # START → query_analysis (질문 의도 분석)
    graph_builder.add_edge(START, "query_analysis")

    # query_analysis → route_question (의도에 따른 라우팅)
    graph_builder.add_conditional_edges(
        "query_analysis",
        route_question,
        {
            "simple_response": "simple_response",  # 간단한 대화 → 직접 답변
            "retrieve": "retrieve",                # RAG 검색
            "web_search": "web_search",            # 웹 검색
        },
    )

    # simple_response → END
    graph_builder.add_edge("simple_response", END)

    # retrieve → grade_documents (문서 관련성 평가)
    graph_builder.add_edge("retrieve", "grade_documents")

    # grade_documents → decide_to_generate (관련성 결과에 따라 분기)
    graph_builder.add_conditional_edges(
        "grade_documents",
        decide_to_generate,
        {
            "transform_query": "transform_query",  # 관련성 낮음, 재시도 여유 있음 → 쿼리 재작성
            "web_search": "web_search",             # 관련성 낮음, 재시도 소진 → 웹 검색으로 context 보강
            "generate": "generate",                # 관련성 높음 → 답변 생성
        },
    )

    # transform_query → source에 따라 retrieve 또는 web_search로 재시도
    graph_builder.add_conditional_edges(
        "transform_query",
        route_after_transform_query,
        {
            "retrieve": "retrieve",       # RAG 문서에서 온 경우 → 다시 RAG 검색
            "web_search": "web_search",   # 웹 검색에서 온 경우 → 다시 웹 검색
        },
    )

    # web_search → generate (웹 검색 결과로 바로 답변 생성)
    graph_builder.add_edge("web_search", "generate")

    # generate → grade_generation_v_documents_and_question (환각 및 유용성 평가)
    graph_builder.add_conditional_edges(
        "generate",
        grade_generation_v_documents_and_question,
        {
            "not supported": "generate",      # 환각 발생 → 재생성
            "useful": END,                    # 유용함 → 종료
            "not useful": "transform_query",  # 유용하지 않음 → 쿼리 재작성
        },
    )

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
