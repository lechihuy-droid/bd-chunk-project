from __future__ import annotations

import logging
import json
import math
import re
import time
from pathlib import Path
from typing import Any

import yaml

import config
from services import boundary, runtime_agents


WORKFLOWS_DIR = config.HUB_DIR / "workflows"
_REQUIRED_TOP_LEVEL_FIELDS = ("id", "nodes", "edges", "stop")
_TEMPLATE_REF = re.compile(r"{{(.*?)}}")


def workflow_path(workflow_id: str) -> Path:
    """Resolve the file for a caller-supplied workflow id, rejecting traversal outside WORKFLOWS_DIR."""
    return boundary.resolve_in_root(f"{workflow_id}.workflow.yaml", base=WORKFLOWS_DIR)


def workflow_layout_path(workflow_id: str) -> Path:
    """Resolve the layout sidecar through the same workflow-id boundary guard."""
    path = workflow_path(workflow_id)
    return path.with_name(f"{workflow_id}.layout.json")


def read_layout(workflow_id: str) -> dict[str, dict[str, float]]:
    """Read valid coordinates for nodes currently present in a workflow."""
    path = workflow_layout_path(workflow_id)
    workflow_data = parse_workflow(workflow_path(workflow_id).read_text(encoding="utf-8"))
    node_ids = {node.get("id") for node in workflow_data.get("nodes", []) if isinstance(node, dict)}
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except (OSError, ValueError, yaml.YAMLError):
        return {}
    if not isinstance(raw, dict) or not isinstance(raw.get("nodes"), dict):
        return {}
    result: dict[str, dict[str, float]] = {}
    for node_id, position in raw["nodes"].items():
        if node_id not in node_ids or not isinstance(position, dict):
            continue
        x, y = position.get("x"), position.get("y")
        if all(isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) for value in (x, y)):
            result[node_id] = {"x": x, "y": y}
    return result


