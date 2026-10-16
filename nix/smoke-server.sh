#!/usr/bin/env bash
set -euo pipefail
if [[ "${SF_SERVER_NAMESPACE:-}" != 1 ]]; then
  exec bwrap --die-with-parent --unshare-net --bind / / --dev-bind /dev /dev \
    --proc /proc --setenv SF_SERVER_NAMESPACE 1 "$0" "$@"
fi
root="${SF_ROOT:-${XDG_DATA_HOME:-$HOME/.local/share}/sf}"
log_directory="$root/server-smoke"
mkdir -p "$log_directory"
endpoint=https://127.0.0.1:7777/api/v1
startup_timeout=300
simulation_wait=10

request() {
  local function="$1"
  local data="${2:-"{}"}"
  local response
  if ! response="$(curl --insecure --silent --show-error --fail-with-body --max-time 30 \
    "$endpoint" -H 'Content-Type: application/json' \
    --data "$(jq -cn --arg function "$function" --argjson data "$data" '{function:$function,data:$data}')")"; then
    printf '%s\n' "$response" >&2
    return 1
  fi
  if [[ -z "$response" ]]; then response='{}'; fi
  printf '%s\n' "$response" | tee "$log_directory/$function.json"
  jq -e 'has("errorCode") | not' <<<"$response" >/dev/null
}

sf-server >"$log_directory/console.log" 2>&1 &
server_process=$!

wait_for_server() {
  local deadline=$((SECONDS + $1))
  while kill -0 "$server_process" 2>/dev/null; do
    if ((SECONDS >= deadline)); then return 1; fi
    sleep 1
  done
}

cleanup() {
  local status=$?
  trap - EXIT INT TERM
  if kill -0 "$server_process" 2>/dev/null; then
    request Shutdown || true
    if ! wait_for_server 30; then
      printf 'Server does not stop after API Shutdown; sending SIGTERM.\n' >&2
      # Background jobs of a non-interactive shell ignore SIGINT.
      kill -TERM "$server_process" 2>/dev/null || true
      if ! wait_for_server 10; then
        printf 'Server does not stop after SIGTERM; sending SIGKILL.\n' >&2
        kill -KILL "$server_process" 2>/dev/null || true
      fi
      status=1
    fi
    wait "$server_process" || status=1
  fi
  exit "$status"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

deadline=$((SECONDS + startup_timeout))
until request HealthCheck '{"ClientCustomData":"EnhancedPower"}' 2>"$log_directory/api-wait.log"; do
  if ! kill -0 "$server_process" 2>/dev/null || ((SECONDS >= deadline)); then
    cat "$log_directory/console.log" >&2
    exit 1
  fi
  sleep 2
done

ss -lntup >"$log_directory/listeners.txt"
if grep -E '([[:space:]]|:)(7777|8888)[[:space:]]' "$log_directory/listeners.txt" | grep -v '127.0.0.1:'; then
  printf 'Server listener is not loopback-only.\n' >&2
  exit 1
fi
request QueryServerState
request GetServerOptions
pause_option="$(jq -er '.data.serverOptions | keys[] | select(test("AutoPause"; "i"))' "$log_directory/GetServerOptions.json")"
request ApplyServerOptions "$(jq -cn --arg option "$pause_option" '{UpdatedServerOptions:{($option):"False"}}')"
request CreateNewGame '{"NewGameData":{"SessionName":"EnhancedPowerHeadless","MapName":"","StartingLocation":"","bSkipOnboarding":true,"AdvancedGameSettings":{},"GameModeSettings":{},"CustomOptionsOnlyForModding":{}}}'

deadline=$((SECONDS + startup_timeout))
until request QueryServerState && jq -e '.data.serverGameState.isGameRunning == true and .data.serverGameState.isGamePaused == false' "$log_directory/QueryServerState.json" >/dev/null; do
  if ! kill -0 "$server_process" 2>/dev/null || ((SECONDS >= deadline)); then exit 1; fi
  sleep 2
done
cp "$log_directory/QueryServerState.json" "$log_directory/state-before.json"
sleep "$simulation_wait"
request QueryServerState
cp "$log_directory/QueryServerState.json" "$log_directory/state-after.json"
jq -e -s '.[1].data.serverGameState.totalGameDuration > .[0].data.serverGameState.totalGameDuration' \
  "$log_directory/state-before.json" "$log_directory/state-after.json"
request RunCommand '{"Command":"server.SaveGame EnhancedPowerHeadless"}'
grep -Ei 'SML.*3\.12\.0|3\.12\.0.*SML' "$log_directory/console.log" >"$log_directory/sml-version.txt"
cat "$log_directory/sml-version.txt"
request Shutdown
if ! wait_for_server 30; then
  printf 'Server shutdown exceeds 30 seconds.\n' >&2
  exit 1
fi
wait "$server_process"
trap - EXIT INT TERM
