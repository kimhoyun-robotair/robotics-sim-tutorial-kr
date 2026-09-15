"""Run a genuine cuRobo checkout example with the selected Isaac Sim Python."""
import argparse
import os
from pathlib import Path

EXAMPLES = {
    'collision': ('collision_checker_example.py', []),
    'motion': ('motion_gen_reacher.py', ['--robot', 'franka.yml']),
    'ik': ('ik_reachability.py', ['--robot', 'franka.yml']),
    'mpc': ('mpc_example.py', ['--robot', 'franka.yml']),
    'multi-arm': ('multi_arm_reacher.py', ['--robot', 'dual_ur10e.yml']),
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--curobo-root', required=True, type=Path)
    parser.add_argument('--isaac-python', required=True, type=Path, help='Isaac Sim 5.1 python.sh')
    parser.add_argument('--example', choices=EXAMPLES, default='motion')
    parser.add_argument('extra', nargs=argparse.REMAINDER, help='Arguments after -- go to the upstream example')
    args = parser.parse_args()
    name, defaults = EXAMPLES[args.example]
    root = args.curobo_root.resolve()
    script = root / 'examples' / 'isaac_sim' / name
    interpreter = args.isaac_python.resolve()
    if not interpreter.is_file() or not os.access(interpreter, os.X_OK):
        parser.error(f'Not an executable Isaac Python launcher: {interpreter}')
    if not script.is_file():
        parser.error(f'This checkout does not provide {script}; see the package version notes')
    extra = args.extra[1:] if args.extra[:1] == ['--'] else args.extra
    os.chdir(root)
    os.execv(str(interpreter), [str(interpreter), str(script), *defaults, *extra])


if __name__ == '__main__':
    main()
