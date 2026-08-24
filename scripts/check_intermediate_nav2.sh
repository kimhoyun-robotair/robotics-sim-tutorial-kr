#!/usr/bin/env bash
# noqa: SIZE_OK — one self-contained disposable-runtime checker keeps cleanup ownership auditable.
set -euo pipefail

checker_argv=("$0" "$@")
command_started_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)
project_root=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)
evidence_dir=''
goal_name='project_goal.yaml'
repeat=1
position_tolerance='0.25'
yaw_tolerance='0.20'
expect_status='4'
fresh_build='false'

while (($#)); do
  case "$1" in
    --fresh-build) fresh_build='true'; shift ;;
    --launch) shift ;;
    --goal-name) goal_name=${2:?--goal-name requires a value}; shift 2 ;;
    --repeat) repeat=${2:?--repeat requires a value}; shift 2 ;;
    --position-tolerance) position_tolerance=${2:?--position-tolerance requires a value}; shift 2 ;;
    --yaw-tolerance) yaw_tolerance=${2:?--yaw-tolerance requires a value}; shift 2 ;;
    --expect-status) expect_status=${2:?--expect-status requires a value}; shift 2 ;;
    --evidence) evidence_dir=${2:?--evidence requires a directory}; shift 2 ;;
    *) printf 'Unknown argument: %s\n' "$1" >&2; exit 2 ;;
  esac
done

[[ $fresh_build == true ]] || { printf '%s\n' '--fresh-build is required.' >&2; exit 2; }
[[ -n $evidence_dir ]] || { printf '%s\n' '--evidence is required.' >&2; exit 2; }
[[ $goal_name =~ ^[A-Za-z0-9_-]+\.yaml$ ]] || { printf 'Malformed goal name: %s\n' "$goal_name" >&2; exit 2; }
[[ $repeat =~ ^[1-9][0-9]*$ ]] || { printf 'Invalid repeat: %s\n' "$repeat" >&2; exit 2; }
[[ $expect_status =~ ^[0-9]+$ ]] || { printf 'Invalid status: %s\n' "$expect_status" >&2; exit 2; }

mkdir -p "$evidence_dir"
evidence_dir=$(CDPATH='' cd -- "$evidence_dir" && pwd)
printf '%q ' "${checker_argv[@]}" > "$evidence_dir/checker.command"
printf '\n' >> "$evidence_dir/checker.command"
printf '%s\n' "$command_started_utc" > "$evidence_dir/command-start.utc"
temp_root=$(mktemp -d /tmp/tutorial-bot-nav2.XXXXXX)
build_pid=''
launch_pid=''
auxiliary_pids=()
run_partitions=()

stop_group() {
  local leader=${1:-}
  [[ $leader =~ ^[1-9][0-9]*$ ]] || return 0
  kill -TERM -- "-$leader" 2>/dev/null || true
  for _ in {1..50}; do
    if ! ps -eo pgid= | awk -v p="$leader" '$1==p {found=1} END {exit !found}'; then
      wait "$leader" 2>/dev/null || true
      return 0
    fi
    sleep 0.1
  done
  kill -KILL -- "-$leader" 2>/dev/null || true
  wait "$leader" 2>/dev/null || true
}

