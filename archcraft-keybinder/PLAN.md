# Archcraft Keybinder — 작업 계획서

CachyOS + Archcraft Openbox 환경에서 `~/.config/openbox/rc.xml`의 키보드 단축키를 안전하게 조회·수정·복원하는 TUI 앱.

- **런타임:** Python 3 + `uv`
- **UI:** Textual (터미널 UI, 카테고리 탭)
- **대상 파일:** `~/.config/openbox/rc.xml`의 `<keyboard>` 섹션만
- **파생물:** `~/.config/openbox/kbinds.txt` (Archcraft `ac-kb`와 동일 목적, 저장 후 갱신)

---

## 1. 목표 / 비목표

### 목표 (MVP)

- 단축키 목록 조회 (검색, 카테고리 탭)
- 단축키 추가 / 수정 / 삭제
- 키 충돌 검사
- 저장 전 자동 백업
- `openbox --reconfigure`로 즉시 반영
- **최초(Archcraft 기본) 설정으로 복원** — 전체 / 개별

### 비목표 (나중에)

- 마우스 바인딩 (`<mouse>`)
- lead(hot corner), sxhkd 등 Openbox 밖 바인딩
- Vue/Tauri GUI
- 테마·폰트 등 `rc.xml`의 비-keyboard 섹션 편집

---

## 2. “최초 설정 복원” 설계

### 소스 오브 트루스

| 우선순위 | 경로 | 설명 |
|----------|------|------|
| 1 | `/etc/skel/.config/openbox/rc.xml` | Archcraft 패키지가 심는 **신규 사용자 기본값** (현재 keybind ~108개) |
| 2 | 앱에 동봉한 스냅샷 `defaults/archcraft-keyboard.xml` | skel이 없거나(비 Archcraft) 버전이 다를 때 fallback |
| — | `/etc/xdg/openbox/rc.xml` | **사용하지 않음** (바닐라 Openbox, keybind ~24개뿐) |

복원은 **파일 전체를 덮어쓰지 않는다.**  
`rc.xml`에서 `<keyboard>…</keyboard>`만 skel(또는 동봉 스냅샷)의 해당 섹션으로 교체한다. 테마·마우스·창 규칙은 유지.

### 복원 동작

1. **전체 복원 (`reset --all`)**
   - 현재 `rc.xml` 백업 → `~/.config/openbox/backups/rc.xml.YYYYMMDD-HHMMSS`
   - skel에서 `<keyboard>` 추출
   - 사용자 `rc.xml`의 `<keyboard>`와 교체
   - `kbinds.txt` 재생성
   - `openbox --reconfigure`
   - TUI에서는 확인 모달 필수 (“모든 단축키가 Archcraft 기본값으로 돌아갑니다”)

2. **개별 복원 (`reset KEY`)**
   - skel에서 해당 `key`의 `<keybind>` 하나를 찾아 사용자 쪽에 덮어쓰거나, skel에만 있으면 추가, 사용자만의 커스텀 키면 삭제 여부를 물어봄
   - 목록에서 “이 키를 기본값으로” 액션으로 노출

3. **기본값 대비 표시**
   - 각 행에 상태: `stock` / `modified` / `custom`(skel에 없는 키)
   - 탭이나 필터로 “수정된 것만” 보기

### 패키지 업데이트와의 관계

`archcraft-openbox` 업데이트 후 skel이 바뀌면 “최초 설정”의 의미가 새 패키지 기본값으로 따라간다.  
원하면 나중에 “앱 설치 시점 스냅샷으로 복원” 옵션을 추가할 수 있으나, MVP는 **항상 현재 skel 기준**으로 한다.

---

## 3. 폴더 / 파일 구조

