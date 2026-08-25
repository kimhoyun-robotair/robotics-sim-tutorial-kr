#!/usr/bin/env bash

owned_process_start_ticks() {
  local pid=${1:?pid required}
  awk '{print $22}' "/proc/$pid/stat" 2>/dev/null
}

owned_validate_isolation() {
  local domain_id=${1:?ROS domain id required}
  local partition=${2:?Gazebo partition required}
  [[ $domain_id =~ ^[0-9]+$ && $partition == tutorial_bot_* ]]
}

owned_stop_pgid() {
  local pgid=${1:?process group required}
  [[ $pgid =~ ^[1-9][0-9]*$ ]] || return 64
  kill -TERM -- "-$pgid" 2>/dev/null || true
  local attempt
  for attempt in {1..50}; do
    ps -eo pgid= | awk -v target="$pgid" '$1 == target {found=1} END {exit found ? 0 : 1}' || return 0
    sleep 0.1
  done
  kill -KILL -- "-$pgid" 2>/dev/null || true
}

owned_start_pgid() {
  local output_name=${1:?output variable required}
  shift
  setsid "$@" &
  local child_pid=$!
  printf -v "$output_name" '%s' "$child_pid"
}
