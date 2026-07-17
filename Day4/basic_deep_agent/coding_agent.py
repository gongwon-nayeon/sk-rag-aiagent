import io
import sys
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend, CompositeBackend, StateBackend


# ============================================
# Python 코드 실행 도구
# ============================================

def execute_python(code: str) -> str:
    """
    Python 코드를 실행하고 결과를 반환합니다.

    Args:
        code: 실행할 Python 코드 문자열

    Returns:
        실행 결과 또는 에러 메시지

    Examples:
        execute_python("print('Hello World')")
        execute_python("def add(a, b): return a + b\\nprint(add(2, 3))")

    Note:
        input(), raw_input() 등 interactive 함수는 차단됩니다.
        interactive 프로그램은 파일로 저장한 후 별도로 실행하세요.
    """
    # Interactive 함수 체크
    forbidden_patterns = ['input(', 'raw_input(', 'sys.stdin.read']
    for pattern in forbidden_patterns:
        if pattern in code:
            return (
                f"❌ 실행 차단: interactive 함수 감지 ({pattern})\n\n"
                "interactive 입력이 필요한 프로그램은 execute_python으로 실행할 수 없습니다.\n"
                "대신 write_file로 파일을 저장한 후, 사용자가 직접 실행하도록 안내하세요.\n\n"
                "예: write_file(path='/workspace/calculator.py', content=...)\n"
                "   → '파일이 저장되었습니다. 터미널에서 python /workspace/calculator.py로 실행하세요.'"
            )

    try:
        # 필요한 모듈들 import
        import ast
        import math
        import json
        import re

        # 안전한 실행을 위한 제한된 환경
        exec_globals = {
            "__builtins__": __builtins__,
            "print": print,
            "range": range,
            "len": len,
            "str": str,
            "int": int,
            "float": float,
            "list": list,
            "dict": dict,
            "set": set,
            "tuple": tuple,
            "ast": ast,
            "math": math,
            "json": json,
            "re": re,
        }
        exec_locals = {}

        # stdout 캡처
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()

        try:
            exec(code, exec_globals, exec_locals)
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        if output:
            return f"✓ 실행 성공:\n{output}"
        else:
            return "✓ 실행 성공 (출력 없음)"

    except Exception as e:
        return f"❌ 실행 오류:\n{type(e).__name__}: {str(e)}"


# ============================================
# System Prompt: Coding Agent
# ============================================

CODING_AGENT_INSTRUCTIONS = """당신은 코딩을 전문으로 하는 AI 어시스턴트입니다.

## 주요 기능
1. 코드 생성 및 실행
2. 파일 시스템 조작 (읽기, 쓰기, 수정)
3. 테스트 실행 및 결과 분석
4. 작업 계획 수립 및 추적

## 사용 가능한 도구

### 1. execute_python
- Python 코드를 즉시 실행하고 결과를 확인합니다
- 간단한 테스트, 계산, 검증용으로 사용하세요
- 사용 가능한 모듈: ast, math, json, re 등 기본 라이브러리
- **주의**: input() 같은 interactive 함수는 사용 불가

### 2. File System (실제 디스크 연결) ✅
- `write_file(path, content)`: 파일 생성/덮어쓰기
- `read_file(path)`: 파일 내용 읽기
- `edit_file(path, old_str, new_str)`: 파일 일부 수정
- `ls(path)`: 디렉토리 내용 조회

**✅ 실제 파일 시스템 특성:**
- `/workspace/`에 저장한 파일은 **실제 디스크에 생성됩니다**
- 파일이 영구적으로 보존됩니다
- 사용자가 직접 파일을 확인하고 실행할 수 있습니다
- 작업 공간: `basic_deep_agent/workspace/` 디렉터리

**파일 생성 시 알려야 할 사항:**
1. 생성한 파일 경로 (예: `/workspace/calculator.py`)
2. 파일이 실제 디스크에 저장되었음을 안내
3. 실행 방법 안내 (예: `python basic_deep_agent/workspace/calculator.py`)

### 3. TODO Planning (내장)
- `write_todos(todos)`: 작업 계획 수립
- 복잡한 작업을 단계별로 나누어 관리

## 작업 흐름

### 코드 작성 작업
1. **Plan**: write_todos로 작업을 단계별로 나눕니다
2. **Write**: write_file로 코드를 `/workspace/`에 저장합니다
3. **Test**: execute_python으로 간단한 로직을 테스트합니다
4. **Verify**: 파일이 실제로 생성되었는지 확인합니다 (ls 사용)
5. **Guide**: 사용자에게 실행 방법을 안내합니다

### Interactive 프로그램 처리
- input(), raw_input() 등 사용자 입력이 필요한 프로그램:
  1. write_file로 `/workspace/`에 파일 저장
  2. 파일이 생성되었음을 확인 (실제 경로 표시)
  3. 사용자에게 터미널에서 실행하도록 안내

## 파일 경로 규칙
- 모든 파일은 `/workspace/` 디렉토리에 저장
- 실제 경로: `basic_deep_agent/workspace/`
- 예: `/workspace/example.py` → `basic_deep_agent/workspace/example.py`

## Best Practices
1. 코드 작성 전 항상 계획을 수립하세요 (write_todos)
2. 작은 단위로 테스트하며 진행하세요 (execute_python)
3. 파일 생성 후 ls로 확인하세요
4. 최종 코드와 실행 방법을 명확히 안내하세요
5. 코드에 주석과 docstring을 포함하세요

## 응답 형식
- 명확하고 구조화된 답변을 제공하세요
- 실행한 작업과 결과를 단계별로 설명하세요
- 파일이 실제 디스크에 생성되었음을 강조하세요
- 터미널에서의 실행 명령을 제공하세요
"""


# ============================================
# Deep Agent 생성
# ============================================

# workspace 디렉터리의 절대 경로
workspace_dir = Path(__file__).parent / "workspace"
workspace_dir.mkdir(exist_ok=True)  # 디렉터리가 없으면 생성

agent = create_deep_agent(
    model="openai:gpt-5.4-mini",
    tools=[execute_python],
    system_prompt=CODING_AGENT_INSTRUCTIONS,
    backend=CompositeBackend(
        default=StateBackend(),  # Agent 내부 데이터는 메모리에 저장
        routes={
            # /workspace/ 경로는 실제 디스크에 저장
            "/workspace/": FilesystemBackend(
                root_dir=str(workspace_dir.absolute()),
                virtual_mode=True,  # 안전한 경로 제한 활성화
            ),
        },
    ),
)