```text
archcraft-keybinder/
├── PLAN.md                 # 이 계획서
├── README.md               # 설치·사용법 (구현 후)
├── pyproject.toml          # uv 프로젝트·의존성·엔트리포인트
├── uv.lock                 # uv가 생성·잠금
│
├── defaults/
│   └── archcraft-keyboard.xml   # skel에서 추출한 <keyboard> 스냅샷 (fallback)
│
├── src/
│   └── keybinder/
│       ├── __init__.py
│       ├── __main__.py     # python -m keybinder
│       ├── cli.py          # CLI 엔트리 (list/get/set/reset/apply)
│       ├── paths.py        # rc.xml, skel, backup 경로 상수
│       ├── models.py       # Keybind, Action, Category dataclass
│       ├── categorize.py   # 영역(탭) 분류 규칙
│       ├── parse.py        # rc.xml → Keybind 리스트
│       ├── write.py        # Keybind 리스트 → keyboard 섹션 패치 + 백업
│       ├── defaults.py     # skel/동봉 기본값 로드, diff, reset
│       ├── apply.py        # kbinds.txt 갱신 + openbox --reconfigure
│       ├── conflicts.py    # 키 충돌 검사
│       └── tui/
│           ├── __init__.py
│           ├── app.py      # Textual App 루트
│           ├── tabs.py     # 카테고리 TabbedContent
│           ├── table.py    # 단축키 DataTable
│           ├── editors.py  # 추가/수정 화면
│           └── dialogs.py  # 확인·에러·전체 복원 모달
│
└── tests/
    ├── fixtures/
    │   ├── rc_sample.xml
    │   └── keyboard_stock.xml
    ├── test_parse.py
    ├── test_write.py
    ├── test_defaults.py
    └── test_conflicts.py
```

개발 중 사용:

```bash
cd ~/Projects/openbox-tools/archcraft-keybinder
uv sync
uv run keybinder            # TUI (기본)
uv run keybinder list       # CLI
uv run keybinder reset --all --dry-run
```

---

## 4. 파일별 역할

### 프로젝트 메타

| 파일 | 역할 |
|------|------|
| `pyproject.toml` | 패키지명, 의존성(`textual`, `lxml`), 스크립트 `keybinder = keybinder.cli:main` |
| `uv.lock` | 재현 가능한 의존성 잠금 (`uv sync`) |
| `defaults/archcraft-keyboard.xml` | 오프라인/비-skel 환경용 기본 `<keyboard>` 스냅샷. 릴리스 시 skel에서 복사해 갱신 |

### 코어 (`src/keybinder/`)

| 파일 | 역할 |
|------|------|
| `paths.py` | `RC_XML = ~/.config/openbox/rc.xml`, `SKEL_RC = /etc/skel/.config/openbox/rc.xml`, `BACKUP_DIR`, `KBIND_TXT` 등 |
| `models.py` | `Keybind(key, actions, category, origin)`, `Action(name, params)` 등 공통 타입 |
| `categorize.py` | 탭 분류: `apps` / `window` / `menus` / `hardware` / `session` / `other`. Execute→command, ShowMenu, WM 액션명, `XF86*`/`Print` 등으로 추론 |
| `parse.py` | Openbox 3.4 네임스페이스 포함 XML 파싱 → `list[Keybind]`. Archcraft `ac-kb`와 동일한 루트 가정 |
| `write.py` | 기존 `rc.xml` 로드 → `<keyboard>`만 새 내용으로 교체 → 원자적 저장(tmp+replace). **주석/다른 섹션 최대한 보존**(lxml 한계 문서화). 저장 전 `backups/`에 복사 |
| `defaults.py` | skel(또는 `defaults/`)에서 stock 키맵 로드. `diff(current, stock)`, `reset_all()`, `reset_one(key)` |
| `conflicts.py` | 같은 `key` 문자열 중복, (선택) modifier 정규화 후 충돌 |
| `apply.py` | 저장 성공 후: (1) `kbinds.txt` 재작성 또는 `ac-kb` 호출 (2) `openbox --reconfigure` (3) 실패 시 사용자에게 알림 |
| `cli.py` | argparse/subcommand. TUI는 인자 없이 또는 `tui` 서브커맨드 |
| `__main__.py` | `python -m keybinder` → `cli.main` |

### CLI 서브커맨드 (예정)

```text
keybinder                  # TUI 실행
keybinder list [--category] [--json] [--modified]
keybinder get <KEY>
keybinder set <KEY> --cmd <command> | --action <Name> ...
keybinder add ...
keybinder rm <KEY>
keybinder conflicts [<KEY>]
keybinder reset --all|--key <KEY> [--dry-run] [--yes]
keybinder apply            # 이미 메모리/파일에 반영된 뒤 reconfigure만
keybinder diff             # 현재 vs Archcraft 기본
```

### TUI (`src/keybinder/tui/`)

| 파일 | 역할 |
|------|------|
| `app.py` | Textual `App`. 키바인딩: 저장 `Ctrl+S`, 전체 복원 `Ctrl+R`(확인 후), 종료 `q` |
| `tabs.py` | 카테고리별 탭. 배지에 “수정 N개” 표시 가능 |
| `table.py` | 컬럼: Key / Action요약 / Status(stock\|modified\|custom) / Category |
| `editors.py` | 키 캡처·커맨드 입력·액션 타입 선택. 저장은 코어 `write` 호출 |
| `dialogs.py` | 전체 복원 확인, 충돌 경고, 백업 경로 안내 |

