#!/usr/bin/env bash
set -uo pipefail

project_root=$(cd -- "$(dirname -- "$0")/.." && pwd)
source "$project_root/scripts/lib/owned_process.sh"

scenario=""
install_base=""
evidence=""
readiness_timeout=20
sim_timeout=20
owned_pids=()
owned_ticks=()
exit_code=1
signal_exit=0

while (( $# > 0 )); do
  case "$1" in
    --scenario) scenario="${2:-}"; shift 2 ;;
    --install-base) install_base="${2:-}"; shift 2 ;;
    --evidence) evidence="${2:-}"; shift 2 ;;
    --internal-readiness-timeout) readiness_timeout="${2:-}"; shift 2 ;;
    --sim-timeout) sim_timeout="${2:-}"; shift 2 ;;
    *) printf 'unknown argument: %s\n' "$1" >&2; exit 64 ;;
  esac
done

if [[ -z "$scenario" || -z "$install_base" || -z "$evidence" ]] ||
   ! [[ "$readiness_timeout" =~ ^[0-9]+$ && "$sim_timeout" =~ ^[0-9]+$ ]] ||
   (( readiness_timeout < 1 || sim_timeout < 1 )); then
  printf 'invalid headless checker arguments\n' >&2
  exit 64
fi

mkdir -p "$evidence"
install_base=$(realpath -m "$install_base")

process_ticks() {
  awk '{print $22}' "/proc/$1/stat" 2>/dev/null
}

register_process() {
  local pid=$1
  local ticks
  ticks=$(process_ticks "$pid") || return 1
  owned_pids+=("$pid")
  owned_ticks+=("$ticks")
}

