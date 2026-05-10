---
name: dcf
description: DCF 가치평가 + 민감도 분석
argument-hint: TICKER (예: 005930, AAPL, 7203)
---

`$ARGUMENTS` 회사에 대해 DCF (현금흐름할인법) 가치평가를 수행하세요.

**필수 읽기**: `../data-access.md`, `../design-system.md`

## 1. 회사 정보 + 시장 데이터

```bash
python infra/free_data_kr.py companies $ARGUMENTS
python infra/market_data.py quote $ARGUMENTS
python infra/market_data.py multiples $ARGUMENTS
```

캡처:
- 현재 주가, 시가총액
- 발행주식수
- 베타 (없으면 1.0 가정 + 명시)
- 순부채 (Total Debt - Cash)

## 2. Historical 재무 데이터 (5-7년)

```bash
python infra/free_data_kr.py fundamentals $ARGUMENTS \
  --periods 2020Q4,2021Q4,2022Q4,2023Q4,2024Q4 \
  --series revenue,operating_income,ebitda,net_income,operating_cash_flow,capex,total_debt,cash_and_equivalents
```

연간 데이터로 변환 (4개 분기 합산 또는 연간 보고서 직접 조회). 추세 파악:
- 매출 CAGR (5년)
- 영업이익률 평균 + 추이
- FCF 변환률 (FCF/Revenue)
- CapEx 강도 (CapEx/Revenue)

## 3. 5년 Forward Projection

`infra/projection_engine.py` 활용 (있으면) 또는 직접 모델링:

3가지 시나리오:
- **Base**: 시장 컨센서스 또는 회사 가이던스 기반
- **Bull**: 상위 시나리오 (TAM 확장, 마진 개선 가속)
- **Bear**: 하위 시나리오 (성장 둔화, 마진 압박)

각 시나리오마다:
| 항목 | Year 1 | Year 2 | Year 3 | Year 4 | Year 5 |
|---|---|---|---|---|---|
| 매출 | | | | | |
| 영업이익률 | | | | | |
| 영업이익 | | | | | |
| 세금 (effective rate) | | | | | |
| NOPAT | | | | | |
| (-) CapEx | | | | | |
| (-) ΔWorking Capital | | | | | |
| FCF (Free Cash Flow to Firm) | | | | | |

## 4. WACC 계산

### 한국주식

- **무위험금리 (Rf)**: `python infra/market_data.py risk-free-rate` (10년 한국국채)
  - 미달성 시 한국 default: 3.5%
- **시장 리스크 프리미엄 (ERP)**: 한국 ERP ~6% (Damodaran 자료 기준)
- **베타 (β)**: yfinance 또는 추정
- **Cost of Equity**: Rf + β × ERP
- **Cost of Debt**: 회사 신용등급 기반 추정 (default 한국은 4-5% pre-tax)
- **세후 Cost of Debt**: × (1 - 한국 법인세율 24%)
- **D/E ratio**: 재무상태표 기반
- **WACC**: 가중평균

### 미국주식

- Rf: 10Y Treasury (FRED 또는 default 4.5%)
- ERP: 5.5%
- 법인세율: 21%

### 일본주식

- Rf: 10Y JGB (~1.0% 최근)
- ERP: 5.5%
- 법인세율: 30%

WACC 표 작성. 모든 가정 명시.

## 5. Terminal Value

Gordon Growth Model:
- Terminal growth rate (g): 보수적으로 GDP 성장률 (한국 ~2%, 미국 ~2.5%, 일본 ~1%)
- TV = FCF_year5 × (1+g) / (WACC - g)

또는 Exit Multiple 방식:
- TV = EBITDA_year5 × Exit Multiple (peer median)

두 방식 모두 계산해서 비교 권장.

## 6. Discount + 합산

각 시나리오마다:
- 5년치 FCF를 WACC로 할인
- TV를 5년차로 할인
- 합산 = Enterprise Value
- (-) Net Debt
- = Equity Value
- ÷ Diluted Shares = 주당 적정가

## 7. 민감도 분석 (Sensitivity Table)

2D 민감도 표: WACC × Terminal Growth Rate

|  | g = 1% | g = 1.5% | g = 2% | g = 2.5% | g = 3% |
|---|---|---|---|---|---|
| WACC = 7% | | | | | |
| WACC = 8% | | | | | |
| WACC = 9% | | | | | |
| WACC = 10% | | | | | |
| WACC = 11% | | | | | |

(각 셀에 implied 주당 가치)

`infra/chart_generator.py dcf-sensitivity` 활용해서 heatmap 차트도 생성.

## 8. Football Field Valuation

DCF 결과를 다른 valuation 방법론과 비교:
- DCF (Bull/Base/Bear): 3개 점
- Trading multiples (P/E, EV/EBITDA): peer median × Q+0 EPS/EBITDA
- 52주 high/low
- 애널리스트 컨센서스 target price

`infra/chart_generator.py football-field` 활용.

## 9. 결론

- Base case 적정가 vs 현재 주가: % upside/downside
- 가장 민감한 변수 (WACC? 마진? 성장률?)
- 핵심 가정의 합리성

## 10. HTML 보고서 저장

`reports/{TICKER}_dcf.html`

구조:
1. 요약 (Base case 적정가 + 현재가 vs)
2. Historical 재무 (5-7년)
3. Forward Projection (3 시나리오)
4. WACC 계산
5. Terminal Value
6. DCF 결과 표
7. 민감도 분석 (heatmap)
8. Football Field
9. 핵심 가정 요약
10. 결론 + 주요 리스크

모든 가정과 숫자에 출처 또는 계산 근거 명시.
