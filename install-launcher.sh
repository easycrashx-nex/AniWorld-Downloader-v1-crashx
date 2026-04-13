#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${HOME}/.local/bin"
TARGET_PATH="${TARGET_DIR}/aniworld"

mkdir -p "${TARGET_DIR}"

cat > "${TARGET_PATH}" <<EOF
#!/usr/bin/env bash
exec "${REPO_ROOT}/aniworld" "\$@"
EOF

chmod +x "${TARGET_PATH}"

ensure_path_line() {
  local file="$1"
  local line='export PATH="$HOME/.local/bin:$PATH"'
  if [[ -f "$file" ]]; then
    if ! grep -Fq "$line" "$file"; then
      printf '\n%s\n' "$line" >> "$file"
    fi
  else
    printf '%s\n' "$line" > "$file"
  fi
}

case "${SHELL:-}" in
  */zsh)
    ensure_path_line "${HOME}/.zshrc"
    ensure_path_line "${HOME}/.zprofile"
    ;;
  *)
    ensure_path_line "${HOME}/.bashrc"
    ensure_path_line "${HOME}/.profile"
    ;;
esac

case ":$PATH:" in
  *":${HOME}/.local/bin:"*) ;;
  *) export PATH="${HOME}/.local/bin:${PATH}" ;;
esac

echo "Installed launcher: ${TARGET_PATH}"
echo "You can now use 'aniworld' in new terminals."
echo "If the current terminal does not resolve it yet, open a new terminal and test with: aniworld --help"
