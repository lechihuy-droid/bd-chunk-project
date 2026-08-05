import hashlib
from concurrent.futures import ThreadPoolExecutor

from domain.artifact import ArtifactIdentity
from persistence.models import ArtifactRevision
from persistence.session import get_sessionmaker
from ports.blob_store import BlobRef
from services.artifact_service import ArtifactService


class BlobFake:
    def __init__(self) -> None:
        self.items: dict[str, bytes] = {}

    def put_immutable(self, *, key: str, data: bytes, mime_type: str) -> BlobRef:
        self.items.setdefault(key, data)
        return BlobRef(f"s3://vgov-artifacts/{key}", "sha256:" + hashlib.sha256(data).hexdigest(), len(data), mime_type)

    def get(self, uri: str) -> bytes:
        return self.items[uri.removeprefix("s3://vgov-artifacts/")]

    def exists(self, key: str) -> bool:
        return key in self.items


def test_parallel_revisions_are_serialized_by_artifact_lock() -> None:
    blobs = BlobFake()
    identity = ArtifactIdentity("project", "API_BASIC_DESIGN", "F001")

    def create(content: bytes) -> int:
        session = get_sessionmaker()()
        try:
            revision = ArtifactService(session, blobs).create_imported(identity, content, "text/markdown", "test", "F001")
            session.commit()
            return revision.revision_no
        finally:
            session.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        numbers = list(pool.map(create, (b"one", b"two")))
    assert sorted(numbers) == [1, 2]
