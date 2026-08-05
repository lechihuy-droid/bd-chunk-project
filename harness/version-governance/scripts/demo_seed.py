"""Seed reproducible Phase B demo data through MLflow and vgov-api."""

import argparse
import hashlib
import json
import os
from urllib.request import Request, urlopen

import mlflow
import mlflow.genai
from mlflow.exceptions import MlflowException

PROMPT_NAME = "api-bd-generator"
WORKFLOW_ID = "rd-to-bd-api"
RELEASE_VERSION = "1.0.0"


def request_json(url: str, method: str = "GET", body: dict | None = None) -> object:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    request = Request(url, data=data, method=method, headers={"Content-Type": "application/json"})
    with urlopen(request) as response:
        return json.load(response)


def prompt_versions() -> list[int]:
    versions: list[int] = []
    for version in range(1, 100):
        try:
            prompt = mlflow.genai.load_prompt(f"prompts:/{PROMPT_NAME}/{version}")
        except MlflowException:
            break
        versions.append(int(prompt.version))
    return versions


def ensure_prompts() -> None:
    versions = prompt_versions()
    if 1 not in versions:
        mlflow.genai.register_prompt(
            name=PROMPT_NAME,
            template="Generate an API basic design from this RD: {{rd}}",
            commit_message="demo seed version 1",
        )
    if 2 not in prompt_versions():
        mlflow.genai.register_prompt(
            name=PROMPT_NAME,
            template=(
                "Generate an API basic design from this RD: {{rd}}. "
                "Apply API naming rule: resource names use kebab-case. "
                "Add traceability from every endpoint back to an RD requirement."
            ),
            commit_message="demo seed version 2: naming and traceability",
        )
    mlflow.genai.set_prompt_alias(PROMPT_NAME, "production", version=1)


def multipart_input(api_base: str, project_key: str, business_key: str, content: bytes) -> dict:
    boundary = "vgov-demo-boundary"
    payload = b"".join(
        [
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"project_key\"\r\n\r\n{project_key}\r\n".encode(),
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"business_key\"\r\n\r\n{business_key}\r\n".encode(),
            b"--" + boundary.encode() + b"\r\nContent-Disposition: form-data; name=\"file\"; filename=\"rd.md\"\r\nContent-Type: text/markdown\r\n\r\n",
            content,
            b"\r\n--" + boundary.encode() + b"--\r\n",
        ]
    )
    request = Request(
        f"{api_base}/inputs",
        data=payload,
        method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urlopen(request) as response:
        return json.load(response)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tracking-uri", default=os.getenv("VGOV_MLFLOW_TRACKING_URI", "http://localhost:8812"))
    parser.add_argument("--api-base", default=os.getenv("VGOV_BASE_URL", "http://localhost:8810/api/vgov"))
    args = parser.parse_args()
    api_base = args.api_base.rstrip("/")
    if not api_base.endswith("/api/vgov"):
        api_base += "/api/vgov"

    mlflow.set_tracking_uri(args.tracking_uri)
    ensure_prompts()
    releases = request_json(f"{api_base}/releases?workflow_id={WORKFLOW_ID}")
    release = next((row for row in releases if row["release_version"] == RELEASE_VERSION), None)
    if release is None:
        release = request_json(
            f"{api_base}/releases",
            "POST",
            {
                "workflow_id": WORKFLOW_ID,
                "release_version": RELEASE_VERSION,
                "git_repo": "ai-project-opus",
                "git_ref": "HEAD",
                "entrypoint": "graph:build_graph",
                "state_schema_version": "v1",
                "bindings": {
                    "generate_bd": {
                        "prompt_ref": f"mlflow://{PROMPT_NAME}",
                        "prompt_alias": "production",
                    }
                },
                "runtime_adapter_id": "langgraph",
                "model_profile": "design-accurate@v1",
                "model_name": "meta/llama-3.1-8b-instruct",
            },
        )
    if release["status"] != "PUBLISHED":
        release = request_json(f"{api_base}/releases/{release['id']}/publish", "POST", {})
    request_json(
        f"{api_base}/environments/PROD",
        "PUT",
        {"workflow_id": WORKFLOW_ID, "release_id": release["id"], "reason": "demo seed"},
    )

    project_key = "demo-api"
    inputs = request_json(f"{api_base}/inputs?project_key={project_key}")
    seeded_inputs = []
    for business_key, content in [
        ("RD-DEMO", b"# RD revision 1\nCreate customer lookup API.\n"),
        ("RD-DEMO", b"# RD revision 2\nCreate customer lookup API with pagination and audit fields.\n"),
    ]:
        content_hash = "sha256:" + hashlib.sha256(content).hexdigest()
        existing = next((row for row in inputs if row["content_hash"] == content_hash), None)
        seeded_inputs.append(existing or multipart_input(api_base, project_key, business_key, content))

    print(
        json.dumps(
            {
                "prompt": PROMPT_NAME,
                "prompt_versions": prompt_versions(),
                "production_version": 1,
                "release_id": release["id"],
                "prod_release_id": release["id"],
                "input_revisions": seeded_inputs,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
