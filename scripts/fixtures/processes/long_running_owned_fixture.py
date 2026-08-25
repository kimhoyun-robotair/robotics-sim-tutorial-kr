from __future__ import annotations

import signal
import sys
import time
from pathlib import Path
from types import FrameType

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scripts.fixtures.processes._fixture_support import spawn_registered_sentinel  # noqa: E402


def exit_for_sigint(_signal_number: int, _frame: FrameType | None) -> None:
    raise SystemExit(130)


spawn_registered_sentinel()
signal.signal(signal.SIGINT, exit_for_sigint)
while True:
    time.sleep(1)
