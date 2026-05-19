#!/usr/bin/env python3
"""
free_data_kr.py - 한국/미국/일본 시장 통합 데이터 wrapper

자동 감지 (티커 포맷 기반):
    - 한국: 6자리 숫자 (예: 005930 = 삼성전자) -> DART + pykrx
    - 미국: 영문 (예: AAPL) -> yfinance + SEC EDGAR
    - 일본: 4자리 숫자 또는 .T suffix (예: 7203 또는 7203.T = Toyota) -> yfinance

CLI 사용법 (Claude Code skills에서 호출):
    python infra/free_data_kr.py companies 005930
    python infra/free_data_kr.py companies AAPL
    python infra/free_data_kr.py companies 7203
    python infra/free_data_kr.py companies 삼성전자
    python infra/free_data_kr.py series 005930 --keywords 매출
    python infra/free_data_kr.py fundamentals 005930 --periods 2024Q1,2024Q2 --series revenue,net_income
    python infra/free_data_kr.py documents "AI" --tickers 005930 --year 2024

출력: stdout으로 JSON. 경고/에러는 stderr.

Daloopa MCP 4개 함수에 대응:
    discover_companies         -> companies
    discover_company_series    -> series
    get_company_fundamentals   -> fundamentals
    search_documents           -> documents
"""

import argparse
import json
import math
import os
import re
import sys
from datetime import date, datetime, timedelta
from typing import Any

import requests

# Optional dependencies - lazy load
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ============================================================================
# Configuration
# ============================================================================

DART_API_KEY = os.environ.get("DART_API_KEY", "")
SEC_USER_AGENT = os.environ.get(
    "SEC_USER_AGENT",
    "Personal Research project@example.com",
)
SEC_HEADERS = {"User-Agent": SEC_USER_AGENT, "Accept-Encoding": "gzip, deflate"}


def _eprint(msg: str) -> None:
    print(msg, file=sys.stderr)


# ============================================================================
# Market detection
# ============================================================================

def detect_market(ticker: str) -> str:
    """티커 포맷으로 시장 자동 감지."""
    t = ticker.strip().upper()
    
    # Korean: 6-digit code
    if re.match(r"^\d{6}$", t):
        return "KR"
    if t.endswith(".KS") or t.endswith(".KQ"):
        return "KR"
    
    # Japan: 4-digit code or .T suffix
    if re.match(r"^\d{4}$", t):
        return "JP"
    if t.endswith(".T"):
        return "JP"
    
    # US: alphabetic
    if re.match(r"^[A-Z][A-Z0-9.\-]{0,9}$", t):
        return "US"
    
    # Korean company name (Hangul)
    if re.search(r"[\uac00-\ud7af]", ticker):
        return "KR"
    
    # Japanese company name (Hiragana/Katakana/Kanji)
    if re.search(r"[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]", ticker):
        return "JP"
    
    return "US"  # default


# ============================================================================
# Korean market: DART + pykrx
# ============================================================================

_KR_TICKER_NAME_CACHE: dict[str, str] = {}


def _resolve_kr_ticker(query: str) -> str | None:
    """회사명 -> 종목코드 변환. 6자리 숫자면 그대로 반환."""
    q = query.strip()
    if re.match(r"^\d{6}$", q):
        return q
    if q.endswith(".KS") or q.endswith(".KQ"):
        return q[:-3]
    
    try:
        from pykrx import stock
        # KOSPI + KOSDAQ 전체 검색
        today = datetime.now().strftime("%Y%m%d")
        for market in ["KOSPI", "KOSDAQ"]:
            tickers = stock.get_market_ticker_list(today, market=market)
            for t in tickers:
                name = stock.get_market_ticker_name(t)
                if name == q or q in name:
                    return t
    except Exception as e:
        _eprint(f"[warn] pykrx 종목 검색 실패: {e}")
    
    # DART 시도
    if DART_API_KEY:
        try:
            from opendartreader import OpenDartReader as _ODR
            dart = _ODR(DART_API_KEY)
            corp_code = dart.find_corp_code(q)
            if corp_code:
                # corp_code -> stock code 매핑은 별도 필요
                companies = dart.list_date_ex(datetime.now().strftime("%Y-%m-%d"))
                # 더 단순한 방법: dart.company 호출
                return q  # placeholder
        except Exception as e:
            _eprint(f"[warn] DART 종목 검색 실패: {e}")
    
    return None


