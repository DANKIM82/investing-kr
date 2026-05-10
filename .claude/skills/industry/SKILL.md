---
name: industry
description: 다회사 비교 분석 (cross-company)
argument-hint: TICKER1 TICKER2 TICKER3 ... (여러 회사)
---

`$ARGUMENTS`로 명시된 여러 회사를 나란히 비교 분석. 같은 시장이거나 다른 시장 (예: 005930 INTC TSM)이어도 OK.

**필수 읽기**: `../data-access.md`, `../design-system.md`

## 1. 각 회사 정보 조회

각 ticker에 대해:
```bash
python infra/free_data_kr.py companies $TICKER
```

회사명, 시장, 통화, 회계연도 종료월 캡처.

## 2. 통화 정규화 결정

다국가 비교 시:
- 절대값 비교 (시가총액, 매출): USD 기준 통일 (FX rate 적용)
- 비율 비교 (마진, 성장률): 통화 무관

FX rate는 yfinance의 `=X` 티커 활용 (예: KRWUSD=X).

## 3. 분기 정규화

각 회사의 회계연도가 다르면 calendar quarter로 통일.

## 4. 핵심 메트릭 수집

각 회사 × 최근 4-8분기:

```bash
python infra/free_data_kr.py fundamentals $TICKER \
  --periods 2024Q1,2024Q2,2024Q3,2024Q4,2025Q1,2025Q2,2025Q3,2025Q4 \
  --series revenue,operating_income,net_income,diluted_eps,operating_cash_flow,capex,total_assets,total_equity
```

## 5. 비교 표 (calendar quarter 기준)

### 매출 성장률 (YoY)

| 회사 | 2024Q4 | 2025Q1 | 2025Q2 | 2025Q3 |
|---|---|---|---|---|
| 삼성전자 | | | | |
| TSMC | | | | |
| Intel | | | | |

### 영업이익률

(같은 형식)

### ROE

(같은 형식)

## 6. 시각화

`infra/chart_generator.py time-series` 활용:
- 매출 성장률 추이 (모든 회사 한 차트)
- 영업이익률 추이
- 시가총액 변화

## 7. Quality vs Valuation 매트릭스

산점도: x축 = 매출 성장률 (TTM), y축 = P/E (forward).

각 회사가 어느 quadrant에 있는가:
- High growth + High multiple (정당화 가능?)
- Low growth + Low multiple (가치주?)
- High growth + Low multiple (저평가?)
- Low growth + High multiple (피해야?)

## 8. 시장점유율 분석

가능한 경우 (예: 반도체 출하량, EV 판매대수):
- 절대 수치
- 시장 점유율 추이
- 점유율 변화 driver

## 9. 강점/약점 매트릭스

각 회사에 대해 1-2 문장으로:
- 강점 (vs peer)
- 약점 (vs peer)

## 10. HTML 보고서 저장

`reports/{TICKERS_joined}_industry.html` (예: AAPL_MSFT_GOOG_industry.html)

구조:
1. 요약 (한 단락)
2. 회사별 1행 요약 표
3. 핵심 메트릭 비교 표 (4-5개)
4. 시각화 (3-4개 차트)
5. Quality vs Valuation
6. 강점/약점 매트릭스
7. 결론 (어느 회사가 가장 매력적, 가장 우려스러운지)
