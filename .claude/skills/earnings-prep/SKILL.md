---
name: earnings-prep
description: 실적 발표 전 준비 보고서
argument-hint: TICKER
---

`$ARGUMENTS` 회사의 다음 실적 발표 전에 봐야 할 핵심 사항을 정리하세요.

**필수 읽기**: `../data-access.md`, `../design-system.md`

## 1. 회사 정보 + 다음 발표일 추정

```bash
python infra/free_data_kr.py companies $ARGUMENTS
```

`latest_calendar_quarter`의 다음 분기가 발표 대상.

## 2. 시장 컨센서스 정리

가능한 범위에서 yfinance의 `analyst_price_targets`, `earnings_estimate` 활용:
- 컨센서스 매출, EPS
- 추정치 분포 (high/low/mean)
- 최근 추정치 revision 추세

데이터 없으면 명시적으로 "Consensus 데이터 미가용" 표기.

## 3. 직전 가이던스

이전 분기 컨퍼런스 콜에서 회사가 제시한 가이던스:

```bash
python infra/free_data_kr.py documents "outlook guidance" --tickers $ARGUMENTS
```

매출/마진/EPS/세그먼트별 가이던스 추출.

## 4. 핵심 모니터링 지표 (Watch List)

5-7개 정량 지표. 각각:
- 직전 분기 값
- 컨센서스/가이던스
- Bull threshold (이상이면 강세)
- Bear threshold (이하면 약세)

회사별 KPI (tearsheet 가이드 참조).

## 5. 5대 질문 (Key Questions)

이번 실적 발표에서 답이 나올 5개 질문 + 각 질문의 의미.

## 6. 시나리오별 주가 영향 추정

- Beat 시나리오 → 즉각 반응, 다음 단계 trigger
- In-line → 가이던스가 핵심
- Miss → 어떤 메트릭의 miss가 가장 치명적

## 7. HTML 보고서 저장

`reports/{TICKER}_earnings_prep.html`

## 8. 마무리

발표 직후 1시간 안에 확인할 체크리스트 5개 항목.
