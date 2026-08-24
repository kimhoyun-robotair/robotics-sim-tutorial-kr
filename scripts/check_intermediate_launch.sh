#!/usr/bin/env bash
set -euo pipefail

project_root=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)
dependency_overlay=${TUTORIAL_BOT_DEPENDENCY_OVERLAY:-}
world='sensor-test'
nav2='false'
evidence_dir=''
expect_failure='false'

while (($#)); do
  case "$1" in
    --launch)
      shift
      ;;
    --nav2)
      nav2=${2:?--nav2 requires a value}
      shift 2
      ;;
    --world)
      world=${2:?--world requires a value}
      shift 2
      ;;
    --evidence)
      evidence_dir=${2:?--evidence requires a directory}
      shift 2
      ;;
    --expect-failure)
      expect_failure='true'
      shift
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
temp_root=$(mktemp -d /tmp/tutorial-bot-intermediate.XXXXXX)
domain_id=$((80 + $$ % 120))
partition="tutorial_bot_task4_${domain_id}_$$"
launch_pid=''
build_pid=''

cleanup() {
  local cleanup_ok='true'
  local launch_process_absent='true'
  local process_group_absent='true'
  local group_leader
  local -a group_pids=()
  for group_leader in "$launch_pid" "$build_pid"; do
    if [[ -z $group_leader || ! $group_leader =~ ^[1-9][0-9]*$ ]]; then
      continue
    fi
    mapfile -t group_pids < <(ps -eo pid=,pgid= | awk -v pgid="$group_leader" '$2 == pgid {print $1}')
    printf '%s\n' "${group_pids[@]}" >> "$evidence_dir/pids.log"
    kill -TERM -- "-$group_leader" 2>/dev/null || true
    wait "$group_leader" 2>/dev/null || true
    for _ in {1..50}; do
      if ! ps -eo pgid= | awk -v pgid="$group_leader" '$1 == pgid {found=1} END {exit !found}'; then
        break
      fi
      sleep 0.1
    done
    if ps -eo pgid= | awk -v pgid="$group_leader" '$1 == pgid {found=1} END {exit !found}'; then
      kill -KILL -- "-$group_leader" 2>/dev/null || true
      for _ in {1..20}; do
        if ! ps -eo pgid= | awk -v pgid="$group_leader" '$1 == pgid {found=1} END {exit !found}'; then
          break
        fi
        sleep 0.1
      done
    fi
    if ps -eo pgid= | awk -v pgid="$group_leader" '$1 == pgid {found=1} END {exit !found}'; then
      process_group_absent='false'
      cleanup_ok='false'
    fi
  done
  if [[ -n $launch_pid ]] && kill -0 "$launch_pid" 2>/dev/null; then
    launch_process_absent='false'
  fi
  if [[ $temp_root == /tmp/tutorial-bot-intermediate.* && -e $temp_root ]]; then
    find "$temp_root" -depth -delete 2>/dev/null || cleanup_ok='false'
  elif [[ $temp_root != /tmp/tutorial-bot-intermediate.* ]]; then
    cleanup_ok='false'
  fi
  {
    printf 'cleanup_ok=%s\n' "$cleanup_ok"
    printf 'launch_process_absent=%s\n' "$launch_process_absent"
    printf 'process_group_absent=%s\n' "$process_group_absent"
    printf 'temp_root_absent=%s\n' "$([[ ! -e $temp_root ]] && echo true || echo false)"
    printf 'ros_domain_id=%s\n' "$domain_id"
    printf 'gz_partition=%s\n' "$partition"
    printf 'temp_root=%s\n' "$temp_root"
  } > "$evidence_dir/cleanup.log"
}
trap cleanup EXIT INT TERM

export HOME="$temp_root/home"
export PATH=/opt/ros/jazzy/bin:/usr/bin:/bin
export LANG=C.UTF-8
export LC_ALL=C.UTF-8
export ROS_DOMAIN_ID="$domain_id"
export GZ_PARTITION="$partition"
export ROS2CLI_DISABLE_DAEMON=1
unset AMENT_PREFIX_PATH CMAKE_PREFIX_PATH COLCON_PREFIX_PATH PYTHONPATH LD_LIBRARY_PATH
unset GZ_SIM_RESOURCE_PATH GAZEBO_MODEL_PATH
mkdir -p "$HOME"
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

build_command=(
  colcon --log-base "$temp_root/log" build
  --base-paths "$project_root/examples/ros2_ws/src"
  --packages-select tutorial_bot_description tutorial_bot_gazebo
  tutorial_bot_control tutorial_bot_bringup
  --build-base "$temp_root/build"
  --install-base "$temp_root/install"
  --event-handlers console_direct+
)
: > "$evidence_dir/pids.log"
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

