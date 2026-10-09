from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / ".env"

load_dotenv(env_path)

from langchain.chat_models import init_chat_model
from deepagents import create_deep_agent # type: ignore
from deepagents.backends import FilesystemBackend

base_dir = Path(__file__).parent

from prompts import RESEARCH_WORKFLOW_INSTRUCTIONS, SUBAGENT_DELEGATION_INSTRUCTIONS
from research_agent import RESEARCHER_INSTRUCTIONS, tavily_search
from report_writer_agent import build_report_writer_subagent

max_concurrent_research_units = 2  # 동시 실행 서브 에이전트 수
max_researcher_iterations = 4      # 최대 반복 횟수

# 현재 날짜 가져오기
current_date = datetime.now().strftime("%Y-%m-%d")

# 오케스트레이터 지시사항 결합 (RESEARCHER_INSTRUCTIONS는 하위 에이전트에만 사용)
INSTRUCTIONS = (
    RESEARCH_WORKFLOW_INSTRUCTIONS
    + "\n\n"
    + "=" * 80
    + "\n\n"
    + SUBAGENT_DELEGATION_INSTRUCTIONS.format(
        max_concurrent_research_units=max_concurrent_research_units,
        max_researcher_iterations=max_researcher_iterations,
    )
)

# 리서치 하위 에이전트 생성
research_sub_agent = {
    "name": "research-agent",
    "description": "하위 에이전트 리서처에게 리서치를 위임합니다. 한 번에 하나의 주제만 제공하세요.",
    "system_prompt": RESEARCHER_INSTRUCTIONS.format(date=current_date),
    "tools": [tavily_search],
}

model = init_chat_model(model="gpt-5.5", temperature=0.0)

report_writer_sub_agent = build_report_writer_subagent(model=model, base_dir=base_dir)

# 에이전트 생성
agent = create_deep_agent(
    model=model,
    tools=[tavily_search],
    system_prompt=INSTRUCTIONS,
    subagents=[research_sub_agent, report_writer_sub_agent],
    backend=FilesystemBackend(root_dir=str(base_dir), virtual_mode=True)
)
