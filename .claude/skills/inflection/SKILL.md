---
name: inflection
description: 메트릭 가속/감속 자동 감지
argument-hint: TICKER
---

`$ARGUMENTS` 회사의 핵심 메트릭에서 추세 변화 시점 (inflection point)을 자동 감지하세요.

**필수 읽기**: `../data-access.md`, `../design-system.md`

## 1. 회사 정보

```bash
python infra/free_data_kr.py companies $ARGUMENTS
```

## 2. 8-12분기 historical 데이터

```bash
python infra/free_data_kr.py fundamentals $ARGUMENTS \
  --periods Q-11,...,Q+0 \
  --series revenue,gross_profit,operating_income,net_income,operating_cash_flow,capex
```

## 3. 분기별 성장률 계산

각 메트릭 × 각 분기에 대해:
- QoQ 성장률
- YoY 성장률
- 2년 CAGR

## 4. Inflection 감지 알고리즘

각 메트릭의 YoY 성장률 시계열에서:
- **가속화 (Acceleration)**: 직전 4Q 평균 성장률 < 직후 4Q 평균 성장률 (10% 이상 격차)
- **감속화 (Deceleration)**: 직전 4Q 평균 > 직후 4Q 평균 (10% 이상 격차)
- **반전 (Inflection)**: 부호 변화 (-에서 +로 또는 그 반대)

각 inflection point 표시:
| 분기 | 메트릭 | 변화 유형 | 직전 4Q 평균 | 직후 4Q 평균 | 격차 |

## 5. 회사별 KPI inflection

`documents`로 회사별 KPI 추출 가능하면 같은 분석:
- 출하량 (반도체, 자동차)
- 가입자 수 (플랫폼)
- 매장 수 (소매)

## 6. Driver 분석

각 inflection 포인트에 대해 가능한 원인 추정:
- 거시 환경 변화 (금리, 환율)
- 산업 구조 변화 (경쟁 강도)
- 회사 내부 이벤트 (신제품 출시, M&A)

`documents`에서 그 분기 공시 검색해서 회사 측 코멘트 확인.

## 7. 현재 추세 평가

가장 최근 분기 기준:
- 어떤 메트릭이 가속 중?
- 어떤 메트릭이 감속 중?
- 다음 분기에 inflection 예상되는 메트릭?

## 8. 시각화

`infra/chart_generator.py time-series` 활용:
- 각 메트릭의 YoY 추이 차트, inflection 포인트 강조 표시

## 9. HTML 보고서 저장

`reports/{TICKER}_inflection.html`

구조:
1. 요약 (감지된 inflection 개수 + 가장 중요한 1-2개)
2. 메트릭별 추이 차트
3. Inflection 포인트 표
4. Driver 분석
5. 현재 추세 + 다음 분기 예상
