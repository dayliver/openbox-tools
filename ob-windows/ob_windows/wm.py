"""Window-manager plumbing shared by ob-grid and ob-layout (python-xlib + EWMH).

Everything that talks to the X server lives here; the rest of the package is
pure. Windows are identified by their X id (``int``).

Why Xlib and not Gtk/Wnck: these commands run once per key press. Importing
Gtk+Wnck and pumping its main loop cost ~400 ms of a ~490 ms `ob-grid move`;
plain EWMH requests need neither.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from Xlib import X, display, error, protocol

from ob_windows.rect import Rect

_STATE_REMOVE, _STATE_ADD = 0, 1
_SOURCE_PAGER = 2  # EWMH "source indication": a pager/tool, not the app itself
_GRAVITY_STATIC = 10
_ICONIC_STATE = 3
_ALL_DESKTOPS = 0xFFFFFFFF

MAX_VERT = "_NET_WM_STATE_MAXIMIZED_VERT"
MAX_HORZ = "_NET_WM_STATE_MAXIMIZED_HORZ"
FULLSCREEN = "_NET_WM_STATE_FULLSCREEN"
HIDDEN = "_NET_WM_STATE_HIDDEN"


@dataclass
class ActiveWindow:
    xid: int
    name: str
    rect: Rect  # outer frame geometry (decorations included)
    work: Rect  # workarea of the monitor the window is on


# --------------------------------------------------------------------------
# connection / low-level helpers

_display: display.Display | None = None
_atoms: dict[str, int] = {}


def dpy() -> display.Display:
    global _display
    if _display is None:
        try:
            _display = display.Display()
        except (error.DisplayError, OSError) as exc:
            raise RuntimeError(f"cannot open X display — is DISPLAY set? ({exc})") from exc
    return _display


def _root():
    return dpy().screen().root


def _win(xid: int):
    return dpy().create_resource_object("window", int(xid))


def _atom(name: str) -> int:
    if name not in _atoms:
        _atoms[name] = dpy().intern_atom(name)
    return _atoms[name]


def _prop(xid: int | None, name: str) -> list[int] | bytes | None:
    """Property value (list of ints, or bytes for strings); None if unset / window gone."""
    win = _root() if xid is None else _win(xid)
    try:
        p = win.get_full_property(_atom(name), X.AnyPropertyType)
    except error.XError:
        return None
    if p is None:
        return None
    return p.value if isinstance(p.value, (bytes, str)) else list(p.value)


def _cardinals(xid: int | None, name: str) -> list[int]:
    v = _prop(xid, name)
    return v if isinstance(v, list) else []


def _send(xid: int | None, message: str, *data: int) -> None:
    """Ask the window manager to do something (EWMH client message to the root)."""
    packed = [int(v) & 0xFFFFFFFF for v in data][:5]
    packed += [0] * (5 - len(packed))
    ev = protocol.event.ClientMessage(
        window=_root() if xid is None else _win(xid),
        client_type=_atom(message),
        data=(32, packed),
    )
    _root().send_event(ev, event_mask=X.SubstructureRedirectMask | X.SubstructureNotifyMask)
    dpy().sync()


def _wait(done, timeout: float = 0.4, step: float = 0.005) -> bool:
    """Poll until ``done()`` — the WM handles our requests asynchronously."""
    deadline = time.monotonic() + timeout
    while True:
        if done():
            return True
        if time.monotonic() >= deadline:
            return False
        time.sleep(step)


# --------------------------------------------------------------------------
# window queries


def window_states(xid: int) -> set[str]:
    d = dpy()
    out = set()
    for a in _cardinals(xid, "_NET_WM_STATE"):
        try:
            out.add(d.get_atom_name(a))
        except error.XError:
            pass
    return out


def is_maximized(xid: int) -> bool:
    return {MAX_VERT, MAX_HORZ} <= window_states(xid)


def is_minimized(xid: int) -> bool:
    return HIDDEN in window_states(xid)


def is_normal(xid: int) -> bool:
    """EWMH window type NORMAL (unset type ⇒ normal unless it is a transient)."""
    types = _cardinals(xid, "_NET_WM_WINDOW_TYPE")
    if types:
        return _atom("_NET_WM_WINDOW_TYPE_NORMAL") in types
    return not _cardinals(xid, "WM_TRANSIENT_FOR")


def window_name(xid: int) -> str:
    v = _prop(xid, "_NET_WM_NAME")
    if isinstance(v, bytes):
        return v.decode("utf-8", "replace")
    try:
        legacy = _win(xid).get_wm_name()
    except error.XError:
        legacy = None
    if isinstance(legacy, bytes):
        return legacy.decode("latin-1", "replace")
    return legacy or ""


def window_class(xid: int) -> tuple[str, str]:
    """(instance, class) from WM_CLASS."""
    try:
        v = _win(xid).get_wm_class()
    except error.XError:
        v = None
    return (v[0] or "", v[1] or "") if v else ("", "")


def window_pid(xid: int) -> int | None:
    v = _cardinals(xid, "_NET_WM_PID")
    return v[0] if v else None


def frame_extents(xid: int) -> tuple[int, int, int, int]:
    """(left, right, top, bottom) decoration widths."""
    v = _cardinals(xid, "_NET_FRAME_EXTENTS")
    return (v[0], v[1], v[2], v[3]) if len(v) >= 4 else (0, 0, 0, 0)


def frame_rect(xid: int) -> Rect:
    """Outer frame geometry in root coordinates."""
    win = _win(xid)
    try:
        geo = win.get_geometry()
        origin = win.translate_coords(_root(), 0, 0)
    except error.XError as exc:
        raise RuntimeError(f"window 0x{xid:x} is gone") from exc
    left, right, top, bottom = frame_extents(xid)
    return Rect(
        -origin.x - left,
        -origin.y - top,
        geo.width + left + right,
        geo.height + top + bottom,
    )


def client_list(*, stacked: bool = False) -> list[int]:
    """Managed windows; with ``stacked`` in bottom-to-top order."""
    return _cardinals(None, "_NET_CLIENT_LIST_STACKING" if stacked else "_NET_CLIENT_LIST")


def active_window() -> ActiveWindow:
    """The focused normal window, else the topmost visible normal one."""
    v = _cardinals(None, "_NET_ACTIVE_WINDOW")
    xid = v[0] if v and v[0] else None
    if xid is None or not is_normal(xid):
        for candidate in reversed(client_list(stacked=True)):
            if is_normal(candidate) and not is_minimized(candidate):
                xid = candidate
                break
    if xid is None:
        raise RuntimeError("No active normal window")
    rect = frame_rect(xid)
    return ActiveWindow(xid=xid, name=window_name(xid), rect=rect, work=workarea_for_rect(rect))


# --------------------------------------------------------------------------
# monitors / workarea


def _monitors() -> list[tuple[Rect, bool]]:
    """[(geometry, is_primary)] — falls back to the whole screen without RandR."""
    try:
        from Xlib.ext import randr

        mons = randr.get_monitors(_root()).monitors
    except Exception:  # noqa: BLE001 — no RandR 1.5: treat the screen as one monitor
        mons = []
    out = [
        (Rect(m.x, m.y, m.width_in_pixels, m.height_in_pixels), bool(m.primary))
        for m in mons
    ]
    if not out:
        s = dpy().screen()
        out = [(Rect(0, 0, s.width_in_pixels, s.height_in_pixels), True)]
    return out


def _desktop_workarea() -> Rect | None:
    """_NET_WORKAREA of the current desktop (Openbox margins/struts removed)."""
    v = _cardinals(None, "_NET_WORKAREA")
    i = 4 * current_desktop()
    if len(v) < i + 4:
        i = 0
    if len(v) < 4:
        return None
    return Rect(v[i], v[i + 1], v[i + 2], v[i + 3])


def _monitor_workarea(monitor: Rect) -> Rect:
    work = _desktop_workarea()
    if work is None:
        return monitor
    return work.intersect(monitor) or monitor


def workarea_for_point(px: int, py: int) -> Rect:
    """Workarea of the monitor under a point (primary monitor if none is)."""
    mons = _monitors()
    for geo, _ in mons:
        if geo.contains(px, py):
            return _monitor_workarea(geo)
    return primary_workarea()


def workarea_for_rect(rect: Rect) -> Rect:
    return workarea_for_point(*rect.center)


def primary_workarea() -> Rect:
    mons = _monitors()
    geo = next((g for g, primary in mons if primary), mons[0][0])
    return _monitor_workarea(geo)


# --------------------------------------------------------------------------
# desktops (0-based)


def current_desktop() -> int:
    v = _cardinals(None, "_NET_CURRENT_DESKTOP")
    return v[0] if v else 0


def desktop_count() -> int:
    v = _cardinals(None, "_NET_NUMBER_OF_DESKTOPS")
    return v[0] if v else 1


def window_desktop(xid: int) -> int:
    """Desktop index; windows shown on all desktops count as desktop 0."""
    v = _cardinals(xid, "_NET_WM_DESKTOP")
    if not v or v[0] == _ALL_DESKTOPS:
        return 0
    return v[0]


def goto_desktop(index: int) -> None:
    if not 0 <= index < desktop_count():
        raise RuntimeError(f"desktop {index + 1} does not exist")
    if current_desktop() == index:
        return
    _send(None, "_NET_CURRENT_DESKTOP", index, X.CurrentTime)
    _wait(lambda: current_desktop() == index)


def move_to_desktop(xid: int, index: int) -> None:
    if not 0 <= index < desktop_count() or window_desktop(xid) == index:
        return
    _send(xid, "_NET_WM_DESKTOP", index, _SOURCE_PAGER)
    _wait(lambda: window_desktop(xid) == index)


# --------------------------------------------------------------------------
# actions


def _set_state(xid: int, action: int, first: str, second: str | None = None) -> None:
    _send(
        xid,
        "_NET_WM_STATE",
        action,
        _atom(first),
        _atom(second) if second else 0,
        _SOURCE_PAGER,
    )


def clear_wm_state(xid: int) -> None:
    """Drop fullscreen / maximized so an explicit geometry is honoured."""
    states = window_states(xid)
    if FULLSCREEN in states:
        _set_state(xid, _STATE_REMOVE, FULLSCREEN)
    if states & {MAX_VERT, MAX_HORZ}:
        _set_state(xid, _STATE_REMOVE, MAX_VERT, MAX_HORZ)
    if states & {FULLSCREEN, MAX_VERT, MAX_HORZ}:
        # Decorations (and so the frame extents) come back with the state change.
        _wait(lambda: not window_states(xid) & {FULLSCREEN, MAX_VERT, MAX_HORZ})


def apply_frame(xid: int, frame: Rect) -> None:
    """Move/resize so the outer frame lands exactly on ``frame``.

    Sent with STATIC gravity, where x/y are the client window's own root position
    and w/h its own size — so the frame extents are subtracted here once. Other
    gravities make Openbox re-apply the extents and drift a little on every call.
    """
    clear_wm_state(xid)
    left, right, top, bottom = frame_extents(xid)
    flags = _GRAVITY_STATIC | (0b1111 << 8) | (_SOURCE_PAGER << 12)  # x, y, w, h all set
    _send(
        xid,
        "_NET_MOVERESIZE_WINDOW",
        flags,
        frame.x + left,
        frame.y + top,
        max(1, frame.w - left - right),
        max(1, frame.h - top - bottom),
    )


def maximize(xid: int) -> None:
    _set_state(xid, _STATE_ADD, MAX_VERT, MAX_HORZ)


def minimize(xid: int) -> None:
    _send(xid, "WM_CHANGE_STATE", _ICONIC_STATE)
