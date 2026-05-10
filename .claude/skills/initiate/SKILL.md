---
name: initiate
description: 신규 커버리지 시작 (Word + Excel 동시 생성)
argument-hint: TICKER
---

`$ARGUMENTS` 회사의 신규 커버리지 보고서 + 모델을 동시에 생성.

**필수 읽기**: `../data-access.md`, `../design-system.md`

## 작업 흐름

이 skill은 다음 4개를 순차 실행한 후 결과를 통합:

### 1단계: Tearsheet 생성
`/tearsheet $ARGUMENTS` skill 실행 → HTML

### 2단계: DCF 가치평가
`/dcf $ARGUMENTS` skill 실행 → 적정가 도출

### 3단계: Comp 분석
`/comps $ARGUMENTS` skill 실행 → peer 비교

### 4단계: Bull/Bear 시나리오
`/bull-bear $ARGUMENTS` skill 실행 → 시나리오 분석

## 통합 결과물

### Word 리서치 노트
`/research-note $ARGUMENTS` 형식으로 모든 분석 통합 → `.docx`

### Excel 모델
`/build-model $ARGUMENTS` 형식으로 5년 projection 모델 → `.xlsx`

## 출력

- `reports/{TICKER}_initiation.docx` — 정식 리서치 노트
- `reports/{TICKER}_model.xlsx` — 5년 재무 모델
- `reports/.tmp/{TICKER}_initiate_context.json` — 미래 update 시 사용할 컨텍스트

## Initiation 보고서의 차별점

일반 research-note와 달리, initiation에는 다음이 강조됨:
- **Investment Thesis**: 명확한 3-5문장 thesis
- **Why Now?**: 지금 시점에 cover 시작하는 이유
- **Variant Perception**: 시장 컨센서스와 다른 관점
- **Scenario Tree**: Bull/Base/Bear 확률가중

## 사용자 안내

생성 완료 후:
- 두 파일 위치 알려주기
- 핵심 conclusions 3-5 줄 요약
- 모니터링 항목 5개 제시
