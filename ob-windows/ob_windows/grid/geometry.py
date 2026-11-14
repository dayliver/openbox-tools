from __future__ import annotations

from ob_windows.grid.config import Config
from ob_windows.rect import Rect

__all__ = [
    "Rect",
    "at_work_bottom",
    "at_work_top",
    "grow_edge",
    "move_window",
    "shrink_toward",
    "snap_size",
]


def span(fraction: float, work_size: int, gap: int) -> int:
    """Tile length for ratio `fraction`.

    Matches: fraction * work_size - gap/2  when fraction == 1/2 and gap is even,
    and generally (work_size - gap) * fraction for fraction < 1 so two complementary
    tiles leave exactly `gap` between them.
    """
    if fraction >= 1.0:
        return work_size
    return max(1, round((work_size - gap) * fraction))


def size_steps(fractions: tuple[float, ...], work_size: int, gap: int) -> list[int]:
    return sorted({span(f, work_size, gap) for f in fractions})


def leading_edge_lines(origin: int, work_size: int, gap: int, fractions: tuple[float, ...]) -> list[int]:
    """Where a left/top edge may sit (flush start, or after a tile + gap)."""
    lines = {origin}
    for f in fractions:
        if f >= 1.0:
            continue
        lines.add(origin + span(f, work_size, gap) + gap)
    return sorted(lines)


def trailing_edge_lines(origin: int, work_size: int, gap: int, fractions: tuple[float, ...]) -> list[int]:
    """Where a right/bottom edge may sit (end of a tile, or flush end)."""
    lines = {origin + work_size}
    for f in fractions:
        lines.add(origin + span(f, work_size, gap))
    return sorted(lines)


def next_value(current: int, candidates: list[int], direction: int, tol: int) -> int | None:
    if direction > 0:
        opts = [c for c in candidates if c > current + tol]
        return min(opts) if opts else None
    opts = [c for c in candidates if c < current - tol]
    return max(opts) if opts else None


def next_size(current: int, steps: list[int], grow: bool, tol: int) -> int | None:
    if grow:
        opts = [s for s in steps if s > current + tol]
        return min(opts) if opts else None
    opts = [s for s in steps if s < current - tol]
    return max(opts) if opts else None


def clamp_rect(rect: Rect, work: Rect) -> Rect:
    w = min(rect.w, work.w)
    h = min(rect.h, work.h)
    x = min(max(rect.x, work.x), work.x + work.w - w)
    y = min(max(rect.y, work.y), work.y + work.h - h)
    return Rect(x, y, w, h)


def move_origins(
    origin: int,
    work_size: int,
    size: int,
    gap: int,
    fractions: tuple[float, ...],
) -> list[int]:
    """Left/top positions a kept-size window may sit on.

    Every leading grid line the window still fits on, plus flush-end (right /
    bottom aligned). Move always steps one leading line at a time — never
    skips 1/4 → 1/2 just because width is a perfect half.
    """
    leads = leading_edge_lines(origin, work_size, gap, fractions)
    flush = origin + work_size - size
    return sorted({pos for pos in leads if origin <= pos <= flush} | {flush})


def move_keep_size(rect: Rect, work: Rect, cfg: Config, direction: str) -> Rect:
    """Keep size; snap the leading edge to the next grid line in `direction`."""
    if direction in ("left", "right"):
        origins = move_origins(
            work.x, work.w, rect.w, cfg.inner_gap, cfg.horizontal
        )
        delta = 1 if direction == "right" else -1
        nxt = next_value(rect.x, origins, delta, cfg.tolerance_px)
        if nxt is None:
            return rect
        return clamp_rect(Rect(nxt, rect.y, rect.w, rect.h), work)

    origins = move_origins(work.y, work.h, rect.h, cfg.inner_gap, cfg.vertical)
    delta = 1 if direction == "down" else -1
    nxt = next_value(rect.y, origins, delta, cfg.tolerance_px)
    if nxt is None:
        return rect
    return clamp_rect(Rect(rect.x, nxt, rect.w, rect.h), work)


def move_shrink_to_fit(rect: Rect, work: Rect, cfg: Config, direction: str) -> Rect:
    """Slide the near edge one grid step; shrink so the far edge stays flush.

    Only `right` / `down` (into the workarea). Used when the window is too large
    to keep its size at the next origin — e.g. maximized + Super+Right ⇒ left at
    the ~25% lead, width ~75% to the workarea's right edge.
    """
    if direction == "right":
        leads = leading_edge_lines(work.x, work.w, cfg.inner_gap, cfg.horizontal)
        nxt = next_value(rect.x, leads, 1, cfg.tolerance_px)
        if nxt is None or nxt >= work.x + work.w:
            return rect
        return clamp_rect(Rect(nxt, rect.y, work.x + work.w - nxt, rect.h), work)

    if direction == "down":
        leads = leading_edge_lines(work.y, work.h, cfg.inner_gap, cfg.vertical)
        nxt = next_value(rect.y, leads, 1, cfg.tolerance_px)
        if nxt is None or nxt >= work.y + work.h:
            return rect
        return clamp_rect(Rect(rect.x, nxt, rect.w, work.y + work.h - nxt), work)

    return rect


