#!/usr/bin/env bash
set -euo pipefail

project_root=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)
source "$project_root/scripts/lib/owned_process.sh"
dependency_overlay=${TUTORIAL_BOT_DEPENDENCY_OVERLAY:-}
matrix_install_base=${TUTORIAL_INSTALL_BASE:-}
evidence_dir=''
missing_frame=''

while (($#)); do
  case "$1" in
    --launch)
      shift
      ;;
    --evidence)
      evidence_dir=${2:?--evidence requires a directory}
      shift 2
      ;;
    --expect-missing-frame)
      missing_frame=${2:?--expect-missing-frame requires a frame name}
      shift 2
      ;;
    *)
      printf 'Unknown argument: %s\n' "$1" >&2
      exit 2
      ;;
  esac
done

if [[ -z $evidence_dir ]]; then
  printf '%s\n' '--evidence is required.' >&2
  exit 2
fi

mkdir -p "$evidence_dir"
evidence_dir=$(CDPATH='' cd -- "$evidence_dir" && pwd)
temp_root=$(mktemp -d /tmp/tutorial-bot-control-tf.XXXXXX)
domain_id=$((80 + $$ % 120))
partition="tutorial_bot_task5_${domain_id}_$$"
launch_pid=''
build_pid=''
auxiliary_pids=()

