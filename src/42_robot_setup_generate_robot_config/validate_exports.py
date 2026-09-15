"""내보낸 URDF와 Lula YAML의 관절/링크 이름 및 구 형상을 교차 검사한다."""
import argparse
from pathlib import Path
import xml.etree.ElementTree as ET


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("urdf", type=Path)
    parser.add_argument("descriptor", type=Path)
    args = parser.parse_args()
    import yaml
    robot = ET.parse(args.urdf).getroot()
    joints = {joint.attrib["name"] for joint in robot.findall("joint")}
    links = {link.attrib["name"] for link in robot.findall("link")}
    descriptor = yaml.safe_load(args.descriptor.read_text())
    missing = set(descriptor["cspace"]) - joints
    if missing:
        raise ValueError(f"Active joints absent from URDF: {sorted(missing)}")
    if len(descriptor["cspace"]) != len(descriptor["default_q"]):
        raise ValueError("default_q length differs from cspace")
    spheres = 0
    for group in descriptor.get("collision_spheres", []):
        for link, values in group.items():
            if link not in links:
                raise ValueError(f"Collision sphere link absent from URDF: {link}")
            for sphere in values:
                if sphere["radius"] <= 0 or len(sphere["center"]) != 3:
                    raise ValueError(f"Invalid sphere on {link}")
                spheres += 1
    if not spheres:
        raise ValueError("No collision spheres exported")
    print({"urdf_links": len(links), "active_joints": descriptor["cspace"], "collision_spheres": spheres})


if __name__ == "__main__":
    main()