def _companies_kr(ticker: str) -> dict[str, Any]:
    """한국 회사 정보 조회 (pykrx + DART)."""
    code = _resolve_kr_ticker(ticker)
    if not code:
        return {"results": [], "error": f"종목코드를 찾을 수 없습니다: {ticker}"}
    
    result = {
        "company_id": code,
        "ticker": code,
        "market": "KR",
        "name": None,
        "name_en": None,
        "sector": None,
        "industry": None,
        "exchange": None,
        "currency": "KRW",
        "latest_calendar_quarter": None,
        "latest_fiscal_quarter": None,
        "fiscal_year_end_month": 12,  # 한국은 대부분 12월말
        "description": None,
        "corp_code": None,
    }
    
    # DART로 회사 정보 조회 (우선)
    if DART_API_KEY:
        try:
            from opendartreader import OpenDartReader as _ODR
            dart = _ODR(DART_API_KEY)
            corp = dart.company(code)
            if corp is not None:
                corp_dict = corp if isinstance(corp, dict) else (
                    corp.to_dict() if hasattr(corp, 'to_dict') else dict(corp)
                )
                result["corp_code"] = corp_dict.get("corp_code")
                result["name"] = corp_dict.get("corp_name") or result["name"]
                result["name_en"] = corp_dict.get("corp_name_eng")
                result["industry"] = corp_dict.get("induty_code")
                result["description"] = corp_dict.get("est_dt", "")
                # corp_cls: Y=유가증권(KOSPI), K=코스닥, N=코넥스
                cls_map = {"Y": "KOSPI", "K": "KOSDAQ", "N": "KONEX"}
                result["exchange"] = cls_map.get(corp_dict.get("corp_cls"))
        except Exception as e:
            _eprint(f"[warn] DART 정보 조회 실패: {e}")

    # pykrx로 보충 (DART에서 못 가져온 필드만)
    if not result["name"]:
        try:
            from pykrx import stock
            result["name"] = stock.get_market_ticker_name(code)
        except Exception as e:
            _eprint(f"[warn] pykrx 정보 조회 실패: {e}")
    
    # 최신 분기 추정 (현재 날짜 기준 1분기 전)
    today = date.today()
    last_quarter_end = today.replace(day=1) - timedelta(days=1)
    # 가장 최근 종료된 분기 계산
    months_back = 0
    while True:
        check_date = today.replace(day=1) - timedelta(days=30 * months_back + 1)
        if check_date.month in [3, 6, 9, 12]:
            result["latest_calendar_quarter"] = f"{check_date.year}Q{check_date.month // 3}"
            break
        months_back += 1
        if months_back > 12:
            break
    
    return {"results": [result]}


def _series_kr(ticker: str, keywords: list[str]) -> dict[str, Any]:
    """한국 회사의 사용 가능 메트릭 목록."""
    # K-IFRS 표준 메트릭 카탈로그
    out = []
    for sid, meta in KR_SERIES_CATALOG.items():
        if keywords:
            haystack = f"{sid} {meta['label_kr']} {meta['label_en']}".lower()
            if not any(k.lower() in haystack for k in keywords):
                continue
        out.append({
            "series_id": sid,
            "label": meta["label_kr"],
            "label_en": meta["label_en"],
            "category": meta["category"],
        })
    return {"company_id": ticker, "market": "KR", "series": out, "total": len(out)}


