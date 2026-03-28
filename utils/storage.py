"""Persistent JSON storage for Discord message IDs."""

import json
import os
from pathlib import Path

STORAGE_FILE = Path("data/message_ids.json")


def _load() -> dict:
    STORAGE_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not STORAGE_FILE.exists():
        return {}
    try:
        return json.loads(STORAGE_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def _save(data: dict) -> None:
    STORAGE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STORAGE_FILE.write_text(json.dumps(data, indent=2))


def get_message_id(key: str) -> int | None:
    return _load().get(key)


def set_message_id(key: str, message_id: int) -> None:
    data = _load()
    data[key] = message_id
    _save(data)
