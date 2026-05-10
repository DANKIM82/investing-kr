---
name: research-note
description: Word 리서치 노트 (.docx)
argument-hint: TICKER
---

`$ARGUMENTS` 회사에 대한 정식 리서치 노트를 Word 문서 형식 (.docx)으로 작성하세요.

**필수 읽기**: `../data-access.md`, `../design-system.md`

## 1. 데이터 수집

다음 skills의 분석 결과를 통합:
- `tearsheet`: 회사 1페이지 요약
- `earnings`: 최근 분기 실적
- `dcf`: 가치평가
- `bull-bear`: 시나리오 분석
- `comps`: 동종업계 multiples

## 2. 리서치 노트 구조

표지 페이지:
- 회사명 (한글 + 영문)
- 티커, 시장
- 보고서 종류 (Initiation / Update / Research Note)
- 작성일, 회사명 (Prepared by)
- 투자의견 (Buy/Hold/Sell) + Target Price

### 1. Executive Summary (1페이지)
- 투자의견 + 적정가
- Investment thesis (3-5 문장)
- Catalysts (2-3개)
- 주요 리스크 (2-3개)

### 2. Company Overview
- 사업 모델
- 세그먼트별 매출 비중
- 주요 경쟁 우위

### 3. Industry Analysis
- 산업 구조
- 시장 규모 (TAM)
- 산업 성장률

### 4. Financial Analysis
- 5년 historical 추이
- 마진 추이
- 분기별 핵심 지표

### 5. Valuation
- DCF (Bull/Base/Bear)
- Comparable companies
- Football field

### 6. Catalysts & Risks
- Bull catalysts
- Bear catalysts
- Key risks

### 7. Recommendation
- 결론 + 적정가 도출
- 모니터링 항목

## 3. Word 문서 생성

`infra/docx_renderer.py` 활용:
```bash
python infra/docx_renderer.py \
  --template templates/research_note_kr.docx \
  --context reports/.tmp/{TICKER}_research_note_context.json \
  --output reports/{TICKER}_research_note.docx
```

Context JSON 구조:
```json
{
  "company": {
    "name": "삼성전자",
    "ticker": "005930",
    "market": "KR",
    "currency": "KRW"
  },
  "report": {
    "date": "2026-05-10",
    "firm_name": "Personal Research",
    "rating": "Buy",
    "target_price": 95000,
    "current_price": 78500
  },
  "executive_summary": "...",
  "sections": [
    {"title": "Company Overview", "content": "...", "tables": [...]},
    ...
  ]
}
```

## 4. 표/차트 삽입

차트는 `infra/chart_generator.py`로 PNG 생성 후 docx에 삽입.

## 5. 출력

저장 후 사용자에게 경로 알려주기. PDF로도 변환 원하면 별도 명령어 안내.

⚠️ **회사명 표기 규칙** (data-access.md Section 5): "Personal Research" 기본값. 실제 투자기관 사칭 금지.