def save_layout(workflow_id: str, layout: dict[str, Any]) -> dict[str, dict[str, float]]:
    """Filter and persist node coordinates without touching workflow YAML."""
    path = workflow_layout_path(workflow_id)
    workflow_data = parse_workflow(workflow_path(workflow_id).read_text(encoding="utf-8"))
    node_ids = {node.get("id") for node in workflow_data.get("nodes", []) if isinstance(node, dict)}
    raw_nodes = layout.get("nodes") if isinstance(layout, dict) else None
    if not isinstance(raw_nodes, dict):
        raise ValueError("layout.nodes must be a mapping")
    filtered: dict[str, dict[str, float]] = {}
    for node_id, position in raw_nodes.items():
        if node_id not in node_ids or not isinstance(position, dict):
            continue
        x, y = position.get("x"), position.get("y")
        if all(isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) for value in (x, y)):
            filtered[node_id] = {"x": x, "y": y}
    path.write_text(json.dumps({"nodes": filtered}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return filtered


def parse_workflow(yaml_text: str) -> dict[str, Any]:
    """Parse a workflow YAML document and ensure its required shape exists."""
    try:
        data = yaml.safe_load(yaml_text)
    except yaml.YAMLError as exc:
        raise ValueError(f"Malformed workflow YAML: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("Workflow YAML must contain a top-level mapping")
    missing = [field for field in _REQUIRED_TOP_LEVEL_FIELDS if field not in data]
    if missing:
        raise ValueError(f"Workflow YAML missing required top-level fields: {', '.join(missing)}")
    return data


def _walk_chain(nodes: list[dict[str, Any]], edges: list[Any]) -> tuple[list[str] | None, bool]:
    node_ids = [node.get("id") for node in nodes if isinstance(node.get("id"), str)]
    node_id_set = set(node_ids)
    in_degree = {node_id: 0 for node_id in node_id_set}
    out_degree = {node_id: 0 for node_id in node_id_set}
    next_node: dict[str, str] = {}
    usable_edges = True

    for edge in edges:
        if not isinstance(edge, (list, tuple)) or len(edge) != 2:
            usable_edges = False
            continue
        source, target = edge
        if source not in node_id_set or target not in node_id_set:
            usable_edges = False
            continue
        out_degree[source] += 1
        in_degree[target] += 1
        next_node[source] = target

    starts = [node_id for node_id, degree in in_degree.items() if degree == 0]
    ends = [node_id for node_id, degree in out_degree.items() if degree == 0]
    degrees_valid = all(degree <= 1 for degree in in_degree.values()) and all(
        degree <= 1 for degree in out_degree.values()
    )
    if not usable_edges or not degrees_valid or len(starts) != 1 or len(ends) != 1:
        return None, False

    walk: list[str] = []
    seen: set[str] = set()
    current = starts[0]
    while True:
        if current in seen:
            return None, False
        seen.add(current)
        walk.append(current)
        if current not in next_node:
            break
        current = next_node[current]

    if len(walk) != len(nodes) or len(seen) != len(node_id_set):
        return None, False
    return walk, True


def validate_workflow(data: dict[str, Any], available_agents: set[str] | None = None) -> list[str]:
    """Return every content-validation error for a parsed workflow."""
    errors: list[str] = []
    nodes_value = data.get("nodes")
    edges_value = data.get("edges")
    stop_value = data.get("stop")
    nodes = nodes_value if isinstance(nodes_value, list) else []
    edges = edges_value if isinstance(edges_value, list) else []

    if not isinstance(nodes_value, list):
        errors.append("nodes must be a list")
    normalized_nodes: list[dict[str, Any]] = []
    node_ids: set[str] = set()
    for index, node in enumerate(nodes):
        if not isinstance(node, dict):
            errors.append(f"Node {index} must be a mapping")
            continue
        normalized_nodes.append(node)
        node_type = node.get("type", "agent")
        if node_type not in {"agent", "validate"}:
            errors.append(f"Node {node.get('id', index)} has unknown type: {node_type}")
        elif node_type == "agent":
            for field in ("id", "agent", "prompt", "gate"):
                if field not in node:
                    errors.append(f"Node {index} missing required field: {field}")
        else:
            for field in ("id", "target", "checks", "on_fail"):
                if field not in node:
                    errors.append(f"Node {index} missing required field: {field}")
        node_id = node.get("id")
        if not isinstance(node_id, str) or not node_id:
            errors.append(f"Node {index} id must be a non-empty string")
        elif node_id in node_ids:
            errors.append(f"Duplicate node id: {node_id}")
        else:
            node_ids.add(node_id)
        if node_type == "agent":
            if node.get("gate") not in {"none", "approval"}:
                errors.append(f"Node {node.get('id', index)} has invalid gate: {node.get('gate')}")
            if not isinstance(node.get("prompt"), str):
                errors.append(f"Node {node.get('id', index)} prompt must be a string")
        elif node_type == "validate":
            target = node.get("target")
            if not isinstance(target, str) or not target:
                errors.append(f"Node {node.get('id', index)} target must be a non-empty string")
            checks = node.get("checks")
            if not isinstance(checks, list) or not checks:
                errors.append(f"Node {node.get('id', index)} checks must be a non-empty list")
            else:
                for check_index, check in enumerate(checks):
                    if not isinstance(check, dict):
                        errors.append(f"Node {node.get('id', index)} check {check_index} must be a mapping")
                        continue
                    kind = check.get("kind")
                    if kind not in {"min_length", "must_include", "must_not_include", "json_parseable"}:
                        errors.append(f"Node {node.get('id', index)} check {check_index} has unknown kind: {kind}")
                    elif kind == "min_length":
                        value = check.get("value")
                        if not isinstance(value, int) or isinstance(value, bool):
                            errors.append(f"Node {node.get('id', index)} check {check_index} min_length value must be an integer")
                    elif kind in {"must_include", "must_not_include"}:
                        values = check.get("values")
                        if not isinstance(values, list) or not values or not all(isinstance(value, str) for value in values):
                            errors.append(f"Node {node.get('id', index)} check {check_index} values must be a non-empty list of strings")
            if node.get("on_fail") not in {"interrupt", "fail"}:
                errors.append(f"Node {node.get('id', index)} has invalid on_fail: {node.get('on_fail')}")

    if available_agents is None:
        available_agents = {agent["id"] for agent in runtime_agents.list_agents()}
    for node in normalized_nodes:
        if node.get("type", "agent") != "agent":
            continue
        agent_id = node.get("agent")
        if agent_id not in available_agents:
            errors.append(f"Node {node.get('id', '?')} references unknown agent: {agent_id}")
        spawn = node.get("spawn", [])
        if not isinstance(spawn, list):
            errors.append(f"Node {node.get('id', '?')} spawn must be a list")
            continue
        for index, item in enumerate(spawn):
            if not isinstance(item, dict):
                errors.append(f"Node {node.get('id', '?')} spawn {index} must be a mapping")
                continue
            spawn_agent = item.get("agent")
            if spawn_agent not in available_agents:
                errors.append(f"Node {node.get('id', '?')} spawn {index} references unknown agent: {spawn_agent}")
            spawn_objective = item.get("objective")
            if not isinstance(spawn_objective, str) or not spawn_objective.strip():
                errors.append(f"Node {node.get('id', '?')} spawn {index} objective must be a non-empty string")

    if not isinstance(edges_value, list):
        errors.append("edges must be a list")
    for index, edge in enumerate(edges):
        if not isinstance(edge, (list, tuple)) or len(edge) != 2:
            errors.append(f"Edge {index} must contain exactly two node ids")
            continue
        for node_id in edge:
            if node_id not in node_ids:
                errors.append(f"Edge {index} references unknown node id: {node_id}")

    walk, chain_valid = _walk_chain(normalized_nodes, edges)
    if not chain_valid:
        errors.append("Edges must form exactly one linear chain covering every node once")

    if not isinstance(stop_value, dict):
        errors.append("stop must be a mapping with max_nodes and max_seconds")
    else:
        max_nodes = stop_value.get("max_nodes")
        if not isinstance(max_nodes, int) or isinstance(max_nodes, bool) or max_nodes <= 0:
            errors.append("stop.max_nodes must be a positive integer")
        max_seconds = stop_value.get("max_seconds")
        if (
            not isinstance(max_seconds, (int, float))
            or isinstance(max_seconds, bool)
            or max_seconds <= 0
        ):
            errors.append("stop.max_seconds must be a positive number")

    if chain_valid and walk is not None:
        walk_position = {node_id: position for position, node_id in enumerate(walk)}
        for node in normalized_nodes:
            node_id = node.get("id")
            if node.get("type", "agent") == "validate":
                target = node.get("target")
                if target not in node_ids:
                    errors.append(f"Node {node_id} references unknown target: {target}")
                elif target == node_id:
                    errors.append(f"Node {node_id} cannot target itself")
                elif isinstance(node_id, str) and walk_position.get(target, -1) >= walk_position.get(node_id, 0):
                    errors.append(f"Node {node_id} target must be an earlier node: {target}")
                continue
            prompt = node.get("prompt")
            if not isinstance(node_id, str):
                continue
            templates: list[tuple[str, str]] = [("prompt", prompt)] if isinstance(prompt, str) else []
            spawn = node.get("spawn", [])
            if not isinstance(spawn, list):
                continue
            for index, item in enumerate(spawn):
                if not isinstance(item, dict):
                    continue
                spawn_objective = item.get("objective")
                if isinstance(spawn_objective, str) and spawn_objective.strip():
                    templates.append((f"spawn {index} objective", spawn_objective))
            for _label, template in templates:
                for token in _TEMPLATE_REF.findall(template):
                    if token == "objective":
                        continue
                    match = re.fullmatch(r"(.+)_(output|claims)", token)
                    if match and match.group(1) in walk_position and walk_position[match.group(1)] < walk_position[node_id]:
                        continue
                    errors.append(f"Node {node_id} has invalid template reference: {{{{{token}}}}}")
    else:
        errors.append("Template validation skipped because the workflow chain is invalid")

    return errors


def build_ir(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Resolve a valid workflow into its start-to-end execution order."""
    nodes = data["nodes"]
    edges = data["edges"]
    walk, chain_valid = _walk_chain(nodes, edges)
    if not chain_valid or walk is None:
        raise ValueError("Cannot build IR for an invalid workflow chain")
    nodes_by_id = {node["id"]: node for node in nodes}
    agents_by_id = {agent["id"]: agent for agent in runtime_agents.list_agents()}
    result: list[dict[str, Any]] = []
    for order, node_id in enumerate(walk):
        node = nodes_by_id[node_id]
        if node.get("type", "agent") == "validate":
            result.append({
                "id": node_id,
                "type": "validate",
                "target": node["target"],
                "checks": [dict(check) for check in node["checks"]],
                "on_fail": node["on_fail"],
                "order": order,
            })
            continue
        result.append({
            "id": node_id,
            "agent": dict(agents_by_id[node["agent"]]),
            "prompt": node["prompt"],
            "gate": node["gate"],
            "spawn": [
                {"agent": dict(agents_by_id[item["agent"]]), "objective": item["objective"]}
                for item in node.get("spawn", [])
            ],
            "order": order,
        })
    return result


def list_workflows() -> list[dict[str, Any]]:
    """Load only valid workflow definitions, warning for malformed files."""
    workflows: list[dict[str, Any]] = []
    if not WORKFLOWS_DIR.exists():
        return workflows
    available_agents = {agent["id"] for agent in runtime_agents.list_agents()}
    logger = logging.getLogger(__name__)
    for path in WORKFLOWS_DIR.glob("*.workflow.yaml"):
        try:
            data = parse_workflow(path.read_text(encoding="utf-8"))
            errors = validate_workflow(data, available_agents)
            if errors:
                logger.warning("Skipping invalid workflow %s: %s", path, "; ".join(errors))
                continue
            workflows.append(data)
        except (OSError, ValueError) as exc:
            logger.warning("Skipping invalid workflow %s: %s", path, exc)
    return workflows


def save_workflow(workflow_id: str, yaml_text: str) -> dict[str, Any]:
    """Validate and replace an existing workflow, retaining one timestamped backup."""
    data = parse_workflow(yaml_text)
    errors = validate_workflow(data)
    if errors:
        raise ValueError("; ".join(errors))
    if data["id"] != workflow_id:
        raise ValueError("Workflow id must match the path id")

    path = workflow_path(workflow_id)
    old_bytes = path.read_bytes()
    backup = path.with_name(f"{path.name}.bak-{int(time.time())}")
    backup.write_bytes(old_bytes)
    path.write_text(yaml_text, encoding="utf-8")
    return data


def model_yaml_text(workflow_id: str, model: dict[str, Any]) -> str:
    """Serialize a model while retaining the existing leading comment block."""
    source = workflow_path(workflow_id).read_text(encoding="utf-8")
    lines: list[str] = []
    for line in source.splitlines(keepends=True):
        if line.strip() == "" or line.lstrip().startswith("#"):
            lines.append(line)
            continue
        break
    header = "".join(lines)
    dumped = yaml.safe_dump(model, sort_keys=False, allow_unicode=True, default_flow_style=False)
    return header + dumped
