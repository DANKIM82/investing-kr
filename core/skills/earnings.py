"""Earnings skill."""

from core.renderer import (
    render_header, render_financial_table, render_metrics_table,
    wrap_html, build_financial_table_rows,
)
from core.skills.base import SkillRunner


KEY_METRICS = [
    ("revenue", "매출액"),
    ("gross_profit", "매출총이익"),
    ("operating_income", "영업이익"),
    ("net_income", "당기순이익"),
    ("diluted_eps", "희석EPS (원)"),
    ("operating_cash_flow", "영업활동현금흐름"),
]


class EarningsSkill(SkillRunner):
    skill_name = "earnings"
    skill_display_name = "Earnings Review"
    skill_md_relative_path = ".claude/skills/earnings/SKILL.md"
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

        latest = periods[-1] if periods else None
        prior = periods[-2] if len(periods) >= 2 else None
        yoy = None
        if latest:
            prev_year = str(int(latest[:4]) - 1) + latest[4:]
            if prev_year in periods:
                yoy = prev_year

        return {
            "company": company,
            "periods": periods,
            "latest_quarter": latest,
            "prior_quarter": prior,
            "yoy_quarter": yoy,
            "quarterly_financials": financial_table,
            "currency": company.get("currency", "KRW"),
            "analysis_focus": f"최근 분기 {latest}의 QoQ({prior}) 및 YoY({yoy}) 변동에 집중",
            "data_notes": f"통화: {company.get('currency', 'KRW')}. 정규화된 분기값.",
        }

    def build_prompt_schema(self) -> str:
        return """{
  "headline_summary": "최근 분기 헤드라인 한 줄 (수치 + 통화 단위 명시)",
  "key_takeaways": [
    "최근 분기 핵심 takeaway 한 줄"
  ],
  "revenue_analysis": {
    "magnitude": "매출 규모 + QoQ/YoY",
    "drivers": "성장/감소 원인",
    "vs_consensus": "컨센서스 대비 (데이터 부족 시 'N/A')"
  },
  "margin_analysis": {
    "summary": "마진 추이 한 줄",
    "key_drivers": "마진 변동 원인"
  },
  "cash_flow_quality": "OCF 품질 평가",
  "monitoring_for_next_quarter": [
    {"metric": "지표명", "rationale": "왜 중요"}
  ],
  "data_quality_notes": "한계"
}"""

    def render(self, ticker: str, data: dict, analysis: dict) -> str:
        company = data["company"]
        currency = company.get("currency", "KRW")
        fund = data["fundamentals"]
        periods = fund["periods"]
        latest = periods[-1] if periods else "?"

        financial_table = build_financial_table_rows(
            fund["normalized"], periods, KEY_METRICS
        )

        takeaways_html = "".join(f"<li>{t}</li>" for t in analysis.get("key_takeaways", []))
        revenue = analysis.get("revenue_analysis", {})
        margin = analysis.get("margin_analysis", {})

        body = render_header(company, "Earnings Review")
        body += f"""
<div class="highlight">
  <span class="badge">{latest}</span>
  &nbsp;{analysis.get('headline_summary', '')}
</div>

<h2>핵심 Takeaway</h2>
<ul>{takeaways_html}</ul>

<h2>매출 분석</h2>
<p><strong>규모:</strong> {revenue.get('magnitude', '—')}</p>
<p><strong>요인:</strong> {revenue.get('drivers', '—')}</p>
<p><strong>vs 컨센서스:</strong> {revenue.get('vs_consensus', '—')}</p>

<h2>마진 분석</h2>
<p>{margin.get('summary', '—')}</p>
<p><strong>요인:</strong> {margin.get('key_drivers', '—')}</p>

<h2>현금흐름 품질</h2>
<p>{analysis.get('cash_flow_quality', '—')}</p>

<h2>분기별 재무 데이터</h2>
{render_financial_table(financial_table, periods, currency=currency)}

<h2>다음 분기 모니터링</h2>
{render_metrics_table(analysis.get('monitoring_for_next_quarter', []))}

<h2>데이터 품질 노트</h2>
<p class="data-note">{analysis.get('data_quality_notes', '—')}</p>
"""
        return wrap_html(f"{company.get('name', ticker)} ({ticker}) — Earnings", body)
