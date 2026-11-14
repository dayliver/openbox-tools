"""Layout-specific window queries: enumeration, workspaces, terminal cwd."""

from __future__ import annotations

import os
import re
import subprocess
import sys
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path

from ob_windows import wm
from ob_windows.rect import Rect


@dataclass
class WinInfo:
    wnck: wm.Wnck.Window
    xid: int
    klass: str
    instance: str
    title: str
    desktop: int  # 0-based
    rect: Rect
    maximized: bool
    cwd: str | None = None


def window_pid(xid: int) -> int | None:
    try:
        out = subprocess.check_output(
            ["xprop", "-id", str(xid), "_NET_WM_PID"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    m = re.search(r"=\s*(\d+)", out)
    return int(m.group(1)) if m else None


_SHELL_NAMES = {
    "bash",
    "zsh",
    "fish",
    "sh",
    "dash",
    "tmux",
    "nu",
    "xonsh",
}


def _proc_comm(pid: int) -> str:
    try:
        return Path(f"/proc/{pid}/comm").read_text().strip()
    except OSError:
        return ""


def _proc_children(pid: int) -> list[int]:
    try:
        text = Path(f"/proc/{pid}/task/{pid}/children").read_text()
    except OSError:
        return []
    return [int(x) for x in text.split() if x.isdigit()]


def _proc_cwd(pid: int) -> str | None:
    try:
        cwd = os.readlink(f"/proc/{pid}/cwd")
    except OSError:
        return None
    if not cwd or not os.path.isdir(cwd):
        return None
    return cwd


def window_cwd(xid: int) -> str | None:
    """Terminal-aware cwd: prefer foreground shell child over emulator process."""
    root = window_pid(xid)
    if not root:
        return None

    # BFS: collect shell-like children first, else deepest child cwd, else root
    shells: list[int] = []
    others: list[int] = []
    q: deque[int] = deque([root])
    seen = {root}
    while q:
        pid = q.popleft()
        for child in _proc_children(pid):
            if child in seen:
                continue
            seen.add(child)
            q.append(child)
            name = _proc_comm(child)
            if name in _SHELL_NAMES:
                shells.append(child)
            else:
                others.append(child)

    for pid in reversed(shells):
        cwd = _proc_cwd(pid)
        if cwd:
            return cwd
    for pid in reversed(others):
        cwd = _proc_cwd(pid)
        if cwd:
            return cwd
    return _proc_cwd(root)


def current_desktop() -> int:
    s = wm.screen()
    ws = s.get_active_workspace()
    return int(ws.get_number()) if ws else 0


def goto_desktop(index: int) -> None:
    s = wm.screen()
    for ws in s.get_workspaces():
        if ws.get_number() == index:
            ws.activate(0)
            wm.pump(0.2)
            return
    raise RuntimeError(f"desktop {index + 1} does not exist")


def list_normal_windows(desktop: int | None = None) -> list[WinInfo]:
    s = wm.screen()
    out: list[WinInfo] = []
    for w in s.get_windows():
        if not wm.is_normal(w):
            continue
        if w.is_minimized():
            continue
        ws = w.get_workspace()
        desk = int(ws.get_number()) if ws else 0
        if desktop is not None and desk != desktop:
            continue
        xid = int(w.get_xid())
        out.append(
            WinInfo(
                wnck=w,
                xid=xid,
                klass=(w.get_class_group_name() or "").strip() or "Unknown",
                instance=(w.get_class_instance_name() or "").strip() or "unknown",
                title=(w.get_name() or "").strip(),
                desktop=desk,
                rect=wm.frame_rect(w),
                maximized=bool(w.is_maximized()),
                cwd=window_cwd(xid),
            )
        )
    # Stable order: top-left first
    out.sort(key=lambda wi: (wi.rect.y, wi.rect.x, wi.klass))
    return out


def move_to_desktop(win: wm.Wnck.Window, desktop: int) -> None:
    s = wm.screen()
    for ws in s.get_workspaces():
        if ws.get_number() == desktop:
            win.move_to_workspace(ws)
            wm.pump(0.1)
            return


def wait_for_window(klass: str, instance: str | None, timeout: float = 8.0) -> WinInfo | None:
    deadline = time.time() + timeout
    klass_l = klass.lower()
    inst_l = (instance or "").lower()
    seen: set[int] = {w.xid for w in list_normal_windows()}
    while time.time() < deadline:
        wm.pump(0.15)
        for wi in list_normal_windows():
            if wi.xid in seen:
                continue
            if wi.klass.lower() == klass_l or (
                inst_l and wi.instance.lower() == inst_l
            ):
                return wi
            # also accept new windows matching either
            if wi.klass.lower() == klass_l:
                return wi
        # also match existing if launched replaced
        for wi in list_normal_windows():
            if wi.klass.lower() == klass_l and wi.xid not in seen:
                return wi
        time.sleep(0.2)
    # last chance: any matching class
    cands = [w for w in list_normal_windows() if w.klass.lower() == klass_l]
    return cands[-1] if cands else None


def notify(msg: str, urgent: bool = False) -> None:
    try:
        subprocess.run(
            [
                "dunstify",
                "-u",
                "critical" if urgent else "low",
                "-h",
                "string:x-dunst-stack-tag:oblayout",
                "Layout",
                msg,
            ],
            check=False,
        )
    except FileNotFoundError:
        print(msg, file=sys.stderr)
