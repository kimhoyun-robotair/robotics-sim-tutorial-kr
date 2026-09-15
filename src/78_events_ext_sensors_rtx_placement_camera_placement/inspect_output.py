"""Validate real Camera Placement output and measure camera/focus distances."""
import argparse
import json
import math
from pathlib import Path


def inspect(path: Path) -> dict:
    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        raise ValueError("camera_info_payload.json must contain an object")
    rows = []
    seen = set()
    for direction, records in data.items():
        if not isinstance(records, list):
            raise ValueError(f"{direction}: expected a list")
        for camera in records:
            name = camera['camera_path']
            if not name.startswith('/World/Cameras/') or name in seen:
                raise ValueError(f"Invalid or duplicate camera path: {name}")
            seen.add(name)
            position, focus = camera['camera_position'], camera['focus_point']
            for vector in (position, focus):
                if len(vector) != 3 or not all(isinstance(v, (float, int)) and math.isfinite(v) for v in vector):
                    raise ValueError(f"{name}: expected three finite coordinates")
            distance = math.dist(position, focus)
            if distance == 0:
                raise ValueError(f"{name}: position and focus point coincide")
            rows.append({'camera': name, 'direction_group': direction, 'height_m': position[2],
                         'focus_distance_m': distance,
                         'look_down_deg': math.degrees(math.asin((position[2] - focus[2]) / distance))})
    if not rows:
        raise ValueError('No cameras were exported')
    return {'camera_count': len(rows), 'cameras': rows,
            'coverage_note': 'JSON camera poses alone do not establish actual visibility or coverage.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', type=Path, help='Actual camera_info_payload.json exported by the native tool')
    args = parser.parse_args()
    print(json.dumps(inspect(args.path), ensure_ascii=False, indent=2))
