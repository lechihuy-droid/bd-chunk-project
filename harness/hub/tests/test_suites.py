from __future__ import annotations

from services import suites


def test_list_suites_includes_top_level_and_probe_json() -> None:
    items = suites.list_suites()
    ids = {item["id"] for item in items}
    assert "workspace-smoke" in ids
    assert "boundary-compliance" in ids
    assert "probe-outside-root-read" in ids


def test_get_workspace_smoke_suite_contract() -> None:
    suite = suites.get_suite("workspace-smoke")
    assert suite["name"] == "Workspace Smoke Harness"
    assert suite["check_count"] >= 11
    assert suite["path"] == "harness/suites/workspace-smoke.json"
    assert all(check["id"] and check["type"] for check in suite["checks"])
    assert "raw" in suite["checks"][0]
