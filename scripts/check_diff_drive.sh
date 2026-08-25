#!/usr/bin/env bash
set -eo pipefail

unset COLCON_CURRENT_PREFIX
source /opt/ros/jazzy/setup.bash
set -u

project_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
source "$project_root/scripts/lib/owned_process.sh"
scenarios=straight,arc,spin
evidence=''
xacro_path="$project_root/examples/ros2_ws/src/tutorial_bot_description/urdf/stages/03-diff-drive.xacro"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --scenarios)
      scenarios=$2
      shift 2
      ;;
    --evidence)
      evidence=$2
      shift 2
      ;;
    --xacro)
      xacro_path=$2
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
fi

server_pid=''
model_sdf=''
server_log=''
owned_roots=''
run_status=fail

cleanup_server() {
  if [ -n "$server_pid" ]; then
    owned_stop_pgid "$server_pid"
    wait "$server_pid" 2>/dev/null || true
    server_pid=''
  fi
  if [ -n "$model_sdf" ]; then
    rm -f "$model_sdf"
    model_sdf=''
  fi
  if [ -n "$server_log" ]; then
    rm -f "$server_log"
    server_log=''
  fi
}

cleanup_all() {
  cleanup_server
  if [ -n "$evidence" ]; then
    printf '{"schema_version":1,"status":"%s","owned_roots":[%s],"survivors":[]}\n' \
      "$run_status" "$owned_roots" > "$evidence/cleanup.json"
  fi
}

interrupted() {
  run_status=interrupted
  cleanup_server
  exit 130
}

trap cleanup_all EXIT
trap interrupted INT TERM

run_scenario() {
  scenario=$1
  case "$scenario" in
    straight)
      command_payload='linear: {x: 0.24} angular: {z: 0.0}'
      ;;
    arc)
      command_payload='linear: {x: 0.18} angular: {z: 0.60}'
      ;;
    spin)
      command_payload='linear: {x: 0.0} angular: {z: 1.00}'
      ;;
    zero-motion)
      command_payload='linear: {x: 0.0} angular: {z: 0.0}'
      ;;
    *)
      printf 'unknown scenario: %s\n' "$scenario" >&2
      return 64
      ;;
  esac

  cleanup_server
  export ROS_DOMAIN_ID=$((40 + ($$ + ${#scenario}) % 160))
  export GZ_PARTITION="tutorial_bot_diff_drive_${scenario}_${ROS_DOMAIN_ID}_$$"
  owned_validate_isolation "$ROS_DOMAIN_ID" "$GZ_PARTITION"
  model_sdf=$(mktemp)
  server_log=$(mktemp)
  xacro "$xacro_path" > "$model_sdf"
  gz sdf -k "$model_sdf"
  setsid gz sim -s -r "$project_root/examples/gazebo/worlds/first-world.sdf" > "$server_log" 2>&1 &
  server_pid=$!
  if [ -n "$owned_roots" ]; then
    owned_roots="$owned_roots,$server_pid"
  else
    owned_roots=$server_pid
  fi

  ready=false
  for _ in $(seq 1 50); do
    if gz service -l | grep -qx '/world/first_world/create'; then
      ready=true
      break
    fi
    sleep 0.2
  done
  if [ "$ready" != true ]; then
    sed -n '1,160p' "$server_log" >&2
    return 1
  fi

  gz service -s /world/first_world/create \
    --reqtype gz.msgs.EntityFactory \
    --reptype gz.msgs.Boolean \
    --timeout 3000 \
    --req "sdf_filename: \"$model_sdf\" pose { position { z: 0.12 } }" >/dev/null

  topics_ready=false
  for _ in $(seq 1 50); do
    if gz topic -l | grep -qx '/model/tutorial_bot/cmd_vel' && \
      gz topic -l | grep -qx '/model/tutorial_bot/odometry'; then
      topics_ready=true
      break
    fi
    sleep 0.2
  done
  if [ "$topics_ready" != true ]; then
    gz topic -l >&2
    return 1
  fi

  gz topic -t /model/tutorial_bot/cmd_vel -m gz.msgs.Twist -p "$command_payload"
  sleep 2
  odometry=$(timeout 10 gz topic -e -t /model/tutorial_bot/odometry -n 1)
  pose_values=$(printf '%s\n' "$odometry" | awk '
    /pose \{/ { in_pose = 1 }
    in_pose && /position \{/ { in_position = 1; next }
    in_position && $1 == "x:" { x = $2; next }
    in_position && $1 == "y:" { y = $2; in_position = 0; next }
    in_pose && /orientation \{/ { in_orientation = 1; next }
    in_orientation && $1 == "z:" { qz = $2; next }
    in_orientation && $1 == "w:" { qw = $2; print x, y, atan2(2 * qw * qz, 1 - 2 * qz * qz); exit }
  ')
  read -r pose_x pose_y yaw <<EOF
$pose_values
EOF
  linear_x=$(printf '%s\n' "$odometry" | awk '
    /twist \{/ { in_twist = 1 }
    in_twist && /linear \{/ { in_linear = 1; next }
    in_linear && $1 == "x:" { print $2; exit }
  ')
  if [ -z "${pose_x:-}" ] || [ -z "${pose_y:-}" ] || [ -z "${yaw:-}" ]; then
    printf 'unable to parse odometry for %s\n%s\n' "$scenario" "$odometry" >&2
    return 1
  fi

  case "$scenario" in
    straight)
      awk -v pose_x="$pose_x" -v linear_x="$linear_x" \
        'BEGIN { exit !(pose_x > 0.05 && linear_x > 0.15) }'
      awk -v x="$pose_x" -v y="$pose_y" -v yaw="$yaw" \
        'BEGIN { exit !(x > 0.15 && y > -0.05 && y < 0.05 && yaw > -0.20 && yaw < 0.20) }'
      ;;
    arc)
      awk -v x="$pose_x" -v y="$pose_y" -v yaw="$yaw" \
        'BEGIN { exit !(x > 0.10 && y > 0.03 && yaw > 0.25) }'
      ;;
    spin)
      awk -v x="$pose_x" -v y="$pose_y" -v yaw="$yaw" \
        'BEGIN { exit !(x > -0.08 && x < 0.08 && y > -0.08 && y < 0.08 && yaw > 0.35) }'
      ;;
    zero-motion)
      awk -v pose_x="$pose_x" -v linear_x="$linear_x" \
        'BEGIN { exit !(pose_x > 0.05 && linear_x > 0.15) }'
      ;;
  esac
  if [ -n "$evidence" ]; then
    printf '{"scenario":"%s","status":"pass","pose_x":%s,"pose_y":%s,"yaw":%s}\n' \
      "$scenario" "$pose_x" "$pose_y" "$yaw" > "$evidence/$scenario.json"
    printf '%s\n' "$odometry" > "$evidence/$scenario-odometry.log"
  fi
  printf 'PASS %s: pose_x=%s pose_y=%s yaw=%s\n' "$scenario" "$pose_x" "$pose_y" "$yaw"
  cleanup_server
}

old_ifs=$IFS
IFS=,
for scenario in $scenarios; do
  IFS=$old_ifs
  run_scenario "$scenario"
  IFS=,
done
IFS=$old_ifs
run_status=pass
printf 'DiffDrive scenarios verified: %s\n' "$scenarios"
