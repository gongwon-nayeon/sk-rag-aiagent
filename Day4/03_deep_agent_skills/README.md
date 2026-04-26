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


### 새로운 Skill 추가

1. `skills/` 폴더에 새 디렉터리 생성:
```bash
mkdir skills/another-docs
```

2. `SKILL.md` 파일 작성:
```markdown
---
name: another-docs
description: Fetches and references documentation for another framework
---

# another-docs

## Workflow
1. Fetch the documentation index
2. Select relevant URLs
3. Fetch and apply
```

3. Agent가 자동으로 새 skill 인식!

### fetch_url 도구 커스터마이징

`graph.py`의 `fetch_url` 함수를 수정하여 추가 기능을 구현할 수 있습니다:
```python
def fetch_url(url: str) -> str:
    # 캐싱 추가
    # 인증 헤더 추가
    # 재시도 로직 구현
    # 등등...
    pass
```