---
name: capital-allocation
description: 자본 배분 분석 — 자사주매입, 배당, 레버리지, 재투자 적정성 심층 분석
argument-hint: TICKER (예: 005930, AAPL, 7203)
needs_market_data: true
---

`$ARGUMENTS` 회사에 대해 자본 배분 (Capital Allocation) 심층 분석을 수행하세요.

**필수 읽기**: `../data-access.md`, `../design-system.md`

이 skill은 단일 기업 분석입니다. 정량 데이터는 `infra/free_data_kr.py` + `infra/market_data.py`에서 가져오고, 정성 분석 (경영진의 자본 배분 철학, M&A 전략 등)은 SEC 검색이 없으므로 **LLM 자체 지식으로 보수적으로** 처리합니다.

## 1. 회사 정보 + 시장 데이터

```bash
python infra/free_data_kr.py companies $ARGUMENTS
python infra/market_data.py quote $ARGUMENTS
```

캡처:
- 현재 주가, 시가총액 (yield 계산의 분모)
- 발행주식수 (diluted)
- 보고통화 (KRW / USD / JPY) — **환산하지 말고 native currency 유지**
- `latest_reported_quarter` (8분기 trailing의 anchor)

시장 데이터 미수신 시: yield 계열 (Shareholder Yield, FCF Yield, Cash/MarketCap) 은 모두 `N/A`로 표기하고 펀더멘털만으로 진행.

## 2. 8분기 Trailing 펀더멘털

`latest_reported_quarter`로부터 8분기 역산해서 분기별 연속 데이터로 pull:

```bash
python infra/free_data_kr.py fundamentals $ARGUMENTS \
  --periods 2023Q1,2023Q2,2023Q3,2023Q4,2024Q1,2024Q2,2024Q3,2024Q4 \
  --series revenue,operating_income,ebitda,depreciation_amortization,\
operating_cash_flow,capex,total_debt,cash_and_equivalents,\
short_term_investments,diluted_shares_outstanding,\
share_repurchase,dividends_paid,dividends_per_share,\
interest_expense,rd_expense,total_equity
```

(시리즈 이름은 `free_data_kr` 노출명에 맞춰 조정. 일부 시리즈가 없으면 해당 행은 비워두고 진행 — extrapolate / zero-fill 금지.)

## 3. 파생 지표 계산

각 분기마다 계산. 모든 파생값은 `(calc.)` 라벨.

**현금흐름**
- FCF = OCF − CapEx `(calc.)`
- FCF Margin = FCF / Revenue
- EBITDA = Operating Income + D&A (보고치 없을 시) `(calc.)`

**주주환원**
- Total Buybacks = share_repurchase
- Total Dividends = dividends_paid
- Total Shareholder Return = Buybacks + Dividends
- **Shareholder Yield = TTM (Buybacks + Dividends) / 현재 시가총액**
- Buyback Yield = TTM Buybacks / Market Cap
- Dividend Yield = TTM Dividends / Market Cap

> ⚠️ 단일 분기를 ×4 해서 annualize 하지 말 것. 반드시 **TTM 합 / 현재 시가총액**.

**FCF 활용**
- FCF Payout Ratio = (Buybacks + Dividends) / FCF — **>100%는 명시적으로 flag** (debt 또는 cash drawdown으로 충당)
- CapEx / Revenue
- CapEx / OCF

**레버리지**
- Net Debt = Total Debt − Cash − ST Investments `(calc.)`
- Net Debt / EBITDA (TTM EBITDA 기준)
  - EBITDA 미수신 시 (D&A가 DART finstate_all 본문에 없는 경우 발생) → **Net Debt / TTM OCF로 proxy**, 표 헤더에 "(EBITDA proxy: OCF)" 명시
- Net Debt / Equity
- Interest Coverage = Operating Income / Interest Expense
- (Cash + ST Inv) / Market Cap

**주식수 추이**
- QoQ Δ shares
- YoY Δ shares
- Implied annual buyback pace (% of float retired/year)
- 현재 페이스 유지 시 10% 매입까지 소요 연수 (pace > 0일 때만)

## 4. 정성 분석 (LLM Judgment, 보수적으로)

SEC/공시 검색 도구가 없으므로 LLM 자체 지식으로 작성. **단, 가드레일**:

- 확신하는 것만 기재. 확실하지 않은 buyback authorization 금액, payout ratio target, M&A 딜 이름은 **만들어내지 말 것**.
- 일반 framing ("배당보다 자사주매입을 우선해 왔음") 은 OK. 구체적 수치 ("2024년 3월 ₩3조 자사주 매입 결의") 는 검증 불가하면 금지.
- 검증 못 하는 경영진 발언 인용 금지. 본인 framing으로 paraphrase.
- 불확실하면 "공시 원문 미검증 — 회사 IR 자료로 재확인 필요" 라고 명시.

다룰 항목 (자신 있는 만큼만):
- 자본 배분 우선순위 (CapEx vs 배당 vs 자사주 vs M&A vs 부채상환)
- 배당 정책 (배당성장 commitment, 누진적/안정적 여부)
- M&A 철학 (bolt-on 중심 / transformational / 거의 없음)
- 최근 자본 배분 전략 변화

## 5. Historical 트렌드 분석 + 가치 판단

