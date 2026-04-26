---
name: langgraph-docs
description: Fetches and references LangGraph Python documentation to build stateful agents, create multi-agent workflows, and implement human-in-the-loop patterns. Use when the user asks about LangGraph, graph agents, state machines, agent orchestration, LangGraph API, or needs LangGraph implementation guidance.
---

# langgraph-docs

## 랭그래프/랭체인 관련 질문에 대한 답변을 위한 반드시 지켜야 할 프로세스

### 1. 참고 가능한 url 목록 가져오기
- `fetch_url` 도구를 사용하여 https://docs.langchain.com/llms.txt 읽기
- 모든 사용 가능한 구조화된 문서 목록 확인

### 2. 관련 문서 선택

1번을 통해 fetch_url로 읽은 내용에서 사용자의 질문과 가장 관련성 높은 URL을 1~2개 선택
예시:
사용자의 질문이 "Human-In-the-loop 패턴이 뭐야?"라면,
[Human-in-the-loop](https://docs.langchain.com/oss/python/deepagents/human-in-the-loop.md): Learn how to configure human approval for sensitive tool operations 이 가장 관련성이 높음

### 3. Fetch and Apply

2번에서 선택한 URL에 대해 반드시 `fetch_url` 도구를 사용하여 내용을 읽은 후, 해당 문서 내용을 충분히 활용하고 출처를 포함하여 사용자의 요청에 대한 답변 제공