bringup_share=$(ros2 pkg prefix --share tutorial_bot_bringup)
gazebo_share=$(ros2 pkg prefix --share tutorial_bot_gazebo)
{
  printf 'bringup_share=%s\n' "$bringup_share"
  printf 'gazebo_share=%s\n' "$gazebo_share"
  find "$bringup_share" -type f -printf '%P\n' | sort
} > "$evidence_dir/installed-share.log"

required_dependencies=(
  controller_manager controller_manager_msgs joint_state_broadcaster
  diff_drive_controller joint_trajectory_controller gz_ros2_control
)
missing_dependencies=()
: > "$evidence_dir/dependencies.log"
for dependency in "${required_dependencies[@]}"; do
  if prefix=$(ros2 pkg prefix "$dependency" 2>&1); then
    printf '%s=%s\n' "$dependency" "$prefix" >> "$evidence_dir/dependencies.log"
  else
    missing_dependencies+=("$dependency")
    printf '%s=MISSING:%s\n' "$dependency" "$prefix" >> "$evidence_dir/dependencies.log"
  fi
done

launch_command=(
  ros2 launch tutorial_bot_bringup simulation.launch.py
  "world:=$world" gui:=false rviz:=false "nav2:=$nav2"
)
printf '%q ' "${launch_command[@]}" > "$evidence_dir/launch.command"
printf '\n' >> "$evidence_dir/launch.command"
setsid "${launch_command[@]}" > "$evidence_dir/launch.log" 2>&1 &
launch_pid=$!
printf '%s\n' "$launch_pid" >> "$evidence_dir/pids.log"

if [[ $expect_failure == true ]]; then
  for _ in {1..100}; do
    kill -0 "$launch_pid" 2>/dev/null || break
    sleep 0.1
  done
  if kill -0 "$launch_pid" 2>/dev/null; then
    printf '%s\n' 'Fault launch did not terminate.' >&2
    exit 1
  fi
  set +e
  wait "$launch_pid"
  launch_exit=$?
  set -e
  launch_pid=''
  printf 'launch_exit=%s\n' "$launch_exit" > "$evidence_dir/fault-observable.log"
  ((launch_exit != 0))
  grep -F "Installed world does not exist: $gazebo_share/worlds/$world.sdf" "$evidence_dir/launch.log"
  if grep -q 'process started with pid' "$evidence_dir/launch.log"; then
    exit 1
  fi
  if grep -q 'Entity creation successful' "$evidence_dir/launch.log"; then
    exit 1
  fi
  printf '%s\n' 'PASS: missing installed world failed before startup; no fallback or readiness.' \
    >> "$evidence_dir/fault-observable.log"
  exit 0
fi

