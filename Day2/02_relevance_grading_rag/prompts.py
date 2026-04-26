from langchain_core.prompts import ChatPromptTemplate


# 문서 관련성 평가 프롬프트
RELEVANCE_GRADER_PROMPT = ChatPromptTemplate.from_template(
    """
    당신은 사용자의 질문에 대한 검색된 문서의 관련성을 평가하는 평가자입니다.

    <context>
    {context}
    </context>

    <question>
    {question}
    </question>

    사용자의 질문이 너무 짧거나, 모호하거나, 명확한 의도를 판단하기에 충분한 맥락이 부족한 경우,
    관련성이 없다고 평가하고 "no"를 반환하세요.
    관련성이 있는 경우 "yes"를 반환하세요.
    """
)


# 질문 재작성 프롬프트
REWRITE_PROMPT = """
당신은 질문을 더 명확하고 구체적으로 개선하는 전문가입니다.
사용자의 질문이 모호하거나 맥락이 부족하여 관련 문서를 찾지 못했습니다.

원래 질문을 분석하고, 더 명확하고 구체적인 질문으로 재작성하세요.

<guidelines>
- 질문의 의도를 명확히 표현
- 구체적인 키워드와 맥락 추가
- 검색하기 쉬운 형태로 재구성
</guidelines>

<original question>
{question}
</original question>

재작성된 질문만 출력하세요.
"""
