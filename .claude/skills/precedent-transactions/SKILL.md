---
name: precedent-transactions
description: M&A 거래 비교 (precedent transactions)
argument-hint: TICKER
---

`$ARGUMENTS` 회사와 유사한 과거 M&A 거래를 찾아 valuation 참고치 도출.

⚠️ **호환성 약함**: 과거 M&A 거래 데이터베이스는 Bloomberg/Capital IQ 같은 유료 서비스가 표준. Free 데이터로는 공개된 큰 거래만 수동 검색 가능.

**필수 읽기**: `../data-access.md`, `../design-system.md`

## 1. 회사 정보

```bash
python infra/free_data_kr.py companies $ARGUMENTS
```

산업, 사업 모델 식별.

## 2. 비슷한 과거 M&A 거래 검색

WebSearch로:
- `"{industry} M&A acquisition 2020 2021 2022 2023 2024"`
- `"{company type} private equity buyout valuation"`
- 한국: `"{산업} 인수합병 거래"` 

대상: 최근 5년 같은 산업/사업 모델의 M&A 거래.

## 3. 거래 정리

| 인수자 | 피인수자 | 발표일 | 거래 규모 | 인수 multiple (EV/Revenue, EV/EBITDA) | 거래 구조 |
|---|---|---|---|---|---|
| | | | | | |

5-10개 precedent transactions 정리.

## 4. Multiple 분석

각 거래의 multiple:
- EV / Revenue
- EV / EBITDA
- EV / FCF (가능한 경우)

Median, mean, range 계산.

## 5. 시장 환경 보정

각 거래 발표 당시:
- 금리 환경 (저금리 → 높은 multiple)
- 산업 사이클 위치
- 거래 동기 (전략적 vs 재무적)

현재 시장과 비교해서 multiple 보정 필요성.

## 6. Implied Valuation

Precedent multiples × target 회사 메트릭:
- Median EV/Revenue × target revenue = implied EV
- Median EV/EBITDA × target EBITDA = implied EV

## 7. 거래 가능성 평가

- Target이 인수 대상이 될 가능성?
- 잠재적 인수자 (전략적 / 재무적)
- 인수 프리미엄 추정 (보통 20-40%)

## 8. HTML 보고서 저장

`reports/{TICKER}_precedent_transactions.html`

⚠️ 본 보고서 한계 명시: "M&A 거래 데이터는 공개 정보만 활용. 비공개 거래 조건은 알 수 없음. 실제 인수 multiple은 거래 구조 (현금/주식/earn-out)에 따라 달라짐."
