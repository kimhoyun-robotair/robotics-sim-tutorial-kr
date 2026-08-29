#!/usr/bin/env python3
"""Static and ROS-aware validation for the Humble / Gazebo Classic tutorial.

The default mode deliberately uses only the Python standard library.  It is
therefore useful on a contributor's laptop before ROS 2 is installed.  CI runs
the same checks again with ``--require-ros-tools`` after the workspace is built;
that mode expands every top-level Xacro, runs ``check_urdf``, and asks Gazebo 11
to validate each world file.
"""

from __future__ import annotations

import argparse
import ast
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Iterable, Optional, Sequence
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET


XACRO_NS = "http://www.ros.org/wiki/xacro"
XACRO_INCLUDE = f"{{{XACRO_NS}}}include"

EXPECTED_PACKAGES = {
    "gazebo_tutorial_bringup",
    "gazebo_tutorial_description",
    "gazebo_tutorial_plugins",
    "gazebo_tutorial_tools",
}

CHAPTER_HINTS = {
    "01": ("setup",),
    "02": ("urdf", "xacro", "sdf"),
    "03": ("diffbot",),
    "04": ("rover",),
    "05": ("sensor",),
    "06": ("tf",),
    "07": ("plugin",),
    "08": ("troubleshoot", "debug", "tips"),
    "09": ("next",),
    "10": ("reference",),
}

HUMBLE_TONE_DOCUMENTS = (
    "README.md",
    "docs/index.md",
    "docs/01_setup.md",
    "docs/02_urdf_xacro_sdf.md",
    "docs/03_diffbot.md",
    "docs/04_rover.md",
    "docs/05_sensors.md",
    "docs/06_tf_rviz.md",
    "docs/07_custom_plugin.md",
    "docs/08_debugging.md",
    "docs/09_next_steps.md",
    "docs/10_reference.md",
    "ros2_ws/src/gazebo_tutorial_bringup/README.md",
    "ros2_ws/src/gazebo_tutorial_description/README.md",
    "ros2_ws/src/gazebo_tutorial_plugins/README.md",
    "ros2_ws/src/gazebo_tutorial_tools/README.md",
)

# Formal-polite Korean endings are intentionally excluded from this tutorial.
# ``니다`` needs an extra Hangul-final check: it is polite in 합니다/입니다,
# but it is also part of plain forms such as 아니다.
POLITE_ENDING = re.compile(
    r"(?:습니다|니다|ㅂ니다|세요|십시오)(?=$|[\s.!?…,:;)\]}\"'”’])"
)

DRIVE_MODELS = {
    "diffbot.urdf.xacro": "diff",
    "rover_diff.urdf.xacro": "diff",
    "rover_ackermann.urdf.xacro": "ackermann",
}

SENSOR_RVIZ_TOPICS = {
    "/imu/data",
    "/camera/image_raw",
    "/stereo/left/image_raw",
    "/stereo/right/image_raw",
    "/rgbd/image_raw",
    "/rgbd/depth/image_raw",
    "/rgbd/points",
    "/fisheye/image_raw",
    "/scan",
    "/points",
    "/wheel_odom_path",
}


def local_name(tag: str) -> str:
    """Return an XML tag without its namespace."""
    return tag.rsplit("}", 1)[-1]


def static_name(value: Optional[str]) -> bool:
    """Whether an XML name is already concrete rather than a Xacro expression."""
    return bool(value and "${" not in value and "$(" not in value)


def child_elements(element: ET.Element, name: str) -> list[ET.Element]:
    return [child for child in list(element) if local_name(child.tag) == name]


def child_texts(element: ET.Element, name: str) -> list[str]:
    return [
        (child.text or "").strip()
        for child in child_elements(element, name)
    ]


def first_child_text(element: ET.Element, name: str) -> Optional[str]:
    values = child_texts(element, name)
    return values[0] if values else None


def all_text(element: ET.Element, name: str) -> list[str]:
    return [
        (node.text or "").strip()
        for node in element.iter()
        if local_name(node.tag) == name
    ]


