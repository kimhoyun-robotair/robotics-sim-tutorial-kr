"""Robotiq ROS1 XACRO를 별도 복사본에서 ROS2 xacro가 읽을 수 있게 경로 정리."""
import argparse
from pathlib import Path
import shutil


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Cloned robotiq_2f_140_gripper_visualization folder")
    parser.add_argument("output", type=Path, help="New local working copy; must not exist")
    args = parser.parse_args()
    source = args.source.resolve()
    target = args.output.resolve()
    if not (source / "urdf/robotiq_arg2f_140_model.xacro").is_file():
        parser.error("source must contain urdf/robotiq_arg2f_140_model.xacro")
    if source == target or source in target.parents:
        parser.error("output must be outside the source tree")
    shutil.copytree(source, target)
    prefix = "robotiq_2f_140_gripper_visualization"
    for path in (target / "urdf").glob("*.xacro"):
        text = path.read_text()
        text = text.replace("$(find " + prefix + ")", str(target))
        text = text.replace("package://" + prefix, str(target))
        path.write_text(text)
    print("Working copy:", target)
    print("Run xacro in its urdf directory. The generated URDF refers to this working copy.")


if __name__ == "__main__":
    main()
