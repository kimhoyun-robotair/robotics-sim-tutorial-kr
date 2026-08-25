#!/usr/bin/env bash
set -eo pipefail

source /opt/ros/jazzy/setup.bash
set -u

project_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
source "$project_root/scripts/lib/owned_process.sh"
export ROS_DOMAIN_ID=$((40 + $$ % 160))
export GZ_PARTITION="tutorial_bot_beginner_fuel_${ROS_DOMAIN_ID}_$$"
owned_validate_isolation "$ROS_DOMAIN_ID" "$GZ_PARTITION"
fuel_uri='https://fuel.gazebosim.org/1.0/OpenRobotics/models/Coke'
fuel_cache=$(mktemp -d)
server_log=$(mktemp)
server_pid=''

cleanup() {
  if [ -n "$server_pid" ]; then
    owned_stop_pgid "$server_pid"
    wait "$server_pid" 2>/dev/null || true
  fi
  if [ -d "$fuel_cache" ]; then
    rm -r -- "$fuel_cache"
  fi
  rm -f "$server_log"
}

trap cleanup EXIT INT TERM

export GZ_FUEL_CACHE_PATH="$fuel_cache"
gz fuel download -u "$fuel_uri"

if ! find "$fuel_cache" -type f -name model.config -print -quit | grep -q .; then
  printf '%s\n' 'Fuel download did not produce model.config.' >&2
  exit 1
fi

setsid gz sim -s -r "$project_root/examples/gazebo/worlds/fuel-world.sdf" > "$server_log" 2>&1 &
server_pid=$!

for _ in $(seq 1 50); do
  if gz service -l | grep -qx '/world/fuel_world/create'; then
    break
  fi
  sleep 0.2
done

if ! gz service -l | grep -qx '/world/fuel_world/create'; then
  sed -n '1,160p' "$server_log" >&2
  exit 1
fi

model_list=$(gz model --list)
printf '%s\n' "$model_list"

if ! printf '%s\n' "$model_list" | grep -Eq '^[[:space:]]*-[[:space:]]+fuel_coke$'; then
  printf '%s\n' 'Fuel model was not present in the running world.' >&2
  exit 1
fi

printf '%s\n' 'Fuel model include verified.'
