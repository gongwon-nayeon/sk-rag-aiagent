from typing import Literal
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from state import State, _get_llm
from prompts import (
    QUERY_ANALYSIS_PROMPT,
    RELEVANCE_GRADER_PROMPT,
    HALLUCINATION_GRADER_PROMPT,
    ANSWER_GRADER_PROMPT,
    QUERY_REWRITER_PROMPT,
)
from retriever import setup_retriever

# 모듈 레벨에서 한 번만 초기화
retriever, retriever_tool = setup_retriever()
llm = _get_llm()

from dotenv import load_dotenv

load_dotenv()


# ===============================
# Pydantic Models
# ===============================

class RouteQuery(BaseModel):
    """질문 의도 분류"""
    intent: str = Field(
        description="질문의 의도: 'simple' (간단한 대화), 'rag' (AI 문서 검색), 'web' (웹 검색)"
    )


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


# ===============================
# Nodes
# ===============================

def query_analysis(state: State):
    """
    질문의 의도를 분석합니다.
    simple: 간단한 대화 → 직접 답변
    rag: AI 문서 검색 → retrieve
    web: 웹 검색 → web_search
    """
    print("##### QUERY ANALYSIS #####")

    question = state["question"]
    print(f"Analyzing question: {question}")

    # LLM으로 질문 분석
    llm = _get_llm()
    router = llm.with_structured_output(RouteQuery)
    chain = QUERY_ANALYSIS_PROMPT | router

    result = chain.invoke({"question": question})
    intent = result.intent

    print(f"Intent: {intent}")

    return {"question": question, "intent": intent}


def simple_response(state: State):
    """
    간단한 대화에 대해 직접 답변합니다.
    """
    print("##### SIMPLE RESPONSE #####")

    question = state["question"]
    llm = _get_llm()

    response = llm.invoke([HumanMessage(content=question)])

    print(f"Response: {response.content}")

    return {"generation": response.content, "messages": [response]}


def retrieve(state: State):
    """
    벡터스토어에서 관련 문서를 검색합니다.
    """
    print("##### RETRIEVE #####")

    question = state["question"]
    print(f"Question: {question}")

    # 문서 검색
    documents = retriever.invoke(question)

    # 검색 결과를 문자열로 변환
    context = ""
    for idx, doc in enumerate(documents):
        context += f"Document {idx + 1}:\n{doc.page_content}\n{doc.metadata}\n"
        print(f"Retrieved Document {idx + 1}: {doc.page_content[:100]}...")

    return {"document": context, "question": question}


def web_search(state: State):
    """
    웹 검색을 수행합니다.
    """
    print("##### WEB SEARCH #####")

    from langchain_tavily import TavilySearch # type: ignore

    question = state["question"]
    print(f"Question: {question}")

    # 웹 검색 수행
    search_tool = TavilySearch(max_results=3, topic="general")
    results = search_tool.invoke(question)

    # 결과를 문자열로 포맷팅
    context = ""
    if isinstance(results, list):
        for idx, result in enumerate(results):
            if isinstance(result, dict):
                context += f"\n[웹 검색 결과 {idx + 1}]\n"
                context += f"제목: {result.get('title', 'N/A')}\n"
                context += f"내용: {result.get('content', 'N/A')}\n"
                context += f"출처: {result.get('url', 'N/A')}\n"
            else:
                context += f"\n[웹 검색 결과 {idx + 1}]: {result}\n"
    else:
        context = str(results)

    print(f"Web search completed")

    return {
        "document": context,
        "question": question
    }


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
        return {"document": document, "question": question, "retry_num": state.get("retry_num", 0)}
    else:
        print("---GRADE: DOCUMENT NOT RELEVANT---")
        return {"document": "", "question": question, "retry_num": state.get("retry_num", 0)}


def generate(state: State):
    """
    검색된 문서를 기반으로 최종 답변을 생성합니다.
    RAG 문서 또는 웹 검색 결과를 모두 처리할 수 있습니다.
    """
    print("##### GENERATE #####")

    question = state["question"]
    document = state.get("document", "")

    if not document:
        print("Warning: No document found, using empty context")

    print(f"Question: {question}")
    print(f"Context: {document[:100] if document else 'No context'}...")

    # RAG 프롬프트 사용
    llm = _get_llm()

    SYSTEM_PROMPT = """
    당신은 관련 문서를 기반으로 답변하는 어시스턴트입니다.
    주어진 문서 텍스트를 기반으로 사용자의 질문에 대해 충실히 답변하세요.

    <rules>
    - context에 제공된 문서의 출처를 언급하며 답변을 작성하세요.
    - 문서가 RAG에서 온 경우: 파일명과 페이지 번호를 명시하세요.
    - 문서가 웹 검색에서 온 경우: 출처 URL을 명시하세요.
    - 답변은 마크다운 문법 형식으로 적절한 볼드체, 제목, 불렛 등을 사용하여 가독성 좋게 작성하세요.
    </rules>

    <output_format>
    답변은 아래와 같은 예시를 참고하여 구조적으로 작성하세요:
    [답변 본문]

    ===
    [출처]
    - RAG 문서: 파일명과 페이지 번호
    - 웹 검색: URL
    </output_format>
    """

    system_msg = SystemMessage(SYSTEM_PROMPT)
    human_msg = HumanMessage(f"""
    다음은 주어진 문서 텍스트입니다.
    <context>
    {document if document else "문서 없음"}
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
        "messages": [response],
        "retry_num": state.get("retry_num", 0)
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
        "messages": [better_question],
        "retry_num": state.get("retry_num", 0) + 1
    }


# ===============================
# 엣지 조건 함수
# ===============================

def route_question(state: State) -> Literal["simple_response", "retrieve", "web_search"]:
    """
    Query Analysis 결과에 따라 질문을 라우팅합니다.
    simple: simple_response (직접 답변)
    rag: retrieve (RAG 플로우)
    web: web_search (웹 검색)
    """
    print("##### ROUTE QUESTION #####")

    intent = state.get("intent", "rag")

    if intent == "simple":
        print("---ROUTE DECISION: SIMPLE CONVERSATION---")
        return "simple_response"
    elif intent == "rag":
        print("---ROUTE DECISION: RAG SEARCH---")
        return "retrieve"
    else:  # web
        print("---ROUTE DECISION: WEB SEARCH---")
        return "web_search"


def decide_to_generate(state: State) -> Literal["transform_query", "generate"]:
    """
    문서 관련성에 따라 답변 생성 또는 쿼리 재작성을 결정합니다.
    관련성 있음 -> generate, 관련성 없음 -> transform_query
    """
    print("##### ASSESS GRADED DOCUMENTS #####")

    if state["document"] == "" and state.get("retry_num", 0) < 2:
        print("---DECISION: TRANSFORM QUERY---")
        return "transform_query"
    else:
        print("---DECISION: GENERATE---")
        return "generate"


def grade_generation_v_documents_and_question(state: State) -> Literal["useful", "not useful", "not supported"]:
    """
    생성된 답변의 환각 여부와 유용성을 평가합니다.
    useful: 환각 없고 유용함
    not useful: 환각 없지만 유용하지 않음
    not supported: 환각 발생
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

        if grade == "yes" or state.get("retry_num", 0) >= 2:  # 유용함
            print("---DECISION: GENERATION ADDRESSES QUESTION---")
            return "useful"
        else:  # 유용하지 않음
            print("---DECISION: GENERATION DOES NOT ADDRESS QUESTION---")
            return "not useful"
    else:  # 환각 발생
        print("---DECISION: GENERATION IS NOT GROUNDED IN DOCUMENTS, RE-TRY---")
        return "not supported"
