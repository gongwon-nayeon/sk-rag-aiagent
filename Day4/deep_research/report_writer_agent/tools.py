from pathlib import Path
from langchain_core.tools import tool


@tool(parse_docstring=True)
def save_html_to_local(
    content: str,
    filename: str,
    output_dir: str = "research_output",
) -> str:
    """HTML 파일을 로컬 디렉토리에 저장합니다.

    이 도구는 에이전트가 생성한 완전한 HTML 코드를 받아서 그대로 파일로 저장합니다.

    **중요: 보고서 본문은 반드시 자연스러운 한국어로 작성합니다. 번역체 표현은 사용하지 않습니다.**

    **사용 워크플로우:**
    1. read_file로 /final_report.md 읽기 (한글로 작성된 보고서)
    2. 읽은 Markdown 내용을 바탕으로 완전한 HTML 생성 (<!DOCTYPE html>부터 </html>까지)
       - HTML 구조, 스타일, 스크립트, 차트 등 모든 것을 직접 작성
       - Markdown을 HTML로 변환하고 모던한 CSS 스타일 적용
       - 필요시 Chart.js, Plotly 등 라이브러리 포함
    3. save_html_to_local(content=생성한HTML, filename="final_report.html") 호출
    4. 생성한 HTML이 research_output/ 디렉토리에 저장됨

    **예시:**
    ```python
    # 1. 보고서 읽기
    report_content = read_file("/final_report.md")

    # 2. 완전한 HTML 생성 (한글 콘텐츠)
    html = '''<!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <title>딥 에이전트 리서치 보고서</title>
        <style>
            body { font-family: -apple-system, sans-serif; max-width: 900px; margin: 0 auto; padding: 40px; }
            h1 { color: #2563eb; border-bottom: 3px solid #2563eb; padding-bottom: 0.3em; }
            h2 { color: #0f172a; margin-top: 1.5em; border-bottom: 2px solid #e2e8f0; }
        </style>
    </head>
    <body>
        <h1>LangChain 딥 에이전트 개요</h1>
        <h2>주요 기능</h2>
        <p>딥 에이전트는 복잡한 멀티스텝 작업을 처리하는 자율 에이전트입니다 [1].</p>
        <h2>출처</h2>
        <p>[1] LangChain 문서: https://example.com</p>
    </body>
    </html>'''

    # 3. 저장
    save_html_to_local(content=html, filename="final_report.html")
    ```

    Args:
        content: 저장할 완전한 HTML 코드 (에이전트가 직접 생성한 HTML)
        filename: 저장할 파일명 (확장자 포함, 예: "report.html")
        output_dir: 저장할 디렉토리 경로 (기본값: "research_output")

    Returns:
        저장된 파일의 전체 경로와 성공 메시지
    """
    try:
        # 출력 디렉토리 생성
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 파일 확장자 확인 및 조정
        if not filename.endswith(".html"):
            filename = filename.rsplit(".", 1)[0] + ".html"

        # 전체 파일 경로
        file_path = output_path / filename

        # 받은 HTML을 그대로 저장
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return f"파일이 성공적으로 저장되었습니다: {file_path.absolute()}\n파일 크기: {len(content)} bytes"

    except Exception as e:
        return f"파일 저장 중 오류 발생: {str(e)}"
