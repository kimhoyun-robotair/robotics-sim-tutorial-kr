#!/usr/bin/env bash
set -eo pipefail

unset COLCON_CURRENT_PREFIX
source /opt/ros/jazzy/setup.bash
set -u

project_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
source "$project_root/scripts/lib/owned_process.sh"
bridge_config="$project_root/examples/ros2_ws/src/tutorial_bot_bringup/config/bridge.yaml"
evidence=''
preflight_only=false
required_packages=(ros_gz_bridge ros_gz_image xacro)

while [ "$#" -gt 0 ]; do
  case "$1" in
    --config)
      bridge_config=$2
      shift 2
      ;;
    --evidence)
      evidence=$2
      shift 2
      ;;
    --preflight-only)
      preflight_only=true
      shift
      ;;
    --require-package)
      required_packages+=("$2")
      shift 2
      ;;
    *)
      printf 'unknown argument: %s\n' "$1" >&2
      exit 64
      ;;
  esac
done

if [ -n "$evidence" ]; then
  mkdir -p "$evidence"
  : > "$evidence/dependencies.log"
fi

missing_packages=()
for package in "${required_packages[@]}"; do
  if prefix=$(ros2 pkg prefix "$package" 2>&1); then
    [ -z "$evidence" ] || printf '%s=%s\n' "$package" "$prefix" >> "$evidence/dependencies.log"
  else
    missing_packages+=("$package")
    [ -z "$evidence" ] || printf '%s=MISSING:%s\n' "$package" "$prefix" >> "$evidence/dependencies.log"
  fi
done
if [ "${#missing_packages[@]}" -gt 0 ]; then
  for package in "${missing_packages[@]}"; do
    printf 'missing ROS package %s; install with: sudo apt install ros-jazzy-%s\n' \
      "$package" "${package//_/-}" >&2
  done
  [ -z "$evidence" ] || printf '{"schema_version":1,"status":"fail","survivors":[]}\n' > "$evidence/cleanup.json"
  exit 2
fi
if [ "$preflight_only" = true ]; then
  printf '%s\n' 'Bridge dependency preflight passed.'
  [ -z "$evidence" ] || printf '{"schema_version":1,"status":"pass","survivors":[]}\n' > "$evidence/cleanup.json"
  exit 0
fi

if [ ! -f "$bridge_config" ]; then
  printf 'bridge config not found: %s\n' "$bridge_config" >&2
  exit 64
fi
if ! python3 - "$bridge_config" <<'PY'
from pathlib import Path
import sys
import yaml

entries = yaml.safe_load(Path(sys.argv[1]).read_text(encoding="utf-8"))
topics = {entry.get("ros_topic_name", entry.get("topic_name")) for entry in entries}
raise SystemExit(0 if "/scan" in topics else 1)
PY
then
  printf '%s\n' 'missing ROS topic /scan' >&2
  if [ -n "$evidence" ]; then
    printf '%s\n' 'missing ROS topic /scan' > "$evidence/observable.log"
    printf '{"schema_version":1,"status":"fail","error":"missing ROS topic /scan"}\n' > "$evidence/result.json"
    printf '{"schema_version":1,"status":"fail","survivors":[]}\n' > "$evidence/cleanup.json"
  fi
  exit 1
fi

export ROS_DOMAIN_ID=$((40 + $$ % 160))
export GZ_PARTITION="tutorial_bot_beginner_bridge_${ROS_DOMAIN_ID}_$$"
owned_validate_isolation "$ROS_DOMAIN_ID" "$GZ_PARTITION"
model_sdf=$(mktemp)
server_log=$(mktemp)
bridge_log=$(mktemp)
image_bridge_log=$(mktemp)
odom_message=$(mktemp)
scan_message=$(mktemp)
imu_message=$(mktemp)
image_message=$(mktemp)
clock_message=$(mktemp)
server_pid=''
bridge_pid=''
image_bridge_pid=''
run_status=fail
owned_roots=''

cleanup() {
  for task_pid in "$image_bridge_pid" "$bridge_pid" "$server_pid"; do
    if [ -n "$task_pid" ]; then
      owned_stop_pgid "$task_pid"
      wait "$task_pid" 2>/dev/null || true
    fi
  done
  rm -f "$model_sdf" "$server_log" "$bridge_log" "$image_bridge_log" \
    "$odom_message" "$scan_message" "$imu_message" "$image_message" "$clock_message"
  if [ -n "$evidence" ]; then
    printf '{"schema_version":1,"status":"%s","owned_roots":[%s],"survivors":[]}\n' \
      "$run_status" "$owned_roots" > "$evidence/cleanup.json"
  fi
}

interrupted() {
  run_status=interrupted
  exit 130
}

trap cleanup EXIT
trap interrupted INT TERM

xacro "$project_root/examples/ros2_ws/src/tutorial_bot_description/urdf/tutorial_bot.urdf.xacro" > "$model_sdf"
setsid gz sim -s -r "$project_root/examples/gazebo/worlds/first-world.sdf" > "$server_log" 2>&1 &
server_pid=$!
owned_roots=$server_pid

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
    gz topic -l | grep -qx '/tutorial_bot/imu' && \
    gz topic -l | grep -qx '/tutorial_bot/camera/image'; then
    break
  fi
  sleep 0.2
done

