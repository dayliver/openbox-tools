from __future__ import annotations

import argparse
import sys

from ob_windows import __version__
from ob_windows.layout.actions import capture_current_workspace, restore_preset
from ob_windows.layout.rofi_ui import ask_name, dmenu
from ob_windows.layout.store import delete_preset, list_presets, load_preset, save_preset
from ob_windows.layout.windows import notify


def cmd_save(name: str | None) -> int:
    if not name:
        name = ask_name("Save layout as")
    if not name:
        return 1
    try:
        data = capture_current_workspace()
        path = save_preset(name, data)
    except Exception as e:
        notify(str(e), urgent=True)
        print(e, file=sys.stderr)
        return 1
    n = len(data["windows"])
    desk = int(data["desktop"]) + 1
    notify(f"saved “{name}” ({n} windows, workspace {desk})")
    print(path)
    return 0


def cmd_load(name: str | None) -> int:
    if not name:
        names = list_presets()
        if not names:
            notify("no presets yet — Save current first", urgent=True)
            return 1
        name = dmenu("Load layout", names)
    if not name:
        return 1
    try:
        data = load_preset(name)
        placed, failed = restore_preset(data)
    except Exception as e:
        notify(str(e), urgent=True)
        print(e, file=sys.stderr)
        return 1
    msg = f"loaded “{name}” ({placed} placed"
    if failed:
        msg += f", {failed} failed"
    msg += ")"
    notify(msg, urgent=bool(failed))
    return 0 if not failed else 2


def cmd_delete(name: str | None, *, yes: bool = False) -> int:
    if not name:
        names = list_presets()
        if not names:
            notify("no presets")
            return 1
        name = dmenu("Delete layout", names)
    if not name:
        return 1
    if not yes:
        confirm = dmenu(f"Delete “{name}”?", ["No", "Yes"])
        if confirm != "Yes":
            return 1
    try:
        delete_preset(name)
    except Exception as e:
        notify(str(e), urgent=True)
        return 1
    notify(f"deleted “{name}”")
    return 0


def cmd_list() -> int:
    for n in list_presets():
        print(n)
    return 0


def cmd_menu() -> int:
    choice = dmenu(
        "Layout",
        [
            "Load",
            "Save current workspace",
            "Delete",
        ],
    )
    if choice == "Load":
        return cmd_load(None)
    if choice == "Save current workspace":
        return cmd_save(None)
    if choice == "Delete":
        return cmd_delete(None)
    return 1


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="ob-layout", description="Openbox workspace layout presets")
    p.add_argument("--version", action="version", version=f"ob-layout {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("save", help="Save current workspace layout")
    s.add_argument("name", nargs="?", help="Preset name")

    l = sub.add_parser("load", help="Load a preset")
    l.add_argument("name", nargs="?", help="Preset name")

    d = sub.add_parser("delete", help="Delete a preset")
    d.add_argument("name", nargs="?", help="Preset name")
    d.add_argument("-y", "--yes", action="store_true", help="Skip confirm")

    sub.add_parser("list", help="List preset names")
    sub.add_parser("menu", help="Rofi menu (Load / Save / Delete)")

    args = p.parse_args(argv)
    if args.cmd == "save":
        return cmd_save(args.name)
    if args.cmd == "load":
        return cmd_load(args.name)
    if args.cmd == "delete":
        return cmd_delete(args.name, yes=args.yes)
    if args.cmd == "list":
        return cmd_list()
    if args.cmd == "menu":
        return cmd_menu()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
