from typing import Any, Callable
from langchain.agents.middleware import (
    TodoListMiddleware,
    SummarizationMiddleware,
    ModelRequest,
    ModelResponse,
    wrap_model_call,
    after_model,
    AgentState,
)
from langchain_openai import ChatOpenAI
from langgraph.runtime import Runtime


# ============================================
# 1. Model Routing Middleware (커스텀)
# ============================================

# 모델 인스턴스를 모듈 레벨에서 한 번만 생성 (매 호출마다 생성 방지)
_PLANNING_MODEL = ChatOpenAI(model="gpt-4o", temperature=0)
_EXECUTION_MODEL = ChatOpenAI(model="gpt-4o-mini", temperature=0)

_PLANNING_KEYWORDS = [
    "write_todos",
    "계획",
    "단계",
    "전략",
    "분석",
    "설계",
    "구조",
]


@wrap_model_call
async def model_routing_middleware(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse],
) -> ModelResponse:
    """
    작업 유형에 따라 적절한 모델을 선택합니다.

    - Planning (todo 작성, 계획 수립) → gpt-4o
    - Execution (도구 호출, 코드 실행) → gpt-4o-mini

    Args:
        request: 모델 요청
        handler: 실제 모델 호출 핸들러

    Returns:
        모델 응답
    """
    # 메시지에서 planning 관련 키워드 확인
    messages = request.messages if hasattr(request, 'messages') else []

    is_planning = False
    if messages:
        last_message = messages[-1]
        content = ""

        if isinstance(last_message, dict):
            content = last_message.get("content", "")
        elif hasattr(last_message, "content"):
            content = last_message.content

        is_planning = any(
            keyword in str(content).lower() for keyword in _PLANNING_KEYWORDS
        )

    if is_planning:
        print(f"[Model Routing] Planning 감지 → gpt-4o 사용")
        modified_request = request.override(model=_PLANNING_MODEL)
    else:
        print(f"[Model Routing] Execution → gpt-4o-mini 사용")
        modified_request = request.override(model=_EXECUTION_MODEL)

    return await handler(modified_request)


# ============================================
# 2. Lint Checker Middleware (커스텀)
# ============================================

@after_model
async def lint_checker_middleware(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    """
    write_file 도구 호출 시 코드를 lint 체크하고 오류가 있으면 차단합니다.

    write_file 도구가 Python 파일을 생성하려고 할 때:
    1. Python 구문 오류 체크
    2. 간단한 lint 규칙 체크 (PEP 8 일부)
    3. 오류 발견 시 ToolMessage 에러를 반환하여 도구 호출 차단

    Args:
        state: 에이전트 상태
        runtime: 런타임 객체

    Returns:
        오류가 있는 write_file 호출에 대한 ToolMessage 목록, 없으면 None
    """
    from langchain_core.messages import AIMessage, ToolMessage

    messages = state.get("messages", [])
    if not messages:
        return None

    # 마지막 AI 메시지 찾기
    last_ai_msg = next((msg for msg in reversed(messages) if isinstance(msg, AIMessage)), None)
    if not last_ai_msg or not last_ai_msg.tool_calls:
        return None

    # write_file 도구 호출 찾기
    write_file_calls = [
        tc for tc in last_ai_msg.tool_calls
        if tc.get("name") == "write_file"
    ]

    if not write_file_calls:
        return None

    print(f"\n🔍 [Lint Checker] write_file 호출 {len(write_file_calls)}개 발견 - lint 검사 시작")

    error_tool_messages = []

    for tool_call in write_file_calls:
        args = tool_call.get("args", {})
        # write_file 도구의 파라미터명은 "filepath" ("file_path" 아님)
        file_path = args.get("filepath", "")
        content = args.get("content", "")

        # Python 파일만 체크
        if not file_path.endswith('.py'):
            continue

        print(f"  → {file_path} 검사 중...")

        errors = []

        # 1. 구문 오류 체크
        try:
            compile(content, file_path, "exec")
        except SyntaxError as e:
            errors.append(f"구문 오류: {e.msg} at line {e.lineno}")

        # 2. 간단한 lint 규칙 체크
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            # PEP 8: 한 줄 길이 제한
            if len(line) > 120:  # 너무 엄격하지 않게 120자로 설정
                errors.append(f"라인 {line_num}: 길이 초과 ({len(line)}자 > 120자)")

            # 들여쓰기 체크 (탭 사용 금지)
            if '\t' in line:
                errors.append(f"라인 {line_num}: 탭 문자 사용 (스페이스 4개를 사용하세요)")

        # 오류가 있으면 ToolMessage 에러 생성
        if errors:
            error_message = f"⚠️ Lint 오류 발견 ({file_path}):\n"
            error_message += "\n".join(f"- {err}" for err in errors[:5])

            if len(errors) > 5:
                error_message += f"\n... 외 {len(errors) - 5}개 오류"

            error_message += "\n\n💡 코드를 수정한 후 다시 시도하세요."

            print(f"    ❌ 오류 {len(errors)}개 발견 - 도구 호출 차단")

            error_tool_messages.append(
                ToolMessage(
                    content=error_message,
                    tool_call_id=tool_call["id"],
                    status="error",
                )
            )
        else:
            print(f"    ✅ 오류 없음")

    # 오류가 있는 도구 호출이 있으면 ToolMessage 반환
    if error_tool_messages:
        print(f"\n⚠️ [Lint Checker] {len(error_tool_messages)}개 파일에서 오류 발견 - 도구 호출 차단됨")
        return {"messages": error_tool_messages}

    print("[Lint Checker] 모든 파일 검사 완료")
    return None


# ============================================
# 3. Tool Call Logging Middleware
# ============================================

@after_model
async def tool_call_logger(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    """
    도구 호출을 로깅합니다.

    Args:
        state: 에이전트 상태
        runtime: 런타임 객체

    Returns:
        None (상태 변경 없음)
    """
    messages = state.get("messages", [])
    if not messages:
        return None

    last_message = messages[-1]

    # 도구 호출 확인
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        for tool_call in last_message.tool_calls:
            tool_name = tool_call.get("name", "unknown")
            tool_args = tool_call.get("args", {})
            print(f"🔧 [Tool Call] {tool_name}({', '.join(f'{k}={v}' for k, v in list(tool_args.items())[:2])}...)")

    return None


# ============================================
# 미들웨어 목록 (graph.py에서 사용)
# ============================================

def create_middleware_stack():
    """
    코딩 에이전트에 필요한 모든 미들웨어를 생성합니다.

    Returns:
        미들웨어 리스트
    """
    return [
        # 1. Planning Middleware
        TodoListMiddleware(),

        # 2. Model Routing (커스텀)
        # planning은 gpt-4o, execution은 gpt-4o-mini
        model_routing_middleware,

        # 3. Summarization Middleware
        SummarizationMiddleware(
            model="gpt-4o-mini",
            trigger=("messages", 20),
            keep=("messages", 8),
        ),

        # 4. Lint Checker (커스텀)
        # 코드 생성 후 자동으로 lint 오류 확인
        lint_checker_middleware,

        # 5. Tool Call Logger (유틸리티)
        # 도구 호출 로깅
        tool_call_logger,
    ]
