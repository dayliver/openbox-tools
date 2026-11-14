from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PRESET_DIR = Path.home() / ".config" / "ob-layout" / "presets"


def _safe_name(name: str) -> str:
    name = name.strip()
    if not name:
        raise ValueError("empty preset name")
    if not re.fullmatch(r"[A-Za-z0-9._\-가-힣 ]{1,64}", name):
        raise ValueError("name may use letters, numbers, space, ._-, hangul (max 64)")
    return name


def preset_path(name: str) -> Path:
    return PRESET_DIR / f"{_safe_name(name)}.json"


def list_presets() -> list[str]:
    PRESET_DIR.mkdir(parents=True, exist_ok=True)
    names = []
    for p in sorted(PRESET_DIR.glob("*.json")):
        names.append(p.stem)
    return names


def load_preset(name: str) -> dict[str, Any]:
    path = preset_path(name)
    if not path.is_file():
        raise FileNotFoundError(f"preset not found: {name}")
    return json.loads(path.read_text())


def save_preset(name: str, data: dict[str, Any]) -> Path:
    PRESET_DIR.mkdir(parents=True, exist_ok=True)
    data = dict(data)
    data["name"] = _safe_name(name)
    data["version"] = 1
    data["saved_at"] = datetime.now(timezone.utc).isoformat()
    path = preset_path(name)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    return path


def delete_preset(name: str) -> None:
    path = preset_path(name)
    if not path.is_file():
        raise FileNotFoundError(f"preset not found: {name}")
    path.unlink()