def _fundamentals_kr(ticker: str, periods: list[str], series_ids: list[str]) -> dict[str, Any]:
    """한국 회사 재무 데이터 (DART)."""
    code = _resolve_kr_ticker(ticker)
    if not code:
        return {"company_id": ticker, "data": [], "error": f"종목코드를 찾을 수 없습니다: {ticker}"}
    
    if not DART_API_KEY:
        return {"company_id": code, "data": [], "error": "DART_API_KEY가 설정되지 않았습니다. .env 파일 확인 필요."}
    
    if not series_ids:
        series_ids = list(KR_SERIES_CATALOG.keys())
    
    data_points = []
    
    try:
        from opendartreader import OpenDartReader as _ODR
        dart = _ODR(DART_API_KEY)

        # 분기 -> DART 보고서 코드 매핑
        # Q1 -> 11013 (1분기보고서)
        # Q2 -> 11012 (반기보고서)
        # Q3 -> 11014 (3분기보고서)
        # Q4 -> 11011 (사업보고서, 연간)
        QUARTER_TO_REPORT = {
            "Q1": "11013",
            "Q2": "11012",
            "Q3": "11014",
            "Q4": "11011",
        }
        
        # 각 요청 분기에 대해 데이터 조회
        if not periods:
            # 기본값: 최근 4분기
            today = date.today()
            year = today.year
            periods = [f"{year-1}Q{q}" for q in [1, 2, 3, 4]]
        
        for period in periods:
            m = re.match(r"(\d{4})Q([1-4])", period)
            if not m:
                continue
            year = int(m.group(1))
            quarter = int(m.group(2))
            report_code = QUARTER_TO_REPORT[f"Q{quarter}"]
            
            try:
                # finstate_all: 단일회사 전체 재무제표
                fs = dart.finstate_all(code, year, reprt_code=report_code)
                if fs is None or (hasattr(fs, "empty") and fs.empty):
                    _eprint(f"[warn] DART 재무제표 없음: {code} {period}")
                    continue
                
                # fs는 DataFrame: account_nm, thstrm_amount 등
                for _, row in fs.iterrows():
                    account = str(row.get("account_nm", "")).strip()
                    amount_str = str(row.get("thstrm_amount", "")).replace(",", "").strip()
                    
                    # 시리즈 매칭
                    matched_sid = None
                    for sid in series_ids:
                        meta = KR_SERIES_CATALOG.get(sid)
                        if not meta:
                            continue
                        if any(label in account for label in meta["dart_labels"]):
                            matched_sid = sid
                            break
                    
                    if not matched_sid:
                        continue
                    
                    try:
                        value = float(amount_str)
                    except (ValueError, TypeError):
                        continue
                    
                    meta = KR_SERIES_CATALOG[matched_sid]
                    data_points.append({
                        "id": f"{code}_{matched_sid}_{period}",
                        "series_id": matched_sid,
                        "label": meta["label_kr"],
                        "label_en": meta["label_en"],
                        "category": meta["category"],
                        "calendar_period": period,
                        "fiscal_period": period,
                        "value": value,
                        "value_formatted": _format_kr(value, matched_sid),
                        "unit": "KRW",
                        "source": "DART",
                        "source_url": f"https://dart.fss.or.kr/dsab007/main.do?option=corp&textCrpNm={code}",
                    })
            except Exception as e:
                _eprint(f"[warn] DART {code} {period} 조회 실패: {e}")
                continue
    
    except ImportError:
        return {"company_id": code, "data": [], "error": "OpenDartReader가 설치되지 않았습니다. pip install OpenDartReader"}
    except Exception as e:
        return {"company_id": code, "data": [], "error": f"DART 호출 실패: {e}"}
    
    # 중복 제거 (같은 series + period가 여러 번 나올 수 있음)
    seen = set()
    unique = []
    for dp in data_points:
        key = (dp["series_id"], dp["calendar_period"])
        if key not in seen:
            seen.add(key)
            unique.append(dp)
    
    # ────────────────────────────────────────────────────────────────────────
    # 파생 시리즈 계산 (EBITDA, FCF, Total Debt, Diluted Shares Outstanding)
    # ────────────────────────────────────────────────────────────────────────
    # period별 raw 값 lookup
    by_period: dict[str, dict[str, float]] = {}
    for dp in unique:
        by_period.setdefault(dp["calendar_period"], {})[dp["series_id"]] = dp["value"]
    
    derived_specs = [
        # (sid, requires_all, calc_fn, note)
        ("ebitda",
         ["operating_income", "depreciation_amortization"],
         lambda v: v["operating_income"] + abs(v["depreciation_amortization"]),
         None),
        ("free_cash_flow",
         ["operating_cash_flow", "capex"],
         lambda v: v["operating_cash_flow"] - abs(v["capex"]),
         None),
        ("total_debt",
         ["short_term_debt", "long_term_debt"],
         lambda v: v["short_term_debt"] + v["long_term_debt"],
         None),
        ("diluted_shares_outstanding",
         ["net_income", "diluted_eps"],
         lambda v: v["net_income"] / v["diluted_eps"] if v["diluted_eps"] else None,
         "approx (net_income / diluted_eps)"),
    ]
    
    for sid, requires, calc_fn, note in derived_specs:
        # 요청에 명시적으로 포함됐거나, 빈 요청(전체)일 때만 계산
        if series_ids and sid not in series_ids:
            continue
        meta = KR_SERIES_CATALOG.get(sid)
        if not meta:
            continue
        for period, vals in by_period.items():
            # 이미 raw 매칭으로 들어가 있으면 skip
            if (sid, period) in seen:
                continue
            if not all(r in vals for r in requires):
                continue
            try:
                value = calc_fn(vals)
            except (ZeroDivisionError, TypeError):
                continue
            if value is None:
                continue
            label_en = meta["label_en"]
            if note:
                label_en = f"{label_en} — {note}"
            unique.append({
                "id": f"{code}_{sid}_{period}",
                "series_id": sid,
                "label": meta["label_kr"],
                "label_en": label_en,
                "category": meta["category"],
                "calendar_period": period,
                "fiscal_period": period,
                "value": value,
                "value_formatted": _format_kr(value, sid),
                "unit": "shares" if sid == "diluted_shares_outstanding" else "KRW",
                "source": "DART (calc.)",
                "source_url": f"https://dart.fss.or.kr/dsab007/main.do?option=corp&textCrpNm={code}",
            })
            seen.add((sid, period))
    
    unique.sort(key=lambda d: (d["series_id"], d["calendar_period"]))
    
    return {
        "company_id": code,
        "market": "KR",
        "periods_requested": periods,
        "series_requested": series_ids,
        "data": unique,
        "total": len(unique),
    }


def _documents_kr(query: str, tickers: list[str], year: int | None) -> dict[str, Any]:
    """DART 공시 검색."""
    if not DART_API_KEY:
        return {"query": query, "documents": [], "error": "DART_API_KEY 설정 필요"}
    
    docs = []
    try:
        from opendartreader import OpenDartReader as _ODR
        dart = _ODR(DART_API_KEY)

        if not year:
            year = datetime.now().year
        
        for ticker in tickers:
            code = _resolve_kr_ticker(ticker)
            if not code:
                continue
            
            try:
                # 정기공시 ('A') 검색
                lst = dart.list(code, start=f"{year-1}-01-01", end=f"{year}-12-31", kind="A")
                if lst is None or (hasattr(lst, "empty") and lst.empty):
                    continue
                
                for _, row in lst.iterrows():
                    docs.append({
                        "document_id": str(row.get("rcept_no", "")),
                        "title": str(row.get("report_nm", "")),
                        "form": str(row.get("report_nm", "")),
                        "filed_date": str(row.get("rcept_dt", "")),
                        "ticker": code,
                        "url": f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={row.get('rcept_no', '')}",
                        "snippet": query,  # DART는 본문 검색이 제한적, 제목만
                    })
            except Exception as e:
                _eprint(f"[warn] DART {ticker} 공시 검색 실패: {e}")
                continue
    
    except ImportError:
        return {"query": query, "documents": [], "error": "OpenDartReader 미설치"}
    
    return {"query": query, "total": len(docs), "documents": docs[:20]}


