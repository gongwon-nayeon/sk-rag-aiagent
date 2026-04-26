# SK RAG AI Agent 4일 과정 - Day 1

1일차에서는 LangChain과 LangGraph의 기초를 학습하고, 간단한 LLM 챗봇을 구현합니다.

### 커리큘럼

1. **LangChain 소개**
2. **[실습] LangChain 기반 LLM 사용하기** - `01_langchain_llm_basics.ipynb`
3. **LangGraph 소개**
4. **[실습] LangGraph 기초 사용법** - `02_langgraph_essentials.ipynb`
5. **[실습] LangGraph 메시지 관리 그래프** - `03_langgraph_messages_state.ipynb`
6. **[실습] LangGraph 노드·엣지 연결 / 조건부 엣지** - `04_langgraph_nodes_edges.ipynb`
7. **AI Agent와 도구 호출 기반 에이전트**
8. **[실습] 도구 기반 에이전트 그래프** - `05_langgraph_tools_chatbot.ipynb`
9. **MCP(Model Context Protocol) 개념과 활용**
10. **[실습] MCP 기반 agent 구현하기** - `mcp/`


| 시간 | 내용 | 유형 | 실습 코드 파일 | 세부 구성 |
|------|------|------|----------------|-----------|
| 09:00–09:30 | 오리엔테이션 & LangChain 소개 | 이론 | - | - 생성형 AI / LLM 애플리케이션의 이해|
| 09:30–10:10 | [실습] LangChain 기반 LLM 사용하기 | 실습 | `01_langchain_llm_basics.ipynb` | - 환경 변수 설정 (OpenAI API Key)<br>- Chat Models 사용법 (init_chat_model, ChatOpenAI)<br>- 메시지 타입 이해 (System, Human, AI, Tool)<br>- 텍스트 vs 메시지 프롬프트<br>- 스트리밍 응답 구현<br>- 멀티턴 대화 구현 |
| 10:10–10:20 | ☕ Break |  | - |  |
| 10:20–10:50 | LangGraph 소개 | 이론 | - | - 왜 LangGraph인가? (AI Agent, Agentic Workflow)<br>- State 기반 흐름 제어<br>- Node / Edge 개념<br>- LangGraph의 장점 |
| 10:50–12:00 | [실습] LangGraph 기초 사용법 | 실습 | `02_langgraph_essentials.ipynb` | - LangGraph 핵심 구성 요소<br>- TypedDict 기본 사용법<br>- Pydantic BaseModel 이해<br>- TypedDict vs Pydantic 비교<br>- State 스키마 정의 (Input, Output)<br>- 노드 함수 정의<br>- StateGraph 빌더로 그래프 구성<br>- 그래프 컴파일 및 실행 |
| 12:00–13:00 | 🍱 Lunch |  | - |  |
| 13:00–13:40 | [실습] LangGraph 메시지 관리 그래프 | 실습 | `03_langgraph_messages_state.ipynb` | - 메시지 상태 수동 관리<br>- add_messages 리듀서 개념<br>- Annotated로 리듀서 지정<br>- LLM 기반 챗봇 그래프 구현<br>- 메시지 자동 누적 및 업데이트<br>- 스트리밍 응답 처리 |
| 13:40–14:30 | [실습] LangGraph 노드·엣지 연결 / 조건부 엣지 | 실습 | `04_langgraph_nodes_edges.ipynb` | - 순차 노드 연결 (다단계 워크플로우)<br>- 다중 노드 간 상태 전달<br>- 조건부 엣지 (add_conditional_edges)<br>- 상태 기반 분기 처리<br>- 다단계 번역 시스템 실습<br>- 감정 기반 응답 시스템 실습 |
| 14:30–14:40 | ☕ Break |  | - |  |
| 14:40–15:00 | AI Agent와 도구 호출 기반 에이전트 | 이론 | - | - AI Agent란 무엇인가?<br>- Function Calling / Tool Calling 개념<br>- ReAct 패턴 (Reasoning + Acting)<br>- Agent 실행 루프 |
| 15:00–15:40 | [실습] 도구 기반 에이전트 그래프 | 실습 | `05_langgraph_tools_chatbot.ipynb` | - Tool 개념과 특징<br>- @tool 데코레이터로 도구 정의<br>- bind_tools로 LLM에 도구 바인딩<br>- LLM의 Tool 호출 확인<br>- State 정의 (MessagesState)<br>- Agent 노드 구현 (LLM 호출)<br>- ToolNode로 도구 실행<br>- 조건부 종료 로직 (should_continue)<br>- ReAct 패턴 Agent 루프 구현 |
| 15:40–15:50 | ☕ Break |  | - |  |
| 15:50–16:10 | MCP 개념과 활용 | 이론 | - | - MCP(Model Context Protocol)란?<br>- Client-Server 구조<br>- LLM과 외부 데이터 연결<br>- 실제 사용 예시 |
| 16:10–17:00 | [실습] MCP 기반 agent 구현하기 | 실습 | `mcp/` | - MCP 서버 이해 (notes_server.py)<br>- 로컬 MCP 서버 연결 (메모 관리)<br>- 원격 MCP 서버 연결 (LangChain 문서 검색)<br>- MCP Tools를 Agent에 통합<br>- MCP 기반 Agent 그래프 구현 |




