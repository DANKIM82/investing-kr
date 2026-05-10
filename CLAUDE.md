# Claude Code 행동 가이드

이 파일은 Claude Code가 이 repo에서 작업할 때 따라야 할 규칙입니다. Claude Code 호출 시 자동으로 읽힙니다.

---

## 핵심 원칙

### 1. 데이터 소스
**모든 재무/시장 데이터는 `infra/free_data_kr.py`와 `infra/market_data.py`만 사용**합니다. 기억에서 답하지 말 것. 매 분석마다 fresh data 호출.

### 2. 시장 자동 감지
ticker 형식으로 시장 자동 감지:
- 6자리 숫자 → 한국 (KR)
- 4자리 또는 `.T` → 일본 (JP)
- 영문 (1-5자) → 미국 (US)

명시적 override는 `--market KR/US/JP` 플래그로.

### 3. 출력 언어
**한영 혼용**:
- 본문: 한국어 위주
- 메트릭 라벨: 한글(영문) 병기 (예: "매출액 (Revenue)")
- 숫자 단위: 한국 단위 + 영문 단위 병기 (예: "2.5조원 (₩2.5tn)")

### 4. 인용 (Citation) 의무
**모든 재무 수치는 반드시 출처 링크 포함**:
- 한국: DART URL
- 미국: yfinance / SEC EDGAR URL
- 일본: yfinance URL

인용 못하는 숫자는 출력하지 말 것.

### 5. 회사명 표기
- 기본값: "Personal Research"
- `.env`의 `FIRM_NAME`으로 변경 가능
- **금지**: 실제 투자기관 이름 사칭 (KB증권, 미래에셋, Goldman Sachs 등)

### 6. 한계 명시
모든 보고서 하단에:
```
Source: DART (한국) / yfinance + SEC EDGAR (미국) / yfinance (일본)
Disclaimer: 학습/연구 목적. 투자 자문 아님. Audit-grade 정확도 보장 안 됨.
```

---

## Skill 호출 흐름

사용자가 `/tearsheet 005930` 같은 slash command를 입력하면:

1. Claude Code가 `.claude/skills/tearsheet/SKILL.md`를 읽음
2. SKILL.md가 `../data-access.md` 참조하라고 지시
3. Claude가 두 파일의 규칙에 따라 분석 수행
4. 결과는 `reports/` 디렉토리에 저장

---

## 데이터 호출 패턴

### 회사 정보
```bash
python infra/free_data_kr.py companies $TICKER
```

### 재무 데이터 (분기)
```bash
python infra/free_data_kr.py fundamentals $TICKER \
  --periods 2024Q1,2024Q2,2024Q3,2024Q4 \
  --series revenue,operating_income,net_income
```

### 공시 검색
```bash
# 한국 (DART 정기공시)
python infra/free_data_kr.py documents "키워드" --tickers $TICKER --year 2024

# 미국 (SEC EDGAR full-text search)
python infra/free_data_kr.py documents "keyword" --tickers $TICKER --forms 10-K,10-Q
```

### 시세 / Multiples
```bash
python infra/market_data.py quote $TICKER
python infra/market_data.py multiples $TICKER
python infra/market_data.py history $TICKER --period 2y
```

---

## 출력물 저장 규칙

| 결과물 종류 | 저장 위치 | 파일명 패턴 |
|---|---|---|
| HTML 보고서 (building blocks) | `reports/` | `{TICKER}_{skill_name}.html` |
| Word 리서치 노트 | `reports/` | `{TICKER}_research_note.docx` 또는 `{TICKER}_initiation.docx` |
| Excel 모델 | `reports/` | `{TICKER}_model.xlsx` 또는 `{TICKER}_comp_sheet.xlsx` |
| 임시 컨텍스트 JSON | `reports/.tmp/` | `{TICKER}_*_context.json` |
| 차트 이미지 | `reports/.tmp/charts/` | `{TICKER}_{chart}.png` |

저장 후 사용자에게 정확한 경로 알려주기.

---

## 자주 하는 실수 방지

### ❌ 하지 말 것
- 학습 데이터에서 답하기 (가격, 실적은 fresh 호출)
- "찾을 수 없으면 추측" (n/a 표기가 정직)
- 영어 단위만 표기 (한영 혼용 원칙 위반)
- 표지 페이지 없이 결과 던지기 (회사명/날짜/firm 명시 필수)
- 공시 URL 없이 인용

### ✅ 해야 할 것
- 매번 `companies` 명령으로 `latest_calendar_quarter` 확인
- 시장 자동 감지 결과 검증 (애매하면 `--market` 사용)
- 데이터 부족 시 솔직하게 명시 + 한계 표시
- 모든 가정 (WACC, 성장률 등) 명시적 표기
- 에러 발생 시 stderr 메시지 사용자에게 전달

---

## 한계점 (반드시 인지)

1. **실시간성 부족**: yfinance, DART는 분기 단위. 실시간 데이터 아님
2. **Historical depth**: yfinance ~5년, DART 2015년 이후 안정적
3. **Consensus 추정치**: yfinance에서 일부만 제공. Bloomberg/Refinitiv 수준 아님
4. **한국 분기 데이터**: 일부 회사는 분기 보고 안 함 (반기/연간만)
5. **세그먼트/지역별**: 구조화된 데이터 없음. 본문 검색으로 추출
6. **회사별 KPI**: 사업보고서/10-K 본문에서 직접 추출 필요
7. **국제 비교**: FX 자동 환산 안 됨. 통화 명시 필수

---

## 새 분석을 시작할 때 체크리스트

1. ✅ `companies $TICKER` 호출해서 시장/회계연도 확인
2. ✅ `latest_calendar_quarter` 기준으로 분기 계산
3. ✅ 적절한 series_id 식별 (`series` 명령으로 확인)
4. ✅ 한영 혼용으로 표 작성
5. ✅ 모든 수치에 인용 링크
6. ✅ 결과물에 Prepared by + 출처 + Disclaimer
7. ✅ `reports/` 디렉토리에 저장
8. ✅ 사용자에게 저장 경로 안내
