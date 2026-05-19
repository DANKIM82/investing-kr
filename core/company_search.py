"""회사 마스터 인덱스 검색 - JSON 로드 + fuzzy match."""

import json
import re
from functools import lru_cache
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
INDEX_PATH = REPO_ROOT / "data" / "companies_master.json"


@lru_cache(maxsize=1)
def _load_index() -> list[dict]:
    """JSON 파일 한 번만 로드 (memoize)."""
    if not INDEX_PATH.exists():
        return []
    try:
        return json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"⚠ 회사 인덱스 로드 실패: {e}")
        return []


def search(query: str, limit: int = 10) -> list[dict]:
    """
    회사 검색.

    매칭 규칙 (우선순위 순):
    1. ticker 정확 일치 (대소문자 무시)
    2. 이름 정확 일치
    3. 이름 시작 일치
    4. 이름 부분 일치
    5. ticker 부분 일치

    각 매칭 안에서는 시총 큰 순으로 정렬.
    """
    index = _load_index()
    if not index or not query or not query.strip():
        return []

    q = query.strip().lower()
    q_upper = query.strip().upper()

    # 6/4자리 숫자 → ticker 정확 매칭 우선
    if re.match(r"^\d{4,6}$", q):
        for c in index:
            if c.get("ticker") == q:
                return [c]

    exact_ticker = []
    exact_name = []
    starts_name = []
    contains_name = []
    contains_ticker = []

    for c in index:
        ticker = (c.get("ticker") or "").lower()
        name = (c.get("name") or "").lower()

        if not ticker and not name:
            continue

        if ticker == q:
            exact_ticker.append(c)
        elif name == q:
            exact_name.append(c)
        elif name.startswith(q):
            starts_name.append(c)
        elif q in name:
            contains_name.append(c)
        elif q in ticker:
            contains_ticker.append(c)

    # 각 그룹 시총순 정렬
    def by_mcap(c):
        return -(c.get("market_cap") or 0)

    for lst in [exact_ticker, exact_name, starts_name, contains_name, contains_ticker]:
        lst.sort(key=by_mcap)

    combined = exact_ticker + exact_name + starts_name + contains_name + contains_ticker
    return combined[:limit]


def format_label(c: dict) -> str:
    """검색 결과 표시용 라벨."""
    market_emoji = {"KR": "🇰🇷", "US": "🇺🇸", "JP": "🇯🇵"}
    emoji = market_emoji.get(c.get("market", ""), "🌐")
    name = c.get("name", "?")
    ticker = c.get("ticker", "?")
    return f"{emoji} {name} ({ticker})"


def is_index_available() -> bool:
    return INDEX_PATH.exists() and len(_load_index()) > 0
