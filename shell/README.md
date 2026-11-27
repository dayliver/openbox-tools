# zsh 프롬프트

```
10:05   openbox-tools   git:(main) ✗
```

Oh My Zsh의 Archcraft 기본 테마(`archcraft.zsh-theme`)에서 맨 앞의 화살표 기호를 현재 시각으로 바꾼 것이다. 나머지는 Archcraft 기본값 그대로다.

| 부분 | 내용 | 색 |
|---|---|---|
| `10` | 시 (`%D{%H}`) | 빨강 |
| `:` | 구분자 | 회색 (8번) |
| `05` | 분 (`%D{%M}`) | 노랑 |
| 폴더 아이콘 | Nerd Font U+F07B | 밝은 초록 (10번) |
| `openbox-tools` | 현재 폴더 이름 (`%c`) | 청록 |
| `git:(main)` | Git 저장소 안에서만 표시. GitHub 아이콘 U+F09B | 파랑, 브랜치는 자홍 |
| ✗ / ✓ | 커밋 안 된 변경 있음(U+F00D) / 없음(U+F00C) | 빨강 / 초록 |

시각은 프롬프트가 그려질 때의 값이고 이후 갱신되지 않는다.

## 필요한 것

- **zsh**가 로그인 셸일 것. 아니면 `chsh -s "$(command -v zsh)"`.
- **Oh My Zsh**. Archcraft 구성을 설치한 PC는 `archcraft-omz` 패키지가 `~/.oh-my-zsh`와 `~/.zshrc`를 이미 넣어 둔다. 없으면 <https://ohmyz.sh> 안내대로 설치한다.
- `~/.zshrc`의 `plugins`에 `git` (Oh My Zsh 기본값).
- 터미널 글꼴이 **Nerd Font**일 것. 이 PC의 Kitty는 `JetBrainsMono Nerd Font`를 쓴다. 아이콘이 네모로 보이면 글꼴 문제다.

## 설치

```bash
./shell/install.sh
exec zsh
```

스크립트가 하는 일은 두 가지다.

1. `archcraft.zsh-theme`를 `~/.oh-my-zsh/custom/themes/`에 복사한다. 내용이 다른 기존 파일은 `.bak`으로 남긴다.
2. `~/.zshrc`의 `ZSH_THEME=` 줄이 `archcraft`가 아니면 `ZSH_THEME="archcraft"`로 바꾼다. 바꾸기 전 `~/.zshrc.bak`을 만든다.

링크가 아니라 복사이므로 이 저장소에서 테마를 고친 뒤에는 스크립트를 다시 실행한다. 손으로 할 때도 같은 두 단계다.

## 색이 다르게 보일 때

테마는 색 이름과 번호(빨강, 노랑, 8번, 10번 등 터미널 16색)만 지정한다. 실제 색조는 터미널 팔레트가 정하므로 같은 색으로 보이려면 Kitty 색 구성도 같아야 한다. 이 PC에서는 Openbox 테마와 `wal`이 Kitty 색상 파일을 다시 쓴다. ([데스크톱 구성 문서](../docs/desktop-profile.md)의 벽지·색 항목)

## 이 PC의 `~/.zshrc`에서 프롬프트 외에 바뀐 것

Archcraft 기본 `~/.zshrc` 끝에 아래를 덧붙였다. 프롬프트와는 무관하고, 필요한 도구가 있는 PC에서만 옮기면 된다.

```zsh
# --- toolchains ---
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"

export BUN_INSTALL="$HOME/.bun"
case ":$PATH:" in *":$BUN_INSTALL/bin:"*) ;; *) PATH="$BUN_INSTALL/bin:$PATH" ;; esac

[ -f "$HOME/.cargo/env" ] && . "$HOME/.cargo/env"
case ":$PATH:" in *":$HOME/.local/bin:"*) ;; *) PATH="$HOME/.local/bin:$PATH" ;; esac

# ls colors (~/.config/dircolors 가 있을 때만)
[[ -f "$HOME/.config/dircolors" ]] && eval "$(dircolors -b "$HOME/.config/dircolors")"

# fzf (fd 필요)
export FZF_DEFAULT_COMMAND='fd --type f --hidden --follow --exclude .git'
export FZF_DEFAULT_OPTS='--height 40% --layout=reverse --border'
```
