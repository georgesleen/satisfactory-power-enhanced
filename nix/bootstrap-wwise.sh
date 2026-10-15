#!/usr/bin/env bash
set -euo pipefail
root="${SF_ROOT:-${XDG_DATA_HOME:-$HOME/.local/share}/sf}"
root="$(realpath -m "$root")"
repo="$(pwd)"
export HOME="$root/bootstrap/wwise-home"
export XDG_CONFIG_HOME="$HOME/.config"
export XDG_CACHE_HOME="$root/cache"
export TMPDIR="$root/tmp"
mkdir -p "$HOME" "$XDG_CONFIG_HOME/Epic/UnrealEngine" "$TMPDIR" "$root/bootstrap/wwise-project"
engine="$(nix build path:.#engine --no-link --print-out-paths)"
printf '[Installations]\n5.6.1-CSS=%s\n' "$engine" > "$XDG_CONFIG_HOME/Epic/UnrealEngine/Install.ini"
printf '{"EngineAssociation":"5.6.1-CSS"}\n' > "$root/bootstrap/wwise-project/FactoryGame.uproject"
if [[ -z "${WWISE_EMAIL:-}" ]]; then
  read -r -p 'Audiokinetic email: ' WWISE_EMAIL
fi
if [[ -z "${WWISE_PASSWORD:-}" ]]; then
  read -r -s -p 'Audiokinetic password: ' WWISE_PASSWORD
  printf '\n'
fi
export WWISE_EMAIL WWISE_PASSWORD
# Upstream prints signed download URLs on stdout and in errors; keep them out of logs.
redact() { sed -E 's#https?://[^[:space:]"]+#<url redacted>#g' >&2; }
{ nix run "path:$repo#wwise-cli" -- --cache-dir "$root/cache/wwise-cli" download \
  --sdk-version 2025.1.6.9117 --filter Packages=SDK \
  --filter DeploymentPlatforms=Windows_vc160 --filter DeploymentPlatforms=Windows_vc170 \
  --filter DeploymentPlatforms=Linux --filter DeploymentPlatforms= 2>&1 > /dev/null; } | redact
{ nix run "path:$repo#wwise-cli" -- --cache-dir "$root/cache/wwise-cli" integrate-ue \
  --integration-version 2025.1.6.4248 \
  --project "$root/bootstrap/wwise-project/FactoryGame.uproject" 2>&1 > /dev/null; } | redact
printf 'Wwise payload ready. Run make import-wwise.\n'
