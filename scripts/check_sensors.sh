#!/usr/bin/env bash
set -eo pipefail

unset COLCON_CURRENT_PREFIX
source /opt/ros/jazzy/setup.bash
set -u

project_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
source "$project_root/scripts/lib/owned_process.sh"
evidence=''
expectations="$project_root/examples/ros2_ws/src/tutorial_bot_gazebo/config/sensor_expectations.yaml"
xacro_path="$project_root/examples/ros2_ws/src/tutorial_bot_description/urdf/stages/04-sensors-final.xacro"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --evidence)
      evidence=$2
      shift 2
      ;;
    --expectations)
      expectations=$2
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
export ROS_DOMAIN_ID=$((40 + $$ % 160))
export GZ_PARTITION="tutorial_bot_beginner_sensors_${ROS_DOMAIN_ID}_$$"
owned_validate_isolation "$ROS_DOMAIN_ID" "$GZ_PARTITION"
model_sdf=$(mktemp)
server_log=$(mktemp)
lidar_message=$(mktemp)
camera_message=$(mktemp)
imu_message=$(mktemp)
server_pid=''
run_status=fail

cleanup() {
  if [ -n "$server_pid" ]; then
    owned_stop_pgid "$server_pid"
    wait "$server_pid" 2>/dev/null || true
  fi
  rm -f "$model_sdf" "$server_log" "$lidar_message" "$camera_message" "$imu_message"
  if [ -n "$evidence" ]; then
    printf '{"schema_version":1,"status":"%s","owned_roots":[%s],"survivors":[]}\n' \
      "$run_status" "${server_pid:-}" > "$evidence/cleanup.json"
  fi
}

interrupted() {
  run_status=interrupted
  exit 130
}

trap cleanup EXIT
trap interrupted INT TERM

topic_type() {
  gz topic -i -t "$1" | awk -F ', ' '/gz\.msgs\./ { print $2; exit }'
}

message_rate() {
  awk '
    function remember(stamp) {
      stamps[++count] = stamp
      have_sec = 0
    }
    $1 == "sec:" {
      if (have_sec) remember(sec)
      sec = $2
      have_sec = 1
      next
    }
    have_sec && $1 == "nsec:" {
      remember(sec + $2 / 1000000000)
      next
    }
    have_sec && $1 == "data" {
      remember(sec)
    }
    END {
      if (have_sec) remember(sec)
      for (idx = 2; idx <= count; idx += 1) intervals[idx - 1] = stamps[idx] - stamps[idx - 1]
      interval_count = count - 1
      for (idx = 2; idx <= interval_count; idx += 1) {
        candidate = intervals[idx]
        position = idx - 1
        while (position >= 1 && intervals[position] > candidate) {
          intervals[position + 1] = intervals[position]
          position -= 1
        }
        intervals[position + 1] = candidate
      }
      if (interval_count > 0 && intervals[int((interval_count + 1) / 2)] > 0) {
        printf "%.6f", 1 / intervals[int((interval_count + 1) / 2)]
      }
    }
  ' "$1"
}

xacro "$xacro_path" > "$model_sdf"
gz sdf -k "$model_sdf"
python3 - "$model_sdf" "$expectations" "${evidence:-/dev/null}" <<'PY'
from __future__ import annotations

import json
import math
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

import yaml

root = ET.parse(sys.argv[1]).getroot()
expected = yaml.safe_load(Path(sys.argv[2]).read_text(encoding="utf-8"))

def sensor(name: str) -> ET.Element:
    found = root.find(f".//sensor[@name='{name}']")
    if found is None:
        raise SystemExit(f"missing sensor {name}")
    return found

def value(node: ET.Element, path: str) -> float:
    text = node.findtext(path)
    if text is None:
        raise SystemExit(f"missing sensor field {path}")
    return float(text)

