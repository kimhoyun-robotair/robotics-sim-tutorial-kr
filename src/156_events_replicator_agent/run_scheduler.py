"""Run the Isaac Sim 5.1 IRA scheduler with a prepared lesson config."""
import argparse
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--isaac-root", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--save-usd", action="store_true")
    args = parser.parse_args()
    root = args.isaac_root.expanduser().resolve()
    config = args.config.expanduser().resolve()
    for path in (root / "python.sh", root / "tools/actor_sdg/sdg_scheduler.py", config):
        if not path.is_file():
            parser.error(f"Required file missing: {path}")
    command = [str(root / "python.sh"), str(root / "tools/actor_sdg/sdg_scheduler.py"), "-c", str(config)]
    if args.save_usd:
        command.append("--save_usd")
    subprocess.run(command, cwd=root, check=True)


if __name__ == "__main__":
    main()
