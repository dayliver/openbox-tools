# Ratio-grid window move / resize for Openbox (Archcraft)

Keeps Archcraft outer margins by using the monitor **workarea** (`_NET_WORKAREA` /
Gdk workarea). Adds a configurable **inner gap** between tiled windows.

## Install

```bash
~/Projects/openbox-tools/ob-grid/install.sh
```

Config: `~/.config/ob-grid/config.toml` (created from `config.default.toml`).

## Commands

| Command | Effect |
|---------|--------|
| `ob-grid move left\|right\|up\|down` | Snap to next grid line (keep size; if too wide/tall, shrink to fit) |
| `ob-grid grow left\|right\|up\|down` | Extend that edge outward to next grid line |
| `ob-grid shrink left\|right\|up\|down` | Pull that edge inward to next grid line |
| `ob-grid size width\|height larger\|smaller` | Step size to next ratio (top-left fixed) |
| `ob-grid info` | Debug current window / workarea / config |

## Default Openbox binds (after install wiring)

| Key | Action |
|-----|--------|
| `Super+Arrows` | `move` (keep size, or shrink to fit) |
| `Super+Down` on a tall/full window | lower top edge; shrink height to fit |
| `Super+Up` at workarea top (no move left) | maximize |
| `Super+Down` at workarea bottom (no move left) | minimize |
| `Super+Ctrl+Right/Down` | `grow` right/down (top-left anchored) |
| `Super+Ctrl+Left/Up` | `shrink` left/up (top-left anchored) |

`Super+Shift+Arrows` and `Super+Ctrl+Shift+Arrows` are unbound.

## Tests

```bash
cd ~/Projects/openbox-tools/ob-grid
PYTHONPATH=. python3 -m pytest -q
```
