---
name: working-capital
description: 운전자본 분석 (재고, 매출채권, 매입채무)
argument-hint: TICKER
---

`$ARGUMENTS` 회사의 운전자본 (working capital) 추이를 분석.

**필수 읽기**: `../data-access.md`, `../design-system.md`

## 1. 회사 정보

```bash
python infra/free_data_kr.py companies $ARGUMENTS
```

## 2. 8분기 운전자본 데이터

```bash
python infra/free_data_kr.py fundamentals $ARGUMENTS \
  --periods Q-7,...,Q+0 \
  --series revenue,cost_of_revenue,inventory,trade_receivables,current_liabilities,operating_cash_flow
```

매입채무 (accounts payable)는 yfinance에서 직접 안 나올 수 있음. current_liabilities로 대체.

## 3. 운전자본 KPI 계산

각 분기마다:
- **DSO (Days Sales Outstanding)**: 매출채권 / 분기매출 × 90일
- **DIO (Days Inventory Outstanding)**: 재고 / 분기 매출원가 × 90일
- **DPO (Days Payable Outstanding)**: 매입채무 / 분기 매출원가 × 90일 (가능한 경우)
- **CCC (Cash Conversion Cycle)**: DSO + DIO - DPO
- **운전자본 / 매출**: (current assets - current liabilities) / TTM revenue

## 4. 추이 분석

| 분기 | DSO | DIO | DPO | CCC | WC/Sales |
|---|---|---|---|---|---|
| Q-7 | | | | | |
| ... | | | | | |
| Q+0 | | | | | |

YoY 변화도 함께.

## 5. 추세 시그널 해석

- **DSO 상승**: 매출 회수 둔화, 채권 부실 가능성
- **DIO 상승**: 재고 누적, 수요 둔화 또는 공급망 문제
- **DPO 하락**: 협상력 약화 또는 유동성 부족
- **CCC 증가**: 현금 효율 악화

각 변화가 일시적/구조적인지 평가.

## 6. Peer 비교

같은 산업 peer 3-5개와 CCC 비교. Peer median 대비 어디?

## 7. 운전자본 변화의 OCF 영향

| 분기 | OCF | OCF - 순이익 = WC 변화 추정 |
|---|---|---|

WC가 OCF를 얼마나 도와주거나 발목 잡았는가.

## 8. 미래 전망

- 회사 가이던스에서 운전자본 관련 코멘트 (있으면)
- 업계 사이클 위치 (고점이면 재고 누적 우려)
- 다음 분기 catalysts

## 9. HTML 보고서 저장

`reports/{TICKER}_working_capital.html`
