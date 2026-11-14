from __future__ import annotations

from typing import Any

from ob_windows import wm
from ob_windows.layout import launch as launchmod
from ob_windows.layout import windows as W
from ob_windows.layout.ratio import from_fractions, to_fractions


def capture_current_workspace() -> dict[str, Any]:
    desk = W.current_desktop()
    wins = W.list_normal_windows(desktop=desk)
    if not wins:
        raise RuntimeError("no normal windows on this workspace")

    entries = []
    for wi in wins:
        frac = to_fractions(wi.rect, wm.workarea_for_rect(wi.rect))
        covers = frac["w"] >= 0.95 and frac["h"] >= 0.95
        maximized = bool(wi.maximized or covers)
        if maximized:
            frac = {"x": 0.0, "y": 0.0, "w": 1.0, "h": 1.0}
        else:
            for k in ("x", "y", "w", "h"):
                frac[k] = max(0.0, min(1.0, frac[k]))
            frac["w"] = max(0.05, frac["w"])
            frac["h"] = max(0.05, frac["h"])
        entry: dict[str, Any] = {
            "class": wi.klass,
            "instance": wi.instance,
            "title": wi.title[:120],
            "launch": launchmod.resolve_launch(wi.klass, wi.instance),
            "maximized": maximized,
            "x": frac["x"],
            "y": frac["y"],
            "w": frac["w"],
            "h": frac["h"],
        }
        if wi.cwd:
            entry["cwd"] = wi.cwd
        entries.append(entry)
    return {
        "desktop": desk,
        "windows": entries,
    }


def _take_from_pool(
    pool: dict[str, list[W.WinInfo]],
    klass: str,
    cwd: str | None,
) -> W.WinInfo | None:
    """Reuse an existing window. If cwd is set, only reuse an exact cwd match."""
    key = klass.lower()
    cands = pool.get(key) or []
    if not cands:
        return None
    if cwd:
        for i, wi in enumerate(cands):
            if wi.cwd == cwd:
                return cands.pop(i)
        # Wrong cwd → launch a fresh terminal instead of stealing another.
        return None
    return cands.pop(0)


def restore_preset(data: dict[str, Any]) -> tuple[int, int]:
    """Returns (placed, failed)."""
    desk = int(data.get("desktop", 0))
    W.goto_desktop(desk)
    work = wm.primary_workarea()

    pool: dict[str, list[W.WinInfo]] = {}
    for wi in W.list_normal_windows():
        pool.setdefault(wi.klass.lower(), []).append(wi)

    placed = 0
    failed = 0
    for entry in data.get("windows", []):
        klass = entry.get("class") or "Unknown"
        instance = entry.get("instance") or ""
        cwd = entry.get("cwd") or None
        if cwd and not isinstance(cwd, str):
            cwd = None

        wi = _take_from_pool(pool, klass, cwd)
        if wi is None:
            base = entry.get("launch") or launchmod.resolve_launch(klass, instance)
            if not base:
                W.notify(f"cannot launch: {klass}", urgent=True)
                failed += 1
                continue
            cmd = launchmod.build_launch_cmd(base, klass, cwd)
            before = {w.xid for w in W.list_normal_windows()}
            launchmod.launch(cmd)
            wi = W.wait_for_window(klass, instance, timeout=10.0)
            if wi is None:
                for w in W.list_normal_windows():
                    if w.xid not in before:
                        wi = w
                        break
            if wi is None:
                W.notify(f"window did not appear: {klass}", urgent=True)
                failed += 1
                continue

        W.move_to_desktop(wi.wnck, desk)
        if entry.get("maximized"):
            wm.maximize(wi.wnck)
        else:
            frame = from_fractions(
                float(entry["x"]),
                float(entry["y"]),
                float(entry["w"]),
                float(entry["h"]),
                work,
            )
            wm.apply_frame(wi.wnck, frame)
        placed += 1

    W.goto_desktop(desk)
    return placed, failed
