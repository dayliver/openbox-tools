"""Heuristic category assignment for keybinds."""

from __future__ import annotations

from keybinder.models import Action, Category, Keybind

WINDOW_ACTIONS = {
    "NextWindow",
    "PreviousWindow",
    "GoToDesktop",
    "SendToDesktop",
    "AddDesktop",
    "RemoveDesktop",
    "ToggleShowDesktop",
    "MoveRelative",
    "ResizeRelative",
    "MoveResizeTo",
    "Unmaximize",
    "UnmaximizeFull",
    "MaximizeFull",
    "Maximize",
    "ToggleMaximize",
    "ToggleFullscreen",
    "ToggleDecorations",
    "ToggleShade",
    "ToggleOmnipresent",
    "ToggleAlwaysOnTop",
    "ToggleAlwaysOnBottom",
    "Iconify",
    "Close",
    "Raise",
    "Lower",
    "FocusToBottom",
    "BeginMove",
    "BeginResize",
}

SESSION_ACTIONS = {
    "Reconfigure",
    "Restart",
    "Exit",
}


def categorize(key: str, actions: list[Action]) -> Category:
    if key.startswith("XF86") or key.endswith("Print") or key == "Print":
        return Category.HARDWARE

    names = {a.name for a in actions}
    if names & SESSION_ACTIONS:
        return Category.SESSION
    if "ShowMenu" in names:
        return Category.MENUS
    if names & WINDOW_ACTIONS:
        return Category.WINDOW
    if "Execute" in names:
        # Session-ish notifies paired with Reconfigure already caught above
        cmd = ""
        for a in actions:
            if a.name == "Execute":
                cmd = (a.params.get("command") or a.params.get("execute") or "").lower()
                break
        if any(x in cmd for x in ("lock", "xkill", "ob-screenshot", "ob-brightness", "ob-volume")):
            if "ob-screenshot" in cmd or "ob-brightness" in cmd or "ob-volume" in cmd:
                return Category.HARDWARE
        return Category.APPS
    return Category.OTHER


def assign_category(kb: Keybind) -> Keybind:
    kb.category = categorize(kb.key, kb.actions)
    return kb
