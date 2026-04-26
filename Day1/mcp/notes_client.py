import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, SystemMessage
from mcp import StdioServerParameters, ClientSession
from mcp.client.stdio import stdio_client  # type: ignore
from langchain_mcp_adapters.tools import load_mcp_tools  # type: ignore
import sys

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

class AgentState(MessagesState):
    """에이전트의 상태 정의"""
    llm_calls: int = 0


def should_continue(state: AgentState):
    """Tool 호출이 필요한지 판단하는 함수"""
    messages = state["messages"]
    last_message = messages[-1]

    # Tool 호출이 있으면 계속 진행
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    # 없으면 종료
    return END


async def main():
    """MCP 서버와 연결하여 노트 관리 에이전트 실행"""

    # MCP 서버 설정
    server_params = StdioServerParameters(
        command="python",
        args=["notes_server.py"],  # 노트 관리 서버
        env=None,
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # MCP 서버 초기화
            await session.initialize()

            # MCP Tools를 LangChain Tools로 변환
            tools = await load_mcp_tools(session)

            print(f"\n✅ {len(tools)}개의 Tool이 로드되었습니다:")
            for tool in tools:
                print(f"  - {tool.name}")
            print()

            # LLM 설정 (Tool 사용 설정)
            llm = init_chat_model(model="gpt-4o", temperature=0)
            llm_with_tools = llm.bind_tools(tools)

            # LLM 노드 정의
            def llm_node(state: AgentState):
                """LLM을 호출하여 Tool 사용 여부 결정"""
                response = llm_with_tools.invoke(state["messages"])
                return {
                    "messages": [response],
                    "llm_calls": state["llm_calls"] + 1
                }

            # StateGraph 생성
            graph_builder = StateGraph(AgentState)

            # 노드 추가
            graph_builder.add_node("llm", llm_node)
            graph_builder.add_node("tools", ToolNode(tools=tools))

            # 엣지 추가
            graph_builder.add_edge(START, "llm")
            graph_builder.add_conditional_edges("llm", should_continue, ["tools", END])
            graph_builder.add_edge("tools", "llm")

            # Graph 컴파일
            graph = graph_builder.compile()

            # 시스템 메시지
            system_msg = SystemMessage(
                content="당신은 노트 관리 전문 AI 비서입니다. "
                        "사용자의 노트를 생성, 조회, 검색, 수정, 삭제하는 작업을 도와줍니다."
                        "사용자로부터 노트의 내용을 중심으로 입력받고, 제목이나 태그가 명시되지 않았다면 자동으로 생성하여 저장하세요."
            )

            print("=" * 60)
            print("📝 노트 관리 에이전트 시작")
            print("=" * 60)
            print("  - 'quit' 또는 'exit': 종료")
            print("-" * 60)
            print()

            while True:
                # 사용자 입력
                user_input = input("💬 질문: ").strip()

                if user_input.lower() in ["quit", "exit"]:
                    print("👋 노트 관리 에이전트를 종료합니다.")
                    break

                if not user_input:
                    continue

                # 초기 상태
                initial_state = {
                    "messages": [system_msg, HumanMessage(content=user_input)],
                    "llm_calls": 0
                }

                try:
                    # Graph 실행
                    result = await graph.ainvoke(initial_state)

                    # 최종 응답 출력
                    final_message = result["messages"][-1]
                    print(f"\n🤖 응답:\n{final_message.content}\n")
                    print("-" * 60)

                except Exception as e:
                    print(f"오류 발생: {e}")
                    print("-" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 프로그램이 중단되었습니다.")
        sys.exit(0)
