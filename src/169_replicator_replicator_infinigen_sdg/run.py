"""Run the installed Isaac Sim 5.1 Infinigen pipeline with this package's configuration."""

import argparse
import json
from pathlib import Path
import subprocess


def main() -> None:
    package = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--isaac-root", required=True, type=Path)
    parser.add_argument("--config", type=Path, default=package / "sdg_config.json")
    parser.add_argument("--environment", type=Path, action="append", help="Exported Infinigen USD; repeat for several rooms")
    parser.add_argument("--output", type=Path, default=package / "output")
    parser.add_argument("--captures", type=int, help="Override total camera capture steps")
    parser.add_argument("--keep-open", action="store_true", help="Compatibility flag; GUI stays open by default unless --steps is set")
    parser.add_argument("--headless", action="store_true", help="Generate the configured captures and exit without a GUI")
    parser.add_argument("--steps", type=int, help="GUI updates after captures; omit to wait for window close")
    parser.add_argument("--check", action="store_true", help="Validate local inputs without starting Isaac Sim")
    args = parser.parse_args()
    if args.steps is not None and args.steps < 1:
        parser.error("--steps must be a positive integer")
    install = args.isaac_root.expanduser().resolve()
    script = install / "standalone_examples/replicator/infinigen/infinigen_sdg.py"
    for required in (install / "python.sh", script, script.with_name("infinigen_sdg_utils.py")):
        if not required.is_file():
            parser.error(f"Isaac Sim 5.1 installation file missing: {required}")
    config = json.loads(args.config.read_text(encoding="utf-8"))
    if args.environment:
        files = [path.expanduser().resolve() for path in args.environment]
        for path in files:
            if not path.is_file() or path.suffix.lower() not in {".usd", ".usdc", ".usda"}:
                parser.error(f"Exported USD file required: {path}")
        config["environments"] = {"folders": [], "files": [path.as_uri() for path in files]}
    if args.captures is not None:
        config["capture"]["total_captures"] = args.captures
    capture = config["capture"]
    for key in ("total_captures", "num_cameras", "rt_subframes"):
        if not isinstance(capture[key], int) or capture[key] < 1:
            parser.error(f"capture.{key} must be a positive integer")
    if capture["num_floating_captures_per_env"] + capture["num_dropped_captures_per_env"] < 1:
        parser.error("At least one floating or dropped capture is required per room")
    if not config["environments"]["files"] and not config["environments"]["folders"]:
        parser.error("An environment USD file or folder is required")
    output = args.output.expanduser().resolve()
    if output.exists():
        parser.error(f"Output already exists; choose a new directory: {output}")
    for index, writer in enumerate(config["writers"]):
        writer["kwargs"]["output_dir"] = str(output / f"{index:02}_{writer['type']}")
    if args.check:
        print(json.dumps(config, indent=2))
        print("Local configuration and installed entrypoint checked; GPU and asset availability NOT checked.")
        return
    output.mkdir(parents=True, exist_ok=False)
    resolved = output / "resolved_config.json"
    resolved.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    command = [str(install / "python.sh"), str(package / "native_runner.py")]
    if args.headless:
        command.append("--headless")
    if args.steps is not None:
        command += ["--steps", str(args.steps)]
    command += [str(script), "--config", str(resolved), "--close-on-completion"]
    subprocess.run(command, cwd=install, check=True)


if __name__ == "__main__":
    main()
