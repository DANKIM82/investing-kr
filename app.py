"""투자 분석 toolkit - v5 (Industry 비교 추가)."""
import os
import sys
import traceback
from pathlib import Path

import streamlit as st

REPO_ROOT = Path(__file__).parent
sys.path.insert(0, str(REPO_ROOT))

try:
    if hasattr(st, "secrets") and len(st.secrets) > 0:
        for key in st.secrets:
            os.environ[key] = str(st.secrets[key])
except Exception:
    pass
from dotenv import load_dotenv
load_dotenv()

from core.skills.tearsheet import TearsheetSkill
from core.skills.earnings import EarningsSkill
from core.skills.dcf import DCFSkill
from core.skills.bull_bear import BullBearSkill
from core.skills.industry import IndustrySkill
from core import company_search


SINGLE_SKILLS = {
    "tearsheet": {
        "display": "📋 Tearsheet — 회사 1페이지 요약",
        "class": TearsheetSkill,
        "desc": "회사 개요 + 5대 Bull/Bear tensions + 8분기 재무 + 모니터링 지표",
    },
    "earnings": {
        "display": "📊 Earnings Review — 최근 분기 실적 분석",
        "class": EarningsSkill,
        "desc": "최근 분기 헤드라인 + 매출/마진/현금흐름 deep dive",
    },
    "dcf": {
        "display": "💰 DCF Valuation — 적정 주가 평가",
        "class": DCFSkill,
        "desc": "5년 projection + Bull/Base/Bear 적정 가치 + 민감도",
    },
    "bull_bear": {
        "display": "🎯 Bull/Base/Bear — 시나리오 분석",
        "class": BullBearSkill,
        "desc": "낙관/중립/비관 3가지 시나리오 + 확률 + 관찰 포인트",
    },
}

EXAMPLES = [
    ("005930", "🇰🇷 삼성전자"), ("000660", "🇰🇷 SK하이닉스"),
    ("035420", "🇰🇷 네이버"), ("035720", "🇰🇷 카카오"),
    ("AAPL", "🇺🇸 Apple"), ("NVDA", "🇺🇸 NVIDIA"),
    ("7203", "🇯🇵 Toyota"), ("6758", "🇯🇵 Sony"),
]

INDUSTRY_PRESETS = [
    ("한국 인터넷", ["035420", "035720"]),
    ("메모리 반도체", ["005930", "000660", "MU"]),
    ("AI 칩", ["NVDA", "AMD", "AVGO"]),
    ("스마트폰", ["AAPL", "005930", "9984"]),
    ("미국 빅테크", ["AAPL", "MSFT", "GOOGL", "META", "AMZN"]),
]


def render_result(result, is_industry=False):
    """결과 렌더링 - 단일/Industry 공통."""
    data = result["data"]

    metric_cols = st.columns(4)
    if is_industry:
        with metric_cols[0]:
            st.metric("비교 회사", f"{len(data.get('ticker_list', []))}개")
        with metric_cols[1]:
            st.metric("통화", "USD 환산")
        with metric_cols[2]:
            st.metric("분기", "최근 8")
        with metric_cols[3]:
            st.metric("API 비용", f"${result['cost']:.4f}")
    else:
        company = data.get("company", {})
        fund = data.get("fundamentals", {})
        with metric_cols[0]:
            st.metric("회사", company.get("name", "?"))
        with metric_cols[1]:
            st.metric("시장", fund.get("market", "?"))
        with metric_cols[2]:
            st.metric("통화", company.get("currency", "?"))
        with metric_cols[3]:
            st.metric("API 비용", f"${result['cost']:.4f}")

    html_path = Path(result["output_path"])
    if html_path.exists():
        html_content = html_path.read_text(encoding="utf-8")
        download_col, _ = st.columns([1, 5])
        with download_col:
            st.download_button(
                "📥 HTML 다운로드",
                data=html_content,
                file_name=html_path.name,
                mime="text/html",
                use_container_width=True,
            )
        st.components.v1.html(html_content, height=2800, scrolling=True)


# ─────────────────────────────────────────────────
st.set_page_config(page_title="투자 분석 toolkit", page_icon="📊", layout="wide")
st.title("📊 투자 분석 toolkit")
st.caption("DART · yfinance · SEC EDGAR · Claude AI · 무료 베타")

