#!/usr/bin/env bash
set -euo pipefail

scenario=""
evidence=""

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
  printf '{"owned_paths":[],"owned_pids":[],"survivors":0,"status":"clean"}\n' > "$cleanup_file"
}
trap cleanup EXIT INT TERM

printf '{"scenario":"%s","status":"unavailable","exit_code":64}\n' "$scenario" > "$evidence/scenario.json"
printf 'scenario unavailable: %s\n' "$scenario" >&2
exit 64
