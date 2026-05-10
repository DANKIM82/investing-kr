---
name: earnings-flash
description: 실적 발표 직후 빠른 첫인상 분석
argument-hint: TICKER
---

`$ARGUMENTS` 회사의 방금 발표된 실적에 대한 빠른 1차 분석. 발표 후 1시간 안에 작성하는 용도.

**필수 읽기**: `../data-access.md`, `../design-system.md`

## 1. 헤드라인 숫자 (5분 안에)

```bash
python infra/free_data_kr.py companies $ARGUMENTS
python infra/free_data_kr.py fundamentals $ARGUMENTS \
  --series revenue,operating_income,net_income,diluted_eps
```

가장 최근 분기 매출, 영업이익, EPS만 추출.

## 2. Beat/Miss 신속 판정

| 지표 | 컨센서스 | 실제 | 차이 | Beat/Miss |
|---|---|---|---|---|
| 매출 | | | | |
| 영업이익 | | | | |
| EPS | | | | |

## 3. 가이던스 vs 실적

직전 분기 가이던스 대비 어떻게?

## 4. 다음 분기 가이던스

회사가 제시한 다음 분기 가이던스 (있으면). 컨센서스 대비 위/아래/일치?

## 5. 5대 take-away

발표 직후 5분 안에 짚어야 할 핵심 5개:
1. 무엇이 surprise인가?
2. 무엇이 우려스러운가?
3. 가이던스의 톤 (자신감 vs 보수적)
4. 시장 반응 예측 (시간외 거래 참조)
5. 다음 들여다볼 것

## 6. HTML 보고서 저장

`reports/{TICKER}_earnings_flash_{Q+0}.html`

짧고 빠른 요약 (1페이지 이내). 자세한 분석은 `/earnings`에서.

⚠️ 데이터 한계: 실적 발표 직후 yfinance가 즉시 업데이트되지 않을 수 있음. 회사 공시 직접 참조 권장.
