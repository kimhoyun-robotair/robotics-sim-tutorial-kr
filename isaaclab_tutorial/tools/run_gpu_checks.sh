#!/usr/bin/env bash
# Run from the Python 3.12 Isaac Lab environment prepared in steps 04–05.
set -euo pipefail

: "${ISAACLAB_ROOT:?먼저 ISAACLAB_ROOT를 IsaacLab 설치 경로로 지정한다}"
tutorial_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
output_dir="${1:-$tutorial_dir/outputs/gpu-$(date -u +%Y%m%dT%H%M%SZ)}"
mkdir -p "$output_dir"
output_dir="$(cd -- "$output_dir" && pwd)"

python "$tutorial_dir/tools/preflight.py" \
  --isaaclab-root "$ISAACLAB_ROOT" --output "$output_dir/preflight.json"

cd -- "$ISAACLAB_ROOT"
run_check() {
  local label="$1"
  shift
  printf 'RUN %s\n' "$label"
  # A slow first shader build may require raising this timeout on the user's PC.
  timeout "${ISAACLAB_CHECK_TIMEOUT:-900}" ./isaaclab.sh -p "$@" 2>&1 | tee "$output_dir/$label.log"
}

run_check p01 "$tutorial_dir/examples/p01_lit_scene.py" --steps 120 --viz none
run_check p02 "$tutorial_dir/examples/p02_stable_rigid.py" --steps 600 --viz none --output "$output_dir/rigid.json"
run_check p03 "$tutorial_dir/examples/p03_hold_franka.py" --steps 600 --viz none --output "$output_dir/franka.json"
run_check p04 "$tutorial_dir/examples/p04_camera_check.py" --steps 120 --viz none --enable_cameras --output-dir "$output_dir/camera"

printf 'All four runtime programs exited successfully. Inspect RGB and the robot in Kit before accepting visual quality.\n'
printf 'Reports: %s\n' "$output_dir"
