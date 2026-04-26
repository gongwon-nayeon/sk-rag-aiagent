from langgraph.graph import END, StateGraph, START
from langgraph.prebuilt import ToolNode, tools_condition

from state import State, InputState, OutputState
from nodes import answer, chatbot
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
    graph_builder.add_node("answer", answer)

    graph_builder.add_edge(START, "chatbot")

    graph_builder.add_conditional_edges(
        "chatbot",
        tools_condition,
        {
            "tools": "retriever",
            END: END
        }
    )

    graph_builder.add_edge("retriever", "answer")
    graph_builder.add_edge("answer", END)

    graph = graph_builder.compile()

    return graph


def create_graph():
    return create_agent_graph()