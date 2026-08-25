#!/usr/bin/env bash
: "${world_path:?}" "${evidence:?}" "${scenario:?}" "${cycles:?}" "${server_pid-}"
: "${capture_pids[*]}"
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

latest_distance() {
  awk -F '[:,}]' '/^\{\}$/ {value=0} /"data"/ {value=$2 + 0} END {print value + 0}' \
    "$evidence/distance.log"
}

wait_distance_greater_than() {
  local threshold=$1
  for _ in {1..80}; do
    awk -F '[:,}]' -v threshold="$threshold" \
      '/"data"/ {if ($2 + 0 > threshold) found=1} END {exit found ? 0 : 1}' \
      "$evidence/distance.log" && return 0
    kill -0 "$server_pid" 2>/dev/null || return 1
    sleep 0.1
  done
  return 1
}

wait_new_status() {
  local expected=$1
  local previous=$2
  for _ in {1..80}; do
    [[ $(grep -c "\"data\":\"$expected\"" "$evidence/status.log" 2>/dev/null || true) -gt $previous ]] && return 0
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

if [[ "$scenario" == "transport" ]]; then
  wait_pattern "$evidence/status.log" 'READY' || exit 1
  gz service -s /world/advanced_diagnostics/set_pose \
    --reqtype gz.msgs.Pose --reptype gz.msgs.Boolean --timeout 1000 \
    --req 'name: "tutorial_bot", position: {x: 1}' > "$evidence/move-enabled.log" 2>&1
  wait_distance_greater_than 0.9 || exit 1
  enabled_distance=$(latest_distance)

  disabled_before=$(grep -c '"data":"DISABLED"' "$evidence/status.log" 2>/dev/null || true)
  gz topic -t /tutorial_bot/diagnostics/enable -m gz.msgs.Boolean \
    -p 'data: false' > "$evidence/disable.log" 2>&1
  wait_new_status DISABLED "$disabled_before" || exit 1
  disabled_start=$(latest_distance)
  gz service -s /world/advanced_diagnostics/set_pose \
    --reqtype gz.msgs.Pose --reptype gz.msgs.Boolean --timeout 1000 \
    --req 'name: "tutorial_bot", position: {x: 5}' > "$evidence/move-disabled.log" 2>&1
  sleep 0.3
  disabled_end=$(latest_distance)
  awk -v start="$disabled_start" -v end="$disabled_end" \
    'BEGIN {delta=start-end; if (delta < 0) delta=-delta; exit delta <= 1e-6 ? 0 : 1}' || exit 1

  ready_before=$(grep -c '"data":"READY"' "$evidence/status.log" 2>/dev/null || true)
  gz topic -t /tutorial_bot/diagnostics/enable -m gz.msgs.Boolean \
    -p 'data: true' > "$evidence/reenable.log" 2>&1
  wait_new_status READY "$ready_before" || exit 1
  reenabled_distance=$(latest_distance)
  awk -v before="$disabled_end" -v after="$reenabled_distance" \
    'BEGIN {delta=before-after; if (delta < 0) delta=-delta; exit delta <= 1e-6 ? 0 : 1}' || exit 1
  gz service -s /world/advanced_diagnostics/set_pose \
    --reqtype gz.msgs.Pose --reptype gz.msgs.Boolean --timeout 1000 \
    --req 'name: "tutorial_bot", position: {x: 6}' > "$evidence/move-reenabled.log" 2>&1
  awk -v baseline="$reenabled_distance" 'BEGIN {print baseline + 0.9}' > "$evidence/resume-threshold.txt"
  wait_distance_greater_than "$(< "$evidence/resume-threshold.txt")" || exit 1

  gz service -s /tutorial_bot/diagnostics/reset \
    --reqtype gz.msgs.Empty --reptype gz.msgs.Boolean --timeout 1000 \
    --req '' > "$evidence/reset.log" 2>&1
  grep -q 'data: true' "$evidence/reset.log" || exit 1
  for _ in {1..80}; do
    awk -v value="$(latest_distance)" 'BEGIN {exit value <= 1e-6 ? 0 : 1}' && break
    sleep 0.1
  done
  reset_distance=$(latest_distance)
  awk -v value="$reset_distance" 'BEGIN {exit value <= 1e-6 ? 0 : 1}' || exit 1

  : > "$evidence/cycles.log"
  completed=0
  while (( completed < cycles )); do
    batch_pids=()
    for _ in {1..2}; do
      (( completed + ${#batch_pids[@]} >= cycles )) && break
      gz service -s /tutorial_bot/diagnostics/reset \
        --reqtype gz.msgs.Empty --reptype gz.msgs.Boolean --timeout 5000 --req '' \
        >> "$evidence/cycles.log" 2>&1 &
      batch_pids+=("$!")
      capture_pids+=("$!")
    done
    for pid in "${batch_pids[@]}"; do
      wait "$pid" || exit 1
    done
    completed=$(( completed + ${#batch_pids[@]} ))
  done
  [[ $(grep -c 'data: true' "$evidence/cycles.log") -eq $cycles ]] || exit 1
  kill -0 "$server_pid" 2>/dev/null || exit 1
  printf '{"scenario":"transport","status":"PASS","cycles":%d,"enabled_distance":%s,"disabled_start":%s,"disabled_end":%s,"reenabled_distance":%s,"reset_distance":%s}\n' \
    "$cycles" "$enabled_distance" "$disabled_start" "$disabled_end" "$reenabled_distance" "$reset_distance" \
    > "$evidence/scenario.json"
  exit 0
fi

if [[ "$scenario" == "transport-wrong-types" ]]; then
  wait_pattern "$evidence/status.log" 'READY' || exit 1
  started_ms=$(date +%s%3N)
  set +e
  timeout 4 gz topic -t /tutorial_bot/diagnostics/enable -m gz.msgs.StringMsg \
    -p 'data: "wrong"' > "$evidence/wrong-subscription.log" 2>&1
  wrong_subscription_exit=$?
  set -e
  wrong_subscription_ms=$(( $(date +%s%3N) - started_ms ))
  (( wrong_subscription_ms <= 5000 )) || exit 1

  started_ms=$(date +%s%3N)
  set +e
  timeout 4 gz service -s /tutorial_bot/diagnostics/reset \
    --reqtype gz.msgs.StringMsg --reptype gz.msgs.Boolean --timeout 1000 \
    --req 'data: "wrong"' > "$evidence/wrong-request.log" 2>&1
  wrong_request_exit=$?
  set -e
  wrong_request_ms=$(( $(date +%s%3N) - started_ms ))
  (( wrong_request_ms <= 5000 )) || exit 1
  grep -q 'Service call timed out' "$evidence/wrong-request.log" || exit 1

  status_lines=$(wc -l < "$evidence/status.log")
  for _ in {1..50}; do
    [[ $(wc -l < "$evidence/status.log") -gt $status_lines ]] && break
    kill -0 "$server_pid" 2>/dev/null || exit 1
    sleep 0.1
  done
  [[ $(wc -l < "$evidence/status.log") -gt $status_lines ]] || exit 1
  grep '"data":"READY"' "$evidence/status.log" | tail -n 1 \
    > "$evidence/valid-status.log"
  grep -q 'READY' "$evidence/valid-status.log" || exit 1
  printf '{"scenario":"transport-wrong-types","status":"PASS","wrong_subscription_exit":%d,"wrong_subscription_ms":%d,"wrong_request_exit":%d,"wrong_request_ms":%d,"plugin_alive":true}\n' \
    "$wrong_subscription_exit" "$wrong_subscription_ms" "$wrong_request_exit" "$wrong_request_ms" \
    > "$evidence/scenario.json"
  exit 0
fi

if [[ "$scenario" == "distance" ]]; then
  wait_pattern "$evidence/distance.log" '^{}$' || exit 1
  gz service -s /world/advanced_diagnostics/set_pose \
    --reqtype gz.msgs.Pose --reptype gz.msgs.Boolean --timeout 1000 \
    --req 'name: "tutorial_bot", position: {x: 1}' > "$evidence/move.log" 2>&1
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
