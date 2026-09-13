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

## 파일 경로 규칙
- 모든 파일은 `/workspace/` 디렉토리에 저장
- 실제 경로: `basic_deep_agent/workspace/`
- 예: `/workspace/example.py` → `basic_deep_agent/workspace/example.py`
"""


# ============================================
# Deep Agent 생성
# ============================================

# workspace 디렉터리의 절대 경로
workspace_dir = Path(__file__).parent / "workspace"
workspace_dir.mkdir(exist_ok=True)  # 디렉터리가 없으면 생성

agent = create_deep_agent(
    model="openai:gpt-5.5",
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
