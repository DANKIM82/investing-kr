"""SkillRunner - 모든 skill 공통 파이프라인. v3: market_data 자동 포함."""

import json
from abc import ABC, abstractmethod
from pathlib import Path

from core.data_fetcher import (
    get_company, get_fundamentals, get_market_data, validate_normalization
)
from core.llm_client import call_claude


REPO_ROOT = Path(__file__).parent.parent.parent


class SkillRunner(ABC):
    skill_name: str = ""
    skill_display_name: str = ""
    skill_md_relative_path: str = ""
    fetch_periods: list[str] | None = None  # None이면 yfinance/DART가 주는 대로
    # market_data가 필요한 skill은 True (DCF 등). 기본 False로 비용 절약
    needs_market_data: bool = False
    # 최근 N분기로 자른다 (data가 더 많이 와도). None이면 전부.
    max_recent_quarters: int | None = 8

    @property
    def skill_md_path(self) -> Path:
        return REPO_ROOT / self.skill_md_relative_path

    def load_skill_prompt(self) -> str:
        if not self.skill_md_path.exists():
            print(f"  ⚠ SKILL.md 없음: {self.skill_md_path}")
            return ""
        return self.skill_md_path.read_text(encoding="utf-8")

    def fetch_data(self, ticker: str) -> dict:
        company = get_company(ticker)
        fundamentals = get_fundamentals(ticker, periods=self.fetch_periods)

        # 최근 N분기로 자르기
        if self.max_recent_quarters and fundamentals["periods"]:
            recent = fundamentals["periods"][-self.max_recent_quarters:]
            fundamentals["periods"] = recent
            fundamentals["normalized"] = {
                series_id: {p: v for p, v in pv.items() if p in recent}
                for series_id, pv in fundamentals["normalized"].items()
            }

        market_data = {}
        if self.needs_market_data:
            print(f"  💹 시장 데이터 fetch 중...")
            market_data = get_market_data(ticker)
            if market_data.get("available"):
                print(f"     주가 {market_data.get('price')}, 시총 {market_data.get('market_cap'):,.0f}")

        return {
            "company": company,
            "fundamentals": fundamentals,
            "market_data": market_data,
        }

    @abstractmethod
    def build_context(self, data: dict) -> dict:
        ...

    @abstractmethod
    def build_prompt_schema(self) -> str:
        ...

    def build_system_prompt(self) -> str:
        skill_prompt = self.load_skill_prompt()
        schema = self.build_prompt_schema()
        return f"""너는 한국/미국/일본 시장 투자 리서치 애널리스트다.
사전 수집된 실제 데이터를 기반으로 {self.skill_display_name or self.skill_name}의 정성적 분석을 JSON으로 출력한다.

<skill_definition>
{skill_prompt}
</skill_definition>

규칙:
- 제공된 데이터의 실제 수치를 직접 인용.
- 추측 금지. 데이터에 없으면 만들지 마라.
- 통화 단위는 company.currency 를 따른다.
- 출력은 JSON 한 덩어리. 다른 텍스트 금지.

JSON 스키마:
{schema}"""

    def build_user_message(self, ticker, context, data):
        company_name = data.get("company", {}).get("name", ticker)
        return f"""다음 데이터로 {company_name}({ticker}) {self.skill_display_name or self.skill_name} 분석을 작성하라.

<pre_fetched_data>
{json.dumps(context, ensure_ascii=False, indent=2, default=str)}
</pre_fetched_data>"""

    @abstractmethod
    def render(self, ticker, data, analysis):
        ...

    def run(self, ticker, model="claude-sonnet-4-6", max_tokens=3500, validate=True):
        print(f"[1/4] {ticker} 데이터 수집 중...")
        data = self.fetch_data(ticker)

        company_name = data.get("company", {}).get("name", "N/A")
        fund = data.get("fundamentals", {})
        market = fund.get("market", "KR")
        print(f"  회사명: {company_name}  (시장: {market})")
        print(f"  fundamentals: {fund.get('data_count', 0)} 포인트, 최근 {len(fund.get('periods', []))} 분기 사용")

        if validate and fund.get("raw_pivot"):
            print(f"\n[2/4] 정규화 검증:")
            validate_normalization(fund["raw_pivot"], fund["normalized"], market=market)

        print(f"\n[3/4] Claude API 호출 ({model})...")
        context = self.build_context(data)
        system_prompt = self.build_system_prompt()
        user_message = self.build_user_message(ticker, context, data)

        response = call_claude(
            system_prompt=system_prompt,
            user_message=user_message,
            model=model,
            max_tokens=max_tokens,
        )

        print(f"\n[4/4] HTML 렌더링...")
        html = self.render(ticker, data, response.analysis)

        # ticker sanitize for filename
        safe_ticker = ticker.replace(",", "_").replace(" ", "").replace("/", "_")
        output_path = REPO_ROOT / "reports" / f"{safe_ticker}_{self.skill_name}.html"
        output_path.parent.mkdir(exist_ok=True)
        output_path.write_text(html, encoding="utf-8")

        print(f"\n완료 → {output_path}")
        t = response.tokens
        print(f"  Cost: ${response.cost:.4f}  (tokens: in={t['input']:,} cache_r={t['cache_read']:,} cache_w={t['cache_write']:,} out={t['output']:,})")

        return {
            "ticker": ticker,
            "skill": self.skill_name,
            "data": data,
            "analysis": response.analysis,
            "output_path": str(output_path),
            "cost": response.cost,
            "tokens": response.tokens,
        }
