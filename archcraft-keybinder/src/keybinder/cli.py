"""CLI entrypoint for Archcraft keybinder."""

from __future__ import annotations

import argparse
import json
import sys

from keybinder import __version__
from keybinder.apply import apply_changes
from keybinder.conflicts import find_conflicts
from keybinder.defaults import (
    DefaultsError,
    diff_keybinds,
    load_current,
    reset_all,
    reset_one,
    stock_keyboard_xml,
)
from keybinder.models import Category, Keybind
from keybinder.mutate import remove_key, set_execute
from keybinder.paths import RC_XML


def _print_table(binds: list[Keybind]) -> None:
    if not binds:
        print("(no keybinds)")
        return
    key_w = max(len(b.key) for b in binds)
    cat_w = max(len(b.category.value) for b in binds)
    ori_w = max(len(b.origin.value) for b in binds)
    for b in binds:
        print(
            f"{b.key:<{key_w}}  {b.category.value:<{cat_w}}  {b.origin.value:<{ori_w}}  {b.summary()}"
        )


def _filter_binds(
    binds: list[Keybind],
    *,
    category: str | None,
    search: str | None,
    modified_only: bool,
) -> list[Keybind]:
    out = binds
    if category:
        out = [b for b in out if b.category.value == category]
    if search:
        q = search.lower()
        out = [
            b
            for b in out
            if q in b.key.lower() or q in b.summary().lower()
        ]
    if modified_only:
        out = [b for b in out if b.origin.value != "stock"]
    return out


def cmd_list(args: argparse.Namespace) -> int:
    binds = load_current(RC_XML if not args.rc else args.rc)
    binds = _filter_binds(
        binds,
        category=args.category,
        search=args.search,
        modified_only=args.modified,
    )
    if args.json:
        print(json.dumps([b.to_dict() for b in binds], indent=2, ensure_ascii=False))
    else:
        _print_table(binds)
        print(f"\n{len(binds)} keybind(s)", file=sys.stderr)
    return 0


def cmd_get(args: argparse.Namespace) -> int:
    from keybinder.defaults import annotate_origins, stock_keybinds
    from keybinder.parse import parse_rc

    path = args.rc or RC_XML
    binds = annotate_origins(parse_rc(path), stock_keybinds())
    matched = [b for b in binds if b.key == args.key]
    if not matched:
        print(f"Keybind not found: {args.key}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps([b.to_dict() for b in matched], indent=2, ensure_ascii=False))
    else:
        _print_table(matched)
    return 0


def cmd_diff(args: argparse.Namespace) -> int:
    path = args.rc or RC_XML
    from keybinder.parse import parse_rc

    result = diff_keybinds(parse_rc(path))
    if args.json:
        print(
            json.dumps(
                {k: [b.to_dict() for b in v] for k, v in result.items()},
                indent=2,
                ensure_ascii=False,
            )
        )
        return 0
    for label in ("modified", "custom", "missing"):
        items = result[label]
        print(f"== {label} ({len(items)}) ==")
        _print_table(items)
        print()
    return 0


def cmd_conflicts(args: argparse.Namespace) -> int:
    binds = load_current(args.rc or RC_XML)
    conflicts = find_conflicts(binds, args.key)
    if args.json:
        print(
            json.dumps(
                {k: [b.to_dict() for b in v] for k, v in conflicts.items()},
                indent=2,
                ensure_ascii=False,
            )
        )
    elif not conflicts:
        print("No conflicts")
    else:
        for key, items in conflicts.items():
            print(f"{key}: {len(items)} bindings")
            _print_table(items)
    return 1 if conflicts else 0


def cmd_set(args: argparse.Namespace) -> int:
    info = set_execute(args.key, args.cmd, path=args.rc or RC_XML)
    print(f"Set {info['key']} -> {info['command']}")
    if info.get("backup"):
        print(f"Backup: {info['backup']}")
    if args.apply:
        applied = apply_changes()
        print(f"Reconfigure: exit {applied['reconfigure_returncode']}")
    return 0


def cmd_rm(args: argparse.Namespace) -> int:
    try:
        info = remove_key(args.key, path=args.rc or RC_XML)
    except KeyError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"Removed {info['key']} ({info['removed']} entries)")
    if info.get("backup"):
        print(f"Backup: {info['backup']}")
    if args.apply:
        applied = apply_changes()
        print(f"Reconfigure: exit {applied['reconfigure_returncode']}")
    return 0


