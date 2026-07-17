import os
from pathlib import Path
from typing import Literal
from dotenv import load_dotenv

# .env 파일 로드 (Day4 폴더의 상위)
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

from tavily import TavilyClient
from deepagents import create_deep_agent

# Tavily 클라이언트 초기화
tavily_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])


def internet_search(
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news", "finance"] = "general",
    include_raw_content: bool = False,
):
    """Run a web search"""
    return tavily_client.search(
        query,
        max_results=max_results,
        include_raw_content=include_raw_content,
        topic=topic,
    )


# System Prompt 정의
RESEARCH_INSTRUCTIONS = """당신은 전문 연구자입니다. 당신의 임무는 철저한 조사를 수행한 후, 정리된 보고서를 작성하는 것입니다.

인터넷 검색 도구를 주요 정보 수집 수단으로 사용할 수 있습니다.

## Workflow
1. **Plan**: write_todos를 사용하여 연구 과제를 단계별로 나눕니다.
2. **Research**: internet_search를 사용하여 정보를 수집합니다.
3. **Save**: write_file을 사용하여 중요한 정보를 파일에 저장합니다.
4. **Synthesize**: 저장된 파일을 읽고 종합적인 보고서를 작성합니다.

## Best Practices
- 검색 결과를 파일에 저장하여 재검색을 피하세요.
- 파일 시스템을 사용하여 정보를 체계적으로 정리하세요.
- 명확하고 잘 구조화된 보고서를 작성하세요.
- 자료의 출처를 명확히 기록하세요.
"""

# Deep Agent 생성
agent = create_deep_agent(
    model="openai:gpt-5.4-mini",
    tools=[internet_search],
    system_prompt=RESEARCH_INSTRUCTIONS,
)
