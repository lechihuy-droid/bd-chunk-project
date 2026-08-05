import hashlib
import json
from typing import Any


def manifest_hash(
    *,
    release_id: Any,
    git_commit: str,
    model_profile: str,
    runtime_adapter_id: str,
    input_hash: str,
    components: list[dict[str, Any]],
) -> str:
    payload = {
        "release_id": str(release_id),
        "git_commit": git_commit,
        "model_profile": model_profile,
        "runtime_adapter_id": runtime_adapter_id,
        "input_hash": input_hash,
        "components": sorted(components, key=lambda component: (component["kind"], component["ref"])),
    }
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()