# ============================================================================
# 한국 시리즈 카탈로그 (DART account_nm 기반)
# ============================================================================

KR_SERIES_CATALOG: dict[str, dict[str, Any]] = {
    # 손익계산서
    "revenue":          {"label_kr": "매출액", "label_en": "Revenue", "category": "income_statement", "dart_labels": ["매출액", "수익(매출액)", "영업수익"]},
    "cost_of_revenue":  {"label_kr": "매출원가", "label_en": "Cost of Revenue", "category": "income_statement", "dart_labels": ["매출원가"]},
    "gross_profit":     {"label_kr": "매출총이익", "label_en": "Gross Profit", "category": "income_statement", "dart_labels": ["매출총이익"]},
    "sga":              {"label_kr": "판매비와관리비", "label_en": "SG&A", "category": "income_statement", "dart_labels": ["판매비와관리비"]},
    "rd_expense":       {"label_kr": "경상연구개발비", "label_en": "R&D Expense", "category": "income_statement", "dart_labels": ["경상연구개발비", "연구개발비", "경상개발비", "연구비", "연구및개발비용"]},
    "operating_income": {"label_kr": "영업이익", "label_en": "Operating Income", "category": "income_statement", "dart_labels": ["영업이익", "영업이익(손실)"]},
    "ebitda":           {"label_kr": "EBITDA (계산)", "label_en": "EBITDA (calc.)", "category": "income_statement", "dart_labels": [], "derived": True},
    "interest_expense": {"label_kr": "이자비용", "label_en": "Interest Expense", "category": "income_statement", "dart_labels": ["이자비용"]},
    "pretax_income":    {"label_kr": "법인세차감전순이익", "label_en": "Pretax Income", "category": "income_statement", "dart_labels": ["법인세비용차감전순이익", "법인세차감전순이익"]},
    "tax_expense":      {"label_kr": "법인세비용", "label_en": "Tax Expense", "category": "income_statement", "dart_labels": ["법인세비용"]},
    "net_income":       {"label_kr": "당기순이익", "label_en": "Net Income", "category": "income_statement", "dart_labels": ["당기순이익", "당기순이익(손실)"]},
    "diluted_eps":      {"label_kr": "희석주당이익", "label_en": "Diluted EPS", "category": "income_statement", "dart_labels": ["희석주당이익", "희석주당순이익"]},
    "basic_eps":        {"label_kr": "기본주당이익", "label_en": "Basic EPS", "category": "income_statement", "dart_labels": ["기본주당이익", "기본주당순이익"]},
    "diluted_shares_outstanding": {"label_kr": "가중평균유통보통주식수 (계산)", "label_en": "Diluted Shares Outstanding (calc.)", "category": "income_statement", "dart_labels": [], "derived": True},
    
    # 재무상태표
    "cash_and_equivalents":   {"label_kr": "현금및현금성자산", "label_en": "Cash & Equivalents", "category": "balance_sheet", "dart_labels": ["현금및현금성자산"]},
    "short_term_investments": {"label_kr": "단기금융상품", "label_en": "Short-term Investments", "category": "balance_sheet", "dart_labels": ["단기금융상품", "단기투자자산", "단기금융자산"]},
    "current_assets":   {"label_kr": "유동자산", "label_en": "Current Assets", "category": "balance_sheet", "dart_labels": ["유동자산"]},
    "inventory":        {"label_kr": "재고자산", "label_en": "Inventory", "category": "balance_sheet", "dart_labels": ["재고자산"]},
    "trade_receivables":{"label_kr": "매출채권", "label_en": "Trade Receivables", "category": "balance_sheet", "dart_labels": ["매출채권", "매출채권및기타채권"]},
    "total_assets":     {"label_kr": "자산총계", "label_en": "Total Assets", "category": "balance_sheet", "dart_labels": ["자산총계"]},
    "current_liabilities": {"label_kr": "유동부채", "label_en": "Current Liabilities", "category": "balance_sheet", "dart_labels": ["유동부채"]},
    "short_term_debt":  {"label_kr": "단기차입금", "label_en": "Short-term Debt", "category": "balance_sheet", "dart_labels": ["단기차입금", "유동성장기차입금", "유동성사채"]},
    "long_term_debt":   {"label_kr": "장기차입금", "label_en": "Long-term Debt", "category": "balance_sheet", "dart_labels": ["장기차입금", "장기사채", "비유동성장기차입금", "사채(비유동)"]},
    "total_debt":       {"label_kr": "총차입금 (계산)", "label_en": "Total Debt (calc.)", "category": "balance_sheet", "dart_labels": [], "derived": True},
    "total_liabilities":{"label_kr": "부채총계", "label_en": "Total Liabilities", "category": "balance_sheet", "dart_labels": ["부채총계"]},
    "total_equity":     {"label_kr": "자본총계", "label_en": "Total Equity", "category": "balance_sheet", "dart_labels": ["자본총계"]},
    
    # 현금흐름표
    "operating_cash_flow":       {"label_kr": "영업활동현금흐름", "label_en": "Operating Cash Flow", "category": "cash_flow", "dart_labels": ["영업활동으로인한현금흐름", "영업활동현금흐름", "영업활동 현금흐름"]},
    "depreciation_amortization": {"label_kr": "감가상각비 및 무형자산상각비", "label_en": "D&A", "category": "cash_flow", "dart_labels": ["감가상각비및무형자산상각비", "감가상각비와무형자산상각비", "감가상각비", "유형자산감가상각비", "무형자산상각비", "유형자산및무형자산상각비"]},
    "capex":            {"label_kr": "유형자산취득", "label_en": "CapEx", "category": "cash_flow", "dart_labels": ["유형자산의취득", "유형자산취득", "유형자산의 취득"]},
    "free_cash_flow":   {"label_kr": "잉여현금흐름 (계산)", "label_en": "FCF (calc.)", "category": "cash_flow", "dart_labels": [], "derived": True},
    "share_repurchase": {"label_kr": "자기주식의취득", "label_en": "Share Repurchase", "category": "cash_flow", "dart_labels": ["자기주식의취득", "자기주식취득", "자기주식의 취득"]},
    "dividends_paid":   {"label_kr": "배당금지급", "label_en": "Dividends Paid", "category": "cash_flow", "dart_labels": ["배당금의지급", "배당금지급", "배당금의 지급"]},
}