if not os.getenv("ANTHROPIC_API_KEY", "").startswith("sk-ant-"):
    st.error("⚠ ANTHROPIC_API_KEY 가 설정되지 않았습니다.")
    st.stop()

if not company_search.is_index_available():
    st.warning("⚠ 회사 인덱스 미빌드. `python scripts/build_company_index.py` 실행 필요.")


# 세션 상태
for k, v in {
    "search_results": [],
    "selected_ticker": None,
    "selected_company": None,
    "industry_tickers": [],
    "industry_search_results": [],
}.items():
    if k not in st.session_state:
        st.session_state[k] = v


tab_single, tab_industry = st.tabs(["🔍 단일 회사 분석", "🏭 Industry 비교 (다회사)"])


# ─────────────────────────────────────────────────
# 단일 회사 탭
# ─────────────────────────────────────────────────
with tab_single:
    with st.container(border=True):
        col1, col2 = st.columns([3, 2])

        with col1:
            st.markdown("**🔍 회사 검색**")
            s_col, b_col = st.columns([4, 1])
            with s_col:
                query = st.text_input("검색", placeholder="삼성, Apple, 미코, 005930 ...",
                                       label_visibility="collapsed", key="q_single")
            with b_col:
                if st.button("🔍 검색", use_container_width=True, key="search_single"):
                    if query:
                        results = company_search.search(query, limit=10)
                        st.session_state.search_results = results
                        st.session_state.selected_ticker = None
                        if not results:
                            st.info(f"'{query}' 검색 결과 없음. 직접 종목코드를 입력하세요.")

            if st.session_state.search_results:
                labels = [company_search.format_label(c) for c in st.session_state.search_results]
                choice = st.radio(f"검색 결과 ({len(labels)}개)", options=labels, key="choice_single")
                idx = labels.index(choice)
                chosen = st.session_state.search_results[idx]
                st.session_state.selected_ticker = chosen["ticker"]
                st.session_state.selected_company = chosen

            st.markdown("---")
            st.markdown("**또는 빠른 예시**")
            for row in range(2):
                cols = st.columns(4)
                for c_idx, col in enumerate(cols):
                    i = row * 4 + c_idx
                    if i < len(EXAMPLES):
                        t, label = EXAMPLES[i]
                        with col:
                            if st.button(label, use_container_width=True, key=f"ex_{t}"):
                                st.session_state.selected_ticker = t
                                st.session_state.selected_company = {"ticker": t, "name": label}
                                st.session_state.search_results = []

            ticker = st.session_state.selected_ticker
            if ticker:
                name = (st.session_state.selected_company or {}).get("name", ticker)
                st.success(f"✓ 선택: **{name}** ({ticker})")

        with col2:
            skill_name = st.radio("분석 종류",
                                  options=list(SINGLE_SKILLS.keys()),
                                  format_func=lambda x: SINGLE_SKILLS[x]["display"])
            st.caption(SINGLE_SKILLS[skill_name]["desc"])
            st.write("")
            run_single = st.button("🚀 분석 실행", type="primary", use_container_width=True,
                                    disabled=not ticker, key="run_single")