def move_window(rect: Rect, work: Rect, cfg: Config, direction: str) -> Rect:
    """Move one grid step: keep size when possible, otherwise shrink to still fit."""
    kept = move_keep_size(rect, work, cfg, direction)
    if kept != rect:
        return kept
    return move_shrink_to_fit(rect, work, cfg, direction)


def grow_edge(rect: Rect, work: Rect, cfg: Config, direction: str) -> Rect:
    """Extend the named edge outward.

    Right/bottom edges only snap to *trailing* lines; left/top to *leading* lines.
    That keeps the inner gap: a left-hand 1/2 tile ends at span(1/2), and the
    right-hand tile starts at span(1/2)+gap — never on the same line.
    """
    if direction == "right":
        lines = trailing_edge_lines(work.x, work.w, cfg.inner_gap, cfg.horizontal)
        nxt = next_value(rect.x2, lines, 1, cfg.tolerance_px)
        if nxt is None:
            return rect
        return clamp_rect(Rect(rect.x, rect.y, nxt - rect.x, rect.h), work)

    if direction == "left":
        lines = leading_edge_lines(work.x, work.w, cfg.inner_gap, cfg.horizontal)
        nxt = next_value(rect.x, lines, -1, cfg.tolerance_px)
        if nxt is None:
            return rect
        return clamp_rect(Rect(nxt, rect.y, rect.x2 - nxt, rect.h), work)

    if direction == "down":
        lines = trailing_edge_lines(work.y, work.h, cfg.inner_gap, cfg.vertical)
        nxt = next_value(rect.y2, lines, 1, cfg.tolerance_px)
        if nxt is None:
            return rect
        return clamp_rect(Rect(rect.x, rect.y, rect.w, nxt - rect.y), work)

    lines = leading_edge_lines(work.y, work.h, cfg.inner_gap, cfg.vertical)
    nxt = next_value(rect.y, lines, -1, cfg.tolerance_px)
    if nxt is None:
        return rect
    return clamp_rect(Rect(rect.x, nxt, rect.w, rect.y2 - nxt), work)


def shrink_toward(rect: Rect, work: Rect, cfg: Config, direction: str) -> Rect:
    """Shrink toward `direction` (left ⇒ right edge moves left onto next trailing line)."""
    if direction == "left":
        lines = trailing_edge_lines(work.x, work.w, cfg.inner_gap, cfg.horizontal)
        nxt = next_value(rect.x2, lines, -1, cfg.tolerance_px)
        if nxt is None or nxt <= rect.x:
            return rect
        return clamp_rect(Rect(rect.x, rect.y, nxt - rect.x, rect.h), work)

    if direction == "right":
        lines = leading_edge_lines(work.x, work.w, cfg.inner_gap, cfg.horizontal)
        nxt = next_value(rect.x, lines, 1, cfg.tolerance_px)
        if nxt is None or nxt >= rect.x2:
            return rect
        return clamp_rect(Rect(nxt, rect.y, rect.x2 - nxt, rect.h), work)

    if direction == "up":
        lines = trailing_edge_lines(work.y, work.h, cfg.inner_gap, cfg.vertical)
        nxt = next_value(rect.y2, lines, -1, cfg.tolerance_px)
        if nxt is None or nxt <= rect.y:
            return rect
        return clamp_rect(Rect(rect.x, rect.y, rect.w, nxt - rect.y), work)

    lines = leading_edge_lines(work.y, work.h, cfg.inner_gap, cfg.vertical)
    nxt = next_value(rect.y, lines, 1, cfg.tolerance_px)
    if nxt is None or nxt >= rect.y2:
        return rect
    return clamp_rect(Rect(rect.x, nxt, rect.w, rect.y2 - nxt), work)


def snap_size(rect: Rect, work: Rect, cfg: Config, axis: str, grow: bool) -> Rect:
    """Change width/height to the next ratio step; keep top-left fixed."""
    if axis == "width":
        steps = size_steps(cfg.horizontal, work.w, cfg.inner_gap)
        nxt = next_size(rect.w, steps, grow, cfg.tolerance_px)
        if nxt is None:
            return rect
        return clamp_rect(Rect(rect.x, rect.y, nxt, rect.h), work)
    steps = size_steps(cfg.vertical, work.h, cfg.inner_gap)
    nxt = next_size(rect.h, steps, grow, cfg.tolerance_px)
    if nxt is None:
        return rect
    return clamp_rect(Rect(rect.x, rect.y, rect.w, nxt), work)


def at_work_top(rect: Rect, work: Rect, tol: int) -> bool:
    return abs(rect.y - work.y) <= tol


def at_work_bottom(rect: Rect, work: Rect, tol: int) -> bool:
    return abs(rect.y2 - work.y2) <= tol
