from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


HUB_DIR = Path(__file__).resolve().parent
HARNESS_DIR = HUB_DIR.parent
ROOT = HARNESS_DIR.parent

# Loads NVIDIA_API_KEY and friends from the repo-root .env. Does not override
# a value already set in the environment (e.g. by the shell or a supervisor).
load_dotenv(ROOT / ".env")
RUNS_DIR = HARNESS_DIR / "runs"
SUITES_DIR = HARNESS_DIR / "suites"
JOBS_DIR = HUB_DIR / "jobs"
RUNTIME_DIR = HUB_DIR / "runtime"
RUNTIME_THREADS_DIR = RUNTIME_DIR / "threads"
RUNTIME_RUNS_DIR = RUNTIME_DIR / "runs"
RUNTIME_STORE_DIR = RUNTIME_DIR / "store"
PORT = 8799
STEP_CAP = 50
JOB_AGENT_CMD = "codex"
JOB_TIME_CAP_SECONDS = 1800
JOB_MAX_RUNS = 3
RUNTIME_MAX_CHILD_RUNS = 3
RUNTIME_CHILD_TIMEOUT_SECONDS = 900
JOB_BLOCKED_TIERS = ["destructive"]
JOB_TTL_SECONDS = 3600
JOB_ALLOW_AGENTS = {"codex"}
GOV_RECOVERY_STEPS = 5
LOOP_CONSECUTIVE_THRESHOLD = 12
ENTROPY_WINDOW = 20
ENTROPY_THRESHOLD = 0.3
OPUS_AI_DIR = ROOT / "opus-animus" / "ai"
INSPECT_MEP_DIR = HARNESS_DIR / "inspect" / "mep"
INSPECT_EXPORT_MEP = HARNESS_DIR / "inspect" / "export_mep.py"
RISK_TIERS_PATH = HUB_DIR / "risk_tiers.json"
HMAC_KEY_FILE = HUB_DIR / ".hmac_key"
INTEGRITY_SIGS_FILE = HUB_DIR / ".cache" / "suite_sigs.json"
GOVERNANCE_STATE_FILE = HUB_DIR / ".cache" / "governance.json"

DEFAULT_RISK_TIERS: dict[str, Any] = {
    "tool_tiers": {},
    "command_tiers": {},
    "network_tokens": [],
    "destructive_tokens": [],
}

