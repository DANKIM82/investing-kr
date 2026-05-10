---
name: unit-economics
description: 단위경제 분석 (ARPU, CAC, LTV, churn 등)
argument-hint: TICKER
---

`$ARGUMENTS` 회사의 단위 경제학 (unit economics) 분석. SaaS, 플랫폼, 소비재 회사에 가장 유용.

⚠️ **호환성**: 이 skill은 회사별 KPI에 크게 의존합니다. Free 데이터 (DART, yfinance, SEC EDGAR)에서 KPI는 본문 검색으로만 추출 가능. 결과 품질이 제한적일 수 있음.

**필수 읽기**: `../data-access.md`, `../design-system.md`

## 1. 회사 정보 + 비즈니스 모델 식별

```bash
python infra/free_data_kr.py companies $ARGUMENTS
```

비즈니스 모델 분류:
- **SaaS / 클라우드**: ARR, Net Revenue Retention, Gross Retention, RPO, ACV
- **플랫폼 (광고)**: DAU/MAU, ARPU, sessions/user, time spent
- **마켓플레이스 / e-commerce**: GMV, take rate, active buyers, AOV
- **구독형 (OTT, 음원)**: 가입자 수, ARPU, churn, content cost/sub
- **소매 / F&B**: same-store sales, 객수, 평균 객단가, 매장당 매출
- **통신**: 가입자 수, ARPU, churn, capex/sub

## 2. KPI 추출

`documents`로 사업보고서/10-K 본문에서 KPI 추출:
```bash
python infra/free_data_kr.py documents "subscribers ARR DAU MAU ARPU" --tickers $ARGUMENTS
```

수동 추출 필요할 수 있음 (filing 본문 직접 읽기).

## 3. 단위 경제 표

분기별/연간별:
| 기간 | 핵심 단위 (예: 가입자) | ARPU | 신규 단위 | 이탈률 (Churn) |
|---|---|---|---|---|

## 4. Funnel 분석 (가능한 경우)

- 잠재고객 → 가입자 → 유료고객 → 이탈
- 각 단계 conversion rate

## 5. CAC vs LTV (가능한 경우)

- **CAC (Customer Acquisition Cost)**: 마케팅비 / 신규 고객 수
- **LTV (Lifetime Value)**: ARPU × Gross Margin / Churn rate
- **LTV/CAC ratio**: 3x 이상이 일반적 healthy

이 값을 산출하려면 비공개 데이터가 많아 추정 필요. 가정 명시.

## 6. 코호트 분석 (가능한 경우)

연도별 가입자 코호트의 retention 추이. 회사가 별도 공시할 때만 가능.

## 7. Peer 비교

같은 비즈니스 모델 peer와 단위 경제 비교:
- ARPU 차이
- Retention 차이
- LTV/CAC

## 8. 단위 경제 → 재무 연결

- ARPU × 가입자 = 매출 (검증)
- LTV가 시가총액과 어떻게 연결되는가

## 9. HTML 보고서 저장

`reports/{TICKER}_unit_economics.html`

⚠️ 본 보고서의 한계 명시: "회사별 KPI는 사업보고서 본문에서 추출했으며, 수동 검증이 필요할 수 있음."
