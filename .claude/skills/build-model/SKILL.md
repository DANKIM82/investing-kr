---
name: build-model
description: Excel 재무 모델 (.xlsx)
argument-hint: TICKER
---

`$ARGUMENTS` 회사의 다중 탭 Excel 재무 모델 생성.

**필수 읽기**: `../data-access.md`, `../design-system.md`

## 1. 데이터 수집

5-7년 historical 데이터 수집 (연간 기준):
```bash
python infra/free_data_kr.py fundamentals $ARGUMENTS \
  --periods 2019Q4,2020Q4,2021Q4,2022Q4,2023Q4,2024Q4
```

(각 분기는 그 해의 연간값으로 변환 — 또는 4개 분기 합산)

## 2. Excel 모델 구조

`infra/excel_builder.py`로 multi-tab Excel 생성:

### Tab 1: Cover
- 모델 제목, 회사명, 티커, 통화, 작성일

### Tab 2: Assumptions
- WACC 가정, terminal growth, 세율
- 시나리오 토글 (Bull/Base/Bear)
- 환율 (다국가의 경우)

### Tab 3: Income Statement (Historical + Projected)
| 항목 | FY-5 | FY-4 | FY-3 | FY-2 | FY-1 | FY+0 | FY+1 | FY+2 | FY+3 | FY+4 | FY+5 |
- 매출 (성장률 sub-row)
- 매출원가 (% of revenue)
- 매출총이익
- 판관비 (% of revenue)
- 영업이익
- 영업이익률
- 이자비용
- 세전이익
- 세금
- 순이익

Forward projection은 가정값 link (Tab 2 참조).

### Tab 4: Balance Sheet
- 자산: 현금, 매출채권, 재고, 유형자산, 무형자산
- 부채: 매입채무, 단기차입금, 장기차입금
- 자본: 자본금, 이익잉여금
- 검증: 자산 = 부채 + 자본

### Tab 5: Cash Flow Statement
- 영업활동: 순이익 + D&A + WC 변화
- 투자활동: CapEx
- 재무활동: 차입, 배당, 자사주
- 현금 변화

### Tab 6: DCF
- 5년 FCF projection
- WACC 계산
- Terminal value
- Enterprise Value → Equity Value → 주당가치
- 민감도 표 (WACC × terminal growth)

### Tab 7: Trading Multiples
- TTM/NTM P/E, EV/EBITDA, P/S
- 5년 historical multiple range

### Tab 8: Charts
- 매출 추이
- 마진 추이
- FCF 추이

## 3. Excel 생성

```bash
python infra/excel_builder.py \
  --context reports/.tmp/{TICKER}_model_context.json \
  --output reports/{TICKER}_model.xlsx
```

## 4. 모델 검증

생성 후 다음을 확인:
- Balance Sheet 균형
- Cash Flow → Balance Sheet 현금 변화 일치
- Forward projection의 합리성 (sanity check)

## 5. 저장 + 사용자 안내

`reports/{TICKER}_model.xlsx`. 저장 위치 + 핵심 가정 요약 알려주기.

⚠️ **한계**: free 데이터의 historical depth 한계 (5년 정도). 더 깊은 historical은 사업보고서 직접 입력 필요.
