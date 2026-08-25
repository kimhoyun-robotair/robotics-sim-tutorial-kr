#!/usr/bin/env bash
set -euo pipefail

scenario=""
evidence=""
world=""
cycles=100
sim_seconds=""
worlds=""
publish_period=""
install_base_argument=""
internal_readiness_timeout=20
sim_timeout=20
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
    --cycles)
      cycles="${2:-}"
      shift 2
      ;;
    --sim-seconds)
      sim_seconds="${2:-}"
      shift 2
      ;;
    --worlds)
      worlds="${2:-}"
      shift 2
      ;;
    --publish-period)
      publish_period="${2:-}"
      shift 2
      ;;
    --install-base)
      install_base_argument="${2:-}"
      shift 2
      ;;
    --internal-readiness-timeout)
      internal_readiness_timeout="${2:-}"
      shift 2
      ;;
    --sim-timeout)
      sim_timeout="${2:-}"
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
  distance|model-lifecycle|transport|transport-wrong-types|physics|invalid-period) ;;
  nominal|missing-model|plugin-missing|misleading-output|cleanup-reuse|timeout|sigint-hold)
    exec "$(dirname "$0")/check_advanced_headless.sh" \
      --scenario "$scenario" \
      --install-base "${install_base_argument:-${TUTORIAL_INSTALL_BASE:-}}" \
      --evidence "$evidence" \
      --internal-readiness-timeout "$internal_readiness_timeout" \
      --sim-timeout "$sim_timeout"
    ;;
  *)
    printf 'unknown scenario: %s\n' "$scenario" >&2
    exit 64
    ;;
esac

if [[ -z "${TUTORIAL_INSTALL_BASE:-}" ]]; then
  printf 'TUTORIAL_INSTALL_BASE is required\n' >&2
  exit 64
fi

install_base=$(realpath -m "$TUTORIAL_INSTALL_BASE")
library="$install_base/tutorial_bot_plugins/lib/libTutorialBotDiagnosticsSystem.so"
world_root="$install_base/tutorial_bot_gazebo/share/tutorial_bot_gazebo/worlds"

# shellcheck source=scripts/lib/check_advanced_physics.sh
source "$(dirname "$0")/lib/check_advanced_physics.sh"

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
# shellcheck source=scripts/lib/check_advanced_scenarios.sh
source "$(dirname "$0")/lib/check_advanced_scenarios.sh"
