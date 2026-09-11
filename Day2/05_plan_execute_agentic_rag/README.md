# 05 계획 수립과 도구 병렬 실행 기반 Agentic RAG

## 파일 구조

```
05_plan_execute_agentic_rag/
├── state.py           # Graph State 정의 (plan_decision, entities, step_results 등)
├── retriever.py        # Retriever 설정 (04와 동일, chroma_db 공유)
├── prompts.py          # 프롬프트 정의 (planner, entity extractor 등)
├── nodes.py            # 노드 함수들
├── graph.py            # 그래프 구성
└── langgraph.json      # LangGraph Studio 설정
```

## 실행 방법

```bash
cd Day2

# 가상환경 활성화 (Windows)
.venv\Scripts\activate

# 가상환경 활성화 (macOS/Linux)
source .venv/bin/activate

# LangGraph Studio 실행
uv run langgraph dev
```
