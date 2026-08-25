from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def spawn_registered_sentinel(*, stale_identity: bool = False) -> subprocess.Popen[bytes]:
    lifetime = "0.5" if stale_identity else "60"
    sentinel = subprocess.Popen(
        [
            sys.executable,
            "-c",
            f"import signal,time; signal.signal(signal.SIGTERM, lambda *_: exit(0)); time.sleep({lifetime})",
        ],
        start_new_session=True,
    )
    registration = os.environ.get("OWNED_PROCESS_SENTINEL_REGISTRATION")
    if registration is not None:
        start_ticks = _start_ticks(sentinel.pid)
        if stale_identity:
            start_ticks += 1
        Path(registration).write_text(
            json.dumps({"pid": sentinel.pid, "start_ticks": start_ticks}) + "\n", encoding="utf-8"
        )
    return sentinel


def _start_ticks(pid: int) -> int:
    fields = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8").split()
    return int(fields[21])
