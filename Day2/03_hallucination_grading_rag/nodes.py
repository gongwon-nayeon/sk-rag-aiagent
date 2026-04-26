from typing import Literal
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from state import State, _get_llm
from prompts import (
    RELEVANCE_GRADER_PROMPT,
    HALLUCINATION_GRADER_PROMPT,
    ANSWER_GRADER_PROMPT,
    QUERY_REWRITER_PROMPT,
)
from retriever import setup_retriever

# 모듈 레벨에서 한 번만 초기화
retriever, retriever_tool = setup_retriever()
llm = _get_llm()


def agent(state: State):
    """
    LLM이 사용자 질문을 분석하고 필요시 Retriever Tool을 호출합니다.
    """
    print("##### AGENT #####")

    question = state["question"]
    print(f"Using original question: {question}")

    messages = [HumanMessage(content=question)]

    # LLM에 도구 바인딩
    llm_with_tools = llm.bind_tools([retriever_tool])
    response = llm_with_tools.invoke(messages)

    print(f"Response: {response}")

    return {"messages": [response], "question": question, "generation": response.content}


def retrieve(state: State):
    """
    벡터스토어에서 관련 문서를 검색합니다.
    """
    print("##### RETRIEVE #####")

    question = state["question"]
    print(f"Question: {question}")

    # 문서 검색
    document = retriever.invoke(question)

    # 직접 검색 결과를 상태에 저장 - 이후 노드에서 활용(합치지 않고 리스트로 저장하여 grade_documents에서 개별 문서 평가 가능)
    context = ""
    for idx, doc in enumerate(document):
        context += f"Document {idx + 1}:\n{doc.page_content}\n문서 페이지: {doc.metadata['page']}\n"
        print(f"Retrieved Document {idx + 1}: {doc.page_content[:100]}...")

    return {"document": context, "question": question}


def grade_documents(state: State):
    """
    검색된 문서가 질문과 관련이 있는지 평가합니다.
    """
    print("##### CHECK RELEVANCE #####")

    question = state["question"]
    document = state["document"]

    # 관련성 평가
    llm = _get_llm()
    grader = llm.with_structured_output(Grade)
    chain = RELEVANCE_GRADER_PROMPT | grader

    score = chain.invoke({"question": question, "context": document})
    grade = score.binary_score

    print(f"Question: {question}")
    print(f"Context: {document[:100]}...")
    print(f"Grade: {grade}")

    if grade == "yes":
        print("---GRADE: DOCUMENT RELEVANT---")
        return {"document": document, "question": question}
    else:
        print("---GRADE: DOCUMENT NOT RELEVANT---")
        return {"document": "", "question": question}


def generate(state: State):
    """
    검색된 문서를 기반으로 최종 답변을 생성합니다.
    """
    print("##### GENERATE #####")

    question = state["question"]
    document = state["document"]

    print(f"Question: {question}")
    print(f"Context: {document[:100]}...")

    # RAG 프롬프트 사용
    llm = _get_llm()

    SYSTEM_PROMPT = """
    당신은 관련 문서를 기반으로 답변하는 어시스턴트입니다.
    주어진 문서 텍스트를 기반으로 사용자의 질문에 대해 충실히 답변하세요.
    답변은 마크다운 문법 형식으로 적절한 볼드체, 제목, 불렛 등을 사용하여 가독성 좋게 작성하세요.
    문서의 출처(문서의 원본 출처와 페이지 출처)도 함께 명시하세요.
    """

    system_msg = SystemMessage(SYSTEM_PROMPT)
    human_msg = HumanMessage(f"""
    다음은 주어진 문서 텍스트입니다.
    <context>
    {document}
    </context>

    <question>
    {question}
    </question>
    """)

    response = llm.invoke([system_msg, human_msg])

    print(f"Response: {response.content[:100]}...")

    return {
        "documents": document,
        "question": question,
        "generation": response.content,
        "messages": [response]
    }


def transform_query(state: State):
    """
    검색 성능 향상을 위해 질문을 재작성합니다.
    """
    print("##### TRANSFORM QUERY #####")

    question = state["question"]

    # 쿼리 재작성
    llm = _get_llm()
    question_rewriter = QUERY_REWRITER_PROMPT | llm
    better_question = question_rewriter.invoke({"question": question})

    print(f"Original Question: {question}")
    print(f"Better Question: {better_question.content}")

    return {
        "question": better_question.content,
        "messages": [better_question]
    }

# ===============================
# 엣지 조건 함수
# ===============================

class Grade(BaseModel):
    """Binary score for relevance check."""
    binary_score: str = Field(description="Relevance score 'yes' or 'no'")


class GradeHallucinations(BaseModel):
    """Binary score for hallucination present in generation answer."""
    binary_score: str = Field(
        description="Answer is grounded in the facts, 'yes' or 'no'"
    )


class GradeAnswer(BaseModel):
    """Binary score to assess answer addresses question."""
    binary_score: str = Field(
        description="Answer addresses the question, 'yes' or 'no'"
    )


def decide_to_generate(state: State) -> Literal["transform_query", "generate"]:
    """
    문서 관련성에 따라 답변 생성 또는 쿼리 재작성을 결정합니다.
    관련성 있음 -> generate, 관련성 없음 -> transform_query
    """
    print("##### ASSESS GRADED DOCUMENTS #####")

    if state["document"] == "":
        print("---DECISION: TRANSFORM QUERY---")
        return "transform_query"
    else:
        print("---DECISION: GENERATE---")
        return "generate"


def grade_generation_v_documents_and_question(state: State) -> Literal["useful", "not useful", "not supported"]:
    """
    생성된 답변의 환각 여부와 유용성을 평가합니다.
    useful: 환각 없고 유용함 | not useful: 환각 없지만 유용하지 않음 | not supported: 환각 발생
    """
    print("##### CHECK HALLUCINATIONS #####")

    question = state["question"]
    document = state["document"]
    generation = state["generation"]

    # 환각 평가
    llm = _get_llm()
    hallucination_grader = llm.with_structured_output(GradeHallucinations)
    hallucination_chain = HALLUCINATION_GRADER_PROMPT | hallucination_grader

    score = hallucination_chain.invoke({
        "document": document,
        "generation": generation
    })
    grade = score.binary_score

    if grade == "yes":  # 환각 없음
        print("---DECISION: GENERATION IS GROUNDED IN DOCUMENTS---")

        # 답변 유용성 평가
        llm = _get_llm()
        answer_grader = llm.with_structured_output(GradeAnswer)
        answer_chain = ANSWER_GRADER_PROMPT | answer_grader

        score = answer_chain.invoke({
            "question": question,
            "generation": generation
        })
        grade = score.binary_score

        if grade == "yes":  # 유용함
            print("---DECISION: GENERATION ADDRESSES QUESTION---")
            return "useful"
        else:  # 유용하지 않음
            print("---DECISION: GENERATION DOES NOT ADDRESS QUESTION---")
            return "not useful"
    else:  # 환각 발생
        print("---DECISION: GENERATION IS NOT GROUNDED IN DOCUMENTS, RE-TRY---")
        return "not supported"
