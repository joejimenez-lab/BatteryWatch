from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


SESSIONS_DIR = Path("sessions")


def utc_timestamp() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def ensure_sessions_dir() -> Path:
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    return SESSIONS_DIR


def next_session_path(mode: str) -> Path:
    sessions_dir = ensure_sessions_dir()
    existing = sorted(sessions_dir.glob(f"{mode}_*.json"))
    next_index = len(existing) + 1
    return sessions_dir / f"{mode}_{next_index:03d}.json"


def save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
