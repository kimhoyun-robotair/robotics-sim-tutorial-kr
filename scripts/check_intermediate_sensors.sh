#!/usr/bin/env bash
# allow: SIZE_OK — one self-contained ROS E2E harness owns process cleanup and simultaneous sensor collection.
set -euo pipefail

project_root=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)
source "$project_root/scripts/lib/owned_process.sh"
evidence_dir=''
expected_width=''
matrix_install_base=${TUTORIAL_INSTALL_BASE:-}

while (($#)); do
  case "$1" in
    --launch) shift ;;
    --evidence) evidence_dir=${2:?--evidence requires a directory}; shift 2 ;;
    --expected-width) expected_width=${2:?--expected-width requires an integer}; shift 2 ;;
    *) printf 'Unknown argument: %s\n' "$1" >&2; exit 2 ;;
  esac
done
[[ -n $evidence_dir ]] || { printf '%s\n' '--evidence is required.' >&2; exit 2; }
[[ -z $expected_width || $expected_width =~ ^[1-9][0-9]*$ ]] || {
  printf 'Invalid expected width: %s\n' "$expected_width" >&2
  exit 2
}

mkdir -p "$evidence_dir"
evidence_dir=$(CDPATH='' cd -- "$evidence_dir" && pwd)
temp_root=$(mktemp -d /tmp/tutorial-bot-sensors.XXXXXX)
domain_id=$((80 + $$ % 120))
partition="tutorial_bot_task6_${domain_id}_$$"
process_groups=()

