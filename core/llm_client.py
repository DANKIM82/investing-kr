"""Claude API 호출 wrapper - prompt caching + JSON 파싱 + 비용 계산."""

import json
from dataclasses import dataclass, field

from anthropic import Anthropic


# Per million tokens (USD) - 2026.05 기준
PRICING = {
    "claude-sonnet-4-6": {"input": 3.00, "cache_read": 0.30, "cache_write": 3.75, "output": 15.00},
    "claude-opus-4-7":   {"input": 5.00, "cache_read": 0.50, "cache_write": 6.25, "output": 25.00},
    "claude-haiku-4-5":  {"input": 1.00, "cache_read": 0.10, "cache_write": 1.25, "output": 5.00},
}


@dataclass
class LLMResponse:
    analysis: dict
    raw_output: str
    cost: float
    tokens: dict = field(default_factory=dict)
    model: str = ""


def call_claude(
    system_prompt: str,
    user_message: str,
    model: str = "claude-sonnet-4-6",
    max_tokens: int = 3000,
    enable_caching: bool = True,
) -> LLMResponse:
    """
    Claude API 호출 + JSON 출력 파싱 + 비용 계산.

    system_prompt 는 자동으로 cache_control (5분 캐시) 적용.
    """
    client = Anthropic()

    system = (
        [{"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}]
        if enable_caching
        else system_prompt
    )

    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user_message}],
    )

    raw_output = response.content[0].text.strip()

    # ```json ... ``` 형식이면 벗기기
    cleaned = raw_output
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        cleaned = "\n".join(lines[1:-1] if lines[-1].startswith("```") else lines[1:])

    try:
        analysis = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"Claude 응답 JSON 파싱 실패: {e}\n원문 앞 500자:\n{cleaned[:500]}")

    # 토큰/비용
    usage = response.usage
    in_tokens = usage.input_tokens
    out_tokens = usage.output_tokens
    cache_read = getattr(usage, "cache_read_input_tokens", 0) or 0
    cache_create = getattr(usage, "cache_creation_input_tokens", 0) or 0
    uncached_in = max(0, in_tokens - cache_read)

    rates = PRICING.get(model, PRICING["claude-sonnet-4-6"])
    cost = (
        uncached_in * rates["input"] / 1_000_000
        + cache_read * rates["cache_read"] / 1_000_000
        + cache_create * rates["cache_write"] / 1_000_000
        + out_tokens * rates["output"] / 1_000_000
    )

    return LLMResponse(
        analysis=analysis,
        raw_output=raw_output,
        cost=cost,
        tokens={
            "input": uncached_in,
            "cache_read": cache_read,
            "cache_write": cache_create,
            "output": out_tokens,
        },
        model=model,
    )
