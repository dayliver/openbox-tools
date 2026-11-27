# openbox-tools

CachyOS에 Archcraft Openbox 구성을 얹고 단축키와 창 배치를 개인화하는 도구 모음.

[이 PC의 Archcraft 기본값 대비 변경과 다른 PC로 옮기는 절차](docs/desktop-profile.md)

| 폴더 | 내용 | 성격 | 지우면 |
|---|---|---|---|
| `ob-windows/` | `ob-grid`(비율 격자 창 이동·크기 조절), `ob-layout`(워크스페이스 레이아웃 저장·복원) | **상시 사용** — Openbox 단축키가 누를 때마다 실행 | `Super+방향키`, `Super+Ctrl+방향키`, `Super+O`가 즉시 먹통 |
| `archcraft-keybinder/` | `rc.xml` 단축키 조회·수정·기본값 복원 (TUI + CLI) | **편집 도구** — 직접 띄울 때만 실행 | 현재 단축키는 그대로 동작. 편집·복원 수단과 `kbinds.txt` 갱신만 사라짐 |
| `shell/` | zsh 프롬프트 (Oh My Zsh `archcraft` 테마에 시각 추가)와 설치 스크립트 | **복사본** — 설치 시 `~/.oh-my-zsh/custom/themes/`로 복사 | 설치된 프롬프트는 그대로. 다른 PC로 옮길 원본만 사라짐 |

상주 프로세스는 없고 `autostart`에서 호출되는 것도 없다.

## 설치

```bash
./ob-windows/install.sh            # ~/.local/bin, ~/.config/openbox/scripts 에 심볼릭 링크
./archcraft-keybinder/install.sh   # uv sync
./shell/install.sh                 # zsh 프롬프트 테마 복사 (선택)
```

`ob-windows`의 링크는 이 폴더를 가리킨다. 폴더를 옮기면 `install.sh`를 다시 실행할 것.

## 런타임이 다른 이유

- `ob-windows`는 **시스템 `python3`** + pacman의 `python-xlib`만 쓴다. pip 의존성 없음.
  키 한 번에 약 0.1초 (Gtk/Wnck를 쓰던 때는 약 0.5초).
- `archcraft-keybinder`는 **`uv` venv**에 `textual`, `lxml`을 쓴다.

키 입력마다 실행되는 쪽이 무거운 의존성에 묶이지 않도록 일부러 분리해 두었다.

## 서로 닿는 지점

- `ob-grid`/`ob-layout`의 단축키는 `rc.xml`에 손으로 등록돼 있다 (`ob-windows/README.md`의 표 참고).
  keybinder로 넣으려면: `keybinder set W-Left --cmd "ob-grid move left" --apply`
- `~/.config/openbox/scripts/rofi-keybinds`는 `kbinds.txt`를 읽는데, 이 파일은 `keybinder apply`가 만든다.
