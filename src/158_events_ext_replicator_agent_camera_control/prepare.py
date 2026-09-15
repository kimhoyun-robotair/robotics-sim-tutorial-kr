"""Render this package's native IRA config; does not launch Kit or download assets."""
import argparse
import json
from pathlib import Path


def main():
    package = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets-root", default="https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/5.1")
    parser.add_argument("--output", type=Path, default=package / "output" / "first_run")
    parser.add_argument("--frames", type=int, default=90)
    parser.add_argument("--seed", type=int, default=123456)
    parser.add_argument("--scene", help="Existing custom USD path or URL, overrides the lesson scene.")
    args = parser.parse_args()
    if args.frames < 1:
        parser.error("--frames must be positive")
    output = args.output.expanduser().resolve()
    if output.exists():
        parser.error("Output already exists; choose another --output to preserve captured data")
    config = json.loads((package / "lesson.json").read_text())
    def resolve(value):
        if isinstance(value, str):
            return value.replace("{ASSETS}", args.assets_root.rstrip("/")).replace("{OUTPUT}", str(output)).replace("{PACKAGE}", str(package))
        if isinstance(value, dict):
            return {key: resolve(item) for key, item in value.items()}
        if isinstance(value, list):
            return [resolve(item) for item in value]
        return value
    config = resolve(config)
    ira = config["isaacsim.replicator.agent"]
    ira["global"].update(seed=args.seed, simulation_length=args.frames)
    if args.scene:
        ira["scene"]["asset_path"] = args.scene
    output.mkdir(parents=True)
    for name in ("character_commands.txt", "robot_commands.txt"):
        (output / name).write_text((package / name).read_text())
    config_path = output / "config.yaml"
    config_path.write_text(json.dumps(config, indent=2) + "\n")
    print(config_path)
    print(f"Frames: {args.frames}; capture directory: {output / 'capture'}")


if __name__ == "__main__":
    main()
