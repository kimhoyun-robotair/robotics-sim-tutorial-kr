"""Isaac Sim을 실행하지 않고 실제 DataLogger JSON의 구조와 시각을 검사한다."""
import argparse
import json
import math
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    args = parser.parse_args()
    frames = json.loads(args.log.read_text())["Isaac Sim Data"]
    if not frames:
        raise ValueError("Empty log")
    previous = -math.inf
    for index, frame in enumerate(frames):
        timestamp = float(frame["current_time"])
        if not math.isfinite(timestamp) or timestamp <= previous:
            raise ValueError(f"Frame {index}: non-increasing simulation time")
        previous = timestamp
        for key, length in [("joint_positions", 9), ("applied_joint_positions", 9), ("target_position", 3), ("target_orientation", 4)]:
            values = frame["data"][key]
            if len(values) != length or not all(isinstance(value, (int, float)) and math.isfinite(value) for value in values):
                raise ValueError(f"Frame {index}: invalid {key}")
    print(json.dumps({"frames": len(frames), "first_time_s": frames[0]["current_time"],
                      "last_time_s": frames[-1]["current_time"], "first_frame": frames[0]}, indent=2))


if __name__ == "__main__":
    main()
