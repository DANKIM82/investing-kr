"""infra/free_data_kr.py 래퍼 + 시장별 정규화 + 정합성 검증."""

import json
import os
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

IS_METRICS = {
    "revenue", "cost_of_revenue", "gross_profit", "sga",
    "operating_income", "interest_expense", "pretax_income",
    "tax_expense", "net_income",
}
CF_METRICS = {"operating_cash_flow", "capex", "free_cash_flow", "dividends_paid"}


def run_infra(cmd: list[str]) -> dict:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    result = subprocess.run(
        [sys.executable, "infra/free_data_kr.py"] + cmd,
        capture_output=True, text=False, cwd=REPO_ROOT, env=env,
    )
    stdout = result.stdout.decode("utf-8", errors="replace") if result.stdout else ""
    stderr = result.stderr.decode("utf-8", errors="replace") if result.stderr else ""

    if result.returncode != 0:
        print(f"  ⚠ 실패: {stderr[:300]}", file=sys.stderr)
        return {}
    if not stdout.strip():
        return {}

    json_start = stdout.find("{")
    if json_start > 0:
        stdout = stdout[json_start:]

    try:
        return json.loads(stdout)
    except json.JSONDecodeError as e:
        print(f"  ⚠ JSON 파싱 실패: {e}", file=sys.stderr)
        return {}


def get_company(ticker: str) -> dict:
    raw = run_infra(["companies", ticker])
    results = raw.get("results", [])
    return results[0] if results else {}


def get_fundamentals(ticker: str, periods: list[str] | None = None) -> dict:
    """
    분기별 재무 데이터 fetch + 시장별 정규화.

    - KR: IS Q4 누적 차감, CF 매 분기 차분, net_income 자동 추정 (pretax - tax)
    - US/JP: yfinance/SEC가 이미 분기값으로 주므로 raw 그대로
    """
    cmd = ["fundamentals", ticker]
    if periods:
        cmd.extend(["--periods", ",".join(periods)])

    raw = run_infra(cmd)
    market = raw.get("market", "KR")

    raw_pivot = defaultdict(dict)
    for d in raw.get("data", []):
        raw_pivot[d["series_id"]][d["calendar_period"]] = d["value"]

    all_periods = sorted({p for pv in raw_pivot.values() for p in pv})

    if market == "KR":
        normalized = _normalize_kr(raw_pivot)
        normalized = _derive_missing_net_income(normalized)
    else:
        normalized = {k: dict(v) for k, v in raw_pivot.items()}

    return {
        "raw_pivot": dict(raw_pivot),
        "normalized": normalized,
        "periods": all_periods,
        "data_count": raw.get("total", 0),
        "market": market,
    }


def _normalize_kr(raw_pivot: dict) -> dict:
    """한국 회사 (12월 결산) DART 정규화."""
    normalized = defaultdict(dict)

    for series_id, period_values in raw_pivot.items():
        if series_id in IS_METRICS:
            for period, value in period_values.items():
                year, q = period[:4], period[-2:]
                if q == "Q4":
                    q1 = period_values.get(f"{year}Q1", 0)
                    q2 = period_values.get(f"{year}Q2", 0)
                    q3 = period_values.get(f"{year}Q3", 0)
                    normalized[series_id][period] = value - q1 - q2 - q3
                else:
                    normalized[series_id][period] = value

        elif series_id in CF_METRICS:
            by_year = defaultdict(dict)
            for period, value in period_values.items():
                year, q = period[:4], period[-2:]
                by_year[year][q] = value
            for year, quarters in by_year.items():
                prev_cum = 0
                for q in ["Q1", "Q2", "Q3", "Q4"]:
                    if q not in quarters:
                        continue
                    current_cum = quarters[q]
                    normalized[series_id][f"{year}{q}"] = current_cum - prev_cum
                    prev_cum = current_cum

        else:
            for period, value in period_values.items():
                normalized[series_id][period] = value

    return dict(normalized)


def _derive_missing_net_income(normalized: dict) -> dict:
    """
    DART가 한국 회사 분기별 net_income을 종종 누락 (Q4 연간만 보고).
    pretax_income - tax_expense 로 누락 분기 추정.
    """
    pretax = normalized.get("pretax_income", {})
    tax = normalized.get("tax_expense", {})

    if "net_income" not in normalized:
        normalized["net_income"] = {}

    derived_count = 0
    for period, pretax_val in pretax.items():
        if period in normalized["net_income"]:
            continue
        if period not in tax:
            continue
        normalized["net_income"][period] = pretax_val - tax[period]
        derived_count += 1

    if derived_count > 0:
        print(f"  ℹ net_income {derived_count}개 분기를 pretax-tax로 추정 (DART 누락 보완)")

    return normalized


def validate_normalization(raw_pivot: dict, normalized: dict, market: str = "KR", verbose: bool = True) -> dict:
    """분기합 vs 원본 연간 누적 비교. KR만 의미 있음."""
    if market != "KR":
        if verbose:
            print(f"  (시장: {market} — raw 분기값 사용, 정규화 미적용)")
        return {}

    years = sorted({p[:4] for pv in raw_pivot.values() for p in pv})
    results = {}

    for year in years:
        year_results = []
        for series_id in (IS_METRICS | CF_METRICS):
            yearly_raw = raw_pivot.get(series_id, {}).get(f"{year}Q4")
            if yearly_raw is None:
                continue
            quarterly_sum = sum(
                normalized.get(series_id, {}).get(f"{year}{q}", 0) or 0
                for q in ["Q1", "Q2", "Q3", "Q4"]
            )
            diff_pct = abs(quarterly_sum - yearly_raw) / abs(yearly_raw) * 100 if yearly_raw else 0
            year_results.append({
                "series_id": series_id,
                "ok": diff_pct < 0.1,
            })

        results[year] = year_results

        if verbose:
            print(f"  ── {year} ──")
            for r in year_results:
                status = "✓" if r["ok"] else "⚠"
                print(f"    {r['series_id']:24} {status}")

    return results
