"""Validate DOPE ground truth and run the official training/inference/evaluation programs."""
import argparse
import json
import math
from pathlib import Path
import subprocess
import sys


# 이 파일은 Isaac Sim이 생성한 자세 추정 데이터를 읽어 외부 DOPE 프로그램으로 전달하는 단계이다.
# SimulationApp을 시작하지 않으며 학습·추론은 --python으로 지정한 별도 환경에서 실행한다.
def audit_dataset(data: Path, object_name: str) -> dict:
    frames = 0
    instances = 0
    for label in sorted(data.rglob("*.json")):
        document = json.loads(label.read_text())
        if "objects" not in document:
            continue
        if not any(label.with_suffix(suffix).is_file() for suffix in (".png", ".jpg", ".jpeg")):
            raise ValueError(f"Missing paired RGB image for {label}")
        frames += 1
        for obj in document["objects"]:
            if obj.get("class", "").lower() != object_name.lower():
                continue
            # DOPE 정답의 projected_cuboid는 물체 경계 상자의 8개 꼭짓점과 중심을 영상에 투영한 9개 좌표이다.
            points = obj.get("projected_cuboid", [])
            if len(points) != 9 or any(len(point) != 2 for point in points):
                raise ValueError(f"Expected eight corners and center (9 x 2) in {label}")
            if not all(isinstance(v, (int, float)) and math.isfinite(v) for point in points for v in point):
                raise ValueError(f"Non-finite cuboid projection in {label}")
            instances += 1
    if frames == 0 or instances == 0:
        raise ValueError(f"No paired DOPE records containing class {object_name!r} in {data}")
    return {"frames": frames, "matching_instances": instances, "object": object_name}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["audit", "train", "infer", "evaluate"])
    parser.add_argument("--repo", type=Path, help="NVlabs/Deep_Object_Pose checkout")
    parser.add_argument("--data", required=True, type=Path)
    parser.add_argument("--object", default="003_cracker_box")
    parser.add_argument("--python", default=sys.executable, help="Python in DOPE's separately prepared environment")
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--batchsize", type=int, default=2)
    parser.add_argument("--weights", type=Path)
    parser.add_argument("--predictions", type=Path)
    parser.add_argument("--inference-config", type=Path)
    parser.add_argument("--camera", type=Path)
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("output"))
    args = parser.parse_args()
    if args.epochs < 1 or args.batchsize < 1:
        parser.error("epochs and batchsize must be positive")
    data = args.data.expanduser().resolve(strict=True)
    report = audit_dataset(data, args.object)
    print(json.dumps(report, indent=2))
    if args.action == "audit":
        return
    if args.repo is None:
        parser.error("--repo is required for execution")
    repo = args.repo.expanduser().resolve(strict=True)
    output = args.output.expanduser().resolve()
    if output.exists():
        parser.error(f"Use a new --output directory: {output}")
    if args.action == "train":
        cwd = repo / "train"
        command = [args.python, "-m", "torch.distributed.launch", "--nproc_per_node=1", "train.py",
                   "--data", str(data), "--object", args.object, "--batchsize", str(args.batchsize),
                   "--epochs", str(args.epochs), "--workers", "0", "--manualseed", "42", "--outf", str(output / "weights")]
        expected = "train.py"
    elif args.action == "infer":
        for name in ["weights", "inference_config", "camera"]:
            value = getattr(args, name)
            if value is None or not value.exists():
                parser.error(f"--{name.replace('_', '-')} must exist")
        cwd = repo / "inference"
        command = [args.python, "inference.py", "--weights", str(args.weights.resolve()), "--parallel",
                   "--data", str(data), "--object", args.object, "--config", str(args.inference_config.resolve()),
                   "--camera", str(args.camera.resolve()), "--outf", str(output / "predictions")]
        expected = "inference.py"
    else:
        if args.predictions is None or not args.predictions.is_dir():
            parser.error("--predictions must be an existing prediction directory")
        cwd = repo / "evaluate"
        command = [args.python, "evaluate.py", "--data_prediction", str(args.predictions.resolve()),
                   "--data", str(data), "--outf", str(output / "metrics"), "--cuboid"]
        expected = "evaluate.py"
    if not (cwd / expected).is_file():
        parser.error(f"Expected pinned DOPE repository layout: {cwd / expected}")
    output.mkdir(parents=True)
    (output / "input_audit.json").write_text(json.dumps(report, indent=2))
    (output / "command.json").write_text(json.dumps(command, indent=2))
    # 준비된 DOPE 환경에서 선택한 학습·추론·평가 프로그램을 실행하고 종료를 기다린다.
    subprocess.run(command, cwd=cwd, check=True)
    if args.action == "train" and not list((output / "weights").glob("*.pth")):
        raise RuntimeError("Training exited without a model checkpoint")
    if args.action == "evaluate" and not (output / "metrics/result.csv").is_file():
        raise RuntimeError("Evaluation exited without result.csv")


if __name__ == "__main__":
    main()
