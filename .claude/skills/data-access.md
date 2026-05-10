# 데이터 액세스 가이드 (Data Access Reference)

이 파일은 모든 분석 skill이 데이터를 가져올 때 참조하는 마스터 reference입니다. 포맷팅과 스타일 규칙은 `design-system.md` 참조.

---

## ⚠️ 한계점 우선 안내

이 툴킷은 **학습/사이드프로젝트용**입니다. 다음 한계가 있습니다:

- 한국: DART (감사받은 재무제표) — 분기/반기/연간만 (월별 데이터 없음)
- 미국: yfinance + SEC EDGAR — Daloopa 대비 historical depth, KPI 부족
- 일본: yfinance만 — 회사별 KPI, 일본어 공시 본문 검색 한계
- 모든 시장: Consensus estimates 매우 제한적
- Audit-grade 정확도 보장 안 됨

실제 투자 결정에는 사용 금지.

---

## Section 1: 통합 데이터 wrapper

`infra/free_data_kr.py`가 한국/미국/일본 3개 시장을 자동 감지해서 처리합니다.

### 시장 자동 감지 규칙

| 입력 형식 | 시장 | 예시 |
|---|---|---|
| 6자리 숫자 | 한국 (KR) | `005930` (삼성전자) |
| 한글 회사명 | 한국 (KR) | `삼성전자` |
| `XXXXXX.KS`, `XXXXXX.KQ` | 한국 (KR) | `005930.KS` |
| 4자리 숫자 또는 `XXXX.T` | 일본 (JP) | `7203` (Toyota) |
| 영문 알파벳 (1-5자) | 미국 (US) | `AAPL` |

자동 감지 결과를 명시적으로 override하고 싶으면 `--market KR/US/JP` 플래그 사용.

### 4개 핵심 명령어

| 작업 | 명령어 |
|---|---|
| 회사 정보 조회 | `python infra/free_data_kr.py companies TICKER` |
| 사용 가능 메트릭 목록 | `python infra/free_data_kr.py series TICKER --keywords KEYWORD` |
| 재무 데이터 조회 | `python infra/free_data_kr.py fundamentals TICKER --periods 2024Q1,2024Q2 --series revenue,net_income` |
| 공시/Filing 검색 | `python infra/free_data_kr.py documents "QUERY" --tickers TICKER` |

모든 출력은 JSON (UTF-8, 한글 그대로 보존).

### 시장별 데이터 소스

| 시장 | 회사 정보 | 재무 데이터 | 공시 검색 |
|---|---|---|---|
| 한국 (KR) | pykrx + DART | DART (감사보고서, 분기/반기/사업보고서) | DART (정기공시) |
| 미국 (US) | yfinance + SEC EDGAR | yfinance | SEC EDGAR full-text search |
| 일본 (JP) | yfinance | yfinance (.T suffix) | (제한적, yfinance에서 가능한 범위) |

### 사용 가능한 Series ID

#### 한국 (K-IFRS 기반)

| series_id | 한글 라벨 | 영문 라벨 |
|---|---|---|
| `revenue` | 매출액 | Revenue |
| `cost_of_revenue` | 매출원가 | Cost of Revenue |
| `gross_profit` | 매출총이익 | Gross Profit |
| `sga` | 판매비와관리비 | SG&A |
| `operating_income` | 영업이익 | Operating Income |
| `interest_expense` | 이자비용 | Interest Expense |
| `pretax_income` | 법인세차감전순이익 | Pretax Income |
| `tax_expense` | 법인세비용 | Tax Expense |
| `net_income` | 당기순이익 | Net Income |
| `diluted_eps` | 희석주당이익 | Diluted EPS |
| `basic_eps` | 기본주당이익 | Basic EPS |
| `cash_and_equivalents` | 현금및현금성자산 | Cash & Equivalents |
| `current_assets` | 유동자산 | Current Assets |
| `inventory` | 재고자산 | Inventory |
| `trade_receivables` | 매출채권 | Trade Receivables |
| `total_assets` | 자산총계 | Total Assets |
| `current_liabilities` | 유동부채 | Current Liabilities |
| `long_term_debt` | 장기차입금 | Long-term Debt |
| `total_liabilities` | 부채총계 | Total Liabilities |
| `total_equity` | 자본총계 | Total Equity |
| `operating_cash_flow` | 영업활동현금흐름 | Operating Cash Flow |
| `capex` | 유형자산취득 | CapEx |
| `dividends_paid` | 배당금지급 | Dividends Paid |

**계산 항목** (직접 산출 필요):
- `ebitda` = 영업이익 + 감가상각비
- `free_cash_flow` = 영업활동현금흐름 - 유형자산취득
- `gross_margin` = 매출총이익 / 매출액
- `operating_margin` = 영업이익 / 매출액
- `net_margin` = 당기순이익 / 매출액

#### 미국/일본 (US GAAP / yfinance 기반)

위 한국 series_id와 거의 동일. 추가로:
- `total_debt`, `share_repurchases`, `diluted_shares`, `basic_shares`, `free_cash_flow` (yfinance 직접 제공)

전체 목록은 `python infra/free_data_kr.py series TICKER` 명령어로 확인.

---

## Section 2: 분기 (Period) 처리

### 분기 표기

모든 시장 공통으로 `YYYYQ#` 형식 사용 (예: `2024Q1`, `2025Q4`).

### 시장별 분기 의미 차이

