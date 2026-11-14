from __future__ import annotations

import os
import re
import subprocess
import sys
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("Wnck", "3.0")

from gi.repository import Gdk, Gtk, Wnck  # noqa: E402


@dataclass(frozen=True)
class Rect:
    x: int
    y: int
    w: int
    h: int

    @property
    def x2(self) -> int:
        return self.x + self.w

    @property
    def y2(self) -> int:
        return self.y + self.h


@dataclass
class WinInfo:
    wnck: Wnck.Window
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


def _ensure_gtk() -> None:
    if not Gtk.init_check(sys.argv)[0]:
        raise RuntimeError("Gtk.init failed — is DISPLAY set?")


def _pump(seconds: float = 0.12) -> None:
    end = time.time() + seconds
    while time.time() < end:
        while Gtk.events_pending():
            Gtk.main_iteration_do(False)
        time.sleep(0.01)


def screen() -> Wnck.Screen:
    _ensure_gtk()
    s = Wnck.Screen.get_default()
    s.force_update()
    _pump(0.05)
    return s


def workarea_for_point(px: int, py: int) -> Rect:
    display = Gdk.Display.get_default()
    if display is None:
        raise RuntimeError("No Gdk display")
    monitor = display.get_monitor_at_point(px, py)
    if monitor is None:
        monitor = display.get_primary_monitor()
    geo = monitor.get_workarea()
    return Rect(geo.x, geo.y, geo.width, geo.height)


def primary_workarea() -> Rect:
    display = Gdk.Display.get_default()
    mon = display.get_primary_monitor() or display.get_monitor(0)
    geo = mon.get_workarea()
    return Rect(geo.x, geo.y, geo.width, geo.height)


def current_desktop() -> int:
    s = screen()
    ws = s.get_active_workspace()
    return int(ws.get_number()) if ws else 0


def goto_desktop(index: int) -> None:
    s = screen()
    for ws in s.get_workspaces():
        if ws.get_number() == index:
            ws.activate(0)
            _pump(0.2)
            return
    raise RuntimeError(f"desktop {index + 1} does not exist")


def list_normal_windows(desktop: int | None = None) -> list[WinInfo]:
    s = screen()
    out: list[WinInfo] = []
    for w in s.get_windows():
        if w.get_window_type() != Wnck.WindowType.NORMAL:
            continue
        if w.is_minimized():
            continue
        ws = w.get_workspace()
        desk = int(ws.get_number()) if ws else 0
        if desktop is not None and desk != desktop:
            continue
        x, y, ww, hh = w.get_geometry()
        xid = int(w.get_xid())
        out.append(
            WinInfo(
                wnck=w,
                xid=xid,
                klass=(w.get_class_group_name() or "").strip() or "Unknown",
                instance=(w.get_class_instance_name() or "").strip() or "unknown",
                title=(w.get_name() or "").strip(),
                desktop=desk,
                rect=Rect(int(x), int(y), int(ww), int(hh)),
                maximized=bool(w.is_maximized()),
                cwd=window_cwd(xid),
            )
        )
    # Stable order: top-left first
    out.sort(key=lambda wi: (wi.rect.y, wi.rect.x, wi.klass))
    return out


def to_fractions(rect: Rect, work: Rect) -> dict[str, float]:
    if work.w <= 0 or work.h <= 0:
        raise RuntimeError("invalid workarea")
    return {
        "x": round((rect.x - work.x) / work.w, 6),
        "y": round((rect.y - work.y) / work.h, 6),
        "w": round(rect.w / work.w, 6),
        "h": round(rect.h / work.h, 6),
    }


def from_fractions(fx: float, fy: float, fw: float, fh: float, work: Rect) -> Rect:
    x = int(round(work.x + fx * work.w))
    y = int(round(work.y + fy * work.h))
    w = max(50, int(round(fw * work.w)))
    h = max(50, int(round(fh * work.h)))
    # Clamp into workarea
    if x < work.x:
        x = work.x
    if y < work.y:
        y = work.y
    if x + w > work.x2:
        w = max(50, work.x2 - x)
    if y + h > work.y2:
        h = max(50, work.y2 - y)
    return Rect(x, y, w, h)


def _clear_wm_state(win: Wnck.Window) -> None:
    changed = False
    if hasattr(win, "is_fullscreen") and win.is_fullscreen():
        win.set_fullscreen(False)
        changed = True
    if win.is_maximized():
        win.unmaximize()
        changed = True
    if win.is_maximized_horizontally():
        win.unmaximize_horizontally()
        changed = True
    if win.is_maximized_vertically():
        win.unmaximize_vertically()
        changed = True
    if changed:
        _pump(0.12)


def apply_frame(win: Wnck.Window, frame: Rect) -> None:
    _clear_wm_state(win)
    mask = (
        Wnck.WindowMoveResizeMask.X
        | Wnck.WindowMoveResizeMask.Y
        | Wnck.WindowMoveResizeMask.WIDTH
        | Wnck.WindowMoveResizeMask.HEIGHT
    )
    win.set_geometry(
        Wnck.WindowGravity.STATIC,
        mask,
        int(frame.x),
        int(frame.y),
        int(frame.w),
        int(frame.h),
    )
    _pump(0.18)


def move_to_desktop(win: Wnck.Window, desktop: int) -> None:
    s = screen()
    for ws in s.get_workspaces():
        if ws.get_number() == desktop:
            win.move_to_workspace(ws)
            _pump(0.1)
            return


def maximize(win: Wnck.Window) -> None:
    win.maximize()
    _pump(0.12)


def wait_for_window(klass: str, instance: str | None, timeout: float = 8.0) -> WinInfo | None:
    deadline = time.time() + timeout
    klass_l = klass.lower()
    inst_l = (instance or "").lower()
    seen: set[int] = {w.xid for w in list_normal_windows()}
    while time.time() < deadline:
        _pump(0.15)
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