## 실습 환경 설정

### 사전 요구사항

- Python 3.11 이상
- OpenAI API Key (https://platform.openai.com/api-keys)

### 1. uv 설치

#### Windows (PowerShell)

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

#### macOS / Linux

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

설치 후 터미널을 재시작하거나 다음 명령으로 PATH를 업데이트하세요.

---

### 2. 가상환경 생성 및 패키지 설치

Day1 폴더로 이동한 후 아래 방법 중 하나를 선택하세요.

#### 방법 1: uv sync 사용 (권장)

```bash
# Day1 폴더로 이동
cd Day1

# pyproject.toml을 기반으로 가상환경 생성 및 패키지 설치
uv sync

# 가상환경 활성화 (Windows)
.venv\Scripts\activate

# 가상환경 활성화 (macOS/Linux)
source .venv/bin/activate
```

#### 방법 2: requirements.txt 사용

```bash
# 가상환경 생성
uv venv

# 가상환경 활성화 (Windows)
.venv\Scripts\activate

# 가상환경 활성화 (macOS/Linux)
source .venv/bin/activate

# 패키지 설치
uv pip install -r requirements.txt
```

---

### 3-A. Jupyter Notebook 커널 등록 (VS Code 사용 시)

VS Code에서 Jupyter Notebook을 사용하려면 커널을 등록해야 합니다.

#### Windows

```powershell
.venv\Scripts\python.exe -m ipykernel install --user --name=llm-day1 --display-name="llm Day1"
```

#### macOS/Linux

```bash
.venv/bin/python -m ipykernel install --user --name=llm-day1 --display-name="llm Day1"
```

커널 등록 후 **VS Code를 리로드**하면 노트북에서 "llm Day1" 커널을 선택할 수 있습니다.

---

### 3-B. Jupyter Notebook 웹 인터페이스 사용

웹 브라우저에서 Jupyter Notebook을 사용하려면 다음 명령어를 실행하세요.

#### Jupyter Notebook

```bash
jupyter notebook
```

#### Jupyter Lab

```bash
jupyter lab
```

명령어 실행 후 자동으로 브라우저가 열리며, 수동으로 열려면 터미널에 표시된 URL을 복사하여 브라우저에 붙여넣으세요.

예: `http://localhost:8888/?token=...`

---

### 4. 환경변수 설정

`.env.example` 파일을 `.env`로 복사하고 본인의 API 키를 입력하세요.

#### Windows

```bash
copy .env.example .env
```

#### macOS/Linux

```bash
cp .env.example .env
```

`.env` 파일을 열고 다음과 같이 수정:

```
OPENAI_API_KEY=your_openai_api_key_here
```