stop_partition() {
  local partition=$1
  local proc pid
  local -a partition_pids=()
  for proc in /proc/[1-9]*; do
    [[ -r $proc/environ ]] || continue
    if tr '\0' '\n' < "$proc/environ" 2>/dev/null | grep -Fxq "GZ_PARTITION=$partition"; then
      pid=${proc#/proc/}
      [[ $pid != "$$" ]] && partition_pids+=("$pid")
    fi
  done
  ((${#partition_pids[@]})) || return 0
  kill -TERM "${partition_pids[@]}" 2>/dev/null || true
  for _ in {1..50}; do
    local alive=false
    for pid in "${partition_pids[@]}"; do kill -0 "$pid" 2>/dev/null && alive=true; done
    [[ $alive == false ]] && return 0
    sleep 0.1
  done
  kill -KILL "${partition_pids[@]}" 2>/dev/null || true
}

cleanup() {
  local exit_code=$?
  local cleanup_ok=true
  local partition_absent=true
  local recorded_pids_absent=true
  local partition
  for auxiliary_pid in "${auxiliary_pids[@]}"; do stop_group "$auxiliary_pid"; done
  stop_group "$launch_pid"
  stop_group "$build_pid"
  for partition in "${run_partitions[@]}"; do
    stop_partition "$partition"
    for proc in /proc/[1-9]*; do
      [[ -r $proc/environ ]] || continue
      if tr '\0' '\n' < "$proc/environ" 2>/dev/null | grep -Fxq "GZ_PARTITION=$partition"; then
        cleanup_ok=false
        partition_absent=false
      fi
    done
  done
  while IFS= read -r pid; do
    [[ $pid =~ ^[1-9][0-9]*$ ]] || continue
    kill -0 "$pid" 2>/dev/null && recorded_pids_absent=false
  done < <(find "$evidence_dir" -name pids.log -type f -exec cat {} + 2>/dev/null || true)
  [[ $recorded_pids_absent == true ]] || cleanup_ok=false
  if [[ $temp_root == /tmp/tutorial-bot-nav2.* && -e $temp_root ]]; then
    find "$temp_root" -depth -delete 2>/dev/null || cleanup_ok=false
  else
    cleanup_ok=false
  fi
  {
    printf 'cleanup_ok=%s\n' "$cleanup_ok"
    printf 'process_group_absent=%s\n' "$(! ps -eo pgid= | awk -v p="$launch_pid" '$1==p {found=1} END {exit !found}' && echo true || echo false)"
    printf 'partition_absent=%s\n' "$partition_absent"
    printf 'recorded_pids_absent=%s\n' "$recorded_pids_absent"
    printf 'temp_root_absent=%s\n' "$([[ ! -e $temp_root ]] && echo true || echo false)"
    printf 'temp_root=%s\n' "$temp_root"
    printf 'exit=%s\n' "$exit_code"
  } > "$evidence_dir/cleanup.log"
  date -u +%Y-%m-%dT%H:%M:%SZ > "$evidence_dir/command-end.utc"
  return "$exit_code"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

export PATH=/opt/ros/jazzy/bin:/usr/bin:/bin
export LANG=C.UTF-8 LC_ALL=C.UTF-8 ROS2CLI_DISABLE_DAEMON=1
export ROS_HOME="$temp_root/ros-home"
unset AMENT_PREFIX_PATH CMAKE_PREFIX_PATH COLCON_PREFIX_PATH COLCON_CURRENT_PREFIX
unset PYTHONPATH LD_LIBRARY_PATH GZ_SIM_RESOURCE_PATH GAZEBO_MODEL_PATH
mkdir -p "$ROS_HOME"
set +u
source /opt/ros/jazzy/setup.bash
set -u

overlay_root="$temp_root/dependency-overlay"
mkdir -p "$overlay_root/debs" "$overlay_root/root"
overlay_packages=(
  ros-jazzy-controller-manager ros-jazzy-controller-manager-msgs
  ros-jazzy-gz-ros2-control ros-jazzy-ros2controlcli
  ros-jazzy-joint-trajectory-controller
)
missing_nav2=()
for dependency in nav2_bringup nav2_amcl nav2_map_server nav2_lifecycle_manager; do
  ros2 pkg prefix "$dependency" >/dev/null 2>&1 || missing_nav2+=("ros-jazzy-${dependency//_/-}")
done
overlay_packages+=("${missing_nav2[@]}")
(
  cd "$overlay_root/debs"
  apt-get download "${overlay_packages[@]}"
) > "$evidence_dir/overlay-download.log" 2>&1
for package in "$overlay_root"/debs/*.deb; do dpkg-deb -x "$package" "$overlay_root/root"; done
overlay_prefix="$overlay_root/root/opt/ros/jazzy"
export PATH="$overlay_prefix/bin:$PATH"
export AMENT_PREFIX_PATH="$overlay_prefix:$AMENT_PREFIX_PATH"
export CMAKE_PREFIX_PATH="$overlay_prefix:$CMAKE_PREFIX_PATH"
export LD_LIBRARY_PATH="$overlay_prefix/lib:$LD_LIBRARY_PATH"
export PYTHONPATH="$overlay_prefix/lib/python3.12/site-packages:$PYTHONPATH"
printf 'overlay_prefix=%s\npackages=%s\n' "$overlay_prefix" "${overlay_packages[*]}" > "$evidence_dir/overlay.log"

build_command=(
  colcon --log-base "$temp_root/log" build
  --base-paths "$project_root/examples/ros2_ws/src"
  --packages-select tutorial_bot_description tutorial_bot_gazebo tutorial_bot_control tutorial_bot_bringup
  --build-base "$temp_root/build" --install-base "$temp_root/install"
  --event-handlers console_direct+
)
printf '%q ' "${build_command[@]}" > "$evidence_dir/build.command"; printf '\n' >> "$evidence_dir/build.command"
setsid "${build_command[@]}" > "$evidence_dir/build.log" 2>&1 & build_pid=$!
wait "$build_pid"; build_pid=''
set +u
source "$temp_root/install/setup.bash"
set -u

bringup_share=$(ros2 pkg prefix --share tutorial_bot_bringup)
gazebo_share=$(ros2 pkg prefix --share tutorial_bot_gazebo)
goal_file="$bringup_share/config/$goal_name"
map_file="$gazebo_share/maps/training.yaml"
for installed in "$goal_file" "$map_file" "$gazebo_share/maps/training.pgm" "$bringup_share/config/nav2_params.yaml"; do
  [[ $installed == "$temp_root"/install/* && -f $installed ]] || { printf 'Missing installed asset: %s\n' "$installed" >&2; exit 1; }
done
{
  printf 'bringup_share=%s\ngazebo_share=%s\n' "$bringup_share" "$gazebo_share"
  find "$bringup_share/config" "$gazebo_share/maps" "$gazebo_share/worlds" -type f -printf '%p\n' | sort
} > "$evidence_dir/installed-share.log"
find "$temp_root/install" -type f -print0 | sort -z | xargs -0 sha256sum | sha256sum > "$evidence_dir/install-tree.sha256"

goal_x=$(awk '$1=="x:" {print $2; exit}' "$goal_file")
goal_y=$(awk '$1=="y:" {print $2; exit}' "$goal_file")
goal_yaw=$(awk '$1=="yaw:" {print $2; exit}' "$goal_file")
[[ -n $goal_x && -n $goal_y && -n $goal_yaw ]] || { printf 'Malformed installed goal: %s\n' "$goal_file" >&2; exit 2; }
goal_z=$(awk -v y="$goal_yaw" 'BEGIN {printf "%.12f", sin(y/2)}')
goal_w=$(awk -v y="$goal_yaw" 'BEGIN {printf "%.12f", cos(y/2)}')

for ((run=1; run<=repeat; run++)); do
  run_dir="$evidence_dir/run-$run"; mkdir -p "$run_dir"
  date -u +%Y-%m-%dT%H:%M:%SZ > "$run_dir/start.utc"
  export ROS_DOMAIN_ID=$((120 + ($$ + run * 17) % 100))
  export GZ_PARTITION="tutorial_bot_task8_${ROS_DOMAIN_ID}_$$_$run"
  printf 'os=%s\nros=%s\ngazebo=%s\nros_domain_id=%s\ngz_partition=%s\ntemp_root=%s\n' \
    "$(uname -srvmo)" 'jazzy+disposable-local-deb-overlay' 'gz-sim8' \
    "$ROS_DOMAIN_ID" "$GZ_PARTITION" "$temp_root" > "$run_dir/environment.log"
  run_partitions+=("$GZ_PARTITION")
  launch_command=(ros2 launch tutorial_bot_bringup simulation.launch.py)
  printf '%q ' "${launch_command[@]}" > "$run_dir/launch.command"; printf '\n' >> "$run_dir/launch.command"
  setsid "${launch_command[@]}" > "$run_dir/launch.log" 2>&1 & launch_pid=$!
  printf '%s\n' "$launch_pid" > "$run_dir/pids.log"

  ready=false
  for _ in {1..900}; do
    state=$(ros2 lifecycle get /bt_navigator 2>/dev/null || true)
    if grep -qx 'active \[3\]' <<< "$state" && ros2 action list 2>/dev/null | grep -qx /navigate_to_pose; then ready=true; break; fi
    kill -0 "$launch_pid" 2>/dev/null || break
    sleep 0.2
  done
  [[ $ready == true ]] || { tail -100 "$run_dir/launch.log" >&2; exit 1; }
  ps -eo pid=,pgid= | awk -v group="$launch_pid" '$2==group {print $1}' >> "$run_dir/pids.log"
  for proc in /proc/[1-9]*; do
    [[ -r $proc/environ ]] || continue
    if tr '\0' '\n' < "$proc/environ" 2>/dev/null | grep -Fxq "GZ_PARTITION=$GZ_PARTITION"; then
      printf '%s\n' "${proc#/proc/}" >> "$run_dir/pids.log"
    fi
  done
  sort -nu -o "$run_dir/pids.log" "$run_dir/pids.log"
  for node in amcl map_server controller_server planner_server bt_navigator; do
    ros2 lifecycle get "/$node" > "$run_dir/lifecycle-$node.log" 2>&1 || true
  done
  grep -qx 'active \[3\]' "$run_dir/lifecycle-amcl.log"
  grep -qx 'active \[3\]' "$run_dir/lifecycle-map_server.log"
  grep -qx 'active \[3\]' "$run_dir/lifecycle-controller_server.log"
  grep -qx 'active \[3\]' "$run_dir/lifecycle-planner_server.log"
  grep -qx 'active \[3\]' "$run_dir/lifecycle-bt_navigator.log"
  for topic_type in '/map nav_msgs/msg/OccupancyGrid' '/scan sensor_msgs/msg/LaserScan' '/odom nav_msgs/msg/Odometry' '/tf tf2_msgs/msg/TFMessage'; do
    read -r topic type <<< "$topic_type"
    timeout 10 ros2 topic echo --once "$topic" "$type" > "$run_dir/topic-${topic#/}.log" 2>&1
  done
  timeout 8 ros2 run tf2_ros tf2_echo map odom -r 20 > "$run_dir/map-odom.log" 2>&1 || true
  tf_count=$(grep -c '^At time ' "$run_dir/map-odom.log" || true)
  ((tf_count >= 50))

  goal="{pose: {header: {frame_id: map}, pose: {position: {x: $goal_x, y: $goal_y, z: 0.0}, orientation: {x: 0.0, y: 0.0, z: $goal_z, w: $goal_w}}}}"
  timeout 300 ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose "$goal" --feedback > "$run_dir/action.log" 2>&1
  status_name=$(awk -F': ' '/Goal finished with status:/ {value=$2} END {print value}' "$run_dir/action.log")
  case "$status_name" in
    SUCCEEDED) status=4 ;;
    ABORTED) status=6 ;;
    CANCELED) status=5 ;;
    *) printf 'Unrecognized action status: %s\n' "$status_name" >&2; exit 1 ;;
  esac
  printf 'status=%s\nexpected_status=%s\n' "$status" "$expect_status" > "$run_dir/status.log"
  [[ $status == "$expect_status" ]] || { cat "$run_dir/action.log" >&2; exit 1; }

  if [[ $expect_status == 4 ]]; then
    timeout 10 ros2 topic echo --once /amcl_pose geometry_msgs/msg/PoseWithCovarianceStamped > "$run_dir/amcl-pose.log" 2>&1
    final_x=$(awk '/position:/{p=1;next} p && $1=="x:" {print $2; exit}' "$run_dir/amcl-pose.log")
    final_y=$(awk '/position:/{p=1;next} p && $1=="y:" {print $2; exit}' "$run_dir/amcl-pose.log")
    final_z=$(awk '/orientation:/{q=1;next} q && $1=="z:" {print $2; exit}' "$run_dir/amcl-pose.log")
    final_w=$(awk '/orientation:/{q=1;next} q && $1=="w:" {print $2; exit}' "$run_dir/amcl-pose.log")
    awk -v x="$final_x" -v y="$final_y" -v gx="$goal_x" -v gy="$goal_y" -v z="$final_z" -v w="$final_w" -v gyaw="$goal_yaw" -v pt="$position_tolerance" -v yt="$yaw_tolerance" 'BEGIN {d=sqrt((x-gx)^2+(y-gy)^2); yaw=atan2(2*w*z,1-2*z*z); e=yaw-gyaw; while(e>3.141592653589793)e-=6.283185307179586; while(e< -3.141592653589793)e+=6.283185307179586; if(e<0)e=-e; printf "final_x=%.6f\nfinal_y=%.6f\nposition_error=%.6f\nyaw_error=%.6f\n",x,y,d,e; exit !(d<=pt && e<=yt)}' > "$run_dir/final-error.log"
  else
    timeout 10 ros2 service call /lifecycle_manager_navigation/manage_nodes nav2_msgs/srv/ManageLifecycleNodes '{command: 0}' > "$run_dir/lifecycle-manage.log" 2>&1
    grep -q 'ManageLifecycleNodes_Response' "$run_dir/lifecycle-manage.log"
    timeout 10 ros2 topic echo --once /scan sensor_msgs/msg/LaserScan > "$run_dir/post-abort-scan.log" 2>&1
    grep -q 'frame_id:' "$run_dir/post-abort-scan.log"
  fi
  kill -0 "$launch_pid"
  stop_group "$launch_pid"
  stop_partition "$GZ_PARTITION"
  launch_pid=''
  printf 'run=%s\nstatus=%s\nmap_odom=%s/50\nlaunch_alive_after_result=true\n' "$run" "$status" "$tf_count" > "$run_dir/observable.log"
  date -u +%Y-%m-%dT%H:%M:%SZ > "$run_dir/end.utc"
done

printf 'PASS: %s/%s goals returned status %s with live Nav2, map, scan, odom, and TF.\n' "$repeat" "$repeat" "$expect_status" > "$evidence_dir/summary.log"
cat "$evidence_dir/summary.log"
