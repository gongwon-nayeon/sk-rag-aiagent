# SK RAG AI Agent 4일 과정 - Day 4

4일차에서는 Deep Agents의 고급 패턴을 학습하고, 실전 Deep Research Agent를 구축합니다.

Day3에서 배운 `create_agent`의 기본을 넘어, 복잡한 작업을 효율적으로 처리하는 Harness, Deep Agents를 마스터합니다.

### 커리큘럼

1. **Deep Agents 개요 + Harness Engineering**
2. **[실습] Virtual File System 구현** - `01_file_system.ipynb`
3. **[실습] create_deep_agent 기초** - `02_basic_deep_agent.ipynb`
4. **[실습] Skills - Progressive Disclosure** - `03_deep_agent_skills/`
5. **[이론] SubAgents & Deep Research 아키텍처**
6. **[실습] Deep Research Agent** - `deep_research/`

| 시간 | 내용 | 유형 | 실습 코드 파일 | 세부 구성 |
|------|------|------|----------------|-----------|
| 09:00–10:10 | Deep Agents 개요 + Harness Engineering | 이론 | - | - Long-horizon tasks (50+ tool calls)<br>- Context Offloading (File System)<br>- Progressive Disclosure (Skills)<br>- Context Isolation (SubAgents)<br>- Harness & Continual Learning<br>- Self-improving AI systems |
| 10:10–10:20 | ☕ Break | - | - | |
| 10:20–11:30 | [실습] Virtual File System 구현 | 실습 | `01_file_system.ipynb` | - State에 파일 시스템 추가<br>- ls(), read_file(), write_file() 구현<br>- Mock 웹 검색 결과 저장<br>- Research workflow 구축<br>- Context offloading 전략 |
| 12:00–13:00 | 🍱 Lunch | - | - | |
| 13:00–13:50 | [실습] create_deep_agent 기초 | 실습 | `02_basic_deep_agent.ipynb` | - create_deep_agent vs create_agent<br>- File System 자동 통합<br>- Custom tools 추가<br>- From Scratch vs create_deep_agent 비교<br>- Multi-turn conversations |
| 13:50–14:00 | ☕ Break | - | - | |
| 14:00–15:00 | [실습] Skills - Progressive Disclosure | 실습 | `03_deep_agent_skills/03_deep_agent_skills.ipynb` | - Skill 파일 작성 (SKILL.md)<br>- StateBackend에 skills 추가<br>- On-demand 스킬 로딩<br>- LangChain 공식 문서 skill 활용<br>- Progressive context loading |
| 15:00–15:10 | ☕ Break | - | - | |
| 15:10–15:40 | SubAgents & Deep Research 설계 | 이론 | - | - SubAgents의 필요성<br>- task() 도구로 작업 위임<br>- Context Isolation 전략<br>- Deep Research Agent 아키텍처 |
| 15:40–17:00 | [실습] Deep Research Agent | 실습 | `deep_research` | - Multi-step research workflow<br>- LangGraph Studio<br>- 실전 활용 사례 |

## 실습 환경 설정

### 사전 요구사항

- Python 3.11 이상
- OpenAI API Key (https://platform.openai.com/api-keys)
- Tavily API Key (https://app.tavily.com/home)

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

Day4 폴더로 이동한 후 아래 방법 중 하나를 선택하세요.

#### 방법 1: uv sync 사용 (권장)

```bash
# Day4 폴더로 이동
cd Day4

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
.venv\Scripts\python.exe -m ipykernel install --user --name=llm-day4 --display-name="llm Day4"
```

#### macOS/Linux

```bash
.venv/bin/python -m ipykernel install --user --name=llm-day4 --display-name="llm Day4"
```

커널 등록 후 **VS Code를 리로드**하면 노트북에서 "llm Day4" 커널을 선택할 수 있습니다.

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
