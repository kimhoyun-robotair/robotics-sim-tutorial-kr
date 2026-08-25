#!/usr/bin/env bash
set -euo pipefail

scenario=""
evidence=""
world=""
server_pid=""
capture_pids=()

while (( $# > 0 )); do
  case "$1" in
    --scenario)
      scenario="${2:-}"
      shift 2
      ;;
    --evidence)
      evidence="${2:-}"
      shift 2
      ;;
    --world)
      world="${2:-}"
      shift 2
      ;;
    *)
      printf 'unknown argument: %s\n' "$1" >&2
      exit 64
      ;;
  esac
done

if [[ -z "$scenario" || -z "$evidence" ]]; then
  printf 'required: --scenario NAME --evidence PATH\n' >&2
  exit 64
fi

mkdir -p "$evidence"
cleanup_file="$evidence/cleanup.json"
cleanup() {
  local pid
  local survivors=0
  local owned_csv
  for pid in "${capture_pids[@]}"; do
    kill -TERM "$pid" 2>/dev/null || true
    wait "$pid" 2>/dev/null || true
  done
  if [[ -n "$server_pid" ]]; then
    kill -INT -- "-$server_pid" 2>/dev/null || true
    for _ in {1..30}; do
      kill -0 "$server_pid" 2>/dev/null || break
      sleep 0.1
    done
    kill -TERM -- "-$server_pid" 2>/dev/null || true
    wait "$server_pid" 2>/dev/null || true
    kill -0 "$server_pid" 2>/dev/null && survivors=1
  fi
  owned_csv=$(IFS=,; printf '%s' "${capture_pids[*]}")
  if [[ -n "$server_pid" ]]; then
    owned_csv="${owned_csv:+$owned_csv,}$server_pid"
  fi
  printf '{"gz_partition":"%s","owned_pids":[%s],"survivors":%d,"status":"%s"}\n' \
    "${GZ_PARTITION:-}" "$owned_csv" "$survivors" \
    "$([[ $survivors -eq 0 ]] && printf clean || printf leaked)" > "$cleanup_file"
}
trap cleanup EXIT INT TERM

case "$scenario" in
  distance|model-lifecycle|missing-model) ;;
  *)
    printf 'unknown scenario: %s\n' "$scenario" >&2
    exit 64
    ;;
esac

if [[ -z "${TUTORIAL_INSTALL_BASE:-}" ]]; then
  printf 'TUTORIAL_INSTALL_BASE is required\n' >&2
  exit 64
fi

install_base=$(realpath "$TUTORIAL_INSTALL_BASE")
library="$install_base/tutorial_bot_plugins/lib/libTutorialBotDiagnosticsSystem.so"
world_name=${world:-advanced-diagnostics.sdf}
world_path="$install_base/tutorial_bot_gazebo/share/tutorial_bot_gazebo/worlds/$world_name"
if [[ ! -f "$library" || ! -f "$world_path" ]]; then
  printf 'installed diagnostics assets not found\n' >&2
  exit 64
fi

export GZ_SIM_SYSTEM_PLUGIN_PATH="$install_base/tutorial_bot_plugins/lib"
export GZ_PARTITION="tutorial_bot_task9_${scenario}_$$_${RANDOM}"
status_topic="/tutorial_bot/diagnostics/status"
distance_topic="/tutorial_bot/diagnostics/distance"
if [[ "$scenario" == "model-lifecycle" || "$scenario" == "missing-model" ]]; then
  status_topic="/lifecycle_bot/diagnostics/status"
  distance_topic="/lifecycle_bot/diagnostics/distance"
fi

timeout 30 gz topic -e --json-output -d 25 -t "$status_topic" > "$evidence/status.log" 2>&1 &
capture_pids+=("$!")
timeout 30 gz topic -e --json-output -d 25 -t "$distance_topic" > "$evidence/distance.log" 2>&1 &
capture_pids+=("$!")
sleep 0.5
setsid gz sim -s "$world_path" > "$evidence/server.log" 2>&1 &
server_pid=$!

wait_pattern() {
  local path=$1
  local pattern=$2
  for _ in {1..80}; do
    grep -q "$pattern" "$path" 2>/dev/null && return 0
    kill -0 "$server_pid" 2>/dev/null || return 1
    sleep 0.1
  done
  return 1
}

for _ in {1..80}; do
  gz service -l 2>/dev/null | grep -q '/world/advanced_diagnostics/control' && break
  kill -0 "$server_pid" 2>/dev/null || exit 1
  sleep 0.1
