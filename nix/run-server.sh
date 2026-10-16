#!/usr/bin/env bash
set -euo pipefail
if [[ "${SF_SERVER_NAMESPACE:-}" != 1 ]]; then
  exec bwrap --die-with-parent --unshare-net --bind / / --dev-bind /dev /dev \
    --proc /proc --setenv SF_SERVER_NAMESPACE 1 "$0" "$@"
fi
root="${SF_ROOT:-${XDG_DATA_HOME:-$HOME/.local/share}/sf}"
instance="$root/server-instance"
export HOME="$root/server-home"
export XDG_CONFIG_HOME="$root/server-config"
export XDG_CACHE_HOME="$root/server-cache"
export XDG_DATA_HOME="$root/server-data"
mkdir -p "$HOME" "$XDG_CONFIG_HOME" "$XDG_CACHE_HOME" "$XDG_DATA_HOME"

if [[ ! -d "$instance" ]]; then
  mkdir -p "$instance"
  cp --recursive --symbolic-link "$SF_SERVER/." "$instance/"
  find "$instance" -type d -exec chmod u+w {} +
  # The launcher and executable define Unreal's installation directory.
  for executable in FactoryServer.sh Engine/Binaries/Linux/FactoryServer-Linux-Shipping \
    Engine/Binaries/Linux/crashpad_handler; do
    if [[ -L "$instance/$executable" ]]; then
      rm "$instance/$executable"
      cp "$SF_SERVER/$executable" "$instance/$executable"
      chmod u+w "$instance/$executable"
    fi
  done
  mkdir -p "$instance/FactoryGame/Mods/SML" "$instance/FactoryGame/Saved" \
    "$instance/FactoryGame/Certificates"
  cp --recursive --symbolic-link "$SF_SML/." "$instance/FactoryGame/Mods/SML/"
  find "$instance/FactoryGame/Mods/SML" -type d -exec chmod u+w {} +
  printf '%s\n' "$SF_SERVER" >"$instance/.server-source"
fi

if [[ "$(cat "$instance/.server-source")" != "$SF_SERVER" ]]; then
  printf 'Instance uses a different server build. Move %s aside before starting this build.\n' "$instance" >&2
  exit 1
fi

cd "$instance"
exec steam-run "$instance/FactoryServer.sh" -unattended -log -nullrhi \
  -multihome=127.0.0.1 -Port=7777 -ReliablePort=8888 \
  '-ini:Engine:[SystemSettings]:FG.DedicatedServer.AllowInsecureLocalAccess=1'
