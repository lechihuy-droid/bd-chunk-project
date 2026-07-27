from __future__ import annotations

from copy import deepcopy

import pytest
import yaml
from fastapi.testclient import TestClient

import server
from services import boundary, workflow


@pytest.fixture(autouse=True)
def fake_agents(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        workflow.runtime_agents,
        "list_agents",
        lambda: [{"id": "reviewer", "name": "Review Worker"}],
    )


def _use_workflows_dir(monkeypatch: pytest.MonkeyPatch, path) -> None:
    """Point WORKFLOWS_DIR at a tmp dir and treat it as the boundary root."""
    monkeypatch.setattr(workflow, "WORKFLOWS_DIR", path)
    monkeypatch.setattr(boundary, "ROOT_RESOLVED", path.resolve())


@pytest.fixture()
def review_ui() -> dict[str, object]:
    return {
        "id": "review-ui",
        "nodes": [
            {"id": "plan", "agent": "reviewer", "prompt": "Plan review for: {{objective}}", "gate": "none"},
            {"id": "act", "agent": "reviewer", "prompt": "Execute: {{plan_output}}", "gate": "approval"},
        ],
        "edges": [["plan", "act"]],
        "stop": {"max_nodes": 10, "max_seconds": 1800},
    }


def test_valid_workflow_builds_ordered_ir(review_ui: dict[str, object]) -> None:
    assert workflow.validate_workflow(review_ui) == []
    ir = workflow.build_ir(review_ui)
    assert [node["id"] for node in ir] == ["plan", "act"]
    assert [node["order"] for node in ir] == [0, 1]
    assert ir[0]["agent"]["id"] == "reviewer"


def test_cycle_is_rejected(review_ui: dict[str, object]) -> None:
    data = deepcopy(review_ui)
    data["edges"] = [["plan", "act"], ["act", "plan"]]
    errors = workflow.validate_workflow(data)
    assert any("linear chain" in error for error in errors)


def test_unknown_agent_is_rejected(review_ui: dict[str, object]) -> None:
    data = deepcopy(review_ui)
    data["nodes"][0]["agent"] = "missing-agent"
    errors = workflow.validate_workflow(data)
    assert any("missing-agent" in error for error in errors)


def test_missing_or_invalid_stop_caps_are_rejected(review_ui: dict[str, object]) -> None:
    data = deepcopy(review_ui)
    data["stop"] = {"max_nodes": 10, "max_seconds": 0}
    errors = workflow.validate_workflow(data)
    assert any("stop.max_seconds" in error for error in errors)


def test_bad_template_reference_is_rejected(review_ui: dict[str, object]) -> None:
    data = deepcopy(review_ui)
    data["nodes"][1]["prompt"] = "Execute: {{act_output}}"
    errors = workflow.validate_workflow(data)
    assert any("{{act_output}}" in error for error in errors)


@pytest.mark.parametrize(
    ("change", "expected_ok"),
    [
        (lambda data: data, True),
        (lambda data: data.update(edges=[["plan", "act"], ["act", "plan"]]), False),
        (lambda data: data["nodes"][0].update(agent="missing-agent"), False),
        (lambda data: data.update(stop={"max_nodes": 10, "max_seconds": 0}), False),
        (lambda data: data["nodes"][1].update(prompt="Execute: {{nonexistent_output}}"), False),
    ],
)
def test_validate_endpoint_reports_every_case(
    review_ui: dict[str, object], change, expected_ok: bool
) -> None:
    data = deepcopy(review_ui)
    change(data)
    client = TestClient(server.app, headers={"x-hub-client": "harness-hub"})
    response = client.post("/api/workflows/validate", json={"yaml_text": yaml.safe_dump(data)})
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is expected_ok
    assert bool(body["errors"]) is not expected_ok
    assert (body["ir"] is not None) is expected_ok


def test_validate_endpoint_requires_yaml_text_or_id() -> None:
    client = TestClient(server.app, headers={"x-hub-client": "harness-hub"})
    response = client.post("/api/workflows/validate", json={})
    assert response.status_code == 400
    assert response.json()["detail"] == "yaml_text or id is required"


