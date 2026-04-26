"""딥 리서치 에이전트 예제.

이 모듈은 웹 검색과 전략적 사고를 위한 커스텀 도구를 사용하여
deepagents 패키지로 리서치 에이전트를 구축하는 방법을 시연합니다.
"""

from research_agent.prompts import (
    RESEARCHER_INSTRUCTIONS,
    RESEARCH_WORKFLOW_INSTRUCTIONS,
    SUBAGENT_DELEGATION_INSTRUCTIONS,
)
from research_agent.tools import tavily_search, think_tool

__all__ = [
    "tavily_search",
    "think_tool",
    "RESEARCHER_INSTRUCTIONS",
    "RESEARCH_WORKFLOW_INSTRUCTIONS",
    "SUBAGENT_DELEGATION_INSTRUCTIONS",
]
