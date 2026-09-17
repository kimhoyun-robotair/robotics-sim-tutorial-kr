"""Prepare this package's IRO YAML, optionally launch the native Isaac Sim extension."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import shlex
import subprocess
import uuid


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path(__file__).with_name("scene.yaml"))
    parser.add_argument("--isaac-root", type=Path, default=Path.home() / "isaacsim")
    parser.add_argument("--output", type=Path, help="New run directory; must not already exist")
    parser.add_argument("--frames", type=int, help="Override the config's bounded num_frames")
    parser.add_argument("--steps", type=int, default=None, help="Native Kit update limit; omitted keeps GUI open")
    parser.add_argument("--seed", type=int, help="Override the first frame seed")
    parser.add_argument("--launch", action="store_true", help="Start the real IRO extension after preparing")
    parser.add_argument("--headless", action="store_true", help="Generate and exit via native windowless mode")
    args = parser.parse_args()
    if args.steps is not None and args.steps < 1:
        parser.error("--steps must be positive")
    if args.frames is not None and args.frames < 1:
        parser.error("--frames must be positive")
    # PyYAML은 이 예제에서 Isaac Sim Replicator Object(IRO)가 읽을 장면 설정을 불러오고 저장한다.
    import yaml

    package = Path(__file__).resolve().parent
    config_path = args.config.expanduser().resolve()
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("isaacsim.replicator.object"), dict):
        parser.error("The YAML must contain an isaacsim.replicator.object mapping")
    # isaacsim.replicator.object 아래의 설정이 IRO 확장에 전달된다.
    # num_frames는 생성할 프레임 수이고 seed는 무작위 장면 생성의 시작 난수 값이다.
    config = data["isaacsim.replicator.object"]
    if "parent_config" in config:
        parser.error("This launcher requires a complete YAML without parent_config")
    if args.frames is not None:
        config["num_frames"] = args.frames
    if args.seed is not None:
        config["seed"] = args.seed
    if type(config.get("num_frames")) is not int or config["num_frames"] < 1:
        parser.error("num_frames must be a positive integer")
    native = args.isaac_root.expanduser().resolve() / "isaac-sim.sh"
    if args.launch and not native.is_file():
        parser.error(f"Isaac Sim launcher not found: {native}")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    output = (args.output or package / "output" / f"{stamp}-{uuid.uuid4().hex[:8]}").expanduser().resolve()
    output.mkdir(parents=True, exist_ok=False)

    def resolve_paths(value):
        if isinstance(value, str):
            return value.replace("@PACKAGE@", package.as_posix()).replace("@OUTPUT@", output.as_posix())
        if isinstance(value, list):
            return [resolve_paths(item) for item in value]
        if isinstance(value, dict):
            return {key: resolve_paths(item) for key, item in value.items()}
        return value

    data = resolve_paths(data)
    data["isaacsim.replicator.object"]["output_path"] = output.as_posix()
    prepared = output / "prepared.yaml"
    prepared.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
    # isaac-sim.sh는 Kit 기반 Isaac Sim 앱을 시작하는 실행 파일이다.
    # --enable isaacsim.replicator.object로 YAML 장면을 해석하고 합성 데이터를 생성할 확장을 켠다.
    command = ["bash", str(native), "--enable", "isaacsim.replicator.object"]
    if args.steps is not None:
        # /app/quitAfter는 Kit 업데이트 횟수에 따른 종료 설정이며, 생성 데이터의 num_frames와는 별개이다.
        command.append(f"--/app/quitAfter={args.steps}")
    elif not args.headless:
        command.append("--/app/quitAfter=-1")
    if args.headless:
        # 창 없는 모드에서는 /config/file로 준비한 YAML 경로를 IRO에 전달한다.
        # GUI 모드에서는 아래에 출력되는 경로를 Object SDG의 Description File에 입력한다.
        command += ["--no-window", "--/windowless=True", f"--/config/file={prepared}"]
    print(f"configuration: {prepared}", flush=True)
    print(f"output: {output}", flush=True)
    print(f"native command: {shlex.join(command)}", flush=True)
    if not args.headless:
        print("Object SDG > Description File: paste the configuration path; then Simulate.", flush=True)
    if args.launch:
        # 별도 Isaac Sim 프로세스를 실행하고 종료를 기다린다. 실제 IRO API 호출은 활성화한 확장 안에서 수행된다.
        subprocess.run(command, cwd=native.parent, check=True)


if __name__ == "__main__":
    main()
