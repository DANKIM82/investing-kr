#!/usr/bin/env python3
"""
chart_generator.py - 분석용 차트 생성 (matplotlib 기반)

지원 차트 종류:
    time-series        : 시계열 추이 (다중 시리즈 지원)
    waterfall          : Waterfall 차트 (실적 변화 분해)
    football-field     : Football field valuation 차트
    pie                : 파이 차트 (세그먼트 비중 등)
    scenario-bar       : Bull/Base/Bear 시나리오 바 차트
    dcf-sensitivity    : DCF 민감도 heatmap

CLI:
    python infra/chart_generator.py time-series \\
        --data '{"x": ["2024Q1","Q2","Q3","Q4"], "series": {"Revenue": [100,110,120,135]}}' \\
        --output reports/chart.png \\
        --title "분기 매출 추이" \\
        --ylabel "매출 (조원)"
"""

import argparse
import json
import os
import sys

# 한글 폰트 설정 (matplotlib)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# 한글 폰트 자동 감지
def _setup_korean_font():
    candidates = [
        "Noto Sans CJK KR", "NanumGothic", "Malgun Gothic",
        "AppleGothic", "Apple SD Gothic Neo", "Pretendard",
    ]
    available = {f.name for f in fm.fontManager.ttflist}
    for c in candidates:
        if c in available:
            plt.rcParams["font.family"] = c
            plt.rcParams["axes.unicode_minus"] = False
            return c
    # Fallback: DejaVu Sans (한글 안 보임 - 경고)
    print("[warn] 한글 폰트 미설치. 한글 표시 깨질 수 있음.", file=sys.stderr)
    return None

_setup_korean_font()


# 색상 팔레트 (design-system.md 기준)
COLOR_PALETTE = ["#0066cc", "#28a745", "#dc3545", "#ffc107", "#6610f2", "#fd7e14", "#20c997", "#e83e8c"]


def chart_time_series(data, output, title, xlabel="", ylabel=""):
    fig, ax = plt.subplots(figsize=(10, 5))
    x = data["x"]
    for i, (name, values) in enumerate(data["series"].items()):
        color = COLOR_PALETTE[i % len(COLOR_PALETTE)]
        ax.plot(x, values, marker="o", label=name, color=color, linewidth=2)
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.legend(loc="best")
    ax.grid(True, alpha=0.3)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(output, dpi=120, bbox_inches="tight")
    plt.close()


def chart_waterfall(data, output, title, ylabel=""):
    """data: {'labels': [...], 'values': [...]}"""
    labels = data["labels"]
    values = data["values"]
    
    cumulative = [0]
    for v in values[:-1]:
        cumulative.append(cumulative[-1] + v)
    
    fig, ax = plt.subplots(figsize=(10, 5))
    for i, (label, val, base) in enumerate(zip(labels, values, cumulative)):
        if i == 0 or i == len(labels) - 1:
            color = "#1a1a1a"
            ax.bar(label, val, bottom=0, color=color)
        else:
            color = "#28a745" if val >= 0 else "#dc3545"
            ax.bar(label, val, bottom=base, color=color)
        ax.text(i, base + val / 2, f"{val:+,.0f}" if i not in [0, len(labels)-1] else f"{val:,.0f}",
                ha="center", va="center", color="white", fontweight="bold")
    
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_ylabel(ylabel)
    ax.grid(True, alpha=0.3, axis="y")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(output, dpi=120, bbox_inches="tight")
    plt.close()


def chart_football_field(data, output, title, current_price=None):
    """data: {'methodology': [...], 'low': [...], 'high': [...]}"""
    methods = data["methodology"]
    lows = data["low"]
    highs = data["high"]
    
    fig, ax = plt.subplots(figsize=(10, max(4, len(methods) * 0.6)))
    y_pos = range(len(methods))
    
    for i, (m, lo, hi) in enumerate(zip(methods, lows, highs)):
        ax.barh(i, hi - lo, left=lo, height=0.5, color=COLOR_PALETTE[i % len(COLOR_PALETTE)], alpha=0.7)
        ax.text(lo, i, f"  {lo:,.0f}", va="center", ha="left", fontsize=9)
        ax.text(hi, i, f"{hi:,.0f}  ", va="center", ha="right", fontsize=9)
    
    if current_price:
        ax.axvline(x=current_price, color="black", linestyle="--", linewidth=2, label=f"현재가: {current_price:,.0f}")
        ax.legend(loc="upper right")
    
    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(methods)
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlabel("주당 가치")
    ax.grid(True, alpha=0.3, axis="x")
    ax.invert_yaxis()
    plt.tight_layout()
    plt.savefig(output, dpi=120, bbox_inches="tight")
    plt.close()


