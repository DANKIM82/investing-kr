"""
build_company_index.py - 회사 마스터 인덱스 빌드 (KR + US + JP).

KR: data/kospi.csv, data/kosdaq.csv (KRX 다운로드. UTF-8/CP949 자동 감지)
US/JP: yfinance

실행: python scripts/build_company_index.py
"""
import csv
import json
import time
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

REPO_ROOT = Path(__file__).parent.parent
DATA_DIR = REPO_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)
OUTPUT_PATH = DATA_DIR / "companies_master.json"

KOSPI_CSV = DATA_DIR / "kospi.csv"
KOSDAQ_CSV = DATA_DIR / "kosdaq.csv"


def _print(msg):
    print(f"  {msg}", flush=True)


def _detect_encoding(path):
    """KRX CSV 인코딩 자동 감지 (UTF-8 → CP949 순서)."""
    for enc in ["utf-8", "utf-8-sig", "cp949", "euc-kr"]:
        try:
            with path.open("r", encoding=enc) as f:
                f.read(2048)
            return enc
        except UnicodeDecodeError:
            continue
    return "cp949"


def _read_krx_csv(path, exchange):
    """KRX CSV 파싱."""
    if not path.exists():
        _print(f"   ⚠ {path.name} 없음")
        return []

    encoding = _detect_encoding(path)
    _print(f"   {path.name} 인코딩: {encoding}")

    rows = []
    with path.open("r", encoding=encoding) as f:
        reader = csv.DictReader(f)
        for row in reader:
            ticker = (row.get("종목코드") or "").strip().strip('"').zfill(6)
            name = (row.get("종목명") or "").strip().strip('"')
            mcap_str = (row.get("상장시가총액") or "0").strip().strip('"').replace(",", "")
            try:
                market_cap = int(mcap_str)
            except ValueError:
                market_cap = 0

            if not ticker or not name:
                continue

            rows.append({
                "ticker": ticker,
                "name": name,
                "market": "KR",
                "exchange": exchange,
                "market_cap": market_cap,
                "currency": "KRW",
            })
    return rows


def build_kr_companies():
    _print("🇰🇷 KR 빌드 (KRX CSV)...")
    kospi = _read_krx_csv(KOSPI_CSV, "KOSPI")
    kosdaq = _read_krx_csv(KOSDAQ_CSV, "KOSDAQ")
    _print(f"   KOSPI: {len(kospi)}, KOSDAQ: {len(kosdaq)}")
    return kospi + kosdaq


def build_us_companies():
    _print("🇺🇸 US 빌드...")
    us_tickers = list(set(_get_sp500_tickers() + _get_extra_us_tickers()))
    us_data = []

    try:
        import yfinance as yf
        for i, ticker in enumerate(us_tickers):
            if i % 50 == 0:
                _print(f"   {i}/{len(us_tickers)}...")
            try:
                info = yf.Ticker(ticker).info
                name = info.get("longName") or info.get("shortName") or ticker
                us_data.append({
                    "ticker": ticker,
                    "name": name,
                    "market": "US",
                    "exchange": info.get("exchange", "NMS"),
                    "sector": info.get("sector"),
                    "market_cap": info.get("marketCap"),
                    "currency": "USD",
                })
                time.sleep(0.05)
            except Exception:
                us_data.append({
                    "ticker": ticker, "name": ticker, "market": "US",
                    "exchange": "?", "currency": "USD",
                })
    except ImportError:
        _print("   ⚠ yfinance 없음, 건너뜀")
        return []

    _print(f"   US: {len(us_data)}")
    return us_data


def _get_sp500_tickers():
    try:
        import requests
        from bs4 import BeautifulSoup
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.find("table", {"id": "constituents"})
        if not table:
            return _fallback_us_tickers()
        return [
            row.find_all("td")[0].text.strip().replace(".", "-")
            for row in table.find_all("tr")[1:] if row.find_all("td")
        ]
    except Exception:
        return _fallback_us_tickers()


def _fallback_us_tickers():
    return [
        "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "NVDA", "META", "TSLA",
        "AVGO", "ORCL", "ADBE", "CRM", "AMD", "INTC", "CSCO", "QCOM", "IBM",
        "NFLX", "PYPL", "UBER", "ABNB", "PLTR", "DDOG", "SNOW", "CRWD",
        "JPM", "BAC", "WFC", "GS", "MS", "V", "MA", "BLK",
        "JNJ", "UNH", "PFE", "LLY", "MRK", "ABBV",
        "WMT", "HD", "COST", "MCD", "NKE", "SBUX", "DIS", "KO", "PEP", "PG",
        "BA", "CAT", "GE", "HON",
        "XOM", "CVX",
    ]


def _get_extra_us_tickers():
    return [
        "PLTR", "RBLX", "DUOL", "SHOP", "SOFI", "DKNG",
        "ASML", "TSM", "MU", "MRVL", "ARM", "SMCI",
        "BABA", "PDD", "JD", "BIDU", "NIO", "LI", "XPEV",
        "EA", "TTWO", "RIOT", "COIN",
    ]


def build_jp_companies():
    _print("🇯🇵 JP 빌드...")
    jp_tickers = _get_jp_tickers()
    jp_data = []
    try:
        import yfinance as yf
        for i, ticker in enumerate(jp_tickers):
            if i % 20 == 0:
                _print(f"   {i}/{len(jp_tickers)}...")
            try:
                info = yf.Ticker(f"{ticker}.T").info
                name = info.get("longName") or info.get("shortName") or ticker
                jp_data.append({
                    "ticker": ticker,
                    "name": name,
                    "market": "JP",
                    "exchange": "JPX",
                    "sector": info.get("sector"),
                    "market_cap": info.get("marketCap"),
                    "currency": "JPY",
                })
                time.sleep(0.05)
            except Exception:
                continue
    except ImportError:
        return []

    _print(f"   JP: {len(jp_data)}")
    return jp_data


def _get_jp_tickers():
    return [
        "7203", "6758", "6861", "8035", "6098", "9984", "9983", "6594",
        "6501", "6502", "6752", "6920", "6981", "6857",
        "7267", "7269", "7270", "7261",
        "8306", "8316", "8411", "8766",
        "8058", "8031", "8001", "8053", "2914",
        "4502", "4503", "4519", "4901",
        "7974", "9697", "9684", "7832",
        "9433", "9432", "9020", "4661", "3382",
        "8801", "8802", "4452", "4911",
    ]


def main():
    print("=" * 60)
    print("회사 마스터 인덱스 빌드 시작")
    print("=" * 60)
    start = time.time()

    all_companies = []

    kr = build_kr_companies()
    all_companies.extend(kr)

    us = build_us_companies()
    all_companies.extend(us)

    jp = build_jp_companies()
    all_companies.extend(jp)

    all_companies.sort(key=lambda c: (c.get("market_cap") or 0), reverse=True)

    OUTPUT_PATH.write_text(
        json.dumps(all_companies, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    elapsed = time.time() - start
    print()
    print("=" * 60)
    print(f"✅ 완료: {len(all_companies)}개 → {OUTPUT_PATH}")
    print(f"   KR: {len(kr)}, US: {len(us)}, JP: {len(jp)}")
    print(f"   파일 크기: {OUTPUT_PATH.stat().st_size / 1024:.1f} KB")
    print(f"   소요: {elapsed:.0f}초")
    print("=" * 60)


if __name__ == "__main__":
    main()
