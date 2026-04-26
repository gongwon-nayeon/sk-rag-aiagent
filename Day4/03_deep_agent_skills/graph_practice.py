"""
자율 실습용 Deep Agent with Custom Skills
==========================================

이 파일은 직접 나만의 스킬(Skill)을 만들어보는 자율 실습용입니다.

실습 목표:
1. ./skills/my-skill-name/SKILL.md 파일을 작성하여 나만의 스킬 정의하기
2. 필요한 경우 추가 도구(tool) 작성하기
3. Deep Agent를 실행하여 스킬이 올바르게 작동하는지 테스트하기 (uv run langgraph dev)

실습 가이드:
- SKILL.md 파일의 템플릿을 따라 작성하세요
- 스킬은 에이전트가 특정 작업을 수행할 때 따라야 할 단계별 프로세스입니다
- 간단한 예시: 특정 주제에 대한 조사 프로세스, 코드 리뷰 체크리스트, 문서 작성 가이드 등
"""

from pathlib import Path
import requests

from deepagents import create_deep_agent  # type: ignore
from deepagents.backends.filesystem import FilesystemBackend  # type: ignore
from dotenv import load_dotenv
from langchain.tools import tool

load_dotenv()


# ========================================
# 기본 도구 정의
# ========================================

@tool
def fetch_url(url: str) -> str:
    """URL에서 콘텐츠를 가져옵니다.

    Args:
        url: 가져올 URL

    Returns:
        URL의 텍스트 내용

    Note:
        웹 리소스를 가져오는 데 사용됩니다.
    """
    print(f"\n{'='*70}")
    print(f"🌐 URL에서 콘텐츠 가져오는 중: {url}")
    print(f"{'='*70}\n")

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        content = response.text

        print(f"✅ 성공적으로 {len(content)} 문자를 가져왔습니다.\n")
        return content
    except requests.RequestException as e:
        error_msg = f"❌ URL 가져오기 실패: {str(e)}"
        print(f"{error_msg}\n")
        return error_msg


# ========================================
# [TODO] 여기에 나만의 도구(tool)를 추가하세요
# ========================================
# 예시:
# @tool
# def my_custom_tool(param: str) -> str:
#     """도구 설명을 작성하세요."""
#     # 여기에 로직을 구현하세요
#     return f"결과: {param}"


# ========================================
# Deep Agent 생성 함수
# ========================================

def create_custom_skill_agent():
    """커스텀 스킬이 포함된 deep agent를 생성하고 반환합니다.

    Returns:
        CompiledGraph: 구성된 deep agent
    """
    # 현재 스크립트의 디렉터리 가져오기
    base_dir = Path(__file__).parent

    # [TODO] 필요한 경우 여기에 추가 도구를 넣으세요
    tools = [fetch_url]

    # Deep Agent 생성
    agent = create_deep_agent(
        model="openai:gpt-5.4", # or "gpt-4o"
        tools=tools,
        skills=["./skills/"],  # skills 폴더의 모든 SKILL.md 파일을 로드
        backend=FilesystemBackend(root_dir=str(base_dir), virtual_mode=True),
        system_prompt=(
            "당신은 도움이 되는 AI 어시스턴트입니다.\n\n"
            "**중요: SKILL 파일은 단순 참고 자료가 아니라 반드시 따라야 할 실행 프로세스입니다.**\n"
            "사용자의 질문에 답변할 때, 관련된 스킬이 있다면 반드시 해당 스킬의 프로세스를 따라 진행하세요.\n\n"
        )
    )

    return agent
