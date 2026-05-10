---
name: tearsheet
description: 회사 1페이지 요약 (한국/미국/일본)
argument-hint: TICKER (예: 005930, AAPL, 7203, 삼성전자)
---

사용자가 지정한 회사 `$ARGUMENTS`의 1페이지 tearsheet (요약 보고서)를 생성하세요.

이는 애널리스트가 미팅 전에 빠르게 훑어보는 종목 스냅샷입니다.

**시작 전 필수 읽기**: `../data-access.md` (데이터 호출 방법) 및 `../design-system.md` (포맷 규칙). 이 두 파일의 규칙을 전 과정에서 따르세요.

## 1. 회사 정보 조회

```bash
python infra/free_data_kr.py companies $ARGUMENTS
```

다음 정보를 캡처:
- `company_id` (티커)
- `market` (KR/US/JP) — 이후 출력 포맷 결정
- `name` (회사명)
- `latest_calendar_quarter` — 모든 분기 계산의 기준 (data-access.md Section 2 참조)
- `fiscal_year_end_month` — 한국은 보통 12월, 일본은 3월, 미국은 회사별
- `currency` — KRW/USD/JPY
- `sector`, `industry`
- 회사명 표기 방식 (data-access.md Section 5)

## 2. 핵심 재무 데이터

`latest_calendar_quarter`에서 8분기 역산 (최근 4분기 + YoY 비교용 1년 전 4분기):

```bash
python infra/free_data_kr.py fundamentals $ARGUMENTS \
  --periods 2024Q1,2024Q2,2024Q3,2024Q4,2025Q1,2025Q2,2025Q3,2025Q4 \
  --series revenue,gross_profit,operating_income,net_income,diluted_eps,operating_cash_flow,capex
```

(분기는 실제 latest_calendar_quarter 기반으로 조정)

가져올 메트릭:
- 매출액 (Revenue)
- 매출총이익 (Gross Profit)
- 영업이익 (Operating Income)
- EBITDA — 별도 보고 안 되면 영업이익 + 감가상각으로 계산, "EBITDA (계산)" 표기
- 당기순이익 (Net Income)
- 희석주당이익 (Diluted EPS)
- 영업활동현금흐름 (Operating Cash Flow)
- CapEx (유형자산취득)
- FCF (계산: OCF - CapEx)

## 3. 핵심 운영 KPI

이 섹션은 **사업 driver 메트릭 전용** — D&A, 자사주 매입 같은 재무 항목은 여기 넣지 않음.

회사별 비즈니스 모델에 따라 KPI가 다름:
- **반도체 (삼성전자, SK하이닉스)**: DRAM/NAND ASP, 출하량, HBM 매출, 가동률
- **자동차 (현대차, 기아, Toyota)**: 판매 대수, 평균 판매단가, 친환경차 비중, 지역별 mix
- **인터넷/플랫폼 (NAVER, 카카오, Google)**: DAU/MAU, ARPU, 광고 매출, 클라우드 매출
- **이차전지 (LG에너지솔루션, 삼성SDI)**: 출하량 (GWh), 가동률, 글로벌 시장점유율
- **SaaS (Salesforce, ServiceNow)**: ARR, NRR, RPO, 고객 수
- **소비재 (LVMH, Costco)**: same-store sales, 매장 수, 평균 객단가
- **바이오/제약 (Pfizer, 셀트리온)**: 파이프라인 단계, 적응증별 매출

회사별 KPI는 `documents` 명령어로 사업보고서/10-K 본문에서 직접 추출:

```bash
python infra/free_data_kr.py documents "회사 KPI 키워드" --tickers $ARGUMENTS --year 2024
```

KPI를 별도로 공시하지 않는 회사는 **솔직하게 명시**: "회사가 [지표]를 별도 공시하지 않음" (재무 메트릭으로 KPI 자리를 메우지 말 것).

## 3b. 자본 환원 (Capital Return)

