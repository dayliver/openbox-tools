# openbox-tools

Archcraft(CachyOS) Openbox 환경용 개인 도구 모음.

| 폴더 | 내용 | 설치 |
|---|---|---|
| `ob-grid/` | 비율 격자 기반 창 이동·크기 조절 | `./ob-grid/install.sh` |
| `ob-layout/` | 워크스페이스 레이아웃 저장·복원 (Rofi 메뉴) | `./ob-layout/install.sh` |
| `archcraft-keybinder/` | Openbox 단축키 관리 TUI (uv) | `./archcraft-keybinder/install.sh` |

`ob-grid`, `ob-layout`의 install.sh는 `~/.local/bin`과 `~/.config/openbox/scripts`에
이 폴더를 가리키는 심볼릭 링크를 만든다. 폴더를 옮기면 install.sh를 다시 실행할 것.
