#!/usr/bin/env bash
# Install the zsh prompt (Oh My Zsh "archcraft" theme with a clock) for the current user.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
omz="${ZSH:-$HOME/.oh-my-zsh}"
themes="${ZSH_CUSTOM:-$omz/custom}/themes"
target="$themes/archcraft.zsh-theme"
zshrc="${ZDOTDIR:-$HOME}/.zshrc"

if [[ ! -f "$omz/oh-my-zsh.sh" ]]; then
    echo "Oh My Zsh not found at $omz." >&2
    echo "Install it first (Archcraft: the archcraft-omz package, otherwise https://ohmyz.sh), then re-run." >&2
    exit 1
fi

mkdir -p "$themes"
if [[ -f "$target" ]] && ! cmp -s "$here/archcraft.zsh-theme" "$target"; then
    cp -p "$target" "$target.bak"
    echo "Backed up existing theme to $target.bak"
fi
cp "$here/archcraft.zsh-theme" "$target"
echo "Installed $target"

if [[ ! -f "$zshrc" ]]; then
    echo "No $zshrc. Create one that sets ZSH_THEME=\"archcraft\" and sources \$ZSH/oh-my-zsh.sh." >&2
    exit 1
elif grep -q '^ZSH_THEME="archcraft"' "$zshrc"; then
    echo "$zshrc already uses ZSH_THEME=\"archcraft\""
elif grep -q '^ZSH_THEME=' "$zshrc"; then
    cp -p "$zshrc" "$zshrc.bak"
    sed -i 's/^ZSH_THEME=.*/ZSH_THEME="archcraft"/' "$zshrc"
    echo "Set ZSH_THEME=\"archcraft\" in $zshrc (backup: $zshrc.bak)"
else
    echo "No ZSH_THEME line in $zshrc. Add ZSH_THEME=\"archcraft\" above the 'source \$ZSH/oh-my-zsh.sh' line." >&2
    exit 1
fi

[[ "$(getent passwd "$USER" | cut -d: -f7)" == */zsh ]] || echo "Login shell is not zsh. Run: chsh -s \"\$(command -v zsh)\""
echo "Open a new terminal or run: exec zsh"
