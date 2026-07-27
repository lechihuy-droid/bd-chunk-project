from __future__ import annotations

from typing import Any

import config


def resolve_price(model: str) -> dict[str, float] | None:
    prices = config.PRICING_USD_PER_MTOK
    exact = prices.get(model)
    if exact is not None:
        return exact
    matches = [key for key in prices if model.startswith(key)]
    if not matches:
        return None
    return prices[max(matches, key=len)]


def estimate_cost(tokens: dict[str, Any]) -> dict[str, Any]:
    model = str(tokens.get("model") or "")
    counts = {
        "input": int(tokens.get("input") or tokens.get("input_tokens") or 0),
        "output": int(tokens.get("output") or tokens.get("output_tokens") or 0),
        "cache_read": int(tokens.get("cache_read") or tokens.get("cache_read_tokens") or 0),
        "cache_creation": int(
            tokens.get("cache_creation") or tokens.get("cache_creation_tokens") or 0
        ),
    }
    price = resolve_price(model)
    if price is None:
        return {
            "estimated_cost_usd": 0.0,
            "unpriced_tokens": sum(counts.values()),
            "priced": False,
        }

    amount = (
        counts["input"] * price.get("input", 0.0)
        + counts["output"] * price.get("output", 0.0)
        + counts["cache_read"] * price.get("cache_read", 0.0)
        + counts["cache_creation"] * price.get("cache_write", 0.0)
    )
    return {"estimated_cost_usd": amount / 1_000_000, "unpriced_tokens": 0, "priced": True}
