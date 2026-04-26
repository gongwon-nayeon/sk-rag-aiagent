from typing import Literal
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from state import State, _get_llm
from prompts import RELEVANCE_GRADER_PROMPT, REWRITE_PROMPT
from retriever import setup_retriever
from time import strftime

_, retriever_tool = setup_retriever()
llm = _get_llm()


def chatbot(state: State):
    """
    LLM이 사용자 질문을 분석하고 필요시 도구를 호출합니다.
    """
    print("##### CHATBOT #####")

    question = state["query"]
    print(f"Using original question: {question}")

    current_time = strftime("%Y-%m-%d %H:%M:%S")
    messages = [SystemMessage(content="당신은 사용자의 질문에 답변하기 위해 관련 문서를 검색하는 어시스턴트입니다. 현재 시각은 {current_time}입니다.".format(current_time=current_time)),
                HumanMessage(content=question)]

    llm_with_tools = llm.bind_tools([retriever_tool])
    response = llm_with_tools.invoke(messages)

    return {
        "messages": [response]
    }


def rewrite(state: State):
    """
    LLM이 더 명확하고 구체적인 질문으로 자동 재작성합니다.
    """
    print("##### REWRITE #####")

    question = state["query"]

    print(f"Original Question: {question}")

    system_msg = SystemMessage(REWRITE_PROMPT.format(question=question))
    response = llm.invoke([system_msg])
    rewritten_question = response.content

    print(f"Rewritten Question: {rewritten_question}")

    return {
        "messages": [HumanMessage(content=rewritten_question)],
        "query": rewritten_question,
        "retry_count": state.get("retry_count", 0) + 1
    }


def generate(state: State):
    """
    검색된 문서를 기반으로 최종 답변을 생성합니다.
    """
    print("##### GENERATE #####")

    # 질문 추출
    question = state["query"]

    # 검색된 문서 추출
    context = state["messages"][-1].content # 바로 전 단계는 무조건 retriever이므로, 검색된 문서가 messages의 마지막에 있다고 가정

    print(f"Question: {question}")
    print(f"Context: {context[:100]}...")

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
    {question}
    </question>
    """)

    response = llm.invoke([system_msg, human_msg])

    print(f"Response: {response.content[:100]}...")

    return {
        "messages": [response],
        "answer": response.content
    }

# ========================================================
# 엣지 조건 함수
# ========================================================

class Grade(BaseModel):
    """Binary score for relevance check."""
    binary_score: str = Field(description="Relevance score 'yes' or 'no'")


def grade_documents(state: State) -> Literal["generate", "rewrite"]:
    """
    검색된 문서가 질문과 관련이 있는지 평가합니다.
    """
    print("##### CHECK RELEVANCE #####")

    # 관련성 평가 체인 생성
    llm = _get_llm()
    grader = llm.with_structured_output(Grade)
    chain = RELEVANCE_GRADER_PROMPT | grader

    # 질문 추출 (재작성된 질문이 있으면 사용)
    if state.get("query"):
        question = state["query"]
    else:
        question = state["query"]

    # 검색된 문서 추출
    docs = state["messages"][-1].content

    print(f"Question: {question}")
    print(f"Context: {docs[:100]}...")

    # 관련성 평가
    scored_result = chain.invoke({"question": question, "context": docs})
    score = scored_result.binary_score

    if score == "yes" or state.get("retry_count", 0) >= 2:  # 관련성이 있다고 평가되거나, 재시도 횟수가 2회 이상인 경우
        print("---DECISION: DOCS RELEVANT---")
        return "generate"
    else:
        print("---DECISION: DOCS NOT RELEVANT---")
        return "rewrite"
