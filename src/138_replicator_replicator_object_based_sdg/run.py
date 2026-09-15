"""Launch this package's NVIDIA 5.1 object_based_sdg pipeline with an isolated config."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--isaac-sim", type=Path, default=Path(os.environ.get("ISAAC_SIM_PATH", str(Path.home() / "isaacsim"))))
    parser.add_argument("--config", type=Path, default=Path(__file__).with_name("config.json"))
    parser.add_argument("--frames", type=int, default=6)
    parser.add_argument("--steps", type=int, default=None, help="GUI inspection updates after capture; omit to keep the GUI open until closed")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("output"))
    parser.add_argument("--check-config", action="store_true", help="Validate and print effective config; does not start Kit")
    args = parser.parse_args()
    if args.steps is not None and args.steps < 1:
        parser.error("--steps must be positive")
    if args.frames < 1:
        parser.error("--frames must be positive")
    if args.config.suffix != ".json":
        parser.error("The beginner launcher accepts JSON; native pipeline also supports YAML")
    config = json.loads(args.config.read_text())
    config["num_frames"] = args.frames
    config.setdefault("launch_config", {})["headless"] = args.headless
    config["keep_open"] = not args.headless and args.steps is None
    config["gui_steps"] = args.steps
    config.setdefault("writer_kwargs", {})["output_dir"] = str(args.output.resolve())
    if args.check_config:
        print(json.dumps(config, indent=2))
        return
    python_sh = args.isaac_sim.resolve() / "python.sh"
    if not python_sh.is_file():
        parser.error(f"Isaac Sim 5.1 python.sh not found: {python_sh}")
    output = args.output.resolve()
    if output.exists():
        parser.error(f"Output exists; select a new --output: {output}")
    output.mkdir(parents=True)
    (output / "effective_config.json").write_text(json.dumps(config, indent=2) + "\n")
    with tempfile.TemporaryDirectory(prefix="isaac51-object_based_sdg-") as tmp:
        config_path = Path(tmp) / "config.json"
        config_path.write_text(json.dumps(config))
        command = [str(python_sh), str(Path(__file__).with_name("object_based_sdg.py")), "--config", str(config_path)]
        if args.steps is not None:
            command.extend(["--steps", str(args.steps)])
        subprocess.run(command, check=True)
    images = list(output.rglob("*.png"))
    if not images:
        raise RuntimeError(f"Pipeline exited without PNG outputs: {output}")
    print(f"Actual PNG files: {len(images)}; output: {output}")


if __name__ == "__main__":
    main()
