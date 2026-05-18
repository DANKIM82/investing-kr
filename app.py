"""
투자 분석 toolkit - Streamlit MVP.

로컬 실행:
    pip install streamlit
    streamlit run app.py

Streamlit Cloud 배포:
    1. requirements.txt 에 'streamlit' 추가
    2. GitHub push
    3. share.streamlit.io 에서 repo 연결
    4. Secrets에 ANTHROPIC_API_KEY, DART_API_KEY, SEC_USER_AGENT 입력
"""
import os
import sys
import traceback
from pathlib import Path

import streamlit as st

REPO_ROOT = Path(__file__).parent
sys.path.insert(0, str(REPO_ROOT))

# Streamlit Cloud는 st.secrets, 로컬은 .env
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


SKILLS = {
    "tearsheet": {
        "display": "Tearsheet — 회사 1페이지 요약",
        "class": TearsheetSkill,
        "desc": "회사 개요 + 5대 Bull/Bear tensions + 8분기 재무 + 모니터링 지표",
    },
    "earnings": {
        "display": "Earnings Review — 최근 분기 실적 분석",
        "class": EarningsSkill,
        "desc": "최근 분기 헤드라인 + 매출/마진/현금흐름 deep dive",
    },
}

EXAMPLES = [
    ("005930", "🇰🇷 삼성전자"),
    ("035420", "🇰🇷 네이버"),
    ("AAPL", "🇺🇸 Apple"),
    ("7203", "🇯🇵 Toyota"),
]


st.set_page_config(
    page_title="투자 분석 toolkit",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.title("📊 투자 분석 toolkit")
st.caption("DART · yfinance · SEC EDGAR · Claude AI · 무료 (베타)")

# API 키 체크
if not os.getenv("ANTHROPIC_API_KEY", "").startswith("sk-ant-"):
    st.error("⚠ ANTHROPIC_API_KEY 가 설정되지 않았습니다. `.env` 또는 Streamlit Secrets 확인.")
    st.stop()


# ─────────────────────────────────────────────────
# 입력 영역
# ─────────────────────────────────────────────────
with st.container(border=True):
    col1, col2 = st.columns([3, 2])

    with col1:
        st.markdown("**빠른 예시**")
        ex_cols = st.columns(len(EXAMPLES))
        for col, (t, label) in zip(ex_cols, EXAMPLES):
            with col:
                if st.button(label, use_container_width=True, key=f"ex_{t}"):
                    st.session_state["ticker_input"] = t

        ticker = st.text_input(
            "종목 코드",
            value=st.session_state.get("ticker_input", ""),
            placeholder="예: 005930 (KR) / AAPL (US) / 7203 (JP)",
            help="한국 6자리 / 미국 영문 / 일본 4자리 — 자동 감지",
        )

    with col2:
        skill_name = st.radio(
            "분석 종류",
            options=list(SKILLS.keys()),
            format_func=lambda x: SKILLS[x]["display"],
        )
        st.caption(SKILLS[skill_name]["desc"])
        st.write("")
        run = st.button("🚀 분석 실행", type="primary", use_container_width=True)

st.caption("⚠ 학습·참고용 도구. 실제 투자 결정에 사용 금지. 데이터 정확성 audit-grade 아님.")


# ─────────────────────────────────────────────────
# 실행
# ─────────────────────────────────────────────────
if run and ticker:
    skill_cls = SKILLS[skill_name]["class"]
    runner = skill_cls()

    with st.status(f"{ticker} 분석 중...", expanded=True) as status:
        try:
            st.write("📡 데이터 수집 중 (DART / yfinance / SEC EDGAR)...")
            st.write("🧠 Claude 분석 호출 중 (~30초)...")
            result = runner.run(ticker)
            status.update(
                label=f"✅ {ticker} 분석 완료 (비용 ${result['cost']:.4f})",
                state="complete",
                expanded=False,
            )
        except Exception as e:
            status.update(label="❌ 분석 실패", state="error")
            st.error(f"오류: {e}")
            with st.expander("상세 오류 로그"):
                st.code(traceback.format_exc())
            st.stop()

    # 결과 요약 카드
    company = result["data"].get("company", {})
    fund = result["data"].get("fundamentals", {})

    metric_cols = st.columns(4)
    with metric_cols[0]:
        st.metric("회사", company.get("name", "?"))
    with metric_cols[1]:
        st.metric("시장", fund.get("market", "?"))
    with metric_cols[2]:
        st.metric("통화", company.get("currency", "?"))
    with metric_cols[3]:
        st.metric("API 비용", f"${result['cost']:.4f}")

    # HTML 리포트
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

        st.components.v1.html(html_content, height=2400, scrolling=True)

elif run and not ticker:
    st.warning("종목 코드를 입력하거나 빠른 예시를 눌러주세요.")
