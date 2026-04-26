# 01 ChromaDB로 만드는 기본 RAG

PDF 문서를 PyMuPDF로 로딩하고 ChromaDB 벡터스토어를 구축하여 기본적인 RAG 시스템을 구현합니다.

## 주요 특징

- **ParentDocumentRetriever**: chunk 단위로 검색하되, 전체 페이지를 반환
- **PyMuPDF(fitz)**: PDF 문서 전처리
- **ChromaDB**: 벡터 저장소
- **LangGraph**: RAG 파이프라인 구성

## 파일 구조

```
01_basic_rag_chromadb/
├── state.py           # Graph State 정의
├── retriever.py       # ParentDocumentRetriever 설정 (PyMuPDF 사용)
├── nodes.py           # 노드 함수들 (chatbot, answer)
├── graph.py           # 그래프 구성 (에이전트 버전)
├── langgraph.json     # LangGraph Studio 설정
└── README.md          # 문서
```

## 실행 방법

### LangGraph Studio 실행

```bash
# 01_basic_rag_chromadb 폴더로 이동
cd 01_basic_rag_chromadb

# LangGraph Studio 실행
uv run langgraph dev
```
