from langchain_mcp_adapters.client import MultiServerMCPClient  # type: ignore
from langchain.chat_models import init_chat_model
from langchain.messages import SystemMessage, HumanMessage

from typing_extensions import TypedDict, Annotated
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

from dotenv import load_dotenv
import os

load_dotenv()
os.getenv("OPENAI_API_KEY")

# LLM 초기화
model = init_chat_model(model="gpt-4o")


# 1. State 정의
class AgentState(TypedDict):
    """Agent의 상태를 정의합니다."""
    messages: Annotated[list, add_messages]


async def create_remote_mcp_agent(client: MultiServerMCPClient):
    """원격 MCP 서버의 Tools를 사용하는 LangGraph Agent를 생성합니다."""

    # 원격 MCP Tools 로드
    tools = await client.get_tools()
    tools_by_name = {tool.name: tool for tool in tools}

    # LLM에 Tools 바인딩
    llm_with_tools = model.bind_tools(tools)

    print(f"\n사용 가능한 원격 MCP Tools: {list(tools_by_name.keys())}\n")


    # 2. LLM 노드 정의
    def llm_node(state: AgentState):
        """LLM을 호출하여 응답하거나 Tool 호출을 결정합니다."""

        system_message = SystemMessage(
            content="""당신은 LangChain 공식 문서를 기반으로 질문에 답변하는 AI 어시스턴트입니다.
사용자가 LangChain 관련 질문을 하면 문서 검색 도구를 사용하여 정확한 정보를 제공하세요.
답변에는 반드시 출처 url을 포함하고 한국어로 친절하게 설명하세요."""
        )

        response = llm_with_tools.invoke(
            [system_message] + state["messages"]
        )

        return {
            "messages": [response],
        }


    # 3. 조건부 종료 로직
    def should_continue(state: AgentState):
        """Tool 호출이 필요한지 판단하는 함수"""
        messages = state["messages"]
        last_message = messages[-1]

        # Tool 호출이 있으면 계속 진행
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tool_node"
        # 없으면 종료
        return END


    # 4. Agent 그래프 구성
    agent_builder = StateGraph(AgentState)

    # 노드 추가
    agent_builder.add_node("llm_node", llm_node)
    agent_builder.add_node("tool_node", ToolNode(tools))

    # 엣지 연결
    agent_builder.add_edge(START, "llm_node")
    agent_builder.add_conditional_edges(
        "llm_node",
        should_continue,
        ["tool_node", END]
    )
    agent_builder.add_edge("tool_node", "llm_node")  # Tool 실행 후 다시 LLM으로

    agent = agent_builder.compile()

    return agent


async def run():
    """원격 MCP 서버 기반 LangChain 문서 Agent를 실행합니다."""

    # 원격 MCP 서버 설정
    # LangChain 공식 문서 MCP 서버: https://docs.langchain.com/mcp
    remote_server_config = {
        "langchain-docs": {
            "url": "https://docs.langchain.com/mcp",
            "transport": "http",
        }
    }

    print("=" * 60)
    print("원격 MCP 서버 연결 중...")
    print(f"Server URL: {remote_server_config['langchain-docs']['url']}")
    print("=" * 60)

    try:
        client = MultiServerMCPClient(remote_server_config)

        agent = await create_remote_mcp_agent(client)

        print("\n" + "=" * 60)
        print("LangChain 문서 기반 Agent")
        print("=" * 60)
        print("LangChain 공식 문서를 검색하여 질문에 답변합니다.")
        print("\n예시 질문:")
        print("  - LangGraph의 특징에 대해 알려주세요.")
        print("  - 랭체인의 create_agent 사용법(파이썬) 알려주세요.")
        print("  - 랭체인을 처음 사용하는 사람이 읽으면 좋은 문서는?")
        print("  - langchain-openai 사용법 알려주세요.")
        print("=" * 60)

        # 사용자 입력
        user_input = input("\n질문을 입력하세요: ")

        initial_messages = [HumanMessage(content=user_input)]

        # Agent 실행
        print("\n=====AGENT 실행 중=====\n")
        result = await agent.ainvoke({
            "messages": initial_messages,
        })

        # 결과 출력
        print("\n" + "=" * 60)
        print("실행 결과:")
        print("=" * 60)
        for msg in result["messages"]:
            msg.pretty_print()

        print("=" * 60)

    except Exception as e:
        print(f"\n오류 발생: {e}")


import asyncio

if __name__ == "__main__":
    asyncio.run(run())
