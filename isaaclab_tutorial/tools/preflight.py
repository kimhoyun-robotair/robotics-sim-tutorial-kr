#!/usr/bin/env python3
"""Record prerequisites without starting Kit. Exit 2 when GPU tests cannot run."""
from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tomllib
from urllib.parse import unquote, urlsplit

PIN = "ffff603eafc6b74264a5261cc0183d6a65390d78"


def capture(command: list[str]) -> dict:
    try:
        p = subprocess.run(command, capture_output=True, text=True, timeout=30, check=False)
        return {"returncode": p.returncode, "stdout": p.stdout.strip(), "stderr": p.stderr.strip()}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"returncode": -1, "error": str(exc)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--isaaclab-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    checks: list[dict] = []

    def check(name: str, ok: bool, detail: object) -> None:
        checks.append({"name": name, "passed": bool(ok), "detail": detail})

    release = platform.freedesktop_os_release() if sys.platform == "linux" else {}
    check("ubuntu_24_04_x86_64", release.get("ID") == "ubuntu" and release.get("VERSION_ID") == "24.04"
          and platform.machine() == "x86_64", release)
    check("python_3_12", sys.version_info[:2] == (3, 12), sys.version)
    git = capture(["git", "-C", str(args.isaaclab_root), "rev-parse", "HEAD"])
    check("isaaclab_commit", git.get("stdout") == PIN, git)
    dirty = capture(["git", "-C", str(args.isaaclab_root), "status", "--porcelain", "--untracked-files=no"])
    check("isaaclab_tracked_source_unmodified", dirty.get("returncode") == 0 and not dirty.get("stdout"), dirty)
    versions = {}
    for package in ("isaacsim", "isaaclab", "isaaclab-physx", "isaaclab-rl", "torch", "torchvision", "rsl-rl-lib"):
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = None
    check("isaacsim_6_0_1", versions["isaacsim"] in ("6.0.1", "6.0.1.0"), versions)
    check("torch_2_10_0", str(versions["torch"]).split("+")[0] == "2.10.0", versions["torch"])
    check("torchvision_0_25_0", str(versions["torchvision"]).split("+")[0] == "0.25.0", versions["torchvision"])
    check("lab_learning_packages", all(versions[x] for x in ("isaaclab", "isaaclab-physx", "isaaclab-rl", "rsl-rl-lib")), versions)
    check("rsl_rl_5_0_1", versions["rsl-rl-lib"] == "5.0.1", versions["rsl-rl-lib"])
    try:
        expected = tomllib.loads((args.isaaclab_root / "source/isaaclab/config/extension.toml").read_text())["package"]["version"]
        check("isaaclab_internal_package_version", versions["isaaclab"] == expected,
              {"expected_from_checkout": expected, "installed": versions["isaaclab"]})
        direct = json.loads(importlib.metadata.distribution("isaaclab").read_text("direct_url.json") or "{}")
        source = Path(unquote(urlsplit(direct.get("url", "")).path)).resolve()
        check("isaaclab_editable_source", direct.get("dir_info", {}).get("editable") is True
              and source == (args.isaaclab_root / "source/isaaclab").resolve(), direct)
    except (OSError, KeyError, ValueError, importlib.metadata.PackageNotFoundError) as exc:
        check("isaaclab_editable_source", False, str(exc))
    smi = capture(["nvidia-smi", "--query-gpu=name,driver_version,memory.total", "--format=csv,noheader"])
    check("nvidia_driver_visible", smi.get("returncode") == 0, smi)
    try:
        import torch
        check("cuda_available", torch.cuda.is_available(), {
            "torch_cuda": torch.version.cuda,
            "device_count": torch.cuda.device_count(),
        })
    except Exception as exc:
        check("cuda_available", False, str(exc))
    disk = shutil.disk_usage(args.output.parent if args.output.parent.exists() else Path.cwd())
    report = {
        "status": "ready_for_gpu_checks" if all(c["passed"] for c in checks) else "prerequisites_failed",
        "checks": checks,
        "python_executable": sys.executable,
        "display_available": bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")),
        "free_disk_gib": round(disk.free / 2**30, 2),
        "note": "This does not certify RTX support, visual quality, robot stability, or trained-policy performance.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for c in checks:
        print(f"{'PASS' if c['passed'] else 'FAIL'} {c['name']}")
    return 0 if all(c["passed"] for c in checks) else 2


if __name__ == "__main__":
    raise SystemExit(main())
