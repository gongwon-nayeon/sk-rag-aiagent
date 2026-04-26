from langgraph.graph import END, StateGraph, START
from langgraph.prebuilt import ToolNode, tools_condition

from state import State, InputState, OutputState
from nodes import chatbot, grade_documents, rewrite, generate
from retriever import setup_retriever

# 모듈 레벨에서 한 번만 초기화
_, retriever_tool = setup_retriever()


def create_agent_graph():
    tools = [retriever_tool]

    # StateGraph 초기화 (입력/출력 스키마 지정)
    graph_builder = StateGraph(State, input_schema=InputState, output_schema=OutputState)

    # 노드 추가
    graph_builder.add_node("chatbot", chatbot)
    tool_node = ToolNode(tools=tools)
    graph_builder.add_node("retriever", tool_node)
    graph_builder.add_node("rewrite", rewrite)
    graph_builder.add_node("generate", generate)

    # 엣지 연결
    graph_builder.add_edge(START, "chatbot")

    # Chatbot -> Retriever or END
    graph_builder.add_conditional_edges(
        "chatbot",
        tools_condition,
        {
            "tools": "retriever",
            END: END
        }
    )

    # Retriever -> Grade Documents (조건부)
    graph_builder.add_conditional_edges(
        "retriever",
        grade_documents,
    )

    # Generate -> END
    graph_builder.add_edge("generate", END)

    # Rewrite -> Chatbot (재시도)
    graph_builder.add_edge("rewrite", "chatbot")

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
