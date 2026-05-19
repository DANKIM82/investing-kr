"""Industry skill v2 - 최대 5개 회사 peer 비교.
v2 변경:
- 분기 표에 회사명 (ticker 대신) 표시
- LLM prompt가 최근 분기 (Q3, Q4) 중심 분석하도록 가이드 추가
- 회사 한 줄 평에 ticker + name 함께 표시
"""

from core.data_fetcher import get_company, get_fundamentals, get_market_data
from core.renderer import render_header, wrap_html
from core.skills.base import SkillRunner


COMPARE_METRICS = [
    ("revenue", "매출액"),
    ("gross_profit", "매출총이익"),
    ("operating_income", "영업이익"),
    ("net_income", "당기순이익"),
    ("operating_cash_flow", "영업활동현금흐름"),
    ("free_cash_flow", "FCF"),
]

FX_TO_USD = {
    "USD": 1.0,
    "KRW": 1.0 / 1370.0,
    "JPY": 1.0 / 155.0,
    "EUR": 1.10,
}


def _to_usd(value, currency):
    if value is None:
        return None
    rate = FX_TO_USD.get(currency, 1.0)
    return value * rate


def _short_name(name, max_len=20):
    """회사명이 너무 길면 자르기."""
    if not name:
        return "?"
    if len(name) > max_len:
        return name[:max_len-1] + "…"
    return name


