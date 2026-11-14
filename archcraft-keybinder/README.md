# Archcraft Keybinder

Manage Openbox keyboard shortcuts on Archcraft (CachyOS).

## Setup

```bash
./install.sh              # → uv sync
./run.sh                  # → uv run keybinder  (Textual TUI)
./run.sh --help
```

Same as:

```bash
uv sync
uv run keybinder
uv run keybinder --help
```

### TUI keys

| Key | Action |
|-----|--------|
| `/` | Focus search |
| `Tab` | Toggle search ↔ table (category bar skipped) |
| `←` `→` | Switch category tabs |
| `enter` | Edit selected keybind · **in editor: save** |
| `esc` | Focus table · **in editor: cancel** |
| `r` | Reset selected key to Archcraft default |
| `R` | Reset **all** keys (confirm) |
| `d` | Delete selected key |
| `a` | Write `kbinds.txt` + `openbox --reconfigure` |
| `F5` | Reload from disk |
| `↓` | From search → table |
| `q` | Quit |

## CLI examples

```bash
./run.sh list
./run.sh list --category apps
./run.sh get W-Return
./run.sh diff
./run.sh reset --all --dry-run
./run.sh set W-Return --cmd kitty --apply
./run.sh reset --all -y --apply
```

Defaults come from `/etc/skel/.config/openbox/rc.xml` (Archcraft), with a bundled fallback under `src/keybinder/data/`.

See `PLAN.md` for architecture and roadmap.
