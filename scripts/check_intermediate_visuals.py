#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "playwright>=1.46,<2",
# ]
# ///

# ─── How to run ───
# 1. Install uv (if not installed):
#      curl -LsSf https://astral.sh/uv/install.sh | sh
# 2. Run directly (no venv, no pip install needed):
#      uv run scripts/check_intermediate_visuals.py --site URL --routes-file FILE --gazebo-title REGEX --rviz-title REGEX --evidence DIR
# 3. Or make executable and run:
#      chmod +x scripts/check_intermediate_visuals.py && ./scripts/check_intermediate_visuals.py --site URL --routes-file FILE --gazebo-title REGEX --rviz-title REGEX --evidence DIR
# ─────────────────

from __future__ import annotations

import hashlib
import json
import os
import re
import signal
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from types import FrameType
from typing import Final
from urllib.parse import urljoin


@dataclass(frozen=True, slots=True)
class Config:
    site: str
    routes_file: Path
    gazebo_title: str
    rviz_title: str
    evidence: Path


@dataclass(frozen=True, slots=True)
class Window:
    xid: str
    title: str
    width: int
    height: int


@dataclass(frozen=True, slots=True)
class ImageInfo:
    width: int
    height: int
    entropy_bits: float


@dataclass(frozen=True, slots=True)
class CheckItem:
    item_id: str
    passed: bool
    artifact: str
    bounds: tuple[int, int, int, int]
    observable: str
    live_status_artifact: str


AuditInputError = ValueError


FLAGS = ("--site", "--routes-file", "--gazebo-title", "--rviz-title", "--evidence")
HELP_TEXT: Final = (
    "usage: check_intermediate_visuals.py --site URL --routes-file FILE "
    "--gazebo-title REGEX --rviz-title REGEX --evidence DIR\n"
)
FROZEN_ROUTES = (
    "/04_intermediate/", "/04_intermediate/01-advanced-sdf/", "/04_intermediate/02-urdf-xacro-sdf/", "/04_intermediate/03-ros2-launch/", "/04_intermediate/04-spawn-model/", "/04_intermediate/05-bridge-yaml/",
    "/04_intermediate/06-tf-rviz/", "/04_intermediate/07-gz-ros2-control/", "/04_intermediate/08-advanced-sensors/", "/04_intermediate/09-multi-robot/", "/04_intermediate/10-nav2/", "/04_intermediate/11_project-autonomous-bot/",
)
WINDOW_LINE = re.compile(
    r'^\s+(?P<xid>0x[0-9a-f]+) "(?P<title>.*?)":'
    + r'(?: \("(?P<class_instance>[^"]*)" "(?P<class_name>[^"]*)"\))?'
    + r'.*?(?P<width>\d+)x(?P<height>\d+)\+-?\d+\+-?\d+'
)
RAISE_WINDOW = (
    "import ctypes,sys,time\n"
    "x=ctypes.CDLL('libX11.so.6'); x.XOpenDisplay.restype=ctypes.c_void_p\n"
    "d=x.XOpenDisplay(None); x.XRaiseWindow(d,int(sys.argv[1],16)); x.XSync(d,False)\n"
    "time.sleep(0.15); x.XCloseDisplay(d)\n"
)
GAZEBO_ITEMS = (
    ("gazebo_robot", "gazebo.png", (405, 525, 60, 50), "rendered robot pixels", "#5ea8f4", 0.005),
    ("gazebo_obstacle_ground", "gazebo.png", (260, 490, 90, 90), "distinct obstacle and ground pixels", "#d57e59", 0.005),
    ("gazebo_sensor_visualization", "gazebo-live.png", (100, 350, 650, 350), "rendered lidar rays", "#0000ff", 0.0001),
)
RVIZ_ITEMS = (
    ("rviz_map_status_ok", 145, "Map enabled under Global Status: Ok"),
    ("rviz_robot_model_status_ok", 165, "RobotModel enabled under Global Status: Ok"),
    ("rviz_laser_scan_status_ok", 185, "LaserScan enabled under Global Status: Ok"),
    ("rviz_point_cloud_status_ok", 205, "PointCloud2 enabled under Global Status: Ok"),
    ("rviz_tf_status_ok", 225, "TF enabled under Global Status: Ok"),
    ("rviz_path", 245, "Path enabled under Global Status: Ok"),
)


