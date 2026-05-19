#!/usr/bin/env python3
"""
market_data.py - 시장 데이터 + multiples 통합 (KR/US/JP)
v2: KR 회사는 yfinance.KS 우선 사용 (KRX 회원제 이슈 우회). pykrx는 fallback.
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta

import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def detect_market(ticker: str) -> str:
    t = ticker.strip().upper()
    if re.match(r"^\d{6}$", t) or t.endswith(".KS") or t.endswith(".KQ"):
        return "KR"
    if re.match(r"^\d{4}$", t) or t.endswith(".T"):
        return "JP"
    if re.search(r"[\uac00-\ud7af]", ticker):
        return "KR"
    if re.search(r"[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]", ticker):
        return "JP"
    return "US"


def normalize_ticker(ticker: str, market: str) -> str:
    t = ticker.strip().upper()
    if market == "KR":
        if re.match(r"^\d{6}$", t):
            return f"{t}.KS"  # Default to KOSPI
        return t
    if market == "JP":
        if re.match(r"^\d{4}$", t):
            return f"{t}.T"
        return t
    return t


def _quote_kr_via_yfinance(ticker: str):
    """KR 회사를 yfinance .KS/.KQ로 조회 (KRX 회원제 우회)."""
    import yfinance as yf

    code = ticker.strip().split(".")[0]
    # KOSPI 시도 → 실패 시 KOSDAQ
    for suffix in [".KS", ".KQ"]:
        yf_ticker = f"{code}{suffix}"
        try:
            yt = yf.Ticker(yf_ticker)
            info = yt.info or {}
            if not info.get("currentPrice") and not info.get("regularMarketPrice"):
                continue

            hist = yt.history(period="5d")
            if hist.empty:
                continue

            latest = hist.iloc[-1]
            prev_close = info.get("previousClose") or (hist.iloc[-2]["Close"] if len(hist) > 1 else latest["Close"])
            change_pct = (latest["Close"] - prev_close) / prev_close * 100 if prev_close else 0

            return {
                "ticker": code,
                "market": "KR",
                "name": info.get("longName") or info.get("shortName"),
                "currency": info.get("currency", "KRW"),
                "price": float(latest["Close"]),
                "change_pct": round(change_pct, 2),
                "volume": int(latest["Volume"]),
                "market_cap": info.get("marketCap"),
                "shares_outstanding": info.get("sharesOutstanding"),
                "beta": info.get("beta"),
                "pe_ttm": info.get("trailingPE"),
                "pe_forward": info.get("forwardPE"),
                "as_of": str(latest.name.date()),
                "_source": f"yfinance ({suffix})",
            }
        except Exception:
            continue
    return None


def cmd_quote(args):
    market = args.market or detect_market(args.ticker)

    if market == "KR":
        # 1순위: yfinance .KS/.KQ
        result = _quote_kr_via_yfinance(args.ticker)
        if result and result.get("price"):
            return result

        # 2순위: pykrx fallback (KRX 인증 필요)
        try:
            from pykrx import stock
            code = args.ticker.strip()
            if "." in code:
                code = code.split(".")[0]
            today = datetime.now().strftime("%Y%m%d")
            yesterday = (datetime.now() - timedelta(days=7)).strftime("%Y%m%d")
            ohlcv = stock.get_market_ohlcv(yesterday, today, code)
            if ohlcv is None or ohlcv.empty:
                return {"error": "데이터 없음", "ticker": code}
            latest = ohlcv.iloc[-1]
            cap_df = stock.get_market_cap(today, code)
            mcap = None
            shares = None
            if cap_df is not None and not cap_df.empty:
                row = cap_df.iloc[0] if len(cap_df) > 0 else None
                if row is not None:
                    mcap = float(row.get("시가총액", 0))
                    shares = float(row.get("상장주식수", 0))
            return {
                "ticker": code,
                "market": "KR",
                "name": stock.get_market_ticker_name(code),
                "currency": "KRW",
                "price": float(latest.get("종가", 0)),
                "change_pct": float(latest.get("등락률", 0)),
                "volume": int(latest.get("거래량", 0)),
                "market_cap": mcap,
                "shares_outstanding": shares,
                "as_of": today,
                "_source": "pykrx",
            }
        except Exception as e:
            return {"error": str(e), "ticker": args.ticker}

    # US / JP via yfinance
    try:
        import yfinance as yf
        yf_ticker = normalize_ticker(args.ticker, market)
        yt = yf.Ticker(yf_ticker)
        info = yt.info or {}
        hist = yt.history(period="5d")
        if hist.empty:
            return {"error": "no data", "ticker": yf_ticker}
        latest = hist.iloc[-1]
        prev_close = info.get("previousClose") or hist.iloc[-2]["Close"] if len(hist) > 1 else latest["Close"]
        change_pct = (latest["Close"] - prev_close) / prev_close * 100 if prev_close else 0
        return {
            "ticker": yf_ticker,
            "market": market,
            "name": info.get("longName") or info.get("shortName"),
            "currency": info.get("currency"),
            "price": float(latest["Close"]),
            "change_pct": round(change_pct, 2),
            "volume": int(latest["Volume"]),
            "market_cap": info.get("marketCap"),
            "shares_outstanding": info.get("sharesOutstanding"),
            "beta": info.get("beta"),
            "pe_ttm": info.get("trailingPE"),
            "pe_forward": info.get("forwardPE"),
            "as_of": str(latest.name.date()),
        }
    except Exception as e:
        return {"error": str(e), "ticker": args.ticker}


def _multiples_kr_via_yfinance(ticker: str):
    """KR 회사 multiples를 yfinance.KS/.KQ로 조회."""
    import yfinance as yf

    code = ticker.strip().split(".")[0]
    for suffix in [".KS", ".KQ"]:
        yf_ticker = f"{code}{suffix}"
        try:
            yt = yf.Ticker(yf_ticker)
            info = yt.info or {}
            if not info.get("marketCap"):
                continue

            return {
                "ticker": code,
                "market": "KR",
                "name": info.get("longName") or info.get("shortName"),
                "currency": info.get("currency", "KRW"),
                "market_cap": info.get("marketCap"),
                "enterprise_value": info.get("enterpriseValue"),
                "pe_ttm": info.get("trailingPE"),
                "pe_forward": info.get("forwardPE"),
                "ev_ebitda": info.get("enterpriseToEbitda"),
                "ev_revenue": info.get("enterpriseToRevenue"),
                "ps_ttm": info.get("priceToSalesTrailing12Months"),
                "pb": info.get("priceToBook"),
                "dividend_yield": info.get("dividendYield"),
                "payout_ratio": info.get("payoutRatio"),
                "beta": info.get("beta"),
                "profit_margin": info.get("profitMargins"),
                "operating_margin": info.get("operatingMargins"),
                "roe": info.get("returnOnEquity"),
                "roa": info.get("returnOnAssets"),
                "revenue_growth_yoy": info.get("revenueGrowth"),
                "earnings_growth_yoy": info.get("earningsGrowth"),
                "_source": f"yfinance ({suffix})",
            }
        except Exception:
            continue
    return None


def cmd_multiples(args):
    market = args.market or detect_market(args.ticker)

    if market == "KR":
        # 1순위: yfinance .KS/.KQ
        result = _multiples_kr_via_yfinance(args.ticker)
        if result and result.get("market_cap"):
            return result

        # 2순위: pykrx fallback
        try:
            from pykrx import stock
            code = args.ticker.strip()
            if "." in code:
                code = code.split(".")[0]
            today = datetime.now().strftime("%Y%m%d")
            fund_df = stock.get_market_fundamental(today, code)
            cap_df = stock.get_market_cap(today, code)
            if fund_df is None or fund_df.empty:
                return {"error": "fundamentals not available", "ticker": code}
            row = fund_df.iloc[0]
            cap_row = cap_df.iloc[0] if cap_df is not None and not cap_df.empty else {}
            return {
                "ticker": code,
                "market": "KR",
                "name": stock.get_market_ticker_name(code),
                "pe_ttm": float(row.get("PER", 0)) or None,
                "pb": float(row.get("PBR", 0)) or None,
                "eps_ttm": float(row.get("EPS", 0)) or None,
                "bps": float(row.get("BPS", 0)) or None,
                "dividend_yield": float(row.get("DIV", 0)) / 100 if row.get("DIV") else None,
                "dps": float(row.get("DPS", 0)) or None,
                "market_cap": float(cap_row.get("시가총액", 0)) if cap_row is not {} else None,
                "as_of": today,
                "_source": "pykrx",
            }
        except Exception as e:
            return {"error": str(e), "ticker": args.ticker}

    try:
        import yfinance as yf
        yf_ticker = normalize_ticker(args.ticker, market)
        yt = yf.Ticker(yf_ticker)
        info = yt.info or {}
        return {
            "ticker": yf_ticker,
            "market": market,
            "name": info.get("longName"),
            "currency": info.get("currency"),
            "market_cap": info.get("marketCap"),
            "enterprise_value": info.get("enterpriseValue"),
            "pe_ttm": info.get("trailingPE"),
            "pe_forward": info.get("forwardPE"),
            "ev_ebitda": info.get("enterpriseToEbitda"),
            "ev_revenue": info.get("enterpriseToRevenue"),
            "ps_ttm": info.get("priceToSalesTrailing12Months"),
            "pb": info.get("priceToBook"),
            "dividend_yield": info.get("dividendYield"),
            "payout_ratio": info.get("payoutRatio"),
            "beta": info.get("beta"),
            "profit_margin": info.get("profitMargins"),
            "operating_margin": info.get("operatingMargins"),
            "roe": info.get("returnOnEquity"),
            "roa": info.get("returnOnAssets"),
            "revenue_growth_yoy": info.get("revenueGrowth"),
            "earnings_growth_yoy": info.get("earningsGrowth"),
        }
    except Exception as e:
        return {"error": str(e), "ticker": args.ticker}


def cmd_history(args):
    market = args.market or detect_market(args.ticker)

    # KR도 history는 yfinance로 (역사 데이터는 yfinance가 안정적)
    if market == "KR":
        import yfinance as yf
        code = args.ticker.strip().split(".")[0]
        for suffix in [".KS", ".KQ"]:
            yf_ticker = f"{code}{suffix}"
            try:
                yt = yf.Ticker(yf_ticker)
                hist = yt.history(period=args.period)
                if hist.empty:
                    continue
                data = []
                for date_idx, row in hist.iterrows():
                    data.append({
                        "date": str(date_idx.date()),
                        "open": float(row["Open"]),
                        "high": float(row["High"]),
                        "low": float(row["Low"]),
                        "close": float(row["Close"]),
                        "volume": int(row["Volume"]),
                    })
                return {"ticker": code, "market": "KR", "period": args.period, "data": data, "total": len(data)}
            except Exception:
                continue
        return {"error": "no data", "ticker": code}

    try:
        import yfinance as yf
        yf_ticker = normalize_ticker(args.ticker, market)
        yt = yf.Ticker(yf_ticker)
        hist = yt.history(period=args.period)
        if hist.empty:
            return {"error": "no data", "ticker": yf_ticker}
        data = []
        for date_idx, row in hist.iterrows():
            data.append({
                "date": str(date_idx.date()),
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
                "volume": int(row["Volume"]),
            })
        return {"ticker": yf_ticker, "market": market, "period": args.period, "data": data, "total": len(data)}
    except Exception as e:
        return {"error": str(e), "ticker": args.ticker}


def cmd_peers(args):
    results = []
    for ticker in args.tickers:
        sub_args = argparse.Namespace(ticker=ticker, market=None)
        results.append(cmd_multiples(sub_args))
    return {"peers": results, "total": len(results)}


def cmd_risk_free_rate(args):
    market = args.market or "US"
    fred_key = os.environ.get("FRED_API_KEY", "")

    if market == "US":
        if fred_key:
            try:
                url = f"https://api.stlouisfed.org/fred/series/observations?series_id=DGS10&api_key={fred_key}&file_type=json&limit=1&sort_order=desc"
                r = requests.get(url, timeout=10)
                r.raise_for_status()
                obs = r.json()["observations"][0]
                return {"market": "US", "rate": float(obs["value"]) / 100, "as_of": obs["date"], "source": "FRED DGS10"}
            except Exception:
                pass
        return {"market": "US", "rate": 0.045, "as_of": "default", "source": "default (4.5%)", "warning": "FRED_API_KEY 없음, default 사용"}

    if market == "KR":
        return {"market": "KR", "rate": 0.035, "as_of": "default", "source": "default (3.5%)", "warning": "한국 10년 국채 자동 조회 미지원, default 사용"}

    if market == "JP":
        return {"market": "JP", "rate": 0.010, "as_of": "default", "source": "default (1.0%)", "warning": "일본 10년 JGB default 사용"}

    return {"error": f"Unknown market: {market}"}


def main():
    parser = argparse.ArgumentParser(description="시장 데이터 통합 (KR/US/JP)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    def add_market(p):
        p.add_argument("--market", choices=["KR", "US", "JP"], help="시장 명시")

    p = sub.add_parser("quote")
    p.add_argument("ticker")
    add_market(p)

    p = sub.add_parser("multiples")
    p.add_argument("ticker")
    add_market(p)

    p = sub.add_parser("history")
    p.add_argument("ticker")
    p.add_argument("--period", default="1y", choices=["1mo", "3mo", "6mo", "1y", "2y", "5y", "max"])
    add_market(p)

    p = sub.add_parser("peers")
    p.add_argument("tickers", nargs="+")

    p = sub.add_parser("risk-free-rate")
    add_market(p)

    args = parser.parse_args()

    handlers = {
        "quote": cmd_quote,
        "multiples": cmd_multiples,
        "history": cmd_history,
        "peers": cmd_peers,
        "risk-free-rate": cmd_risk_free_rate,
    }
    result = handlers[args.cmd](args)
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
