#!/usr/bin/env bash
set -euo pipefail
: "${WWISE_ROOT:?Enter the complete devshell first}"
: "${SML_DIR:?Enter the complete devshell first}"
mkdir -p "$SML_DIR/Plugins"
for plugin in "$WWISE_ROOT"/Plugins/*; do
  destination="$SML_DIR/Plugins/$(basename "$plugin")"
  if [[ -e "$destination" ]]; then
    printf 'Refusing to overwrite existing Wwise integration: %s\n' "$destination" >&2
    exit 1
  fi
done
for plugin in "$WWISE_ROOT"/Plugins/*; do
  destination="$SML_DIR/Plugins/$(basename "$plugin")"
  mkdir -p "$destination"
  while IFS= read -r -d '' entry; do
    if [[ "$(basename "$entry")" == ThirdParty ]]; then
      ln -s "$entry" "$destination/ThirdParty"
    else
      cp -a --no-preserve=mode "$entry" "$destination/"
    fi
  done < <(find "$plugin" -mindepth 1 -maxdepth 1 -print0)
done
