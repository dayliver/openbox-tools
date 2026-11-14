# ob-layout

Save / restore Openbox workspace layouts as **workarea-relative ratios**
(so style/margin changes still make sense).

## Install

```bash
~/Projects/openbox-tools/ob-layout/install.sh
```

## Usage

| | |
|--|--|
| `Super+O` | Rofi menu — Load / Save / Delete |
| `ob-layout menu` | same |
| `ob-layout save coding` | save current workspace as `coding` |
| `ob-layout load coding` | restore |
| `ob-layout list` | list names |
| `ob-layout delete coding` | delete |

Presets: `~/.config/ob-layout/presets/*.json`
