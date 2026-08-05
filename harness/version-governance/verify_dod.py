"""Exercise the Version Governance POC Definition of Done against the running compose stack."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
COMPOSE = ROOT / "deploy" / "docker-compose.yml"
API = "http://localhost:8810/api/vgov"
PROMPT = "api-bd-generator"


def request(path: str, method: str = "GET", body: dict | None = None) -> object:
    payload = json.dumps(body).encode() if body is not None else None
    req = Request(f"{API}{path}", data=payload, method=method, headers={"Content-Type": "application/json"})
    with urlopen(req, timeout=30) as response:
        return json.load(response)


def command(args: list[str], *, check: bool = True) -> str:
    result = subprocess.run(args, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if check and result.returncode:
        raise RuntimeError(result.stdout)
    return result.stdout


def in_api(*args: str) -> list[str]:
    """Chạy lệnh bên trong container vgov-api.

    demo_seed/demo_run cần `mlflow` và mạng nội bộ compose; python trên host không có cả hai.
    scripts/ đã được mount vào /app/scripts qua docker-compose.
    """
    return ["docker", "compose", "-f", str(COMPOSE), "exec", "-T", "vgov-api", *args]


def script(name: str, *args: str) -> dict:
    output = command(in_api(
        "python", f"/app/scripts/{name}",
        "--api-base", "http://localhost:8810/api/vgov",
        "--tracking-uri", "http://mlflow:8812",
        *args,
    ))
    # MLflow ghi log tiến trình ra stdout; chỉ lấy phần JSON ở cuối.
    start = output.index("{")
    return json.loads(output[start:])


def demo(scenario: str) -> dict:
    return script("demo_run.py", "--scenario", scenario)


def request_openapi_paths() -> list[str]:
    """Danh sách route thật mà vgov-api đang phục vụ, đọc từ OpenAPI."""
    with urlopen("http://localhost:8810/openapi.json", timeout=30) as response:
        return list(json.load(response).get("paths", {}))


def api_error(path: str, body: dict) -> tuple[int, dict]:
    try:
        request(path, "POST", body)
    except HTTPError as error:
        return error.code, json.load(error)
    raise AssertionError("expected HTTP error")


def pytest_case(filename: str) -> bool:
    output = command(["docker", "compose", "-f", str(COMPOSE), "exec", "-T", "vgov-api", "python", "-m", "pytest", f"tests/{filename}", "-q"], check=False)
    return "passed" in output and "failed" not in output.lower()


def database_scalar(sql: str) -> str:
    return command([
        "docker", "compose", "-f", str(COMPOSE), "exec", "-T", "postgres",
        "psql", "-U", "vgov", "-d", "vgov", "-Atc", sql,
    ]).strip()


def error_cases(input_id: str) -> list[str]:
    """Report resilience checks; always restore prompt alias/runtime for later operators."""
    results: list[str] = []
    mlflow = ["docker", "compose", "-f", str(COMPOSE), "exec", "-T", "vgov-api", "python", "-c"]
    delete = "import mlflow; mlflow.set_tracking_uri('http://mlflow:8812'); mlflow.MlflowClient().delete_prompt_alias('api-bd-generator','production')"
    restore = "import mlflow; mlflow.set_tracking_uri('http://mlflow:8812'); mlflow.genai.set_prompt_alias('api-bd-generator','production',version=1)"
    try:
        command(mlflow + [delete])
        status, payload = api_error("/runs", {"project_key": "demo-api", "workflow_id": "rd-to-bd-api", "input_revision_id": input_id, "output_business_key": "VERIFY-ALIAS", "environment": "PROD"})
        manifests = database_scalar("SELECT count(*) FROM run_manifest m JOIN execution_run r ON r.id=m.run_id WHERE r.output_business_key='VERIFY-ALIAS'")
        results.append(f"alias removed: HTTP {status}, code={payload.get('detail', {}).get('code', 'unknown')}, manifests={manifests}")
    except Exception as error:  # resilience reporting must not hide the DoD result
        results.append(f"alias removed: ERROR {error}")
    finally:
        command(mlflow + [restore], check=False)

    try:
        command(["docker", "compose", "-f", str(COMPOSE), "stop", "vgov-runtime"])
        status, payload = api_error("/runs", {"project_key": "demo-api", "workflow_id": "rd-to-bd-api", "input_revision_id": input_id, "output_business_key": "VERIFY-RUNTIME", "environment": "PROD"})
        row = database_scalar("SELECT status || ':' || coalesce(error_code,'') FROM execution_run WHERE output_business_key='VERIFY-RUNTIME' ORDER BY created_at DESC LIMIT 1")
        manifests = database_scalar("SELECT count(*) FROM run_manifest m JOIN execution_run r ON r.id=m.run_id WHERE r.output_business_key='VERIFY-RUNTIME'")
        results.append(f"runtime stopped: HTTP {status}, code={payload.get('detail', {}).get('code', 'unknown')}, run={row}, manifests={manifests}")
    except Exception as error:
        results.append(f"runtime stopped: ERROR {error}")
    finally:
        command(["docker", "compose", "-f", str(COMPOSE), "start", "vgov-runtime"], check=False)
    results.append("callback lost: covered by tests/test_reconcile.py (runtime terminal without callback closes CALLBACK_LOST)")
    return results


def main() -> int:
    script("demo_seed.py")
    a, b, c = demo("A"), demo("B"), demo("C")
    a_run, b_run, c_run = a["run"], b["run"], c["run"]
    a_revision = a["revisions"][-1]
    b_revision = b["revisions"][-1]
    a_manifest = request(f"/runs/{a_run['id']}/manifest")
    b_manifest = request(f"/runs/{b_run['id']}/manifest")
    # content endpoint streams plain text, so retain byte-for-byte integrity check outside JSON helper.
    with urlopen(f"{API}/revisions/{a_revision['id']}/content", timeout=30) as response:
        content_bytes = response.read()
    lineage = request(f"/revisions/{a_revision['id']}/lineage")
    diff = request("/explain-difference", "POST", {"left": {"revision_id": a_revision["id"]}, "right": {"revision_id": b_revision["id"]}})
    repeat_a = demo("A")
    repeat_manifest = request(f"/runs/{repeat_a['run']['id']}/manifest")
    release = next(row for row in request("/releases?workflow_id=rd-to-bd-api") if row["status"] == "PUBLISHED")
    prompt = next(row for row in a_manifest["components"] if row["kind"] == "PROMPT")
    changed_categories = {row["category"] for row in diff["changed"]}
    unchanged_categories = {row["category"] for row in diff["unchanged"]}
    placeholder_output = content_bytes.startswith(b"Review and return final basic design:")
    prompt_publish_routes = [
        route for route in request_openapi_paths()
        if "prompt" in route.lower() or route.rstrip("/").endswith("/aliases")
    ]
    checks = [
        ("Release exact 40-hex + immutable", bool(re.fullmatch(r"[0-9a-f]{40}", release.get("git_commit") or "")) and pytest_case("test_immutability.py")),
        ("Run persisted before runtime start", pytest_case("test_freeze_order.py")),
        ("PROMPT component pins numeric exact version", bool(re.fullmatch(r"[0-9]+", prompt["exact_version"]))),
        ("Manifest frozen before start + immutable", pytest_case("test_freeze_order.py") and pytest_case("test_immutability.py")),
        # "Không rỗng" là tiêu chí quá lỏng: khi NVIDIA_API_KEY rỗng, runtime/graph.py trả
        # placeholder `f"{prompt}\n\n{rd_text}"` — vẫn non-empty, nên DoD #5 sẽ PASS mà LLM chưa
        # từng được gọi. Placeholder luôn bắt đầu bằng prompt của node review_bd, dùng nó làm sentinel.
        ("Output BD Markdown non-empty and produced by a real LLM call", bool(content_bytes.strip()) and not placeholder_output),
        ("Revision hash matches content + source run", a_revision["content_hash"] == "sha256:" + hashlib.sha256(content_bytes).hexdigest() and a_revision["source_run_id"] == a_run["id"]),
        ("Lineage reaches input hash", lineage.get("manifest", {}).get("input_hash") == lineage.get("input_revision", {}).get("content_hash")),
        ("Same input runs prompt v1 and v2", prompt["exact_version"] == "1" and next(row for row in b_manifest["components"] if row["kind"] == "PROMPT")["exact_version"] == "2"),
        # TOOL vắng mặt là hợp lệ: release demo không khai báo tool nào nên category đó không có
        # facet để so. Điều kiện thật là PROMPT là thứ DUY NHẤT đổi, và mọi category có dữ liệu
        # đều nằm bên unchanged.
        ("A vs B only changes PROMPT", changed_categories == {"PROMPT"} and unchanged_categories >= {"INPUT", "WORKFLOW_RELEASE", "MODEL", "RUNTIME", "HUMAN_EDIT"}),
        # DoD #10: user không phải publish prompt ở cả hai nơi -> vgov KHÔNG được hở endpoint nào
        # tạo/sửa prompt hay alias. Import adapter là wiring, không tính.
        ("No prompt-publishing endpoint in vgov", not prompt_publish_routes),
        ("No standalone governance frontend", (ROOT.parent / "hub" / "web-v3").is_dir() and not (ROOT / "web").exists() and not (ROOT / "frontend").exists()),
        ("Repeated Run A has identical manifest hash", a_manifest["manifest_hash"] == repeat_manifest["manifest_hash"]),
    ]
    print("Definition of Done")
    for index, (label, passed) in enumerate(checks, 1):
        print(f"{index:>2}. {'PASS' if passed else 'FAIL'}  {label}")
    print(f"\n{sum(passed for _, passed in checks)}/{len(checks)} PASS")
    print("\nError cases (informational)")
    input_id = request("/inputs?project_key=demo-api")[0]["id"]
    for result in error_cases(input_id):
        print(f"- {result}")
    return 0 if all(passed for _, passed in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
