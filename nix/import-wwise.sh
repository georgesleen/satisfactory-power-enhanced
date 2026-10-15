#!/usr/bin/env bash
set -euo pipefail
root="${SF_ROOT:-${XDG_DATA_HOME:-$HOME/.local/share}/sf}"
source="$root/bootstrap/wwise-project/Plugins"
archive="$root/dl/enhancedpower-wwise-2025.1.6.9117-2025.1.6.4248.tar.zst"
test -d "$source/Wwise/ThirdParty"
mkdir -p "$root/dl"
tar --sort=name --mtime=@0 --owner=0 --group=0 --numeric-owner \
  -C "$(dirname "$source")" -cf - Plugins | zstd -T0 -o "$archive" -f
read -r hash _ < <(sha256sum "$archive")
nix-store --add-fixed sha256 "$archive"
printf '{"sha256":"%s","sdkVersion":"2025.1.6.9117","integrationVersion":"2025.1.6.4248"}\n' "$hash" > nix/wwise-source.json
# Git flakes (direnv `use flake .`) only see files in the Git index.
git add nix/wwise-source.json
printf 'Wwise source imported; nix/wwise-source.json is staged as its lock.\n'