setsid ros2 run ros_gz_bridge parameter_bridge --ros-args -p config_file:="$bridge_config" > "$bridge_log" 2>&1 &
bridge_pid=$!
owned_roots="$owned_roots,$bridge_pid"
setsid ros2 run ros_gz_image image_bridge /tutorial_bot/camera/image > "$image_bridge_log" 2>&1 &
image_bridge_pid=$!
owned_roots="$owned_roots,$image_bridge_pid"

for _ in $(seq 1 50); do
  ros_topics=$(ros2 topic list)
  if printf '%s\n' "$ros_topics" | grep -qx '/clock' && \
    printf '%s\n' "$ros_topics" | grep -qx '/cmd_vel' && \
    printf '%s\n' "$ros_topics" | grep -qx '/odom' && \
    printf '%s\n' "$ros_topics" | grep -qx '/scan' && \
    printf '%s\n' "$ros_topics" | grep -qx '/imu' && \
    printf '%s\n' "$ros_topics" | grep -qx '/tutorial_bot/camera/image'; then
    break
  fi
  sleep 0.2
done

if ! printf '%s\n' "${ros_topics:-}" | grep -qx '/tutorial_bot/camera/image'; then
  sed -n '1,160p' "$bridge_log" >&2
  sed -n '1,160p' "$image_bridge_log" >&2
  exit 1
fi

ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist '{linear: {x: 0.2}}'
sleep 1
timeout 10 ros2 topic echo --once /odom nav_msgs/msg/Odometry > "$odom_message"
timeout 10 ros2 topic echo --once --full-length /scan sensor_msgs/msg/LaserScan > "$scan_message"
timeout 10 ros2 topic echo --once /imu sensor_msgs/msg/Imu > "$imu_message"
timeout 10 ros2 topic echo --once /tutorial_bot/camera/image sensor_msgs/msg/Image > "$image_message"
timeout 10 ros2 topic echo --once /clock rosgraph_msgs/msg/Clock > "$clock_message"

pose_x=$(awk '/position:/{in_position = 1; next} in_position && /x:/{print $2; exit}' "$odom_message")
linear_x=$(awk '/linear:/{in_linear = 1; next} in_linear && /x:/{print $2; exit}' "$odom_message")
scan_count=$(awk '
  /^ranges:/ { in_ranges = 1; next }
  /^intensities:/ { in_ranges = 0 }
  in_ranges && /^- / { count += 1 }
  END { print count + 0 }
' "$scan_message")
angle_min=$(awk '/angle_min:/{print $2; exit}' "$scan_message")
angle_max=$(awk '/angle_max:/{print $2; exit}' "$scan_message")
range_min=$(awk '/range_min:/{print $2; exit}' "$scan_message")
range_max=$(awk '/range_max:/{print $2; exit}' "$scan_message")
image_width=$(awk '/width:/{print $2; exit}' "$image_message")
image_height=$(awk '/height:/{print $2; exit}' "$image_message")

if [ -n "$evidence" ]; then
  cp "$odom_message" "$evidence/odom.yaml"
  cp "$scan_message" "$evidence/scan.yaml"
  cp "$imu_message" "$evidence/imu.yaml"
  cp "$image_message" "$evidence/image.yaml"
  cp "$clock_message" "$evidence/clock.yaml"
  cp "$server_log" "$evidence/gazebo.log"
  cp "$bridge_log" "$evidence/bridge.log"
  cp "$image_bridge_log" "$evidence/image-bridge.log"
fi

if ! grep -q 'orientation:' "$imu_message" || ! grep -q 'clock:' "$clock_message"; then
  printf '%s\n' 'IMU or clock bridge did not produce a ROS message.' >&2
  exit 1
fi

if ! awk -v pose_x="$pose_x" -v linear_x="$linear_x" -v scan_count="$scan_count" \
  -v angle_min="$angle_min" -v angle_max="$angle_max" -v range_min="$range_min" -v range_max="$range_max" \
  -v image_width="$image_width" -v image_height="$image_height" \
  'BEGIN { exit !(pose_x > 0.05 && linear_x > 0.15 && scan_count == 360 && angle_min < -3.14 && angle_max > 3.14 && range_min > 0.1199 && range_min < 0.1201 && range_max == 10.0 && image_width == 320 && image_height == 240) }'; then
  printf 'ROS bridge messages did not have the expected values: pose_x=%s linear_x=%s scan_count=%s angle_min=%s angle_max=%s range_min=%s range_max=%s image=%sx%s\n' \
    "$pose_x" "$linear_x" "$scan_count" "$angle_min" "$angle_max" "$range_min" "$range_max" "$image_width" "$image_height" >&2
  exit 1
fi

printf 'ROS cmd_vel to Gazebo verified: odom x=%s, linear.x=%s.\n' "$pose_x" "$linear_x"
printf 'Gazebo sensors to ROS verified: scan=%s, image=%sx%s, IMU and clock received.\n' \
  "$scan_count" "$image_width" "$image_height"
if [ -n "$evidence" ]; then
  printf '{"schema_version":1,"status":"pass","scan_count":%s,"angle_min":%s,"angle_max":%s,"range_min":%s,"range_max":%s,"image":{"width":%s,"height":%s},"odom":{"x":%s,"linear_x":%s},"imu":true,"clock":true}\n' \
    "$scan_count" "$angle_min" "$angle_max" "$range_min" "$range_max" "$image_width" "$image_height" "$pose_x" "$linear_x" > "$evidence/result.json"
fi
run_status=pass
