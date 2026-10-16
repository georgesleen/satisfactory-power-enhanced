#!/usr/bin/env bash
# Downloads the free Satisfactory dedicated server with anonymous SteamCMD and imports it into the Nix store.
set -euo pipefail
root="${SF_ROOT:-${XDG_DATA_HOME:-$HOME/.local/share}/sf}"
repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
app_id=1690800
install_dir="$root/dl/server"
steam_home="$root/steamcmd-home"
mkdir -p "$install_dir" "$steam_home"

# SteamCMD state lives in a private HOME under SF_ROOT.
HOME="$steam_home" steamcmd +force_install_dir "$install_dir" +login anonymous \
  +app_update "$app_id" validate +quit

manifest="$install_dir/steamapps/appmanifest_$app_id.acf"
build_id="$(sed -n 's/^[[:space:]]*"buildid"[[:space:]]*"\([0-9]*\)".*/\1/p' "$manifest")"
if [[ -z "$build_id" || "$build_id" == 0 || ! -f "$install_dir/FactoryServer.sh" ]]; then
  printf 'Server installation is incomplete: %s\n' "$manifest" >&2
  exit 1
fi

archive="$root/dl/satisfactory-server-$build_id.tar.zst"
if [[ ! -f "$archive" ]]; then
  printf 'Archiving server build %s\n' "$build_id"
  tar --create --sort=name --mtime=@0 --owner=0 --group=0 --numeric-owner \
    --exclude=./steamapps --directory="$install_dir" . |
    zstd --threads=4 -3 --quiet --force -o "$archive.partial"
  mv "$archive.partial" "$archive"
fi

sha256="$(sha256sum "$archive" | cut -d' ' -f1)"
nix-store --add-fixed sha256 "$archive"
printf '{\n  "buildId": "%s",\n  "name": "%s",\n  "sha256": "%s"\n}\n' \
  "$build_id" "$(basename "$archive")" "$sha256" >"$repo/nix/server-source.json"
printf 'Recorded server build %s in nix/server-source.json\n' "$build_id"
