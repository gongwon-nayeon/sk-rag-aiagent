from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from state import State, _get_llm
from retriever import setup_retriever

# 모듈 레벨에서 한 번만 초기화
_, retriever_tool = setup_retriever()
llm = _get_llm()
llm_with_tools = llm.bind_tools([retriever_tool])


def chatbot(state: State):
    """
    LLM이 사용자 질문을 분석하고 필요시 도구를 호출합니다.
    """
    query = state["query"]
    messages = [HumanMessage(content=query)]
    response = llm_with_tools.invoke(messages)
    return {
        "query": query,
        "messages": [response],
        "answer": response.content # tool_calls 가 존재해서 content가 비워져 있는 상태여도, 결국 answer 노드에서 다시 덮어씌워짐
        }


def answer(state: State):
    """
    검색된 문서를 기반으로 사용자 질문에 답변합니다.
    """
    print("##### ANSWER #####")
    query = state["query"]
    context = state["messages"][-1].content  # 마지막 메시지 = tool에서 반환된 검색 결과

    # 커스텀 시스템 프롬프트 사용
    SYSTEM_PROMPT = """
    당신은 관련 문서를 기반으로 답변하는 어시스턴트입니다.
    주어진 문서 텍스트를 기반으로 사용자의 질문에 대해 충실히 답변하세요.
    답변은 마크다운 문법 형식으로 적절한 볼드체, 제목, 불렛 등을 사용하여 가독성 좋게 작성하세요.
    """
    system_msg = SystemMessage(SYSTEM_PROMPT)
    human_msg = HumanMessage(f"""
    다음은 주어진 문서 텍스트입니다.
    <context>
    {context}
    </context>

    <question>
    {query}
    </question>
    """)

    # LLM 호출
    llm = _get_llm()
    response = llm.invoke([system_msg, human_msg])

    print(f"[생성된 답변]\n{response.content}\n")

    return {
        "query": query,
        "context": context,
        "answer": response.content,
        "messages": [response]
    }