def _format_kr(v: float, sid: str) -> str:
    """한국식 숫자 포맷: 조 / 억 / 백만원 + 영문 단위 병기."""
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "n/a"
    if "eps" in sid:
        return f"{v:,.0f}원 (₩{v:,.0f})"
    if "shares" in sid:
        abs_v = abs(v)
        if abs_v >= 1e8:
            return f"{v/1e8:,.2f}억주 ({v/1e6:,.0f}M shares)"
        if abs_v >= 1e4:
            return f"{v/1e4:,.0f}만주 ({v:,.0f} shares)"
        return f"{v:,.0f}주"
    
    abs_v = abs(v)
    if abs_v >= 1e12:
        return f"{v/1e12:,.2f}조원 (₩{v/1e9:,.0f}bn)"
    if abs_v >= 1e8:
        return f"{v/1e8:,.0f}억원 (₩{v/1e9:,.2f}bn)"
    if abs_v >= 1e6:
        return f"{v/1e6:,.0f}백만원 (₩{v/1e6:,.0f}mm)"
    return f"{v:,.0f}원"


# ============================================================================
# US market: yfinance + SEC EDGAR (free_data.py에서 가져옴)
# ============================================================================

US_SERIES_CATALOG: dict[str, dict[str, Any]] = {
    "revenue":             {"labels": ["Total Revenue", "Operating Revenue"], "category": "income_statement"},
    "cost_of_revenue":     {"labels": ["Cost Of Revenue", "Reconciled Cost Of Revenue"], "category": "income_statement"},
    "gross_profit":        {"labels": ["Gross Profit"], "category": "income_statement"},
    "operating_income":    {"labels": ["Operating Income"], "category": "income_statement"},
    "ebitda":              {"labels": ["EBITDA", "Normalized EBITDA"], "category": "income_statement"},
    "net_income":          {"labels": ["Net Income", "Net Income Common Stockholders"], "category": "income_statement"},
    "diluted_eps":         {"labels": ["Diluted EPS"], "category": "income_statement"},
    "basic_eps":           {"labels": ["Basic EPS"], "category": "income_statement"},
    "diluted_shares":      {"labels": ["Diluted Average Shares"], "category": "income_statement"},
    "cash_and_equivalents":{"labels": ["Cash And Cash Equivalents", "Cash Cash Equivalents And Short Term Investments"], "category": "balance_sheet"},
    "current_assets":      {"labels": ["Current Assets"], "category": "balance_sheet"},
    "inventory":           {"labels": ["Inventory"], "category": "balance_sheet"},
    "total_assets":        {"labels": ["Total Assets"], "category": "balance_sheet"},
    "long_term_debt":      {"labels": ["Long Term Debt"], "category": "balance_sheet"},
    "total_debt":          {"labels": ["Total Debt"], "category": "balance_sheet"},
    "total_equity":        {"labels": ["Stockholders Equity", "Total Equity Gross Minority Interest"], "category": "balance_sheet"},
    "operating_cash_flow": {"labels": ["Operating Cash Flow", "Cash Flow From Continuing Operating Activities"], "category": "cash_flow"},
    "capex":               {"labels": ["Capital Expenditure", "Net PPE Purchase And Sale"], "category": "cash_flow"},
    "free_cash_flow":      {"labels": ["Free Cash Flow"], "category": "cash_flow"},
    "dividends_paid":      {"labels": ["Cash Dividends Paid"], "category": "cash_flow"},
    "share_repurchases":   {"labels": ["Repurchase Of Capital Stock"], "category": "cash_flow"},
}


_CIK_CACHE: dict[str, str] | None = None

def _ticker_to_cik(ticker: str) -> str | None:
    global _CIK_CACHE
    if _CIK_CACHE is None:
        try:
            r = requests.get("https://www.sec.gov/files/company_tickers.json", headers=SEC_HEADERS, timeout=10)
            r.raise_for_status()
            raw = r.json()
            _CIK_CACHE = {entry["ticker"].upper(): str(entry["cik_str"]).zfill(10) for entry in raw.values()}
        except Exception as e:
            _eprint(f"[warn] CIK table 로드 실패: {e}")
            _CIK_CACHE = {}
    return _CIK_CACHE.get(ticker.upper())


