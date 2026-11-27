# ob-windows — ob-grid + ob-layout

Openbox 창 도구 두 개를 담은 패키지. **상시 사용 코드**다: Openbox 단축키가 누를 때마다
`ob-grid` / `ob-layout`을 실행한다. 이 폴더를 지우거나 옮기면 아래 단축키가 바로 죽는다
(옮겼으면 `./install.sh` 재실행).

```bash
./install.sh
```

요구 사항: 시스템 `python3`, `python-xlib`, 그리고 ob-layout용 `rofi`, `dunst`(알림).
EWMH를 지원하는 창 관리자(Openbox)의 X11 세션에서만 동작한다.

## ob-grid — 비율 격자 창 이동·크기 조절

모니터 **workarea**(Archcraft 바깥 여백이 이미 빠진 영역)를 비율로 나누고, 나란한 두 창
사이에 **안쪽 간격**이 남도록 창을 격자선에 맞춘다.

| 명령 | 동작 |
|---|---|
| `ob-grid move left\|right\|up\|down` | 크기를 유지한 채 다음 격자선으로. 너무 크면(오른쪽·아래 방향) 반대쪽 변을 화면 끝에 붙인 채 줄여서 맞춤 |
| `ob-grid grow left\|right\|up\|down` | 그 방향의 변을 다음 격자선까지 바깥으로 확장 |
| `ob-grid shrink left\|right\|up\|down` | 그 방향으로 줄임 (`left` ⇒ 오른쪽 변이 왼쪽으로) |
| `ob-grid size width\|height larger\|smaller` | 좌상단을 고정하고 크기를 다음 비율 단계로 |
| `ob-grid info` | 현재 창 / workarea / 설정 출력 (디버그) |

`rc.xml`에 등록된 단축키:

| 키 | 명령 | 비고 |
|---|---|---|
| `Super+←/→/↑/↓` | `move` | 더 갈 격자선이 없을 때 `↑`는 최대화, `↓`는 최소화 |
| `Super+Ctrl+→/↓` | `grow right/down` | 좌상단 고정 |
| `Super+Ctrl+←/↑` | `shrink left/up` | 좌상단 고정 |

`size`, `grow left/up`, `shrink right/down`은 구현돼 있지만 단축키가 없다.

설정: `~/.config/ob-grid/config.toml` (없으면 `config.default.toml`에서 복사). 매 실행마다 읽으므로
고치면 다음 키 입력부터 반영된다.

## ob-layout — 워크스페이스 레이아웃 저장·복원

현재 워크스페이스의 창 배치를 **workarea 대비 비율**로 저장한다. 여백이나 해상도가 바뀌어도 의미가 유지된다.

| | |
|---|---|
| `Super+O` / `ob-layout menu` | Rofi 메뉴 — Load / Save / Delete |
| `ob-layout save [이름]` | 현재 워크스페이스 저장 (이름 생략 시 Rofi로 물음) |
| `ob-layout load [이름]` | 복원 |
| `ob-layout list` | 이름 목록 |
| `ob-layout delete [이름] [-y]` | 삭제 |

- 저장: 창마다 클래스, 제목, 실행 명령, 비율 좌표, (터미널이면) 셸의 작업 디렉터리.
  화면의 95% 이상을 덮으면 최대화로 기록.
- 복원: 같은 클래스의 열린 창을 재사용, 없으면 실행해서 최대 10초 대기. cwd가 저장된
  터미널은 같은 cwd의 창만 재사용하고 아니면 그 디렉터리에서 새로 띄운다.
- 프리셋: `~/.config/ob-layout/presets/*.json`

알려진 한계:

- 저장은 창이 있는 모니터 기준, 복원은 **주 모니터** 기준이다 (멀티모니터에서 어긋남).
- `alacritty_fullscreen`의 cwd 포함 실행 명령은 `ob-furminal` 내용을 `layout/launch.py`에
  복사해 둔 것이라, 그 스크립트를 고치면 여기도 고쳐야 한다.
- `kitty_fullscreen`은 `ob-furminal --working-directory <경로>`로 복원한다. Kitty용
  `ob-furminal` 래퍼는 받은 인수를 Kitty에 전달해야 한다.

## 구조

```text
ob_windows/
  rect.py            Rect (순수)
  wm.py              X 서버와 닿는 유일한 모듈 — python-xlib + EWMH: 활성 창, workarea, 프레임 적용,
                     최대화/최소화, 워크스페이스
  grid/              cli, geometry(순수), config(순수)
  layout/            cli, actions, windows(창 열거·워크스페이스·cwd), ratio(순수), store(순수), launch(순수), rofi_ui
bin/ob-grid, bin/ob-layout   시스템 python3로 위 모듈을 실행하는 래퍼
```

## 테스트

순수 모듈만 테스트한다. `wm.py`는 실제 X 세션이 필요해서 손으로 확인한다
(`ob-grid info`로 창·workarea 값을 볼 수 있다).

```bash
PYTHONPATH=. uvx pytest -q
```
