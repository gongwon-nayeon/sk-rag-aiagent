# SK Langchain/Langgraph 기반 RAG 및 AI Agent 4일 과정

Python version: 3.13.5

강의 자료(PDF): https://drive.google.com/file/d/1FqPUt1xuC10cAhUf-bHU5C0unTLhrFdl/view?usp=sharing

```
📦sk-rag-aiagent
 ┣ 📂Day1
 ┃ ┣ 📜01_langchain_llm_basics.ipynb
 ┃ ┣ 📜02_langgraph_essentials.ipynb
 ┃ ┣ 📜03_langgraph_messages_state.ipynb
 ┃ ┣ 📜04_langgraph_nodes_edges.ipynb
 ┃ ┣ 📜05_langgraph_tools_chatbot.ipynb
 ┃ ┣ 📂mcp
 ┃ ┣ 📜pyproject.toml
 ┃ ┣ 📜requirements.txt
 ┃ ┗ 📜README.md
 ┣ 📂Day2
 ┃ ┣ 📜01_basic_rag_chromadb.ipynb
 ┃ ┣ 📂01_basic_rag_chromadb
 ┃ ┣ 📂02_relevance_grading_rag
 ┃ ┣ 📂03_hallucination_grading_rag
 ┃ ┣ 📂04_agentic_rag_websearch
 ┃ ┣ 📂dataset
 ┃ ┣ 📜pyproject.toml
 ┃ ┣ 📜requirements.txt
 ┃ ┗ 📜README.md
 ┣ 📂Day3
 ┃ ┣ 📜01_langchain_create_agent.ipynb
 ┃ ┣ 📜02_web_search_agent.ipynb
 ┃ ┣ 📜03_custom_middleware.ipynb
 ┃ ┣ 📜04_builtin_middleware.ipynb
 ┃ ┣ 📂mini_coding_agent
 ┃ ┣ 📂workspace
 ┃ ┣ 📜pyproject.toml
 ┃ ┣ 📜requirements.txt
 ┃ ┗ 📜README.md
 ┣ 📂Day4
 ┃ ┣ 📜01_file_system.ipynb
 ┃ ┣ 📜02_basic_deep_agent.ipynb
 ┃ ┣ 📂03_deep_agent_skills
 ┃ ┣ 📂deep_research
 ┃ ┣ 📜pyproject.toml
 ┃ ┣ 📜requirements.txt
 ┃ ┗ 📜README.md
 ┗ 📜README.md
```

---

## 강의 커리큘럼

### 📂 Day1 - LangChain & LangGraph 기초 / MCP
- LangChain 소개
- [실습] LangChain 기반 LLM 사용하기 - `01_langchain_llm_basics.ipynb`
- LangGraph 소개
- [실습] LangGraph 기초 사용법 - `02_langgraph_essentials.ipynb`
- [실습] LangGraph 메시지 관리 그래프 - `03_langgraph_messages_state.ipynb`
- [실습] LangGraph 노드·엣지 연결 / 조건부 엣지 - `04_langgraph_nodes_edges.ipynb`
- AI Agent와 도구 호출 기반 에이전트
- [실습] 도구 기반 에이전트 그래프 - `05_langgraph_tools_chatbot.ipynb`
- MCP(Model Context Protocol) 개념과 활용
- [실습] MCP 기반 agent 구현하기 - `mcp/`

### 📂 Day2 - RAG & Agentic RAG
- RAG 이해하기
- [실습] ChromaDB로 만드는 기본 RAG - `01_basic_rag_chromadb.ipynb`
- [실습] ChromaDB로 만드는 기본 RAG (랭그래프 스튜디오) - `01_basic_rag_chromadb/`
- Agentic RAG 개념 및 기능
- [실습] 검색 문서의 관련성 검증을 추가한 RAG - `02_relevance_grading_rag/`
- [실습] 환각 여부를 평가하는 Agentic RAG - `03_hallucination_grading_rag/`
- [실습] 사용자 질문 의도를 분류하는 Agentic RAG - `04_agentic_rag_websearch/`

### 📂 Day3 - AI Agent 구현
- AI 에이전트 이해하기
- [실습] Langchain의 create_agent 이해하기 (도구 정의) - `01_langchain_create_agent.ipynb`
- [실습] 웹 검색 에이전트 구현하기 (Tavily Search) - `02_web_search_agent.ipynb`
- [실습] 커스텀 미들웨어 만들기 - `03_custom_middleware.ipynb`
- [실습] 빌트인 미들웨어 활용하기 - `04_builtin_middleware.ipynb`
- [실습] Mini Coding Agent 구현 - `mini_coding_agent/`

### 📂 Day4 - Deep Agents
- Deep Agents 개요 + Harness Engineering
- [실습] Virtual File System 구현 - `01_file_system.ipynb`
- [실습] create_deep_agent 기초 - `02_basic_deep_agent.ipynb`
- [실습] Skills - Progressive Disclosure - `03_deep_agent_skills/`
- SubAgents & Deep Research 설계
- [실습] Deep Research Agent - `deep_research/`

---

📍 본 레포지토리는 **SK Langchain/Langgraph 기반 RAG 및 AI Agent 4일 과정**의 실습 코드입니다.