def _calendar_quarter_from_date(d) -> str:
    if hasattr(d, "date"):
        d = d.date()
    q = (d.month - 1) // 3 + 1
    return f"{d.year}Q{q}"


def _find_row_us(df, candidate_labels: list[str]):
    if df is None or df.empty:
        return None
    for label in candidate_labels:
        if label in df.index:
            return df.loc[label]
    lower_idx = {str(i).lower(): i for i in df.index}
    for label in candidate_labels:
        if label.lower() in lower_idx:
            return df.loc[lower_idx[label.lower()]]
    return None


def _format_us(v: float, sid: str) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "n/a"
    if "eps" in sid:
        return f"${v:.2f}"
    if "shares" in sid:
        if abs(v) >= 1e9:
            return f"{v/1e9:.2f}bn shares"
        return f"{v/1e6:,.0f}mm shares"
    if abs(v) >= 1e9:
        return f"${v/1e9:.2f}bn"
    if abs(v) >= 1e6:
        return f"${v/1e6:,.0f}mm"
    return f"${v:,.0f}"


def _companies_us(ticker: str) -> dict[str, Any]:
    import yfinance as yf
    yt = yf.Ticker(ticker.upper())
    try:
        info = yt.info or {}
    except Exception:
        info = {}
    cik = _ticker_to_cik(ticker)
    
    latest_cal_q = None
    fy_end_month = None
    try:
        qis = yt.quarterly_income_stmt
        if qis is not None and not qis.empty:
            latest_cal_q = _calendar_quarter_from_date(max(qis.columns))
    except Exception:
        pass
    
    if "lastFiscalYearEnd" in info:
        try:
            fy_end_month = datetime.fromtimestamp(info["lastFiscalYearEnd"]).date().month
        except Exception:
            pass
    
    return {"results": [{
        "company_id": ticker.upper(),
        "ticker": ticker.upper(),
        "market": "US",
        "name": info.get("longName") or info.get("shortName") or ticker.upper(),
        "name_en": info.get("longName") or info.get("shortName"),
        "cik": cik,
        "latest_calendar_quarter": latest_cal_q,
        "latest_fiscal_quarter": latest_cal_q,
        "fiscal_year_end_month": fy_end_month,
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "exchange": info.get("exchange"),
        "currency": info.get("currency", "USD"),
        "description": info.get("longBusinessSummary"),
    }]}


def _series_us(ticker: str, keywords: list[str]) -> dict[str, Any]:
    out = []
    for sid, meta in US_SERIES_CATALOG.items():
        if keywords:
            haystack = f"{sid} {' '.join(meta['labels'])}".lower()
            if not any(k.lower() in haystack for k in keywords):
                continue
        out.append({
            "series_id": sid,
            "label": meta["labels"][0],
            "category": meta["category"],
        })
    return {"company_id": ticker.upper(), "market": "US", "series": out, "total": len(out)}


def _fundamentals_us(ticker: str, periods: list[str], series_ids: list[str]) -> dict[str, Any]:
    import yfinance as yf
    if not series_ids:
        series_ids = list(US_SERIES_CATALOG.keys())
    
    yt = yf.Ticker(ticker.upper())
    try:
        qis = yt.quarterly_income_stmt
        qbs = yt.quarterly_balance_sheet
        qcf = yt.quarterly_cashflow
    except Exception as e:
        return {"company_id": ticker.upper(), "data": [], "error": str(e)}
    
    data_points = []
    for sid in series_ids:
        meta = US_SERIES_CATALOG.get(sid)
        if not meta:
            continue
        labels = meta["labels"]
        row = _find_row_us(qis, labels)
        if row is None:
            row = _find_row_us(qbs, labels)
        if row is None:
            row = _find_row_us(qcf, labels)
        if row is None:
            continue
        
        for col_date, value in row.items():
            if value is None or (isinstance(value, float) and math.isnan(value)):
                continue
            period_date = col_date.date() if hasattr(col_date, "date") else col_date
            cal_q = _calendar_quarter_from_date(period_date)
            if periods and cal_q not in periods:
                continue
            try:
                value_num = float(value)
            except (TypeError, ValueError):
                continue
            
            unit = "USD"
            if "eps" in sid:
                unit = "USD/share"
            elif "shares" in sid:
                unit = "shares"
            
            data_points.append({
                "id": f"{ticker.upper()}_{sid}_{cal_q}",
                "series_id": sid,
                "label": meta["labels"][0],
                "category": meta["category"],
                "calendar_period": cal_q,
                "fiscal_period": cal_q,
                "period_end_date": str(period_date),
                "value": value_num,
                "value_formatted": _format_us(value_num, sid),
                "unit": unit,
                "source": "yfinance",
                "source_url": f"https://finance.yahoo.com/quote/{ticker.upper()}/financials",
            })
    
    data_points.sort(key=lambda d: (d["series_id"], d["calendar_period"]))
    return {
        "company_id": ticker.upper(),
        "market": "US",
        "periods_requested": periods,
        "series_requested": series_ids,
        "data": data_points,
        "total": len(data_points),
    }


