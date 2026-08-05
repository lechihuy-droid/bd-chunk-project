import ast
from pathlib import Path


BANNED = {"langgraph", "mlflow", "boto3", "sqlalchemy", "psycopg", "fastapi"}
ROOT = Path(__file__).resolve().parents[1]


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module.split(".")[0])
    return modules


def test_domain_and_ports_do_not_import_vendor_packages():
    violations: list[str] = []
    for package in ("domain", "ports"):
        for path in (ROOT / package).rglob("*.py"):
            forbidden = imported_modules(path) & BANNED
            violations.extend(f"{path.relative_to(ROOT)}: {name}" for name in sorted(forbidden))
    assert not violations, "Forbidden boundary imports:\n" + "\n".join(violations)
