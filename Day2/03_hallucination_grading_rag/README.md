# 03 환각 여부를 평가하는 Agentic RAG

검색 문서의 관련성, 답변의 환각 여부, 답변의 유용성을 평가하는 완전한 Agentic RAG 시스템입니다.

- **문서 관련성 평가**: 검색된 문서와 질문의 관련성 자동 평가
- **환각 평가**: 생성된 답변이 검색된 문서에 기반하는지 검증
- **답변 유용성 평가**: 답변이 질문을 해결하는지 평가
- **쿼리 재작성**: 검색 성능 향상을 위한 자동 쿼리 개선
- **다중 분기 조건**: 평가 결과에 따른 동적 워크플로우

## 파일 구조

```
03_hallucination_grading_rag/
├── state.py           # Graph State 정의
├── retriever.py       # Retriever 설정
├── prompts.py         # 프롬프트 정의 (관련성, 환각, 답변 평가, 쿼리 재작성)
├── nodes.py           # 노드 함수들
├── graph.py           # 그래프 구성
├── __init__.py        # 패키지 초기화
├── langgraph.json     # LangGraph Studio 설정
└── .env.example       # 환경변수 예시
```

## 실행 방법


```bash
# 03_hallucination_grading_rag 폴더로 이동
cd 03_hallucination_grading_rag

# LangGraph Studio 실행
uv run langgraph dev
```