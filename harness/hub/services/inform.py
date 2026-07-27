from __future__ import annotations

import re
import unicodedata
from typing import Any


ZERO_WIDTH_RE = re.compile(r"[\u200B-\u200D\uFEFF\u2060]")
BIDI_CONTROL_RE = re.compile(r"[\u202A-\u202E\u2066-\u2069]")

INJECTION_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("ignore_previous_instructions", re.compile(r"ignore\s+(?:all\s+)?previous\s+instructions", re.IGNORECASE)),
    ("disregard_system_or_above", re.compile(r"disregard\s+(?:the\s+)?(?:system|above)", re.IGNORECASE)),
    ("system_prompt", re.compile(r"system\s+prompt", re.IGNORECASE)),
    ("bcc", re.compile(r"\bBCC\b", re.IGNORECASE)),
    ("exfiltrate", re.compile(r"exfiltrat\w*", re.IGNORECASE)),
    ("reveal_secret", re.compile(r"reveal[\s\S]{0,160}\b(?:key|token|secret)\b", re.IGNORECASE)),
    ("long_base64_blob", re.compile(r"\b[A-Za-z0-9+/_-]{80,}={0,2}\b", re.IGNORECASE)),
]


def _strip_matches(text: str, pattern: re.Pattern[str], label: str) -> tuple[str, list[dict[str, Any]]]:
    findings: list[dict[str, Any]] = []
    pieces: list[str] = []
    last = 0
    for match in pattern.finditer(text):
        findings.append({"type": "strip", "pattern": label, "offset": match.start()})
        pieces.append(text[last : match.start()])
        last = match.end()
    pieces.append(text[last:])
    return "".join(pieces), findings


def sanitize_text(s: Any) -> tuple[str, list[dict[str, Any]]]:
    text = unicodedata.normalize("NFKC", str(s or ""))
    text, zero_width = _strip_matches(text, ZERO_WIDTH_RE, "zero_width")
    text, bidi = _strip_matches(text, BIDI_CONTROL_RE, "bidi_control")

    findings: list[dict[str, Any]] = [*zero_width, *bidi]
    for label, pattern in INJECTION_PATTERNS:
        for match in pattern.finditer(text):
            findings.append(
                {
                    "type": "injection_pattern",
                    "pattern": label,
                    "offset": match.start(),
                }
            )
    findings.sort(key=lambda item: int(item.get("offset") or 0))
    return text, findings


def has_injection_finding(findings: Any) -> bool:
    if not isinstance(findings, list):
        return False
    return any(isinstance(item, dict) and item.get("type") == "injection_pattern" for item in findings)
