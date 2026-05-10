---
name: earnings
description: 분기 실적 분석 (가이던스 추적 포함)
argument-hint: TICKER (예: 005930, AAPL, 7203)
---

`$ARGUMENTS` 회사의 가장 최근 분기 실적을 심도있게 분석하세요.

**필수 읽기**: `../data-access.md`, `../design-system.md`

## 1. 회사 정보 + 최신 분기 확인

```bash
python infra/free_data_kr.py companies $ARGUMENTS
```

`latest_calendar_quarter` 캡처. 이게 분석 대상 분기 (이하 "Q+0").

## 2. 8분기 + 비교용 1년 전 데이터

QoQ + YoY 비교 위해 최근 8분기 + Q-0 대비 1년 전 분기 = 총 9-10 분기.

```bash
python infra/free_data_kr.py fundamentals $ARGUMENTS \
  --periods Q-7,Q-6,...,Q+0 \
  --series revenue,gross_profit,operating_income,ebitda,net_income,diluted_eps,operating_cash_flow,capex
```

## 3. 헤드라인 분석

- **매출**: Q+0 vs Q-1 (QoQ), Q+0 vs Q-4 (YoY). 가속화/감속화 여부.
- **영업이익**: 같은 비교, 마진 변화도 함께.
- **EPS**: 같은 비교. EPS 성장 vs 매출 성장 발산 여부 (자사주 매입 효과 등).
- **컨센서스 vs 실적**: yfinance에서 가능한 범위 — `analyst_price_targets`, 직전 가이던스.

## 4. Beat / Miss 판정

각 메트릭에 대해:
- 회사 가이던스 (이전 분기에 발표) 대비
- 컨센서스 추정치 대비 (가능한 경우)
- 결과: Beat / In-line / Miss + 차이 (% 또는 bps)

## 5. 가이던스 추적 (Guidance Tracker)

`documents` 명령어로 이전 분기 실적 발표 시 회사가 제시한 가이던스 검색:

```bash
python infra/free_data_kr.py documents "guidance" --tickers $ARGUMENTS --year 2024
```

테이블:
| 메트릭 | 이전 분기 가이던스 | 실제 (Q+0) | Beat/Miss | 격차 |

다음 분기 가이던스도 동일하게 추출 (있으면).

## 6. 세그먼트/제품별 분석

회사가 사업부별 매출/영업이익을 별도 공시하면 그것 활용:
- 사업부별 매출 성장률
- 사업부별 마진 추이
- 어떤 사업부가 surprise driver인가?

회사별 본문 검색:
```bash
python infra/free_data_kr.py documents "segment" --tickers $ARGUMENTS
```

## 7. KPI 분석

회사별 핵심 KPI (tearsheet skill의 회사별 KPI 가이드 참조):
- 분기별 추이 표
- 가속화/감속화 시점
- 가이던스 대비 성과

## 8. 경영진 코멘트 / 컨퍼런스 콜 핵심

`documents`에서 최근 분기 컨콜 transcript 또는 보도자료 검색:
- 향후 전망에 대한 핵심 발언 3-5개
- 우려 사항에 대한 답변
- 새로운 이니셔티브

각 인용은 출처 링크 포함.

## 9. 5대 시사점 (Takeaways)

이번 실적이 투자 thesis에 미친 영향:
- 강세 thesis 강화한 점 2-3개
- 약세 thesis 강화한 점 2-3개
- 다음 분기까지 모니터링할 것

## 10. HTML 보고서 생성

`reports/{TICKER}_earnings_{Q+0}.html`에 저장. 

표 + 분석 + 인용으로 구성. design-system.md HTML 템플릿 사용.

구조:
1. 헤드라인 요약 (한 단락)
2. 핵심 재무 표 (8분기)
3. Beat/Miss 표
4. 세그먼트 분석
5. KPI 분석
6. 가이던스 트래커
7. 경영진 코멘트
8. 5대 시사점
9. 모니터링 항목
