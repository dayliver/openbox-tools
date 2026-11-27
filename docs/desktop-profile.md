# CachyOS에 Archcraft Openbox를 얹은 데스크톱 구성

## 비교 기준

2026-11-25에 이 PC의 패키지 DB, `/etc`와 사용자 X11·Openbox 설정, 로컬 변경 기록을 읽어 작성했다. CachyOS 위에 Openbox 3.6.1과 `archcraft-openbox-premium 7.0-9`, `archcraft-openbox-themes`, `archcraft-skeleton`, Archcraft 배경·폰트·GTK·아이콘 패키지가 설치돼 있다. 디스플레이 매니저는 SDDM이고 `Openbox` X11 세션은 `/usr/bin/openbox-session`으로 시작된다. pacman에는 CachyOS/Arch 저장소와 `[archcraft]` 항목이 있다.

단축키 기준값은 Premium 패키지가 소유한 `/etc/skel/.config/openbox/rc.xml`이다. pacman 캐시의 일반 `archcraft-openbox 7.0-9` 패키지에서 추출한 같은 파일과 바이트 단위로 일치했고, 이 저장소에 번들된 키바인더의 기본 단축키 108개도 XML 동작 기준으로 모두 일치했다. 따라서 아래 단축키 차이는 두 에디션에 공통으로 적용된다. 시작 스크립트는 일반판에 환영 앱의 첫 실행 블록이 추가되어 있고, 테마 목록은 에디션마다 다르다. 테마와 세션 시작 스크립트 비교에는 설치된 Premium의 `/etc/skel`을 사용했다. 데스크톱 세션의 실제 실행 상태와 다른 PC에서의 적용은 확인하지 않았다. [Archcraft Openbox 공식 문서](https://wiki.archcraft.io/docs/window-managers/stacking-wm/openbox/)

## 단축키

현재 `~/.config/openbox/rc.xml`에는 최상위 키바인딩 110개가 있다. 기본값 대비 19개 추가, 17개 제거, 16개 동작 변경이다. 표는 이 차이를 묶어 정리했다. XML에서 `W`는 Super, `C`는 Ctrl, `A`는 Alt, `S`는 Shift다.

| 키 | 기본 동작 → 현재 동작 |
|---|---|
| Super+Enter | Alacritty → `ob-furminal`로 전체화면 Kitty |
| Alt+Enter | 새 바인딩 → `ob-furminal` |
| Super+T | `ob-furminal` → 일반 Kitty |
| Ctrl+Alt+T | Xfce Terminal → 일반 Kitty |
| Ctrl+Alt+V / H | Alacritty에서 Vim / htop → `kitty -e vim` / `kitty -e htop` |
| Alt+F1 → Super+A | Rofi 앱 런처를 옮김. `rofi-launcher`에서 Escape 또는 Super+A로 닫기 |
| Super+K | 창을 우상단에 배치 → `rofi-keybinds`로 단축키 검색 |
| Super+O | 새 바인딩 → `ob-layout menu`로 창 배치 저장·복원 |
| Super+← / → / ↑ / ↓ | 좌우 50%, 최대화, 중앙 복원 → `ob-grid move left/right/up/down`. 격자 끝에서 위는 최대화, 아래는 최소화 |
| Super+Ctrl+→ / ↓ | 20px씩 확대 → `ob-grid grow right/down` |
| Super+Ctrl+← / ↑ | 20px씩 축소 → `ob-grid shrink left/up` |
| Ctrl+Alt+← / → | 이전·다음 워크스페이스로 이동 → `DirectionalFocusWest/East` |
| Ctrl+Alt+↑ / ↓ | 새 바인딩 → `DirectionalFocusNorth/South` |
| Super+1…5 → Super+F1…F5 | `GoToDesktop`의 `<to>1…5</to>`. 숫자 키 바인딩 제거 |
| Super+Shift+1…5 → Super+Shift+F1…F5 | `SendToDesktop`의 `<desktop>1…5</desktop>`. 숫자 키 바인딩 제거 |
| Ctrl+Shift+R → Super+Ctrl+R | `dunstify` 알림을 띄운 뒤 `Reconfigure`. 브라우저의 Ctrl+Shift+R을 돌려줌 |
| Super+Shift+R | 새 바인딩 → `rofi-rustdesk` |
| Super+Shift+C | 새 바인딩 → `ob-change-colors` |
| Super+Shift+P | 새 바인딩 → `power-profile-cycle` |
| Super+Shift+← / → | 창을 이전·다음 워크스페이스로 보내고 따라가기 제거 |
| Super+Shift+↑ / ↓ | 창을 상·하단 절반에 붙이기 제거 |
| Ctrl+Alt+R | Alacritty에서 Ranger 실행 제거 |

Alt+Shift 및 기타 단축키를 포함한 전체 목록은 대상 PC에서 `./archcraft-keybinder/run.sh list`로 볼 수 있다. `ob-workspace-nav`라는 별도 탐색 스크립트는 로컬에 있지만 현재 `rc.xml` 및 시작 스크립트에서 이를 호출하는 구성은 확인되지 않았다.

## 터미널과 기본 앱

- 일반 터미널은 **Kitty**다. Yazi 등에서 이미지 미리보기를 쓰고 한글을 입력하기 위해 Alacritty에서 Kitty로 전환했다. Openbox 메뉴 4종의 Terminal Emulator 명령은 `alacritty`에서 `kitty`로 변경됐다. 현재 Openbox 메뉴는 `menu-icons.xml`이다. Polybar의 일부 프로세스 모니터 클릭 동작도 Kitty를 호출한다.
- 전체화면 터미널은 `~/.config/openbox/scripts/ob-furminal`이다. 기본 Alacritty 래퍼를 아래 명령으로 바꿨다. Kitty의 `kitty_fullscreen` 클래스, 패딩 45, 불투명도 1.0, 글꼴 크기 14, 로그인 zsh를 사용한다. 전체화면이 Polybar를 가린다.
- `~/.config/xfce4/helpers.rc`는 `TerminalEmulator=kitty`, `FileManager=Thunar`다. Thunar의 `Ctrl+.`와 **Open Terminal Here**는 `~/.config/Thunar/uca.xml`에서 `exo-open --working-directory %f --launch TerminalEmulator`를 실행한다. 따라서 현재 폴더에서 Kitty가 열린다. 다른 Thunar 메뉴 중 일부는 이 PC에 없다고 기록된 `archcraft-tcma`를 여전히 참조한다.
- 사용자 MIME 기본값은 HTTP/HTTPS에 Chrome, 디렉터리에 Thunar, ZIP에 Xarchiver, JPEG/PNG/SVG에 feh다. 로컬 기본값의 SVG는 Viewnior였다. 연결은 대상 PC에 설치된 앱의 desktop ID로 적용한다.
- 셸은 zsh이고 `~/.zshrc`는 Oh My Zsh의 `archcraft` 테마를 사용한다. 프롬프트 맨 앞에 시각을 추가한 테마 파일과 설치 스크립트는 [`shell/`](../shell/README.md)에 있다. Kitty 폰트는 `JetBrainsMono Nerd Font`이고 색상은 테마 적용 시 바뀐다. Alacritty도 설치돼 있고 색상 파일이 남아 있다.

```bash
#!/usr/bin/env bash
exec kitty --class kitty_fullscreen --start-as=fullscreen \
    -o window_padding_width=45 -o background_opacity=1.0 -o font_size=14 \
    /bin/zsh -l
```

`ob-layout`에는 일반 `kitty`의 작업 디렉터리 복원 처리가 있지만 `kitty_fullscreen`은 지원 클래스 목록에 없다. 기존 `alacritty_fullscreen`의 작업 디렉터리 복원 분기에는 Alacritty 명령이 남아 있다. 다른 PC에서 전체화면 창을 포함한 프리셋을 옮길 때 이 차이를 확인한다. 멀티모니터에서는 저장 시 창이 있는 모니터를 기준으로 계산하고 복원 시 주 모니터를 기준으로 배치한다. [레이아웃 실행 로직](../ob-windows/ob_windows/layout/launch.py) · [창 도구 문서](../ob-windows/README.md)

## 외형, 패널, 세션 시작

| 항목 | 확인한 차이와 설정 위치 |
|---|---|
| Openbox | `themes/.current`는 `default` → `adaptive`. `rc.xml`의 창 테마는 `OB-Arc-Dark` → `OB-Adapta-Nokto`, 제목 버튼 배열은 `DLIMC` → `MLC`, 위 여백은 48 → 44px. 나머지 여백은 10px이고 데스크톱은 5개다. |
| 창 격자 | `~/.config/ob-grid/config.toml`은 저장소 기본값과 동일하다. 가로 ¼·⅓·½·⅔·¾·1, 세로 ⅓·½·⅔·¾·1, 창 사이 간격 10px, 스냅 허용 오차 12px. 바깥 여백은 Openbox 작업 영역에서 반영된다. |
| Polybar | Adaptive의 `polybar/config.ini`에서 `backlight` → `brightness`. `themes/system.ini`의 백라이트 장치도 `amdgpu_bl1` → `amdgpu_bl2`. 현재 나머지 설정값은 AC `ACAD`, 배터리 `BAT1`, 네트워크 `wlan0`이다. 여러 스타일의 모듈·팔레트 파일에도 변경이 있다. |
| Rofi | 런처, 실행기, 전원 메뉴, 스크린샷, Bluetooth, askpass, 음악 래퍼가 `adaptive` 스타일을 직접 지정한다. `rofi-keybinds`와 `rofi-rustdesk`는 `.current`를 읽고 각 스타일의 `keybinds.rasi` / `rustdesk.rasi`를 사용한다. `rofi-keybinds`의 데이터는 `kbinds.txt`이며 키바인더의 `apply`로 생성한다. 사진 캡처 스크립트의 선택 테두리 색도 변경돼 있다. |
| 벽지·색 | Nitrogen의 저장된 벽지는 Adaptive의 `wallpaper` 링크를 가리킨다. 메뉴 4종의 Change Wallpaper는 `ob-change-wallpaper`를 호출한다. Nitrogen에서 Apply를 누르면 `ob-theme-random.sh`가 `wal`로 팔레트를 생성한다. 색 변경은 Polybar, Rofi, Openbox 프레임, GTK CSS에 연결되고 여러 스타일의 `random.sh`가 공통 스크립트를 가리킨다. 전체 스타일 전환에는 기본 팔레트 복구와 Geany 적용 보조 코드가 있다. GTK CSS와 Kitty·Alacritty 색상 파일도 기본값에서 변경됐다. |
| Picom | `~/.config/picom.conf`의 `#-ob-grid-anim-start`부터 끝 표식까지 `geometry-change` 애니메이션(0.18초)을 추가했다. 함께 비교한 별도 Picom 설정 세 가지는 기본값과 같았다. |
| Dunst | Openbox 시작 시 `systemctl --user start dunst.service`를 시도하고 실패 시 직접 시작한다. 테마 적용 스크립트도 같은 방식으로 재시작하며 `height`·`offset`을 튜플 문법으로 출력한다. 현재 값은 `height = (0, 80)`, `offset = (10, 44)`. 사용자 autostart에서 xfce4-notifyd를 숨겼다. |
| 워크스페이스별 벽지 | `autostart`에 `workspace-wallpaper.sh` 호출이 있다. `workspace-wallpaper.py`는 Pillow와 Xlib을 사용한다. 현재 `~/.config/openbox/wallpapers/off` 표식이 있어 이 실험 기능은 꺼져 있다. |
| 앱 메뉴 | `menu-*.xml`의 일부 pipemenu 호출이 기존 XML 엔티티에서 작성 당시 홈의 절대 경로로 바뀌었다. 경로와 실제 `pipemenus/` 파일, 패키지가 제공하는 `/usr/share/archcraft/openbox/pipemenus/`를 대상 PC 기준으로 확인한다. |

`~/.config/openbox/environment`는 패키지 기본값과 같고 Openbox 스크립트 폴더를 PATH 앞에 추가한다. 공개 저장소에서 사용할 파일을 만들 때 이 경로 동작을 이용하면 원래 설치 경로나 사용자 이름에 의존하는 링크를 줄일 수 있다.

## 입력기와 기기 설정

- 한글은 Fcitx5 + Hangul이다. Openbox `autostart`에서 `fcitx5 -d`를 실행하고 `~/.xprofile`, `~/.config/environment.d/fcitx.conf`에 `GTK_IM_MODULE=fcitx`, `QT_IM_MODULE=fcitx`, `XMODIFIERS=@im=fcitx`, `GLFW_IM_MODULE=ibus`를 둔다. 마지막 값은 Kitty/GLFW에 사용하는 설정이다. 현재 프로필에는 `keyboard-us`와 `hangul`이 있고 기존 기록의 전환 키는 Ctrl+Space, 오른쪽 Alt, Hangul이다.
- 전원 메뉴의 Rofi 스크립트와 Openbox pipemenu는 절전 전 음악 정지·음소거 실패가 절전을 막지 않도록 바뀌었다. Rofi는 logind에 최대 절전 지원 여부를 물어보고 지원하지 않으면 알림을 띄운다.
- 이 노트북의 `/etc/systemd/logind.conf.d/50-laptop.conf`는 덮개를 닫거나 전원 버튼을 누르면 절전, 도킹 중 덮개를 닫으면 무시하도록 설정돼 있다. Xfce Power Manager의 `logind-handle-lid-switch`는 true다. `Super+Shift+P`는 사용자 스크립트와 전원 프로필 서비스가 필요하다.
- PipeWire/WirePlumber 관련 사용자 유닛 링크와 Bluetooth 헤드셋 볼륨 제한용 `bt-safe-volume.service`가 있다. 후자는 `~/.local/bin/bt-safe-volume` 및 로컬 기기 설정을 참조한다. Xfce의 디스플레이·입력 장치 설정도 별도로 있다.
- GPU 드라이버, 커널, 부트 설정, 공유 저장소 마운트와 사용자 서비스는 이 PC 환경의 일부다. 새 PC에서는 CachyOS 쪽 설정을 바탕으로 GPU, 화면 배치, 볼륨 장치, 배터리, 네트워크를 각각 확인한다.

## 다른 PC에 적용할 순서

1. 대상 PC에서 Openbox **X11** 세션을 준비하고 해당 에디션의 Archcraft 설정을 설치한다. 같은 외형을 재현하려면 본인이 확보한 Openbox Premium 패키지와 해당 테마·아이콘·폰트·배경을 준비한다. 일반판에서도 단축키와 창 도구를 적용할 수 있고 테마 선택지는 패키지마다 다르다. Openbox가 뜨면 사용자 설정을 백업하고 해당 버전의 `/etc/skel/.config/openbox`를 기준으로 변경을 적용한다. [Archcraft 공식 설치 및 설정 안내](https://wiki.archcraft.io/docs/window-managers/stacking-wm/openbox/)
2. GitHub에서 저장소를 최종 보관 위치에 clone한다. `python-xlib`, `rofi`, `dunst`, `uv`를 준비하고 저장소 루트에서 `./ob-windows/install.sh` 및 `./archcraft-keybinder/install.sh`를 실행한다. 창 도구 링크가 체크아웃 경로를 가리키므로 이동 후에는 창 도구 설치 스크립트를 다시 실행한다.
3. Kitty, zsh, 폰트를 준비하고 `./shell/install.sh`로 프롬프트를 맞춘다. 이어서 위 `ob-furminal`을 대상 PC의 Openbox 스크립트 폴더에 저장해 실행 권한을 준다. 메뉴와 XFCE 기본 앱을 수정한다. 단축키 표의 명령은 키바인더 CLI로 등록할 수 있고, 네이티브 동작은 기존 `rc.xml` 항목의 키나 액션을 수정한다. 예를 들어 `./archcraft-keybinder/run.sh set W-Left --cmd 'ob-grid move left'`로 바꾼다. 기존 키를 제거하거나 옮길 때는 `rm`을 사용할 수 있다. Rofi 키바인드 뷰어·RustDesk·전원 프로필·색 변경은 각 보조 스크립트와 리소스를 준비한 뒤 연결한다.
4. `themes/system.ini`의 장치값을 `ls /sys/class/power_supply /sys/class/backlight`, `ip -br link`, Openbox 세션의 `xrandr --query` 결과에 맞춘다. 원하는 테마, 패널, Picom, 벽지, 한글 입력기를 적용한다. 테마 변경 후에는 테마 스크립트가 다시 쓸 수 있는 Rofi·Kitty·Dunst 설정을 확인한다.
5. Openbox에 로그인한 상태에서 `./archcraft-keybinder/run.sh conflicts`를 실행한 다음 `./archcraft-keybinder/run.sh apply`로 단축키 목록과 Openbox 설정을 갱신한다. `Super+Enter`, `Super+T`, `Super+A`, `Super+방향키`, `Super+Ctrl+방향키`, `Super+O`, Thunar의 `Ctrl+.`, Kitty 한글 전환을 확인한다. `ob-grid info`는 활성 창과 작업 영역을 확인할 때 쓸 수 있다.

## GitHub에 올릴 때의 구성

현재 Git에서 관리하는 것은 창 도구 두 개, 키바인더, 이 문서와 각 도구의 테스트 및 설정 기본값이다. clone 후 추가로 필요한 로컬 작업은 위 절차에 기록했다. Rofi 애플릿, 테마 적용·벽지·전원 스크립트, Thunar·IME 설정까지 자동 설치하려면 본인 변경분을 검토해 이식 가능한 오버레이로 따로 추가해야 한다.

공개 배포에는 직접 작성한 변경과 재배포 조건을 확인한 자료를 사용한다. Premium 패키지와 원본 자산은 각 PC에서 제공처를 통해 준비한다. 홈 전체, 계정 정보, RustDesk 접속 정보, 네트워크·Bluetooth 프로필, 브라우저 데이터, 마운트 유닛, 로컬 로그·백업·프리셋을 그대로 올리면 개인 경로나 기기 정보가 따라갈 수 있다. 벽지와 생성된 팔레트는 원본 이미지와 재배포 조건을 확인하고, 사용자 경로와 장치명은 대상 PC의 로컬 설정으로 둔다.
