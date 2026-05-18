"""Tearsheet skill."""

from core.renderer import (
    render_header, render_tensions, render_financial_table,
    render_metrics_table, wrap_html, build_financial_table_rows,
)
from core.skills.base import SkillRunner


KEY_METRICS = [
    ("revenue", "매출액"),
    ("gross_profit", "매출총이익"),
    ("operating_income", "영업이익"),
    ("pretax_income", "법인세전이익"),
    ("net_income", "당기순이익"),
    ("diluted_eps", "희석EPS (원)"),  # 통화별 자동 변환됨 (원→$/¥)
    ("operating_cash_flow", "영업활동현금흐름"),
    ("cash_and_equivalents", "현금성자산"),
    ("total_assets", "자산총계"),
    ("total_equity", "자본총계"),
]


class TearsheetSkill(SkillRunner):
    skill_name = "tearsheet"
    skill_display_name = "Tearsheet"
    skill_md_relative_path = ".claude/skills/tearsheet/SKILL.md"
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

        yoy_pairs = []
        for p in periods:
            prev = str(int(p[:4]) - 1) + p[4:]
            if prev in periods:
                yoy_pairs.append({"current": p, "prior": prev})

        return {
            "company": company,
            "periods": periods,
            "quarterly_financials": financial_table,
            "yoy_comparison_pairs": yoy_pairs,
            "currency": company.get("currency", "KRW"),
            "data_notes": f"통화: {company.get('currency', 'KRW')}. 분기값 정규화 적용 (KR: IS Q4 누적 차감 + CF 분기 차분 + net_income pretax-tax 추정 / US·JP: yfinance/SEC raw).",
        }

    def build_prompt_schema(self) -> str:
        return """{
  "company_overview": "회사 개요 200-300자 (YoY 변화나 분기 추이 인용, 통화 단위 명시)",
  "key_tensions": [
    {"bull": "긍정 한 줄", "bear": "부정 한 줄", "explanation": "100-150자, 수치+YoY 인용"}
  ],
  "monitoring_metrics": [
    {"metric": "지표명", "rationale": "왜 중요한지 한 줄"}
  ],
  "data_quality_notes": "데이터 한계, 추가 필요 데이터"
}"""

    def render(self, ticker: str, data: dict, analysis: dict) -> str:
        company = data["company"]
        currency = company.get("currency", "KRW")
        fund = data["fundamentals"]
        periods = fund["periods"]

        financial_table = build_financial_table_rows(
            fund["normalized"], periods, KEY_METRICS
        )

        body = render_header(company, "Tearsheet")
        body += f"""
<h2>회사 개요</h2>
<div class="overview">{analysis.get('company_overview', '')}</div>

<h2>5대 Key Tensions</h2>
{render_tensions(analysis.get('key_tensions', []))}

<h2>분기별 재무 데이터 — 최근 {len(periods)}분기</h2>
<p class="data-note">{'KR: IS Q4 누적 차감 + CF 분기 차분 + net_income 추정 보완.' if fund.get('market') == 'KR' else f"시장: {fund.get('market', '?')} — yfinance/SEC raw 분기값."}</p>
{render_financial_table(financial_table, periods, currency=currency)}

<h2>모니터링 지표</h2>
{render_metrics_table(analysis.get('monitoring_metrics', []))}

<h2>데이터 품질 노트</h2>
<p class="data-note">{analysis.get('data_quality_notes', '—')}</p>
"""
        return wrap_html(f"{company.get('name', ticker)} ({ticker}) — Tearsheet", body)
