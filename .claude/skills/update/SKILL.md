---
name: update
description: 기존 커버리지 회사 업데이트 (이전 보고서 후 변화)
argument-hint: TICKER
---

`$ARGUMENTS` 회사를 이전에 cover 한 적 있으면 그 이후 변화를 업데이트하세요.

**필수 읽기**: `../data-access.md`, `../design-system.md`

## 1. 이전 컨텍스트 로드

`reports/.tmp/{TICKER}_initiate_context.json` 또는 가장 최근 `{TICKER}_*.html` 파일 확인:
- 이전 적정가
- 이전 thesis
- 이전 모니터링 항목

이전 자료가 없으면 `/initiate` 사용 권유.

## 2. 새 데이터 수집

```bash
python infra/free_data_kr.py companies $ARGUMENTS
python infra/free_data_kr.py fundamentals $ARGUMENTS \
  --periods <since_last_report>
```

## 3. 변화 분석

| 항목 | 이전 보고서 | 현재 | 변화 |
|---|---|---|---|
| 주가 | | | % |
| 매출 (TTM) | | | YoY |
| EPS (TTM) | | | YoY |
| Forward P/E | | | |

## 4. Thesis 평가

이전 thesis가 여전히 유효한가?
- **Confirmed**: 데이터가 thesis를 강화 → 업데이트 + Buy 유지
- **Challenged**: 일부 가정 흔들림 → 적정가 재조정
- **Broken**: 핵심 가정 무너짐 → Sell or Hold로 강등

## 5. 새 가이던스 / 이벤트

직전 보고서 이후 주요 변화:
- 실적 발표 결과 (vs 가이던스)
- 새 가이던스
- M&A, 자사주, 배당 변화
- 경영진 변화
- 산업 환경 변화

## 6. 적정가 업데이트

DCF/comps multiples 재계산. 이전 대비 변화 사유 명시.

## 7. HTML 보고서 저장

`reports/{TICKER}_update_{YYYYMMDD}.html`

구조:
1. 이전 보고서 요약 (한 단락)
2. 그 이후 핵심 변화 (3-5개 bullet)
3. 데이터 변화 표
4. Thesis 재평가 (Confirmed/Challenged/Broken)
5. 적정가 변경 사유
6. 새 모니터링 항목