별도 섹션:
- 발행주식수
- 자사주 매입 (share_repurchases)
- 배당 지급 (dividends_paid)

같은 분기 범위로.

## 4. 핵심 비율 계산

최근 4분기, 각 분기마다 YoY 변화 표시:
- 매출총이익률 (Gross Margin %)
- 영업이익률 (Operating Margin %)
- EBITDA 마진
- 순이익률 (Net Margin %)
- 매출 성장률 (YoY)
- EPS 성장률 (YoY)

계절성 강한 업종 (Apple Q4, 한국 4분기 등)은 별도 메모로 표기.

## 5. 최근 동향 (Recent Developments)

`documents` 명령어로 최근 2분기 공시 검색:

```bash
# 한국
python infra/free_data_kr.py documents "$ARGUMENTS 실적" --tickers $ARGUMENTS --year 2024

# 미국 (예: AI 키워드)
python infra/free_data_kr.py documents "AI revenue" --tickers AAPL --forms 10-K,10-Q
```

추출:
- 회사 사업 설명 (2-3 문장)
- 최근 주요 발표/전략적 변화
- 경영진 코멘트 (인용 링크 필수)

3-5개 bullet point로 간결하게.

## 6. 5대 Key Tensions (강세/약세 논쟁점)

종목의 핵심 bull/bear 포인트 5개. 각 tension은 한 줄로:
- "1. <Bull factor> vs <Bear factor> — <구체 데이터>"
- bullish-leaning과 bearish-leaning 번갈아 가며

각 tension은 위에서 본 데이터를 직접 인용.

## 7. 뉴스 스냅샷

WebSearch 2회:
1. `"{ticker} {company_name} 뉴스 {current_year}"` — 한국주식이면 한국어 뉴스
2. `"{ticker} catalysts risks {current_year}"`

최근 6개월 핵심 이벤트 3-5개. 각 이벤트: 날짜, 한 줄 헤드라인, 감성 태그 (긍정/부정/혼합/예정).

## 8. 모니터링 지표 (What to Watch)

5개의 정량 모니터링 지표 — 강세/약세 thresholds 명시:
- 형식: "지표: 현재값 — 강세 임계값 / 약세 임계값"
- 예: "영업이익률: 12.4% — 13% 이상이면 가격결정력 확인 / 11% 이하면 비용 압박"

## 9. 보고서 저장

`reports/{TICKER}_tearsheet.html`에 저장. design-system.md의 HTML 템플릿 사용.

구조:

```html
<h1>{Company Name} ({TICKER}) — Tearsheet</h1>
<p>Generated: {date}</p>

<h2>회사 개요 (Company Overview)</h2>
{2-3 문장 요약}

<h2>5대 Key Tensions</h2>
{번호 매긴 5개 bull/bear 논쟁점}

<h2>핵심 재무 (Last 4 Quarters)</h2>
<table>...</table>

<h2>세그먼트/지역별 매출</h2>
{가능한 경우, 본문에서 추출}

<h2>운영 KPI</h2>
<table>{사업 driver 전용}</table>

<h2>자본 환원</h2>
<table>{share count, 자사주, 배당}</table>

<h2>마진 & 성장률</h2>
<table>{YoY 변화 포함}</table>

<h2>최근 동향</h2>
<ul>{bullet points with 인용}</ul>

<h2>뉴스 스냅샷</h2>
{3-5개 최근 이벤트}

<h2>모니터링 지표</h2>
{5개 quantitative monitors}
```

모든 재무 수치는 인용 링크 필수 (data-access.md Section 4).

저장 위치를 사용자에게 알려주기.

## 10. 마무리 코멘트

2-3 문장 요약 + 정직한 평가:
- 가장 큰 리스크는 무엇인가?
- 현재 valuation이 성장 궤적 대비 합리적인가?
- 보유 시 주의할 점은?

추측성 발언은 피하고, 위에서 본 데이터에 기반.