done
gz service -s /world/advanced_diagnostics/control \
  --reqtype gz.msgs.WorldControl --reptype gz.msgs.Boolean --timeout 1000 \
  --req 'pause: false' > "$evidence/unpause.log" 2>&1

if [[ "$scenario" == "distance" ]]; then
  wait_pattern "$evidence/distance.log" '^{}$' || exit 1
  gz topic -t /model/tutorial_bot/cmd_vel -m gz.msgs.Twist \
    -p 'linear: {x: 0.5}' > "$evidence/move.log" 2>&1
  for _ in {1..80}; do
    awk -F '[:,}]' '/"data"/ {if ($2 + 0 > 0.01) found=1} END {exit found ? 0 : 1}' \
      "$evidence/distance.log" && break
    sleep 0.1
  done
  awk -F '[:,}]' '/"data"/ {if ($2 + 0 > 0.01) found=1} END {exit found ? 0 : 1}' \
    "$evidence/distance.log" || exit 1
  printf '{"scenario":"distance","status":"PASS","observed_zero":true,"observed_positive":true}\n' \
    > "$evidence/scenario.json"
  exit 0
fi

wait_pattern "$evidence/status.log" 'WAITING_FOR_MODEL' || exit 1
if [[ "$scenario" == "missing-model" ]]; then
  printf '{"scenario":"missing-model","status":"EXPECTED_FAILURE","state":"WAITING_FOR_MODEL","exit_code":20}\n' \
    > "$evidence/scenario.json"
  exit 20
fi

spawn_request='sdf: "<sdf version=\"1.10\"><model name=\"lifecycle_bot\"><static>true</static><link name=\"base_link\"/></model></sdf>"'
gz service -s /world/advanced_diagnostics/create \
  --reqtype gz.msgs.EntityFactory --reptype gz.msgs.Boolean --timeout 1000 \
  --req "$spawn_request" > "$evidence/spawn-1.log" 2>&1
wait_pattern "$evidence/status.log" 'READY' || exit 1
gz service -s /world/advanced_diagnostics/set_pose \
  --reqtype gz.msgs.Pose --reptype gz.msgs.Boolean --timeout 1000 \
  --req 'name: "lifecycle_bot", position: {x: 2}' > "$evidence/move.log" 2>&1
for _ in {1..80}; do
  awk -F '[:,}]' '/"data"/ {if ($2 + 0 > 1.9) found=1} END {exit found ? 0 : 1}' \
    "$evidence/distance.log" && break
  sleep 0.1
done
awk -F '[:,}]' '/"data"/ {if ($2 + 0 > 1.9) found=1} END {exit found ? 0 : 1}' \
  "$evidence/distance.log" || exit 1
distance_before_remove=$(awk -F '[:,}]' '/"data"/ {value=$2} END {print value}' \
  "$evidence/distance.log")
gz service -s /world/advanced_diagnostics/remove \
  --reqtype gz.msgs.Entity --reptype gz.msgs.Boolean --timeout 1000 \
  --req 'name: "lifecycle_bot", type: MODEL' > "$evidence/remove.log" 2>&1
wait_pattern "$evidence/status.log" 'MODEL_REMOVED' || exit 1
distance_while_removed=$(awk -F '[:,}]' '/"data"/ {value=$2} END {print value}' \
  "$evidence/distance.log")
awk -v before="$distance_before_remove" -v removed="$distance_while_removed" \
  'BEGIN {delta=before-removed; if (delta < 0) delta=-delta; exit delta < 1e-9 ? 0 : 1}' || exit 1
ready_before_respawn=$(grep -c '"data":"READY"' "$evidence/status.log" 2>/dev/null || true)
distance_lines_before_respawn=$(wc -l < "$evidence/distance.log")
gz service -s /world/advanced_diagnostics/create \
  --reqtype gz.msgs.EntityFactory --reptype gz.msgs.Boolean --timeout 1000 \
  --req "$spawn_request" > "$evidence/spawn-2.log" 2>&1
for _ in {1..80}; do
  [[ $(grep -c '"data":"READY"' "$evidence/status.log" 2>/dev/null || true) -gt $ready_before_respawn ]] && break
  sleep 0.1
done
[[ $(grep -c '"data":"READY"' "$evidence/status.log" 2>/dev/null || true) -gt $ready_before_respawn ]] || exit 1
tail -n "+$((distance_lines_before_respawn + 1))" "$evidence/distance.log" | grep -q '^{}$' || exit 1
printf '{"scenario":"model-lifecycle","status":"PASS","transitions":["WAITING_FOR_MODEL","READY","MODEL_REMOVED","READY"],"respawn_distance":0}\n' \
  > "$evidence/scenario.json"
