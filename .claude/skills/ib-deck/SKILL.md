---
name: ib-deck
description: IB-스타일 PowerPoint 발표 자료
argument-hint: TICKER
---

`$ARGUMENTS` 회사에 대한 IB (Investment Banking) 스타일 PowerPoint 자료 생성.

⚠️ **호환성 약함**: 이 skill은 `pptx` Python 라이브러리 + 차트 통합 + 이미지 생성이 필요. 기본 골격만 생성하고 사용자가 보완 필요.

**필수 읽기**: `../data-access.md`, `../design-system.md`

## 1. 데이터 수집

다음 skills의 결과물 활용:
- `tearsheet`: 회사 개요
- `dcf`: 가치평가
- `comps`: peer 비교
- `bull-bear`: 시나리오

## 2. PowerPoint 구조 (12-15 슬라이드)

### Slide 1: Cover
- 회사 로고 (옵션), 회사명, 티커
- 보고서 유형 (Investment Recommendation)
- 작성일, Prepared by {FIRM_NAME}

### Slide 2: Executive Summary
- 투자의견 + 적정가
- 4-5 bullet thesis
- 현재가 대비 upside

### Slide 3: Company Overview
- 회사 소개 (왼쪽: 사업 설명, 오른쪽: key metrics)
- 사업 모델 다이어그램

### Slide 4: Financial Highlights
- 5년 매출/이익 추이 차트
- 마진 추이
- ROE / ROIC

### Slide 5: Industry Overview
- TAM 차트
- 시장 점유율 추이
- 경쟁 구도

### Slide 6: Investment Thesis
- 3-5개 thesis pillars
- 각 pillar의 supporting data

### Slide 7: Valuation - DCF
- DCF 결과 표
- WACC 가정
- Terminal value

### Slide 8: Valuation - Comps
- Peer multiples 표
- 산점도 (Growth vs P/E)

### Slide 9: Football Field
- DCF / Comps / 52w / Target prices 시각화

### Slide 10: Bull / Bear Scenarios
- 3 시나리오 표
- 확률가중 적정가

### Slide 11: Catalysts
- 6-12개월 기대 catalyst
- 시점별 정렬

### Slide 12: Risks
- Top 5 리스크
- 각 리스크의 mitigant

### Slide 13: Recommendation
- 결론 + 적정가
- 모니터링 항목

### Slide 14: Appendix
- 상세 재무 historical
- 주요 가정

## 3. 생성 (수동 단계)

PPTX 자동 생성은 복잡하므로:

옵션 A: HTML 슬라이드 (`reports/{TICKER}_ib_deck.html`)
- reveal.js 또는 단순 HTML 슬라이드
- 데이터/차트 포함

옵션 B: PPTX 골격 + 사용자 보완
- `python-pptx` 활용
- 텍스트 + 표 자동 생성
- 사용자가 디자인 마감

## 4. 출력

기본: HTML 형식으로 저장 → `reports/{TICKER}_ib_deck.html`
PPTX 원하면: `pip install python-pptx` 설치 후 별도 변환.

⚠️ 본 skill 한계 명시: "최종 IB-quality 자료는 디자인 마감이 필요. 자동 생성은 데이터 + 골격까지."
