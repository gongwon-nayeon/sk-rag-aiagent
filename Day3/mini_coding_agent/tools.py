import os
import subprocess
import json
import glob as glob_module
from typing import Any
from langchain.tools import tool


# ============================================
# 1. 코드 실행 도구 (Python REPL)
# ============================================

@tool
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
                "예: write_file(filepath='../workspace/calculator.py', content=...)\n"
                "   → '파일이 저장되었습니다. 터미널에서 python ../workspace/calculator.py로 실행하세요.'"
            )

    try:
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
        }
        exec_locals = {}

        # stdout 캡처
        import io
        import sys
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()

        try:
            exec(code, exec_globals, exec_locals)
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        if output:
            return f"✅ 실행 성공:\n{output}"
        else:
            return "✅ 실행 성공 (출력 없음)"

    except Exception as e:
        return f"❌ 실행 오류:\n{type(e).__name__}: {str(e)}"


# ============================================
# 2. 파일 시스템 도구
# ============================================

@tool
def read_file(filepath: str) -> str:
    """
    파일의 내용을 읽어서 반환합니다.

    Args:
        filepath: 읽을 파일 경로

    Returns:
        파일 내용 또는 에러 메시지
    """
    try:
        if not os.path.exists(filepath):
            return f"❌ 파일을 찾을 수 없습니다: {filepath}"

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        line_count = len(content.split('\n'))
        return f"✅ 파일 읽기 성공 ({line_count}줄):\n{filepath}\n\n{content}"

    except Exception as e:
        return f"❌ 파일 읽기 오류: {str(e)}"


@tool
def write_file(filepath: str, content: str) -> str:
    """
    파일에 내용을 작성합니다. 기존 파일이 있으면 덮어씁니다.

    Args:
        filepath: 작성할 파일 경로
        content: 파일에 쓸 내용

    Returns:
        성공/실패 메시지
    """
    try:
        # 디렉토리가 없으면 생성
        directory = os.path.dirname(filepath)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        line_count = len(content.split('\n'))
        return f"✅ 파일 작성 성공: {filepath} ({line_count}줄)"

    except Exception as e:
        return f"❌ 파일 작성 오류: {str(e)}"


@tool
def edit_file(filepath: str, old_content: str, new_content: str) -> str:
    """
    파일의 특정 부분을 수정합니다.

    Args:
        filepath: 수정할 파일 경로
        old_content: 찾을 기존 내용
        new_content: 교체할 새 내용

    Returns:
        성공/실패 메시지
    """
    try:
        if not os.path.exists(filepath):
            return f"❌ 파일을 찾을 수 없습니다: {filepath}"

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        if old_content not in content:
            return f"❌ 파일에서 해당 내용을 찾을 수 없습니다"

        new_file_content = content.replace(old_content, new_content, 1)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_file_content)

        return f"✅ 파일 수정 성공: {filepath}"

    except Exception as e:
        return f"❌ 파일 수정 오류: {str(e)}"


@tool
def grep_search(pattern: str, directory: str = ".", file_pattern: str = "*.py") -> str:
    """
    디렉토리에서 패턴을 검색합니다.

    Args:
        pattern: 검색할 패턴 (문자열)
        directory: 검색할 디렉토리 (기본값: 현재 디렉토리)
        file_pattern: 파일 패턴 (기본값: *.py)

    Returns:
        검색 결과
    """
    try:
        results = []
        search_pattern = os.path.join(directory, "**", file_pattern)

        for filepath in glob_module.glob(search_pattern, recursive=True):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        if pattern in line:
                            results.append(f"{filepath}:{line_num}: {line.strip()}")
            except:
                continue

        if results:
            return f"✅ 검색 결과 ({len(results)}건):\n" + "\n".join(results[:20])
        else:
            return f"❌ 검색 결과 없음: '{pattern}'"

    except Exception as e:
        return f"❌ 검색 오류: {str(e)}"


@tool
def glob(pattern: str, directory: str = ".") -> str:
    """
    디렉토리에서 파일 패턴에 맞는 파일들을 찾습니다.

    Args:
        pattern: 파일 패턴 (예: *.py, **/*.md)
        directory: 검색할 디렉토리

    Returns:
        일치하는 파일 목록
    """
    try:
        search_pattern = os.path.join(directory, pattern)
        files = glob_module.glob(search_pattern, recursive=True)

        if files:
            return f"✅ 파일 목록 ({len(files)}개):\n" + "\n".join(files)
        else:
            return f"❌ 일치하는 파일 없음: {pattern}"

    except Exception as e:
        return f"❌ 검색 오류: {str(e)}"


# ============================================
# 3. 테스트 실행 도구 (pytest)
# ============================================

@tool
def run_pytest(test_path: str = ".", args: str = "-v") -> str:
    """
    pytest를 실행하고 결과를 반환합니다.

    Args:
        test_path: 테스트 파일 또는 디렉토리 경로
        args: pytest 추가 인자 (기본값: -v)

    Returns:
        테스트 실행 결과

    Examples:
        run_pytest("tests/")
        run_pytest("test_math.py", "-v -s")
    """
    try:
        cmd = ["pytest", test_path] + args.split()
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        output = result.stdout + result.stderr

        if result.returncode == 0:
            return f"✅ 테스트 통과:\n{output}"
        else:
            return f"❌ 테스트 실패:\n{output}"

    except subprocess.TimeoutExpired:
        return "❌ 테스트 실행 시간 초과 (30초)"
    except FileNotFoundError:
        return "❌ pytest가 설치되어 있지 않습니다. 'pip install pytest'로 설치하세요."
    except Exception as e:
        return f"❌ 테스트 실행 오류: {str(e)}"


@tool
def parse_pytest_results(pytest_output: str) -> str:
    """
    pytest 출력을 파싱하여 요약 정보를 반환합니다.

    Args:
        pytest_output: pytest 실행 결과 문자열

    Returns:
        파싱된 결과 요약
    """
    try:
        lines = pytest_output.split('\n')

        summary = {
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "skipped": 0,
            "failed_tests": []
        }

        for line in lines:
            if " passed" in line:
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == "passed" and i > 0:
                        try:
                            summary["passed"] = int(parts[i-1])
                        except:
                            pass

            if " failed" in line:
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == "failed" and i > 0:
                        try:
                            summary["failed"] = int(parts[i-1])
                        except:
                            pass

            if "FAILED" in line:
                summary["failed_tests"].append(line.strip())

        result = f"""
📊 테스트 결과 요약:
- 통과: {summary['passed']}
- 실패: {summary['failed']}
- 오류: {summary['errors']}
- 건너뜀: {summary['skipped']}
"""

        if summary["failed_tests"]:
            result += f"\n실패한 테스트:\n" + "\n".join(summary["failed_tests"])

        return result

    except Exception as e:
        return f"❌ 결과 파싱 오류: {str(e)}"


# ============================================
# 도구 목록
# ============================================

ALL_TOOLS = [
    # 코드 실행
    execute_python,

    # 파일 시스템
    read_file,
    write_file,
    edit_file,
    grep_search,
    glob,

    # 테스트
    run_pytest,
    parse_pytest_results,
]
