# Archcraft Keybinder

Manage Openbox keyboard shortcuts on Archcraft (CachyOS).

**편집 도구**다. 직접 띄울 때만 실행되고, 결과는 전부 `~/.config/openbox/`(`rc.xml`,
`kbinds.txt`, `backups/`)에 남는다. 이 폴더를 지워도 현재 단축키는 그대로 동작한다.
잃는 것은 편집·기본값 복원 수단과, `rofi-keybinds`가 읽는 `kbinds.txt`의 갱신뿐이다.

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
./run.sh reset --key W-Return
./run.sh set W-Return --cmd kitty --apply
./run.sh reset --all -y --apply
```

Defaults come from `/etc/skel/.config/openbox/rc.xml` (Archcraft), with a bundled fallback under `src/keybinder/data/`.

Tests: `uv run pytest -q`

See `PLAN.md` for the original design notes (written before implementation; the
`defaults/` folder it mentions is now only `src/keybinder/data/`).
