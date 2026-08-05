"""Step A0 spike — verify MLflow Prompt Registry API surface against the REAL stack.

Chạy trong container mlflow (cùng image, cùng version với production của POC):

    docker compose -f deploy/docker-compose.yml exec -T mlflow \
        python /scripts/spike_a0.py

Không phải production code. Mục tiêu duy nhất: chốt shape của object mà
`mlflow.genai.load_prompt` trả về, trước khi viết MLflowPromptAdapter ở Step B2.
Xác nhận đồng thời hai tính chất nền của Version Governance:

- alias là mutable pointer (di chuyển được),
- exact version là immutable target (không đổi khi alias di chuyển).
"""

from __future__ import annotations

import os
import sys

import mlflow
import mlflow.genai

TRACKING_URI = os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:8812")
NAME = "spike-a0-probe"

print(f"mlflow           = {mlflow.__version__}")
mlflow.set_tracking_uri(TRACKING_URI)
print(f"tracking uri     = {mlflow.get_tracking_uri()}")

v1 = mlflow.genai.register_prompt(
    name=NAME,
    template="v1 template with {{rd}}",
    commit_message="spike v1",
)
v2 = mlflow.genai.register_prompt(
    name=NAME,
    template="v2 template with {{rd}} plus naming rule",
    commit_message="spike v2",
)
print(f"register v1      -> version={v1.version!r} ({type(v1.version).__name__})")
print(f"register v2      -> version={v2.version!r}")

mlflow.genai.set_prompt_alias(NAME, "production", version=1)
by_alias = mlflow.genai.load_prompt(f"prompts:/{NAME}@production")

print("--- load by alias ---")
print(f"  type           = {type(by_alias).__module__}.{type(by_alias).__name__}")
print(f"  name           = {by_alias.name!r}")
print(f"  version        = {by_alias.version!r} ({type(by_alias.version).__name__})")
print(f"  template[:40]  = {by_alias.template[:40]!r}")
print(f"  public attrs   = {[a for a in dir(by_alias) if not a.startswith('_')]}")

assert by_alias.name == NAME
assert int(by_alias.version) == 1, f"alias production phải là version 1, nhận {by_alias.version}"

# Mutable pointer: alias di chuyển được.
mlflow.genai.set_prompt_alias(NAME, "production", version=2)
moved = mlflow.genai.load_prompt(f"prompts:/{NAME}@production")
assert int(moved.version) == 2, "alias phải di chuyển được"
print(f"alias moved      -> version={moved.version!r}   (mutable pointer OK)")

# Immutable target: exact version không đổi khi alias đã di chuyển.
pinned = mlflow.genai.load_prompt(f"prompts:/{NAME}/1")
assert int(pinned.version) == 1, "exact version phải bất biến sau khi alias đổi"
assert pinned.template == v1.template, "nội dung của version 1 phải giữ nguyên"
print(f"pinned /1        -> version={pinned.version!r}   (immutable target OK)")

# Fail closed: alias không tồn tại phải ném exception, không trả None.
try:
    mlflow.genai.load_prompt(f"prompts:/{NAME}@khong-ton-tai")
except Exception as exc:  # noqa: BLE001 - spike cần biết chính xác exception type
    print(f"unresolved alias -> raises {type(exc).__module__}.{type(exc).__name__}")
else:
    print("FAIL: alias không tồn tại KHÔNG raise — adapter phải tự kiểm tra để fail closed")
    sys.exit(1)

print("\nA0 spike: PASS")