def test_save_workflow_writes_valid_yaml_and_backup(
    monkeypatch: pytest.MonkeyPatch, tmp_path, review_ui: dict[str, object]
) -> None:
    _use_workflows_dir(monkeypatch, tmp_path)
    path = tmp_path / "review-ui.workflow.yaml"
    old_text = yaml.safe_dump(review_ui)
    path.write_text(old_text, encoding="utf-8")
    updated = deepcopy(review_ui)
    updated["nodes"][0]["prompt"] = "Updated: {{objective}}"
    new_text = yaml.safe_dump(updated)

    result = workflow.save_workflow("review-ui", new_text)

    assert result["nodes"][0]["prompt"] == "Updated: {{objective}}"
    assert path.read_text(encoding="utf-8") == new_text
    backups = list(tmp_path.glob("review-ui.workflow.yaml.bak-*"))
    assert len(backups) == 1
    assert backups[0].read_text(encoding="utf-8") == old_text


def test_save_workflow_rejects_invalid_yaml_without_changes(
    monkeypatch: pytest.MonkeyPatch, tmp_path, review_ui: dict[str, object]
) -> None:
    _use_workflows_dir(monkeypatch, tmp_path)
    path = tmp_path / "review-ui.workflow.yaml"
    old_text = yaml.safe_dump(review_ui)
    path.write_text(old_text, encoding="utf-8")
    invalid = deepcopy(review_ui)
    invalid["nodes"][0]["gate"] = "invalid"

    with pytest.raises(ValueError, match="invalid gate"):
        workflow.save_workflow("review-ui", yaml.safe_dump(invalid))

    assert path.read_text(encoding="utf-8") == old_text
    assert list(tmp_path.glob("review-ui.workflow.yaml.bak-*")) == []


def test_save_workflow_rejects_mismatched_id(
    monkeypatch: pytest.MonkeyPatch, tmp_path, review_ui: dict[str, object]
) -> None:
    _use_workflows_dir(monkeypatch, tmp_path)
    (tmp_path / "review-ui.workflow.yaml").write_text(yaml.safe_dump(review_ui), encoding="utf-8")
    changed = deepcopy(review_ui)
    changed["id"] = "other"

    with pytest.raises(ValueError, match="must match"):
        workflow.save_workflow("review-ui", yaml.safe_dump(changed))


def test_save_workflow_requires_existing_file(monkeypatch: pytest.MonkeyPatch, tmp_path, review_ui: dict[str, object]) -> None:
    _use_workflows_dir(monkeypatch, tmp_path)

    with pytest.raises(FileNotFoundError):
        workflow.save_workflow("review-ui", yaml.safe_dump(review_ui))


def test_model_save_preserves_vietnamese_header_and_rejects_branch(
    monkeypatch: pytest.MonkeyPatch, tmp_path, review_ui: dict[str, object]
) -> None:
    _use_workflows_dir(monkeypatch, tmp_path)
    header = "# code-task\n# Bốn dòng tiếng Việt\n# Giữ nguyên\n# Kết thúc\n"
    path = tmp_path / "review-ui.workflow.yaml"
    path.write_text(header + yaml.safe_dump(review_ui, allow_unicode=True, sort_keys=False), encoding="utf-8")
    model = deepcopy(review_ui)
    model["nodes"][0]["prompt"] = "Mục tiêu: {{objective}}"
    saved = workflow.save_workflow("review-ui", workflow.model_yaml_text("review-ui", model))
    assert saved["nodes"][0]["prompt"] == "Mục tiêu: {{objective}}"
    written = path.read_text(encoding="utf-8")
    assert written.startswith(header)
    assert "Mục tiêu" in written

    before = written
    branched = deepcopy(model)
    branched["edges"] = [["plan", "act"], ["plan", "act"]]
    with pytest.raises(ValueError, match="linear chain"):
        workflow.save_workflow("review-ui", workflow.model_yaml_text("review-ui", branched))
    assert path.read_text(encoding="utf-8") == before