# ─────────────────────────────────────────────────
# Industry 탭
# ─────────────────────────────────────────────────
with tab_industry:
    with st.container(border=True):
        st.markdown("**🏭 비교할 회사들 (2-5개)**")

        st.markdown("**산업군 프리셋:**")
        preset_cols = st.columns(len(INDUSTRY_PRESETS))
        for i, (preset_name, preset_tickers) in enumerate(INDUSTRY_PRESETS):
            with preset_cols[i]:
                if st.button(preset_name, key=f"preset_{i}", use_container_width=True):
                    st.session_state.industry_tickers = list(preset_tickers)
                    st.rerun()

        st.markdown("---")
        st.markdown("**또는 직접 검색해서 추가:**")
        s_col, b_col = st.columns([4, 1])
        with s_col:
            ind_query = st.text_input("검색", placeholder="회사명 또는 ticker",
                                       label_visibility="collapsed", key="q_industry")
        with b_col:
            if st.button("🔍 검색", use_container_width=True, key="search_industry"):
                if ind_query:
                    st.session_state.industry_search_results = company_search.search(ind_query, limit=10)

        if st.session_state.industry_search_results:
            labels = [company_search.format_label(c) for c in st.session_state.industry_search_results]
            choice = st.radio("회사 선택 후 추가", options=labels, key="choice_industry")
            idx = labels.index(choice)
            chosen = st.session_state.industry_search_results[idx]
            add_col, _ = st.columns([1, 4])
            with add_col:
                if st.button("➕ 리스트에 추가", key="add_btn"):
                    if len(st.session_state.industry_tickers) >= 5:
                        st.warning("최대 5개")
                    elif chosen["ticker"] in st.session_state.industry_tickers:
                        st.info("이미 추가됨")
                    else:
                        st.session_state.industry_tickers.append(chosen["ticker"])
                        st.session_state.industry_search_results = []
                        st.rerun()

        st.markdown("---")
        n = len(st.session_state.industry_tickers)
        st.markdown(f"**📋 비교 대상 ({n}/5):**")
        if n == 0:
            st.info("프리셋을 누르거나 검색해서 회사를 추가하세요. 최소 2개 필요.")
        else:
            chip_cols = st.columns(5)
            for i, t in enumerate(st.session_state.industry_tickers):
                with chip_cols[i]:
                    if st.button(f"❌ {t}", key=f"rm_{t}", use_container_width=True):
                        st.session_state.industry_tickers.remove(t)
                        st.rerun()

        st.write("")
        run_industry = st.button("🚀 Industry 비교 실행", type="primary", use_container_width=True,
                                  disabled=n < 2, key="run_industry")

st.caption("⚠ 학습·참고용. 실제 투자 결정에 사용 금지. 데이터 정확성 audit-grade 아님.")


# ─────────────────────────────────────────────────
# 실행
# ─────────────────────────────────────────────────
if run_single and st.session_state.selected_ticker:
    ticker = st.session_state.selected_ticker
    skill_cls = SINGLE_SKILLS[skill_name]["class"]
    runner = skill_cls()

    with st.status(f"{ticker} 분석 중...", expanded=True) as status:
        try:
            st.write("📡 데이터 수집 (DART / yfinance / SEC EDGAR)...")
            if skill_cls.needs_market_data:
                st.write("💹 실시간 시장 데이터 fetch...")
            st.write(f"🧠 Claude로 {SINGLE_SKILLS[skill_name]['display']} 생성 중 (~30-60초)...")
            max_tokens_map = {"dcf": 6000, "bull_bear": 5000, "tearsheet": 3500, "earnings": 3500}
            result = runner.run(ticker, max_tokens=max_tokens_map.get(skill_name, 3500))
            status.update(label=f"✅ {ticker} 완료 (${result['cost']:.4f})",
                          state="complete", expanded=False)
        except Exception as e:
            status.update(label="❌ 분석 실패", state="error")
            st.error(f"오류: {e}")
            with st.expander("상세 오류 로그"):
                st.code(traceback.format_exc())
            st.stop()

    render_result(result, is_industry=False)


if run_industry and len(st.session_state.industry_tickers) >= 2:
    tickers = list(st.session_state.industry_tickers)
    runner = IndustrySkill(tickers=tickers)

    with st.status(f"{len(tickers)}개 회사 비교 중...", expanded=True) as status:
        try:
            st.write(f"📡 {len(tickers)}개 회사 데이터 수집 (회사당 ~10-15초)...")
            st.write("💹 실시간 시장 데이터 fetch (전 회사)...")
            st.write("🌐 USD 환산 통일...")
            st.write("🧠 Claude로 산업 비교 분석 생성 중 (~60-90초)...")
            result = runner.run(max_tokens=6000)
            status.update(label=f"✅ {' vs '.join(tickers)} 완료 (${result['cost']:.4f})",
                          state="complete", expanded=False)
        except Exception as e:
            status.update(label="❌ 분석 실패", state="error")
            st.error(f"오류: {e}")
            with st.expander("상세 오류 로그"):
                st.code(traceback.format_exc())
            st.stop()

    render_result(result, is_industry=True)