def cmd_reset(args: argparse.Namespace) -> int:
    path = args.rc or RC_XML
    try:
        if args.all:
            if not args.yes and not args.dry_run:
                print(
                    "This will replace the entire <keyboard> section with Archcraft defaults.",
                    file=sys.stderr,
                )
                confirm = input("Type 'yes' to continue: ").strip()
                if confirm != "yes":
                    print("Aborted")
                    return 1
            info = reset_all(path=path, dry_run=args.dry_run)
        elif args.key:
            info = reset_one(
                args.key,
                path=path,
                dry_run=args.dry_run,
                remove_custom=args.remove_custom,
            )
        else:
            print("Specify --all or --key KEY", file=sys.stderr)
            return 2
    except (DefaultsError, KeyError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(json.dumps(info, indent=2) if args.json else info)
    if not args.dry_run and args.apply:
        applied = apply_changes()
        print(f"Reconfigure: exit {applied['reconfigure_returncode']}")
    return 0


def cmd_apply(args: argparse.Namespace) -> int:
    info = apply_changes()
    print(json.dumps(info, indent=2) if args.json else info)
    return 0 if info["reconfigure_returncode"] == 0 else 1


def cmd_stock_source(_: argparse.Namespace) -> int:
    xml, source = stock_keyboard_xml()
    print(f"source: {source}")
    print(f"keybinds: {xml.count('<keybind')}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="keybinder",
        description="Manage Archcraft Openbox keyboard shortcuts",
    )
    parser.add_argument("--version", action="version", version=f"keybinder {__version__}")
    parser.add_argument(
        "--rc",
        type=str,
        default=None,
        help="Path to rc.xml (default: ~/.config/openbox/rc.xml)",
    )

    sub = parser.add_subparsers(dest="command")

    p_list = sub.add_parser("list", help="List keybinds")
    p_list.add_argument("--category", choices=[c.value for c in Category])
    p_list.add_argument("--search", "-s")
    p_list.add_argument("--modified", action="store_true", help="Hide stock-identical binds")
    p_list.add_argument("--json", action="store_true")
    p_list.set_defaults(func=cmd_list)

    p_get = sub.add_parser("get", help="Show one keybind")
    p_get.add_argument("key")
    p_get.add_argument("--json", action="store_true")
    p_get.set_defaults(func=cmd_get)

    p_diff = sub.add_parser("diff", help="Diff against Archcraft defaults")
    p_diff.add_argument("--json", action="store_true")
    p_diff.set_defaults(func=cmd_diff)

    p_conf = sub.add_parser("conflicts", help="Find duplicate keys")
    p_conf.add_argument("key", nargs="?")
    p_conf.add_argument("--json", action="store_true")
    p_conf.set_defaults(func=cmd_conflicts)

    p_set = sub.add_parser("set", help="Set an Execute keybind")
    p_set.add_argument("key")
    p_set.add_argument("--cmd", required=True, help="Command to run")
    p_set.add_argument("--apply", action="store_true", help="Reconfigure Openbox after write")
    p_set.set_defaults(func=cmd_set)

    p_rm = sub.add_parser("rm", help="Remove a keybind")
    p_rm.add_argument("key")
    p_rm.add_argument("--apply", action="store_true")
    p_rm.set_defaults(func=cmd_rm)

    p_reset = sub.add_parser("reset", help="Restore Archcraft default keybinds")
    g = p_reset.add_mutually_exclusive_group(required=True)
    g.add_argument("--all", action="store_true", help="Replace entire <keyboard> section")
    g.add_argument("--key", help="Restore a single key")
    p_reset.add_argument("--remove-custom", action="store_true", help="Delete custom key on --key reset")
    p_reset.add_argument("--dry-run", action="store_true")
    p_reset.add_argument("--yes", "-y", action="store_true", help="Skip confirmation for --all")
    p_reset.add_argument("--apply", action="store_true")
    p_reset.add_argument("--json", action="store_true")
    p_reset.set_defaults(func=cmd_reset)

    p_apply = sub.add_parser("apply", help="Rewrite kbinds.txt and openbox --reconfigure")
    p_apply.add_argument("--json", action="store_true")
    p_apply.set_defaults(func=cmd_apply)

    p_stock = sub.add_parser("stock-source", help="Show where defaults are loaded from")
    p_stock.set_defaults(func=cmd_stock_source)

    p_tui = sub.add_parser("tui", help="Open the terminal UI (default)")
    p_tui.set_defaults(func=cmd_tui)

    return parser


def cmd_tui(args: argparse.Namespace) -> int:
    from keybinder.tui import run_tui

    return run_tui(rc_path=args.rc)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    # Normalize --rc on namespace used by commands
    if getattr(args, "rc", None):
        from pathlib import Path

        args.rc = Path(args.rc)
    else:
        args.rc = None
    if not getattr(args, "command", None):
        return cmd_tui(args)
    try:
        return args.func(args)
    except BrokenPipeError:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
