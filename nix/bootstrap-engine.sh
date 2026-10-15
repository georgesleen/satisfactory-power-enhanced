#!/usr/bin/env bash
set -euo pipefail
root="${SF_ROOT:-${XDG_DATA_HOME:-$HOME/.local/share}/sf}"
mkdir -p "$root/dl"
names=(00 01 02 03)
hashes=(
  5847a80489d04e7ec231de01c154e1046174aa69f5d2c00023a62a67626001e7
  06e8177c34ac2cae5568a71dc92b735162ee29987e964ecf312620f0b11a8d9f
  b624c15b9becf336b6ed4e71b73498f208d3f6edaf857e0bcdcebce7540a9362
  565829545aff54f3771ac80d00e6edea38fd0a235c723c55be063f563aadb049
)
for index in "${!names[@]}"; do
  part="$root/dl/UnrealEngine-CSS-Editor-Linux.tar.zst.${names[index]}"
  if [[ ! -f "$part" ]] || ! printf '%s  %s\n' "${hashes[index]}" "$part" | sha256sum --check --status; then
    printf 'Downloading missing or incomplete engine part %s\n' "${names[index]}"
    GODEBUG=http2client=0 gh release download 5.6.1-css-83 --repo satisfactorymodding/UnrealEngine \
      --pattern "$(basename "$part")" --dir "$root/dl" --clobber
    printf '%s  %s\n' "${hashes[index]}" "$part" | sha256sum --check
  fi
  nix-store --add-fixed sha256 "$part"
done
