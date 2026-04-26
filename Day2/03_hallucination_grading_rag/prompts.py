from langchain_core.prompts import ChatPromptTemplate


# 문서 관련성 평가 프롬프트
RELEVANCE_GRADER_PROMPT = ChatPromptTemplate.from_template(
    """
    당신은 사용자 질문에 대한 검색된 문서의 관련성을 평가하는 평가자입니다.

    <context>
    {context}
    </context>

    <question>
    {question}
    </question>

    문서가 사용자 질문과 관련된 키워드나 의미를 포함하고 있다면, 관련성이 있다고 평가하세요.
    엄격한 테스트일 필요는 없습니다. 목표는 잘못된 검색 결과를 걸러내는 것입니다.

    관련성이 있는 경우 'yes', 관련성이 없는 경우 'no'를 반환하세요.
    """
)


# 환각 평가 프롬프트
HALLUCINATION_GRADER_PROMPT = ChatPromptTemplate.from_template(
    """
    당신은 LLM이 생성한 답변이 검색된 사실에 근거하고 있는지 평가하는 평가자입니다.

    <facts>
    {document}
    </facts>

    <generation>
    {generation}
    </generation>

    답변이 주어진 사실에 근거하고 있으면 'yes', 그렇지 않으면 'no'를 반환하세요.
    'yes'는 답변이 사실 세트에 의해 뒷받침된다는 의미입니다.
    """
)


# 답변 유용성 평가 프롬프트
ANSWER_GRADER_PROMPT = ChatPromptTemplate.from_template(
    """
    당신은 답변이 질문을 해결하는지 평가하는 평가자입니다.

    <question>
    {question}
    </question>

    <generation>
    {generation}
    </generation>

    답변이 질문을 해결하면 'yes', 그렇지 않으면 'no'를 반환하세요.
    모호한 경우에는 'no'를 반환하세요.
    """
)


# 쿼리 재작성 프롬프트
QUERY_REWRITER_PROMPT = ChatPromptTemplate.from_template(
    """
    당신은 입력된 질문을 벡터스토어 검색에 최적화된 더 나은 버전으로 변환하는 질문 재작성자입니다.
    입력을 보고 근본적인 의미적 의도를 추론하세요.

    <question>
    {question}
    </question>

    위 질문을 개선하여 한국어로 재작성하세요.
    """
)
