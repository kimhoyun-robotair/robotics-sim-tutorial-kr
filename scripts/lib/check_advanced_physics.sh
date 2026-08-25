#!/usr/bin/env bash
: "${evidence:?}" "${world_root:?}" "${scenario:?}" "${sim_seconds-}" "${worlds-}"
: "${library:?}" "${install_base:?}" "${publish_period-}" "${server_pid-}"
: "${capture_pids[*]}"
run_physics_variant() {
  local world_name=$1
  local label=$2
  local iterations=$3
  local period=$4
  local stats_pid distance_pid status_pid

  timeout 20 gz topic -e --json-output -t "/world/advanced_${label}/stats" \
    > "$evidence/$label-stats.log" 2>&1 &
  stats_pid=$!
  capture_pids+=("$stats_pid")
  timeout 20 gz topic -e --json-output -t "/tutorial_bot/$label/diagnostics/distance" \
    > "$evidence/$label-distance.log" 2>&1 &
  distance_pid=$!
  capture_pids+=("$distance_pid")
  timeout 20 gz topic -e --json-output -t "/tutorial_bot/$label/diagnostics/status" \
    > "$evidence/$label-status.log" 2>&1 &
  status_pid=$!
  capture_pids+=("$status_pid")
  sleep 0.5
  setsid gz sim -s -r --iterations "$iterations" "$world_root/$world_name" \
    > "$evidence/$label-server.log" 2>&1 &
  server_pid=$!
  wait "$server_pid" || return 1
  server_pid=""
  sleep 0.5
  kill -TERM "$stats_pid" "$distance_pid" "$status_pid" 2>/dev/null || true
  wait "$stats_pid" "$distance_pid" "$status_pid" 2>/dev/null || true
  grep -q "publish_period=$period" "$evidence/$label-server.log"
  grep -q 'state_transition.*to=READY' "$evidence/$label-server.log"
  grep -q 'READY' "$evidence/$label-status.log"
  [[ -s "$evidence/$label-stats.log" && -s "$evidence/$label-distance.log" ]]
}

if [[ "$scenario" == "physics" ]]; then
  [[ "$sim_seconds" == "2.0" && "$worlds" == "advanced-fast.sdf,advanced-slow.sdf" ]] || exit 64
  [[ -f "$library" && -f "$world_root/advanced-fast.sdf" && -f "$world_root/advanced-slow.sdf" ]] || exit 64
  export GZ_SIM_SYSTEM_PLUGIN_PATH="$install_base/tutorial_bot_plugins/lib"
  export GZ_PARTITION="tutorial_bot_task11_physics_$$_${RANDOM}"
  run_physics_variant advanced-fast.sdf fast 2000 0.05 || exit $?
  run_physics_variant advanced-slow.sdf slow 500 0.2 || exit $?
  fast_count=$(wc -l < "$evidence/fast-distance.log")
  slow_count=$(wc -l < "$evidence/slow-distance.log")
  ratio=$(awk -v fast="$fast_count" -v slow="$slow_count" \
    'BEGIN {if (slow <= 0) exit 1; ratio=fast/slow; if (ratio < 3 || ratio > 5) exit 1; print ratio}') || exit 1
  for label in fast slow; do
    awk '
      /"simTime"/ {
        line=$0; sub(/,"realTime".*/, "", line); sec=0; nsec=0
        if (line ~ /"sec"/) {part=line; sub(/.*"sec":"?/, "", part); sub(/"?[,}].*/, "", part); sec=part+0}
        if (line ~ /"nsec"/) {part=line; sub(/.*"nsec":/, "", part); sub(/[,}].*/, "", part); nsec=part+0}
        value=sec+nsec/1000000000
        if (seen && value <= previous) exit 1
        previous=value; seen=1
      }
      END {if (!seen || previous < 1.99 || previous > 2.0) exit 1}
    ' "$evidence/$label-stats.log" || exit 1
  done
  printf '{"scenario":"physics","status":"PASS","sim_seconds":2.0,"fast_messages":%d,"slow_messages":%d,"ratio":%s,"time_basis":"simulation"}\n' \
    "$fast_count" "$slow_count" "$ratio" > "$evidence/scenario.json"
  exit 0
fi

if [[ "$scenario" == "invalid-period" ]]; then
  [[ -n "$publish_period" && -f "$library" && -f "$world_root/advanced-fast.sdf" ]] || exit 64
  awk -v value="$publish_period" 'BEGIN {exit (value == value && value + 0 > 0) ? 1 : 0}' || exit 64
  export GZ_SIM_SYSTEM_PLUGIN_PATH="$install_base/tutorial_bot_plugins/lib"
  export GZ_PARTITION="tutorial_bot_task11_invalid_$$_${RANDOM}"
  sed "s#<publish_period>0.05</publish_period>#<publish_period>$publish_period</publish_period>#" \
    "$world_root/advanced-fast.sdf" > "$evidence/invalid-period.sdf"
  timeout 10 gz topic -e --json-output -t /tutorial_bot/fast/diagnostics/status \
    > "$evidence/status.log" 2>&1 &
  capture_pids+=("$!")
  timeout 10 gz topic -e --json-output -t /tutorial_bot/fast/diagnostics/distance \
    > "$evidence/distance.log" 2>&1 &
  capture_pids+=("$!")
  sleep 0.5
  setsid gz sim -s -r --iterations 50 "$evidence/invalid-period.sdf" \
    > "$evidence/server.log" 2>&1 &
  server_pid=$!
  wait "$server_pid" || exit 1
  server_pid=""
  sleep 0.5
  grep -q 'INVALID_CONFIG' "$evidence/status.log" || exit 1
  [[ ! -s "$evidence/distance.log" ]] || exit 1
  grep -q 'state=INVALID_CONFIG' "$evidence/server.log" || exit 1
  printf '{"scenario":"invalid-period","status":"EXPECTED_FAILURE","state":"INVALID_CONFIG","publish_period":"%s","distance_publisher":false,"exit_code":64}\n' \
    "$publish_period" > "$evidence/scenario.json"
  exit 64
fi
