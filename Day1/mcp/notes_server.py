from mcp.server.fastmcp import FastMCP   # type: ignore
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

mcp = FastMCP("NotesManager")

# 노트 저장 경로
NOTES_DIR = Path("notes_data")
NOTES_FILE = NOTES_DIR / "notes.json"


def ensure_notes_file():
    """노트 파일이 없으면 생성"""
    NOTES_DIR.mkdir(exist_ok=True)
    if not NOTES_FILE.exists():
        with open(NOTES_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)


def load_notes() -> list:
    """모든 노트 불러오기"""
    ensure_notes_file()
    with open(NOTES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_notes(notes: list):
    """노트 저장하기"""
    with open(NOTES_FILE, "w", encoding="utf-8") as f:
        json.dump(notes, f, ensure_ascii=False, indent=2)


@mcp.tool()
def create_note(title: str, content: str, tags: Optional[List[str]] = None) -> dict:
    """
    새로운 노트를 생성합니다.

    Args:
        title (str): 노트 제목 (내용과 어울리는 간결한 제목)
        content (str): 노트 내용
        tags (Optional[List[str]]): 태그 리스트 (예: ["업무", "아이디어"], 입력이 없으면 기본값으로 ["기본"] 저장)

    Returns:
        dict: 생성된 노트 정보 (id, title, created_at 포함)
    """
    notes = load_notes()

    note_id = str(len(notes) + 1)
    new_note = {
        "id": note_id,
        "title": title,
        "content": content,
        "tags": tags or ["기본"],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }

    notes.append(new_note)
    save_notes(notes)

    return {
        "id": note_id,
        "title": title,
        "message": f"노트 '{title}'가 생성되었습니다.",
        "created_at": new_note["created_at"]
    }


@mcp.tool()
def get_note(note_id: str) -> dict:
    """
    특정 노트의 전체 내용을 조회합니다.

    Args:
        note_id (str): 노트 ID

    Returns:
        dict: 노트의 모든 정보
    """
    notes = load_notes()

    for note in notes:
        if note["id"] == note_id:
            return note

    raise ValueError(f"노트 ID '{note_id}'를 찾을 수 없습니다.")


@mcp.tool()
def list_notes(tag: Optional[str] = None, limit: int = 10) -> list:
    """
    모든 노트의 목록을 조회합니다.

    Args:
        tag (Optional[str]): 특정 태그로 필터링 (예: "업무")
        limit (int): 반환할 최대 노트 개수 (기본값: 10)

    Returns:
        list: 노트 목록 (id, title, tags, created_at만 포함)
    """
    notes = load_notes()

    # 태그로 필터링
    if tag:
        notes = [n for n in notes if tag in n.get("tags", [])]

    # 최신 순으로 정렬
    notes.sort(key=lambda x: x["created_at"], reverse=True)

    # 간단한 정보만 반환
    result = []
    for note in notes[:limit]:
        result.append({
            "id": note["id"],
            "title": note["title"],
            "tags": note.get("tags", []),
            "created_at": note["created_at"],
            "preview": note["content"][:50] + "..." if len(note["content"]) > 50 else note["content"]
        })

    return result


@mcp.tool()
def search_notes(keyword: str) -> list:
    """
    제목이나 내용에서 키워드를 검색합니다.

    Args:
        keyword (str): 검색할 키워드

    Returns:
        list: 검색된 노트 목록
    """
    notes = load_notes()
    keyword_lower = keyword.lower()

    results = []
    for note in notes:
        title_match = keyword_lower in note["title"].lower()
        content_match = keyword_lower in note["content"].lower()

        if title_match or content_match:
            results.append({
                "id": note["id"],
                "title": note["title"],
                "tags": note.get("tags", []),
                "match_type": "제목" if title_match else "내용",
                "preview": note["content"][:100] + "..." if len(note["content"]) > 100 else note["content"]
            })

    return results


@mcp.tool()
def update_note(note_id: str, title: Optional[str] = None,
                content: Optional[str] = None, tags: Optional[List[str]] = None) -> dict:
    """
    기존 노트를 수정합니다.

    Args:
        note_id (str): 수정할 노트 ID
        title (Optional[str]): 새 제목 (변경하지 않으려면 None)
        content (Optional[str]): 새 내용 (변경하지 않으려면 None)
        tags (Optional[List[str]]): 새 태그 리스트 (변경하지 않으려면 None)

    Returns:
        dict: 수정된 노트 정보
    """
    notes = load_notes()

    for note in notes:
        if note["id"] == note_id:
            if title is not None:
                note["title"] = title
            if content is not None:
                note["content"] = content
            if tags is not None:
                note["tags"] = tags

            note["updated_at"] = datetime.now().isoformat()
            save_notes(notes)

            return {
                "id": note_id,
                "title": note["title"],
                "message": f"노트가 수정되었습니다.",
                "updated_at": note["updated_at"]
            }

    raise ValueError(f"노트 ID '{note_id}'를 찾을 수 없습니다.")


@mcp.tool()
def delete_note(note_id: str) -> dict:
    """
    노트를 삭제합니다.

    Args:
        note_id (str): 삭제할 노트 ID

    Returns:
        dict: 삭제 결과 메시지
    """
    notes = load_notes()

    for i, note in enumerate(notes):
        if note["id"] == note_id:
            deleted_title = note["title"]
            notes.pop(i)
            save_notes(notes)

            return {
                "message": f"노트 '{deleted_title}'가 삭제되었습니다.",
                "deleted_id": note_id
            }

    raise ValueError(f"노트 ID '{note_id}'를 찾을 수 없습니다.")


@mcp.tool()
def list_all_tags() -> dict:
    """
    모든 노트에서 사용된 태그 목록을 조회합니다.

    Returns:
        dict: 태그와 각 태그의 사용 횟수
    """
    notes = load_notes()

    tag_counts = {}
    for note in notes:
        for tag in note.get("tags", []):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    return {
        "total_tags": len(tag_counts),
        "tags": tag_counts
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