cleanup() {
  local cleanup_ok='true'
  local process_group_absent='true'
  local group_leader
  local -a group_pids=()
  local -a leaders=("$launch_pid" "$build_pid" "${auxiliary_pids[@]}")
  for group_leader in "${leaders[@]}"; do
    if [[ -z $group_leader || ! $group_leader =~ ^[1-9][0-9]*$ ]]; then
      continue
    fi
    mapfile -t group_pids < <(
      ps -eo pid=,pgid= | awk -v pgid="$group_leader" '$2 == pgid {print $1}'
    )
    printf '%s\n' "${group_pids[@]}" >> "$evidence_dir/pids.log"
    kill -TERM -- "-$group_leader" 2>/dev/null || true
    wait "$group_leader" 2>/dev/null || true
    for _ in {1..100}; do
      if ! ps -eo pgid= | awk -v pgid="$group_leader" \
        '$1 == pgid {found=1} END {exit !found}'; then
        break
      fi
      sleep 0.1
    done
    if ps -eo pgid= | awk -v pgid="$group_leader" \
      '$1 == pgid {found=1} END {exit !found}'; then
      kill -KILL -- "-$group_leader" 2>/dev/null || true
      for _ in {1..30}; do
        if ! ps -eo pgid= | awk -v pgid="$group_leader" \
          '$1 == pgid {found=1} END {exit !found}'; then
          break
        fi
        sleep 0.1
      done
      if ps -eo pgid= | awk -v pgid="$group_leader" \
        '$1 == pgid {found=1} END {exit !found}'; then
        process_group_absent='false'
        cleanup_ok='false'
      fi
    fi
  done
  if [[ $temp_root == /tmp/tutorial-bot-control-tf.* && -e $temp_root ]]; then
    find "$temp_root" -depth -delete 2>/dev/null || cleanup_ok='false'
  else
    cleanup_ok='false'
  fi
  {
    printf 'cleanup_ok=%s\n' "$cleanup_ok"
    printf 'process_group_absent=%s\n' "$process_group_absent"
    printf 'temp_root_absent=%s\n' "$([[ ! -e $temp_root ]] && echo true || echo false)"
    printf 'ros_domain_id=%s\n' "$domain_id"
    printf 'gz_partition=%s\n' "$partition"
    printf 'temp_root=%s\n' "$temp_root"
  } > "$evidence_dir/cleanup.log"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

export PATH=/opt/ros/jazzy/bin:/usr/bin:/bin
export LANG=C.UTF-8
export LC_ALL=C.UTF-8
export ROS_DOMAIN_ID="$domain_id"
export GZ_PARTITION="$partition"
owned_validate_isolation "$ROS_DOMAIN_ID" "$GZ_PARTITION"
export ROS2CLI_DISABLE_DAEMON=1
export ROS_HOME="$temp_root/ros-home"
unset AMENT_PREFIX_PATH CMAKE_PREFIX_PATH COLCON_PREFIX_PATH PYTHONPATH LD_LIBRARY_PATH
unset GZ_SIM_RESOURCE_PATH GAZEBO_MODEL_PATH
mkdir -p "$ROS_HOME"
set +u
source /opt/ros/jazzy/setup.bash
set -u
if [[ -n $dependency_overlay ]]; then
  overlay_prefix="$dependency_overlay/opt/ros/jazzy"
  if [[ $dependency_overlay != /* || ! -d $overlay_prefix/share/ament_index ]]; then
    printf 'Invalid dependency overlay: %s\n' "$dependency_overlay" >&2
    exit 2
  fi
  export PATH="$overlay_prefix/bin:$PATH"
  export AMENT_PREFIX_PATH="$overlay_prefix:$AMENT_PREFIX_PATH"
  export CMAKE_PREFIX_PATH="$overlay_prefix:$CMAKE_PREFIX_PATH"
  export LD_LIBRARY_PATH="$overlay_prefix/lib:$LD_LIBRARY_PATH"
  export PYTHONPATH="$overlay_prefix/lib/python3.12/site-packages:$PYTHONPATH"
fi

required_dependencies=(
  controller_manager controller_manager_msgs diff_drive_controller
  gz_ros2_control joint_state_broadcaster joint_trajectory_controller
  ros2controlcli rviz2 tf2_ros
)
: > "$evidence_dir/dependencies.log"
for dependency in "${required_dependencies[@]}"; do
  prefix=$(ros2 pkg prefix "$dependency" 2>&1) || {
    printf '%s=MISSING:%s\n' "$dependency" "$prefix" >> "$evidence_dir/dependencies.log"
    exit 78
  }
  printf '%s=%s\n' "$dependency" "$prefix" >> "$evidence_dir/dependencies.log"
done

: > "$evidence_dir/pids.log"
if [[ -n $matrix_install_base ]]; then
  [[ $matrix_install_base == /* && -f $matrix_install_base/setup.bash ]] || {
    printf 'Invalid TUTORIAL_INSTALL_BASE: %s\n' "$matrix_install_base" >&2
    exit 2
  }
  active_install_base=$matrix_install_base
  printf 'reused_install_base=%s\n' "$active_install_base" > "$evidence_dir/build.command"
  printf 'reused_install_base=%s\n' "$active_install_base" > "$evidence_dir/build.log"
else
  build_command=(
    colcon --log-base "$temp_root/log" build
    --base-paths "$project_root/examples/ros2_ws/src"
    --packages-select tutorial_bot_description tutorial_bot_gazebo
    tutorial_bot_control tutorial_bot_bringup
    --build-base "$temp_root/build"
    --install-base "$temp_root/install"
    --event-handlers console_direct+
  )
  printf '%q ' "${build_command[@]}" > "$evidence_dir/build.command"
  printf '\n' >> "$evidence_dir/build.command"
  setsid "${build_command[@]}" > "$evidence_dir/build.log" 2>&1 &
  build_pid=$!
  printf '%s\n' "$build_pid" >> "$evidence_dir/pids.log"
  wait "$build_pid"
  build_pid=''
  active_install_base=$temp_root/install
fi
set +u
source "$active_install_base/setup.bash"
set -u

bringup_share=$(ros2 pkg prefix --share tutorial_bot_bringup)
control_share=$(ros2 pkg prefix --share tutorial_bot_control)
{
  printf 'bringup_share=%s\n' "$bringup_share"
  printf 'control_share=%s\n' "$control_share"
  find "$bringup_share" "$control_share" -type f -printf '%p\n' | sort
} > "$evidence_dir/installed-share.log"
test -f "$bringup_share/rviz/tutorial_bot.rviz"
test -f "$control_share/config/controllers.yaml"

launch_command=(
  ros2 launch tutorial_bot_bringup simulation.launch.py
  world:=sensor-test gui:=false rviz:=false nav2:=false
)
printf '%q ' "${launch_command[@]}" > "$evidence_dir/launch.command"
printf '\n' >> "$evidence_dir/launch.command"
setsid "${launch_command[@]}" > "$evidence_dir/launch.log" 2>&1 &
launch_pid=$!
printf '%s\n' "$launch_pid" >> "$evidence_dir/pids.log"

controllers=''
for _ in {1..900}; do
  controllers=$(ros2 control list_controllers -c /controller_manager 2>/dev/null || true)
  if grep -Eq '^joint_state_broadcaster.*[[:space:]]active[[:space:]]*$' <<< "$controllers" && \
    grep -Eq '^diff_drive_controller.*[[:space:]]active[[:space:]]*$' <<< "$controllers" && \
    grep -Eq '^joint_trajectory_controller.*[[:space:]]inactive[[:space:]]*$' <<< "$controllers"; then
    break
  fi
  kill -0 "$launch_pid" 2>/dev/null || break
  sleep 0.2
done
printf '%s\n' "$controllers" > "$evidence_dir/controllers-initial.log"
grep -Eq '^joint_state_broadcaster.*[[:space:]]active[[:space:]]*$' "$evidence_dir/controllers-initial.log"
grep -Eq '^diff_drive_controller.*[[:space:]]active[[:space:]]*$' "$evidence_dir/controllers-initial.log"
grep -Eq '^joint_trajectory_controller.*[[:space:]]inactive[[:space:]]*$' "$evidence_dir/controllers-initial.log"

ros2 control list_hardware_interfaces -c /controller_manager \
  > "$evidence_dir/hardware-interfaces.log"
for joint in left_wheel_joint right_wheel_joint; do
  for interface in position velocity effort; do
    grep -Eq "^[[:space:]]*$joint/$interface([[:space:]]|$)" \
      "$evidence_dir/hardware-interfaces.log"
  done
done

required_frames=(
  base_link left_wheel_link right_wheel_link lidar_link camera_link imu_link
)
: > "$evidence_dir/tf-lookup-summary.log"
if [[ -n $missing_frame ]]; then
  set +e
  timeout 5 ros2 run tf2_ros tf2_echo odom "$missing_frame" -r 20 \
    > "$evidence_dir/missing-frame.log" 2>&1
  lookup_exit=$?
  set -e
  printf 'frame=%s\nlookup_exit=%s\n' "$missing_frame" "$lookup_exit" \
    >> "$evidence_dir/missing-frame.log"
  printf 'ERROR: required frame %s is missing (lookup exit %s).\n' \
    "$missing_frame" "$lookup_exit" >&2
  exit 1
fi

for frame in "${required_frames[@]}"; do
  output="$evidence_dir/tf-odom-${frame}.log"
  setsid timeout 6 ros2 run tf2_ros tf2_echo odom "$frame" -r 20 > "$output" 2>&1 &
  auxiliary_pids+=("$!")
done
for _ in {1..60}; do
  all_tf_ready=true
  for frame in "${required_frames[@]}"; do
    output="$evidence_dir/tf-odom-${frame}.log"
    (($(grep -c '^At time ' "$output" || true) >= 50)) || all_tf_ready=false
  done
  [[ $all_tf_ready == true ]] && break
  sleep 0.1
done
for auxiliary_pid in "${auxiliary_pids[@]}"; do
  kill -TERM -- "-$auxiliary_pid" 2>/dev/null || true
  set +e
  wait "$auxiliary_pid"
  set -e
done
auxiliary_pids=()
for frame in "${required_frames[@]}"; do
  output="$evidence_dir/tf-odom-${frame}.log"
  lookup_count=$(grep -c '^At time ' "$output" || true)
  ((lookup_count >= 50))
  printf '%s=%s/50\n' "$frame" "$lookup_count" >> "$evidence_dir/tf-lookup-summary.log"
done

set +e
timeout 4 ros2 run tf2_ros tf2_echo map odom -r 20 \
  > "$evidence_dir/map-odom-absent.log" 2>&1
map_lookup_exit=$?
set -e
((map_lookup_exit != 0))
if grep -q '^At time ' "$evidence_dir/map-odom-absent.log"; then
  printf '%s\n' 'Unexpected map->odom transform before Nav2.' >&2
  exit 1
fi

set +e
timeout 5 ros2 topic echo --no-daemon /tf tf2_msgs/msg/TFMessage \
  > "$evidence_dir/tf-stream.log" 2>&1
tf_echo_exit=$?
set -e
printf 'echo_exit=%s\n' "$tf_echo_exit" >> "$evidence_dir/tf-stream.log"
awk '
  /^[[:space:]]*frame_id:/ {parent=$2; gsub(/['"'"']/, "", parent)}
  /^[[:space:]]*child_frame_id:/ {
    child=$2; gsub(/['"'"']/, "", child)
    key=child SUBSEP parent
    pairs[key]=1
  }
  END {
    for (key in pairs) {
      split(key, fields, SUBSEP)
      parents[fields[1]]++
    }
    duplicates=0
    for (child in parents) {
      if (parents[child] > 1) {
        print child, parents[child]
        duplicates++
      }
    }
    exit duplicates > 0
  }
' "$evidence_dir/tf-stream.log" > "$evidence_dir/duplicate-tf-parents.log"
if grep -Ei 'multiple.*parent|different parent|TF_REPEATED_DATA|TF_OLD_DATA' \
  "$evidence_dir/launch.log" > "$evidence_dir/duplicate-parent-warnings.log"; then
  exit 1
fi
: > "$evidence_dir/duplicate-parent-warnings.log"

ros2 control switch_controllers -c /controller_manager --strict \
  --deactivate diff_drive_controller \
  --activate joint_trajectory_controller > "$evidence_dir/switch-to-trajectory.log"
ros2 control list_controllers -c /controller_manager \
  > "$evidence_dir/controllers-trajectory.log"
grep -Eq '^diff_drive_controller.*[[:space:]]inactive[[:space:]]*$' "$evidence_dir/controllers-trajectory.log"
grep -Eq '^joint_trajectory_controller.*[[:space:]]active[[:space:]]*$' "$evidence_dir/controllers-trajectory.log"
if grep -Eq '^diff_drive_controller.*[[:space:]]active[[:space:]]*$' "$evidence_dir/controllers-trajectory.log"; then
  exit 1
fi

setsid timeout 15 ros2 topic echo --no-daemon /joint_states \
  sensor_msgs/msg/JointState --field position > "$evidence_dir/joint-positions.log" 2>&1 &
joint_echo_pid=$!
auxiliary_pids+=("$joint_echo_pid")
timeout 15 ros2 topic pub --once /joint_trajectory_controller/joint_trajectory \
  trajectory_msgs/msg/JointTrajectory \
  "{joint_names: [left_wheel_joint, right_wheel_joint], points: [{positions: [1.0, 1.0], time_from_start: {sec: 2}}]}" \
  > "$evidence_dir/trajectory-command.log"
positions=''
for _ in {1..150}; do
  positions=$(grep '^array' "$evidence_dir/joint-positions.log" | tail -1 | \
    sed -E "s/.*\[([^,]+),[[:space:]]*([^]]+)\].*/\1 \2/" || true)
  if awk -v values="$positions" 'BEGIN {
    count=split(values, p, /[[:space:]]+/)
    exit !(count >= 2 && p[1] > 0.85 && p[1] < 1.15 && p[2] > 0.85 && p[2] < 1.15)
  }'; then
    break
  fi
  sleep 0.1
done
kill -TERM -- "-$joint_echo_pid" 2>/dev/null || true
wait "$joint_echo_pid" 2>/dev/null || true
auxiliary_pids=()
awk -v values="$positions" 'BEGIN {
  count=split(values, p, /[[:space:]]+/)
  exit !(count >= 2 && p[1] > 0.85 && p[1] < 1.15 && p[2] > 0.85 && p[2] < 1.15)
}'

ros2 control switch_controllers -c /controller_manager --strict \
  --deactivate joint_trajectory_controller \
  --activate diff_drive_controller > "$evidence_dir/switch-back-diff.log"
ros2 control list_controllers -c /controller_manager \
  > "$evidence_dir/controllers-final.log"
grep -Eq '^joint_state_broadcaster.*[[:space:]]active[[:space:]]*$' "$evidence_dir/controllers-final.log"
grep -Eq '^diff_drive_controller.*[[:space:]]active[[:space:]]*$' "$evidence_dir/controllers-final.log"
grep -Eq '^joint_trajectory_controller.*[[:space:]]inactive[[:space:]]*$' "$evidence_dir/controllers-final.log"
if grep -Eq '^joint_trajectory_controller.*[[:space:]]active[[:space:]]*$' "$evidence_dir/controllers-final.log"; then
  exit 1
fi

timeout 5 ros2 topic echo --no-daemon --once /odom nav_msgs/msg/Odometry \
  --field pose.pose.position > "$evidence_dir/odom-before.log"
ros2 topic pub --rate 20 --times 40 --max-wait-time-secs 5 \
  /diff_drive_controller/cmd_vel geometry_msgs/msg/TwistStamped \
  '{header: auto, twist: {linear: {x: 0.2}}}' \
  > "$evidence_dir/twist-command.log"
timeout 5 ros2 topic echo --no-daemon --once /odom nav_msgs/msg/Odometry \
  --field pose.pose.position > "$evidence_dir/odom-after.log"
awk '$1 == "x:" {x=$2} $1 == "y:" {y=$2} END {print x, y}' \
  "$evidence_dir/odom-before.log" > "$evidence_dir/odom-before.xy"
awk '$1 == "x:" {x=$2} $1 == "y:" {y=$2} END {print x, y}' \
  "$evidence_dir/odom-after.log" > "$evidence_dir/odom-after.xy"
read -r before_x before_y < "$evidence_dir/odom-before.xy"
read -r after_x after_y < "$evidence_dir/odom-after.xy"
displacement=$(awk -v x0="$before_x" -v y0="$before_y" \
  -v x1="$after_x" -v y1="$after_y" \
  'BEGIN {dx=x1-x0; dy=y1-y0; printf "%.6f", sqrt(dx*dx+dy*dy)}')
printf 'before=%s,%s\nafter=%s,%s\ndisplacement_m=%s\nthreshold_m=0.30\n' \
  "$before_x" "$before_y" "$after_x" "$after_y" "$displacement" \
  > "$evidence_dir/displacement.log"
awk -v displacement="$displacement" 'BEGIN {exit !(displacement >= 0.30)}'

{
  printf '%s\n' 'PASS: joint_state and diff_drive active; trajectory inactive by default.'
  printf '%s\n' 'PASS: position, velocity, and effort interfaces are exported for both wheels.'
  printf '%s\n' 'PASS: every required odom lookup produced at least 50 stamped transforms.'
  printf '%s\n' 'PASS: no map->odom, duplicate TF parent, or duplicate-parent warning exists.'
  printf '%s\n' 'PASS: atomic trajectory switch, position verification, and switch-back completed.'
  printf 'PASS: TwistStamped 0.2 m/s for 3 s displaced robot %s m.\n' "$displacement"
} > "$evidence_dir/nominal-observable.log"
