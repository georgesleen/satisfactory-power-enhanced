#!/usr/bin/env bash
set -euo pipefail
root="${SF_ROOT:-${XDG_DATA_HOME:-$HOME/.local/share}/sf}"
project="$root/s"
revision=8eebc9e659f0b2ff4392d2f8cf6e2cff60c8ea49
repo="$(pwd -P)"
if [[ ! -d "$project" ]]; then
  mkdir -p "$root"
  git init "$project"
  git -C "$project" remote add origin https://github.com/satisfactorymodding/SatisfactoryModLoader.git
  git -C "$project" fetch --depth 1 origin "$revision"
  git -C "$project" checkout --detach FETCH_HEAD
fi
if [[ "$(git -C "$project" rev-parse HEAD)" != "$revision" ]]; then
  printf 'Existing starter checkout differs from pinned revision %s; preserve changes before updating it.\n' "$revision" >&2
  exit 1
fi
link="$project/Mods/EnhancedPower"
if [[ -L "$link" && "$(readlink -f "$link")" == "$repo" ]]; then
  exit 0
fi
if [[ -e "$link" || -L "$link" ]]; then
  printf 'Refusing to replace existing mod path: %s\n' "$link" >&2
  exit 1
fi
ln -s "$repo" "$link"
