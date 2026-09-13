# LangGraph 문서 도우미 Deep Agent with Skills

LangGraph 공식 문서를 검색하고 활용하는 Deep Agent로, **langgraph-docs** 스킬을 사용합니다.

## 개요

이 프로젝트는 LangChain의 Deep Agents framework를 사용하여 LangGraph 문서를 검색하고 참조하는 AI 에이전트입니다. Skills 시스템을 통해 효과적인 문서 검색 워크플로우를 제공합니다.

## 주요 기능

### Skills (Progressive Disclosure)
- **langgraph-docs**: LangGraph Python 문서를 가져와 참조하는 전문 워크플로우
  - 상태 기반 에이전트 구축 가이드
  - 멀티 에이전트 워크플로우 구현
  - Human-in-the-loop 패턴
  - LangGraph API 레퍼런스

### 작동 방식
1. **문서 인덱스 가져오기**: https://docs.langchain.com/llms.txt에서 전체 문서 목록 확인
2. **관련 문서 선택**: 사용자 질문과 가장 관련 있는 2-4개 URL 선택
3. **문서 가져오기 및 적용**: fetch_url 도구로 문서 콘텐츠를 로드하고 답변 제공

## 프로젝트 구조

```
03_deep_agent_skills/
├── graph.py                      # Deep Agent 구현 및 CLI
├── langgraph.json                # LangGraph 설정
├── README.md                     # 이 파일
├── .env.example                  # 환경 변수 템플릿
└── skills/                       # Skills 폴더
    └── langgraph-docs/
        └── SKILL.md              # LangGraph 문서 검색 워크플로우
```

### Skills란?

Skills는 재사용 가능한 도메인 지식과 워크플로우를 패키징한 것입니다. 각 skill은:
- **SKILL.md** 파일로 정의됨
- **Frontmatter**: name, description 등 메타데이터
- **Instructions**: 상세한 작업 지침과 워크플로우

### langgraph-docs Skill의 워크플로우

1. **문서 인덱스 가져오기**
   - `fetch_url`을 사용하여 https://docs.langchain.com/llms.txt 읽기
   - 모든 사용 가능한 문서 목록 확인

2. **관련 문서 선택**
   - 사용자 질문과 가장 관련 있는 2-4개 URL 식별
   - 우선순위:
     - 구현 질문 → how-to 가이드
     - 개념 질문 → 핵심 개념 페이지
     - 종단 간 예제 → 튜토리얼
     - API 세부사항 → 레퍼런스 문서

3. **문서 가져오기 및 적용**
   - 선택한 URL에서 `fetch_url` 사용
   - 문서 내용을 기반으로 사용자 요청 완료


## 실행

### 랭그래프 스튜디오 실행

```bash
uv run langgraph dev --allow-blocking
```

### 예시 질문

- 랭체인으로 SQL 에이전트 만드는법
- 랭체인으로 MCP 서버 연결하는법 예제


## 나만의 Skill 만들어 적용하기

1. 어떤 Skill을 만들지 정하기 (예: 특정 도메인 문서 검색, 계산, API 조회 등)
2. make_skill_tool_prompt.txt 맨 아래 요구사항란에 그 내용을 적어 AI 툴 (ChatGPT 등)에 입력
3. 생성된 결과 중 SKILL.md 부분 → skills/my-skill-name/SKILL.md에 덮어쓰기
4. 생성된 tool 코드 → graph_practice.py의 TODO 위치에 삽입하고 tools 리스트에 추가
   - Skill에서 언급한 tool 이름과 실제 함수명이 동일한지 확인
5. `uv run langgraph dev --allow-blocking`로 실행 후, 해당 Skill이 트리거되는 질문을 던져서 테스트