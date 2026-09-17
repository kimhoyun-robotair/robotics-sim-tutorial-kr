"""Run the native pose generator using this package's private, editable configuration."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--isaac-sim", type=Path, default=Path(os.environ.get("ISAAC_SIM_PATH", Path.home() / "isaacsim")))
    parser.add_argument("--writer", choices=["dope", "centerpose", "ycbvideo"], default="dope")
    parser.add_argument("--num-mesh", type=int, default=4)
    parser.add_argument("--num-dome", type=int, default=4)
    parser.add_argument("--dome-interval", type=int, default=1)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("output"))
    parser.add_argument("--use-s3", action="store_true")
    parser.add_argument("--endpoint")
    parser.add_argument("--bucket")
    parser.add_argument("--steps", type=int, help="GUI updates after the finite dataset is saved; omit to wait for window close")
    args = parser.parse_args()
    if args.steps is not None and args.steps < 1:
        parser.error("--steps must be a positive integer")
    if min(args.num_mesh, args.num_dome) < 0 or args.num_mesh + args.num_dome < 1 or args.dome_interval < 1:
        parser.error("Use nonnegative frame counts, at least one frame, and positive dome interval")
    if args.use_s3 and (args.writer != "dope" or not args.endpoint or not args.bucket):
        parser.error("S3 requires writer=dope, --endpoint and --bucket")
    install = args.isaac_sim.expanduser().resolve()
    # 설치된 pose_generation 예제는 객체 자세 추정에 사용할 이미지와 정답 주석을 생성한다.
    native = install / "standalone_examples/replicator/pose_generation"
    if not (native / "pose_generation.py").is_file() or not (install / "python.sh").is_file():
        parser.error(f"Isaac Sim 5.1 pose_generation is missing: {native}")
    output = args.output.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=False)
    work = output / "native"
    # 설치 예제와 설정을 작업 폴더로 복사하여 이번 실행의 writer·장면 설정을 적용한다.
    shutil.copytree(native, work, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for config in Path(__file__).with_name("config").glob("*.yaml"):
        shutil.copy2(config, work / "config" / config.name)
    # Isaac Sim의 python.sh를 통해 native_runner와 pose_generation을 실행한다.
    # --writer는 DOPE·CenterPose·YCBVideo 중 주석의 저장 형식을 선택한다.
    command = [str(install / "python.sh"), str(Path(__file__).with_name("native_runner.py"))]
    if args.headless:
        command.append("--headless")
    if args.steps is not None:
        command += ["--steps", str(args.steps)]
    command += [str(work / "pose_generation.py"),
               "--writer", args.writer, "--num_mesh", str(args.num_mesh), "--num_dome", str(args.num_dome),
               "--dome_interval", str(args.dome_interval), "--output_folder", str(output / "data"), "--debug"]
    if args.headless:
        command += ["--no-window"]
    if args.use_s3:
        command += ["--use_s3", "--endpoint", args.endpoint, "--bucket", args.bucket]
    (output / "command.json").write_text(json.dumps(command, indent=2))
    subprocess.run(command, cwd=work, check=True)
    if not args.use_s3 and not any((output / "data").rglob("*.png")):
        raise RuntimeError("Generator exited without PNG data; inspect asset/writer logs")


if __name__ == "__main__":
    main()
