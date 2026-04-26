# SK RAG AI Agent 4일 과정 - Day 2

2일차에서는 RAG(Retrieval-Augmented Generation)의 기본 개념부터 시작하여 Agentic RAG를 구현합니다.

### 커리큘럼

1. **RAG 이해하기**
2. **[실습] ChromaDB로 만드는 기본 RAG** - `01_basic_rag_chromadb.ipynb`
3. **[실습] ChromaDB로 만드는 기본 RAG - 랭그래프 스튜디오 사용** - `01_basic_rag_chromadb`
4. **Agentic RAG 개념 및 기능**
5. **[실습] 검색 문서의 관련성 검증을 추가한 RAG** - `02_relevance_grading_rag`
6. **[실습] 환각 여부를 평가하는 Agentic RAG** - `03_hallucination_grading_rag`
7. **[실습] 질문 의도를 분류하는 Agentic RAG** - `04_agentic_rag_websearch`

| 시간 | 내용 | 유형 | 실습 코드 파일 | 세부 구성 |
|------|------|------|----------------|-----------|
| 09:00–09:30 | RAG 이해하기 | 이론 | - | - RAG의 개념과 필요성<br>- 벡터 데이터베이스<br>- 문서 분할 및 임베딩<br>- 검색 및 생성 과정 |
| 09:30–10:20 | [실습] ChromaDB로 만드는 기본 RAG | 실습 | `01_basic_rag_chromadb.ipynb` | - 문서 로딩 (PDF)<br>- RecursiveCharacterTextSplitter<br>- ChromaDB 벡터스토어 구축<br>- 임베딩 및 유사도 검색<br>- RAG 체인 구성 및 테스트 |
| 10:20–10:30 | ☕ Break |  | - |  |
| 10:30–11:30 | [실습] ChromaDB로 만드는 기본 RAG | 실습 | `01_basic_rag_chromadb` | - 랭그래프 스튜디오 사용 |
| 11:30–11:50 | Agentic RAG 개념 및 기능 | 이론 | - | - Agentic RAG란?<br>- LangGraph 기반 워크플로우<br>- 관련성 평가 노드<br>- 환각 평가 노드<br>- 쿼리 재작성 모듈 |
| 12:00–13:00 | 🍱 Lunch |  | - |  |
| 13:00–14:20 | [실습] 검색 문서의 관련성 검증을 추가한 RAG | 실습 | `02_relevance_grading_rag` | - 검색 문서 관련성 평가기 구현<br>- LangGraph State 정의<br>- 조건부 엣지로 관련성 검증<br>- 그래프 컴파일 및 실행 |
| 14:20–14:30 | ☕ Break |  | - |  |
| 14:30–15:50 | [실습] 환각 여부를 평가하는 Agentic RAG | 실습 | `03_hallucination_grading_rag` | - 할루시네이션 평가기 구현<br>- 쿼리 재작성 모듈<br>- 전체 Agentic RAG 워크플로우 구성 |
| 15:50–16:50 | [실습] 사용자 질문 의도를 분류하는 Agentic RAG | 실습 | `04_agentic_rag_websearch` | - 사용자 질문 의도 분류<br>- 웹 검색 기반 신뢰성 있는 답변 제공<br>- 다중 분기 조건 처리 |
| 16:50–17:00 | Q&A 및 코드 정리 | 마무리 | - | - 개별 자율 실습<br>- 질의응답 |



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

Day2 폴더로 이동한 후 아래 방법 중 하나를 선택하세요.

#### 방법 1: uv sync 사용 (권장)

```bash
# Day2 폴더로 이동
cd Day2

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
.venv\Scripts\python.exe -m ipykernel install --user --name=llm-day2 --display-name="llm Day2"
```

#### macOS/Linux

```bash
.venv/bin/python -m ipykernel install --user --name=llm-day2 --display-name="llm Day2"
```

커널 등록 후 **VS Code를 리로드**하면 노트북에서 "llm Day2" 커널을 선택할 수 있습니다.

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

---

### 5. LangGraph Studio 실행

각 실습 폴더에서 LangGraph Studio를 실행할 수 있습니다.

```bash
# 01번 실습 - 기본 RAG
cd 01_basic_rag_chromadb
uv run langgraph dev

# 02번 실습 - 관련성 검증 RAG
cd 02_relevance_grading_rag
uv run langgraph dev

# 03번 실습 - 환각 평가 RAG
cd 03_hallucination_grading_rag
uv run langgraph dev
```
