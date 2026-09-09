#!/usr/bin/env python3
"""Run bounded Isaac Sim 5.1 GPU exercises and retain machine-readable evidence.

Use system Python: python3 scripts/validate_runtime.py --isaacsim-path ~/isaacsim
Exit 0: selected tests passed; 1: test failed/timed out; 2: runtime not available.
This script never installs Isaac Sim or changes an existing installation.
"""

import argparse
import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import re
import shutil
import signal
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
TESTS = ("hello_stage", "drive_jetbot", "camera_imu", "rtx_lidar")


def capture(command):
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=15, check=False)
        return {"returncode": result.returncode, "stdout": result.stdout.strip(), "stderr": result.stderr.strip()}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"returncode": None, "error": f"{type(exc).__name__}: {exc}"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--isaacsim-path", type=Path, default=Path(os.environ.get("ISAACSIM_PATH", "~/isaacsim")))
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results" / "runtime")
    parser.add_argument("--only", choices=TESTS, nargs="+", default=list(TESTS))
    parser.add_argument("--timeout", type=float, default=600, help="Maximum wall seconds per process, including startup")
    parser.add_argument("--gui", action="store_true")
    args = parser.parse_args()
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("--timeout must be finite and positive")
    if len(args.only) != len(set(args.only)):
        parser.error("--only must not contain duplicate tests")
    installation = args.isaacsim_path.expanduser().resolve()
    output = args.output_dir.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    # A new directory prevents stale child results from being reused after a failed launch.
    run_dir = output / datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
    run_dir.mkdir()
    summary_path = run_dir / "summary.json"
    report = {
        "status": "RUNNING", "scope": list(args.only), "complete_suite": set(args.only) == set(TESTS),
        "python": sys.version, "platform": platform.platform(), "installation": str(installation),
        "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "git_commit": capture(["git", "-C", str(ROOT), "rev-parse", "HEAD"]),
        "nvidia_smi": capture(["nvidia-smi", "--query-gpu=name,driver_version,memory.total", "--format=csv,noheader"]),
        "tests": [],
    }
    source_paths = [ROOT / "examples" / "standalone" / f"{name}.py" for name in (*TESTS, "smoke_common")]
    report["source_sha256"] = {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                               for path in source_paths}

    def save():
        summary_path.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")

    launcher = installation / "python.sh"
    version_file = installation / "VERSION"
    version = version_file.read_text(encoding="utf-8").strip() if version_file.is_file() else None
    report["installation_version"] = version
    reasons = []
    if not launcher.is_file() or not os.access(launcher, os.X_OK):
        reasons.append(f"실행 가능한 python.sh가 없다: {launcher}")
    if version is None or not re.match(r"^5\.1\.0(?:[^0-9]|$)", version):
        reasons.append("설치 폴더의 VERSION에서 Isaac Sim 5.1.0을 확인하지 못했다")
    if shutil.which("nvidia-smi") is None or report["nvidia_smi"]["returncode"] != 0:
        reasons.append("NVIDIA GPU/드라이버를 nvidia-smi로 확인하지 못했다")
    if reasons:
        report.update(status="NOT_RUN", reasons=reasons)
        report["tests"] = [{"test": name, "status": "NOT_RUN"} for name in args.only]
        save()
        print(f"NOT_RUN: {summary_path}")
        for reason in reasons:
            print(reason)
        return 2

    save()
    for name in args.only:
        test_dir = run_dir / name
        test_dir.mkdir()
        command = [str(launcher), str(ROOT / "examples" / "standalone" / f"{name}.py"),
                   "--output-dir", str(test_dir)]
        if args.gui:
            command.append("--gui")
        item = {"test": name, "command": command, "status": "RUNNING"}
        report["tests"].append(item)
        save()
        started = time.monotonic()
        print(f"RUNNING: {name}", flush=True)
        with (test_dir / "runtime.log").open("w", encoding="utf-8") as log:
            try:
                process = subprocess.Popen(command, cwd=installation, stdout=log,
                                           stderr=subprocess.STDOUT, start_new_session=True)
                try:
                    returncode = process.wait(timeout=args.timeout)
                    item["returncode"] = returncode
                except (subprocess.TimeoutExpired, KeyboardInterrupt) as exc:
                    interrupted = isinstance(exc, KeyboardInterrupt)
                    os.killpg(process.pid, signal.SIGTERM)
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait()
                    item.update(status="INTERRUPTED" if interrupted else "TIMEOUT",
                                returncode=process.returncode)
                child_path = test_dir / "result.json"
                child = json.loads(child_path.read_text(encoding="utf-8")) if child_path.exists() else {}
                item["result"] = child
                if item["status"] not in ("TIMEOUT", "INTERRUPTED"):
                    item["status"] = "PASS" if process.returncode == 0 and child.get("status") == "PASS" else "FAIL"
            except (OSError, ValueError) as exc:
                item.update(status="FAIL", error=f"{type(exc).__name__}: {exc}")
        item["elapsed_seconds"] = round(time.monotonic() - started, 3)
        item["log"] = str(test_dir / "runtime.log")
        fatal_pattern = re.compile(r"VK_ERROR_DEVICE_LOST|VK_ERROR_OUT_OF_DEVICE_MEMORY|ERROR_OUT_OF_DEVICE_MEMORY|CUDA_ERROR_ILLEGAL_ADDRESS|CUDA_ERROR_OUT_OF_MEMORY|Failed to create any GPU devices|Out of device memory")
        with (test_dir / "runtime.log").open(encoding="utf-8", errors="replace") as log:
            item["fatal_gpu_log_lines"] = [line.strip()[:500] for line in log if fatal_pattern.search(line)][:10]
        if item["fatal_gpu_log_lines"] and item["status"] == "PASS":
            item["status"] = "FAIL"
        save()
        print(f"{item['status']}: {name}", flush=True)
        if item["status"] == "INTERRUPTED":
            break

    report["status"] = "PASS" if all(test["status"] == "PASS" for test in report["tests"]) else "FAIL"
    save()
    print(f"{report['status']}: {summary_path}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