@dataclass
class Validator:
    root: Path
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    checks: int = 0
    package_dirs: dict[str, Path] = field(default_factory=dict)
    xml_cache: dict[Path, ET.Element] = field(default_factory=dict)

    def require(self, condition: bool, location: object, message: str) -> None:
        self.checks += 1
        if not condition:
            path = self.display_path(location)
            self.errors.append(f"{path}: {message}")

    def warn(self, location: object, message: str) -> None:
        self.warnings.append(f"{self.display_path(location)}: {message}")

    def display_path(self, location: object) -> str:
        if isinstance(location, Path):
            try:
                return str(location.resolve().relative_to(self.root))
            except (OSError, ValueError):
                return str(location)
        return str(location)

    def read_text(self, path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            self.require(False, path, f"UTF-8 text로 읽을 수 없습니다: {exc}")
            return ""

    def parse_xml(self, path: Path) -> Optional[ET.Element]:
        if path in self.xml_cache:
            return self.xml_cache[path]
        try:
            root = ET.parse(path).getroot()
        except (OSError, ET.ParseError) as exc:
            self.require(False, path, f"XML parse 실패: {exc}")
            return None
        self.xml_cache[path] = root
        self.checks += 1
        return root


def validate_packages(v: Validator) -> None:
    source = v.root / "ros2_ws" / "src"
    manifests = sorted(source.glob("*/package.xml"))
    v.require(bool(manifests), source, "package.xml을 찾지 못했습니다")

    parsed: dict[str, tuple[Path, ET.Element]] = {}
    for manifest in manifests:
        package = v.parse_xml(manifest)
        if package is None:
            continue
        v.require(local_name(package.tag) == "package", manifest, "root tag는 <package>여야 합니다")
        v.require(package.get("format") == "3", manifest, "ROS 2 package format 3을 사용해야 합니다")

        names = child_texts(package, "name")
        name = names[0] if len(names) == 1 else ""
        v.require(len(names) == 1 and bool(name), manifest, "<name>이 정확히 하나 필요합니다")
        if not name:
            continue
        v.require(name == manifest.parent.name, manifest, "package 이름과 디렉터리 이름이 다릅니다")
        v.require(name not in parsed, manifest, f"중복 package 이름: {name}")
        parsed[name] = (manifest.parent, package)
        v.package_dirs[name] = manifest.parent

        for tag in ("version", "description", "maintainer", "license"):
            values = child_texts(package, tag)
            v.require(len(values) == 1 and bool(values[0]), manifest, f"비어 있지 않은 <{tag}>가 정확히 하나 필요합니다")

        build_types = [
            (node.text or "").strip()
            for export in child_elements(package, "export")
            for node in child_elements(export, "build_type")
        ]
        v.require(len(build_types) == 1, manifest, "<export><build_type>가 정확히 하나 필요합니다")
        if not build_types:
            continue

        build_type = build_types[0]
        cmake = manifest.parent / "CMakeLists.txt"
        setup_py = manifest.parent / "setup.py"
        if build_type == "ament_cmake":
            v.require(cmake.is_file(), manifest.parent, "ament_cmake package에 CMakeLists.txt가 없습니다")
            if cmake.is_file():
                validate_cmake_package(v, name, cmake)
        elif build_type == "ament_python":
            v.require(setup_py.is_file(), manifest.parent, "ament_python package에 setup.py가 없습니다")
            validate_python_package(v, name, manifest.parent)
        else:
            v.require(False, manifest, f"지원하지 않는 build_type: {build_type!r}")

        local_dependencies = {
            (node.text or "").strip()
            for node in package
            if local_name(node.tag).endswith("depend")
            and (node.text or "").strip().startswith("gazebo_tutorial_")
        }
        # The existence check happens after all manifests have been collected.
        package.set("_local_dependencies", ";".join(sorted(local_dependencies)))

    missing = EXPECTED_PACKAGES - set(parsed)
    v.require(not missing, source, f"필수 tutorial package 누락: {', '.join(sorted(missing))}")

    for name, (directory, package) in parsed.items():
        dependencies = package.get("_local_dependencies", "").split(";")
        for dependency in filter(None, dependencies):
            v.require(dependency in parsed, directory / "package.xml", f"로컬 dependency package가 없습니다: {dependency}")


def validate_cmake_package(v: Validator, package_name: str, cmake: Path) -> None:
    text = v.read_text(cmake)
    project = re.search(r"\bproject\s*\(\s*([A-Za-z0-9_]+)", text, re.IGNORECASE)
    v.require(bool(project), cmake, "project(...) 선언이 없습니다")
    if project:
        v.require(project.group(1) == package_name, cmake, "project 이름이 package.xml과 다릅니다")
    v.require(bool(re.search(r"\bfind_package\s*\(\s*ament_cmake\s+REQUIRED", text, re.IGNORECASE)), cmake, "ament_cmake REQUIRED가 없습니다")
    v.require(bool(re.search(r"\bament_package\s*\(\s*\)", text)), cmake, "ament_package()가 없습니다")

    directory = cmake.parent
    if (directory / "urdf").is_dir():
        v.require(bool(re.search(r"install\s*\([^)]*\bDIRECTORY\s+[^)]*\burdf/?\b", text, re.DOTALL | re.IGNORECASE)), cmake, "urdf/ install 규칙이 없습니다")


def validate_python_package(v: Validator, package_name: str, directory: Path) -> None:
    setup_py = directory / "setup.py"
    setup_cfg = directory / "setup.cfg"
    resource = directory / "resource" / package_name
    module_init = directory / package_name / "__init__.py"
    v.require(setup_cfg.is_file(), directory, "setup.cfg가 없습니다")
    v.require(resource.is_file(), directory, f"ament resource marker {resource.name}가 없습니다")
    v.require(module_init.is_file(), directory, f"Python module {package_name}/__init__.py가 없습니다")
    text = v.read_text(setup_py)
    try:
        ast.parse(text, filename=str(setup_py))
        v.checks += 1
    except SyntaxError as exc:
        v.require(False, setup_py, f"Python syntax 오류: {exc.msg} (line {exc.lineno})")
    v.require(re.search(rf"package_name\s*=\s*['\"]{re.escape(package_name)}['\"]", text) is not None, setup_py, "package_name 상수가 package.xml과 다릅니다")

    runtime_dirs = [name for name in ("launch", "rviz", "worlds") if (directory / name).is_dir()]
    for runtime_dir in runtime_dirs:
        v.require(runtime_dir in text, setup_py, f"{runtime_dir}/ data_files 설치 규칙이 없습니다")


def validate_python_sources(v: Validator) -> None:
    workspace = v.root / "ros2_ws" / "src"
    for path in sorted(workspace.rglob("*.py")):
        text = v.read_text(path)
        try:
            tree = ast.parse(text, filename=str(path))
            compile(tree, str(path), "exec")
            v.checks += 1
        except SyntaxError as exc:
            v.require(False, path, f"Python syntax 오류: {exc.msg} (line {exc.lineno})")
            continue

        if path.name.endswith(".launch.py"):
            functions = {
                node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            }
            v.require("generate_launch_description" in functions, path, "generate_launch_description()가 없습니다")
            validate_launch_wrapper(v, path, tree)


def literal_keyword(call: ast.Call, keyword_name: str) -> Optional[str]:
    for keyword in call.keywords:
        if keyword.arg != keyword_name:
            continue
        if isinstance(keyword.value, ast.Constant) and isinstance(keyword.value.value, str):
            return keyword.value.value
    return None


def boolean_keyword(call: ast.Call, keyword_name: str) -> Optional[bool]:
    for keyword in call.keywords:
        if keyword.arg == keyword_name and isinstance(keyword.value, ast.Constant):
            if isinstance(keyword.value.value, bool):
                return keyword.value.value
    return None


def validate_launch_wrapper(v: Validator, path: Path, tree: ast.AST) -> None:
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
    robot_calls = [
        call
        for call in calls
        if (
            isinstance(call.func, ast.Name) and call.func.id == "generate_robot_launch"
        ) or (
            isinstance(call.func, ast.Attribute) and call.func.attr == "generate_robot_launch"
        )
    ]
    v.require(len(robot_calls) == 1, path, "shared generate_robot_launch()를 정확히 한 번 호출해야 합니다")
    if not robot_calls:
        return
    call = robot_calls[0]
    xacro_name = literal_keyword(call, "default_xacro")
    entity = literal_keyword(call, "default_entity")
    rviz_name = literal_keyword(call, "default_rviz_config") or "odom.rviz"
    world_name = literal_keyword(call, "default_world_file") or "empty.world"
    v.require(bool(xacro_name), path, "default_xacro는 문자열 상수여야 합니다")
    v.require(bool(entity), path, "default_entity는 비어 있지 않은 문자열이어야 합니다")
    if xacro_name:
        target = v.root / "ros2_ws" / "src" / "gazebo_tutorial_description" / "urdf" / xacro_name
        v.require(target.is_file(), path, f"default_xacro가 존재하지 않습니다: {xacro_name}")
    rviz_target = v.root / "ros2_ws" / "src" / "gazebo_tutorial_bringup" / "rviz" / rviz_name
    v.require(rviz_target.is_file(), path, f"default RViz config가 존재하지 않습니다: {rviz_name}")
    world_target = v.root / "ros2_ws" / "src" / "gazebo_tutorial_bringup" / "worlds" / world_name
    v.require(world_target.is_file(), path, f"default world가 존재하지 않습니다: {world_name}")
    if xacro_name == "rover_ackermann.urdf.xacro":
        v.require(boolean_keyword(call, "use_ackermann_encoder_odom") is True, path, "Ackermann launch는 encoder wheel odometry node를 활성화해야 합니다")
    if xacro_name == "sensor_bot.urdf.xacro":
        v.require(boolean_keyword(call, "pass_sensor_profile") is True, path, "sensor launch는 sensor_profile을 Xacro에 전달해야 합니다")


def resolve_xacro_include(v: Validator, source: Path, value: str) -> Optional[Path]:
    find_match = re.fullmatch(r"\$\(find\s+([A-Za-z0-9_]+)\)/(.*)", value)
    if find_match:
        package, relative = find_match.groups()
        package_dir = v.package_dirs.get(package)
        if package_dir is None:
            v.require(False, source, f"Xacro include가 알 수 없는 package를 참조합니다: {package}")
            return None
        return package_dir / relative

    share_match = re.fullmatch(r"\$\(find-pkg-share\s+([A-Za-z0-9_]+)\)/(.*)", value)
    if share_match:
        package, relative = share_match.groups()
        package_dir = v.package_dirs.get(package)
        if package_dir is None:
            v.require(False, source, f"Xacro include가 알 수 없는 package를 참조합니다: {package}")
            return None
        return package_dir / relative

    package_match = re.fullmatch(r"package://([A-Za-z0-9_]+)/(.*)", value)
    if package_match:
        package, relative = package_match.groups()
        package_dir = v.package_dirs.get(package)
        if package_dir is None:
            v.require(False, source, f"Xacro include가 알 수 없는 package를 참조합니다: {package}")
            return None
        return package_dir / relative

    if "$" in value:
        # A computed include cannot be resolved without expanding Xacro.  CI's
        # ROS-aware pass will still exercise it.
        v.warn(source, f"정적으로 해석할 수 없는 Xacro include: {value}")
        return None
    return source.parent / value


def validate_xml_sources(v: Validator) -> None:
    workspace = v.root / "ros2_ws" / "src"
    paths = sorted(workspace.rglob("*.xacro")) + sorted(workspace.rglob("*.world"))
    for path in paths:
        root = v.parse_xml(path)
        if root is None:
            continue
        suffixes = "".join(path.suffixes)
        expected_root = "sdf" if path.suffix == ".world" else "robot"
        v.require(local_name(root.tag) == expected_root, path, f"{suffixes} root tag는 <{expected_root}>여야 합니다")
        if path.name.endswith(".urdf.xacro"):
            v.require(static_name(root.get("name")), path, "top-level robot name이 필요합니다")
        if path.suffix == ".world":
            validate_sdf_tree(v, path, root)

        validate_scoped_xml_names(v, path, root)
        for include in root.iter(XACRO_INCLUDE):
            filename = (include.get("filename") or "").strip()
            v.require(bool(filename), path, "xacro:include filename이 비어 있습니다")
            if not filename:
                continue
            target = resolve_xacro_include(v, path, filename)
            if target is not None:
                v.require(target.is_file(), path, f"Xacro include 대상이 없습니다: {v.display_path(target)}")


def validate_scoped_xml_names(v: Validator, path: Path, root: ET.Element) -> None:
    named_tags = {"world", "model", "link", "joint", "plugin", "sensor", "camera", "collision", "visual"}
    for parent in root.iter():
        names: dict[tuple[str, str], int] = Counter()
        for child in list(parent):
            tag = local_name(child.tag)
            name = child.get("name")
            if tag in named_tags and static_name(name):
                names[(tag, name)] += 1
        duplicates = [f"<{tag} name=\"{name}\">" for (tag, name), count in names.items() if count > 1]
        v.require(not duplicates, path, f"같은 XML scope에 중복 name이 있습니다: {', '.join(duplicates)}")

    # URDF link and joint names are global, not merely sibling-scoped.  Ignore
    # names that contain Xacro expressions because one macro may be called many
    # times with distinct values.
    if local_name(root.tag) == "robot":
        for tag in ("link", "joint"):
            names = [node.get("name", "") for node in root.iter() if local_name(node.tag) == tag and static_name(node.get("name"))]
            duplicates = sorted(name for name, count in Counter(names).items() if count > 1)
            v.require(not duplicates, path, f"중복된 static <{tag}> name: {', '.join(duplicates)}")


def validate_sdf_tree(v: Validator, path: Path, root: ET.Element) -> None:
    version = root.get("version", "")
    v.require(bool(re.fullmatch(r"1\.[4-9]", version)), path, f"Gazebo Classic 호환 SDF version이 아닙니다: {version!r}")
    worlds = child_elements(root, "world")
    v.require(len(worlds) == 1, path, "world 파일에는 <world>가 정확히 하나 필요합니다")
    if worlds:
        world = worlds[0]
        v.require(static_name(world.get("name")), path, "world name이 필요합니다")
        uris = all_text(world, "uri")
        v.require(any(uri == "model://ground_plane" for uri in uris), path, "ground_plane include가 없습니다")


def find_plugins(root: ET.Element, filename: str) -> list[ET.Element]:
    return [
        node
        for node in root.iter()
        if local_name(node.tag) == "plugin" and node.get("filename") == filename
    ]


def remapping_contract(plugin: ET.Element, topic: str) -> bool:
    for value in all_text(plugin, "remapping"):
        if ":=" not in value:
            continue
        source, target = (part.strip() for part in value.split(":=", 1))
        if source.strip("~/") == topic and target.strip("/") == topic:
            return True
    return False


def remapping_target(plugin: ET.Element, topic: str) -> Optional[str]:
    for value in all_text(plugin, "remapping"):
        if ":=" not in value:
            continue
        source, target = (part.strip() for part in value.split(":=", 1))
        if source.strip("~/") == topic:
            return target
    return None


def require_bool_child(v: Validator, path: Path, plugin: ET.Element, name: str) -> None:
    value = (first_child_text(plugin, name) or "").lower()
    v.require(value in {"true", "1"}, path, f"{plugin.get('filename')}의 <{name}>가 true여야 합니다")


def validate_drive_plugin(v: Validator, path: Path, root: ET.Element, drive_kind: str) -> None:
    filename = "libgazebo_ros_diff_drive.so" if drive_kind == "diff" else "libgazebo_ros_ackermann_drive.so"
    plugins = find_plugins(root, filename)
    v.require(len(plugins) == 1, path, f"{filename} plugin이 정확히 하나 필요합니다")
    if not plugins:
        return
    plugin = plugins[0]
    v.require(remapping_contract(plugin, "cmd_vel"), path, "drive plugin에 cmd_vel remapping 계약이 없습니다")
    require_bool_child(v, path, plugin, "publish_odom")
    v.require(first_child_text(plugin, "robot_base_frame") == "base_footprint", path, "robot_base_frame은 base_footprint여야 합니다")

    if drive_kind == "diff":
        v.require(remapping_contract(plugin, "odom"), path, "diff drive plugin에 odom remapping 계약이 없습니다")
        require_bool_child(v, path, plugin, "publish_odom_tf")
        v.require(first_child_text(plugin, "odometry_frame") == "odom", path, "diff drive odometry_frame은 odom이어야 합니다")
        try:
            pair_count = int(first_child_text(plugin, "num_wheel_pairs") or "1")
        except ValueError:
            pair_count = 0
        left = child_texts(plugin, "left_joint")
        right = child_texts(plugin, "right_joint")
        separations = child_texts(plugin, "wheel_separation")
        diameters = child_texts(plugin, "wheel_diameter")
        v.require(pair_count >= 1, path, "num_wheel_pairs는 1 이상이어야 합니다")
        v.require(len(left) == pair_count and len(right) == pair_count, path, "left/right_joint 개수는 num_wheel_pairs와 같아야 합니다")
        v.require(len(separations) == pair_count, path, "wheel_separation은 wheel pair마다 하나씩 필요합니다")
        v.require(len(diameters) == pair_count, path, "wheel_diameter는 wheel pair마다 하나씩 필요합니다")
        v.require(len(set(left + right)) == len(left + right) and all(left + right), path, "drive joint 이름은 비어 있지 않고 서로 달라야 합니다")
        v.require(first_child_text(plugin, "odometry_source") == "0", path, "wheel encoder odometry에는 <odometry_source>0</odometry_source>가 필요합니다")
    else:
        # Humble's Ackermann plugin always uses Model::WorldPose for odometry;
        # it has no encoder-source switch.  Keep that ground truth on a
        # separate topic/frame and let the tutorial's JointState integrator own
        # /odom and odom -> base_footprint.
        ground_truth_topic = (remapping_target(plugin, "odom") or "").strip("/")
        v.require(ground_truth_topic == "ground_truth/odom", path, "Ackermann built-in world-pose odom은 ground_truth/odom으로 remap해야 합니다")
        publish_odom_tf = (first_child_text(plugin, "publish_odom_tf") or "").lower()
        v.require(publish_odom_tf in {"false", "0"}, path, "Ackermann built-in plugin은 odom TF를 발행하면 안 됩니다")
        v.require(first_child_text(plugin, "odometry_frame") == "world", path, "Ackermann built-in odometry_frame은 world여야 합니다")
        # gazebo_ros_pkgs 3.9.0 supports this optional diagnostic output.
        publish_steerangle = (first_child_text(plugin, "publish_steerangle") or "").lower()
        if publish_steerangle:
            v.require(
                publish_steerangle in {"true", "1", "false", "0"},
                path,
                "Ackermann <publish_steerangle>은 boolean 값이어야 합니다",
            )
        joint_tags = (
            "front_left_joint",
            "front_right_joint",
            "rear_left_joint",
            "rear_right_joint",
            "left_steering_joint",
            "right_steering_joint",
        )
        joint_names = [first_child_text(plugin, tag) or "" for tag in joint_tags]
        v.require(all(joint_names), path, "Ackermann plugin의 6개 wheel/steering joint 태그가 모두 필요합니다")
        v.require(len(set(joint_names)) == len(joint_names), path, "Ackermann plugin joint 태그가 같은 joint를 중복 참조합니다")
        for pid_tag in ("left_steering_pid_gain", "right_steering_pid_gain", "linear_velocity_pid_gain"):
            raw = first_child_text(plugin, pid_tag) or ""
            try:
                gains = [float(value) for value in raw.split()]
            except ValueError:
                gains = []
            v.require(len(gains) == 3 and any(value != 0.0 for value in gains), path, f"<{pid_tag}>에는 non-zero P/I/D 3개 값이 필요합니다")


def validate_robot_contracts(v: Validator) -> None:
    urdf_dir = v.root / "ros2_ws" / "src" / "gazebo_tutorial_description" / "urdf"
    for filename, drive_kind in DRIVE_MODELS.items():
        path = urdf_dir / filename
        v.require(path.is_file(), urdf_dir, f"필수 robot Xacro 누락: {filename}")
        root = v.parse_xml(path) if path.is_file() else None
        if root is None:
            continue
        validate_drive_plugin(v, path, root, drive_kind)

        if filename == "diffbot.urdf.xacro":
            caster_nodes = [
                node for node in root.iter()
                if local_name(node.tag) in {"link", "joint"}
                and "caster" in (node.get("name") or "").lower()
            ]
            v.require(bool(caster_nodes), path, "2륜 robot에 caster link/joint가 없습니다")

    sensor_path = urdf_dir / "sensor_bot.urdf.xacro"
    v.require(sensor_path.is_file(), urdf_dir, "sensor_bot.urdf.xacro가 없습니다")
    sensor_root = v.parse_xml(sensor_path) if sensor_path.is_file() else None
    if sensor_root is not None:
        validate_drive_plugin(v, sensor_path, sensor_root, "diff")
        sensor_roots = [sensor_root]
        include_nodes = [
            node for node in sensor_root.iter()
            if node.tag == XACRO_INCLUDE
        ]
        for include in include_nodes:
            filename = include.get("filename", "")
            marker = "/urdf/sensors/"
            if marker not in filename:
                continue
            relative = filename.split(marker, 1)[1]
            included_path = urdf_dir / "sensors" / relative
            v.require(included_path.is_file(), sensor_path, f"sensor Xacro include 누락: {relative}")
            if included_path.is_file():
                included_root = v.parse_xml(included_path)
                if included_root is not None:
                    sensor_roots.append(included_root)
        v.require(len(sensor_roots) > 1, sensor_path, "분리된 urdf/sensors/*.xacro include가 없습니다")
        validate_sensor_contract(v, sensor_path, sensor_roots)

    validate_path_visualization_contract(v)


def validate_sensor_contract(
    v: Validator,
    path: Path,
    roots: Sequence[ET.Element],
) -> None:
    nodes = [node for root in roots for node in root.iter()]
    sensors = [node for node in nodes if local_name(node.tag) == "sensor"]
    types = Counter(node.get("type", "") for node in sensors)
    for sensor_type in ("imu", "camera", "multicamera", "depth", "wideanglecamera"):
        v.require(types[sensor_type] >= 1, path, f"필수 sensor type 누락: {sensor_type}")
    v.require(types["ray"] >= 2, path, "2D/3D LiDAR용 ray sensor가 각각 필요합니다")

    required_plugins = {
        "libgazebo_ros_imu_sensor.so",
        "libgazebo_ros_camera.so",
        "libgazebo_ros_ray_sensor.so",
    }
    filenames = {
        node.get("filename", "")
        for node in nodes
        if local_name(node.tag) == "plugin"
    }
    for filename in required_plugins:
        v.require(filename in filenames, path, f"필수 sensor plugin 누락: {filename}")

    image_noise_sensors = [
        sensor for sensor in sensors
        if sensor.get("type") in {"camera", "multicamera", "depth"}
    ]
    for sensor in image_noise_sensors:
        noise_parameters = set(all_text(sensor, "stddev"))
        v.require(
            bool(noise_parameters)
            and noise_parameters == {"${image_noise_stddev}"},
            path,
            f"{sensor.get('type')} <camera><noise>는 image_noise_stddev macro parameter를 사용해야 합니다",
        )

    fisheye_sensors = [
        sensor for sensor in sensors
        if sensor.get("type") == "wideanglecamera"
    ]
    v.require(len(fisheye_sensors) == 1, path, "fisheye wideanglecamera가 정확히 하나 필요합니다")
    for sensor in fisheye_sensors:
        fisheye_plugins = find_plugins(sensor, "libgazebo_ros_camera.so")
        v.require(
            len(fisheye_plugins) == 1,
            path,
            "fisheye wideanglecamera에 libgazebo_ros_camera.so가 필요합니다",
        )
        lens_types = [
            first_child_text(lens, "type") or ""
            for lens in sensor.iter()
            if local_name(lens.tag) == "lens"
        ]
        v.require(
            lens_types == ["${lens_type}"],
            path,
            "fisheye <lens><type>은 lens_type macro parameter를 사용해야 합니다",
        )

    multicameras = [node for node in sensors if node.get("type") == "multicamera"]
    v.require(any(len(child_elements(node, "camera")) >= 2 for node in multicameras), path, "stereo multicamera에는 camera가 2개 이상 필요합니다")
    stereo_plugins = [
        node
        for sensor in multicameras
        for node in sensor.iter()
        if local_name(node.tag) == "plugin"
        and node.get("filename") == "libgazebo_ros_camera.so"
    ]
    v.require(len(stereo_plugins) == 1, path, "stereo camera ROS plugin이 정확히 하나 필요합니다")

    stereo_cameras = [
        camera
        for sensor in multicameras
        for camera in child_elements(sensor, "camera")
    ]
    cameras_by_name = {camera.get("name", ""): camera for camera in stereo_cameras}
    v.require(set(cameras_by_name) == {"left", "right"}, path, "stereo camera 이름은 left/right여야 합니다")
    left_pose = first_child_text(cameras_by_name.get("left", ET.Element("camera")), "pose") or ""
    right_pose = first_child_text(cameras_by_name.get("right", ET.Element("camera")), "pose") or ""
    v.require(
        re.search(r"\$\{\s*baseline\s*/\s*2(?:\.0)?\s*\}", left_pose) is not None,
        path,
        "stereo left camera pose에 +baseline/2 물리 오프셋이 필요합니다",
    )
    v.require(
        re.search(r"\$\{\s*-baseline\s*/\s*2(?:\.0)?\s*\}", right_pose) is not None,
        path,
        "stereo right camera pose에 -baseline/2 물리 오프셋이 필요합니다",
    )

    main_root = roots[0]
    stereo_calls = [
        node for node in main_root.iter()
        if local_name(node.tag) == "gazebo_stereo_camera"
    ]
    v.require(bool(stereo_calls), path, "sensor_bot에 gazebo_stereo_camera macro 호출이 없습니다")
    for call in stereo_calls:
        try:
            configured_baseline = float(call.get("baseline", "0"))
        except ValueError:
            configured_baseline = 0.0
        v.require(
            configured_baseline > 0.0,
            path,
            "gazebo_stereo_camera 호출에는 양수 baseline이 필요합니다",
        )
        camera_name = call.get("camera_name", "").strip("/")
        v.require(camera_name == "stereo", path, "stereo macro camera_name은 stereo여야 합니다")
        rviz_path = v.root / "ros2_ws" / "src" / "gazebo_tutorial_bringup" / "rviz" / "sensors.rviz"
        rviz_text = v.read_text(rviz_path) if rviz_path.is_file() else ""
        for side in ("left", "right"):
            topic = f"/{camera_name}/{side}/image_raw"
            v.require(topic in rviz_text, rviz_path, f"stereo RViz topic 누락: {topic}")

    fisheye_calls = [
        node for node in main_root.iter()
        if local_name(node.tag) == "gazebo_fisheye_camera"
    ]
    v.require(bool(fisheye_calls), path, "sensor_bot에 gazebo_fisheye_camera macro 호출이 없습니다")
    for call in fisheye_calls:
        v.require(
            call.get("lens_type") == "equidistant",
            path,
            "fisheye macro lens_type은 equidistant여야 합니다",
        )

    ray_outputs = {
        first_child_text(plugin, "output_type")
        for root in roots
        for plugin in find_plugins(root, "libgazebo_ros_ray_sensor.so")
    }
    v.require("sensor_msgs/LaserScan" in ray_outputs, path, "2D LiDAR LaserScan output_type이 없습니다")
    v.require("sensor_msgs/PointCloud2" in ray_outputs, path, "3D LiDAR PointCloud2 output_type이 없습니다")
    remappings = {
        value
        for root in roots
        for value in all_text(root, "remapping")
    }
    generic_topic_remap = any(
        value.split(":=", 1)[-1].strip() == "${topic}"
        for value in remappings
    )
    topic_macros = {
        "imu/data": "gazebo_imu_sensor",
        "scan": "gazebo_lidar_2d",
        "points": "gazebo_lidar_3d",
    }
    for topic, macro_name in topic_macros.items():
        concrete_remap = any(
            value.split(":=", 1)[-1].strip("/") == topic
            for value in remappings
        )
        matching_calls = [
            node for node in main_root.iter()
            if local_name(node.tag) == macro_name
            and node.get("topic", "").strip("/") == topic
        ]
        v.require(
            concrete_remap or (generic_topic_remap and bool(matching_calls)),
            path,
            f"{macro_name} 호출의 sensor topic remapping 누락: {topic}",
        )

    args = [node.get("name") for node in nodes if node.tag == f"{{{XACRO_NS}}}arg"]
    v.require("sensor_profile" in args, path, "고비용 센서를 선택할 sensor_profile Xacro arg가 없습니다")


def validate_path_visualization_contract(v: Validator) -> None:
    bringup = v.root / "ros2_ws" / "src" / "gazebo_tutorial_bringup"
    tools = v.root / "ros2_ws" / "src" / "gazebo_tutorial_tools"
    launch_api = bringup / "gazebo_tutorial_bringup" / "launch_api.py"
    odom_node = tools / "gazebo_tutorial_tools" / "odom_to_path.py"
    tools_setup = tools / "setup.py"
    odom_rviz = bringup / "rviz" / "odom.rviz"
    sensors_rviz = bringup / "rviz" / "sensors.rviz"

    for path in (launch_api, odom_node, tools_setup, odom_rviz, sensors_rviz):
        v.require(path.is_file(), path.parent, f"필수 파일 누락: {path.name}")

    launch_text = v.read_text(launch_api) if launch_api.is_file() else ""
    for token in ("gazebo.launch.py", "robot_state_publisher", "spawn_entity.py", "odom_to_path", "rviz2", "wheel_odom_path"):
        v.require(token in launch_text, launch_api, f"launch orchestration 계약 누락: {token}")

    node_text = v.read_text(odom_node) if odom_node.is_file() else ""
    for token in ("nav_msgs.msg", "Odometry", "Path", "odom_topic", "path_topic", "/wheel_odom_path"):
        v.require(token in node_text, odom_node, f"odom_to_path 계약 누락: {token}")

    setup_text = v.read_text(tools_setup) if tools_setup.is_file() else ""
    v.require(re.search(r"odom_to_path\s*=\s*gazebo_tutorial_tools\.odom_to_path:main", setup_text) is not None, tools_setup, "odom_to_path console_script가 없습니다")

    ackermann_node = tools / "gazebo_tutorial_tools" / "ackermann_odom.py"
    v.require(ackermann_node.is_file(), tools, "Ackermann wheel encoder odometry node가 없습니다")
    ackermann_text = v.read_text(ackermann_node) if ackermann_node.is_file() else ""
    for token in ("JointState", "Odometry", "rear_left_wheel_joint", "rear_right_wheel_joint", "front_left_steering_joint", "front_right_steering_joint", "equivalent_center_steering_angle", "TransformBroadcaster"):
        v.require(token in ackermann_text, ackermann_node, f"Ackermann wheel odometry 계약 누락: {token}")
    v.require(re.search(r"ackermann_odom\s*=\s*gazebo_tutorial_tools\.ackermann_odom:main", setup_text) is not None, tools_setup, "ackermann_odom console_script가 없습니다")
    v.require("ackermann_odom" in launch_text, launch_api, "Ackermann launch가 wheel odometry node를 시작하지 않습니다")
    v.require("ackermann_publish_tf" in launch_text, launch_api, "Ackermann TF 소유권을 끌 수 있는 launch 인자가 없습니다")

    odom_rviz_text = v.read_text(odom_rviz) if odom_rviz.is_file() else ""
    for token in ("rviz_default_plugins/Path", "/wheel_odom_path", "/odom", "Fixed Frame: odom"):
        v.require(token in odom_rviz_text, odom_rviz, f"wheel odom RViz 계약 누락: {token}")

    sensor_rviz_text = v.read_text(sensors_rviz) if sensors_rviz.is_file() else ""
    for topic in sorted(SENSOR_RVIZ_TOPICS):
        v.require(topic in sensor_rviz_text, sensors_rviz, f"sensor RViz topic 누락: {topic}")
    for display in ("rviz_imu_plugin/Imu", "rviz_default_plugins/LaserScan", "rviz_default_plugins/PointCloud2", "rviz_default_plugins/Image"):
        v.require(display in sensor_rviz_text, sensors_rviz, f"sensor RViz display 누락: {display}")


def validate_custom_plugin(v: Validator) -> None:
    package = v.root / "ros2_ws" / "src" / "gazebo_tutorial_plugins"
    cmake = package / "CMakeLists.txt"
    manifest = package / "package.xml"
    source = package / "src" / "ground_truth_path_plugin.cpp"
    macro = package / "urdf" / "ground_truth_path_plugin.gazebo.xacro"
    for path in (cmake, manifest, source, macro):
        v.require(path.is_file(), package, f"custom plugin 필수 파일 누락: {path.relative_to(package)}")
    if not all(path.is_file() for path in (cmake, manifest, source, macro)):
        return

    cmake_text = v.read_text(cmake)
    target_match = re.search(r"add_library\s*\(\s*([A-Za-z0-9_]+)\s+SHARED\b", cmake_text, re.DOTALL)
    v.require(bool(target_match), cmake, "SHARED plugin library target이 없습니다")
    target = target_match.group(1) if target_match else ""
    if target:
        v.require(re.search(rf"install\s*\(\s*TARGETS\s+[^)]*\b{re.escape(target)}\b", cmake_text, re.DOTALL) is not None, cmake, f"plugin target {target} install 규칙이 없습니다")

    manifest_root = v.parse_xml(manifest)
    if manifest_root is not None:
        dependencies = {
            (node.text or "").strip()
            for node in manifest_root
            if local_name(node.tag).endswith("depend")
        }
        for dependency in ("gazebo_dev", "gazebo_ros", "nav_msgs", "rclcpp"):
            v.require(dependency in dependencies, manifest, f"custom plugin dependency 누락: {dependency}")
        gazebo_exports = [node for export in child_elements(manifest_root, "export") for node in child_elements(export, "gazebo_ros")]
        v.require(any("gazebo_plugin_path" in node.attrib for node in gazebo_exports), manifest, "Gazebo plugin path export가 없습니다")

    source_text = v.read_text(source)
    for token in (
        "public ModelPlugin",
        "GZ_REGISTER_MODEL_PLUGIN",
        "gazebo_ros::Node::Get",
        "nav_msgs::msg::Path",
        "ConnectWorldUpdateBegin",
        "WorldPose",
        "simTime",
    ):
        v.require(token in source_text, source, f"custom ModelPlugin API 계약 누락: {token}")

    macro_root = v.parse_xml(macro)
    if macro_root is not None:
        plugins = [node for node in macro_root.iter() if local_name(node.tag) == "plugin"]
        v.require(len(plugins) == 1, macro, "custom plugin Xacro에는 plugin 블록이 정확히 하나 필요합니다")
        if plugins and target:
            v.require(plugins[0].get("filename") == f"lib{target}.so", macro, "Xacro filename과 CMake library target이 다릅니다")
        if plugins:
            for tag in ("update_rate", "topic", "frame", "max_points"):
                v.require(bool(child_elements(plugins[0], tag)), macro, f"custom plugin SDF tag 누락: {tag}")


def select_humble_chapters(v: Validator) -> list[Path]:
    docs = v.root / "docs"
    selected: list[Path] = []
    for number, hints in CHAPTER_HINTS.items():
        candidates = sorted(docs.glob(f"{number}_*.md"))
        matches = [path for path in candidates if any(hint in path.stem.lower() for hint in hints)]
        if number == "08" and not matches:
            matches = candidates
        v.require(bool(matches), docs, f"Humble tutorial {number}장 문서가 없습니다 (힌트: {', '.join(hints)})")
        if matches:
            selected.append(matches[0])
    return selected


def markdown_prose_lines(text: str) -> Iterable[tuple[int, str]]:
    """Yield line-numbered Markdown prose with fenced/inline code removed."""
    fence: Optional[str] = None
    for line_number, line in enumerate(text.splitlines(), start=1):
        stripped = line.lstrip()
        marker = stripped[:3]
        if marker in {"```", "~~~"}:
            if fence is None:
                fence = marker
            elif fence == marker:
                fence = None
            continue
        if fence is None:
            yield line_number, re.sub(r"`[^`]*`", "", line)


def without_markdown_code(text: str) -> str:
    return "\n".join(line for _, line in markdown_prose_lines(text))


def polite_tone_violations(text: str) -> Iterable[tuple[int, str]]:
    """Yield formal-polite endings found in Markdown prose."""
    for line_number, prose in markdown_prose_lines(text):
        for match in POLITE_ENDING.finditer(prose):
            ending = match.group(0)
            if ending == "니다":
                if match.start() == 0:
                    continue
                preceding = prose[match.start() - 1]
                codepoint = ord(preceding) - 0xAC00
                # A ``-ㅂ니다`` form is encoded as a preceding Hangul syllable
                # whose final-consonant (jongseong) index is bieup (17).
                if not (0 <= codepoint <= 0xD7A3 - 0xAC00 and codepoint % 28 == 17):
                    continue
                ending = preceding + ending
            yield line_number, ending


def local_markdown_targets(text: str) -> Iterable[str]:
    clean = without_markdown_code(text)
    patterns = (
        r"!?\[[^\]]*\]\(\s*<?([^\s)>]+)>?(?:\s+[^)]*)?\)",
        r"(?m)^\s*\[[^\]]+\]:\s*<?([^\s>]+)>?",
        r"(?:src|href)=[\"']([^\"']+)[\"']",
    )
    for pattern in patterns:
        yield from re.findall(pattern, clean)


def resolve_markdown_target(source: Path, raw_target: str) -> Optional[Path]:
    target = raw_target.strip().strip("<>")
    parsed = urlsplit(target)
    if parsed.scheme or parsed.netloc or target.startswith(("#", "/", "mailto:")):
        return None
    if not parsed.path or any(token in parsed.path for token in ("{{", "}}", "${")):
        return None
    return source.parent / unquote(parsed.path)


def markdown_target_exists(path: Path) -> bool:
    if path.exists():
        return True
    if not path.suffix and path.with_suffix(".md").is_file():
        return True
    if not path.suffix and (path / "index.md").is_file():
        return True
    if path.suffix == ".html" and path.with_suffix(".md").is_file():
        return True
    return False


def validate_docs(v: Validator) -> None:
    chapters = select_humble_chapters(v)
    entrypoints = [v.root / "README.md", v.root / "docs" / "index.md"]
    docs = [path for path in entrypoints + chapters if path.is_file()]
    for path in entrypoints:
        v.require(path.is_file(), path.parent, f"문서 entrypoint 누락: {path.name}")

    for path in docs:
        text = v.read_text(path)
        if path in chapters:
            korean_chars = len(re.findall(r"[가-힣]", without_markdown_code(text)))
            v.require(korean_chars >= 20, path, "한국어 본문이 너무 적습니다")
        for target in local_markdown_targets(text):
            resolved = resolve_markdown_target(path, target)
            if resolved is None:
                continue
            v.require(markdown_target_exists(resolved), path, f"깨진 local 문서 링크: {target}")

    # The user-facing Humble course uses the plain declarative ``~하다`` style.
    # Keep code examples out of this check because command output and copied API
    # identifiers are not tutorial narration.
    for relative in HUMBLE_TONE_DOCUMENTS:
        path = v.root / relative
        v.require(path.is_file(), path.parent, f"문체 검사 대상 문서 누락: {path.name}")
        if not path.is_file():
            continue
        for line_number, ending in polite_tone_violations(v.read_text(path)):
            v.require(
                False,
                f"{v.display_path(path)}:{line_number}",
                f"~하다체 문서에 격식 존댓말 어미가 남아 있습니다: {ending}",
            )

    mkdocs = v.root / "mkdocs.yml"
    v.require(mkdocs.is_file(), v.root, "mkdocs.yml이 없습니다")
    mkdocs_text = v.read_text(mkdocs) if mkdocs.is_file() else ""
    for chapter in chapters:
        relative = chapter.relative_to(v.root / "docs").as_posix()
        v.require(relative in mkdocs_text, mkdocs, f"Humble tutorial 문서가 nav에 없습니다: {relative}")


def validate_rendered_urdf(v: Validator, label: object, root: ET.Element) -> None:
    v.require(local_name(root.tag) == "robot", label, "Xacro 결과 root가 <robot>이 아닙니다")
    links = [node for node in root if local_name(node.tag) == "link"]
    joints = [node for node in root if local_name(node.tag) == "joint"]
    link_names = [node.get("name", "") for node in links]
    joint_names = [node.get("name", "") for node in joints]
    for kind, names in (("link", link_names), ("joint", joint_names)):
        duplicates = sorted(name for name, count in Counter(names).items() if not name or count > 1)
        v.require(not duplicates, label, f"rendered URDF의 {kind} name이 비었거나 중복입니다: {', '.join(duplicates)}")

    known_links = set(link_names)
    parent_of: dict[str, str] = {}
    for joint in joints:
        name = joint.get("name", "<unnamed>")
        parents = child_elements(joint, "parent")
        children = child_elements(joint, "child")
        v.require(len(parents) == 1 and len(children) == 1, label, f"joint {name}에는 parent/child가 각각 하나 필요합니다")
        if len(parents) != 1 or len(children) != 1:
            continue
        parent = parents[0].get("link", "")
        child = children[0].get("link", "")
        v.require(parent in known_links, label, f"joint {name}의 parent link가 없습니다: {parent}")
        v.require(child in known_links, label, f"joint {name}의 child link가 없습니다: {child}")
        v.require(parent != child, label, f"joint {name}이 같은 link를 parent/child로 사용합니다")
        v.require(child not in parent_of, label, f"link {child}에 parent joint가 둘 이상입니다")
        parent_of[child] = parent

    roots = known_links - set(parent_of)
    v.require(len(roots) == 1, label, f"URDF TF tree root link가 정확히 하나가 아닙니다: {', '.join(sorted(roots))}")
    for link in known_links:
        seen: set[str] = set()
        cursor = link
        while cursor in parent_of:
            if cursor in seen:
                v.require(False, label, f"URDF TF tree에 cycle이 있습니다: {cursor}")
                break
            seen.add(cursor)
            cursor = parent_of[cursor]

    known_joints = set(joint_names)
    joint_reference_tags = {
        "left_joint", "right_joint", "front_left_joint", "front_right_joint",
        "rear_left_joint", "rear_right_joint", "left_steering_joint",
        "right_steering_joint", "steering_wheel_joint", "joint_name",
    }
    for node in root.iter():
        if local_name(node.tag) in joint_reference_tags:
            reference = (node.text or "").strip()
            v.require(reference in known_joints, label, f"plugin이 없는 joint를 참조합니다: <{local_name(node.tag)}>{reference}")
        if local_name(node.tag) == "gazebo" and node.get("reference"):
            reference = node.get("reference", "")
            v.require(reference in known_links or reference in known_joints, label, f"<gazebo reference> 대상이 없습니다: {reference}")

    validate_scoped_xml_names(v, Path(str(label)), root)


def run_checked(v: Validator, label: object, command: Sequence[str], *, input_text: Optional[str] = None) -> Optional[str]:
    try:
        result = subprocess.run(
            command,
            input=input_text,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=120,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        v.require(False, label, f"명령 실행 실패: {' '.join(command)}: {exc}")
        return None
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip().splitlines()
        summary = detail[-1] if detail else f"exit {result.returncode}"
        v.require(False, label, f"명령 실패 ({' '.join(command)}): {summary}")
        return None
    v.checks += 1
    return result.stdout


def validate_with_ros_tools(v: Validator) -> None:
    xacro = shutil.which("xacro")
    check_urdf = shutil.which("check_urdf")
    gz = shutil.which("gz")
    v.require(xacro is not None, "PATH", "--require-ros-tools에는 xacro가 필요합니다")
    v.require(check_urdf is not None, "PATH", "--require-ros-tools에는 check_urdf가 필요합니다")
    v.require(gz is not None, "PATH", "--require-ros-tools에는 Gazebo 11의 gz CLI가 필요합니다")
    if not xacro or not check_urdf or not gz:
        return

    urdf_dir = v.root / "ros2_ws" / "src" / "gazebo_tutorial_description" / "urdf"
    profiles = {
        "diffbot.urdf.xacro": (None,),
        "rover_diff.urdf.xacro": (None,),
        "rover_ackermann.urdf.xacro": (None,),
        "sensor_bot.urdf.xacro": ("all", "cameras", "lidars", "minimal"),
    }
    with tempfile.TemporaryDirectory(prefix="gazebo-tutorial-validation-") as temporary:
        temporary_dir = Path(temporary)
        for filename, sensor_profiles in profiles.items():
            source = urdf_dir / filename
            if not source.is_file():
                continue
            for profile in sensor_profiles:
                command = [xacro, str(source)]
                label = filename
                if profile is not None:
                    command.append(f"sensor_profile:={profile}")
                    label = f"{filename}[sensor_profile={profile}]"
                rendered = run_checked(v, label, command)
                if rendered is None:
                    continue
                try:
                    root = ET.fromstring(rendered)
                except ET.ParseError as exc:
                    v.require(False, label, f"rendered URDF XML parse 실패: {exc}")
                    continue
                validate_rendered_urdf(v, label, root)
                output = temporary_dir / f"{filename}.{profile or 'default'}.urdf"
                output.write_text(rendered, encoding="utf-8")
                run_checked(v, label, [check_urdf, str(output)])

    for world in sorted((v.root / "ros2_ws" / "src").rglob("*.world")):
        run_checked(v, world, [gz, "sdf", "-k", str(world)])


def run_validation(root: Path, require_ros_tools: bool = False) -> Validator:
    v = Validator(root=root.resolve())
    validate_packages(v)
    validate_python_sources(v)
    validate_xml_sources(v)
    validate_robot_contracts(v)
    validate_custom_plugin(v)
    validate_docs(v)
    if require_ros_tools:
        validate_with_ros_tools(v)
    return v


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="repository root (default: parent of scripts/)",
    )
    parser.add_argument(
        "--require-ros-tools",
        action="store_true",
        help="require xacro, check_urdf and Gazebo 11 gz; expand/check models",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    validator = run_validation(args.root, args.require_ros_tools)
    for warning in validator.warnings:
        print(f"WARNING: {warning}")
    if validator.errors:
        for error in validator.errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(
            f"Humble tutorial validation FAILED: "
            f"{len(validator.errors)} error(s), {validator.checks} check(s)",
            file=sys.stderr,
        )
        return 1
    print(
        f"Humble tutorial validation OK: {validator.checks} checks, "
        f"{len(validator.warnings)} warning(s)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