class IndustrySkill(SkillRunner):
    skill_name = "industry"
    skill_display_name = "Industry Comparison"
    skill_md_relative_path = ".claude/skills/industry/SKILL.md"
    needs_market_data = True
    max_recent_quarters = 8

    def __init__(self, tickers: list[str] | None = None):
        self.tickers = tickers or []
        if len(self.tickers) > 5:
            raise ValueError("최대 5개 회사까지만 비교 가능")
        if len(self.tickers) < 2:
            raise ValueError("최소 2개 회사가 필요")

    def fetch_data(self, ticker: str = None) -> dict:
        companies_data = []

        for t in self.tickers:
            print(f"  → {t} fetch 중...")
            company = get_company(t)
            fundamentals = get_fundamentals(t, periods=None)

            if fundamentals.get("periods"):
                recent = fundamentals["periods"][-self.max_recent_quarters:]
                fundamentals["periods"] = recent
                fundamentals["normalized"] = {
                    s: {p: v for p, v in pv.items() if p in recent}
                    for s, pv in fundamentals["normalized"].items()
                }

            market_data = get_market_data(t)
            currency = company.get("currency", "USD")

            normalized_usd = {}
            for series_id, period_values in fundamentals.get("normalized", {}).items():
                if series_id in ("diluted_eps", "basic_eps", "diluted_shares"):
                    normalized_usd[series_id] = dict(period_values)
                else:
                    normalized_usd[series_id] = {
                        p: _to_usd(v, currency)
                        for p, v in period_values.items()
                    }

            companies_data.append({
                "ticker": t,
                "company": company,
                "fundamentals_usd": {
                    "periods": fundamentals.get("periods", []),
                    "normalized": normalized_usd,
                    "market": fundamentals.get("market"),
                },
                "market_data": market_data,
                "original_currency": currency,
            })

        return {"companies": companies_data, "ticker_list": self.tickers}

    def build_context(self, data: dict) -> dict:
        companies = []
        all_periods = set()

        for c in data["companies"]:
            fund = c["fundamentals_usd"]
            all_periods.update(fund["periods"])

            quarterly = {}
            for series_id, label in COMPARE_METRICS:
                quarterly[series_id] = {
                    p: fund["normalized"].get(series_id, {}).get(p)
                    for p in fund["periods"]
                }

            md = c["market_data"]
            companies.append({
                "ticker": c["ticker"],
                "name": c["company"].get("name", c["ticker"]),
                "market": fund.get("market"),
                "original_currency": c["original_currency"],
                "industry": c["company"].get("industry", "—"),
                "quarterly_usd_billions": {
                    label: {p: round(v / 1e9, 2) if v else None for p, v in pv.items()}
                    for (sid, label), pv in zip(COMPARE_METRICS, [quarterly[sid] for sid, _ in COMPARE_METRICS])
                },
                "market_snapshot": {
                    "price": md.get("price"),
                    "market_cap_usd_b": round((md.get("market_cap") or 0) * FX_TO_USD.get(c["original_currency"], 1.0) / 1e9, 2) if md.get("market_cap") else None,
                    "pe_forward": md.get("pe_forward"),
                    "ev_ebitda": md.get("ev_ebitda"),
                    "ev_revenue": md.get("ev_revenue"),
                    "profit_margin": md.get("profit_margin"),
                    "operating_margin": md.get("operating_margin"),
                    "roe": md.get("roe"),
                    "revenue_growth_yoy": md.get("revenue_growth_yoy"),
                    "beta": md.get("beta"),
                },
            })

        # 최근 분기 명시 (LLM에 강조)
        sorted_periods = sorted(all_periods)
        latest = sorted_periods[-1] if sorted_periods else None
        prior = sorted_periods[-2] if len(sorted_periods) >= 2 else None

        return {
            "companies": companies,
            "all_periods": sorted_periods,
            "latest_quarter": latest,
            "prior_quarter": prior,
            "analysis_focus": (
                f"분석은 가장 최근 분기 ({latest}) 와 직전 분기 ({prior}) 에 집중. "
                "오래된 분기 (2025Q1, Q2) 의 변동은 부차적. "
                "단, 추세 (improving / deteriorating) 를 보여줄 때만 과거 분기 참고."
            ),
            "data_notes": "모든 재무 수치는 USD 환산 (KRW 1370, JPY 155). EPS는 원본 단위. 시장 데이터는 실시간.",
        }

    def build_prompt_schema(self) -> str:
        return """{
  "industry_overview": "산업 개요 200-300자",
  "leader_laggard_analysis": {
    "leader": "ticker + 회사명 + 최근 분기 (Q3/Q4) 수치 기반 leader 선정 이유",
    "laggard": "ticker + 회사명 + 최근 분기 수치 기반 laggard 선정 이유. 오래된 분기 (Q1, Q2) 위주 분석 금지",
    "wildcards": "흥미로운 outlier 1-2개 (최근 분기 기준)"
  },
  "competitive_dynamics": [
    {"theme": "테마", "observation": "최근 분기 (Q3, Q4) 수치 위주 관찰. 트렌드 보여줄 때만 과거 참고"}
  ],
  "valuation_comparison": {
    "summary": "PE forward, EV/EBITDA 기준 멀티플 비교 한 줄",
    "key_observations": "흥미로운 valuation 관찰 2-3개"
  },
  "company_one_liners": [
    {"ticker": "...", "tagline": "한 줄 평 (최근 분기 + 회사 고유 특징)"}
  ],
  "monitoring_metrics": [
    {"metric": "지표", "rationale": "왜 중요"}
  ],
  "data_quality_notes": "한계"
}"""

    def build_system_prompt(self) -> str:
        """Industry 전용 시스템 프롬프트. 최근 분기 강조."""
        skill_prompt = self.load_skill_prompt()
        schema = self.build_prompt_schema()
        return f"""너는 한국/미국/일본 시장 투자 리서치 애널리스트로 peer group 비교 분석을 수행한다.

<skill_definition>
{skill_prompt}
</skill_definition>

🚨 분석 시점 규칙 (중요):
- **분석의 80%는 가장 최근 분기 (latest_quarter) 와 직전 분기 (prior_quarter) 에 집중**.
- 과거 분기 (예: 2025Q1, Q2) 는 **추세 비교** 목적으로만 짧게 인용. 오래된 변동을 길게 분석하지 말 것.
- Leader/Laggard 선정 시 반드시 **최근 분기 수치** 기반.
- 예: "2025Q1→Q2 변동" 같은 과거 추이는 부차적. "Q3→Q4 추이" 가 1차.

기타 규칙:
- 제공된 데이터의 실제 수치를 직접 인용.
- 추측 금지. 데이터에 없으면 만들지 마라.
- 통화 단위는 USD 통일 ($XX.XB 형식).
- 출력은 JSON 한 덩어리. 다른 텍스트 금지.

JSON 스키마:
{schema}"""

    def render(self, ticker: str, data: dict, analysis: dict) -> str:
        companies = data["companies"]
        all_periods = sorted({p for c in companies for p in c["fundamentals_usd"]["periods"]})
        recent_periods = all_periods[-4:]

        company_one_liners = {ol["ticker"]: ol["tagline"] for ol in analysis.get("company_one_liners", [])}

        # 회사 헤더: ticker + 짧은 회사명 (밸류에이션 표용)
        company_headers = "".join(
            f"<th><div style='font-weight: 600;'>{c['ticker']}</div>"
            f"<div style='font-size: 11px; color: #666 !important; font-weight: normal;'>{_short_name(c['company'].get('name', '?'))}</div></th>"
            for c in companies
        )

        def format_pct(v):
            if v is None:
                return "—"
            return f"{v*100:.1f}%" if abs(v) < 5 else f"{v:.1f}"

        def format_num(v, suffix=""):
            if v is None:
                return "—"
            return f"{v:.1f}{suffix}"

        market_rows = ""
        market_rows += "<tr><td><strong>시가총액 (USD)</strong></td>"
        for c in companies:
            mcap = c["market_data"].get("market_cap")
            fx = FX_TO_USD.get(c["original_currency"], 1.0)
            mcap_usd_b = (mcap * fx / 1e9) if mcap else None
            market_rows += f"<td>{format_num(mcap_usd_b, 'B')}</td>"
        market_rows += "</tr>"

        for label, key, is_pct in [
            ("PE Forward", "pe_forward", False),
            ("EV/EBITDA", "ev_ebitda", False),
            ("EV/Revenue", "ev_revenue", False),
            ("영업이익률", "operating_margin", True),
            ("ROE", "roe", True),
            ("매출 YoY 성장", "revenue_growth_yoy", True),
            ("Beta", "beta", False),
        ]:
            market_rows += f"<tr><td><strong>{label}</strong></td>"
            for c in companies:
                v = c["market_data"].get(key)
                if is_pct:
                    market_rows += f"<td>{format_pct(v)}</td>"
                else:
                    market_rows += f"<td>{format_num(v, 'x' if 'PE' in label or 'EV' in label else '')}</td>"
            market_rows += "</tr>"

        # 분기 재무 데이터 (USD billions) - 회사명 표시
        quarterly_section = ""
        for series_id, label in COMPARE_METRICS:
            quarterly_section += f"<h3 style='font-size: 14px; margin-top: 20px; color: #1a4480 !important;'>{label} (USD Billions)</h3>"
            quarterly_section += "<table><thead><tr><th style='min-width: 240px;'>회사</th>"
            for p in recent_periods:
                quarterly_section += f"<th>{p}</th>"
            quarterly_section += "</tr></thead><tbody>"

            for c in companies:
                normalized = c["fundamentals_usd"]["normalized"]
                series_data = normalized.get(series_id, {})
                # ticker + 회사명 같이 표시
                ticker_str = c["ticker"]
                name_str = c["company"].get("name", "?")
                quarterly_section += (
                    f"<tr><td>"
                    f"<strong>{name_str}</strong>"
                    f"<span style='color: #666 !important; font-size: 11px;'> ({ticker_str})</span>"
                    f"</td>"
                )
                for p in recent_periods:
                    v = series_data.get(p)
                    if v is None:
                        quarterly_section += "<td>—</td>"
                    else:
                        quarterly_section += f"<td>${v/1e9:,.2f}B</td>"
                quarterly_section += "</tr>"
            quarterly_section += "</tbody></table>"

        # 회사별 한 줄 평
        taglines_html = ""
        for c in companies:
            tagline = company_one_liners.get(c["ticker"], "—")
            taglines_html += f"""
            <div class="tension">
              <div class="tension-num" style="font-size: 14px; min-width: 60px;">{c['ticker']}</div>
              <div class="tension-content">
                <div class="tension-headline"><strong>{c['company'].get('name', '?')}</strong></div>
                <div class="tension-explanation">{tagline}</div>
              </div>
            </div>"""

        dynamics_html = ""
        for d in analysis.get("competitive_dynamics", []):
            dynamics_html += f"""
            <div style="margin: 10px 0; padding: 10px; border-left: 3px solid #1a4480; background: #f5f7fa !important;">
              <strong style="color: #1a4480 !important;">{d.get('theme', '')}</strong><br>
              <span style="color: #222 !important;">{d.get('observation', '')}</span>
            </div>"""

        ll = analysis.get("leader_laggard_analysis", {})
        leader_html = f"""
<div class="highlight">
  🏆 <strong>Leader:</strong> {ll.get('leader', '—')}
</div>
<div class="highlight" style="background: #fee7e7 !important; color: #5a1818 !important;">
  ⚠ <strong>Laggard:</strong> {ll.get('laggard', '—')}
</div>"""
        if ll.get("wildcards"):
            leader_html += f"""
<div class="highlight" style="background: #fff4e0 !important; color: #5a3818 !important;">
  🃏 <strong>Wildcard:</strong> {ll.get('wildcards', '—')}
</div>"""

        vc = analysis.get("valuation_comparison", {})

        monitoring_html = ""
        for m in analysis.get("monitoring_metrics", []):
            monitoring_html += f"<tr><td><strong>{m.get('metric', '')}</strong></td><td>{m.get('rationale', '')}</td></tr>"

        title = " vs ".join(c["ticker"] for c in companies) + " — Industry Comparison"

        # 비교 회사 명단 표시
        roster_html = "<div style='margin: 16px 0; padding: 12px; background: #f0f4f8 !important; border-radius: 4px;'>"
        roster_html += "<strong style='color: #222 !important;'>비교 대상:</strong> "
        roster_html += " · ".join(
            f"<span style='color: #1a4480 !important;'>{c['company'].get('name', '?')}</span> "
            f"<span style='color: #666 !important; font-size: 12px;'>({c['ticker']})</span>"
            for c in companies
        )
        roster_html += "</div>"

        body = f"""
<h1>{title}</h1>
<div class="meta">생성일: {__import__('datetime').datetime.now().strftime('%Y-%m-%d')} · 통화: USD 환산 ($1=₩1,370=¥155)</div>
<div class="disclaimer">⚠ 학습·참고용. 실제 투자 결정에 사용 금지.</div>

{roster_html}

<h2>산업 개요</h2>
<div class="overview">{analysis.get('industry_overview', '')}</div>

<h2>Leader / Laggard</h2>
{leader_html}

<h2>경쟁 역학</h2>
{dynamics_html if dynamics_html else '<p>—</p>'}

<h2>밸류에이션 비교</h2>
<table>
<thead><tr><th>지표</th>{company_headers}</tr></thead>
<tbody>{market_rows}</tbody>
</table>
<p style="margin-top: 12px;"><strong>요약:</strong> {vc.get('summary', '—')}</p>
<p><strong>주요 관찰:</strong> {vc.get('key_observations', '—')}</p>

<h2>분기별 재무 비교 (최근 4분기)</h2>
{quarterly_section}

<h2>회사별 한 줄 평</h2>
{taglines_html}

<h2>다음 분기 모니터링</h2>
<table><thead><tr><th>지표</th><th>중요성</th></tr></thead><tbody>{monitoring_html}</tbody></table>

<h2>데이터 품질 노트</h2>
<p class="data-note">{analysis.get('data_quality_notes', '—')}</p>
"""
        return wrap_html(title, body)

    def run(self, ticker_or_list=None, model="claude-sonnet-4-6", max_tokens=5000, validate=False):
        identifier = "_vs_".join(self.tickers)
        print(f"[1/4] Industry 비교: {' vs '.join(self.tickers)}")

        data = self.fetch_data()

        print(f"\n[3/4] Claude API 호출 ({model})...")
        context = self.build_context(data)
        system_prompt = self.build_system_prompt()

        import json
        user_message = f"""다음 데이터로 {' vs '.join(self.tickers)} industry comparison 분석을 작성하라.

🚨 분석은 최근 분기 ({context.get('latest_quarter')}, {context.get('prior_quarter')}) 중심.
과거 분기는 추세 보여줄 때만 짧게 참고.

<pre_fetched_data>
{json.dumps(context, ensure_ascii=False, indent=2, default=str)}
</pre_fetched_data>"""

        from core.llm_client import call_claude
        response = call_claude(
            system_prompt=system_prompt,
            user_message=user_message,
            model=model,
            max_tokens=max_tokens,
        )

        print(f"\n[4/4] HTML 렌더링...")
        html = self.render(identifier, data, response.analysis)

        from pathlib import Path
        REPO_ROOT = Path(__file__).parent.parent.parent
        safe_id = "_vs_".join(self.tickers).replace("/", "_")
        output_path = REPO_ROOT / "reports" / f"industry_{safe_id}.html"
        output_path.parent.mkdir(exist_ok=True)
        output_path.write_text(html, encoding="utf-8")

        print(f"\n완료 → {output_path}")
        t = response.tokens
        print(f"  Cost: ${response.cost:.4f}")

        return {
            "ticker": identifier,
            "skill": self.skill_name,
            "data": data,
            "analysis": response.analysis,
            "output_path": str(output_path),
            "cost": response.cost,
            "tokens": response.tokens,
        }
