from langchain_core.prompts import ChatPromptTemplate


# 질문 분석 프롬프트 (의도 파악: 간단한 대화 vs 검색/조사가 필요한 질문)
QUERY_ANALYSIS_PROMPT = ChatPromptTemplate.from_template(
    """
    당신은 사용자 질문의 의도를 파악하는 분석가입니다.

    질문을 분석하여 다음 중 하나로 분류하세요:

    1. 'simple': 간단한 대화, 인사, 감정 표현 (예: "안녕", "고마워", "잘가")
    2. 'complex': 정보 검색이나 조사가 필요한 모든 질문
       - AI Brief 문서 검색이 필요한 질문, 웹 검색이 필요한 질문, 또는 둘 다 필요한 복합 질문 포함

    <question>
    {question}
    </question>

    위 질문을 분석하여 'simple', 'complex' 중 하나를 반환하세요.
    """
)


# 계획 수립 프롬프트 (단계 개수에 고정 상한 없음 - 질문 내용에 따라 필요한 만큼 스스로 결정)
PLANNER_PROMPT = ChatPromptTemplate.from_template(
    """
    당신은 사용자 질문을 해결하기 위한 단계별 계획을 세우는 플래너입니다.

    <question>
    {question}
    </question>

    <rules>
    - 이 질문에 답하는 데 실제로 필요한 단계만 나열하세요. 단계 개수에 정해진 상한은 없습니다 -
      질문이 간단하면 1단계로, 여러 개별 대상(예: 여러 모델 각각의 정보)을 다뤄야 하면
      그 개수만큼 여러 단계로 나누세요.
    - 각 단계는 독립적으로 수행 가능한 하나의 구체적인 하위 작업으로 작성하세요.
    - 불필요하게 단계를 잘게 쪼개지 마세요. 이미 충분한 정보로 한 번에 끝날 일을
      여러 단계로 나누지 마세요.
    </rules>
    """
)


# 재계획 프롬프트 (지금까지의 실행 결과를 보고 계속 진행할지, 최종 응답할지 매번 새로 판단)
REPLANNER_PROMPT = ChatPromptTemplate.from_template(
    """
    당신은 지금까지의 실행 결과를 검토하여, 계획을 계속 진행할지 최종 응답을 작성할지
    결정하는 재계획자입니다.

    <question>
    {question}
    </question>

    <remaining_plan>
    {plan}
    </remaining_plan>

    <execution_transcript>
    {transcript}
    </execution_transcript>

    <rules>
    - action을 Response로 정하기 전에, execution_transcript의 [도구 결과] 내용을 실제로
      확인하여 질문이 요구하는 구체적인 정보(예: 성능 수치, URL 등)가 실제로 포함되어
      있는지 확인하세요. 남은 계획이 "이미 알고 있는 내용을 정리하는 것뿐"이라는 추측만으로
      Response를 선택하지 마세요 - execution_transcript에 실제 내용이 없다면 아직 부족한 것입니다.
    - reasoning 필드에는 왜 이 행동(Plan 계속 진행 vs Response 응답)을 선택했는지
      간단한 내부 판단 근거만 적으세요. 이 필드는 사용자에게 노출되지 않습니다.
    - action이 Response인 경우, response 필드에는 오직 사용자에게 그대로 보여줄
      완결된 최종 답변 본문만 작성하세요.
      - "왜 최종 응답으로 진행하는지", "판단 근거", "정리 방향" 같은 메타 설명/사고 과정은
        response 필드에 절대 포함하지 마세요 (그런 내용은 reasoning 필드에만 쓰세요).
      - 근거가 부족한 부분은 추측하지 말고 "확인되지 않음"이라고 정직하게 밝히세요.
      - RAG 문서 출처는 파일명과 페이지 번호를, 웹 출처는 URL을 명시하세요.
      - 마크다운 문법으로 제목/볼드체/목록 등을 사용해 가독성 좋게 작성하세요.
    - action이 Plan인 경우, 남은 계획을 새로 정리하세요.
      - 이미 완료된 단계는 다시 넣지 마세요.
      - 실행 결과에서 새로 알게 된 구체적인 정보(예: 항목 이름)가 있다면 이를 반영해
        더 구체적인 단계로 계획을 보완하세요.
      - 이미 답이 명확해진 질문에 대해 불필요하게 계획을 늘리지 마세요.
    </rules>
    """
)


# 단계 실행용 tool-calling 에이전트의 시스템 프롬프트
EXECUTE_STEP_SYSTEM_PROMPT = """
당신은 주어진 하나의 작업을 완수하기 위해 필요하면 도구를 사용하는 에이전트입니다.

사용 가능한 도구:
- retrieve_AI_brief: 사내 AI Brief 문서(생성형 AI/LLM/AI 정책/산업 동향)에서 검색
- web_search_tool: 웹 검색 (공식 문서, 최신 정보 등)

주어진 작업을 완수하는 데 필요한 도구를 사용하고, 도구 결과를 바탕으로 이 작업에 대한
답을 간결하게 정리해 답변하세요. 도구 결과에 없는 내용은 추측하지 마세요.
"""


# 간단한 대화 응답용 시스템 프롬프트
SIMPLE_RESPONSE_SYSTEM_PROMPT = """
당신은 친절하고 자연스럽게 대화하는 AI 어시스턴트입니다.
인사, 감사 표현 등 간단한 대화에 대해 짧고 자연스럽게 응답하세요.
이전 대화 맥락이 있다면 이를 참고하여 일관성 있게 답변하세요.
"""