| 시장 | Q1 | Q2 | Q3 | Q4 |
|---|---|---|---|---|
| 한국 | 1분기보고서 (1-3월) | 반기보고서 (4-6월) | 3분기보고서 (7-9월) | 사업보고서 (연간) |
| 미국 | 1-3월 (대부분) | 4-6월 | 7-9월 | 10-12월 |
| 일본 | (회사별 회계연도 다양, 3월말 결산이 다수) | | | |

**중요**: 회사 정보 조회 시 반환되는 `latest_calendar_quarter`를 기준으로 모든 period 계산. 현재 날짜로 추측하지 말 것.

### 자주 쓰는 period 계산

| 분석 요구사항 | 계산 방법 |
|---|---|
| 최근 4분기 | `latest_calendar_quarter`에서 4Q 역산 |
| 최근 8분기 | `latest_calendar_quarter`에서 8Q 역산 |
| YoY 비교 | 최근 4Q + 1년 전 같은 4Q (총 8Q) |
| 5년 추이 | 최근 20Q |

예시: `latest_calendar_quarter` = "2025Q4"이면 최근 8Q = `["2024Q1", ..., "2024Q4", "2025Q1", ..., "2025Q4"]`

---

## Section 3: 시장 데이터 (가격, 시가총액, 멀티플)

`infra/market_data.py` 사용:

| 작업 | 명령어 |
|---|---|
| 현재 시세 | `python infra/market_data.py quote TICKER` |
| Trading multiples | `python infra/market_data.py multiples TICKER` |
| 과거 가격 | `python infra/market_data.py history TICKER --period 2y` |
| Peer 비교 | `python infra/market_data.py peers TICKER1 TICKER2 ...` |
| 무위험금리 (10Y 국채) | `python infra/market_data.py risk-free-rate` |

한국은 pykrx, 미국/일본은 yfinance 사용. 자동 라우팅됨.

---

## Section 4: 인용 (Citation) 규칙 (필수)

**모든 재무 수치는 출처 링크를 포함해야 합니다.** 예외 없음.

### 한국 (DART)

```
[2.5조원 (₩2.5tn)](https://dart.fss.or.kr/dsab007/main.do?option=corp&textCrpNm=005930)
```

`fundamentals` 응답의 `source_url` 필드를 그대로 사용.

### 미국 (yfinance + SEC EDGAR)

```
[$94.93bn](https://finance.yahoo.com/quote/AAPL/financials)
```

SEC 문서 인용:
```
[10-K filing](https://www.sec.gov/Archives/edgar/data/0000320193/000032019324000123/aapl-20240928.htm)
```

`documents` 응답의 `url` 필드를 그대로 사용.

### 일본 (yfinance)

```
[¥1.5조 (¥1.5tn)](https://finance.yahoo.com/quote/7203.T/financials)
```

### 정직성 원칙

데이터를 찾을 수 없으면 **추측하지 말 것**. "n/a — 공개 데이터 미존재"로 표시. 인용 못 하는 숫자는 출력하지 말 것.

---

## Section 5: 회사 표시명 (Firm Attribution)

모든 결과물에 "Prepared by {FIRM_NAME}" 표시:
- **기본값**: "Personal Research" (학습용)
- **사용자 지정**: 프롬프트에서 회사명 명시 시 그것 사용
- **금지**: 실제 투자기관 이름 사칭 (Goldman, Morgan Stanley, KB증권, 미래에셋 등)

HTML 푸터: `Prepared by {FIRM_NAME} | Data: DART, yfinance, SEC EDGAR`

---

## Section 6: 인프라 도구 (project repo 전용)

### 차트 생성

`python infra/chart_generator.py {chart_type} --data '{json}' --output path.png`

차트 종류: `time-series`, `waterfall`, `football-field`, `pie`, `scenario-bar`, `dcf-sensitivity`

### 결과물 렌더링

| 형식 | 명령어 |
|---|---|
| Word | `python infra/docx_renderer.py --template templates/research_note_kr.docx --context context.json --output output.docx` |
| Excel | `python infra/excel_builder.py --context context.json --output output.xlsx` |
| PDF | `python infra/pdf_renderer.py --markdown report.md --output output.pdf` |

### Building block skills의 HTML 출력

별도 스크립트 불필요. `design-system.md`의 HTML 템플릿 사용해서 직접 작성. 결과물은 `reports/{TICKER}_{skill}.html`에 저장.

---

## Section 7: 알려진 한계점 (반드시 보고서에 명시)

1. **한국 분기 데이터의 분기성**: DART 분기/반기 보고서는 회사가 자율 공시하므로 일부 회사는 분기 데이터 없음 (사업보고서만)
2. **세그먼트/지역별 데이터**: 구조화된 형태로 제공 안 됨. 본문 검색으로 추출 필요
3. **회사별 KPI**: 구독자 수, ARR 등은 본문에서 직접 추출 필요
4. **Historical 깊이**:
   - DART: 2015년 이후 안정적
   - yfinance: 4-5년 정도
5. **Restated/수정 재공시**: 반영 안 될 수 있음
6. **국제 비교**: 통화 환산은 사용자가 직접 (FX는 yfinance에서 별도 조회)

모든 보고서 하단에 출처 라인 명시:
`Source: DART (한국) / yfinance + SEC EDGAR (미국) / yfinance (일본). Data quality not audit-grade.`
