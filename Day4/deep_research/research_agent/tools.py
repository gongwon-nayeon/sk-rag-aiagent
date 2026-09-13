import httpx
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