8분기 흐름 분석:
- 자사주매입 가속/감속 여부
- **Discipline 체크**: 분기별 매입금액 × 평균 주가 비교 → 주가 낮을 때 더 사는가 (disciplined) 높을 때 더 사는가 (less disciplined)
- 배당 성장률 (8Q CAGR if 데이터 충분)
- CapEx vs Buybacks vs Dividends vs Debt repayment 의 mix shift
- FCF conversion (OCF → FCF) 추이

**가치 창출 vs 가치 파괴 판정 — 솔직하게**:
- 펀더멘털 악화 중인데 사상최고가에서 자사주매입 → EPS는 좋아 보여도 **가치 파괴**로 명명
- CapEx / R&D 축소해서 자사주 funding → 장기 경쟁력 risk flag
- FCF Payout > 100% → 부채 또는 현금 곳간으로 funding, **지속불가**
- Implied buyback return (≈ 매입가 P/E의 역수) vs 유기적 재투자 ROIC 비교

## 6. 재투자 적정성 (Reinvestment Assessment)

8분기 재투자 지표:
- R&D 절대값 + R&D / Revenue
  - 한국 대기업 일부 (삼성전자 등) 는 R&D를 손익계산서 본문이 아닌 사업보고서 주석에 공시 → DART `finstate_all`로 수신 불가. 이 경우 **"본문 미보고 — 사업보고서 주석 재확인 필요"** 명시하고 다음 단계로
- CapEx 절대값 + CapEx / Revenue
- 비즈니스 모델에 맞는 1-2개 성장 KPI:
  - **SaaS/Cloud**: ARR, NRR, RPO, $100K+ 고객수
  - **Consumer Tech/Platform**: DAU/MAU, ARPU, 유료가입자
  - **E-commerce/Marketplace**: GMV, take rate, active buyer/seller
  - **유통**: 동일점 성장률, 점포수, 객단가
  - **통신/미디어**: 가입자, churn, ARPU, 콘텐츠 투자액
  - **하드웨어/반도체**: 출하량, ASP, capa 가동률
  - **금융**: AUM, NIM, 대출증가율
  - **제약/바이오**: 파이프라인 단계, 처방수, 점유율
  - **산업재/에너지**: 수주잔고, book-to-bill, 가동률, 생산량

`free_data_kr`에서 해당 KPI 못 가져오면 해당 항목 noting하고 skip — 만들어내지 말 것.

**적정성 판정**:
- R&D/Revenue 하락 + 자사주매입 증가 → 혁신 underinvestment 가능성
- CapEx/Revenue 하락하는데 인프라 지속투자가 필요한 비즈니스 (클라우드/제조/매장) → harvesting 의심
- 성장 KPI 악화 + 주주환원 사상최고 → red flag (성장 아니라 수확 단계)
- Peer 비교는 이 skill 범위 밖 (단일기업) — follow-up으로만 언급

**가치 창출 vs 추출 verdict** (한 단락):
회사가 장기 가치를 창출 (고ROIC 재투자 + 저평가 자사주매입 + 지속가능 배당성장) 하는가, 추출 (재투자 부족으로 프리미엄 밸류에서 자사주매입, 레버리지 통해 환원) 하는가.

## 7. 차트 생성

`infra/chart_generator.py` 활용 (있는 차트 타입에 맞춰):
- Shareholder yield trend (8Q 시계열)
- Buyback discipline scatter (분기 매입금액 vs 평균 주가)
- Capital allocation mix (분기별 stacked bar: CapEx / Buyback / Dividend / Debt repay)
- FCF Payout Ratio 추이

지원 안 되는 차트는 skip.

## 8. HTML 보고서 저장

`reports/{TICKER}_capital_allocation.html`

구조:
1. **요약** — 한 줄 핵심 스토리 ("XX는 지난 1년간 ₩X조 환원, shareholder yield X.X%, 자사주매입 가속 중") + 가치창출/추출 verdict
2. **Current Snapshot** — Market Cap, TTM FCF, FCF Yield, Shareholder Yield, Net Debt/EBITDA, Cash/MarketCap
3. **현금흐름 & FCF (8분기)** — OCF / CapEx / FCF / FCF Margin
4. **자사주매입 & 배당 (8분기)** — Buyback $ / Dividends $ / Total Return / Diluted Shares / QoQ Δ / YoY Δ
5. **Shareholder Yield 분석** — Buyback Yield / Div Yield / Total Yield / FCF Payout Ratio
6. **레버리지 & 재무상태표 (8분기)** — Cash / ST Inv / Total Debt / Net Debt / Net Debt/EBITDA / Interest Coverage
7. **자본 배분 프레임워크** — LLM 정성 분석 (불확실한 부분은 flag)
8. **재투자 적정성** — R&D, CapEx, 성장 KPI 8분기 표 + 적정성 판정 + verdict
9. **자사주매입 Discipline** — timing vs 주가, 페이스, scatter 차트
10. **M&A 활동** — LLM 지식 기반, 보수적 (가짜 딜 만들지 말 것)
11. **핵심 관찰** — 3-5개 bullet
12. **리스크** — 자본 배분 관점의 주요 리스크

모든 정량 수치는 `infra/free_data_kr` 또는 `market_data` 출처. 정성 섹션 (프레임워크, M&A) 에 특정 수치/딜명이 등장하면 LLM 추정임을 명시.

마지막에 사용자에게 저장 경로 알려주고, 한 줄 핵심 스토리로 요약.
