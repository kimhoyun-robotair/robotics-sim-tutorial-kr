#!/usr/bin/env bash
set -Eeuo pipefail
source_root=${1:?source repository required}
evidence=${2:?evidence directory required}
mkdir -p "$evidence"
evidence=$(realpath "$evidence")
report_failure() {
  local status=$? log
  trap - ERR
  printf 'Jazzy validation failed with exit code %s. Recent diagnostic logs follow.\n' "$status" >&2
  for log in "$evidence"/rosdep-update.log "$evidence"/apt-update.log "$evidence"/rosdep.log \
      "$evidence"/build.log "$evidence"/colcon-test.log "$evidence"/colcon-test-result.log \
      "$evidence"/regressions.log "$evidence"/tutorial-sensors/*.log \
      "$evidence"/tutorial-sensors/collection.json "$evidence"/simple_rover/launch.log \
      "$evidence"/simple_rover/result.json "$evidence"/f1tenth_sim/launch.log \
      "$evidence"/f1tenth_sim/result.json; do
    [[ -f $log ]] || continue
    printf '\n%s\n' "$log" >&2
    tail -n 100 "$log" >&2 || true
  done
  exit "$status"
}
trap report_failure ERR
export CTEST_PARALLEL_LEVEL=1
export ROS_DOMAIN_ID=$((100 + $$ % 100))
export GZ_PARTITION="jazzy_full_tests_$$_${RANDOM}"
cd "$source_root"
set +u
source /opt/ros/jazzy/setup.bash
set -u
# Apply the mounted checkout exception to child test processes without changing global Git settings.
export GIT_CONFIG_GLOBAL="$evidence/gitconfig"
git config --file "$GIT_CONFIG_GLOBAL" safe.directory "$source_root"
git rev-parse HEAD > "$evidence/source-sha.txt"
gz sim --versions > "$evidence/gazebo-version.txt"
rosdep update --rosdistro jazzy > "$evidence/rosdep-update.log" 2>&1
apt-get update > "$evidence/apt-update.log" 2>&1
rosdep install --from-paths examples/ros2_ws/src --ignore-src --rosdistro jazzy -y > "$evidence/rosdep.log" 2>&1
dpkg-query -W > "$evidence/packages.txt"
bridge_version=$(dpkg-query -W -f='${Version}' ros-jazzy-ros-gz-bridge)
dpkg --compare-versions "$bridge_version" ge 1.0.22 || {
  printf 'ros_gz_bridge >= 1.0.22 is required; installed: %s\n' "$bridge_version" >&2
  exit 1
}
cd examples/ros2_ws
colcon build --symlink-install --cmake-args -DBUILD_TESTING=ON > "$evidence/build.log" 2>&1
set +u
source install/setup.bash
set -u
colcon test --executor sequential --event-handlers console_direct+ > "$evidence/colcon-test.log" 2>&1
colcon test-result --all --verbose > "$evidence/colcon-test-result.log" 2>&1
cat "$evidence/colcon-test-result.log"
cd "$source_root"
python3 -m pytest -q scripts/test_final_project.py scripts/test_beginner_sensors.py \
  scripts/test_rover_examples.py scripts/test_sensor_rendering_contract.py > "$evidence/regressions.log" 2>&1
export TUTORIAL_INSTALL_BASE="$source_root/examples/ros2_ws/install"
bash scripts/check_intermediate_sensors.sh --launch --evidence "$evidence/tutorial-sensors"
cat "$evidence/tutorial-sensors/collection.json"
for package in simple_rover f1tenth_sim; do
  xvfb-run -a -s '-screen 0 1440x1000x24' python3 scripts/check_final_project_runtime.py \
    --package "$package" --evidence "$evidence/$package" --rviz
  cat "$evidence/$package/result.json"
done
