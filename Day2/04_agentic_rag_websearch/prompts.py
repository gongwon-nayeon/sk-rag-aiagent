from langchain_core.prompts import ChatPromptTemplate


# 질문 분석 프롬프트 (의도 파악)
QUERY_ANALYSIS_PROMPT = ChatPromptTemplate.from_template(
    """
    당신은 사용자 질문의 의도를 파악하는 분석가입니다.

    질문을 분석하여 다음 중 하나로 분류하세요:

    1. 'simple': 간단한 대화, 인사, 감정 표현 (예: "안녕", "고마워", "잘가")
    2. 'rag': AI 기술/산업 관련 질문 (AI Brief 문서에서 찾을 수 있는 내용)
       - 생성형 AI, LLM, AI 정책, AI 산업 동향 등
    3. 'web': 일반적인 지식, 최신 정보, AI Brief와 무관한 질문
       - 날씨, 뉴스, 일반 지식, 코딩 방법 등

    <question>
    {question}
    </question>

    위 질문을 분석하여 'simple', 'rag', 'web' 중 하나를 반환하세요.
    """
)


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
    당신은 답변이 질문에 대해 유용한 정보를 제공하는지 평가하는 평가자입니다.

    <question>
    {question}
    </question>

    <generation>
    {generation}
    </generation>

    다음 기준으로 평가하세요:
    - 답변이 질문의 핵심 의도에 대응하는가?
    - 질문에서 요청한 정보를 실질적으로 제공하는가?
    - 답변 내용이 질문과 관련성이 있는가?

    답변이 질문에 대해 의미 있는 정보를 제공한다면 'yes'를 반환하세요.
    답변이 질문과 완전히 무관하거나 요청한 정보를 전혀 제공하지 않을 때만 'no'를 반환하세요.

    관대하게 평가하세요. 답변이 부분적으로라도 질문에 답하고 있다면 'yes'입니다.
    """
)


# 쿼리 재작성 프롬프트 (검색 대상에 따라 재작성 지침이 달라짐)
QUERY_REWRITER_PROMPT = ChatPromptTemplate.from_template(
    """
    당신은 입력된 질문을 더 나은 검색 쿼리로 변환하는 질문 재작성자입니다.
    입력을 보고 근본적인 의미적 의도를 추론하세요.

    <question>
    {question}
    </question>

    <guidance>
    {rewrite_guidance}
    </guidance>

    위 지침에 따라 질문을 개선하여 한국어로 재작성하세요.
    """
)


# 간단한 대화 응답용 시스템 프롬프트
SIMPLE_RESPONSE_SYSTEM_PROMPT = """
당신은 친절하고 자연스럽게 대화하는 AI 어시스턴트입니다.
인사, 감사 표현 등 간단한 대화에 대해 짧고 자연스럽게 응답하세요.
이전 대화 맥락이 있다면 이를 참고하여 일관성 있게 답변하세요.
"""


# RAG/웹 검색 결과 기반 답변 생성용 시스템 프롬프트
GENERATE_SYSTEM_PROMPT = """
당신은 관련 문서를 기반으로 답변하는 어시스턴트입니다.
주어진 문서 텍스트와 이전 대화 맥락을 기반으로 사용자의 질문에 대해 충실히 답변하세요.

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