def _documents_us(query: str, tickers: list[str], forms: list[str], limit: int) -> dict[str, Any]:
    ciks = []
    for t in tickers:
        c = _ticker_to_cik(t)
        if c:
            ciks.append(c)
    
    params = {"q": f'"{query}"', "forms": ",".join(forms)}
    if ciks:
        params["ciks"] = ",".join(ciks)
    
    try:
        r = requests.get("https://efts.sec.gov/LATEST/search-index", params=params, headers=SEC_HEADERS, timeout=15)
        r.raise_for_status()
        raw = r.json()
    except Exception as e:
        return {"query": query, "documents": [], "error": str(e)}
    
    hits = raw.get("hits", {}).get("hits", [])
    docs = []
    for h in hits[:limit]:
        src = h.get("_source", {})
        doc_id = h.get("_id", "")
        if ":" in doc_id:
            acc_dashed, fname = doc_id.split(":", 1)
        else:
            acc_dashed, fname = doc_id, ""
        acc_clean = acc_dashed.replace("-", "")
        ciks_in_doc = src.get("ciks", [])
        cik_for_url = ciks_in_doc[0] if ciks_in_doc else ""
        url = f"https://www.sec.gov/Archives/edgar/data/{cik_for_url}/{acc_clean}/{fname}"
        snippet_parts = h.get("highlight", {}).get("description", [])
        snippet = " ... ".join(snippet_parts) if snippet_parts else src.get("file_description", "")
        docs.append({
            "document_id": acc_dashed,
            "title": (src.get("display_names") or ["Unknown"])[0],
            "form": src.get("form", ""),
            "filed_date": src.get("file_date", ""),
            "ciks": ciks_in_doc,
            "url": url,
            "snippet": snippet,
        })
    
    return {"query": query, "total": raw.get("hits", {}).get("total", {}).get("value", 0), "documents": docs}


# ============================================================================
# Japan market: yfinance with .T suffix
# ============================================================================

def _normalize_jp_ticker(ticker: str) -> str:
    """일본 티커 정규화: 7203 -> 7203.T"""
    t = ticker.strip().upper()
    if t.endswith(".T"):
        return t
    if re.match(r"^\d{4}$", t):
        return f"{t}.T"
    return t


def _companies_jp(ticker: str) -> dict[str, Any]:
    import yfinance as yf
    yf_ticker = _normalize_jp_ticker(ticker)
    yt = yf.Ticker(yf_ticker)
    try:
        info = yt.info or {}
    except Exception:
        info = {}
    
    latest_cal_q = None
    fy_end_month = None
    try:
        qis = yt.quarterly_income_stmt
        if qis is not None and not qis.empty:
            latest_cal_q = _calendar_quarter_from_date(max(qis.columns))
    except Exception:
        pass
    
    if "lastFiscalYearEnd" in info:
        try:
            fy_end_month = datetime.fromtimestamp(info["lastFiscalYearEnd"]).date().month
        except Exception:
            pass
    
    return {"results": [{
        "company_id": yf_ticker,
        "ticker": yf_ticker,
        "market": "JP",
        "name": info.get("longName") or info.get("shortName") or yf_ticker,
        "name_en": info.get("longName") or info.get("shortName"),
        "latest_calendar_quarter": latest_cal_q,
        "latest_fiscal_quarter": latest_cal_q,
        "fiscal_year_end_month": fy_end_month,
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "exchange": info.get("exchange"),
        "currency": info.get("currency", "JPY"),
        "description": info.get("longBusinessSummary"),
    }]}


def _format_jp(v: float, sid: str) -> str:
    """일본식 숫자 포맷: 兆 / 億 / 百万円."""
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "n/a"
    if "eps" in sid:
        return f"¥{v:,.0f}"
    abs_v = abs(v)
    if abs_v >= 1e12:
        return f"{v/1e12:,.2f}兆円 (¥{v/1e9:,.0f}bn)"
    if abs_v >= 1e8:
        return f"{v/1e8:,.0f}億円 (¥{v/1e9:,.2f}bn)"
    if abs_v >= 1e6:
        return f"{v/1e6:,.0f}百万円 (¥{v/1e6:,.0f}mm)"
    return f"¥{v:,.0f}"


