---
name: comp-sheet
description: 다회사 비교 Excel 모델 (comp sheet)
argument-hint: TICKER
---

`$ARGUMENTS` 회사를 중심으로 같은 산업 peer 5-10개를 비교하는 Excel 모델 생성.

**필수 읽기**: `../data-access.md`, `../design-system.md`

## 1. Target + Peer 식별

```bash
python infra/free_data_kr.py companies $ARGUMENTS
```

`industry` 기반으로 peer 5-10개 선정 (`/comps` skill의 peer 가이드 참조).

## 2. 각 회사 데이터 수집

각 회사 × 최근 8분기:
```bash
python infra/free_data_kr.py fundamentals TICKER \
  --periods Q-7,...,Q+0 \
  --series revenue,gross_profit,operating_income,ebitda,net_income,diluted_eps,operating_cash_flow,capex,total_debt,cash_and_equivalents,total_equity
```

각 회사 multiples:
```bash
python infra/market_data.py multiples TICKER
```

## 3. 통화 정규화 (다국가일 경우)

USD 기준으로 환산. yfinance에서 환율 조회.

## 4. Excel 컴포 시트 구성

`infra/comp_builder.py` 활용해서 multi-tab Excel 생성:

### Tab 1: Cover
- 시트 제목, 회사 리스트, 생성일, 출처

### Tab 2: Trading Multiples
| 회사 | Mkt Cap | EV | P/E (TTM) | P/E (NTM) | EV/EBITDA (TTM) | EV/EBITDA (NTM) | P/S | P/B | DivYield |
|---|---|---|---|---|---|---|---|---|---|

각 회사 행 + Median/Mean 행.

### Tab 3: Operating Metrics
| 회사 | Revenue (TTM) | Rev Growth (1Y) | Rev Growth (3Y CAGR) | Gross Margin | OPM | EBITDA Margin | Net Margin | ROE | ROIC |

### Tab 4: Quality Metrics
| 회사 | Net Debt/EBITDA | Interest Coverage | FCF Margin | FCF/Net Income | CapEx/Revenue |

### Tab 5: 4-Quarter Trend (Target 회사)
| Q-3 | Q-2 | Q-1 | Q+0 |
- 매출, 마진, 성장률 등

### Tab 6: 4-Quarter Trend (각 Peer 별 sub-tab)
같은 형식으로 peer 1, peer 2, ...

### Tab 7: Visual Comparison
- 산점도 데이터 (성장률 vs P/E)
- Bar chart 데이터 (마진 비교)

### Tab 8: Notes
- Peer 선정 근거
- 데이터 출처
- 한계점

## 5. 저장

`reports/{TICKER}_comp_sheet.xlsx`

```bash
python infra/comp_builder.py --context context.json --output reports/{TICKER}_comp_sheet.xlsx
```

## 6. HTML 보충 요약

같은 데이터로 HTML summary도 함께:
`reports/{TICKER}_comp_sheet_summary.html`

핵심 발견 5개 + key visualization.