lidar = sensor("lidar")
camera = sensor("camera")
imu = sensor("imu")
checks = {
    "lidar_type": lidar.attrib.get("type") == "gpu_lidar",
    "lidar_rate": value(lidar, "update_rate") == expected["lidar"]["expected_rate_hz"],
    "lidar_samples": value(lidar, "lidar/scan/horizontal/samples") == expected["lidar"]["samples"],
    "lidar_min_angle": math.isclose(value(lidar, "lidar/scan/horizontal/min_angle"), expected["lidar"]["min_angle_rad"], abs_tol=1e-11),
    "lidar_max_angle": math.isclose(value(lidar, "lidar/scan/horizontal/max_angle"), expected["lidar"]["max_angle_rad"], abs_tol=1e-11),
    "lidar_min_range": value(lidar, "lidar/range/min") == expected["lidar"]["min_range_m"],
    "lidar_max_range": value(lidar, "lidar/range/max") == expected["lidar"]["max_range_m"],
    "lidar_resolution": value(lidar, "lidar/range/resolution") == 0.01,
    "lidar_noise": value(lidar, "lidar/noise/stddev") == expected["lidar"]["noise_stddev_m"],
    "camera_type": camera.attrib.get("type") == "rgbd_camera",
    "camera_rate": value(camera, "update_rate") == expected["camera"]["expected_rate_hz"],
    "camera_hfov": value(camera, "camera/horizontal_fov") == expected["camera"]["hfov_rad"],
    "camera_width": value(camera, "camera/image/width") == expected["camera"]["width_px"],
    "camera_height": value(camera, "camera/image/height") == expected["camera"]["height_px"],
    "camera_near": value(camera, "camera/clip/near") == expected["camera"]["near_clip_m"],
    "camera_far": value(camera, "camera/clip/far") == expected["camera"]["far_clip_m"],
    "imu_rate": value(imu, "update_rate") == expected["imu"]["expected_rate_hz"],
    "imu_noise": all(float(item.text or "nan") == expected["imu"]["noise_stddev"] for item in imu.findall(".//stddev")),
}
report = {"schema_version": 1, "status": "pass" if all(checks.values()) else "fail", "checks": checks}
if sys.argv[3] != "/dev/null":
    Path(sys.argv[3], "source-contract.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
if not all(checks.values()):
    print(json.dumps(report, sort_keys=True), file=sys.stderr)
    raise SystemExit(1)
PY
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

for _ in $(seq 1 50); do
  if gz topic -l | grep -qx '/tutorial_bot/lidar' && \
    gz topic -l | grep -qx '/tutorial_bot/camera/image' && \
    gz topic -l | grep -qx '/tutorial_bot/imu'; then
    break
  fi
  sleep 0.2
done

if ! gz topic -l | grep -qx '/tutorial_bot/lidar' || \
  ! gz topic -l | grep -qx '/tutorial_bot/camera/image'; then
  gz topic -l >&2
  sed -n '1,160p' "$server_log" >&2
  exit 1
fi

if [ "$(topic_type /tutorial_bot/lidar)" != 'gz.msgs.LaserScan' ]; then
  gz topic -i -t /tutorial_bot/lidar >&2
  exit 1
fi

if [ "$(topic_type /tutorial_bot/camera/image)" != 'gz.msgs.Image' ]; then
  gz topic -i -t /tutorial_bot/camera/image >&2
  exit 1
fi

if [ "$(topic_type /tutorial_bot/imu)" != 'gz.msgs.IMU' ]; then
  gz topic -i -t /tutorial_bot/imu >&2
  exit 1
fi

timeout 20 gz topic -e -t /tutorial_bot/lidar -n 11 > "$lidar_message"
timeout 20 gz topic -e -t /tutorial_bot/camera/image -n 31 > "$camera_message"
timeout 20 gz topic -e -t /tutorial_bot/imu -n 101 > "$imu_message"

scan_count=$(awk '$1 == "count:" { print $2; exit }' "$lidar_message")
finite_range_count=$(awk '
  $1 == "ranges:" && $2 != "inf" && $2 != "-inf" && $2 != "nan" { count += 1 }
  END { print count + 0 }
' "$lidar_message")
image_width=$(awk '$1 == "width:" { print $2; exit }' "$camera_message")
image_height=$(awk '$1 == "height:" { print $2; exit }' "$camera_message")
angle_min=$(awk '$1 == "angle_min:" { print $2; exit }' "$lidar_message")
angle_max=$(awk '$1 == "angle_max:" { print $2; exit }' "$lidar_message")
range_min=$(awk '$1 == "range_min:" { print $2; exit }' "$lidar_message")
range_max=$(awk '$1 == "range_max:" { print $2; exit }' "$lidar_message")
lidar_messages=$(awk '$1 == "count:" { count += 1 } END { print count + 0 }' "$lidar_message")
camera_messages=$(awk '$1 == "width:" { count += 1 } END { print count + 0 }' "$camera_message")
imu_messages=$(awk '$1 == "angular_velocity" && $2 == "{" { count += 1 } END { print count + 0 }' "$imu_message")
lidar_rate=$(message_rate "$lidar_message")
camera_rate=$(message_rate "$camera_message")
imu_rate=$(message_rate "$imu_message")

if [ -n "$evidence" ]; then
  cp "$lidar_message" "$evidence/lidar.log"
  cp "$camera_message" "$evidence/camera.log"
  cp "$imu_message" "$evidence/imu.log"
  cp "$server_log" "$evidence/gazebo.log"
fi

if ! awk -v scan_count="$scan_count" -v finite_range_count="$finite_range_count" \
  -v image_width="$image_width" -v image_height="$image_height" -v angle_min="$angle_min" \
  -v angle_max="$angle_max" -v range_min="$range_min" -v range_max="$range_max" \
  -v lidar_messages="$lidar_messages" -v camera_messages="$camera_messages" -v imu_messages="$imu_messages" \
  -v lidar_rate="$lidar_rate" -v camera_rate="$camera_rate" -v imu_rate="$imu_rate" \
  'BEGIN { exit !(scan_count == 360 && finite_range_count > 0 && image_width == 320 && image_height == 240 && angle_min < -3.14 && angle_max > 3.14 && range_min == 0.12 && range_max == 10.0 && lidar_messages >= 11 && camera_messages >= 31 && imu_messages >= 101 && lidar_rate >= 9 && lidar_rate <= 11 && camera_rate >= 27 && camera_rate <= 33 && imu_rate >= 90 && imu_rate <= 110) }'; then
  printf 'Sensor messages did not match the parsed contract: scan=%s finite=%s angles=%s..%s ranges=%s..%s image=%sx%s messages=%s/%s/%s rates=%s/%s/%s\n' \
    "$scan_count" "$finite_range_count" "$angle_min" "$angle_max" "$range_min" "$range_max" \
    "$image_width" "$image_height" "$lidar_messages" "$camera_messages" "$imu_messages" \
    "$lidar_rate" "$camera_rate" "$imu_rate" >&2
  exit 1
fi

printf 'LiDAR scan verified: %s ranges, %s obstacle readings.\n' "$scan_count" "$finite_range_count"
printf 'Camera image verified: %sx%s.\n' "$image_width" "$image_height"
printf 'Sensor cadence verified: LiDAR=%s Hz, Camera=%s Hz, IMU=%s Hz.\n' \
  "$lidar_rate" "$camera_rate" "$imu_rate"
if [ -n "$evidence" ]; then
  printf '{"schema_version":1,"status":"pass","lidar":{"samples":%s,"messages":%s,"finite_ranges":%s,"angle_min":%s,"angle_max":%s,"range_min":%s,"range_max":%s,"rate_hz":%s},"camera":{"width":%s,"height":%s,"messages":%s,"rate_hz":%s},"imu":{"messages":%s,"rate_hz":%s}}\n' \
    "$scan_count" "$lidar_messages" "$finite_range_count" "$angle_min" "$angle_max" "$range_min" "$range_max" "$lidar_rate" "$image_width" "$image_height" "$camera_messages" "$camera_rate" "$imu_messages" "$imu_rate" > "$evidence/result.json"
fi
run_status=pass
