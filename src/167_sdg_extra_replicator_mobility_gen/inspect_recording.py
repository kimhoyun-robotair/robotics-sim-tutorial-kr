"""Inspect real MobilityGen recording layout without launching Isaac Sim."""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("recording", type=Path)
    args = parser.parse_args()
    root = args.recording.expanduser()
    config = json.loads((root / "config.json").read_text())
    for key in ("robot_type", "scenario_type", "scene_usd"):
        if not config.get(key):
            raise ValueError(f"Missing configuration field: {key}")
    paths = list((root / "state" / "common").glob("*.npy"))
    if not paths:
        raise ValueError("No recorded common state files")
    steps = sorted(int(path.stem) for path in paths)
    print(json.dumps({"configuration":config,"state_count":len(steps),"first_step":steps[0],"last_step":steps[-1],
                      "sensor_files":{name:sum(path.is_file() for path in (root / "state" / name).rglob("*")) for name in ("rgb","segmentation","depth","normals")}},indent=2))


if __name__ == "__main__":
    main()