def _fundamentals_jp(ticker: str, periods: list[str], series_ids: list[str]) -> dict[str, Any]:
    """일본은 yfinance만 사용 (US와 동일 로직, ticker만 .T 추가)."""
    import yfinance as yf
    if not series_ids:
        series_ids = list(US_SERIES_CATALOG.keys())
    
    yf_ticker = _normalize_jp_ticker(ticker)
    yt = yf.Ticker(yf_ticker)
    try:
        qis = yt.quarterly_income_stmt
        qbs = yt.quarterly_balance_sheet
        qcf = yt.quarterly_cashflow
    except Exception as e:
        return {"company_id": yf_ticker, "data": [], "error": str(e)}
    
    data_points = []
    for sid in series_ids:
        meta = US_SERIES_CATALOG.get(sid)
        if not meta:
            continue
        labels = meta["labels"]
        row = _find_row_us(qis, labels)
        if row is None:
            row = _find_row_us(qbs, labels)
        if row is None:
            row = _find_row_us(qcf, labels)
        if row is None:
            continue
        
        for col_date, value in row.items():
            if value is None or (isinstance(value, float) and math.isnan(value)):
                continue
            period_date = col_date.date() if hasattr(col_date, "date") else col_date
            cal_q = _calendar_quarter_from_date(period_date)
            if periods and cal_q not in periods:
                continue
            try:
                value_num = float(value)
            except (TypeError, ValueError):
                continue
            
            unit = "JPY"
            if "eps" in sid:
                unit = "JPY/share"
            elif "shares" in sid:
                unit = "shares"
            
            data_points.append({
                "id": f"{yf_ticker}_{sid}_{cal_q}",
                "series_id": sid,
                "label": meta["labels"][0],
                "category": meta["category"],
                "calendar_period": cal_q,
                "fiscal_period": cal_q,
                "period_end_date": str(period_date),
                "value": value_num,
                "value_formatted": _format_jp(value_num, sid),
                "unit": unit,
                "source": "yfinance",
                "source_url": f"https://finance.yahoo.com/quote/{yf_ticker}/financials",
            })
    
    data_points.sort(key=lambda d: (d["series_id"], d["calendar_period"]))
    return {
        "company_id": yf_ticker,
        "market": "JP",
        "periods_requested": periods,
        "series_requested": series_ids,
        "data": data_points,
        "total": len(data_points),
    }


# ============================================================================
# Unified routing
# ============================================================================

def cmd_companies(args) -> dict[str, Any]:
    market = args.market or detect_market(args.ticker)
    if market == "KR":
        return _companies_kr(args.ticker)
    elif market == "JP":
        return _companies_jp(args.ticker)
    else:
        return _companies_us(args.ticker)


def cmd_series(args) -> dict[str, Any]:
    market = args.market or detect_market(args.ticker)
    keywords = []
    if args.keywords:
        keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
    if market == "KR":
        return _series_kr(args.ticker, keywords)
    else:
        return _series_us(args.ticker, keywords)


def cmd_fundamentals(args) -> dict[str, Any]:
    market = args.market or detect_market(args.ticker)
    periods = []
    if args.periods:
        periods = [p.strip() for p in args.periods.split(",") if p.strip()]
    series_ids = []
    if args.series:
        series_ids = [s.strip() for s in args.series.split(",") if s.strip()]
    
    if market == "KR":
        return _fundamentals_kr(args.ticker, periods, series_ids)
    elif market == "JP":
        return _fundamentals_jp(args.ticker, periods, series_ids)
    else:
        return _fundamentals_us(args.ticker, periods, series_ids)


def cmd_documents(args) -> dict[str, Any]:
    tickers = []
    if args.tickers:
        tickers = [t.strip() for t in args.tickers.split(",") if t.strip()]
    
    # 시장 감지: 첫 번째 ticker로 결정
    market = args.market
    if not market and tickers:
        market = detect_market(tickers[0])
    
    if market == "KR":
        return _documents_kr(args.query, tickers, args.year)
    else:
        # US: forms
        forms = (args.forms or "10-K,10-Q,8-K").split(",")
        return _documents_us(args.query, tickers, forms, args.limit)


# ============================================================================
# CLI
# ============================================================================

def main():
    # Windows cp949 콘솔에서도 ₩ 및 한글 출력 안전하게 (UTF-8 강제)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, Exception):
        pass  # 일부 환경에서 reconfigure 미지원
    
    parser = argparse.ArgumentParser(
        description="한국/미국/일본 시장 통합 데이터 wrapper (DART + yfinance + SEC EDGAR)"
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    
    # 공통 --market 옵션
    def add_market_arg(p):
        p.add_argument("--market", choices=["KR", "US", "JP"], help="명시적 시장 지정 (기본: 자동 감지)")
    
    p = sub.add_parser("companies", help="회사 정보 조회 (= discover_companies)")
    p.add_argument("ticker", help="티커 (예: 005930, AAPL, 7203, 삼성전자)")
    add_market_arg(p)
    
    p = sub.add_parser("series", help="사용 가능 메트릭 목록 (= discover_company_series)")
    p.add_argument("ticker")
    p.add_argument("--keywords", help="필터 키워드 (콤마 구분)")
    add_market_arg(p)
    
    p = sub.add_parser("fundamentals", help="재무 데이터 조회 (= get_company_fundamentals)")
    p.add_argument("ticker")
    p.add_argument("--periods", help="분기 (콤마 구분, 예: 2024Q1,2024Q2)")
    p.add_argument("--series", help="시리즈 ID (콤마 구분, 예: revenue,net_income)")
    add_market_arg(p)
    
    p = sub.add_parser("documents", help="공시/Filing 검색 (= search_documents)")
    p.add_argument("query", help="검색어")
    p.add_argument("--tickers", help="티커 (콤마 구분)")
    p.add_argument("--forms", help="[US/JP] 보고서 종류 (기본: 10-K,10-Q,8-K)")
    p.add_argument("--year", type=int, help="[KR] 검색 연도")
    p.add_argument("--limit", type=int, default=10)
    add_market_arg(p)
    
    args = parser.parse_args()
    
    handlers = {
        "companies": cmd_companies,
        "series": cmd_series,
        "fundamentals": cmd_fundamentals,
        "documents": cmd_documents,
    }
    
    result = handlers[args.cmd](args)
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
