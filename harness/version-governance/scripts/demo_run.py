"""Run Phase C demo scenario through public REST endpoints."""

import argparse
import json
import os
import time
from urllib.request import Request, urlopen

import mlflow
import mlflow.genai

PROMPT_NAME = "api-bd-generator"
WORKFLOW_ID = "rd-to-bd-api"
PROJECT_KEY = "demo-api"


def request_json(url: str, method: str = "GET", body: dict | None = None) -> object:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    request = Request(url, data=data, method=method, headers={"Content-Type": "application/json"})
    with urlopen(request) as response:
        return json.load(response)


def set_alias_and_wait(version: int, timeout_seconds: float = 30.0) -> None:
    """Move the production alias and block until the registry actually serves it.

    MLflow does not guarantee that a freshly written alias is visible to the next reader.
    Starting a run before it propagates freezes the OLD prompt version into the manifest —
    the manifest would be correct (it records what resolved at freeze time) but the demo
    scenario would silently prove nothing.
    """
    mlflow.genai.set_prompt_alias(PROMPT_NAME, "production", version=version)
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if int(mlflow.genai.load_prompt(f"prompts:/{PROMPT_NAME}@production").version) == version:
            return
        time.sleep(0.5)
    raise RuntimeError(f"alias production did not propagate to version {version} within {timeout_seconds}s")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", choices=("A", "B", "C"), required=True)
    parser.add_argument("--tracking-uri", default=os.getenv("VGOV_MLFLOW_TRACKING_URI", "http://localhost:8812"))
    parser.add_argument("--api-base", default=os.getenv("VGOV_BASE_URL", "http://localhost:8810/api/vgov"))
    args = parser.parse_args()
    api_base = args.api_base.rstrip("/")
    if not api_base.endswith("/api/vgov"):
        api_base += "/api/vgov"

    mlflow.set_tracking_uri(args.tracking_uri)
    prompt_version = 1 if args.scenario == "A" else 2
    set_alias_and_wait(prompt_version)
    inputs = request_json(f"{api_base}/inputs?project_key={PROJECT_KEY}")
    target_revision = 1 if args.scenario in {"A", "B"} else 2
    input_revision = next(row for row in inputs if row["revision_no"] == target_revision)
    run = request_json(f"{api_base}/runs", "POST", {
        "project_key": PROJECT_KEY, "workflow_id": WORKFLOW_ID,
        "input_revision_id": input_revision["id"], "output_business_key": "BD-DEMO",
        "output_artifact_type": "API_BASIC_DESIGN", "environment": "PROD",
    })
    deadline = time.monotonic() + 90
    while run["status"] in {"CREATED", "MANIFEST_FROZEN", "RUNNING"} and time.monotonic() < deadline:
        time.sleep(1)
        run = request_json(f"{api_base}/runs/{run['id']}")
    if run["status"] != "SUCCEEDED":
        raise RuntimeError(f"run did not succeed: {run}")
    artifacts = request_json(
        f"{api_base}/artifacts?project_key={PROJECT_KEY}&artifact_type=API_BASIC_DESIGN"
    )
    artifact = next(row for row in artifacts if row["business_key"] == "BD-DEMO")
    revisions = request_json(f"{api_base}/artifacts/{artifact['id']}/revisions")
    print(json.dumps({"scenario": args.scenario, "prompt_version": prompt_version, "run": run, "artifact": artifact, "revisions": revisions}, indent=2, default=str))


if __name__ == "__main__":
    main()