if ((${#missing_dependencies[@]})); then
  for _ in {1..300}; do
    grep -q 'Entity creation successful' "$evidence_dir/launch.log" && break
    kill -0 "$launch_pid" 2>/dev/null || break
    sleep 0.1
  done
  grep -q '\[gazebo-1\]: process started' "$evidence_dir/launch.log"
  grep -q '\[robot_state_publisher-2\]: process started' "$evidence_dir/launch.log"
  grep -q '\[create-3\]: process started' "$evidence_dir/launch.log"
  grep -q '\[parameter_bridge-4\]: process started' "$evidence_dir/launch.log"
  grep -q '\[image_bridge-5\]: process started' "$evidence_dir/launch.log"
  grep -q 'Entity creation successful' "$evidence_dir/launch.log"
  for _ in {1..100}; do
    grep -q '\[wait_controller_manager-6\]: process started' "$evidence_dir/launch.log" && break
    kill -0 "$launch_pid" 2>/dev/null || break
    sleep 0.1
  done
  grep -q '\[wait_controller_manager-6\]: process started' "$evidence_dir/launch.log"
  {
    printf 'status=environment-blocked\n'
    printf 'missing_dependencies=%s\n' "${missing_dependencies[*]}"
    printf '%s\n' 'maximal_surface=gazebo,state_publisher,create,parameter_bridge,image_bridge,entity_created'
    printf '%s\n' 'controllers_ready=false'
  } > "$evidence_dir/nominal-observable.log"
  exit 78
fi

for _ in {1..900}; do
  controllers=$(ros2 control list_controllers -c /controller_manager 2>/dev/null || true)
  if grep -q '^joint_state_broadcaster.*active' <<< "$controllers" && \
    grep -q '^diff_drive_controller.*active' <<< "$controllers"; then
    break
  fi
  kill -0 "$launch_pid" 2>/dev/null || break
  sleep 0.2
done
printf '%s\n' "$controllers" > "$evidence_dir/controllers.log"
grep -q '^joint_state_broadcaster.*active' "$evidence_dir/controllers.log"
grep -q '^diff_drive_controller.*active' "$evidence_dir/controllers.log"
gz model --list > "$evidence_dir/entities.log"
grep -Eq '^[[:space:]]*-[[:space:]]+tutorial_bot$' "$evidence_dir/entities.log"
ros2 node list --no-daemon > "$evidence_dir/nodes.log"
grep -qx '/robot_state_publisher' "$evidence_dir/nodes.log"
for _ in {1..300}; do
  topics=$(ros2 topic list --no-daemon)
  if grep -qx '/diff_drive_controller/cmd_vel' <<< "$topics" && \
    grep -qx '/odom' <<< "$topics" && grep -qx '/clock' <<< "$topics" && \
    grep -qx '/scan' <<< "$topics" && grep -qx '/imu' <<< "$topics" && \
    grep -qx '/camera/image' <<< "$topics"; then
    break
  fi
  kill -0 "$launch_pid" 2>/dev/null || break
  sleep 0.1
done
printf '%s\n' "$topics" > "$evidence_dir/topics.log"
grep -qx '/diff_drive_controller/cmd_vel' "$evidence_dir/topics.log"
grep -qx '/odom' "$evidence_dir/topics.log"
grep -qx '/clock' "$evidence_dir/topics.log"
grep -qx '/scan' "$evidence_dir/topics.log"
grep -qx '/imu' "$evidence_dir/topics.log"
grep -qx '/camera/image' "$evidence_dir/topics.log"
ros2 topic info --no-daemon --spin-time 2 -v /diff_drive_controller/cmd_vel > "$evidence_dir/cmd-vel-info.log"
grep -q 'Type: geometry_msgs/msg/TwistStamped' "$evidence_dir/cmd-vel-info.log"
grep -Eq 'Subscription count: [1-9][0-9]*' "$evidence_dir/cmd-vel-info.log"
ros2 topic info --no-daemon --spin-time 2 -v /odom > "$evidence_dir/odom-info.log"
grep -q 'Publisher count: 1' "$evidence_dir/odom-info.log"
grep -q 'diff_drive_controller' "$evidence_dir/odom-info.log"
ros2 topic info --no-daemon --spin-time 2 /clock > "$evidence_dir/clock-info.log"
grep -q 'Publisher count: 1' "$evidence_dir/clock-info.log"
timeout 20 ros2 topic echo --no-daemon --once /scan sensor_msgs/msg/LaserScan > "$evidence_dir/scan.log"
timeout 20 ros2 topic echo --no-daemon --once /imu sensor_msgs/msg/Imu > "$evidence_dir/imu.log"
timeout 20 ros2 topic echo --no-daemon --once /camera/image sensor_msgs/msg/Image > "$evidence_dir/image.log"
timeout 20 ros2 topic echo --no-daemon /clock rosgraph_msgs/msg/Clock > "$evidence_dir/clock-samples.log" &
clock_echo_pid=$!
for _ in {1..1200}; do
  sample_count=$(grep -c '^---$' "$evidence_dir/clock-samples.log" || true)
  if ((sample_count >= 100)) && awk '$1 == "sec:" {sec=$2} $1 == "nanosec:" {stamp=sec*1000000000+$2; if (!seen) first=stamp; else if (stamp<=last) exit 1; last=stamp; seen=1; count++} END {exit !(count>=100 && last-first>=1000000000)}' "$evidence_dir/clock-samples.log"; then
    break
  fi
  sleep 0.1
done
kill "$clock_echo_pid" 2>/dev/null || true
wait "$clock_echo_pid" 2>/dev/null || true
sample_count=$(grep -c '^---$' "$evidence_dir/clock-samples.log" || true)
((sample_count >= 100))
awk '$1 == "sec:" {sec=$2} $1 == "nanosec:" {stamp=sec*1000000000+$2; if (!seen) first=stamp; else if (stamp<=last) exit 1; last=stamp; seen=1; count++} END {exit !(count>=100 && last-first>=1000000000)}' \
  "$evidence_dir/clock-samples.log"
printf '%s\n' 'PASS: entity, processes, controllers, clock, sensors, cmd subscriber, and controller odom ready.' \
  > "$evidence_dir/nominal-observable.log"
