---
name: guidance-tracker
description: 경영진 가이던스 vs 실제 결과 추적
argument-hint: TICKER
---

`$ARGUMENTS` 회사가 과거 제시한 가이던스의 정확도를 추적하세요. 경영진의 신뢰성 평가가 핵심.

**필수 읽기**: `../data-access.md`, `../design-system.md`

## 1. 회사 정보

```bash
python infra/free_data_kr.py companies $ARGUMENTS
```

## 2. 과거 4-8분기 가이던스 추출

각 분기마다 `documents` 검색:
```bash
python infra/free_data_kr.py documents "guidance outlook expects" --tickers $ARGUMENTS --year 2024
```

각 분기 발표 시 회사가 다음 분기/연간 가이던스로 제시한 수치 추출:
- 매출 가이던스
- 영업이익 (또는 영업이익률) 가이던스
- EPS 가이던스
- CapEx 가이던스
- 세그먼트별 가이던스 (있으면)

## 3. 실제 실적 데이터 수집

같은 분기들의 actual:
```bash
python infra/free_data_kr.py fundamentals $ARGUMENTS \
  --periods Q1,Q2,...,Q8 \
  --series revenue,operating_income,net_income,diluted_eps,capex
```

## 4. Beat/Miss 트래커 표

| 분기 | 메트릭 | 가이던스 | 실제 | 차이 (%) | Beat/In-line/Miss |
|---|---|---|---|---|---|
| 2024Q1 | 매출 | | | | |
| 2024Q1 | EPS | | | | |
| 2024Q2 | 매출 | | | | |
| ... | | | | | |

## 5. 정확도 통계

- 매출 가이던스 정확도: Beat % / In-line % / Miss %
- EPS 가이던스 정확도
- 평균 차이 (bps 또는 %)
- Conservative bias (체계적으로 under-promise) vs Aggressive bias (over-promise)

## 6. 가이던스 톤 변화

분기별 가이던스 언어 변화 추적:
- 자신감 있는 톤 vs 보수적 톤
- 가이던스 범위 (좁은가 넓은가)
- 가이던스 raised/lowered/maintained 패턴

## 7. 다음 분기 가이던스 평가

가장 최근 발표된 가이던스를 과거 정확도와 함께 평가:
- 컨센서스 대비 어디인가
- 회사의 historical bias 감안하면 얼마나 신뢰?
- Realistic upside/downside

## 8. 시각화

`infra/chart_generator.py time-series` 활용:
- 분기별 가이던스 vs 실제 비교 차트

## 9. HTML 보고서 저장

`reports/{TICKER}_guidance_tracker.html`

⚠️ **한계**: free data로는 정확한 historical guidance 추출이 어려움. 보도자료 원문에서 수동 추출 필요할 수 있음. 가능한 범위 내에서 작업하고 한계 명시.
