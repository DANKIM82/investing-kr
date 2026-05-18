"""DCF v3 - 실제 시장 데이터 (주가/시총/주식수/WACC inputs) 통합.

환각 완전 제거: LLM에 실제 현재 주가와 발행주식수 제공.
Per share fair value 산출 가능 + upside/downside 비교 가능.
"""

from core.renderer import (
    render_header, render_financial_table,
    wrap_html, build_financial_table_rows,
)
from core.skills.base import SkillRunner


KEY_METRICS = [
    ("revenue", "매출액"),
    ("operating_income", "영업이익"),
    ("net_income", "당기순이익"),
    ("operating_cash_flow", "영업활동현금흐름"),
    ("capex", "CapEx"),
    ("free_cash_flow", "FCF"),
    ("total_equity", "자본총계"),
]


class DCFSkill(SkillRunner):
    skill_name = "dcf"
    skill_display_name = "DCF Valuation"
    skill_md_relative_path = ".claude/skills/dcf/SKILL.md"
    needs_market_data = True  # 시장 데이터 필요
    max_recent_quarters = 8

    def build_context(self, data: dict) -> dict:
        company = data["company"]
        fund = data["fundamentals"]
        market_data = data.get("market_data", {})
        periods = fund["periods"]

        financial_table = build_financial_table_rows(
            fund["normalized"], periods, KEY_METRICS
        )

        return {
            "company": company,
            "periods": periods,
            "quarterly_financials": financial_table,
            "currency": company.get("currency", "KRW"),
            "market_data": market_data,
            "data_notes": (
                "사전 수집: 분기 재무 + 실제 시장 데이터 (현재 주가, 시총, 발행주식수, beta, multiples, risk-free-rate). "
                "실제 시장 데이터를 기반으로 분석하라."
            ),
        }

    def build_system_prompt(self) -> str:
        """DCF 전용 - 실제 시장 데이터 활용."""
        skill_prompt = self.load_skill_prompt()
        schema = self.build_prompt_schema()
        return f"""너는 한국/미국/일본 시장 투자 리서치 애널리스트로 DCF 가치평가를 수행한다.

<skill_definition>
{skill_prompt}
</skill_definition>

🚨 핵심 규칙:
- 컨텍스트의 `market_data` 에 **실제 현재 주가, 시총, 발행주식수, beta, multiples, risk-free-rate** 가 들어있다.
- 이 실제 데이터를 **반드시 사용**하라. 가격이나 시총을 임의로 만들지 마라.
- WACC 산출 시 `market_data.beta` + `market_data.risk_free_rate` 를 사용.
- Per share fair value 산출 시 `market_data.shares_outstanding` 로 나눠라.
- 현재 주가 (`market_data.price`) 대비 upside/downside 명확히 비교.

추가 규칙:
- 가정은 제공된 분기 재무와 시장 데이터에서 합리적으로 추론.
- 통화는 company.currency 를 따른다 (KRW=조/억, USD=B/M, JPY=조엔/억엔).
- 출력은 JSON 한 덩어리. 다른 텍스트 금지.

JSON 스키마:
{schema}"""

    def build_prompt_schema(self) -> str:
        return """{
  "valuation_summary": "한 줄 결론. 현재 주가 vs base case fair value 비교 (예: '현재 $421, base $450, upside +7%')",
  "current_market_snapshot": {
    "price": "market_data.price 값 그대로",
    "market_cap": "market_data.market_cap 그대로 (B/조 단위 변환)",
    "shares_outstanding": "market_data.shares_outstanding 그대로",
    "current_pe_forward": "market_data.pe_forward 그대로"
  },
  "key_assumptions": {
    "revenue_growth_5y_cagr": "% (분기 재무 추세 + market_data.revenue_growth_yoy 참고)",
    "terminal_growth": "% (보통 시장 GDP 성장률 수준)",
    "operating_margin_target": "% (market_data.operating_margin 참고하여 타겟 설정)",
    "wacc": "% (risk_free_rate + beta × equity_risk_premium 으로 산출. equity_risk_premium 가정값 명시)",
    "tax_rate": "%"
  },
  "projection_summary": [
    {"year": "FY+1", "revenue_growth_pct": "...", "operating_margin_pct": "...", "fcf_estimate": "..."},
    {"year": "FY+2", "revenue_growth_pct": "...", "operating_margin_pct": "...", "fcf_estimate": "..."},
    {"year": "FY+3", "revenue_growth_pct": "...", "operating_margin_pct": "...", "fcf_estimate": "..."},
    {"year": "FY+4", "revenue_growth_pct": "...", "operating_margin_pct": "...", "fcf_estimate": "..."},
    {"year": "FY+5", "revenue_growth_pct": "...", "operating_margin_pct": "...", "fcf_estimate": "..."}
  ],
  "bull_case": {
    "equity_value_total": "Bull Equity Value 총액",
    "fair_value_per_share": "Equity Value ÷ shares_outstanding (실제 발행주식수 사용)",
    "upside_vs_current": "fair_value vs current price = +X%",
    "key_drivers": "낙관 요인 3개"
  },
  "base_case": {
    "equity_value_total": "Base Equity Value 총액",
    "fair_value_per_share": "...",
    "upside_vs_current": "+/-X%",
    "rationale": "기본 가정 근거"
  },
  "bear_case": {
    "equity_value_total": "Bear Equity Value 총액",
    "fair_value_per_share": "...",
    "downside_vs_current": "+/-X%",
    "key_risks": "비관 요인 3개"
  },
  "valuation_vs_multiples_check": "산출된 base case 기반 implied PE vs market_data.pe_forward 비교. 합리적인지 sanity check",
  "sensitivity_insight": "WACC ±1%p 또는 terminal growth ±0.5%p 변동 시 base case fair value 변동",
  "data_quality_notes": "DCF 한계, 추가 필요 데이터"
}"""

    def render(self, ticker: str, data: dict, analysis: dict) -> str:
        company = data["company"]
        currency = company.get("currency", "KRW")
        fund = data["fundamentals"]
        periods = fund["periods"]
        market_data = data.get("market_data", {})

        financial_table = build_financial_table_rows(
            fund["normalized"], periods, KEY_METRICS
        )

        # Market snapshot
        snapshot = analysis.get("current_market_snapshot", {})
        snapshot_html = ""
        if market_data.get("available"):
            currency_symbol = {"USD": "$", "KRW": "₩", "JPY": "¥"}.get(currency, "")
            snapshot_html = f"""
<table>
<thead><tr><th>지표</th><th>현재값</th></tr></thead>
<tbody>
  <tr><td><strong>현재 주가</strong></td><td>{currency_symbol}{market_data.get('price', '?'):,.2f}</td></tr>
  <tr><td><strong>시가총액</strong></td><td>{currency_symbol}{(market_data.get('market_cap') or 0)/1e9:,.1f}B</td></tr>
  <tr><td><strong>발행주식수</strong></td><td>{(market_data.get('shares_outstanding') or 0)/1e9:,.2f}B 주</td></tr>
  <tr><td><strong>Forward PE</strong></td><td>{market_data.get('pe_forward', '?'):.1f}x</td></tr>
  <tr><td><strong>EV/EBITDA</strong></td><td>{market_data.get('ev_ebitda', '?'):.1f}x</td></tr>
  <tr><td><strong>Beta</strong></td><td>{market_data.get('beta', '?'):.2f}</td></tr>
  <tr><td><strong>Risk-Free Rate</strong></td><td>{(market_data.get('risk_free_rate') or 0)*100:.2f}%</td></tr>
</tbody>
</table>"""

        # Assumptions
        assumptions = analysis.get("key_assumptions", {})
        assumption_labels = {
            "revenue_growth_5y_cagr": "5Y 매출 성장 (CAGR)",
            "terminal_growth": "영구 성장률",
            "operating_margin_target": "목표 영업이익률",
            "wacc": "WACC",
            "tax_rate": "유효세율",
        }
        assumptions_html = "".join(
            f"<tr><td><strong>{assumption_labels.get(k, k)}</strong></td><td>{v}</td></tr>"
            for k, v in assumptions.items()
        )

        # Projections
        projections = analysis.get("projection_summary", [])
        proj_html = ""
        if projections:
            proj_headers = "".join(f"<th>{p.get('year', '?')}</th>" for p in projections)
            proj_rows = (
                "<tr><td><strong>매출 성장률</strong></td>"
                + "".join(f"<td>{p.get('revenue_growth_pct', '—')}</td>" for p in projections)
                + "</tr>"
                "<tr><td><strong>영업이익률</strong></td>"
                + "".join(f"<td>{p.get('operating_margin_pct', '—')}</td>" for p in projections)
                + "</tr>"
                "<tr><td><strong>FCF (추정)</strong></td>"
                + "".join(f"<td>{p.get('fcf_estimate', '—')}</td>" for p in projections)
                + "</tr>"
            )
            proj_html = f"""
<table>
<thead><tr><th>지표</th>{proj_headers}</tr></thead>
<tbody>{proj_rows}</tbody>
</table>"""

        bull = analysis.get("bull_case", {})
        base = analysis.get("base_case", {})
        bear = analysis.get("bear_case", {})

        body = render_header(company, "DCF Valuation")
        body += f"""
<div class="highlight">💰 {analysis.get('valuation_summary', '')}</div>

<h2>현재 시장 스냅샷</h2>
{snapshot_html if snapshot_html else '<p class="data-note">시장 데이터 미수집</p>'}

<h2>핵심 가정</h2>
<table>
<thead><tr><th>가정</th><th>값 + 근거</th></tr></thead>
<tbody>{assumptions_html}</tbody>
</table>

<h2>5년 Projection</h2>
{proj_html}

<h2>시나리오별 Fair Value</h2>
<div class="tension">
  <div class="tension-num">🐂</div>
  <div class="tension-content">
    <div class="tension-headline"><strong>Bull Case:</strong> {bull.get('fair_value_per_share', '—')} / 주 (총 {bull.get('equity_value_total', '—')})</div>
    <div class="tension-explanation"><strong>{bull.get('upside_vs_current', '—')}</strong> · {bull.get('key_drivers', '—')}</div>
  </div>
</div>
<div class="tension">
  <div class="tension-num">≈</div>
  <div class="tension-content">
    <div class="tension-headline"><strong>Base Case:</strong> {base.get('fair_value_per_share', '—')} / 주 (총 {base.get('equity_value_total', '—')})</div>
    <div class="tension-explanation"><strong>{base.get('upside_vs_current', '—')}</strong> · {base.get('rationale', '—')}</div>
  </div>
</div>
<div class="tension">
  <div class="tension-num">🐻</div>
  <div class="tension-content">
    <div class="tension-headline"><strong>Bear Case:</strong> {bear.get('fair_value_per_share', '—')} / 주 (총 {bear.get('equity_value_total', '—')})</div>
    <div class="tension-explanation"><strong>{bear.get('downside_vs_current', '—')}</strong> · {bear.get('key_risks', '—')}</div>
  </div>
</div>

<h2>Multiples Sanity Check</h2>
<p>{analysis.get('valuation_vs_multiples_check', '—')}</p>

<h2>민감도 인사이트</h2>
<p>{analysis.get('sensitivity_insight', '—')}</p>

<h2>역사적 재무 데이터</h2>
{render_financial_table(financial_table, periods, currency=currency)}

<h2>데이터 품질 노트</h2>
<p class="data-note">{analysis.get('data_quality_notes', '—')}</p>
"""
        return wrap_html(f"{company.get('name', ticker)} ({ticker}) — DCF", body)
