#!/usr/bin/env bash
set -eo pipefail

source /opt/ros/jazzy/setup.bash
set -u

project_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
source "$project_root/scripts/lib/owned_process.sh"
export ROS_DOMAIN_ID=$((40 + $$ % 160))
export GZ_PARTITION="tutorial_bot_beginner_sensors_${ROS_DOMAIN_ID}_$$"
owned_validate_isolation "$ROS_DOMAIN_ID" "$GZ_PARTITION"
model_sdf=$(mktemp)
server_log=$(mktemp)
lidar_message=$(mktemp)
camera_message=$(mktemp)
server_pid=''

cleanup() {
  if [ -n "$server_pid" ]; then
    owned_stop_pgid "$server_pid"
    wait "$server_pid" 2>/dev/null || true
  fi
  rm -f "$model_sdf" "$server_log" "$lidar_message" "$camera_message"
}

trap cleanup EXIT INT TERM

topic_type() {
  gz topic -i -t "$1" | awk -F ', ' '/gz\.msgs\./ { print $2; exit }'
}

xacro "$project_root/examples/ros2_ws/src/tutorial_bot_description/urdf/tutorial_bot.urdf.xacro" > "$model_sdf"
gz sdf -k "$model_sdf"
setsid gz sim -s -r "$project_root/examples/gazebo/worlds/first-world.sdf" > "$server_log" 2>&1 &
server_pid=$!

for _ in $(seq 1 30); do
  if gz service -l | grep -qx '/world/first_world/create'; then
    break
  fi
  sleep 0.2
done

if ! gz service -l | grep -qx '/world/first_world/create'; then
  sed -n '1,160p' "$server_log" >&2
  exit 1
fi

gz service -s /world/first_world/create \
  --reqtype gz.msgs.EntityFactory \
  --reptype gz.msgs.Boolean \
  --timeout 3000 \
  --req "sdf_filename: \"$model_sdf\" pose { position { z: 0.12 } }"

for _ in $(seq 1 50); do
  if gz topic -l | grep -qx '/tutorial_bot/lidar' && \
    gz topic -l | grep -qx '/tutorial_bot/camera/image'; then
    break
  fi
  sleep 0.2
done

if ! gz topic -l | grep -qx '/tutorial_bot/lidar' || \
  ! gz topic -l | grep -qx '/tutorial_bot/camera/image'; then
  gz topic -l >&2
  sed -n '1,160p' "$server_log" >&2
  exit 1
fi

if [ "$(topic_type /tutorial_bot/lidar)" != 'gz.msgs.LaserScan' ]; then
  gz topic -i -t /tutorial_bot/lidar >&2
  exit 1
fi

if [ "$(topic_type /tutorial_bot/camera/image)" != 'gz.msgs.Image' ]; then
  gz topic -i -t /tutorial_bot/camera/image >&2
  exit 1
fi

gz topic -e -t /tutorial_bot/lidar -n 1 > "$lidar_message"
gz topic -e -t /tutorial_bot/camera/image -n 1 > "$camera_message"

scan_count=$(awk '$1 == "count:" { print $2; exit }' "$lidar_message")
finite_range_count=$(awk '
  $1 == "ranges:" && $2 != "inf" && $2 != "-inf" && $2 != "nan" { count += 1 }
  END { print count + 0 }
' "$lidar_message")
image_width=$(awk '$1 == "width:" { print $2; exit }' "$camera_message")
image_height=$(awk '$1 == "height:" { print $2; exit }' "$camera_message")

if ! awk -v scan_count="$scan_count" -v finite_range_count="$finite_range_count" \
  -v image_width="$image_width" -v image_height="$image_height" \
  'BEGIN { exit !(scan_count == 360 && finite_range_count > 0 && image_width == 320 && image_height == 240) }'; then
  printf '%s\n' 'Sensor messages did not have the expected dimensions.' >&2
  exit 1
fi

printf 'LiDAR scan verified: %s ranges, %s obstacle readings.\n' "$scan_count" "$finite_range_count"
printf 'Camera image verified: %sx%s.\n' "$image_width" "$image_height"
