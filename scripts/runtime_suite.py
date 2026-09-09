"""Isaac Sim 6.0.1 실습을 독립 프로세스로 실행하고 증거를 모은다. GPU 필수."""
import argparse
import datetime
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]


def passed(report):
    """결과가 없거나 성공 키가 불명확하면 통과시키지 않는다."""
    if not isinstance(report, dict):
        return False
    if report.get("error") or report.get("errors") or report.get("status") in ("FAIL", "PARTIAL", "NOT_RUN"):
        return False
    if "passed" in report:
        return report["passed"] is True
    return report.get("status") == "PASS"


def read_report(path):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {"status": "FAIL", "error": "report is not an object"}
    except (OSError, ValueError):
        return {"status": "FAIL", "error": "missing or malformed report", "path": str(path)}


def stop_process(process):
    if process.poll() is None:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            return
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                return
            process.wait(timeout=10)


def execute(command, log, timeout):
    started = time.monotonic()
    env = dict(os.environ, PYTHONUNBUFFERED="1")
    with log.open("w", encoding="utf-8") as stream:
        try:
            process = subprocess.Popen(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT,
                                       env=env, start_new_session=True)
        except OSError as exc:
            stream.write(str(exc))
            return {"returncode": 127, "error": str(exc), "command": command, "log": str(log)}
        try:
            code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            stop_process(process)
            code = 124
        finally:
            stop_process(process)
    return {"returncode": code, "wall_seconds": round(time.monotonic() - started, 3),
            "command": command, "log": str(log)}


def run_ros(isaac_python, ros_python, out, timeout):
    log = out / "ros-scene.log"
    env = dict(os.environ, PYTHONUNBUFFERED="1")
    command = [str(isaac_python), str(ROOT / "examples/07_ros_scene.py"), "--headless", "--seconds", "35",
               "--output", str(out / "ros-scene.json")]
    with log.open("w", encoding="utf-8") as stream:
        try:
            process = subprocess.Popen(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT,
                                       env=env, start_new_session=True)
        except OSError as exc:
            return {"status": "FAIL", "error": str(exc), "log": str(log)}
        try:
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    return {"status": "FAIL", "error": "ROS scene exited before READY", "log": str(log)}
                if "READY:" in log.read_text(encoding="utf-8", errors="replace"):
                    break
                time.sleep(0.25)
            else:
                return {"status": "FAIL", "error": "ROS scene startup timeout", "log": str(log)}
            result = execute([str(ros_python), str(ROOT / "scripts/ros_acceptance.py"), "--mode", "scene",
                              "--duration", "15", "--exercise-timeout", "--output", str(out / "ros-acceptance.json")],
                             out / "ros-acceptance.log", 45)
            try:
                scene_code = process.wait(timeout=60)
            except subprocess.TimeoutExpired:
                scene_code = 124
            acceptance = read_report(out / "ros-acceptance.json")
            scene = read_report(out / "ros-scene.json")
            required = acceptance.get("checks")
            required = required if isinstance(required, dict) else {}
            ok = result["returncode"] == 0 and scene_code == 0 and passed(acceptance) and passed(scene)
            ok = ok and acceptance.get("exercise_timeout") is True
            ok = ok and required.get("command_caused_motion") is True and required.get("watchdog_observed_stop") is True
            ok = ok and isinstance(scene.get("commands_received"), int) and scene["commands_received"] > 0
            ok = ok and isinstance(scene.get("watchdog_stops"), int) and scene["watchdog_stops"] > 0
            return {"status": "PASS" if ok else "FAIL", "acceptance": acceptance,
                    "scene": scene, "scene_returncode": scene_code, **result}
        finally:
            stop_process(process)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--isaac-path", type=Path, default=Path(os.environ.get("ISAAC_SIM_PATH", "~/isaacsim-6.0.1")).expanduser())
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=600, help="각 GPU 프로세스 제한(초)")
    parser.add_argument("--with-ros", action="store_true", help="Jazzy 터미널에서 통신·watchdog도 함께 검증하다")
    parser.add_argument("--ros-python", type=Path, default=Path("/usr/bin/python3"))
    args = parser.parse_args()
    if args.timeout < 60:
        parser.error("--timeout은 셰이더 초기화를 고려하여 60초 이상 지정한다")
    out = args.output_dir.resolve()
    if out.exists() and any(out.iterdir()):
        parser.error("새 출력 폴더를 사용한다. 이전 PASS 파일을 재사용하지 않는다")
    out.mkdir(parents=True, exist_ok=True)
    isaac_python = args.isaac_path.resolve() / "python.sh"
    version_path = args.isaac_path / "VERSION"
    version = version_path.read_text().strip() if version_path.exists() else "missing"
    if not isaac_python.is_file() or not (version == "6.0.1" or version.startswith(("6.0.1-", "6.0.1+"))):
        parser.error("Isaac Sim 6.0.1 배포판의 VERSION과 python.sh가 필요하다")
    if args.with_ros and os.environ.get("ROS_DISTRO") != "jazzy":
        parser.error("--with-ros는 source /opt/ros/jazzy/setup.bash 후 실행한다")
    entries = []
    report = {"status": "RUNNING", "version": version, "created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "ros_requested": args.with_ros, "entries": entries,
              "scope": "bounded fixtures only; GUI appearance, Nav2 performance and all hardware combinations are outside automated acceptance"}
    def save():
        (out / "suite.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    save()
    tasks = [
        ("drop", "01_drop_cube.py", ["--output", str(out / "drop.json")], out / "drop.json"),
        ("robot", "03_robot_stability.py", ["--output-dir", str(out / "robot")], out / "robot/report.json"),
        ("camera", "04_camera_check.py", ["--output-dir", str(out / "camera")], out / "camera/report.json"),
        ("lidar", "05_lidar_check.py", ["--output-dir", str(out / "lidar")], out / "lidar/report.json"),
    ]
    for name, script, extra, result_path in tasks:
        print(f"RUN {name}", flush=True)
        result = execute([str(isaac_python), str(ROOT / "examples" / script), "--headless", *extra], out / f"{name}.log", args.timeout)
        evidence = read_report(result_path)
        entries.append({"name": name, "status": "PASS" if result["returncode"] == 0 and passed(evidence) else "FAIL",
                        "evidence": str(result_path), **result})
        save()
    print("RUN dataset", flush=True)
    capture = execute([str(isaac_python), str(ROOT / "examples/08_dataset.py"), "--headless", "--frames", "12",
                       "--seed", "601", "--output-dir", str(out / "dataset")], out / "dataset.log", args.timeout)
    inspection = execute([sys.executable, str(ROOT / "scripts/inspect_dataset.py"), str(out / "dataset")], out / "dataset-inspection.log", 120)
    ok = capture["returncode"] == 0 and inspection["returncode"] == 0 and passed(read_report(out / "dataset/inspection.json"))
    entries.append({"name": "dataset", "status": "PASS" if ok else "FAIL", "capture": capture, "inspection": inspection})
    save()
    if args.with_ros:
        print("RUN ROS closed loop", flush=True)
        entries.append({"name": "ros", **run_ros(isaac_python, args.ros_python, out, args.timeout)})
    else:
        entries.append({"name": "ros", "status": "NOT_RUN"})
    report["status"] = ("FAIL" if any(e["status"] == "FAIL" for e in entries)
                        else "PASS" if args.with_ros else "PARTIAL")
    save()
    print(f"{report['status']}: {out / 'suite.json'}")
    return {"PASS": 0, "FAIL": 1, "PARTIAL": 2}[report["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
