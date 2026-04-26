# 04 사용자 질문 의도에 따라 일반답변/웹검색/문서검색을 하는 Agentic RAG

## 파일 구조

```
04_agentic_rag_websearch/
├── state.py           # Graph State 정의
├── retriever.py       # Retriever 설정
├── prompts.py         # 프롬프트 정의
├── nodes.py           # 노드 함수들
├── graph.py           # 그래프 구성
├── __init__.py        # 패키지 초기화
├── langgraph.json     # LangGraph Studio 설정
└── .env.example       # 환경변수 예시
```

## 실행 방법


```bash
# 04_agentic_rag_websearch 폴더로 이동
cd 04_agentic_rag_websearch

# LangGraph Studio 실행
uv run langgraph dev
```