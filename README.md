# investing-kr

> 한국 / 미국 / 일본 주식을 위한 무료 투자 분석 툴킷
> Claude Code 기반, DART + yfinance + SEC EDGAR 데이터 사용

[![Markets](https://img.shields.io/badge/markets-KR%20%7C%20US%20%7C%20JP-blue)]()
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

## 무엇을 만드는가

[daloopa/investing](https://github.com/daloopa/investing)을 fork해서 Daloopa MCP 의존성을 무료 데이터 소스로 교체하고, 한국 / 미국 / 일본 3개 시장으로 확장한 버전입니다.

**16개 분석 skills + 5개 결과물 skills** = 총 **21개의 Claude Code slash commands**.

```
/tearsheet 005930      → 삼성전자 1페이지 요약
/tearsheet AAPL        → Apple 1페이지 요약
/tearsheet 7203        → Toyota 1페이지 요약
/dcf 005930            → 삼성전자 DCF 가치평가
/initiate 005930       → 삼성전자 신규 커버리지 (Word + Excel)
```

티커 형식만 보고 어느 시장인지 자동 감지합니다.

---

## 빠른 시작 (5분)

### 1. Repo Clone

```powershell
cd C:\!Workspace\Project
git clone https://github.com/YOUR_USERNAME/investing-kr.git
cd investing-kr
```

### 2. Python 패키지 설치

```powershell
pip install -r requirements.txt
```

### 3. API 키 설정

```powershell
copy .env.example .env
notepad .env
```

`.env`에서 다음 값 입력:
- `DART_API_KEY`: [opendart.fss.or.kr](https://opendart.fss.or.kr) 가입 후 발급
- `SEC_USER_AGENT`: `"이름 your@email.com"` 형식
- `FRED_API_KEY`: 옵션 (없으면 default 4.5% 사용)

### 4. 동작 확인

각 시장별 1개씩 테스트:

```powershell
# 한국
python infra/free_data_kr.py companies 005930

# 미국
python infra/free_data_kr.py companies AAPL

# 일본
python infra/free_data_kr.py companies 7203
```

각각 회사 정보가 JSON으로 출력되면 OK.

### 5. Claude Code 실행

```powershell
claude
```

이어서 slash command 사용:

```
/tearsheet 005930
```

---

## 주요 기능

### 시장 자동 감지

티커 형식만으로 시장 식별:

| 입력 | 시장 | 데이터 소스 |
|---|---|---|
| `005930` (6자리) | 🇰🇷 한국 | DART + pykrx |
| `삼성전자` (한글) | 🇰🇷 한국 | DART + pykrx |
| `AAPL` (영문) | 🇺🇸 미국 | yfinance + SEC EDGAR |
| `7203` (4자리) | 🇯🇵 일본 | yfinance |
| `7203.T` | 🇯🇵 일본 | yfinance |

명시적 지정: `--market KR/US/JP`

### 21개 분석 Skills

#### Tier 1: 핵심 분석 (🟢 호환성 좋음)
- `/tearsheet TICKER` — 1페이지 회사 요약
- `/earnings TICKER` — 분기 실적 분석
- `/earnings-prep TICKER` — 실적 발표 전 준비
- `/earnings-flash TICKER` — 실적 발표 직후 빠른 분석
- `/bull-bear TICKER` — Bull/Base/Bear 시나리오
- `/dcf TICKER` — DCF 가치평가 + 민감도
- `/comps TICKER` — Trading multiples peer 비교
- `/industry TICKER1 TICKER2 ...` — 다회사 비교
- `/inflection TICKER` — 추세 변화 자동 감지
- `/capital-allocation TICKER` — 자사주/배당/CapEx 분석
- `/working-capital TICKER` — 운전자본 분석

#### Tier 2: 보조 분석 (🟡 부분 호환)
- `/guidance-tracker TICKER` — 가이던스 정확도 추적
- `/comp-sheet TICKER` — Excel 다회사 비교 모델

#### Tier 3: 한계 있는 분석 (🔴 데이터 한계)
- `/unit-economics TICKER` — 단위경제 (KPI 의존)
- `/supply-chain TICKER` — 공급망 분석 (제한적)
- `/precedent-transactions TICKER` — M&A 거래 비교 (수동)

#### 통합 결과물
- `/research-note TICKER` — Word 리서치 노트
- `/build-model TICKER` — Excel 재무 모델
- `/initiate TICKER` — 신규 커버리지 (Word + Excel)
- `/update TICKER` — 기존 커버리지 업데이트
- `/ib-deck TICKER` — IB 스타일 PowerPoint

---

## 사용 예시

### 예시 1: 삼성전자 Tearsheet

```
> /tearsheet 005930
```

생성:
- `reports/005930_tearsheet.html`

내용:
- 회사 개요 (DART 기반)
- 5대 Bull/Bear tensions
- 최근 8분기 매출/이익 추이
- 사업부별 매출 (반도체/MX/DS/SDC 등)
- 자사주/배당
- 모니터링 지표 5개

### 예시 2: Apple DCF

```
> /dcf AAPL
```

생성:
- `reports/AAPL_dcf.html`

내용:
- 5년 historical
- Bull/Base/Bear projection
- WACC 계산 (ERP 5.5%, 21% 세율)
- Terminal value (Gordon)
- 민감도 매트릭스 (heatmap)
- Football field

### 예시 3: 한미일 반도체 비교

```
> /industry 005930 INTC 7735
```

(삼성전자, Intel, SCREEN Holdings)

생성:
- `reports/005930_INTC_7735_industry.html`

내용:
- 매출 성장률 비교 차트
- 영업이익률 비교
- ROE / ROIC
- Quality vs Valuation 매트릭스

### 예시 4: NAVER 신규 커버리지

```
> /initiate 035420
```

생성:
- `reports/035420_initiation.docx` — 정식 리서치 노트
- `reports/035420_model.xlsx` — 5년 재무 모델

---

## 한국 시장 특이사항

### DART 분기 구조

| Quarter | DART 보고서 | 코드 |
|---|---|---|
| Q1 | 1분기보고서 | 11013 |
| Q2 | 반기보고서 | 11012 |
| Q3 | 3분기보고서 | 11014 |
| Q4 | 사업보고서 (연간) | 11011 |

### K-IFRS 메트릭

`free_data_kr.py`는 K-IFRS 표준 라벨을 사용합니다:
- `revenue` → 매출액
- `operating_income` → 영업이익
- `net_income` → 당기순이익
- 등등

전체 목록: `python infra/free_data_kr.py series 005930`

### 회사명 → 종목코드 자동 변환

```bash
python infra/free_data_kr.py companies 삼성전자
# → 005930.KS 정보 출력
```

### 한국식 숫자 포맷

- `2.5조원 (₩2.5tn)`
- `2,345억원 (₩234bn)`
- `1,250원` (EPS 등)

---

## 미국 시장 특이사항

### SEC EDGAR Full-Text Search

```bash
python infra/free_data_kr.py documents "AI revenue" --tickers AAPL --forms 10-K,10-Q
```

10-K, 10-Q, 8-K 등 본문 검색.

### 회계연도 차이

회사별로 회계연도 종료월 다름. `companies` 응답의 `fiscal_year_end_month` 확인:
- Apple: 9월
- Microsoft: 6월
- Nike: 5월

---

## 일본 시장 특이사항

### 4자리 종목코드 + .T

- `7203` → Toyota (자동으로 `.T` 추가됨)
- `9984.T` → SoftBank Group
- `8035.T` → Tokyo Electron

### 회계연도

일본 대부분의 회사는 3월말 결산 (한국/미국과 다름).

### 데이터 한계

J-Quants를 쓰지 않으면 yfinance만 사용. 일본어 공시 본문 검색 불가. 큰 회사 위주로만 안정적.

---

## 디렉토리 구조

```
investing-kr/
├── .claude/
│   └── skills/
│       ├── data-access.md           # 마스터 데이터 reference
│       ├── design-system.md         # 포맷/스타일 가이드
│       ├── tearsheet/SKILL.md       # 21개 분석 skills
│       ├── earnings/SKILL.md
│       ├── ...
├── infra/
│   ├── free_data_kr.py              # ⭐ 데이터 wrapper (KR/US/JP)
│   ├── market_data.py               # 시세 + multiples
│   ├── chart_generator.py           # 차트 (matplotlib)
│   ├── docx_renderer.py             # Word 생성
│   ├── excel_builder.py             # Excel 생성
│   ├── pdf_renderer.py              # PDF 생성
│   ├── comp_builder.py              # Comp sheet Excel
│   └── projection_engine.py         # 5년 forward projection + DCF
├── templates/                       # docx 템플릿
├── reports/                         # 결과물 (gitignore됨)
│   └── .tmp/                        # 임시 context JSON
├── scripts/                         # 헬퍼 스크립트
├── .env.example                     # 환경변수 예시
├── requirements.txt                 # Python 의존성
├── CLAUDE.md                        # Claude Code 행동 가이드
├── .gitignore
└── README.md                        # 이 파일
```

---

## API 키 발급 가이드

### DART API (필수, 한국 데이터)

1. [opendart.fss.or.kr](https://opendart.fss.or.kr) 접속
2. 우측 상단 "회원가입" → 이메일 인증
3. 로그인 후 "인증키 신청/관리" → "인증키 신청"
4. 신청 후 즉시 발급됨
5. `.env`의 `DART_API_KEY=` 뒤에 키 입력

### SEC User-Agent (필수, 미국 데이터)

별도 등록 불요. SEC 정책상 정상적인 이메일 주소만 있으면 됨:
```
SEC_USER_AGENT=Personal Research yourname@example.com
```

### FRED API (옵션, 미국 거시 데이터)

1. [fred.stlouisfed.org](https://fred.stlouisfed.org) 가입
2. My Account → API Keys → Request New Key
3. `.env`의 `FRED_API_KEY=` 뒤에 입력

미설정 시 DCF에서 무위험금리 default 4.5% 사용.

### J-Quants (옵션, 일본 상세 데이터)

1. [jpx-jquants.com](https://jpx-jquants.com) 가입
2. Free tier: 12주 지연 데이터 제공
3. Refresh token을 `.env`에 저장

미설정 시 yfinance로만 사용 (제한적).

---

## 알려진 한계

### 데이터 측면

- **한국**: DART는 분기/반기/연간만 (월별 없음). 일부 중소형주는 분기 데이터 부족.
- **미국**: yfinance 5년 historical. Consensus 추정치 일부만 제공.
- **일본**: yfinance만 사용 시 큰 회사 위주.
- **공통**: Audit-grade 정확도 보장 안 됨.

### 분석 측면

- 일부 skills (unit-economics, supply-chain, precedent-transactions)는 비공개 KPI 또는 거래 데이터에 의존하므로 **결과 품질 제한적**
- 회사별 KPI는 본문 검색으로만 추출 가능 (수동 검증 권장)
- 국제 비교 시 FX 자동 환산 안 됨

### 결과물 측면

- IB-deck (PPT)은 골격만 자동 생성. 디자인 마감 필요.
- DCF의 가정 (성장률, 마진)은 사용자가 검증/조정 권장.

---

## 자주 묻는 질문

**Q. Daloopa 원본과 비교하면?**
A. 데이터 정확도와 historical depth는 Daloopa가 우수. 이 repo는 무료 + 한일 시장 추가 + Claude Code 친화적 구조.

**Q. 실제 투자에 써도 되나요?**
A. **아니요**. 학습/사이드프로젝트 용도. 실제 투자 결정은 audit-grade 데이터 기반으로.

**Q. 회사명 표기는?**
A. `.env`의 `FIRM_NAME`으로 변경. 기본값 "Personal Research". 실제 투자기관 사칭 금지.

**Q. 결과 파일은 어디에?**
A. `reports/` 디렉토리. HTML / Word / Excel 형식.

**Q. 일본 종목 검색이 잘 안 돼요.**
A. yfinance의 일본 데이터 한계. 큰 회사 (시총 10조원 이상) 위주로 사용 권장. J-Quants 가입 시 더 나음.

**Q. 한국 회사명을 영어로 입력하면?**
A. `Samsung Electronics`는 안 되고, `삼성전자` 또는 `005930`으로 입력. 영어 검색은 미국 시장으로 라우팅됨.

---

## 라이선스

MIT License. 원본 [daloopa/investing](https://github.com/daloopa/investing)의 fork.

---

## 면책

이 도구는 학습 및 연구 목적으로만 제공됩니다. 투자 자문이 아니며, 투자 결정에 따른 모든 책임은 사용자 본인에게 있습니다. 데이터의 정확성을 보장하지 않습니다.

---

## 관련 자료

- [원본 daloopa/investing](https://github.com/daloopa/investing)
- [DART 전자공시](https://dart.fss.or.kr)
- [Claude Code 문서](https://docs.claude.com/en/docs/claude-code)
- [OpenDartReader](https://github.com/FinanceData/OpenDartReader)
- [pykrx](https://github.com/sharebook-kr/pykrx)
- [yfinance](https://github.com/ranaroussi/yfinance)

---

**Generated**: 2026-05-10
**Markets supported**: 🇰🇷 KR + 🇺🇸 US + 🇯🇵 JP
**Skills**: 21
**Status**: Educational use only