USAGE_SOURCES = {
    "claude": Path.home() / ".claude" / "projects",
    "codex": [
        Path.home() / ".codex" / "sessions",
        Path.home() / ".codex" / "archived_sessions",
    ],
    "inspect": HARNESS_DIR / "inspect" / "logs",
}
# Curated general-purpose chat + reasoning models from the NVIDIA catalog
# (integrate.api.nvidia.com). Embedding / safety-guard / retriever / reward /
# OCR / translate / code-only models are intentionally excluded.
CHAT_MODEL_CATALOG: list[dict[str, Any]] = [
    {
        "rank": 1,
        "id": "nvidia/nemotron-3-super-120b-a12b",
        "shortName": "Nemotron 3 Super 120B",
        "label": "#01 Nemotron 3 Super 120B - Primary balanced",
        "category": "Primary",
        "bestFor": "Primary bulk coding/reasoning",
        "strengths": ["Balanced coding", "Reasoning", "Planning", "Tool calling", "1M context"],
        "weaknesses": ["Heavier than flash/nano models"],
        "recommendedUse": "Generate coding tests, reference solutions, rubrics, and reasoning-heavy outputs.",
        "avoidWhen": "Simple formatting, classification, dedupe, or very cheap batch jobs.",
    },
    {
        "rank": 2,
        "id": "deepseek-ai/deepseek-v4-flash",
        "shortName": "DeepSeek V4 Flash",
        "label": "#02 DeepSeek V4 Flash - Fast coding batch",
        "category": "Fast",
        "bestFor": "Fast coding / agent batch",
        "strengths": ["Fast coding", "Agent batch", "1M context"],
        "weaknesses": ["Needs external verification for hard cases"],
        "recommendedUse": "Mass generation of coding tasks, solutions, and first-pass outputs.",
        "avoidWhen": "Final judging without a second verifier model.",
    },
    {
        "rank": 3,
        "id": "mistralai/mistral-small-4-119b-2603",
        "shortName": "Mistral Small 4 119B",
        "label": "#03 Mistral Small 4 119B - Stable coding",
        "category": "Primary",
        "bestFor": "Coding + reasoning on dinh",
        "strengths": ["Stable coding", "Rubric generation", "Unit test generation", "256K context"],
        "weaknesses": ["Shorter context than 1M models"],
        "recommendedUse": "Create test cases, rubrics, reference solutions, and review tasks.",
        "avoidWhen": "Extremely long-context tasks above 256K.",
    },
    {
        "rank": 4,
        "id": "minimaxai/minimax-m2.7",
        "shortName": "MiniMax M2.7",
        "label": "#04 MiniMax M2.7 - Code + reasoning",
        "category": "Primary",
        "bestFor": "Coding/reasoning/office task",
        "strengths": ["Coding", "Reasoning", "Explanation", "Office-style tasks"],
        "weaknesses": ["Less proven than top primary pool"],
        "recommendedUse": "Generate and explain coding tasks, especially when explanation quality matters.",
        "avoidWhen": "You need the safest primary model without benchmark testing.",
    },
    {
        "rank": 5,
        "id": "qwen/qwen3.5-122b-a10b",
        "shortName": "Qwen 3.5 122B A10B",
        "label": "#05 Qwen 3.5 122B A10B - Agent/tool coding",
        "category": "Primary",
        "bestFor": "Agent-ready coding + tool calling",
        "strengths": ["Agent-ready", "Tool calling", "Coding", "Reasoning"],
        "weaknesses": ["Needs benchmark in your own harness"],
        "recommendedUse": "Tool-based coding agent workflows.",
        "avoidWhen": "You need a model already validated by your production benchmark.",
    },
    {
        "rank": 6,
        "id": "openai/gpt-oss-120b",
        "shortName": "GPT-OSS 120B",
        "label": "#06 GPT-OSS 120B - Judge/reasoning",
        "category": "Judge",
        "bestFor": "Reasoning + function calling",
        "strengths": ["Reasoning", "Function calling", "Verifier role"],
        "weaknesses": ["Not ideal as fastest bulk generator"],
        "recommendedUse": "Judge, verifier, scoring, and second-pass review.",
        "avoidWhen": "Low-cost mass generation is the priority.",
    },
    {
        "rank": 7,
        "id": "meta/llama-3.3-70b-instruct",
        "shortName": "Llama 3.3 70B",
        "label": "#07 Llama 3.3 70B - Stable fallback",
        "category": "Fallback",
        "bestFor": "Stable fallback",
        "strengths": ["Stable", "General reasoning", "Fallback-safe"],
        "weaknesses": ["Not specialized for hard coding"],
        "recommendedUse": "Fallback for general reasoning and non-critical coding tasks.",
        "avoidWhen": "Hard algorithmic coding tasks need deep code specialization.",
    },
    {
        "rank": 8,
        "id": "nvidia/nemotron-3-nano-30b-a3b",
        "shortName": "Nemotron 3 Nano 30B",
        "label": "#08 Nemotron 3 Nano 30B - Cheap bulk worker",
        "category": "Cheap",
        "bestFor": "Cheap/fast bulk worker",
        "strengths": ["Cheap", "Fast", "1M context", "Bulk-friendly"],
        "weaknesses": ["Weaker on complex algorithmic tasks"],
        "recommendedUse": "Pass-1 worker, classification, formatting, and simple generation.",
        "avoidWhen": "Hard coding or final correctness judgment.",
    },
    {
        "rank": 9,
        "id": "mistralai/mistral-medium-3.5-128b",
        "shortName": "Mistral Medium 3.5 128B",
        "label": "#09 Mistral Medium 3.5 128B - Agentic coding",
        "category": "Primary",
        "bestFor": "Agentic coding",
        "strengths": ["Agentic coding", "General high performance"],
        "weaknesses": ["Needs practical latency test"],
        "recommendedUse": "Agentic coding backup and generation tasks.",
        "avoidWhen": "Latency is unknown and must be guaranteed.",
    },
    {
        "rank": 10,
        "id": "stepfun-ai/step-3.7-flash",
        "shortName": "Step 3.7 Flash",
        "label": "#10 Step 3.7 Flash - Fast backup",
        "category": "Fast",
        "bestFor": "Fast coding/agent backup",
        "strengths": ["Fast", "Agentic", "Coding capable", "Vision capable"],
        "weaknesses": ["Backup, not primary until tested"],
        "recommendedUse": "Speed fallback and agentic backup.",
        "avoidWhen": "Primary production generation before benchmark validation.",
    },
    {
        "rank": 11,
        "id": "minimaxai/minimax-m3",
        "shortName": "MiniMax M3",
        "label": "#11 MiniMax M3 - New coding candidate",
        "category": "Primary",
        "bestFor": "Recent coding/tool-calling candidate",
        "strengths": ["Newer coding candidate", "Tool calling", "Reasoning"],
        "weaknesses": ["Newer model, less proven"],
        "recommendedUse": "Experimental pool for coding and tool-calling tasks.",
        "avoidWhen": "Stable production model is required.",
    },
    {
        "rank": 12,
        "id": "nvidia/llama-3.3-nemotron-super-49b-v1.5",
        "shortName": "Nemotron Super 49B v1.5",
        "label": "#12 Nemotron Super 49B v1.5 - Efficient reasoning",
        "category": "Fallback",
        "bestFor": "Efficient reasoning + tool calling",
        "strengths": ["Efficient reasoning", "Tool calling", "Instruction following"],
        "weaknesses": ["Smaller than Nemotron 3 Super 120B"],
        "recommendedUse": "Efficient review and fallback reasoning.",
        "avoidWhen": "You need the strongest final reviewer.",
    },
    {
        "rank": 13,
        "id": "deepseek-ai/deepseek-v4-pro",
        "shortName": "DeepSeek V4 Pro",
        "label": "#13 DeepSeek V4 Pro - Hard-case judge",
        "category": "Judge",
        "bestFor": "Hard coding cases / judge",
        "strengths": ["Hard coding", "Reasoning", "1M context"],
        "weaknesses": ["Better saved for difficult cases"],
        "recommendedUse": "Hard-case verification and complex coding review.",
        "avoidWhen": "Every request is simple and cost/throughput matters more.",
    },
    {
        "rank": 14,
        "id": "nvidia/nemotron-3-ultra-550b-a55b",
        "shortName": "Nemotron 3 Ultra 550B",
        "label": "#14 Nemotron 3 Ultra 550B - Final reviewer",
        "category": "Judge",
        "bestFor": "Final reviewer / planning",
        "strengths": ["Strong final reasoning", "Planning", "Coding", "1M context"],
        "weaknesses": ["Too heavy for full mass usage"],
        "recommendedUse": "Final review, planning, and high-stakes verification.",
        "avoidWhen": "Bulk generation or cheap preprocessing.",
    },
    {
        "rank": 15,
        "id": "qwen/qwen3-next-80b-a3b-instruct",
        "shortName": "Qwen3 Next 80B A3B",
        "label": "#15 Qwen3 Next 80B A3B - Long-context worker",
        "category": "Fallback",
        "bestFor": "Efficient long-context worker",
        "strengths": ["Efficient MoE", "Long-context", "Function calling"],
        "weaknesses": ["Not best for deep reasoning mode"],
        "recommendedUse": "Long-context worker and structured processing.",
        "avoidWhen": "Deep reasoning is the main requirement.",
    },
    {
        "rank": 16,
        "id": "openai/gpt-oss-20b",
        "shortName": "GPT-OSS 20B",
        "label": "#16 GPT-OSS 20B - Cheap simple worker",
        "category": "Cheap",
        "bestFor": "Low-cost simple worker",
        "strengths": ["Cheap", "Simple reasoning", "Normalization"],
        "weaknesses": ["Weak for hard coding"],
        "recommendedUse": "Classification, formatting, skeleton generation, and normalization.",
        "avoidWhen": "Complex algorithmic coding or final judge.",
    },
    {
        "rank": 17,
        "id": "stepfun-ai/step-3.5-flash",
        "shortName": "Step 3.5 Flash",
        "label": "#17 Step 3.5 Flash - Agentic backup",
        "category": "Fast",
        "bestFor": "Agentic coding backup",
        "strengths": ["Agentic", "Coding", "Reasoning backup"],
        "weaknesses": ["Older than Step 3.7 Flash"],
        "recommendedUse": "Backup worker for agentic coding.",
        "avoidWhen": "Step 3.7 Flash is available and benchmarked better.",
    },
    {
        "rank": 18,
        "id": "meta/llama-4-maverick-17b-128e-instruct",
        "shortName": "Llama 4 Maverick",
        "label": "#18 Llama 4 Maverick - Multimodal fallback",
        "category": "Multimodal",
        "bestFor": "General multimodal fallback",
        "strengths": ["Multimodal", "General fallback"],
        "weaknesses": ["Not top pure coding model"],
        "recommendedUse": "Coding tasks with screenshot/image-related input.",
        "avoidWhen": "Pure text-based hard coding where code-specialized models are better.",
    },
    {
        "rank": 19,
        "id": "meta/llama-3.1-8b-instruct",
        "shortName": "Llama 3.1 8B",
        "label": "#19 Llama 3.1 8B - Filter/format/dedupe",
        "category": "Cheap",
        "bestFor": "Fast cheap filter",
        "strengths": ["Very cheap", "Filter", "Format", "Dedupe"],
        "weaknesses": ["No function calling", "Weak hard coding"],
        "recommendedUse": "Preprocessing, dedupe, formatting, and simple JSON normalization.",
        "avoidWhen": "Solving or judging difficult coding tasks.",
    },
    {
        "rank": 20,
        "id": "nvidia/llama-3.3-nemotron-super-49b-v1",
        "shortName": "Nemotron Super 49B v1",
        "label": "#20 Nemotron Super 49B v1 - Backup for v1.5",
        "category": "Fallback",
        "bestFor": "Fallback for v1.5",
        "strengths": ["Backup", "Reasoning", "Instruction following"],
        "weaknesses": ["Lower priority than v1.5"],
        "recommendedUse": "Reserve fallback when v1.5 is unavailable.",
        "avoidWhen": "v1.5 or stronger Nemotron models are available.",
    },
    {
        "rank": 21,
        "id": "z-ai/glm-5.2",
        "shortName": "GLM 5.2",
        "label": "#21 GLM 5.2 - Agentic reasoning candidate",
        "category": "Primary",
        "bestFor": "Agentic reasoning / coding candidate",
        "strengths": ["Reasoning", "Coding candidate", "Agentic workflows"],
        "weaknesses": ["Newly added; needs harness benchmark"],
        "recommendedUse": "Trial model for coding, planning, and agentic reasoning tasks.",
        "avoidWhen": "You need a model already validated by local benchmark results.",
    },
]
CHAT_MODELS = [row["id"] for row in CHAT_MODEL_CATALOG]
CHAT_DEFAULT_MODEL = "nvidia/nemotron-3-super-120b-a12b"
CHAT_MAX_TOKENS = 16384
CHAT_REASONING: list[dict[str, Any]] = [
    {
        "prefix": "deepseek",
        "extra_body": {"chat_template_kwargs": {"thinking": True, "reasoning_effort": "high"}},
    },
    {
        "prefix": "qwen",
        "extra_body": {"chat_template_kwargs": {"thinking": True}},
    },
    {
        "prefix": "openai/gpt-oss",
        "params": {"reasoning_effort": "high"},
    },
    {
        "prefix": "nvidia/",
        "system": "detailed thinking on",
    },
]


