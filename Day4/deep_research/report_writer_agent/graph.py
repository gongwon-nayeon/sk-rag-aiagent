from __future__ import annotations

import re
from pathlib import Path
from typing import Annotated, TypedDict

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

from deepagents import CompiledSubAgent  # type: ignore

from report_writer_agent.prompts import REPORT_WRITER_INSTRUCTIONS
from report_writer_agent.tools import save_html_to_disk

REPORT_MD_FILENAME = "final_report.md"
REPORT_HTML_FILENAME = "final_report.html"
REPORT_OUTPUT_DIR = "research_output"


class ReportWriterState(TypedDict):
    """compiled graph의 상태. `messages`는 task() 도구와 결과를 주고받기 위해 필수."""

    messages: Annotated[list[AnyMessage], add_messages]
    report_markdown: str
    report_html: str
    error: str | None


def _strip_code_fence(text: str) -> str:
    """모델이 ```html ... ``` 로 감싸서 응답한 경우 코드 펜스를 제거합니다."""
    stripped = text.strip()
    match = re.match(r"^```(?:html)?\s*\n(.*)\n```$", stripped, re.DOTALL)
    return match.group(1).strip() if match else stripped


def build_report_writer_subagent(
    model: BaseChatModel,
    base_dir: Path,
) -> CompiledSubAgent:
    """report-writer를 단방향 compiled graph 서브 에이전트로 빌드합니다.

    Args:
        model: HTML 생성에 사용할 채팅 모델 (오케스트레이터와 동일 모델 재사용 권장)
        base_dir: 오케스트레이터의 FilesystemBackend `root_dir`과 동일한 경로.
            `/final_report.md`가 이 디렉토리에 실제로 저장되어 있다고 가정합니다.

    Returns:
        `create_deep_agent(subagents=[...])`에 바로 전달 가능한 CompiledSubAgent
    """
    report_md_path = base_dir / REPORT_MD_FILENAME
    output_dir = base_dir / REPORT_OUTPUT_DIR

    def read_report(state: ReportWriterState) -> dict:
        try:
            markdown = report_md_path.read_text(encoding="utf-8")
        except OSError as exc:
            return {"error": f"'{report_md_path}' 파일을 읽을 수 없습니다: {exc}"}
        return {"report_markdown": markdown}

    def route_after_read(state: ReportWriterState) -> str:
        return "handle_error" if state.get("error") else "generate_html"

    def generate_html(state: ReportWriterState) -> dict:
        try:
            response = model.invoke(
                [
                    SystemMessage(content=REPORT_WRITER_INSTRUCTIONS),
                    HumanMessage(content=state["report_markdown"]),
                ]
            )
        except Exception as exc:  # noqa: BLE001 - surface any model error to the orchestrator
            return {"error": f"HTML 생성 중 모델 호출 오류: {exc}"}
        html = _strip_code_fence(response.text or "")
        if not html:
            return {"error": "모델이 빈 HTML 응답을 반환했습니다."}
        return {"report_html": html}

    def route_after_generate(state: ReportWriterState) -> str:
        return "handle_error" if state.get("error") else "save_html"

    def save_html(state: ReportWriterState) -> dict:
        result = save_html_to_disk(
            content=state["report_html"],
            filename=REPORT_HTML_FILENAME,
            output_dir=output_dir,
        )
        return {"messages": [AIMessage(content=result)]}

    def handle_error(state: ReportWriterState) -> dict:
        return {"messages": [AIMessage(content=f"HTML 저장 실패: {state.get('error')}")]}

    graph = StateGraph(ReportWriterState)
    graph.add_node("read_report", read_report)
    graph.add_node("generate_html", generate_html)
    graph.add_node("save_html", save_html)
    graph.add_node("handle_error", handle_error)

    graph.add_edge(START, "read_report")
    graph.add_conditional_edges(
        "read_report", route_after_read, ["generate_html", "handle_error"]
    )
    graph.add_conditional_edges(
        "generate_html", route_after_generate, ["save_html", "handle_error"]
    )
    graph.add_edge("save_html", END)
    graph.add_edge("handle_error", END)

    compiled = graph.compile()

    return CompiledSubAgent(
        name="report-writer",
        description="완성된 `/final_report.md`를 HTML로 변환하여 저장합니다. 리서치나 내용 작성 없이 형식 변환과 저장만 담당합니다.",
        runnable=compiled,
    )


def save_graph_visualization(
    compiled_graph: StateGraph,
    output_path: Path | None = None,
) -> Path:
    """compiled graph 구조를 Mermaid PNG로 렌더링해 로컬에 저장합니다.

    Jupyter의 `display(Image(graph.get_graph().draw_mermaid_png()))`와 동일한
    렌더링 결과를 파일로 저장하는 스크립트 환경용 버전입니다.

    Args:
        compiled_graph: `StateGraph.compile()`로 생성된 컴파일된 그래프
        output_path: 저장할 PNG 경로 (기본값: 이 파일과 같은 폴더의 `graph.png`)

    Returns:
        저장된 PNG 파일의 경로
    """
    if output_path is None:
        output_path = Path(__file__).parent / "graph.png"

    png_bytes = compiled_graph.get_graph().draw_mermaid_png()
    output_path.write_bytes(png_bytes)
    return output_path


if __name__ == "__main__":
    from dotenv import load_dotenv

    env_path = Path(__file__).parent.parent.parent / ".env"
    load_dotenv(env_path)

    from langchain.chat_models import init_chat_model

    _model = init_chat_model(model="gpt-5.5", temperature=0.0)
    _base_dir = Path(__file__).parent.parent
    _subagent = build_report_writer_subagent(model=_model, base_dir=_base_dir)
    _compiled_graph = _subagent["runnable"]

    saved_path = save_graph_visualization(_compiled_graph)
    print(f"그래프 다이어그램을 저장했습니다: {saved_path}")

