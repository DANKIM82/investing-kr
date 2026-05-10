---
name: capital-allocation
description: 자사주, 배당, 주주환원 분석
argument-hint: TICKER
---

`$ARGUMENTS` 회사의 자본 배분 (capital allocation) 정책 분석. 어떻게 현금을 사용하고 주주에게 돌려주는가.

**필수 읽기**: `../data-access.md`, `../design-system.md`

## 1. 회사 정보 + 시장 데이터

```bash
python infra/free_data_kr.py companies $ARGUMENTS
python infra/market_data.py quote $ARGUMENTS
```

시가총액, 발행주식수, 베타 캡처.

## 2. 5년 historical 자본 배분 데이터

```bash
python infra/free_data_kr.py fundamentals $ARGUMENTS \
  --periods 2020Q4,2021Q4,2022Q4,2023Q4,2024Q4 \
  --series operating_cash_flow,capex,dividends_paid,share_repurchases,total_debt,cash_and_equivalents
```

연간 합계로 변환.

## 3. Cash Flow 흐름 분석

| 항목 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|
| 영업활동현금흐름 (OCF) | | | | | |
| (-) CapEx | | | | | |
| = Free Cash Flow | | | | | |
| (-) 배당금 | | | | | |
| (-) 자사주 매입 | | | | | |
| = 유보현금 (Retained Cash) | | | | | |

각 행이 OCF의 몇 % 인가도 함께 표기.

## 4. 주주 환원 (Shareholder Yield)

- **배당 수익률**: 연간 배당 / 시가총액
- **자사주 매입률**: 연간 자사주 매입 / 시가총액
- **Total Shareholder Yield**: 배당 + 자사주 매입 / 시가총액
- **Net buyback rate**: (자사주매입 - 자사주발행) / 시가총액

5년 추이로 표시.

## 5. 부채 정책

| 항목 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|
| 총 부채 | | | | | |
| 현금 | | | | | |
| 순부채 (Net Debt) | | | | | |
| 순부채/EBITDA | | | | | |

레버리지 추이 (deleveraging vs leveraging).

## 6. CapEx 패턴

- CapEx / Revenue (capital intensity)
- CapEx / OCF
- 성장 vs 유지 CapEx 분류 (가능한 경우)
- 5년 trend

## 7. M&A History (가능한 경우)

`documents`로 검색:
```bash
python infra/free_data_kr.py documents "acquisition merger" --tickers $ARGUMENTS
```

주요 M&A 이벤트와 규모 정리.

## 8. 자본 배분 평가

5점 척도로 평가:
- **Discipline (기강)**: CapEx 규율, M&A 가격 정책
- **Returns (환원)**: shareholder yield 일관성
- **Balance (균형)**: 성장 투자 vs 환원 균형
- **Communication (소통)**: 자본 배분 정책 명확성
- **Track record**: 과거 결정의 결과 (좋은 M&A vs 실패한 M&A 등)

## 9. Peer 비교

같은 산업 peer 3-5개와 shareholder yield, capex intensity 비교.

## 10. HTML 보고서 저장

`reports/{TICKER}_capital_allocation.html`

구조:
1. 요약 (5년 평균 환원율, 평가 점수)
2. Cash Flow 흐름 표
3. 주주 환원 분석
4. 부채 정책
5. CapEx 패턴
6. M&A 이력
7. Peer 비교
8. 5점 척도 평가
9. 결론
