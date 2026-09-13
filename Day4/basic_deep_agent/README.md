# Deep Agent

## 랭그래프 스튜디오 실행

```bash
cd Day4/basic_deep_agent

uv run langgraph dev --no-reload --allow-blocking
```

## 예시 질문

- LangGraph가 무엇인지 조사하고 입문자 온보딩을 위한 보고서를 작성해주세요.
- ChatGPT, Claude, Gemini의 최신 요금제 정보를 수집해 정리하고, 이를 비교 분석한 뒤 어떤 선택이 가장 합리적인지 비교한 보고서를 만들어줘.

- 온라인 쇼핑몰 주문 데이터 100건을 orders.csv로 생성해줘.
컬럼은 order_id, customer_id, product, category, quantity, unit_price, order_date, status로 구성해줘.
그리고 이 데이터를 읽어서 월별 매출과 카테고리별 매출을 계산하는 analyze_orders.py를 작성하고, 분석 결과를 sales_summary.json으로 저장해줘.
분석이 끝나면 orders.csv에서 취소된 주문만 추출해서 cancelled_orders.csv로 저장해줘.