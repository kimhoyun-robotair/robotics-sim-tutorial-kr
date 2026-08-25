#!/usr/bin/env bash
set -eo pipefail

source /opt/ros/jazzy/setup.bash
set -u

project_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
source "$project_root/scripts/lib/owned_process.sh"
export ROS_DOMAIN_ID=$((40 + $$ % 160))
export GZ_PARTITION="tutorial_bot_beginner_diff_drive_${ROS_DOMAIN_ID}_$$"
owned_validate_isolation "$ROS_DOMAIN_ID" "$GZ_PARTITION"
model_sdf=$(mktemp)
server_log=$(mktemp)
server_pid=''

cleanup() {
  if [ -n "$server_pid" ]; then
    owned_stop_pgid "$server_pid"
    wait "$server_pid" 2>/dev/null || true
  fi
  rm -f "$model_sdf" "$server_log"
}

trap cleanup EXIT INT TERM

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

for _ in $(seq 1 30); do
  if gz topic -l | grep -qx '/model/tutorial_bot/cmd_vel' && \
    gz topic -l | grep -qx '/model/tutorial_bot/odometry'; then
    gz topic -t /model/tutorial_bot/cmd_vel \
      -m gz.msgs.Twist \
      -p 'linear: {x: 0.2}'
    sleep 1
    odometry=$(gz topic -e -t /model/tutorial_bot/odometry -n 1)
    printf '%s\n' "$odometry"
    pose_x=$(printf '%s\n' "$odometry" | awk '
      /pose \{/ { in_pose = 1 }
      in_pose && /position \{/ { in_position = 1; next }
      in_position && $1 == "x:" { print $2; exit }
    ')
    linear_x=$(printf '%s\n' "$odometry" | awk '
      /twist \{/ { in_twist = 1 }
      in_twist && /linear \{/ { in_linear = 1; next }
      in_linear && $1 == "x:" { print $2; exit }
    ')
    if ! awk -v pose_x="$pose_x" -v linear_x="$linear_x" \
      'BEGIN { exit !(pose_x > 0.05 && linear_x > 0.15) }'; then
      printf '%s\n' 'DiffDrive odometry did not show expected forward motion.' >&2
      exit 1
    fi
    printf '%s\n' 'DiffDrive motion verified.'
    exit 0
  fi
  sleep 0.2
done

gz topic -l >&2
exit 1
