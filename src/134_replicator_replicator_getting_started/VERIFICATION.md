# Verification scope

- All local Python source parsed with ast.parse (no Isaac Sim imports).
- python3 run.py --help: exit 0.
- All local JSON files parsed with json.loads.
- Manifest entrypoint and listed artifact paths exist.

GPU/Kit, GUI interactions, physical robot execution and generated annotation content were not run by this package author. `tutorial.json` therefore retains `verification: "not_run"`. Root-level runtime evidence, if collected, must identify its actual command, output path and limitation.
