"""Expand a TurtleBot xacro/URDF without overwriting an existing output."""
import argparse
from pathlib import Path
import subprocess

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("urdf", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = args.urdf.expanduser().resolve(strict=True)
    if args.output.exists():
        parser.error("output already exists; choose a new path")
    result = subprocess.run(["xacro", str(source), "namespace:="], cwd=source.parent,
                            check=True, capture_output=True, text=True)
    import xml.etree.ElementTree as ET
    robot = ET.fromstring(result.stdout)
    names = {joint.attrib["name"] for joint in robot.findall("joint")}
    expected = {"wheel_left_joint", "wheel_right_joint"}
    if not expected.issubset(names):
        raise ValueError(f"Wheel joints missing: {expected - names}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        stream.write(result.stdout)
    print("expanded robot=", robot.attrib.get("name"), "joints=", sorted(names))

if __name__ == "__main__":
    main()
