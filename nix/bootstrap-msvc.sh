#!/usr/bin/env bash
set -euo pipefail

project=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
if [[ "${1:-}" != --inside-nix ]]; then
  exec nix shell --inputs-from "path:$project" \
    nixpkgs#bash nixpkgs#python3 nixpkgs#git nixpkgs#gnutar \
    nixpkgs#gzip nixpkgs#coreutils \
    --command bash "$project/nix/bootstrap-msvc.sh" --inside-nix
fi

metadata=$(nix eval --impure --json --expr "
  let
    pkgs = import (builtins.getFlake \"path:$project\").inputs.nixpkgs {
      system = builtins.currentSystem;
      config.allowUnfree = true;
    };
  in (import $project/nix/msvc.nix { inherit pkgs; }).payload
")
field() {
  python3 -c 'import json,sys; print(json.loads(sys.argv[1])[sys.argv[2]])' "$metadata" "$1"
}
name=$(field name)
expected_hash=$(field sha256)
revision=$(field upstreamRevision)
root="${SF_ROOT:-${XDG_DATA_HOME:-$HOME/.local/share}/sf}/msvc-download"
cache="$root/$name.cache"
mkdir -p "$cache" "$root/tmp"
export TMPDIR="$root/tmp"
work=$(mktemp -d "$TMPDIR/bootstrap.XXXXXXXX")
trap 'rm -rf -- "$work"' EXIT
mkdir -p "$work/source" "$work/payload/upstream"
git -C "$work/source" init --quiet
git -C "$work/source" remote add origin https://github.com/mircearoata/msvc-wine.git
git -C "$work/source" fetch --quiet --depth 1 origin "$revision"
git -C "$work/source" archive FETCH_HEAD | tar -x -C "$work/payload/upstream"
python3 -c 'import sys,urllib.request; urllib.request.urlretrieve(sys.argv[1],sys.argv[2])' \
  "$(field manifestUrl)" "$work/payload/manifest.json"
python3 "$work/payload/upstream/vsdownload.py" \
  --accept-license --manifest "$work/payload/manifest.json" \
  --channel "$(field channel)" --msvc-version "$(field msvcVersion)" \
  --sdk-version "$(field sdkVersion)" --host-arch x64 \
  --cache "$cache" --only-download \
  Microsoft.Net.4.8.SDK Microsoft.VisualStudio.MinShell
cp -a "$cache" "$work/payload/cache"
tar --sort=name --format=gnu --mtime=@0 --owner=0 --group=0 --numeric-owner \
  --mode='u+rwX,go+rX,go-w' -C "$work/payload" -cf - . \
  | gzip -n > "$work/$name"
actual_hash=$(sha256sum "$work/$name")
actual_hash=${actual_hash%% *}
if [[ "$actual_hash" != "$expected_hash" ]]; then
  printf 'MSVC payload hash mismatch: expected %s, received %s\n' "$expected_hash" "$actual_hash" >&2
  exit 1
fi
mv -- "$work/$name" "$root/$name"
nix-store --add-fixed sha256 "$root/$name"
