import os
import subprocess
from collections.abc import Iterator

import pytest
from sqlalchemy import text

_production_url = os.environ.get("VGOV_DATABASE_URL", "postgresql+psycopg://vgov:change-me@postgres:5432/vgov")
os.environ["VGOV_DATABASE_URL"] = os.environ.get(
    "VGOV_TEST_DATABASE_URL", _production_url.rsplit("/", 1)[0] + "/vgov_test"
)

from persistence.session import get_engine, get_sessionmaker


@pytest.fixture(scope="session", autouse=True)
def migrate_test_database() -> Iterator[None]:
    subprocess.run(["alembic", "-c", "alembic.ini", "upgrade", "head"], check=True, env=os.environ.copy())
    yield
    get_engine().dispose()


@pytest.fixture(autouse=True)
def clean_database() -> Iterator[None]:
    with get_engine().begin() as connection:
        connection.execute(text("TRUNCATE TABLE runtime_callback, approved_baseline, artifact_revision, artifact, run_component, run_manifest, execution_run, environment_mapping_audit, environment_mapping, workflow_release RESTART IDENTITY CASCADE"))
    yield


@pytest.fixture
def session() -> Iterator:
    db = get_sessionmaker()()
    try:
        yield db
    finally:
        db.close()
