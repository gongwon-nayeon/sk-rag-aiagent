# Deep Research Agent

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

Day4/deep_research 폴더로 이동한 후 아래 방법 중 하나를 선택하세요.

#### 방법 1: uv sync 사용 (권장)

```bash
cd Day4/deep_research

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


### 3. 랭그래프 스튜디오 실행

```bash
uv run langgraph dev
```