import httpx
from pathlib import Path
from langchain_core.tools import InjectedToolArg, tool
from markdownify import markdownify # type: ignore
from tavily import TavilyClient # type: ignore
from typing_extensions import Annotated, Literal

tavily_client = TavilyClient()


def fetch_webpage_content(url: str, timeout: float = 10.0) -> str:
    """웹페이지 콘텐츠를 가져와서 마크다운으로 변환합니다.

    Args:
        url: 가져올 URL
        timeout: 요청 제한시간 (초)

    Returns:
        마크다운 형식의 웹페이지 콘텐츠
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = httpx.get(url, headers=headers, timeout=timeout, follow_redirects=True)
        response.raise_for_status()

        content_type = response.headers.get("content-type", "").lower()
        if "html" not in content_type and "text" not in content_type:
            return f"{url}은(는) HTML 페이지가 아닙니다 (Content-Type: {content_type})"

        try:
            html_content = response.text
        except UnicodeDecodeError:
            # 인코딩 실패시 UTF-8로 강제 변환
            html_content = response.content.decode('utf-8', errors='ignore')

        # 마크다운 변환
        markdown_content = markdownify(html_content)
        return markdown_content

    except httpx.HTTPStatusError as e:
        return f"{url} 접근 실패: HTTP {e.response.status_code} 에러"
    except httpx.TimeoutException:
        return f"{url} 요청 시간 초과 (>{timeout}초)"
    except Exception as e:
        return f"{url}에서 콘텐츠를 가져오는 중 오류 발생: {type(e).__name__}: {str(e)}"


@tool(parse_docstring=True)
def tavily_search(
    query: str,
    max_results: Annotated[int, InjectedToolArg] = 3,
    topic: Annotated[
        Literal["general", "news", "finance"], InjectedToolArg
    ] = "general",
) -> str:
    """주어진 쿼리에 대한 웹 정보를 검색합니다.

    Tavily를 사용하여 관련 URL을 찾은 다음, 전체 웹페이지 콘텐츠를 마크다운으로 가져와 반환합니다.

    Args:
        query: 실행할 검색 쿼리
        max_results: 반환할 최대 결과 수 (기본값: 3)
        topic: 주제 필터 - 'general', 'news', 또는 'finance' (기본값: 'general')

    Returns:
        전체 웹페이지 콘텐츠가 포함된 형식화된 검색 결과
    """
    # Tavily를 사용하여 URL 발견
    search_results = tavily_client.search(
        query,
        max_results=max_results,
        topic=topic,
    )

    # 각 URL의 전체 콘텐츠 가져오기
    result_texts = []
    for result in search_results.get("results", []):
        url = result["url"]
        title = result["title"]

        # 웹페이지 콘텐츠 가져오기
        content = fetch_webpage_content(url)

        result_text = f"""## {title}
**URL:** {url}

{content}

---
"""
        result_texts.append(result_text)

    # 최종 응답 형식화
    response = f"""🔍 '{query}'에 대한 {len(result_texts)}개의 결과를 찾았습니다:

{chr(10).join(result_texts)}"""

    return response


@tool(parse_docstring=True)
def think_tool(reflection: str) -> str:
    """리서치 진행 상황과 의사결정에 대한 전략적 성찰 도구.

    각 검색 후 이 도구를 사용하여 결과를 분석하고 다음 단계를 체계적으로 계획하세요.
    이는 품질 높은 의사결정을 위해 리서치 워크플로우에 의도적인 일시 중지를 만듭니다.

    사용 시점:
    - 검색 결과를 받은 후: 어떤 핵심 정보를 찾았는가?
    - 다음 단계를 결정하기 전: 포괄적으로 답변할 충분한 정보가 있는가?
    - 리서치 공백을 평가할 때: 아직 누락된 구체적인 정보는 무엇인가?
    - 리서치를 마무리하기 전: 지금 완전한 답변을 제공할 수 있는가?

    성찰에서 다뤄야 할 사항:
    1. 현재 발견 사항 분석 - 어떤 구체적인 정보를 수집했는가?
    2. 공백 평가 - 아직 누락된 중요한 정보는 무엇인가?
    3. 품질 평가 - 좋은 답변을 위한 충분한 증거/예시가 있는가?
    4. 전략적 결정 - 계속 검색해야 하는가 아니면 답변을 제공해야 하는가?

    Args:
        reflection: 리서치 진행 상황, 발견 사항, 공백 및 다음 단계에 대한 상세한 성찰

    Returns:
        의사결정을 위해 성찰이 기록되었다는 확인
    """
    return f"성찰 기록됨: {reflection}"


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