# shellcheck disable=SC2317  # Invoked indirectly by EXIT, INT, and TERM traps.
cleanup() {
  local index pid expected actual survivors=0 identity_mismatch=0
  local survivor_json=""
  trap - EXIT INT TERM
  for (( index=${#owned_pids[@]}-1; index>=0; index-- )); do
    pid=${owned_pids[$index]}
    expected=${owned_ticks[$index]}
    actual=$(process_ticks "$pid")
    if [[ -n "$actual" && "$actual" != "$expected" ]]; then
      identity_mismatch=1
      continue
    fi
    if [[ -n "$actual" ]]; then
      kill -INT -- "-$pid" 2>/dev/null || kill -INT "$pid" 2>/dev/null || true
    fi
  done
  for _ in {1..30}; do
    survivors=0
    for (( index=0; index<${#owned_pids[@]}; index++ )); do
      pid=${owned_pids[$index]}
      [[ "$(process_ticks "$pid")" == "${owned_ticks[$index]}" ]] && survivors=$((survivors + 1))
    done
    (( survivors == 0 )) && break
    sleep 0.1
  done
  for (( index=0; index<${#owned_pids[@]}; index++ )); do
    pid=${owned_pids[$index]}
    expected=${owned_ticks[$index]}
    if [[ "$(process_ticks "$pid")" == "$expected" ]]; then
      owned_stop_pgid "$pid"
      wait "$pid" 2>/dev/null || true
    fi
    if [[ "$(process_ticks "$pid")" == "$expected" ]]; then
      survivor_json="${survivor_json}${survivor_json:+,}$pid"
    fi
  done
  if [[ -z "$survivor_json" ]]; then
    survivors=0
  else
    survivors=$(awk -F, '{print NF}' <<< "$survivor_json")
  fi
  printf '{"scenario":"%s","owned_pids":[%s],"survivors":[%s],"identity_mismatch":%s,"status":"%s"}\n' \
    "$scenario" "$(IFS=,; printf '%s' "${owned_pids[*]}")" "$survivor_json" \
    "$([[ $identity_mismatch -eq 0 ]] && printf false || printf true)" \
    "$([[ $survivors -eq 0 && $identity_mismatch -eq 0 ]] && printf clean || printf failed)" \
    > "$evidence/cleanup.json"
  if (( survivors > 0 || identity_mismatch > 0 )); then
    exit 70
  fi
  if (( signal_exit > 0 )); then
    exit "$signal_exit"
  fi
  exit "$exit_code"
}

trap 'signal_exit=130; cleanup' INT
trap 'signal_exit=143; cleanup' TERM
trap cleanup EXIT

library="$install_base/tutorial_bot_plugins/lib/libTutorialBotDiagnosticsSystem.so"
world="$install_base/tutorial_bot_gazebo/share/tutorial_bot_gazebo/worlds/advanced-diagnostics.sdf"
bridge="$install_base/tutorial_bot_bringup/share/tutorial_bot_bringup/config/bridge.yaml"

case "$scenario" in
  plugin-missing)
    missing_library="$evidence/missing/libTutorialBotDiagnosticsSystem.so"
    sed "s#libTutorialBotDiagnosticsSystem.so#$missing_library#g" "$world" \
      > "$evidence/plugin-missing.sdf"
    export GZ_PARTITION="tutorial_bot_task12_plugin_missing_$$_${RANDOM}"
    setsid gz sim -s -r --iterations 5 "$evidence/plugin-missing.sdf" \
      > "$evidence/server.log" 2>&1 &
    plugin_server_pid=$!
    register_process "$plugin_server_pid" || exit 70
    wait "$plugin_server_pid" 2>/dev/null || true
    grep -q 'Failed to load system plugin' "$evidence/server.log" || exit 1
    printf '{"scenario":"plugin-missing","asset":"%s","asset_exists":false,"launch_attempted":true,"exit_code":21}\n' \
      "$missing_library" > "$evidence/scenario.json"
    exit_code=21
    exit "$exit_code"
    ;;
  cleanup-reuse)
    owned_pids+=("$$")
    owned_ticks+=("0")
    exit_code=0
    exit "$exit_code"
    ;;
  misleading-output)
    printf 'PASS nominal displacement=1.0 reset=0.0\n' > "$evidence/server.log"
    printf '{"scenario":"misleading-output","live_samples":false,"exit_code":1}\n' > "$evidence/scenario.json"
    exit_code=1
    exit "$exit_code"
    ;;
esac

if [[ ! -f "$world" || ! -f "$bridge" ]]; then
  printf 'installed headless assets not found\n' >&2
  exit_code=64
  exit "$exit_code"
fi
if [[ ! -f "$library" ]]; then
  printf 'installed diagnostics plugin not found\n' >&2
  exit_code=21
  exit "$exit_code"
fi

export GZ_SIM_SYSTEM_PLUGIN_PATH="$install_base/tutorial_bot_plugins/lib"
export GZ_PARTITION="tutorial_bot_task12_$$_${RANDOM}"
if [[ "$scenario" == "missing-model" ]]; then
  sed 's/<model name="tutorial_bot">/<model name="unrelated_bot">/' "$world" \
    > "$evidence/missing-model.sdf"
  world="$evidence/missing-model.sdf"
fi
setsid gz sim -s "$world" > "$evidence/server.log" 2>&1 &
server_pid=$!
register_process "$server_pid" || exit 70

if [[ "$scenario" == "timeout" ]]; then
  printf '{"scenario":"timeout","deadline_seconds":%d,"deadline_source":"internal-readiness-timeout","exit_code":124}\n' \
    "$readiness_timeout" > "$evidence/scenario.json"
  for (( elapsed=0; elapsed<readiness_timeout; elapsed++ )); do sleep 1; done
  exit_code=124
  exit "$exit_code"
fi

if [[ "$scenario" == "sigint-hold" ]]; then
  for (( elapsed=0; elapsed<readiness_timeout*10; elapsed++ )); do
    if gz service -l 2>/dev/null | grep -q '/world/advanced_diagnostics/control'; then
      printf '{"scenario":"sigint-hold","ready":true}\n' > "$evidence/scenario.json"
      while true; do sleep 1; done
    fi
    sleep 0.1
  done
  exit_code=124
  exit "$exit_code"
fi

if [[ "$scenario" == "missing-model" ]]; then
  setsid timeout "$readiness_timeout" gz topic -e --json-output -t /lifecycle_bot/diagnostics/status \
    > "$evidence/status.log" 2>&1 &
  status_pid=$!
  register_process "$status_pid" || exit 70
  gz service -s /world/advanced_diagnostics/control --reqtype gz.msgs.WorldControl \
    --reptype gz.msgs.Boolean --timeout 1000 --req 'pause: false' > "$evidence/unpause.log" 2>&1 || true
  for (( elapsed=0; elapsed<readiness_timeout*10; elapsed++ )); do
    if grep -q WAITING_FOR_MODEL "$evidence/status.log" 2>/dev/null; then
      printf '{"scenario":"missing-model","state":"WAITING_FOR_MODEL","exit_code":20}\n' > "$evidence/scenario.json"
      exit_code=20
      exit "$exit_code"
    fi
    sleep 0.1
  done
  exit_code=124
  exit "$exit_code"
fi

setsid timeout "$sim_timeout" gz topic -e --json-output -t /tutorial_bot/diagnostics/distance \
  > "$evidence/distance.log" 2>&1 &
distance_pid=$!
register_process "$distance_pid" || exit 70
setsid timeout "$sim_timeout" gz topic -e --json-output -t /world/advanced_diagnostics/stats \
  > "$evidence/stats.log" 2>&1 &
stats_pid=$!
register_process "$stats_pid" || exit 70
setsid ros2 run ros_gz_bridge parameter_bridge \
  '/world/advanced_diagnostics/pose/info@geometry_msgs/msg/PoseArray[gz.msgs.Pose_V' \
  > "$evidence/bridge.log" 2>&1 &
bridge_pid=$!
register_process "$bridge_pid" || exit 70
setsid ros2 topic echo /world/advanced_diagnostics/pose/info geometry_msgs/msg/PoseArray \
  --filter 'len(m.poses) > 0' \
  > "$evidence/ros-pose.log" 2>&1 &
pose_pid=$!
register_process "$pose_pid" || exit 70

for (( elapsed=0; elapsed<readiness_timeout*10; elapsed++ )); do
  gz service -l 2>/dev/null | grep -q '/world/advanced_diagnostics/control' && break
  sleep 0.1
done
gz service -s /world/advanced_diagnostics/control --reqtype gz.msgs.WorldControl \
  --reptype gz.msgs.Boolean --timeout 1000 --req 'pause: false' > "$evidence/unpause.log" 2>&1 || true
gz topic -t /model/tutorial_bot/cmd_vel -m gz.msgs.Twist -p 'linear: {x: 0.5}' \
  > "$evidence/command.log" 2>&1

for (( elapsed=0; elapsed<sim_timeout*10; elapsed++ )); do
  plugin_distance=$(awk -F '[:,}]' '/"data"/ {value=$2+0} END {print value+0}' "$evidence/distance.log" 2>/dev/null)
  awk -v value="${plugin_distance:-0}" 'BEGIN {exit value >= 0.10 ? 0 : 1}' && break
  sleep 0.1
done

ros_displacement=$(awk '
  /^---$/ {pose_index=0; in_position=0}
  /^- position:/ {pose_index++; in_position=1}
  /^  orientation:/ {in_position=0}
  in_position && /^    x:/ {x=$2+0}
  in_position && /^    y:/ {
    y=$2+0
    if (!(pose_index in seen)) {first_x[pose_index]=x; first_y[pose_index]=y; seen[pose_index]=1}
    dx=x-first_x[pose_index]; dy=y-first_y[pose_index]; distance=sqrt(dx*dx+dy*dy)
    if (distance > maximum) maximum=distance
  }
  END {print maximum+0}
' "$evidence/ros-pose.log")
gz topic -t /model/tutorial_bot/cmd_vel -m gz.msgs.Twist -p 'linear: {x: 0}' \
  > "$evidence/stop-command.log" 2>&1
distance_lines_before_reset=$(wc -l < "$evidence/distance.log")
gz service -s /tutorial_bot/diagnostics/reset --reqtype gz.msgs.Empty \
  --reptype gz.msgs.Boolean --timeout 1000 --req '' > "$evidence/reset.log" 2>&1
for _ in {1..30}; do
  reset_distance=$(tail -n "+$((distance_lines_before_reset + 1))" "$evidence/distance.log" | \
    awk '/^\{\}$/ {minimum=0; seen=1} /"data"/ {line=$0; sub(/.*"data":/, "", line); sub(/}.*/, "", line); value=line+0; if (!seen || value < minimum) minimum=value; seen=1} END {print seen ? minimum : 1}')
  awk -v value="$reset_distance" 'BEGIN {exit value <= 0.000001 ? 0 : 1}' && break
  sleep 0.1
done
sim_seconds=$(awk '/"simTime"/ {line=$0; sub(/.*"sec":"?/,"",line); sub(/"?[,}].*/,"",line); value=line+0} END {print value+0}' "$evidence/stats.log")

if awk -v ros="$ros_displacement" -v plugin="${plugin_distance:-0}" -v reset="${reset_distance:-1}" \
  'BEGIN {exit ros >= 0.10 && plugin >= 0.10 && reset <= 0.000001 ? 0 : 1}'; then
  printf '{"scenario":"nominal","status":"PASS","sim_seconds":%s,"ros_planar_displacement":%s,"plugin_distance":%s,"reset_response":true,"post_reset_distance":%s}\n' \
    "${sim_seconds:-0}" "$ros_displacement" "${plugin_distance:-0}" "${reset_distance:-1}" > "$evidence/scenario.json"
  exit_code=0
else
  printf '{"scenario":"nominal","status":"FAIL","sim_seconds":%s,"ros_planar_displacement":%s,"plugin_distance":%s,"post_reset_distance":%s}\n' \
    "${sim_seconds:-0}" "$ros_displacement" "${plugin_distance:-0}" "${reset_distance:-1}" > "$evidence/scenario.json"
  exit_code=1
fi
exit "$exit_code"