def chart_pie(data, output, title):
    """data: {'labels': [...], 'values': [...]}"""
    labels = data["labels"]
    values = data["values"]
    
    fig, ax = plt.subplots(figsize=(8, 8))
    colors = [COLOR_PALETTE[i % len(COLOR_PALETTE)] for i in range(len(labels))]
    wedges, texts, autotexts = ax.pie(
        values, labels=labels, colors=colors, autopct="%1.1f%%",
        startangle=90, textprops={"fontsize": 11},
    )
    for autotext in autotexts:
        autotext.set_color("white")
        autotext.set_fontweight("bold")
    ax.set_title(title, fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(output, dpi=120, bbox_inches="tight")
    plt.close()


def chart_scenario_bar(data, output, title, ylabel=""):
    """data: {'scenarios': ['Bear','Base','Bull'], 'values': [...], 'probabilities': [...] (optional)}"""
    scenarios = data["scenarios"]
    values = data["values"]
    probs = data.get("probabilities", [None] * len(scenarios))
    
    fig, ax = plt.subplots(figsize=(8, 5))
    colors = ["#dc3545", "#0066cc", "#28a745"][:len(scenarios)]
    bars = ax.bar(scenarios, values, color=colors)
    for bar, val, prob in zip(bars, values, probs):
        height = bar.get_height()
        label = f"{val:,.0f}"
        if prob is not None:
            label += f"\n({prob:.0%})"
        ax.text(bar.get_x() + bar.get_width() / 2, height, label,
                ha="center", va="bottom", fontsize=11, fontweight="bold")
    
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_ylabel(ylabel)
    ax.grid(True, alpha=0.3, axis="y")
    plt.tight_layout()
    plt.savefig(output, dpi=120, bbox_inches="tight")
    plt.close()


def chart_dcf_sensitivity(data, output, title="DCF 민감도 분석"):
    """data: {'wacc': [...], 'growth': [...], 'matrix': [[...]]} - matrix[i][j] = wacc[i], growth[j]"""
    import numpy as np
    
    wacc = data["wacc"]
    growth = data["growth"]
    matrix = np.array(data["matrix"])
    
    fig, ax = plt.subplots(figsize=(8, 6))
    im = ax.imshow(matrix, cmap="RdYlGn", aspect="auto")
    
    ax.set_xticks(range(len(growth)))
    ax.set_yticks(range(len(wacc)))
    ax.set_xticklabels([f"{g*100:.1f}%" for g in growth])
    ax.set_yticklabels([f"{w*100:.1f}%" for w in wacc])
    ax.set_xlabel("Terminal Growth Rate")
    ax.set_ylabel("WACC")
    ax.set_title(title, fontsize=14, fontweight="bold")
    
    for i in range(len(wacc)):
        for j in range(len(growth)):
            ax.text(j, i, f"{matrix[i, j]:,.0f}", ha="center", va="center",
                    color="black", fontsize=9)
    
    fig.colorbar(im, ax=ax, label="주당 가치")
    plt.tight_layout()
    plt.savefig(output, dpi=120, bbox_inches="tight")
    plt.close()


HANDLERS = {
    "time-series": chart_time_series,
    "waterfall": chart_waterfall,
    "football-field": chart_football_field,
    "pie": chart_pie,
    "scenario-bar": chart_scenario_bar,
    "dcf-sensitivity": chart_dcf_sensitivity,
}


def main():
    parser = argparse.ArgumentParser(description="차트 생성 (matplotlib)")
    parser.add_argument("chart_type", choices=list(HANDLERS.keys()))
    parser.add_argument("--data", required=True, help="JSON 데이터 (또는 @path/to/file.json)")
    parser.add_argument("--output", required=True, help="출력 PNG 경로")
    parser.add_argument("--title", default="")
    parser.add_argument("--xlabel", default="")
    parser.add_argument("--ylabel", default="")
    parser.add_argument("--current-price", type=float, default=None, help="football-field용 현재가")
    args = parser.parse_args()
    
    # 데이터 로드
    if args.data.startswith("@"):
        with open(args.data[1:], encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = json.loads(args.data)
    
    # 출력 디렉토리 생성
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    
    handler = HANDLERS[args.chart_type]
    
    # 핸들러별 인자 적응
    if args.chart_type == "time-series":
        handler(data, args.output, args.title, args.xlabel, args.ylabel)
    elif args.chart_type == "waterfall":
        handler(data, args.output, args.title, args.ylabel)
    elif args.chart_type == "football-field":
        handler(data, args.output, args.title, args.current_price)
    elif args.chart_type == "pie":
        handler(data, args.output, args.title)
    elif args.chart_type == "scenario-bar":
        handler(data, args.output, args.title, args.ylabel)
    elif args.chart_type == "dcf-sensitivity":
        handler(data, args.output, args.title)
    
    print(json.dumps({"output": args.output, "chart_type": args.chart_type}, ensure_ascii=False))


if __name__ == "__main__":
    main()
