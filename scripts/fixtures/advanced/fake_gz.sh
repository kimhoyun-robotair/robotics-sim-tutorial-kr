#!/usr/bin/env bash
set -euo pipefail

printf '%s\n' "$*" >> "$FAKE_GZ_CALLS"
if [[ "${1:-}" == "topic" && "${2:-}" == "-e" ]]; then
  if [[ "$*" == *diagnostics/status* ]]; then
    printf '{"data":"READY"}\n'
  else
    printf '{}\n{"data":1}\n'
  fi
  sleep 30
elif [[ "${1:-}" == "sim" ]]; then
  sleep 30
elif [[ "${1:-}" == "service" && "${2:-}" == "-l" ]]; then
  printf '/world/advanced_diagnostics/control\n'
else
  printf 'data: true\n'
fi
