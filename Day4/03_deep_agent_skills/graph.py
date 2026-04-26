from pathlib import Path
import requests

from deepagents import create_deep_agent # type: ignore
from deepagents.backends.filesystem import FilesystemBackend # type: ignore
from dotenv import load_dotenv
from langchain.tools import tool

load_dotenv()

@tool
def fetch_url(url: str) -> str:
    """URL에서 콘텐츠를 가져옵니다.

    Args:
        url: 가져올 URL

    Returns:
        URL의 텍스트 내용

    Note:
        LangGraph 문서 및 기타 웹 리소스를 가져오는 데 사용됩니다.
    """
    print(f"\n{'='*70}")
    print(f"🌐 URL에서 콘텐츠 가져오는 중: {url}")
    print(f"{'='*70}\n")

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        content = response.text

        print(f"성공적으로 {len(content)} 문자를 가져왔습니다.\n")
        return content
    except requests.RequestException as e:
        error_msg = f"URL 가져오기 실패: {str(e)}"
        print(f"{error_msg}\n")
        return error_msg


def create_langgraph_doc_assistant():
    """LangGraph 문서 스킬이 포함된 문서 도우미 deep agent를 생성하고 반환합니다.

    Returns:
        CompiledGraph: 구성된 deep agent
    """
    # 현재 스크립트의 디렉터리 가져오기
    base_dir = Path(__file__).parent

    tools = [fetch_url]

    agent = create_deep_agent(
        model="openai:gpt-5.4", # or "gpt-4o"
        tools=tools,
        skills=["./skills/"],
        backend=FilesystemBackend(root_dir=str(base_dir), virtual_mode=True),  # 파일시스템 백엔드 사용
        system_prompt=(
            "당신은 LangGraph/LangChain 문서 도우미입니다.\n\n"
            "**중요: SKILL 파일은 단순 참고 자료가 아니라 반드시 따라야 할 실행 프로세스입니다.**\n\n"
        )
    )

    return agent
