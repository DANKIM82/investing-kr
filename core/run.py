"""CLI: python -m core.run <skill> <ticker> [--model claude-haiku-4-5]"""

import sys

from dotenv import load_dotenv
load_dotenv()

from core.skills.tearsheet import TearsheetSkill
from core.skills.earnings import EarningsSkill
from core.skills.dcf import DCFSkill
from core.skills.bull_bear import BullBearSkill


SKILLS = {
    "tearsheet": TearsheetSkill,
    "earnings": EarningsSkill,
    "dcf": DCFSkill,
    "bull_bear": BullBearSkill,
}


def main():
    if len(sys.argv) < 3:
        print("사용법: python -m core.run <skill> <ticker> [--model claude-sonnet-4-6]")
        print(f"사용 가능 skill: {', '.join(SKILLS.keys())}")
        sys.exit(1)

    skill_name = sys.argv[1]
    ticker = sys.argv[2]

    model = "claude-sonnet-4-6"
    if "--model" in sys.argv:
        idx = sys.argv.index("--model")
        if idx + 1 < len(sys.argv):
            model = sys.argv[idx + 1]

    skill_cls = SKILLS.get(skill_name)
    if not skill_cls:
        print(f"⚠ 알 수 없는 skill: {skill_name}")
        print(f"사용 가능: {', '.join(SKILLS.keys())}")
        sys.exit(1)

    runner = skill_cls()
    runner.run(ticker, model=model)


if __name__ == "__main__":
    main()