### 테스트

| 파일 | 역할 |
|------|------|
| `fixtures/*.xml` | 잘린 샘플 `rc.xml` / stock keyboard |
| `test_parse.py` | keybind 개수·Execute/ShowMenu 파싱 |
| `test_write.py` | keyboard만 바뀌고 mouse 등은 유지되는지 |
| `test_defaults.py` | reset_all / reset_one / modified 판정 |
| `test_conflicts.py` | 중복 키 |

---

## 5. 카테고리(탭) 규칙 (초안)

| 탭 | 판별 |
|----|------|
| **Apps** | `action=Execute` 이고 command가 앱/터미널/스크립트 (`alacritty`, `firefox`, `rofi-*`, `ob-*` 등) |
| **Menus** | `ShowMenu` 또는 rofi 런처류를 메뉴로 묶을지 정책으로 결정 (MVP: ShowMenu만 Menus, rofi는 Apps) |
| **Window** | `NextWindow`, `Close`, `Maximize*`, `Move*`, `Resize*`, `GoToDesktop`, `SendToDesktop` 등 WM 액션 |
| **Hardware** | 키 이름 `XF86*` / `Print` / `*Brightness*` 등 |
| **Session** | `Reconfigure`, `Restart`, `Exit`, 설정 리로드 알림 조합 |
| **Other** | 나머지 |

분류는 휴리스틱이라 `categorize.py`에서만 바꾸면 탭이 따라가게 한다.

---

## 6. 구현 페이즈

### Phase 0 — 골격 (½일)

- `uv init` / `pyproject.toml` / 패키지 레이아웃
- `paths.py`, 빈 CLI `keybinder --help`
- skel에서 `defaults/archcraft-keyboard.xml` 추출해 동봉

### Phase 1 — 코어 + CLI (핵심)

- `parse` / `write` / `backup`
- `list` / `get` / `set` / `rm` / `conflicts`
- **`reset --all` / `reset --key` / `diff`**
- `apply` (reconfigure + kbinds.txt)
- 단위 테스트로 write/write/reset 고정

### Phase 2 — TUI

- 탭 + 테이블 + 검색
- 편집 / 삭제
- **전체·개별 복원 다이얼로그**
- modified 표시

### Phase 3 — 다듬기

- README, `uv tool install .`
- (선택) 데스크톱 메뉴 항목 / Openbox 메뉴에 “Keybinder” 추가 가이드
- write 시 XML 포맷/주석 보존 개선

---

## 7. 위험 요소와 대응

| 위험 | 대응 |
|------|------|
| lxml이 XML 주석/포맷을 깨뜨림 | keyboard 섹션만 문자열 치환하는 방식도 검토; 항상 백업; `--dry-run` |
| openbox 네임스페이스 | `{http://openbox.org/3.4/rc}` 고정 처리 (`ac-kb`와 동일) |
| skel 부재 (순정 Arch 등) | `defaults/archcraft-keyboard.xml` fallback + 경고 |
| 사용자가 rc.xml 전체를 pacnew로 교체 | 앱은 keyboard만 다루므로 영향 제한적; 복원은 다시 skel 기준 |
| reconfigure 실패 | 비Openbox 세션 감지 시 메시지만, 파일은 저장된 상태 유지 |

---

## 8. 성공 기준 (MVP 완료 조건)

1. `uv run keybinder list`로 현재 ~108개 단축키가 보인다.
2. 키 하나 변경 → 백업 생성 → `openbox --reconfigure` 후 실제 동작이 바뀐다.
3. `keybinder reset --all` 후 단축키가 `/etc/skel/.../rc.xml`의 keyboard와 일치한다. (테마 등 다른 섹션은 그대로)
4. TUI에서 카테고리 탭으로 탐색하고, 확인 모달 뒤에 전체 복원을 실행할 수 있다.

---

## 9. 다음 액션

계획 승인 후 Phase 0부터 진행:

1. `uv`로 프로젝트 초기화
2. 위 디렉터리 생성
3. skel → `defaults/archcraft-keyboard.xml` 스냅샷
4. `parse` + `reset --all --dry-run`까지 먼저 동작 확인
