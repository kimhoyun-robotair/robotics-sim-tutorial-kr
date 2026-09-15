"""Generate and export real Infinigen dining rooms using an existing Infinigen environment."""

import argparse
from pathlib import Path
import subprocess


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--infinigen-root", type=Path, required=True)
    parser.add_argument("--python", type=Path, required=True, help="Python executable of the installed Infinigen environment")
    parser.add_argument("--seeds", type=int, nargs="+", default=[1, 2])
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent / "rooms")
    args = parser.parse_args()
    root = args.infinigen_root.expanduser().resolve()
    executable = args.python.expanduser().resolve()
    if not (root / "infinigen_examples/generate_indoors.py").is_file() or not executable.is_file():
        parser.error("Provide an installed Infinigen checkout and its Python executable")
    if len(set(args.seeds)) != len(args.seeds):
        parser.error("Seeds must be unique")
    output = args.output.expanduser().resolve()
    if output.exists():
        parser.error(f"Output already exists: {output}")
    output.mkdir(parents=True, exist_ok=False)
    for seed in args.seeds:
        room = output / "indoors" / f"dining_room_{seed}"
        exported = output / "omniverse" / f"dining_room_{seed}"
        subprocess.run([
            str(executable), "-m", "infinigen_examples.generate_indoors", "--seed", str(seed),
            "--task", "coarse", "--output_folder", str(room), "-g", "fast_solve.gin", "singleroom.gin",
            "-p", "compose_indoors.terrain_enabled=False", 'restrict_solving.restrict_parent_rooms=["DiningRoom"]',
        ], cwd=root, check=True)
        subprocess.run([
            str(executable), "-m", "infinigen.tools.export", "--input_folder", str(room),
            "--output_folder", str(exported), "-f", "usdc", "-r", "1024", "--omniverse",
        ], cwd=root, check=True)
        usd_files = list(exported.rglob("*.usdc"))
        if not usd_files:
            raise RuntimeError(f"Exporter produced no USDC files in {exported}")
        for path in usd_files:
            print(path)


if __name__ == "__main__":
    main()
