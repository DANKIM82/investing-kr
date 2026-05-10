#!/usr/bin/env python3
"""
projection_engine.py - 5년 forward 재무 예측 엔진

Historical 데이터 + 가정 -> 5년 projection.

CLI:
    python infra/projection_engine.py \\
        --historical reports/.tmp/historical.json \\
        --assumptions reports/.tmp/assumptions.json \\
        --output reports/.tmp/projection.json
"""

import argparse
import json
import os
import sys


def project(historical, assumptions, scenario="base"):
    """
    historical: {"revenue": [y1,y2,...,y5], "operating_income": [...], ...}
    assumptions: {
        "revenue_growth_5y": [0.10, 0.09, 0.08, 0.07, 0.06],  # 시나리오별
        "operating_margin_5y": [0.18, 0.19, 0.20, 0.20, 0.20],
        "tax_rate": 0.24,
        "capex_to_revenue": 0.08,
        "wc_to_revenue_change": 0.02,
        "depreciation_to_revenue": 0.03,
    }
    """
    last_revenue = historical["revenue"][-1] if historical.get("revenue") else 0
    
    # 시나리오별 multiplier
    scenario_mult = {"bear": 0.7, "base": 1.0, "bull": 1.3}.get(scenario, 1.0)
    
    growth_rates = assumptions.get("revenue_growth_5y", [0.05] * 5)
    margins = assumptions.get("operating_margin_5y", [0.15] * 5)
    tax_rate = assumptions.get("tax_rate", 0.24)
    capex_ratio = assumptions.get("capex_to_revenue", 0.05)
    wc_change_ratio = assumptions.get("wc_to_revenue_change", 0.02)
    da_ratio = assumptions.get("depreciation_to_revenue", 0.03)
    
    # Adjust by scenario
    growth_rates = [g * scenario_mult for g in growth_rates]
    margins = [min(m * (0.9 + 0.1 * scenario_mult), 0.5) for m in margins]
    
    revenues = []
    op_incomes = []
    nopats = []
    capexes = []
    wc_changes = []
    fcfs = []
    da = []
    ebitdas = []
    
    rev = last_revenue
    for year_idx in range(5):
        rev = rev * (1 + growth_rates[year_idx])
        op_income = rev * margins[year_idx]
        d_a = rev * da_ratio
        ebitda = op_income + d_a
        nopat = op_income * (1 - tax_rate)
        capex = rev * capex_ratio
        wc_change = rev * wc_change_ratio
        fcf = nopat + d_a - capex - wc_change
        
        revenues.append(rev)
        op_incomes.append(op_income)
        nopats.append(nopat)
        capexes.append(capex)
        wc_changes.append(wc_change)
        fcfs.append(fcf)
        da.append(d_a)
        ebitdas.append(ebitda)
    
    return {
        "scenario": scenario,
        "years": list(range(1, 6)),
        "revenue": revenues,
        "revenue_growth": growth_rates,
        "operating_margin": margins,
        "operating_income": op_incomes,
        "depreciation_amortization": da,
        "ebitda": ebitdas,
        "tax_rate": tax_rate,
        "nopat": nopats,
        "capex": capexes,
        "working_capital_change": wc_changes,
        "free_cash_flow": fcfs,
    }


def discount_to_pv(fcfs, wacc):
    """Discount FCFs to present value."""
    return [fcf / ((1 + wacc) ** (year + 1)) for year, fcf in enumerate(fcfs)]


def terminal_value_gordon(fcf_year5, terminal_growth, wacc):
    """Gordon growth model."""
    return fcf_year5 * (1 + terminal_growth) / (wacc - terminal_growth)


def terminal_value_exit_multiple(ebitda_year5, exit_multiple):
    """Exit multiple method."""
    return ebitda_year5 * exit_multiple


def run_dcf(historical, assumptions, scenario="base"):
    proj = project(historical, assumptions, scenario)
    
    wacc = assumptions.get("wacc", 0.085)
    terminal_growth = assumptions.get("terminal_growth", 0.025)
    exit_multiple = assumptions.get("exit_multiple", None)
    
    pv_fcfs = discount_to_pv(proj["free_cash_flow"], wacc)
    
    # Terminal value
    tv_gordon = terminal_value_gordon(proj["free_cash_flow"][-1], terminal_growth, wacc)
    tv_pv_gordon = tv_gordon / ((1 + wacc) ** 5)
    
    tv_exit = None
    tv_pv_exit = None
    if exit_multiple:
        tv_exit = terminal_value_exit_multiple(proj["ebitda"][-1], exit_multiple)
        tv_pv_exit = tv_exit / ((1 + wacc) ** 5)
    
    enterprise_value = sum(pv_fcfs) + tv_pv_gordon
    
    # Equity value
    net_debt = assumptions.get("net_debt", 0)
    diluted_shares = assumptions.get("diluted_shares", 1)
    equity_value = enterprise_value - net_debt
    implied_share_price = equity_value / diluted_shares if diluted_shares else None
    
    return {
        "scenario": scenario,
        "projection": proj,
        "wacc": wacc,
        "terminal_growth": terminal_growth,
        "pv_fcfs": pv_fcfs,
        "terminal_value_gordon": tv_gordon,
        "terminal_value_pv_gordon": tv_pv_gordon,
        "terminal_value_exit": tv_exit,
        "terminal_value_pv_exit": tv_pv_exit,
        "enterprise_value": enterprise_value,
        "net_debt": net_debt,
        "equity_value": equity_value,
        "diluted_shares": diluted_shares,
        "implied_share_price": implied_share_price,
    }


def sensitivity_table(historical, assumptions, wacc_range, growth_range, scenario="base"):
    """2D sensitivity: WACC × terminal growth."""
    matrix = []
    for w in wacc_range:
        row = []
        for g in growth_range:
            adj_assumptions = {**assumptions, "wacc": w, "terminal_growth": g}
            result = run_dcf(historical, adj_assumptions, scenario)
            row.append(result["implied_share_price"])
        matrix.append(row)
    return {"wacc": wacc_range, "growth": growth_range, "matrix": matrix}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--historical", required=True)
    parser.add_argument("--assumptions", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--scenario", default="base", choices=["bull", "base", "bear"])
    parser.add_argument("--sensitivity", action="store_true", help="Run 2D sensitivity")
    args = parser.parse_args()
    
    with open(args.historical, encoding="utf-8") as f:
        historical = json.load(f)
    with open(args.assumptions, encoding="utf-8") as f:
        assumptions = json.load(f)
    
    result = run_dcf(historical, assumptions, args.scenario)
    
    if args.sensitivity:
        wacc_range = [0.07, 0.08, 0.09, 0.10, 0.11]
        growth_range = [0.01, 0.015, 0.02, 0.025, 0.03]
        result["sensitivity"] = sensitivity_table(historical, assumptions, wacc_range, growth_range, args.scenario)
    
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(json.dumps({"output": args.output, "implied_price": result.get("implied_share_price")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
