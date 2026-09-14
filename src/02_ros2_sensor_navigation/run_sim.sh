#!/usr/bin/env bash
set -euo pipefail
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
isaac_dir="${ISAAC_SIM_PATH:-$HOME/isaacsim}"
if [[ ! -x "$isaac_dir/python.sh" ]]; then
    echo "ISAAC_SIM_PATH를 Isaac Sim 5.1 설치 디렉터리로 설정하세요." >&2
    exit 1
fi
# ROS-side Python과 Kit의 Python ABI가 섞이지 않도록 이 자식 프로세스만 초기화한다.
unset ROS_DISTRO PYTHONPATH AMENT_PREFIX_PATH CMAKE_PREFIX_PATH COLCON_PREFIX_PATH LD_LIBRARY_PATH
set +u
source "$isaac_dir/setup_ros_env.sh"
set -u
exec "$isaac_dir/python.sh" "$project_dir/run.py" "$@"
