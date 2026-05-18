"""공통 HTML 렌더링 헬퍼들. v3: 모바일 다크모드 강제 라이트모드."""

from datetime import datetime


# 모든 색상 명시적 + !important 로 iOS Safari 다크모드 자동변환 방지
CSS = """
  :root { color-scheme: light only; }
  html, body { background: #ffffff !important; color: #222222 !important; }
  body {
    font-family: -apple-system, 'Segoe UI', sans-serif;
    max-width: 1200px;
    margin: 40px auto;
    padding: 20px;
    line-height: 1.6;
    -webkit-text-size-adjust: 100%;
  }
  h1 {
    font-size: 22px;
    color: #222222 !important;
    border-bottom: 2px solid #222222;
    padding-bottom: 8px;
  }
  h2 {
    font-size: 16px;
    margin-top: 32px;
    color: #1a4480 !important;
  }
  p, li, td, th, div, span {
    color: #222222 !important;
  }
  .meta {
    color: #555555 !important;
    font-size: 13px;
  }
  .disclaimer {
    background: #fff8e1 !important;
    color: #4a3800 !important;
    border-left: 3px solid #f9a825;
    padding: 8px 12px;
    margin: 16px 0;
    font-size: 13px;
  }
  .disclaimer * { color: #4a3800 !important; }
  .overview {
    background: #f0f4f8 !important;
    color: #222222 !important;
    padding: 16px;
    border-radius: 4px;
  }
  .tension {
    display: flex;
    gap: 12px;
    margin: 12px 0;
    padding: 10px;
    border-left: 3px solid #1a4480;
    background: #f5f7fa !important;
    color: #222222 !important;
  }
  .tension * { color: #222222 !important; }
  .tension-num {
    font-size: 18px;
    font-weight: bold;
    color: #1a4480 !important;
    min-width: 32px;
  }
  .tension-headline { font-size: 14px; }
  .tension-explanation {
    font-size: 13px;
    color: #444444 !important;
    margin-top: 4px;
  }
  table {
    width: 100%;
    border-collapse: collapse;
    margin: 12px 0;
    font-size: 12px;
    background: #ffffff !important;
  }
  th, td {
    padding: 5px 8px;
    border: 1px solid #dddddd;
    text-align: right;
    background: #ffffff !important;
    color: #222222 !important;
  }
  th:first-child, td:first-child { text-align: left; }
  th {
    background: #f0f0f0 !important;
    font-weight: 600;
  }
  tbody tr:hover { background: #fafafa !important; }
  .data-note {
    font-size: 12px;
    color: #666666 !important;
    font-style: italic;
  }
  .badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 3px;
    font-size: 11px;
    background: #1a4480 !important;
    color: #ffffff !important;
  }
  .highlight {
    background: #e7f3ff !important;
    color: #0d2c54 !important;
    padding: 14px;
    border-radius: 4px;
    font-size: 15px;
    font-weight: 600;
    margin: 16px 0;
  }
  .highlight * { color: #0d2c54 !important; }
  ul { padding-left: 24px; }
  ul li {
    margin: 6px 0;
    color: #222222 !important;
  }

  /* iOS Safari 다크모드 강제 비활성화 */
  @media (prefers-color-scheme: dark) {
    html, body { background: #ffffff !important; color: #222222 !important; }
    h1, h2, h3, p, li, td, th, div, span { color: #222222 !important; }
    .meta { color: #555555 !important; }
    .data-note { color: #666666 !important; }
    .tension-explanation { color: #444444 !important; }
    .badge { color: #ffffff !important; }
    .highlight, .highlight * { color: #0d2c54 !important; }
    .disclaimer, .disclaimer * { color: #4a3800 !important; }
  }
"""


CURRENCY_UNITS = {
    "KRW": {
        "eps_label": "원",
        "scales": [(1e12, "조"), (1e8, "억")],
    },
    "USD": {
        "eps_label": "$",
        "scales": [(1e9, "B"), (1e6, "M"), (1e3, "K")],
    },
    "JPY": {
        "eps_label": "¥",
        "scales": [(1e12, "조엔"), (1e8, "억엔")],
    },
    "EUR": {
        "eps_label": "€",
        "scales": [(1e9, "B"), (1e6, "M"), (1e3, "K")],
    },
}


def fmt_num(v, currency: str = "KRW") -> str:
    if v is None:
        return "—"
    unit_def = CURRENCY_UNITS.get(currency, CURRENCY_UNITS["KRW"])
    abs_v = abs(v)
    for threshold, suffix in unit_def["scales"]:
        if abs_v >= threshold:
            return f"{v/threshold:,.2f}{suffix}"
    return f"{v:,.0f}"


def localize_label(label: str, currency: str = "KRW") -> str:
    if currency == "KRW" or "(원)" not in label:
        return label
    unit_def = CURRENCY_UNITS.get(currency, CURRENCY_UNITS["KRW"])
    return label.replace("(원)", f"({unit_def['eps_label']})")


def render_header(company: dict, skill_display_name: str) -> str:
    ticker = company.get("ticker", company.get("company_id", "?"))
    return f"""
<h1>{company.get('name', '?')} ({ticker}) — {skill_display_name}</h1>
<div class="meta">
  생성일: {datetime.now().strftime('%Y-%m-%d')} ·
  시장: {company.get('exchange', '—')} ·
  업종: {company.get('industry', '—')} ·
  통화: {company.get('currency', 'KRW')}
</div>
<div class="disclaimer">
  ⚠ 학습·참고용. 실제 투자 결정에 사용 금지. 데이터 출처: DART / yfinance / SEC EDGAR. audit-grade 아님.
</div>"""


def render_tensions(tensions: list) -> str:
    html = ""
    for i, t in enumerate(tensions, 1):
        html += f"""
        <div class="tension">
          <div class="tension-num">{i:02d}</div>
          <div class="tension-content">
            <div class="tension-headline"><strong>{t.get('bull', '')}</strong> vs {t.get('bear', '')}</div>
            <div class="tension-explanation">{t.get('explanation', '')}</div>
          </div>
        </div>"""
    return html


def render_financial_table(financial_table: list, periods: list, currency: str = "KRW") -> str:
    headers = "".join(f"<th>{p}</th>" for p in periods)
    rows = ""
    for row in financial_table:
        label = localize_label(row['label'], currency)
        cells = "".join(f"<td>{fmt_num(row.get(p), currency)}</td>" for p in periods)
        rows += f"<tr><td><strong>{label}</strong></td>{cells}</tr>"
    return f"""
<table>
<thead><tr><th>지표</th>{headers}</tr></thead>
<tbody>{rows}</tbody>
</table>"""


def render_metrics_table(metrics: list) -> str:
    rows = ""
    for m in metrics:
        rows += f"<tr><td><strong>{m.get('metric', '')}</strong></td><td>{m.get('rationale', '')}</td></tr>"
    return f"""
<table><thead><tr><th>지표</th><th>중요성</th></tr></thead><tbody>{rows}</tbody></table>"""


def wrap_html(title: str, body: str, lang: str = "ko") -> str:
    """v3: color-scheme + viewport 메타 추가."""
    return f"""<!DOCTYPE html>
<html lang="{lang}"><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light only">
<meta name="supported-color-schemes" content="light">
<title>{title}</title>
<style>{CSS}</style>
</head><body>
{body}
</body></html>"""


def build_financial_table_rows(normalized: dict, periods: list, metrics_def: list) -> list:
    table = []
    for series_id, label in metrics_def:
        row = {"label": label, "series_id": series_id}
        for p in periods:
            row[p] = normalized.get(series_id, {}).get(p)
        table.append(row)
    return table
