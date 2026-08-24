#!/usr/bin/env bash
set -euo pipefail

project_root=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)
evidence_dir=''
robot1_name='robot1'
robot2_name='robot2'
robot1_namespace='/robot1'
robot2_namespace='/robot2'

while (($#)); do
  case "$1" in
    --launch) shift ;;
    --evidence)
      evidence_dir=${2:?--evidence requires a directory}
      shift 2
      ;;
    --robot1-name)
      robot1_name=${2:?--robot1-name requires a value}
      shift 2
      ;;
    --robot2-name)
      robot2_name=${2:?--robot2-name requires a value}
      shift 2
      ;;
    --robot1-namespace)
      robot1_namespace=${2:?--robot1-namespace requires a value}
      shift 2
      ;;
    --robot2-namespace)
      robot2_namespace=${2:?--robot2-namespace requires a value}
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
temp_root=$(mktemp -d /tmp/tutorial-bot-multi-robot.XXXXXX)
domain_id=$((80 + $$ % 120))
partition="tutorial_bot_task7_${domain_id}_$$"
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
    wait "$group_leader" 2>/dev/null || true
  done
  if [[ $temp_root == /tmp/tutorial-bot-multi-robot.* && -e $temp_root ]]; then
    find "$temp_root" -depth -delete 2>/dev/null || cleanup_ok='false'
  else
    cleanup_ok='false'
  fi
  {
    printf 'cleanup_ok=%s\n' "$cleanup_ok"
    printf 'process_group_absent=%s\n' "$process_group_absent"
    printf 'temp_root_absent=%s\n' "$([[ ! -e $temp_root ]] && echo true || echo false)"
    printf 'dependency_overlay_absent=%s\n' "$([[ ! -e $temp_root/dependency-overlay ]] && echo true || echo false)"
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
export ROS2CLI_DISABLE_DAEMON=1
export ROS_HOME="$temp_root/ros-home"
unset AMENT_PREFIX_PATH CMAKE_PREFIX_PATH COLCON_PREFIX_PATH PYTHONPATH LD_LIBRARY_PATH
unset GZ_SIM_RESOURCE_PATH GAZEBO_MODEL_PATH
mkdir -p "$ROS_HOME"
set +u
source /opt/ros/jazzy/setup.bash
set -u

: > "$evidence_dir/pids.log"
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
set +u
source "$temp_root/install/setup.bash"
set -u
find "$temp_root/install" -type f -print0 | sort -z | xargs -0 sha256sum | sha256sum \
  > "$evidence_dir/install-tree.sha256"

bringup_share=$(ros2 pkg prefix --share tutorial_bot_bringup)
control_share=$(ros2 pkg prefix --share tutorial_bot_control)
{
  printf 'bringup_share=%s\ncontrol_share=%s\n' "$bringup_share" "$control_share"
  find "$bringup_share" "$control_share" -type f -printf '%p\n' | sort
} > "$evidence_dir/installed-share.log"
test -f "$bringup_share/launch/multi_robot.launch.py"
test -f "$bringup_share/config/bridge-multi-robot.yaml"
test -f "$control_share/config/multi_robot_controllers.yaml"

launch_command=(
  ros2 launch tutorial_bot_bringup multi_robot.launch.py
  "robot1_name:=$robot1_name" "robot2_name:=$robot2_name"
  "robot1_namespace:=$robot1_namespace" "robot2_namespace:=$robot2_namespace"
)
printf '%q ' "${launch_command[@]}" > "$evidence_dir/launch.command"
printf '\n' >> "$evidence_dir/launch.command"
setsid "${launch_command[@]}" > "$evidence_dir/launch.log" 2>&1 &
launch_pid=$!
printf '%s\n' "$launch_pid" >> "$evidence_dir/pids.log"

if [[ $robot1_name == "$robot2_name" || $robot1_namespace == "$robot2_namespace" ]]; then
  for _ in {1..100}; do
    kill -0 "$launch_pid" 2>/dev/null || break
    sleep 0.1
  done
  if kill -0 "$launch_pid" 2>/dev/null; then
    printf '%s\n' 'Collision launch remained alive instead of failing before readiness.' >&2
    exit 1
  fi
  set +e
  wait "$launch_pid"
  launch_exit=$?
  set -e
  launch_pid=''
  {
    printf 'launch_exit=%s\n' "$launch_exit"
    printf 'collision_name=%s\n' "$robot1_name"
    printf 'robot1_namespace=%s\nrobot2_namespace=%s\n' \
      "$robot1_namespace" "$robot2_namespace"
    printf '%s\n' 'readiness_reached=false'
  } > "$evidence_dir/collision.log"
  if [[ $robot1_name == "$robot2_name" ]]; then
    cp "$evidence_dir/collision.log" "$evidence_dir/name-collision.log"
  else
    cp "$evidence_dir/collision.log" "$evidence_dir/namespace-collision.log"
  fi
  ((launch_exit != 0))
  if [[ $robot1_name == "$robot2_name" ]]; then
    grep -F "Entity name collision: both robots requested '$robot1_name'." "$evidence_dir/launch.log"
  else
    grep -F "ROS namespace collision: both robots requested '$robot1_namespace'." "$evidence_dir/launch.log"
  fi
  if grep -q 'process started with pid' "$evidence_dir/launch.log"; then
    printf '%s\n' 'A process started before collision validation.' >&2
    exit 1
  fi
  printf '%s\n' 'ERROR: robot identity collision rejected before readiness.' >&2
  exit 1
fi

required_dependencies=(
  controller_manager controller_manager_msgs diff_drive_controller
  gz_ros2_control joint_state_broadcaster ros2controlcli tf2_ros
)
: > "$evidence_dir/dependencies.log"
missing_dependencies=()
for dependency in "${required_dependencies[@]}"; do
  prefix=$(ros2 pkg prefix "$dependency" 2>&1) || {
    missing_dependencies+=("$dependency")
    printf '%s=MISSING:%s\n' "$dependency" "$prefix" >> "$evidence_dir/dependencies.log"
    continue
  }
  printf '%s=%s\n' "$dependency" "$prefix" >> "$evidence_dir/dependencies.log"
done

if ((${#missing_dependencies[@]})); then
  kill -TERM -- "-$launch_pid" 2>/dev/null || true
  wait "$launch_pid" 2>/dev/null || true
  launch_pid=''
  overlay_root="$temp_root/dependency-overlay"
  mkdir -p "$overlay_root/debs" "$overlay_root/root"
  overlay_packages=(
    ros-jazzy-controller-manager ros-jazzy-controller-manager-msgs
    ros-jazzy-gz-ros2-control ros-jazzy-ros2controlcli
  )
  (
    cd "$overlay_root/debs"
    apt-get download "${overlay_packages[@]}"
  ) > "$evidence_dir/overlay-download.log" 2>&1
  for package in "$overlay_root"/debs/*.deb; do
    dpkg-deb -x "$package" "$overlay_root/root"
  done
  overlay_prefix="$overlay_root/root/opt/ros/jazzy"
  export PATH="$overlay_prefix/bin:$PATH"
  export AMENT_PREFIX_PATH="$overlay_prefix:$AMENT_PREFIX_PATH"
  export CMAKE_PREFIX_PATH="$overlay_prefix:$CMAKE_PREFIX_PATH"
  export LD_LIBRARY_PATH="$overlay_prefix/lib:$LD_LIBRARY_PATH"
  export PYTHONPATH="$overlay_prefix/lib/python3.12/site-packages:$PYTHONPATH"
  printf 'overlay_prefix=%s\npackages=%s\n' "$overlay_prefix" "${overlay_packages[*]}" \
    > "$evidence_dir/overlay.log"
  setsid "${launch_command[@]}" > "$evidence_dir/launch.log" 2>&1 &
  launch_pid=$!
  printf '%s\n' "$launch_pid" >> "$evidence_dir/pids.log"
fi

setsid timeout 180 ros2 topic echo --no-daemon --qos-reliability reliable \
  --qos-durability transient_local --qos-depth 100 \
  /tf_static tf2_msgs/msg/TFMessage > "$evidence_dir/tf-static.log" 2>&1 &
tf_static_pid=$!
auxiliary_pids+=("$tf_static_pid")

for robot in robot1 robot2; do
  controllers=''
  for _ in {1..900}; do
    controllers=$(ros2 control list_controllers -c "/$robot/controller_manager" 2>/dev/null || true)
    if grep -Eq '^joint_state_broadcaster.*[[:space:]]active[[:space:]]*$' <<< "$controllers" && \
      grep -Eq '^diff_drive_controller.*[[:space:]]active[[:space:]]*$' <<< "$controllers"; then
      break
    fi
    kill -0 "$launch_pid" 2>/dev/null || break
    sleep 0.2
  done
  printf '%s\n' "$controllers" > "$evidence_dir/$robot-controllers.log"
  grep -Eq '^joint_state_broadcaster.*[[:space:]]active[[:space:]]*$' "$evidence_dir/$robot-controllers.log"
  grep -Eq '^diff_drive_controller.*[[:space:]]active[[:space:]]*$' "$evidence_dir/$robot-controllers.log"
done

gz model --list > "$evidence_dir/entities.log"
grep -Eq '^[[:space:]]*-[[:space:]]+robot1$' "$evidence_dir/entities.log"
grep -Eq '^[[:space:]]*-[[:space:]]+robot2$' "$evidence_dir/entities.log"
ros2 node list --no-daemon --spin-time 5 > "$evidence_dir/nodes.log" 2>&1 || true
ros2 topic list --no-daemon --spin-time 5 > "$evidence_dir/topics.log" 2>&1 || true
for robot in robot1 robot2; do
  timeout 15 ros2 topic echo --no-daemon --once "/$robot/scan" sensor_msgs/msg/LaserScan \
    > "$evidence_dir/$robot-scan.log"
  timeout 15 ros2 topic echo --no-daemon --once "/$robot/imu" sensor_msgs/msg/Imu \
    > "$evidence_dir/$robot-imu.log"
  timeout 15 ros2 topic echo --no-daemon --once "/$robot/camera/image" sensor_msgs/msg/Image \
    > "$evidence_dir/$robot-image.log"
  timeout 15 ros2 topic echo --no-daemon --once "/$robot/joint_states" sensor_msgs/msg/JointState \
    > "$evidence_dir/$robot-joint-states.log"
  grep -q "frame_id: $robot/lidar_link" "$evidence_dir/$robot-scan.log"
  grep -q "frame_id: $robot/imu_link" "$evidence_dir/$robot-imu.log"
  grep -q "frame_id: $robot/camera_optical_frame" "$evidence_dir/$robot-image.log"
done

ros2 topic info --no-daemon --spin-time 2 /clock > "$evidence_dir/clock-info.log"
grep -q 'Publisher count: 1' "$evidence_dir/clock-info.log"
gz topic -i -t /clock > "$evidence_dir/gz-clock-info.log"
setsid timeout 20 ros2 topic echo --no-daemon /clock rosgraph_msgs/msg/Clock \
  > "$evidence_dir/clock-samples.log" 2>&1 &
clock_pid=$!
auxiliary_pids+=("$clock_pid")
for _ in {1..200}; do
  if awk '$1 == "sec:" {sec=$2} $1 == "nanosec:" {stamp=sec*1000000000+$2; if (!seen) first=stamp; else if (stamp<=last) exit 1; last=stamp; seen=1; count++} END {exit !(count>=100 && last-first>=1000000000)}' \
    "$evidence_dir/clock-samples.log"; then
    break
  fi
  sleep 0.1
done
kill -TERM -- "-$clock_pid" 2>/dev/null || true
wait "$clock_pid" 2>/dev/null || true
auxiliary_pids=()
awk '$1 == "sec:" {sec=$2} $1 == "nanosec:" {stamp=sec*1000000000+$2; if (!seen) first=stamp; else if (stamp<=last) exit 1; last=stamp; seen=1; count++} END {print "samples=" count; print "duration_ns=" last-first; exit !(count>=100 && last-first>=1000000000)}' \
  "$evidence_dir/clock-samples.log" > "$evidence_dir/clock-summary.log"

setsid timeout 8 ros2 topic echo --no-daemon /tf tf2_msgs/msg/TFMessage \
  > "$evidence_dir/tf.log" 2>&1 &
tf_pid=$!
auxiliary_pids+=("$tf_pid")
ros2 topic info --no-daemon --spin-time 2 -v /tf_static \
  > "$evidence_dir/tf-static-info.log"
wait "$tf_pid" 2>/dev/null || true
for _ in {1..100}; do
  if grep -q 'robot1/imu_link' "$evidence_dir/tf-static.log" && \
    grep -q 'robot2/imu_link' "$evidence_dir/tf-static.log"; then
    break
  fi
  kill -0 "$launch_pid" 2>/dev/null || break
  sleep 0.1
done
kill -TERM -- "-$tf_static_pid" 2>/dev/null || true
wait "$tf_static_pid" 2>/dev/null || true
auxiliary_pids=()
cat "$evidence_dir/tf.log" "$evidence_dir/tf-static.log" > "$evidence_dir/tf-all.log"
for robot in robot1 robot2; do
  for frame in odom base_link left_wheel_link right_wheel_link lidar_link camera_link imu_link; do
    grep -q "${robot}/${frame}" "$evidence_dir/tf-all.log"
  done
done
awk '
  /^[[:space:]]*frame_id:/ {parent=$2; gsub(/['"'"']/, "", parent)}
  /^[[:space:]]*child_frame_id:/ {
    child=$2; gsub(/['"'"']/, "", child); pairs[child SUBSEP parent]=1
  }
  END {
    for (key in pairs) {split(key, fields, SUBSEP); parents[fields[1]]++}
    for (child in parents) if (parents[child] > 1) {print child, parents[child]; bad=1}
    exit bad
  }
' "$evidence_dir/tf-all.log" > "$evidence_dir/duplicate-tf-parents.log"

capture_pose() {
  local robot=$1
  local label=$2
  timeout 8 ros2 topic echo --no-daemon --once "/$robot/odom" nav_msgs/msg/Odometry \
    --field pose.pose.position > "$evidence_dir/$label-$robot.pose"
  awk '$1 == "x:" {x=$2} $1 == "y:" {y=$2} END {print x, y}' \
    "$evidence_dir/$label-$robot.pose" > "$evidence_dir/$label-$robot.xy"
}

for robot in robot1 robot2; do
  ros2 topic pub --once --max-wait-time-secs 5 \
    "/$robot/diff_drive_controller/cmd_vel" geometry_msgs/msg/TwistStamped \
    '{twist: {linear: {x: 0.0}}}' \
    > "$evidence_dir/$robot-initialize-command.log"
done
capture_pose robot1 before-first
capture_pose robot2 before-first
ros2 topic pub --rate 20 --times 60 --max-wait-time-secs 5 \
  /robot1/diff_drive_controller/cmd_vel geometry_msgs/msg/TwistStamped \
  '{twist: {linear: {x: 0.2}}}' > "$evidence_dir/robot1-command.log"
ros2 topic pub --once --max-wait-time-secs 5 \
  /robot1/diff_drive_controller/cmd_vel geometry_msgs/msg/TwistStamped \
  '{twist: {linear: {x: 0.0}}}' > "$evidence_dir/robot1-stop-command.log"
capture_pose robot1 after-first
capture_pose robot2 after-first
capture_pose robot1 before-second
capture_pose robot2 before-second
ros2 topic pub --rate 20 --times 60 --max-wait-time-secs 5 \
  /robot2/diff_drive_controller/cmd_vel geometry_msgs/msg/TwistStamped \
  '{twist: {linear: {x: 0.2}}}' > "$evidence_dir/robot2-command.log"
ros2 topic pub --once --max-wait-time-secs 5 \
  /robot2/diff_drive_controller/cmd_vel geometry_msgs/msg/TwistStamped \
  '{twist: {linear: {x: 0.0}}}' > "$evidence_dir/robot2-stop-command.log"
capture_pose robot1 after-second
capture_pose robot2 after-second

displacement() {
  local before=$1
  local after=$2
  read -r x0 y0 < "$before"
  read -r x1 y1 < "$after"
  awk -v x0="$x0" -v y0="$y0" -v x1="$x1" -v y1="$y1" \
    'BEGIN {dx=x1-x0; dy=y1-y0; printf "%.6f", sqrt(dx*dx+dy*dy)}'
}
robot1_first=$(displacement "$evidence_dir/before-first-robot1.xy" "$evidence_dir/after-first-robot1.xy")
robot2_first=$(displacement "$evidence_dir/before-first-robot2.xy" "$evidence_dir/after-first-robot2.xy")
robot1_second=$(displacement "$evidence_dir/before-second-robot1.xy" "$evidence_dir/after-second-robot1.xy")
robot2_second=$(displacement "$evidence_dir/before-second-robot2.xy" "$evidence_dir/after-second-robot2.xy")
{
  printf 'robot1_command_robot1_displacement_m=%s\n' "$robot1_first"
  printf 'robot1_command_robot2_displacement_m=%s\n' "$robot2_first"
  printf 'robot2_command_robot1_displacement_m=%s\n' "$robot1_second"
  printf 'robot2_command_robot2_displacement_m=%s\n' "$robot2_second"
} > "$evidence_dir/displacements.log"
awk -v moving="$robot1_first" -v stationary="$robot2_first" \
  'BEGIN {exit !(moving >= 0.30 && stationary <= 0.03)}'
awk -v moving="$robot2_second" -v stationary="$robot1_second" \
  'BEGIN {exit !(moving >= 0.30 && stationary <= 0.03)}'

{
  printf '%s\n' 'PASS: robot1 and robot2 entities and namespaced controllers are ready.'
  printf '%s\n' 'PASS: namespaced TF trees have zero duplicate parents.'
  printf '%s\n' 'PASS: distinct namespaced sensor topics carry prefixed frames.'
  printf '%s\n' 'PASS: exactly one ROS clock publisher produced 100 increasing samples over at least one simulated second.'
  cat "$evidence_dir/displacements.log"
} > "$evidence_dir/nominal-observable.log"
cat "$evidence_dir/nominal-observable.log"
