from __future__ import annotations

import json
from typing import Any


def run_checks(text: str, checks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Run deterministic validation checks and return small, stable violations."""
    violations: list[dict[str, Any]] = []
    for check in checks:
        kind = check.get("kind") if isinstance(check, dict) else None
        if kind == "min_length":
            value = check.get("value")
            if not isinstance(value, int) or isinstance(value, bool):
                violations.append({"kind": kind, "message": "min_length value must be an integer", "expected": value})
            elif len(text) < value:
                violations.append({"kind": kind, "message": f"text is shorter than {value} characters", "expected": value, "found": len(text)})
        elif kind in {"must_include", "must_not_include"}:
            values = check.get("values")
            if not isinstance(values, list):
                violations.append({"kind": kind, "message": "values must be a list", "expected": "non-empty list of strings"})
                continue
            for value in values:
                if not isinstance(value, str):
                    violations.append({"kind": kind, "message": "values must contain only strings", "expected": "string", "found": value})
                elif kind == "must_include" and value not in text:
                    violations.append({"kind": kind, "message": f"missing required string: {value}", "missing": value})
                elif kind == "must_not_include" and value in text:
                    violations.append({"kind": kind, "message": f"forbidden string found: {value}", "found": value})
        elif kind == "json_parseable":
            try:
                json.loads(text)
            except (TypeError, json.JSONDecodeError):
                violations.append({"kind": kind, "message": "text is not valid JSON"})
        else:
            violations.append({"kind": kind, "message": f"unknown validation check kind: {kind}", "found": kind})
    return violations
