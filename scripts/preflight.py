"""Ubuntu/Jazzy/Isaac Sim 배포판/GPU를 읽기 전용으로 확인한다. 렌더 검사는 별도이다."""
import argparse
import json
import os
import platform
import re
import shutil
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--isaac-path", type=Path, default=Path(os.environ.get("ISAAC_SIM_PATH", "~/isaacsim-6.0.1")).expanduser())
    parser.add_argument("--output", type=Path, default=Path("artifacts/preflight.json"))
    args = parser.parse_args()
    checks = []
    def check(name, ok, observed):
        checks.append({"name": name, "status": "PASS" if ok else "FAIL", "observed": observed})
    try:
        os_release = platform.freedesktop_os_release()
    except OSError:
        os_release = {}
    check("OS", os_release.get("ID") == "ubuntu" and os_release.get("VERSION_ID") == "24.04", os_release)
    check("architecture", platform.machine() == "x86_64", platform.machine())
    version_file = args.isaac_path / "VERSION"
    version = version_file.read_text().strip() if version_file.is_file() else "missing"
    check("Isaac Sim VERSION", bool(re.match(r"^6\.0\.1(?:$|[-+])", version)), version)
    check("python.sh", (args.isaac_path / "python.sh").is_file(), str(args.isaac_path / "python.sh"))
    check("ROS_DISTRO", os.environ.get("ROS_DISTRO") == "jazzy", os.environ.get("ROS_DISTRO"))
    check("ros2 CLI", bool(shutil.which("ros2")), shutil.which("ros2"))
    if shutil.which("nvidia-smi"):
        gpu = subprocess.run(["nvidia-smi", "--query-gpu=name,driver_version,memory.total", "--format=csv,noheader"],
                             capture_output=True, text=True, timeout=20)
        check("NVIDIA GPU query", gpu.returncode == 0 and bool(gpu.stdout.strip()), gpu.stdout.strip() or gpu.stderr.strip())
    else:
        check("NVIDIA GPU query", False, "nvidia-smi missing")
    report = {"status": "PASS" if all(c["status"] == "PASS" for c in checks) else "FAIL", "checks": checks,
              "scope": "environment presence only; RT cores, driver suitability, VRAM sufficiency and simulation require Compatibility Checker and runtime tests"}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