cleanup() {
  local cleanup_ok=true group
  for group in "${process_groups[@]}"; do
    [[ $group =~ ^[1-9][0-9]*$ ]] || continue
    ps -eo pid=,pgid= | awk -v pgid="$group" '$2 == pgid {print $1}' >> "$evidence_dir/pids.log"
    kill -TERM -- "-$group" 2>/dev/null || true
    wait "$group" 2>/dev/null || true
    for _ in {1..50}; do
      ps -eo pgid= | awk -v pgid="$group" '$1 == pgid {found=1} END {exit !found}' || break
      sleep 0.1
    done
    if ps -eo pgid= | awk -v pgid="$group" '$1 == pgid {found=1} END {exit !found}'; then
      kill -KILL -- "-$group" 2>/dev/null || true
      cleanup_ok=false
    fi
  done
  if [[ $temp_root == /tmp/tutorial-bot-sensors.* ]]; then
    find "$temp_root" -depth -delete 2>/dev/null || cleanup_ok=false
  else
    cleanup_ok=false
  fi
  {
    printf 'cleanup_ok=%s\n' "$cleanup_ok"
    printf 'process_groups_absent=%s\n' "$([[ $cleanup_ok == true ]] && echo true || echo false)"
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
export LANG=C.UTF-8 LC_ALL=C.UTF-8
export ROS_DOMAIN_ID=$domain_id GZ_PARTITION=$partition ROS2CLI_DISABLE_DAEMON=1
owned_validate_isolation "$ROS_DOMAIN_ID" "$GZ_PARTITION"
export ROS_HOME="$temp_root/ros-home"
unset AMENT_PREFIX_PATH CMAKE_PREFIX_PATH COLCON_PREFIX_PATH PYTHONPATH LD_LIBRARY_PATH
unset GZ_SIM_RESOURCE_PATH GAZEBO_MODEL_PATH
mkdir -p "$ROS_HOME"
set +u
source /opt/ros/jazzy/setup.bash
set -u

: > "$evidence_dir/pids.log"
for dependency in ros_gz_bridge ros_gz_image ros_gz_sim robot_state_publisher xacro; do
  ros2 pkg prefix "$dependency" >> "$evidence_dir/dependencies.log"
done

if [[ -n $matrix_install_base ]]; then
  [[ $matrix_install_base == /* && -f $matrix_install_base/local_setup.bash ]] || {
    printf 'Invalid TUTORIAL_INSTALL_BASE: %s\n' "$matrix_install_base" >&2
    exit 2
  }
  active_install_base=$matrix_install_base
  printf 'reused_install_base=%s\n' "$active_install_base" > "$evidence_dir/build.command"
  printf 'reused_install_base=%s\n' "$active_install_base" > "$evidence_dir/build.log"
else
  build_command=(colcon --log-base "$temp_root/log" build
    --base-paths "$project_root/examples/ros2_ws/src"
    --packages-select tutorial_bot_description tutorial_bot_gazebo tutorial_bot_control tutorial_bot_bringup
    --build-base "$temp_root/build" --install-base "$temp_root/install"
    --event-handlers console_direct+)
  printf '%q ' "${build_command[@]}" > "$evidence_dir/build.command"
  printf '\n' >> "$evidence_dir/build.command"
  setsid "${build_command[@]}" > "$evidence_dir/build.log" 2>&1 &
  process_groups+=("$!")
  wait "${process_groups[-1]}"
  active_install_base=$temp_root/install
fi
set +u
source "$active_install_base/local_setup.bash"
set -u
(cd "$active_install_base" && find . -type f -print0 | sort -z | xargs -0 sha256sum) \
  | sha256sum > "$evidence_dir/install-tree.sha256"

expectations=$(ros2 pkg prefix --share tutorial_bot_gazebo)/config/sensor_expectations.yaml
world=$(ros2 pkg prefix --share tutorial_bot_gazebo)/worlds/sensor-test.sdf
xacro_file=$(ros2 pkg prefix --share tutorial_bot_description)/urdf/tutorial_bot.urdf.xacro
bridge=$(ros2 pkg prefix --share tutorial_bot_bringup)/config/bridge-intermediate.yaml
for installed in "$expectations" "$world" "$xacro_file" "$bridge"; do
  [[ -f $installed ]] || { printf 'Missing installed resource: %s\n' "$installed" >&2; exit 1; }
  printf '%s\n' "$installed" >> "$evidence_dir/installed-resources.log"
done
xacro "$xacro_file" control_backend:=gazebo_diff_drive > "$temp_root/tutorial_bot.urdf"

setsid gz sim -s -r --seed 42 "$world" > "$evidence_dir/gazebo.log" 2>&1 &
process_groups+=("$!")
setsid ros2 run robot_state_publisher robot_state_publisher "$temp_root/tutorial_bot.urdf" \
  --ros-args -p use_sim_time:=true > "$evidence_dir/state-publisher.log" 2>&1 &
process_groups+=("$!")
setsid ros2 run ros_gz_bridge parameter_bridge --ros-args -p config_file:="$bridge" \
  > "$evidence_dir/bridge.log" 2>&1 &
process_groups+=("$!")
setsid ros2 run ros_gz_image image_bridge /tutorial_bot/camera/image \
  /tutorial_bot/camera/depth/image --ros-args \
  -r /tutorial_bot/camera/image:=/camera/image \
  -r /tutorial_bot/camera/depth/image:=/camera/depth/image \
  > "$evidence_dir/image-bridge.log" 2>&1 &
process_groups+=("$!")

for _ in {1..100}; do
  gz service -s /world/sensor_test/control --reqtype gz.msgs.WorldControl \
    --reptype gz.msgs.Boolean --timeout 1000 --req 'pause: false' >/dev/null 2>&1 && break
  sleep 0.1
done
ros2 run ros_gz_sim create -world sensor_test -name tutorial_bot \
  -file "$temp_root/tutorial_bot.urdf" -z 0.12 > "$evidence_dir/spawn.log" 2>&1

topics=(/scan /imu /camera/image /camera/camera_info /camera/depth/image
  /camera/depth/camera_info /camera/points)
for _ in {1..200}; do
  ready=true
  for topic in "${topics[@]}"; do
    ros2 topic type "$topic" >/dev/null 2>&1 || ready=false
  done
  [[ $ready == true ]] && break
  sleep 0.1
done
[[ ${ready:-false} == true ]] || { printf '%s\n' 'Sensor topics did not become ready.' >&2; exit 1; }
ros2 topic list -t > "$evidence_dir/topics.log"

python3 - "$expectations" "$expected_width" "$evidence_dir/collection.json" <<'PY'
from __future__ import annotations

import json
import math
import statistics
import struct
import sys
import time
from collections.abc import Callable
from pathlib import Path

import rclpy
import yaml
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import CameraInfo, Image, Imu, LaserScan, PointCloud2

config = yaml.safe_load(Path(sys.argv[1]).read_text(encoding="utf-8"))
width_override = int(sys.argv[2]) if sys.argv[2] else None
output_path = Path(sys.argv[3])
errors: list[str] = []
stamps: dict[str, list[int]] = {name: [] for name in (
    "scan", "imu", "rgb", "rgb_info", "depth", "depth_info", "points"
)}
frames: dict[str, set[str]] = {name: set() for name in stamps}
warmup_stamps: dict[str, list[int]] = {name: [] for name in stamps}
laser_residuals: list[float] = []
laser_extreme: list[float | int] = [0, 0.0, 0.0, 0.0]
truth_ranges = config["lidar"]["truth_ranges_m"]
lidar_sigma = config["lidar"]["noise_stddev_m"]
edge_indices = {
    index
    for index, truth in enumerate(truth_ranges)
    if max(
        abs(truth - truth_ranges[index - 1]),
        abs(truth - truth_ranges[(index + 1) % len(truth_ranges)]),
    ) > 8 * lidar_sigma
}
imu_values: list[list[float]] = [[] for _ in range(6)]
point_finite = 0
point_total = 0
laser_finite = 0
laser_edge_samples = 0
laser_edge_violations = 0
dimensions: dict[str, list[int]] = {}
camera_infos: dict[str, CameraInfo] = {}
collecting = False

def stamp_ns(message: LaserScan | Imu | Image | CameraInfo | PointCloud2) -> int:
    return message.header.stamp.sec * 1_000_000_000 + message.header.stamp.nanosec

def remember(name: str, message: LaserScan | Imu | Image | CameraInfo | PointCloud2) -> None:
    if collecting:
        stamps[name].append(stamp_ns(message))
        frames[name].add(message.header.frame_id)
    else:
        warmup_stamps[name].append(stamp_ns(message))

def scan_callback(message: LaserScan) -> None:
    global laser_edge_samples, laser_edge_violations, laser_finite
    remember("scan", message)
    if not collecting:
        return
    dimensions["scan"] = [len(message.ranges)]
    dimensions["scan_meta"] = [message.angle_min, message.angle_max, message.range_min, message.range_max]
    for index, value in enumerate(message.ranges):
        if math.isfinite(value):
            laser_finite += 1
            if index in edge_indices:
                laser_edge_samples += 1
                neighbors = (
                    truth_ranges[index - 1],
                    truth_ranges[index],
                    truth_ranges[(index + 1) % len(truth_ranges)],
                )
                if not min(neighbors) - 5 * lidar_sigma <= value <= max(neighbors) + 5 * lidar_sigma:
                    laser_edge_violations += 1
                continue
            residual = value - truth_ranges[index]
            laser_residuals.append(residual)
            if abs(residual) > abs(float(laser_extreme[3])):
                laser_extreme[:] = [index, value, truth_ranges[index], residual]

def imu_callback(message: Imu) -> None:
    remember("imu", message)
    if collecting:
        values = (message.angular_velocity.x, message.angular_velocity.y, message.angular_velocity.z,
                  message.linear_acceleration.x, message.linear_acceleration.y, message.linear_acceleration.z)
        for retained, value in zip(imu_values, values, strict=True):
            if math.isfinite(value):
                retained.append(value)

def image_callback(name: str) -> Callable[[Image], None]:
    def callback(message: Image) -> None:
        remember(name, message)
        if collecting:
            dimensions[name] = [message.width, message.height]
    return callback

def info_callback(name: str) -> Callable[[CameraInfo], None]:
    def callback(message: CameraInfo) -> None:
        remember(name, message)
        if collecting:
            camera_infos[name] = message
    return callback

def points_callback(message: PointCloud2) -> None:
    global point_finite, point_total
    remember("points", message)
    if not collecting:
        return
    dimensions["points"] = [message.width, message.height]
    offsets = {field.name: field.offset for field in message.fields}
    for index in range(0, message.width * message.height, 100):
        base = index * message.point_step
        xyz = struct.unpack_from("<fff", message.data, base + offsets["x"])
        point_total += 1
        point_finite += int(all(math.isfinite(value) for value in xyz))

rclpy.init()
node = Node("intermediate_sensor_checker")
node.create_subscription(LaserScan, "/scan", scan_callback, qos_profile_sensor_data)
node.create_subscription(Imu, "/imu", imu_callback, qos_profile_sensor_data)
node.create_subscription(Image, "/camera/image", image_callback("rgb"), qos_profile_sensor_data)
node.create_subscription(CameraInfo, "/camera/camera_info", info_callback("rgb_info"), qos_profile_sensor_data)
node.create_subscription(Image, "/camera/depth/image", image_callback("depth"), qos_profile_sensor_data)
node.create_subscription(CameraInfo, "/camera/depth/camera_info", info_callback("depth_info"), qos_profile_sensor_data)
node.create_subscription(PointCloud2, "/camera/points", points_callback, qos_profile_sensor_data)

warmup_started = time.monotonic()
warmup_deadline = warmup_started + 20.0
warmup_counts = {"scan": 20, "imu": 200, "rgb": 60, "rgb_info": 60,
                 "depth": 60, "depth_info": 60, "points": 60}
warmup_ready = False
while time.monotonic() < warmup_deadline:
    rclpy.spin_once(node, timeout_sec=0.05)
    warmup_seconds = time.monotonic() - warmup_started
    warmup_ready = warmup_seconds >= 2.0 and all(
        len(warmup_stamps[name]) >= count
        and all(current > previous for previous, current in zip(
            warmup_stamps[name], warmup_stamps[name][1:], strict=False
        ))
        for name, count in warmup_counts.items()
    )
    if warmup_ready:
        break
if not warmup_ready:
    raise RuntimeError(
        "sensor warmup did not reach two seconds of monotonic samples on every stream"
    )
collecting = True
collection_started = time.monotonic()
minimum_collection_end = collection_started + 10.0
collection_deadline = collection_started + 12.0
minimum_counts = {"scan": 95, "imu": 950, "rgb": 285, "rgb_info": 285,
                  "depth": 285, "depth_info": 285, "points": 285}
while time.monotonic() < minimum_collection_end or (
    time.monotonic() < collection_deadline
    and any(len(stamps[name]) < count for name, count in minimum_counts.items())
):
    rclpy.spin_once(node, timeout_sec=0.02)
collection_seconds = time.monotonic() - collection_started
node.destroy_node()
rclpy.shutdown()

rates = {"scan": config["lidar"]["expected_rate_hz"], "imu": config["imu"]["expected_rate_hz"],
         "rgb": config["camera"]["expected_rate_hz"], "rgb_info": config["camera"]["expected_rate_hz"],
         "depth": config["camera"]["expected_rate_hz"], "depth_info": config["camera"]["expected_rate_hz"],
         "points": config["camera"]["expected_rate_hz"]}
measured_rates: dict[str, float] = {}
for name, expected_rate in rates.items():
    values = stamps[name]
    ratio = len(values) / (expected_rate * 10.0)
    if ratio < 0.95:
        errors.append(f"{name}: received={len(values)} expected={expected_rate * 10:.0f} ratio={ratio:.3f}")
    if any(current <= previous for previous, current in zip(values, values[1:])):
        errors.append(f"{name}: timestamps are not strictly increasing")
    if len(values) >= 2:
        measured = 1e9 / statistics.median(b - a for a, b in zip(values, values[1:]))
        measured_rates[name] = measured
        if not 0.8 * expected_rate <= measured <= 1.2 * expected_rate:
            errors.append(f"{name}: median_rate={measured:.3f} expected={expected_rate:.3f}")

expected_frames = {"scan": config["lidar"]["frame_id"], "imu": config["imu"]["frame_id"]}
expected_frames.update({name: config["camera"]["message_frame_id"] for name in ("rgb", "rgb_info", "depth", "depth_info", "points")})
for name, expected_frame in expected_frames.items():
    if frames[name] != {expected_frame}:
        errors.append(f"{name}: frame expected={expected_frame} actual={sorted(frames[name])}")

scan_meta = dimensions.get("scan_meta", [])
if dimensions.get("scan") != [config["lidar"]["samples"]]:
    errors.append(f"scan: samples expected={config['lidar']['samples']} actual={dimensions.get('scan')}")
expected_meta = [config["lidar"][key] for key in ("min_angle_rad", "max_angle_rad", "min_range_m", "max_range_m")]
if len(scan_meta) != 4 or any(abs(actual - expected) > 1e-5 for actual, expected in zip(scan_meta, expected_meta, strict=True)):
    errors.append(f"scan: metadata expected={expected_meta} actual={scan_meta}")
finite_ratio = laser_finite / max(1, len(stamps["scan"]) * config["lidar"]["samples"])
if finite_ratio < 0.95:
    errors.append(f"scan: finite_ratio={finite_ratio:.3f} expected>=0.950")
if laser_edge_violations:
    errors.append(
        f"scan: edge_geometry_violations={laser_edge_violations} "
        f"edge_samples={laser_edge_samples}"
    )

expected_width = width_override or config["camera"]["width_px"]
for name in ("rgb", "depth"):
    actual = dimensions.get(name)
    expected = [expected_width, config["camera"]["height_px"]]
    if actual != expected:
        errors.append(f"{name}: dimensions expected={expected[0]}x{expected[1]} actual={actual[0] if actual else 'missing'}x{actual[1] if actual else 'missing'}")
for name in ("rgb_info", "depth_info"):
    info = camera_infos.get(name)
    if info is None:
        errors.append(f"{name}: CameraInfo missing")
        continue
    if [info.width, info.height] != [config["camera"]["width_px"], config["camera"]["height_px"]]:
        errors.append(f"{name}: dimensions mismatch")
    if any(abs(actual - expected) > 1e-5 for actual, expected in zip(info.k, config["camera"]["camera_info"]["k"], strict=True)):
        errors.append(f"{name}: K intrinsics mismatch")
    if any(abs(actual - expected) > 1e-5 for actual, expected in zip(info.p, config["camera"]["camera_info"]["p"], strict=True)):
        errors.append(f"{name}: P intrinsics mismatch")
if point_finite / max(1, point_total) < 0.95:
    errors.append(f"points: finite_ratio={point_finite / max(1, point_total):.3f} expected>=0.950")

noise_results: dict[str, dict[str, float | int]] = {}
def check_noise(name: str, values: list[float], truth: float, sigma: float, bias: float, tolerance: float) -> None:
    residuals = [value - truth - bias for value in values]
    count = len(residuals)
    mean = statistics.fmean(residuals) if residuals else math.nan
    deviation = statistics.stdev(residuals) if count >= 2 else math.nan
    maximum = max((abs(value) for value in residuals), default=math.inf)
    five_sigma_limit = 5 * max(sigma, deviation)
    noise_results[name] = {"n": count, "mean_error": mean, "stddev": deviation,
                           "max_abs_residual": maximum, "five_sigma_limit": five_sigma_limit}
    mean_limit = max(5 * max(sigma, deviation) / math.sqrt(max(1, count)), tolerance)
    noise_results[name]["mean_limit"] = mean_limit
    if count < 100 or abs(mean) > mean_limit or not 0.5 * sigma <= deviation <= 1.5 * sigma or maximum > five_sigma_limit:
        errors.append(f"{name}: n={count} mean={mean:.8f} stddev={deviation:.8f} max={maximum:.8f} sigma={sigma:.8f}")

check_noise("lidar", laser_residuals, 0.0, config["lidar"]["noise_stddev_m"], config["lidar"]["bias_m"], 0.0)
imu_truth = [*config["imu"]["angular_velocity_truth_rad_s"], *config["imu"]["linear_acceleration_truth_m_s2"]]
for axis, values, truth, bias in zip(("wx", "wy", "wz", "ax", "ay", "az"), imu_values, imu_truth, [*config["imu"]["bias"], *config["imu"]["bias"]], strict=True):
    check_noise(f"imu_{axis}", values, truth, config["imu"]["noise_stddev"], bias, config["imu"]["bias_tolerance"])

result = {"passed": not errors, "warmup_seconds": warmup_seconds, "collection_seconds": collection_seconds, "counts": {name: len(value) for name, value in stamps.items()},
          "rates_hz": measured_rates, "frames": {name: sorted(value) for name, value in frames.items()}, "dimensions": dimensions,
          "finite": {"scan_ratio": finite_ratio, "point_ratio": point_finite / max(1, point_total), "point_samples": point_total,
                     "edge_indices": len(edge_indices), "edge_samples": laser_edge_samples,
                     "edge_geometry_violations": laser_edge_violations},
          "noise": noise_results, "laser_extreme": laser_extreme, "errors": errors}
output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
for error in errors:
    print(error, file=sys.stderr)
raise SystemExit(0 if not errors else 1)
PY

printf '%s\n' 'Advanced sensor checks passed.' | tee "$evidence_dir/nominal-observable.log"
