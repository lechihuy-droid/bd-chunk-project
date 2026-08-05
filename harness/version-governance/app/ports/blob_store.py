from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class BlobRef:
    uri: str
    content_hash: str
    size_bytes: int
    mime_type: str


class BlobStorePort(Protocol):
    def put_immutable(self, *, key: str, data: bytes, mime_type: str) -> BlobRef: ...

    def get(self, uri: str) -> bytes: ...

    def exists(self, key: str) -> bool: ...
