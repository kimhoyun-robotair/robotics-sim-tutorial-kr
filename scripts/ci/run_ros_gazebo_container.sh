#!/usr/bin/env bash
set -euo pipefail

source_root=""
evidence=""
scenario=""
internal_timeout=10
image=${TUTORIAL_CI_IMAGE:-gazebo-tutorial-kr:ubuntu24.04-jazzy-harmonic}
container="gazebo-task14-$$_${RANDOM}"
owned=false
exit_code=0

while (($#)); do
  case "$1" in
    --source) source_root=${2:-}; shift 2 ;;
    --evidence) evidence=${2:-}; shift 2 ;;
    --scenario) scenario=${2:-}; shift 2 ;;
    --internal-timeout) internal_timeout=${2:-}; shift 2 ;;
    *) printf 'unknown argument: %s\n' "$1" >&2; exit 64 ;;
  esac
done

case "$scenario" in
  nominal|plugin-missing|timeout|sigint-hold) ;;
  *) printf 'unknown scenario: %s\n' "${scenario:-}" >&2; exit 64 ;;
esac
if [[ ! "$internal_timeout" =~ ^[1-9][0-9]*$ ]] || [[ -z "$source_root" || -z "$evidence" ]]; then
  printf 'invalid container arguments\n' >&2
  exit 64
fi
command -v docker >/dev/null || { printf 'docker runtime not found\n' >&2; exit 69; }
if [[ ! -f "$source_root/scripts/ci/Dockerfile.ubuntu24.04" ]]; then
  printf 'container source not found\n' >&2
  exit 64
fi
source_root=$(realpath "$source_root")
mkdir -p "$evidence"
evidence=$(realpath "$evidence")
cache=${TUTORIAL_CI_CCACHE:-${XDG_CACHE_HOME:-$HOME/.cache}/gazebo-tutorial-task14-ccache}
mkdir -p "$cache"
cache=$(realpath "$cache")

# shellcheck disable=SC2317
cleanup() {
  local survivors='[]' status=clean
  trap - EXIT INT TERM
  if [[ "$owned" == true ]] && docker inspect "$container" >/dev/null 2>&1; then
    docker rm -f "$container" >/dev/null 2>&1 || true
  fi
  if docker inspect "$container" >/dev/null 2>&1; then
    survivors="[\"$container\"]"
    status=failed
    exit_code=70
  fi
  printf '{"container":"%s","image":"%s","survivors":%s,"status":"%s"}\n' \
    "$container" "$image" "$survivors" "$status" > "$evidence/container-cleanup.json"
  exit "$exit_code"
}
# shellcheck disable=SC2317
interrupt() {
  exit_code=130
  docker kill --signal INT "$container" >/dev/null 2>&1 || true
  cleanup
}
trap cleanup EXIT TERM
trap interrupt INT

if ! docker image inspect "$image" >/dev/null 2>&1; then
  docker build --label gazebo-tutorial.task=14 -t "$image" -f "$source_root/scripts/ci/Dockerfile.ubuntu24.04" "$source_root"
fi
docker run --name "$container" --label gazebo-tutorial.task=14 \
  --network bridge --read-only --tmpfs /work:exec,size=4g --tmpfs /tmp:exec,size=512m \
  -e HOME=/tmp \
  -v "$source_root:/source:ro" -v "$evidence:/evidence" -v "$cache:/ccache" \
  "$image" --source /source --evidence /evidence --scenario "$scenario" --internal-timeout "$internal_timeout" &
docker_pid=$!
owned=true
set +e
wait "$docker_pid"
exit_code=$?
set -e
exit "$exit_code"
