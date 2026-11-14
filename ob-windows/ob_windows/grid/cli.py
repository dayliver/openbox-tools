from __future__ import annotations

import argparse
import sys

from ob_windows import __version__
from ob_windows.grid.config import USER_CONFIG, ensure_user_config, load_config
from ob_windows.grid.geometry import (
    at_work_bottom,
    at_work_top,
    grow_edge,
    move_window,
    shrink_toward,
    snap_size,
)

DIRS = ("left", "right", "up", "down")


def _run_transform(transform) -> int:
    from ob_windows import wm  # lazy: --help / --version need no X connection

    ensure_user_config()
    cfg = load_config()
    active = wm.active_window()
    new_rect = transform(active.rect, active.work, cfg)
    if new_rect == active.rect:
        return 0
    wm.apply_frame(active.xid, new_rect)
    return 0


def cmd_move(args: argparse.Namespace) -> int:
    from ob_windows import wm

    ensure_user_config()
    cfg = load_config()
    active = wm.active_window()

    # Prefer a real move (incl. shrink-to-fit) before edge actions. Otherwise a
    # maximized window is flush with the bottom and Super+Down would minimize
    # instead of dropping the top edge to ~1/3 with height ~2/3.
    new_rect = move_window(active.rect, active.work, cfg, args.direction)
    if new_rect != active.rect:
        wm.apply_frame(active.xid, new_rect)
        return 0

    if args.direction == "up" and at_work_top(active.rect, active.work, cfg.tolerance_px):
        wm.maximize(active.xid)
        return 0
    if args.direction == "down" and at_work_bottom(active.rect, active.work, cfg.tolerance_px):
        wm.minimize(active.xid)
        return 0
    return 0


def cmd_grow(args: argparse.Namespace) -> int:
    return _run_transform(lambda r, w, c: grow_edge(r, w, c, args.direction))


def cmd_shrink(args: argparse.Namespace) -> int:
    return _run_transform(lambda r, w, c: shrink_toward(r, w, c, args.direction))


def cmd_size(args: argparse.Namespace) -> int:
    grow = args.which == "larger"
    return _run_transform(lambda r, w, c: snap_size(r, w, c, args.axis, grow))


def cmd_info(_: argparse.Namespace) -> int:
    from ob_windows import wm

    ensure_user_config()
    cfg = load_config()
    active = wm.active_window()
    print(f"config: {USER_CONFIG}")
    print(f"horizontal: {cfg.horizontal}")
    print(f"vertical:   {cfg.vertical}")
    print(f"inner_gap:  {cfg.inner_gap}")
    print(f"workarea:   {active.work}")
    print(f"window:     {active.rect}  ({active.name})")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ob-grid",
        description="Snap Openbox windows to a configurable ratio grid (keeps Archcraft workarea margins).",
    )
    p.add_argument("--version", action="version", version=f"ob-grid {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    m = sub.add_parser(
        "move",
        help="Move window to next grid line (keep size, or shrink to fit if needed)",
    )
    m.add_argument("direction", choices=DIRS)
    m.set_defaults(func=cmd_move)

    g = sub.add_parser("grow", help="Extend the named edge outward to the next grid line")
    g.add_argument("direction", choices=DIRS)
    g.set_defaults(func=cmd_grow)

    s = sub.add_parser(
        "shrink",
        help="Shrink toward direction (left ⇒ right edge moves left onto next grid line)",
    )
    s.add_argument("direction", choices=DIRS)
    s.set_defaults(func=cmd_shrink)

    z = sub.add_parser("size", help="Step width/height to next ratio (top-left fixed)")
    z.add_argument("axis", choices=("width", "height"))
    z.add_argument("which", choices=("larger", "smaller"))
    z.set_defaults(func=cmd_size)

    i = sub.add_parser("info", help="Show active window + workarea + config")
    i.set_defaults(func=cmd_info)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except Exception as exc:  # noqa: BLE001 — CLI boundary
        print(f"ob-grid: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
