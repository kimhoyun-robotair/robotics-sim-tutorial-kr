#!/usr/bin/env bash
set -euo pipefail

scenario=nominal
internal_timeout=10
source_root=/source
evidence=/evidence

while (($#)); do
  case "$1" in
    --source) source_root=${2:-}; shift 2 ;;
    --evidence) evidence=${2:-}; shift 2 ;;
    --scenario) scenario=${2:-}; shift 2 ;;
    --internal-timeout) internal_timeout=${2:-}; shift 2 ;;
    *) printf 'unknown argument: %s\n' "$1" >&2; exit 64 ;;
  esac
done

case "$scenario" in
  nominal|plugin-missing|timeout|sigint-hold) ;;
  *) printf 'unknown scenario: %s\n' "$scenario" >&2; exit 64 ;;
esac
if [[ ! "$internal_timeout" =~ ^[1-9][0-9]*$ ]] || [[ ! -d "$source_root/examples/ros2_ws/src" ]]; then
  printf 'invalid source or timeout\n' >&2
  exit 64
fi

mkdir -p "$evidence" /work/source /work/build /work/install /work/log /ccache
if [[ "$scenario" == "timeout" ]]; then
  printf '{"scenario":"timeout","deadline_seconds":%d,"deadline_source":"internal","exit_code":124}\n' \
    "$internal_timeout" > "$evidence/scenario.json"
  sleep "$internal_timeout"
  exit 124
fi
if [[ "$scenario" == "sigint-hold" ]]; then
  trap 'exit 130' INT TERM
  printf '{"scenario":"sigint-hold","ready":true}\n' > "$evidence/scenario.json"
  while true; do sleep 1; done
fi
cp -a "$source_root/examples" "$source_root/scripts" /work/source/
set +u
# shellcheck source=/dev/null
source /opt/ros/jazzy/setup.bash
set -u
export GZ_CONFIG_PATH="/usr/share/gz${GZ_CONFIG_PATH:+:$GZ_CONFIG_PATH}"
export CCACHE_DIR=/ccache
export CMAKE_CXX_COMPILER_LAUNCHER=ccache
export CTEST_PARALLEL_LEVEL=1
export GZ_PARTITION="tutorial_bot_task14_tests_$$_${RANDOM}"
export LIBGL_ALWAYS_SOFTWARE=1
export GZ_SIM_RENDER_ENGINE_SERVER=ogre2

{
  awk -F= '$1 == "VERSION_ID" {gsub(/"/, "", $2); print "ubuntu=" $2}' /etc/os-release
  printf 'ros_distro=%s\n' "$ROS_DISTRO"
  dpkg-query -W -f='${Package}=${Version}\n' ros-jazzy-ros-base ros-jazzy-ros-gz-bridge gz-sim8-cli libgz-sim8-dev
  gz sim --versions
  gcc --version | head -n 1
  g++ --version | head -n 1
  ccache --version | head -n 1
} > "$evidence/resolved-versions.txt"

cd /work/source/examples/ros2_ws
rosdep update --rosdistro jazzy > "$evidence/rosdep-update.log" 2>&1
rosdep install --from-paths src/tutorial_bot_plugins --ignore-src --rosdistro jazzy -y \
  --skip-keys "gz-msgs10 gz-plugin2 gz-sim8 gz-transport13" \
  > "$evidence/rosdep.log" 2>&1
packages=(tutorial_bot_plugins tutorial_bot_description tutorial_bot_control tutorial_bot_gazebo tutorial_bot_bringup tutorial_bot_tests)
colcon --log-base /work/log build --build-base /work/build --install-base /work/install \
  --packages-select "${packages[@]}" --cmake-args -DBUILD_TESTING=ON \
  > "$evidence/build.log" 2>&1
set +u
# shellcheck source=/dev/null
source /work/install/setup.bash
set -u
colcon --log-base /work/test-log test --build-base /work/build --install-base /work/install \
  --executor sequential --packages-select tutorial_bot_plugins tutorial_bot_tests \
  --event-handlers console_direct+ --ctest-args -R \
  '^(advanced_contract|advanced_framework_cli|advanced_headless_integration|rover_examples|diagnostics_distance|diagnostics_enable_reset|diagnostics_enable_reset_concurrency|diagnostics_model_lifecycle|diagnostics_physics_cadence)$' \
  > "$evidence/test.log" 2>&1
colcon test-result --test-result-base /work/build --verbose > "$evidence/test-results.log" 2>&1

printf '{"packages":["tutorial_bot_plugins","tutorial_bot_gazebo","tutorial_bot_bringup","tutorial_bot_tests"],"build":true,"tests":true}\n' \
  > "$evidence/selected-workspace.json"
exec /work/source/scripts/check_advanced_course.sh \
  --scenario "$scenario" \
  --install-base /work/install \
  --evidence "$evidence/smoke" \
  --internal-readiness-timeout "$internal_timeout"
