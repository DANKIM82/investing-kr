"""Bull / Base / Bear 시나리오 분석 skill."""

from core.renderer import (
    render_header, render_financial_table,
    wrap_html, build_financial_table_rows,
)
from core.skills.base import SkillRunner


KEY_METRICS = [
    ("revenue", "매출액"),
    ("operating_income", "영업이익"),
    ("net_income", "당기순이익"),
    ("diluted_eps", "희석EPS (원)"),
    ("operating_cash_flow", "영업활동현금흐름"),
]


class BullBearSkill(SkillRunner):
    skill_name = "bull_bear"
    skill_display_name = "Bull / Base / Bear"
    skill_md_relative_path = ".claude/skills/bull-bear/SKILL.md"
    fetch_periods = [
        "2024Q1", "2024Q2", "2024Q3", "2024Q4",
        "2025Q1", "2025Q2", "2025Q3", "2025Q4",
    ]

    def build_context(self, data: dict) -> dict:
        company = data["company"]
        fund = data["fundamentals"]
        periods = fund["periods"]
        financial_table = build_financial_table_rows(
            fund["normalized"], periods, KEY_METRICS
        )
        return {
            "company": company,
            "periods": periods,
            "quarterly_financials": financial_table,
            "currency": company.get("currency", "KRW"),
        }

    def build_prompt_schema(self) -> str:
        return """{
  "thesis_summary": "투자 thesis 한 줄 (이 회사를 보유/매수해야 하는 핵심 이유)",
  "bull_case": {
    "narrative": "Bull 시나리오 설명 (실현 시 어떤 일이 일어나는지, 100-150자)",
    "key_assumptions": ["가정 1 (구체적)", "가정 2", "가정 3"],
    "implied_metrics": "달성 시 예상 매출/이익/주가 등 (수치 포함, 통화 명시)",
    "probability_pct": "확률 추정 (예: 25)"
  },
  "base_case": {
    "narrative": "Base 시나리오 (가장 가능성 높은 경로)",
    "key_assumptions": ["가정 1", "가정 2", "가정 3"],
    "implied_metrics": "수치",
    "probability_pct": "확률 (예: 50)"
  },
  "bear_case": {
    "narrative": "Bear 시나리오 (위험 시나리오)",
    "key_assumptions": ["가정 1", "가정 2", "가정 3"],
    "implied_metrics": "수치",
    "probability_pct": "확률 (예: 25)"
  },
  "key_catalysts_to_watch": [
    "관찰해야 할 이벤트/지표 (3-5개, 시점 명시 가능하면 명시)"
  ],
  "data_quality_notes": "한계"
}"""

    def render(self, ticker: str, data: dict, analysis: dict) -> str:
        company = data["company"]
        currency = company.get("currency", "KRW")
        fund = data["fundamentals"]
        periods = fund["periods"]
        financial_table = build_financial_table_rows(
            fund["normalized"], periods, KEY_METRICS
        )

        def render_scenario(emoji, name, scen):
            assumptions = scen.get("key_assumptions", [])
            assumptions_html = "".join(f"<li>{a}</li>" for a in assumptions)
            prob = scen.get("probability_pct", "—")
            return f"""
<div class="tension">
  <div class="tension-num">{emoji}</div>
  <div class="tension-content">
    <div class="tension-headline"><strong>{name} Case</strong> &nbsp;<span class="badge">확률 {prob}%</span></div>
    <div class="tension-explanation">{scen.get('narrative', '—')}</div>
    <p style="margin: 8px 0 4px 0; font-size: 13px;"><strong>주요 가정:</strong></p>
    <ul style="margin: 4px 0;">{assumptions_html}</ul>
    <p style="margin: 8px 0 0 0; font-size: 13px;"><strong>달성 시 결과:</strong> {scen.get('implied_metrics', '—')}</p>
  </div>
</div>"""

        bull_html = render_scenario("🐂", "Bull", analysis.get("bull_case", {}))
        base_html = render_scenario("≈", "Base", analysis.get("base_case", {}))
        bear_html = render_scenario("🐻", "Bear", analysis.get("bear_case", {}))

        catalysts = analysis.get("key_catalysts_to_watch", [])
        catalysts_html = "".join(f"<li>{c}</li>" for c in catalysts)

        body = render_header(company, "Bull / Base / Bear")
        body += f"""
<div class="highlight">📍 {analysis.get('thesis_summary', '')}</div>

<h2>시나리오 분석</h2>
{bull_html}
{base_html}
{bear_html}

<h2>관찰 포인트 (Key Catalysts)</h2>
<ul>{catalysts_html}</ul>

<h2>역사적 재무 (참고)</h2>
{render_financial_table(financial_table, periods, currency=currency)}

<h2>데이터 품질 노트</h2>
<p class="data-note">{analysis.get('data_quality_notes', '—')}</p>
"""
        return wrap_html(f"{company.get('name', ticker)} ({ticker}) — Bull/Base/Bear", body)
