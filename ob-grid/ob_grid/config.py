from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore

DEFAULT_CONFIG = Path(__file__).resolve().parent.parent / "config.default.toml"
USER_CONFIG = Path.home() / ".config" / "ob-grid" / "config.toml"


@dataclass(frozen=True)
class Config:
    horizontal: tuple[float, ...]
    vertical: tuple[float, ...]
    inner_gap: int
    tolerance_px: int


def ensure_user_config() -> Path:
    USER_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    if not USER_CONFIG.exists():
        shutil.copyfile(DEFAULT_CONFIG, USER_CONFIG)
    return USER_CONFIG


def _fractions(raw: list[object], *, axis: str) -> tuple[float, ...]:
    out: list[float] = []
    for item in raw:
        if isinstance(item, str) and "/" in item:
            a, b = item.split("/", 1)
            val = float(a) / float(b)
        else:
            val = float(item)  # type: ignore[arg-type]
        if not 0 < val <= 1:
            raise ValueError(f"grid.{axis} values must be in (0, 1], got {val}")
        out.append(val)
    vals = tuple(sorted(set(out)))
    if not vals:
        raise ValueError(f"grid.{axis} must not be empty")
    if vals[-1] != 1.0:
        vals = vals + (1.0,)
    return vals


def load_config(path: Path | None = None) -> Config:
    cfg_path = path or ensure_user_config()
    data = tomllib.loads(cfg_path.read_text(encoding="utf-8"))
    grid = data.get("grid", {})
    gaps = data.get("gaps", {})
    behavior = data.get("behavior", {})
    return Config(
        horizontal=_fractions(list(grid.get("horizontal", [0.5, 1.0])), axis="horizontal"),
        vertical=_fractions(list(grid.get("vertical", [0.5, 1.0])), axis="vertical"),
        inner_gap=int(gaps.get("inner", 10)),
        tolerance_px=int(behavior.get("tolerance_px", 12)),
    )
