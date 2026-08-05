from __future__ import annotations

from pathlib import Path
import re

import config
from services import boundary


_CHAT_ID = re.compile(r"[A-Za-z0-9_-]{1,128}\Z")
CHAT_FILE_CONTEXT_MAX_CHARS = 100_000


def _files_dir(chat_id: str) -> Path:
    if not _CHAT_ID.fullmatch(chat_id):
        raise FileNotFoundError("Chat not found")
    path = boundary.resolve_in_root(config.RUNTIME_STORE_DIR / "chats" / chat_id / "files", config.RUNTIME_STORE_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _path(chat_id: str, name: str) -> Path:
    if not name or Path(name).name != name or name in {".", ".."}:
        raise PermissionError("File path is outside chat root")
    return boundary.resolve_in_root(_files_dir(chat_id) / name, _files_dir(chat_id))


def list_files(chat_id: str) -> list[dict[str, object]]:
    root = _files_dir(chat_id)
    return [
        {"name": path.name, "size": path.stat().st_size, "updated_at": path.stat().st_mtime_ns}
        for path in sorted(root.iterdir(), key=lambda item: item.name.lower()) if path.is_file()
    ]


def list_all_files() -> list[dict[str, object]]:
    root = boundary.resolve_in_root(config.RUNTIME_STORE_DIR / "chats", config.RUNTIME_STORE_DIR)
    if not root.is_dir():
        return []
    items: list[dict[str, object]] = []
    for chat_dir in sorted(root.iterdir(), key=lambda item: item.name.lower()):
        if not chat_dir.is_dir() or not _CHAT_ID.fullmatch(chat_dir.name):
            continue
        for item in list_files(chat_dir.name):
            items.append({"chat_id": chat_dir.name, **item})
    return items


def upload(chat_id: str, name: str, content: bytes) -> dict[str, object]:
    if len(content) > config.RUNTIME_FILE_MAX_BYTES:
        raise ValueError("File exceeds size limit")
    root = _files_dir(chat_id)
    target = _path(chat_id, name)
    used = sum(path.stat().st_size for path in root.iterdir() if path.is_file())
    previous = target.stat().st_size if target.is_file() else 0
    if used - previous + len(content) > config.RUNTIME_FILES_MAX_BYTES:
        raise ValueError("Chat files exceed size limit")
    target.write_bytes(content)
    return {"name": target.name, "size": len(content), "updated_at": target.stat().st_mtime_ns}


def download(chat_id: str, name: str) -> Path:
    path = _path(chat_id, name)
    if not path.is_file():
        raise FileNotFoundError("File not found")
    return path


def delete(chat_id: str, name: str) -> None:
    download(chat_id, name).unlink()


def context(chat_id: str) -> str:
    parts: list[str] = []
    remaining = CHAT_FILE_CONTEXT_MAX_CHARS
    for item in list_files(chat_id):
        if remaining <= 0:
            break
        path = download(chat_id, str(item["name"]))
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            parts.append(f"[File đính kèm: {path.name}; nội dung nhị phân không được đưa vào prompt]")
            continue
        excerpt = text[:remaining]
        parts.append(f"[File đính kèm: {path.name}]\n{excerpt}")
        remaining -= len(excerpt)
    return "\n\n".join(parts)
