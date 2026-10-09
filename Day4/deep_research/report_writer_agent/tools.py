from pathlib import Path


def save_html_to_disk(
    content: str,
    filename: str,
    output_dir: str | Path = "research_output",
) -> str:
    """HTML 콘텐츠를 디스크에 저장하는 순수 함수 (LLM 도구 호출 없이 직접 사용 가능).

    Args:
        content: 저장할 완전한 HTML 코드
        filename: 저장할 파일명 (확장자 포함, 예: "report.html")
        output_dir: 저장할 디렉토리 경로 (상대 또는 절대 경로)

    Returns:
        저장된 파일의 전체 경로와 성공 메시지, 실패 시 오류 메시지
    """
    try:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        if not filename.endswith(".html"):
            filename = filename.rsplit(".", 1)[0] + ".html"

        file_path = output_path / filename

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return f"파일이 성공적으로 저장되었습니다: {file_path.absolute()}\n파일 크기: {len(content)} bytes"

    except Exception as e:
        return f"파일 저장 중 오류 발생: {str(e)}"
