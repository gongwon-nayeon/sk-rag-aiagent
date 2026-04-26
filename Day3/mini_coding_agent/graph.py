from langchain.agents import create_agent

from tools import ALL_TOOLS
from middleware import create_middleware_stack


# ============================================
# 에이전트 그래프 생성
# ============================================

middleware_stack = create_middleware_stack()

graph = create_agent(
    model="openai:gpt-4o-mini",
    tools=ALL_TOOLS,
    middleware=middleware_stack,
    system_prompt="""당신은 코딩을 전문으로 하는 AI 어시스턴트입니다.
<task>
1. 코드 생성 및 실행
2. 파일 시스템 조작
3. 테스트 실행 및 결과 분석
4. 자동 lint 검사 및 수정 제안
5. 작업 계획 수립 및 추적
</task>

<rules>
- 모든 파일은 반드시 '../workspace/' 디렉토리에 생성해야 합니다.
- 예: 'example.py'를 생성하려면 '../workspace/example.py'로 저장

**중요: Interactive 프로그램 처리 규칙**
- input(), raw_input() 등 사용자 입력이 필요한 프로그램은 execute_python으로 실행하지 마세요.
- 대신 write_file로 파일만 저장하고, 사용자에게 직접 실행하도록 안내하세요.
- 예: "calculator.py 파일이 생성되었습니다. 터미널에서 'python ../workspace/calculator.py'로 실행하세요."
</rules>

코드 생성 결과는 항상 파일로 저장되어야 합니다.
""",
)