# --- Hub v2: Command Center (Phase A) ---
CHAT_USAGE_FILE = HUB_DIR / ".cache" / "chat_usage.jsonl"
SKILL_DEPLOY_LOG = HUB_DIR / ".cache" / "skill_deploy_log.jsonl"

# CLI provider layer
MAX_CONCURRENT_CLI = 3
CHAT_CLI_TIMEOUT = 300
QUOTA_WARN_PER_DAY = 200

# User-editable shadow estimates, not official billing rates or invoices.
# Exact model ids are preferred; services.pricing.py also supports prefixes.
PRICING_USD_PER_MTOK: dict[str, dict[str, float]] = {
    # Anthropic public API pricing (standard global, 5-minute cache writes).
    "claude-opus-4-8": {
        "input": 5.0,
        "output": 25.0,
        "cache_read": 0.5,
        "cache_write": 6.25,
    },
    # Introductory public API pricing through 2026-08-31.
    "claude-sonnet-5": {
        "input": 2.0,
        "output": 10.0,
        "cache_read": 0.2,
        "cache_write": 2.5,
    },
}
PROVIDERS: dict[str, Any] = {
    "claude": {"cmd": ["claude"]},
    "codex": {"cmd": [str(Path.home() / "AppData" / "Local" / "pnpm" / "codex")]},
    "nvidia": {},
    "gemini": {"cmd": ["gemini"]},
}

MODEL_CLASS_ROUTING: dict[str, dict[str, Any]] = {
    "cheap": {"provider": "nvidia", "model": None},
    "code": {"provider": "codex", "model": None},
    "smart": {"provider": "claude", "model": None},
}

# Skill library sources (read + deploy targets)
SKILL_SOURCES: dict[str, Path] = {
    "claude_user": Path.home() / ".claude" / "skills",
    "claude_project": ROOT / ".claude" / "skills",
    "codex_user": Path.home() / ".codex" / "skills",
}

# CSRF guard (local-only origins)
ALLOWED_ORIGINS = (
    "http://127.0.0.1:8799",
    "http://localhost:8799",
)
HUB_CLIENT_HEADER = "x-hub-client"
HUB_CLIENT_VALUE = "harness-hub"


if __name__ == "__main__":
    print(ROOT)


def load_risk_tiers() -> dict[str, Any]:
    try:
        data = json.loads(RISK_TIERS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return dict(DEFAULT_RISK_TIERS)
    if not isinstance(data, dict):
        return dict(DEFAULT_RISK_TIERS)
    merged = dict(DEFAULT_RISK_TIERS)
    merged.update(data)
    return merged