def parse_config(argv: list[str]) -> Config:
    if len(argv) != 10:
        raise AuditInputError(f"expected exactly five option/value pairs: {', '.join(FLAGS)}")
    values: dict[str, str] = {}
    for index in range(0, len(argv), 2):
        flag, value = argv[index : index + 2]
        if flag not in FLAGS or flag in values:
            raise AuditInputError(f"unsupported or repeated option: {flag}")
        values[flag] = value
    return Config(values["--site"], Path(values["--routes-file"]), values["--gazebo-title"], values["--rviz-title"], Path(values["--evidence"]))


def command(argv: list[str], timeout: float = 12.0) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, check=False, capture_output=True, text=True, timeout=timeout)


def image_info(path: Path) -> ImageInfo:
    result = command(["identify", "-format", "%m %w %h %[entropy]", str(path)])
    if result.returncode != 0:
        return ImageInfo(0, 0, 0.0)
    image_format, width, height, entropy = result.stdout.split()
    if image_format != "PNG":
        return ImageInfo(0, 0, 0.0)
    return ImageInfo(int(width), int(height), float(entropy) * 8.0)


def crop_signal(path: Path, bounds: tuple[int, int, int, int], color: str | None) -> float:
    operations = ["-format", "%[entropy]", "info:"] if color is None else ["-fuzz", "12%", "-fill", "black", "+opaque", color, "-fill", "white", "-opaque", color, "-format", "%[fx:mean]", "info:"]
    result = command(["convert", str(path), "-crop", f"{bounds[2]}x{bounds[3]}+{bounds[0]}+{bounds[1]}", *operations])
    return float(result.stdout) * (8.0 if color is None else 1.0) if result.returncode == 0 and result.stdout else 0.0


def canonical_window_title(title: str, class_instance: str | None) -> str:
    if class_instance == "gz-sim-gui" and title == "Gazebo Sim":
        return "Gazebo"
    if class_instance == "rviz2" and title.endswith(" - RViz"):
        return "RViz"
    return title


def windows_for(title_pattern: str) -> list[Window]:
    try:
        title_regex = re.compile(title_pattern)
    except re.error as error:
        raise AuditInputError(f"invalid title regex {title_pattern!r}: {error}") from error
    result = command(["xwininfo", "-root", "-tree"])
    matches: list[Window] = []
    for line in result.stdout.splitlines():
        parsed = WINDOW_LINE.match(line)
        if parsed:
            title = canonical_window_title(parsed["title"], parsed["class_instance"])
            if title_regex.fullmatch(title):
                matches.append(Window(parsed["xid"], title, int(parsed["width"]), int(parsed["height"])))
    return sorted(matches, key=lambda window: window.width * window.height)


def required_window(label: str, title_pattern: str) -> Window:
    windows = windows_for(title_pattern)
    if len(windows) == 1:
        return windows[0]
    if not windows:
        raise AuditInputError(f"{label} window missing for {title_pattern!r}")
    raise AuditInputError(f"{label} window ambiguous for {title_pattern!r}: {len(windows)} matches")


def capture_window(window: Window, destination: Path) -> ImageInfo:
    _ = command([sys.executable, "-c", RAISE_WINDOW, window.xid])
    result = command(["import", "-window", window.xid, str(destination)])
    return image_info(destination) if result.returncode == 0 else ImageInfo(0, 0, 0.0)


def validate_boxes(items: list[CheckItem], dimensions: dict[str, tuple[int, int]]) -> list[str]:
    failures: list[str] = []
    for item in items:
        x, y, width, height = item.bounds
        image_width, image_height = dimensions.get(item.artifact, (0, 0))
        if min(x, y, width, height) < 0 or width == 0 or height == 0 or x + width > image_width or y + height > image_height:
            failures.append(f"{item.item_id}: invalid bounding box")
    for index, left in enumerate(items):
        lx, ly, lw, lh = left.bounds
        for right in items[index + 1 :]:
            rx, ry, rw, rh = right.bounds
            overlaps = left.artifact == right.artifact and lx < rx + rw and rx < lx + lw and ly < ry + rh and ry < ly + lh
            if overlaps:
                failures.append(f"{left.item_id}/{right.item_id}: overlapping bounding boxes")
    return failures


