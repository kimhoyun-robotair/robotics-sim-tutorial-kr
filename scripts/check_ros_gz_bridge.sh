#!/usr/bin/env bash
set -eo pipefail

source /opt/ros/jazzy/setup.bash
set -u

project_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
source "$project_root/scripts/lib/owned_process.sh"
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

cleanup() {
  for task_pid in "$image_bridge_pid" "$bridge_pid" "$server_pid"; do
    if [ -n "$task_pid" ]; then
      owned_stop_pgid "$task_pid"
      wait "$task_pid" 2>/dev/null || true
    fi
  done
  rm -f "$model_sdf" "$server_log" "$bridge_log" "$image_bridge_log" \
    "$odom_message" "$scan_message" "$imu_message" "$image_message" "$clock_message"
}

trap cleanup EXIT INT TERM

xacro "$project_root/examples/ros2_ws/src/tutorial_bot_description/urdf/tutorial_bot.urdf.xacro" > "$model_sdf"
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
    gz topic -l | grep -qx '/tutorial_bot/imu' && \
    gz topic -l | grep -qx '/tutorial_bot/camera/image'; then
    break
  fi
  sleep 0.2
done

bridge_config="$project_root/examples/ros2_ws/src/tutorial_bot_bringup/config/bridge.yaml"
setsid ros2 run ros_gz_bridge parameter_bridge --ros-args -p config_file:="$bridge_config" > "$bridge_log" 2>&1 &
bridge_pid=$!
setsid ros2 run ros_gz_image image_bridge /tutorial_bot/camera/image > "$image_bridge_log" 2>&1 &
image_bridge_pid=$!

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
timeout 10 ros2 topic echo --once /scan sensor_msgs/msg/LaserScan > "$scan_message"
timeout 10 ros2 topic echo --once /imu sensor_msgs/msg/Imu > "$imu_message"
timeout 10 ros2 topic echo --once /tutorial_bot/camera/image sensor_msgs/msg/Image > "$image_message"
timeout 10 ros2 topic echo --once /clock rosgraph_msgs/msg/Clock > "$clock_message"

pose_x=$(awk '/position:/{in_position = 1; next} in_position && /x:/{print $2; exit}' "$odom_message")
linear_x=$(awk '/linear:/{in_linear = 1; next} in_linear && /x:/{print $2; exit}' "$odom_message")
scan_count=$(awk '/ranges:/{in_ranges = 1; next} in_ranges && /^- / {count += 1} END {print count + 0}' "$scan_message")
image_width=$(awk '/width:/{print $2; exit}' "$image_message")
image_height=$(awk '/height:/{print $2; exit}' "$image_message")

if ! grep -q 'orientation:' "$imu_message" || ! grep -q 'clock:' "$clock_message"; then
  printf '%s\n' 'IMU or clock bridge did not produce a ROS message.' >&2
  exit 1
fi

if ! awk -v pose_x="$pose_x" -v linear_x="$linear_x" -v scan_count="$scan_count" \
  -v image_width="$image_width" -v image_height="$image_height" \
  'BEGIN { exit !(pose_x > 0.05 && linear_x > 0.15 && scan_count > 0 && image_width == 320 && image_height == 240) }'; then
  printf '%s\n' 'ROS bridge messages did not have the expected values.' >&2
  exit 1
fi

printf 'ROS cmd_vel to Gazebo verified: odom x=%s, linear.x=%s.\n' "$pose_x" "$linear_x"
printf 'Gazebo sensors to ROS verified: scan=%s, image=%sx%s, IMU and clock received.\n' \
  "$scan_count" "$image_width" "$image_height"
