from __future__ import annotations

from datetime import UTC, datetime

import config
from services import pricing, usage


def test_estimate_cost_prices_token_types_separately(monkeypatch) -> None:
    monkeypatch.setattr(
        config,
        "PRICING_USD_PER_MTOK",
        {"test-model": {"input": 1.0, "output": 2.0, "cache_read": 0.1, "cache_write": 10.0}},
    )
    result = pricing.estimate_cost(
        {"model": "test-model", "input": 1_000_000, "output": 1_000_000, "cache_read": 1_000_000, "cache_creation": 1_000_000}
    )
    assert result == {"estimated_cost_usd": 13.1, "unpriced_tokens": 0, "priced": True}


def test_unpriced_model_is_explicit_and_safe() -> None:
    result = pricing.estimate_cost(
        {"model": "unknown-model", "input": 2, "output": 3, "cache_read": 5, "cache_creation": 7}
    )
    assert result == {"estimated_cost_usd": 0.0, "unpriced_tokens": 17, "priced": False}


def test_resolve_price_exact_then_longest_prefix(monkeypatch) -> None:
    monkeypatch.setattr(
        config,
        "PRICING_USD_PER_MTOK",
        {
            "model": {"input": 1.0},
            "model-special": {"input": 2.0},
        },
    )
    assert pricing.resolve_price("model") == {"input": 1.0}
    assert pricing.resolve_price("model-special-v2") == {"input": 2.0}
    assert pricing.resolve_price("missing") is None


def test_rollup_cost_totals_equal_model_costs() -> None:
    events = [
        {"model": "claude-opus-4-8", "source": "codex", "ts": "2026-07-22T00:00:00Z", "input_tokens": 2, "output_tokens": 3, "cache_read_tokens": 5, "cache_creation_tokens": 7, "total_tokens": 17, "calls": 1},
        {"model": "unknown-model", "source": "chat", "ts": "2026-07-22T01:00:00Z", "input_tokens": 11, "output_tokens": 13, "cache_read_tokens": 17, "cache_creation_tokens": 19, "total_tokens": 60, "calls": 1},
    ]
    rolled = usage.rollup(events)
    assert rolled["totals"]["estimated_cost_usd"] == sum(row["estimated_cost_usd"] for row in rolled["by_model"])
    assert rolled["totals"]["unpriced_tokens"] == 60
    assert rolled["totals"]["cache_tokens"] == 48
    assert rolled["totals"]["cache_read_tokens"] == 22
    assert rolled["totals"]["cache_creation_tokens"] == 26


def test_rollup_preserves_legacy_fields() -> None:
    rolled = usage.rollup([])
    assert set(("calls", "input_tokens", "output_tokens", "total_tokens", "cache_tokens", "non_cache_tokens")) <= rolled["totals"].keys()
    assert rolled["totals"]["estimated_cost_usd"] == 0.0
    assert rolled["totals"]["unpriced_tokens"] == 0
    assert set(("by_model", "by_day", "by_source", "totals")) <= rolled.keys()


def test_cockpit_quota_pct_and_zero_quota(monkeypatch) -> None:
    today = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    events = [{"model": "cli:codex", "ts": today, "calls": 2, "total_tokens": 0}]
    monkeypatch.setattr(usage, "_collect_all", lambda: (events, []))
    monkeypatch.setattr(config, "QUOTA_WARN_PER_DAY", 4)
    stats = usage.cockpit_stats()
    assert stats["today"]["by_provider"][0]["quota_pct"] == 50.0
    monkeypatch.setattr(config, "QUOTA_WARN_PER_DAY", 0)
    assert usage.cockpit_stats()["today"]["by_provider"][0]["quota_pct"] is None
