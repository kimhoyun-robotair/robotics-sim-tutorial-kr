#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import time
from pathlib import Path
from typing import Final


POLL_SECONDS: Final = 0.02


def parse_signal_after(raw: str | None) -> tuple[float, signal.Signals] | None:
    if raw is None:
        return None
    try:
        seconds_raw, signal_raw = raw.split(":", 1)
        seconds = float(seconds_raw)
        selected = signal.Signals[f"SIG{signal_raw.upper().removeprefix('SIG')}"]
    except (KeyError, ValueError) as error:
        raise argparse.ArgumentTypeError("--signal-after must be SECONDS:SIGNAL") from error
    if seconds <= 0:
        raise argparse.ArgumentTypeError("--signal-after seconds must be positive")
    return seconds, selected


def process_start_ticks(pid: int) -> int | None:
    try:
        return int(Path(f"/proc/{pid}/stat").read_text(encoding="utf-8").split()[21])
    except (FileNotFoundError, IndexError, PermissionError, ValueError):
        return None


def group_members(pgid: int) -> list[int]:
    members: list[int] = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            fields = (entry / "stat").read_text(encoding="utf-8").split()
            if int(fields[4]) == pgid:
                members.append(int(entry.name))
        except (FileNotFoundError, IndexError, PermissionError, ValueError):
            continue
    return sorted(members)


def signal_group(pgid: int, selected: signal.Signals) -> bool:
    try:
        os.killpg(pgid, selected)
    except ProcessLookupError:
        return False
    return True


def wait_group_empty(pgid: int, seconds: float) -> list[int]:
    deadline = time.monotonic() + seconds
    survivors = group_members(pgid)
    while survivors and time.monotonic() < deadline:
        time.sleep(POLL_SECONDS)
        survivors = group_members(pgid)
    return survivors


def stop_group(pgid: int) -> list[int]:
    if group_members(pgid):
        signal_group(pgid, signal.SIGTERM)
    survivors = wait_group_empty(pgid, 2.0)
    if survivors:
        signal_group(pgid, signal.SIGKILL)
        survivors = wait_group_empty(pgid, 2.0)
    return survivors


def read_registration(path: Path) -> tuple[int, int] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return int(data["pid"]), int(data["start_ticks"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None


def reap_sentinel(registration: tuple[int, int] | None) -> tuple[bool, bool, bool, list[int]]:
    if registration is None:
        return False, False, False, []
    pid, expected_ticks = registration
    actual_ticks = process_start_ticks(pid)
    stale_identity = actual_ticks is not None and actual_ticks != expected_ticks
    survived = actual_ticks is not None
    if stale_identity:
        deadline = time.monotonic() + 2.0
        while process_start_ticks(pid) is not None and time.monotonic() < deadline:
            time.sleep(POLL_SECONDS)
        remaining = [pid] if process_start_ticks(pid) is not None else []
        return survived, not remaining, True, remaining
    if actual_ticks == expected_ticks:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        deadline = time.monotonic() + 2.0
        while process_start_ticks(pid) == expected_ticks and time.monotonic() < deadline:
            time.sleep(POLL_SECONDS)
        if process_start_ticks(pid) == expected_ticks:
            os.kill(pid, signal.SIGKILL)
    remaining = [pid] if process_start_ticks(pid) == expected_ticks else []
    return survived, not remaining, stale_identity, remaining


def normalize_exit(returncode: int) -> int:
    return 128 + abs(returncode) if returncode < 0 else returncode


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    result.add_argument("--timeout", required=True, type=float)
    result.add_argument("--signal-after")
    result.add_argument("--cleanup-receipt", required=True)
    result.add_argument("command", nargs=argparse.REMAINDER)
    return result


def main() -> int:
    args = parser().parse_args()
    command = list(args.command)
    if command[:1] == ["--"]:
        command = command[1:]
    if not command or args.timeout <= 0:
        parser().error("a command and positive --timeout are required")
    signal_plan = parse_signal_after(args.signal_after)
    receipt_path = Path(args.cleanup_receipt)
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    registration_path = receipt_path.with_name(f".{receipt_path.name}.sentinel")
    environment = os.environ.copy()
    environment["OWNED_PROCESS_SENTINEL_REGISTRATION"] = str(registration_path)
    started = time.monotonic()
    process = subprocess.Popen(command, start_new_session=True, env=environment)
    termination_reason = "completed"
    signal_sent: str | None = None
    signal_deadline = started + signal_plan[0] if signal_plan else None
    while process.poll() is None:
        now = time.monotonic()
        if signal_plan and signal_deadline is not None and now >= signal_deadline:
            signal_sent = signal_plan[1].name
            signal_group(process.pid, signal_plan[1])
            termination_reason = "signal"
            signal_plan = None
        elif now - started >= args.timeout:
            signal_sent = signal.SIGTERM.name
            signal_group(process.pid, signal.SIGTERM)
            termination_reason = "timeout"
            break
        time.sleep(POLL_SECONDS)
    if termination_reason == "timeout":
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            signal_group(process.pid, signal.SIGKILL)
            process.wait(timeout=2)
        dut_exit = 124
    else:
        dut_exit = normalize_exit(process.wait())
    group_survivors = stop_group(process.pid)
    registration = read_registration(registration_path)
    sentinel_survived, sentinel_reaped, stale_identity, sentinel_survivors = reap_sentinel(registration)
    registration_path.unlink(missing_ok=True)
    receipt = {
        "schema_version": 1,
        "command": command,
        "dut_pid": process.pid,
        "dut_pgid": process.pid,
        "dut_exit": dut_exit,
        "wrapper_exit": 0,
        "termination_reason": termination_reason,
        "signal_sent": signal_sent,
        "stale_identity": stale_identity,
        "sentinel_survived_dut_teardown": sentinel_survived,
        "sentinel_reaped": sentinel_reaped,
        "survivors": sorted(set(group_survivors + sentinel_survivors)),
        "elapsed_seconds": round(time.monotonic() - started, 3),
    }
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
