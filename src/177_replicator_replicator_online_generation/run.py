"""Launch the installed 5.1 online dataset/training example with checked local inputs."""
import argparse
import json
import os
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["audit", "convert", "sample", "train"])
    parser.add_argument("--isaac-sim", type=Path, default=Path(os.environ.get("ISAAC_SIM_PATH", Path.home() / "isaacsim")))
    parser.add_argument("--root", type=Path, required=True, help="Raw ShapeNet for convert; geometry-only USD root otherwise")
    parser.add_argument("--config", type=Path, default=Path(__file__).with_name("experiment.json"))
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("output"))
    parser.add_argument("--max-models", type=int, default=10)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--steps", type=int, help="GUI updates after conversion/sampling/training; omit to wait for window close")
    args = parser.parse_args()
    if args.steps is not None and args.steps < 1:
        parser.error("--steps must be a positive integer")
    cfg = json.loads(args.config.read_text())
    if len(cfg["categories"]) < 2 or len(cfg["categories"]) != len(cfg["synsets"]):
        parser.error("categories and synsets must describe the same two or more classes")
    if args.max_models < 1 or cfg["training_steps"] < 1 or cfg["num_test_images"] < 1:
        parser.error("iteration and model counts must be positive")
    root = args.root.expanduser().resolve(strict=True)
    report = []
    for name, synset in zip(cfg["categories"], cfg["synsets"]):
        folder = root / synset
        pattern = "*.obj" if args.action == "convert" else "*.usd"
        files = sorted(folder.rglob(pattern)) if folder.is_dir() else []
        usable = [f for f in files if args.action == "convert" or f.stat().st_size <= cfg["max_asset_size_mb"] * 1024**2]
        report.append({"class": name, "synset": synset, "files": len(files), "size_eligible": len(usable)})
        if not usable:
            parser.error(f"No eligible {pattern} files in {folder}; check conversion/category/size limit")
    print(json.dumps(report, indent=2))
    if args.action == "audit":
        return
    install = args.isaac_sim.expanduser().resolve()
    scripts = install / "standalone_examples/replicator/online_generation"
    filename = {"convert": "usd_convertor.py", "sample": "generate_shapenet.py", "train": "train_shapenet.py"}[args.action]
    script = scripts / filename
    launcher = install / "python.sh"
    if not script.is_file() or not launcher.is_file():
        parser.error(f"Isaac Sim 5.1 installed example missing: {script}")
    output = args.output.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=False)
    (output / "asset_audit.json").write_text(json.dumps(report, indent=2))
    command = [str(launcher), str(Path(__file__).with_name("native_runner.py"))]
    if args.headless:
        command.append("--headless")
    if args.steps is not None:
        command += ["--steps", str(args.steps)]
    command += [str(script), "--categories", *cfg["categories"]]
    env = os.environ.copy()
    if args.action == "convert":
        converted = Path(str(root) + "_nomat")
        if converted.exists():
            parser.error(f"Refusing conversion over existing directory {converted}; use a fresh ShapeNet copy")
        env["SHAPENET_LOCAL_DIR"] = str(root)
        command += ["--max_models", str(args.max_models)]
    else:
        command += ["--root", str(root), "--max_asset_size", str(cfg["max_asset_size_mb"])]
        if args.action == "sample":
            command += ["--num_test_images", str(cfg["num_test_images"])]
        else:
            # The upstream break test is i > max_iters; subtract one for exactly N updates.
            command += ["--max_iters", str(cfg["training_steps"] - 1), "--learning_rate", str(cfg["learning_rate"]), "--visualize"]
    if args.headless:
        command += ["--no-window"]
        env["MPLBACKEND"] = "Agg"
    (output / "command.json").write_text(json.dumps(command, indent=2))
    subprocess.run(command, cwd=output, env=env, check=True)
    if args.action == "sample":
        images = list((output / "_out_gen_imgs").glob("*.png"))
        if len(images) != cfg["num_test_images"]:
            raise RuntimeError(f"Expected {cfg['num_test_images']} images, got {len(images)}")


if __name__ == "__main__":
    main()