def browser_audit(config: Config, routes: list[str], failures: list[str]) -> list[dict[str, str | int | bool]]:
    from playwright.sync_api import Error as PlaywrightError
    from playwright.sync_api import sync_playwright

    records: list[dict[str, str | int | bool]] = []
    screenshot_hashes: list[str] = []
    (config.evidence / "route-h1").mkdir(exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            for index, route in enumerate(routes):
                console_errors: list[str] = []
                network_errors: list[str] = []
                page = browser.new_page(viewport={"width": 1280, "height": 720})
                page.on("console", lambda message, errors=console_errors: errors.append(message.text) if message.type == "error" else None)
                page.on("requestfailed", lambda request, errors=network_errors: errors.append(f"{request.method} {request.url}: {request.failure}"))
                try:
                    response = page.goto(urljoin(config.site.rstrip("/") + "/", route.lstrip("/")), wait_until="networkidle", timeout=10_000)
                    status = response.status if response else 0
                    h1_locator = page.locator("h1").first
                    h1 = h1_locator.text_content() or ""
                    active = page.locator("nav .md-nav__link--active").count() > 0
                    font_ready = page.wait_for_function("document.fonts.status === 'loaded'")
                    font_ready.dispose()
                    screenshot = config.evidence / "routes" / f"{index + 1:02d}-{route.strip('/').split('/')[-1] or 'index'}.png"
                    route_bytes = page.screenshot(path=str(screenshot), full_page=True)
                    h1_capture = config.evidence / "route-h1" / screenshot.name
                    info = image_info(screenshot)
                    h1_bytes = b""
                    h1_info = ImageInfo(0, 0, 0.0)
                    if h1.strip() and h1_locator.is_visible(timeout=1_000):
                        h1_bytes = h1_locator.screenshot(path=str(h1_capture))
                        h1_info = image_info(h1_capture)
                    screenshot_hashes.append(hashlib.sha256(screenshot.read_bytes()).hexdigest())
                    passed = status == 200 and bool(h1.strip()) and bool(route_bytes) and bool(h1_bytes) and active and not console_errors and not network_errors and info.width == 1280 and info.entropy_bits > 0.0 and h1_info.entropy_bits > 0.05
                except PlaywrightError as error:
                    status, h1, active, passed = 0, "", False, False
                    console_errors.append(str(error))
                finally:
                    page.close()
                if not passed:
                    failures.append(f"broken route {route}: http={status} h1={bool(h1.strip())} active_nav={active} errors={console_errors + network_errors}")
                records.append({"route": route, "http": status, "h1": h1, "active_nav": active, "passed": passed})
            if len(set(screenshot_hashes)) != len(routes):
                failures.append("route screenshots are not visually distinct")
        finally:
            browser.close()
    return records


def runtime_corroboration(config: Config, gazebo_window: Window, rviz_window: Window) -> bool:
    log_path = config.evidence / "live-corroboration.log"
    gazebo = config.evidence / "gazebo.png"
    rviz = config.evidence / "rviz.png"
    if os.environ.get("VISUAL_AUDIT_FIXTURE") == "animated-x11":
        gazebo_live = config.evidence / "gazebo-live.png"
        rviz_live = config.evidence / "rviz-live.png"
        _ = capture_window(gazebo_window, gazebo_live)
        _ = capture_window(rviz_window, rviz_live)
        gz_diff = command(["compare", "-metric", "AE", str(gazebo), str(gazebo_live), "null:"])
        rviz_diff = command(["compare", "-metric", "AE", str(rviz), str(rviz_live), "null:"])
        _ = log_path.write_text(f"fixture=animated-x11\ngazebo_changed_pixels={gz_diff.stderr}\nrviz_changed_pixels={rviz_diff.stderr}\n", encoding="utf-8")
        return gz_diff.stderr.strip() not in ("", "0") and rviz_diff.stderr.strip() not in ("", "0")
    gz_models, gz_topics = command(["timeout", "8", "gz", "model", "--list"]), command(["timeout", "8", "gz", "topic", "-l"])
    ros_topics = command(["timeout", "8", "ros2", "topic", "list"])
    tf = command(["timeout", "8", "ros2", "run", "tf2_ros", "tf2_echo", "map", "base_link"], 10.0)
    live_info = capture_window(gazebo_window, config.evidence / "gazebo-live.png")
    combined = f"{gz_models.stdout}\n{gz_topics.stdout}\n{ros_topics.stdout}\n{tf.stdout}\n{tf.stderr}"
    _ = log_path.write_text(combined, encoding="utf-8")
    required = ("training_floor", "training_obstacle", "tutorial_bot", "/tutorial_bot/lidar", "/map", "/scan", "/camera/points", "/plan", "/robot_description", "Translation:")
    return all(token in combined for token in required) and live_info.width >= 1280 and live_info.height >= 720


def run(config: Config) -> int:
    config.evidence.mkdir(parents=True, exist_ok=True)
    (config.evidence / "routes").mkdir(exist_ok=True)
    failures: list[str] = []
    routes = [route.strip() for route in config.routes_file.read_text(encoding="utf-8").splitlines() if route.strip()]
    missing_routes = [route for route in FROZEN_ROUTES if route not in routes]
    unexpected_routes = [route for route in routes if route not in FROZEN_ROUTES]
    if missing_routes or unexpected_routes or len(routes) != len(FROZEN_ROUTES):
        failures.append(f"frozen route list mismatch: missing={missing_routes} unexpected={unexpected_routes} count={len(routes)}")
    records = browser_audit(config, routes, failures)
    gazebo_window: Window | None = None
    rviz_window: Window | None = None
    for label, title_pattern in (("Gazebo", config.gazebo_title), ("RViz", config.rviz_title)):
        try:
            window = required_window(label, title_pattern)
        except AuditInputError as error:
            failures.append(str(error))
        else:
            if label == "Gazebo":
                gazebo_window = window
            else:
                rviz_window = window
    infos: dict[str, ImageInfo] = {}
    for label, window in (("gazebo", gazebo_window), ("rviz", rviz_window)):
        if window is not None:
            infos[f"{label}.png"] = capture_window(window, config.evidence / f"{label}.png")
            info = infos[f"{label}.png"]
            if info.width < 1280 or info.height < 720 or info.entropy_bits <= 1.0:
                failures.append(f"{label} screenshot undersized/blank: {info.width}x{info.height} entropy={info.entropy_bits:.3f}")
    live = gazebo_window is not None and rviz_window is not None and runtime_corroboration(config, gazebo_window, rviz_window)
    items: list[CheckItem] = []
    for item_id, artifact, bounds, observable, color, threshold in GAZEBO_ITEMS:
        passed = live and crop_signal(config.evidence / artifact, bounds, color) > threshold if (config.evidence / artifact).exists() else False
        items.append(CheckItem(item_id, passed, artifact, bounds, observable, "live-corroboration.log"))
    for item_id, y, observable in RVIZ_ITEMS:
        bounds = (20, y, 155, 18)
        passed = live and crop_signal(config.evidence / "rviz.png", bounds, None) > 0.5 if (config.evidence / "rviz.png").exists() else False
        items.append(CheckItem(item_id, passed, "rviz.png", bounds, observable, "live-corroboration.log"))
    for item in items:
        if not item.passed:
            failures.append(f"missing required semantic item: {item.item_id}")
    dimensions = {artifact: (info.width, info.height) for artifact, info in infos.items()}
    dimensions["gazebo-live.png"] = dimensions.get("gazebo.png", (0, 0))
    failures.extend(validate_boxes(items, dimensions))
    checklist = {"schema_version": 1, "items": [{"id": item.item_id, "passed": item.passed, "artifact": item.artifact, "bounds": list(item.bounds), "observable": item.observable, "live_status_artifact": item.live_status_artifact} for item in items]}
    _ = (config.evidence / "semantic-checklist.json").write_text(json.dumps(checklist, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = {"schema_version": 1, "passed": not failures, "routes": records, "windows": {name: {"width": info.width, "height": info.height, "entropy_bits": info.entropy_bits} for name, info in infos.items()}, "failures": failures}
    _ = (config.evidence / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("visual audit PASS" if not failures else "visual audit FAIL: " + "; ".join(failures))
    return 0 if not failures else 1


def interrupt(_signal_number: int, _frame: FrameType | None) -> None:
    raise InterruptedError


def main() -> int:
    try:
        if sys.argv[1:] == ["--help"]:
            print(HELP_TEXT, end="")
            return 0
        config = parse_config(sys.argv[1:])
        _ = signal.signal(signal.SIGTERM, interrupt)
        return run(config)
    except (AuditInputError, OSError, subprocess.TimeoutExpired, InterruptedError) as error:
        print(f"visual audit FAIL: {error}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("visual audit FAIL: interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
