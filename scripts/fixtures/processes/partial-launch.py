from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scripts.fixtures.processes._fixture_support import spawn_registered_sentinel  # noqa: E402


parser = argparse.ArgumentParser()
parser.add_argument("--fail-after-spawn", action="store_true")
args = parser.parse_args()
spawn_registered_sentinel()
raise SystemExit(1 if args.fail_after_spawn else 0)
