#!/usr/bin/env -S uv run --script
# noqa: RUF100  # noqa: SIZE_OK — one CLI owns the inseparable frozen evidence and F4 comparison boundaries.
# /// script
# requires-python = ">=3.12"
# dependencies = ["pydantic>=2.0"]
# ///

# ─── How to run ───
# 1. Install uv (if not installed):
#      curl -LsSf https://astral.sh/uv/install.sh | sh
# 2. Run directly (no venv, no pip install needed):
#      uv run audit_intermediate_evidence.py --help
# 3. Or make executable and run:
#      chmod +x audit_intermediate_evidence.py && ./audit_intermediate_evidence.py --help
# ──────────────────

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections.abc import Sequence
from dataclasses import dataclass
from fnmatch import fnmatchcase
from pathlib import Path
from typing import Final, TypeAliasType, override

from pydantic import TypeAdapter, ValidationError

JsonValue = TypeAliasType("JsonValue", None | bool | int | float | str | Sequence["JsonValue"] | dict[str, "JsonValue"])
JsonMap = TypeAliasType("JsonMap", dict[str, JsonValue])
RFC3339: Final = re.compile(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?Z$")
HANDOFF_REQUIREMENTS: Final = (
    ("10.1", "docs/intermediate/01-advanced-sdf.md"),
    ("10.2", "docs/intermediate/02-urdf-xacro-sdf.md"),
    ("10.3", "docs/intermediate/03-ros2-launch.md"),
    ("10.4", "docs/intermediate/04-spawn-model.md"),
    ("10.5", "docs/intermediate/05-bridge-yaml.md"),
    ("10.6", "docs/intermediate/06-tf-rviz.md"),
    ("10.7", "docs/intermediate/07-gz-ros2-control.md"),
    ("10.8", "docs/intermediate/08-advanced-sensors.md"),
    ("10.9", "docs/intermediate/09-multi-robot.md"),
    ("10.10", "docs/intermediate/10-nav2.md"),
    ("10.11", "docs/intermediate/project-autonomous-bot.md"),
)
COMPARE_LOGS: Final = {"nominal-diff-drive": "diff-drive.log", "nominal-sensors": "sensors.log", "nominal-ros-gz-bridge": "bridge.log"}
RUNTIME_FINGERPRINT_NORMALIZERS: Final = {
    "nominal-sensors": (
        re.compile(r"LiDAR scan verified: 360 ranges, \d+ obstacle readings\.\r?\nCamera image verified: 320x240\."),
        "LiDAR scan verified: 360 ranges; Camera image verified: 320x240.",
    ),
    "nominal-ros-gz-bridge": (
        re.compile(r"ROS cmd_vel to Gazebo verified: odom x=-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?, linear\.x=-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?\.\r?\nGazebo sensors to ROS verified: scan=\d+, image=320x240, IMU and clock received\."),
        "ROS cmd_vel to Gazebo verified; Gazebo sensors to ROS verified.",
    ),
}
ARTIFACT_EVIDENCE_PREFIX: Final = ".omo/evidence/intermediate/"


JSON_ADAPTER: Final[TypeAdapter[JsonValue]] = TypeAdapter(JsonValue)


class Args(argparse.Namespace):
    plan: str | None = None
    evidence: str | None = None
    handoff: str | None = None
    expected_task_receipts: int | None = None
    compare_baseline: str | None = None
    current: str | None = None
    allowed_paths: str | None = None
    json: str = ""


@dataclass(frozen=True, slots=True)
class AuditFailure(Exception):
    path: Path
    reason: str

    @override
    def __str__(self) -> str:
        return f"{self.path}: {self.reason}"


def load_json(path: Path) -> JsonValue:
    try:
        value = JSON_ADAPTER.validate_json(path.read_bytes())
    except OSError as error:
        raise AuditFailure(path, str(error)) from error
    except ValidationError as error:
        raise AuditFailure(path, f"invalid JSON/schema: {error.title}") from error
    return value


def mapping(value: JsonValue, label: str) -> JsonMap:
    if not isinstance(value, dict):
        raise AuditFailure(Path(label), "expected JSON object")
    return value


def sequence(value: JsonValue, label: str) -> list[JsonValue]:
    if not isinstance(value, list):
        raise AuditFailure(Path(label), "expected JSON array")
    return value


def text_field(data: JsonMap, key: str, label: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise AuditFailure(Path(label), f"{key} must be a nonempty string")
    return value


def hash_field(data: JsonMap, key: str, label: str) -> str:
    value = text_field(data, key, label)
    if re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise AuditFailure(Path(label), f"{key} must be lowercase SHA-256")
    return value


def resolve_artifact(evidence: Path, recorded: str) -> Path:
    recorded_path = Path(recorded)
    if recorded_path.is_absolute():
        raise AuditFailure(recorded_path, "artifact path must be relative to .omo/evidence/intermediate")
    if not recorded.startswith(ARTIFACT_EVIDENCE_PREFIX):
        raise AuditFailure(recorded_path, "artifact path must be a canonical .omo/evidence/intermediate path")
    relative = Path(recorded.removeprefix(ARTIFACT_EVIDENCE_PREFIX))
    if ".." in relative.parts:
        raise AuditFailure(recorded_path, "artifact path must not contain traversal segments")
    if not relative.parts or recorded != ARTIFACT_EVIDENCE_PREFIX + relative.as_posix():
        raise AuditFailure(recorded_path, "artifact path must be a canonical .omo/evidence/intermediate path")
    root = evidence.resolve()
    resolved = (root / relative).resolve()
    try:
        _ = resolved.relative_to(root)
    except ValueError as error:
        raise AuditFailure(recorded_path, "artifact path resolves outside supplied evidence root") from error
    return resolved


def patterns_match(path: str, patterns: list[str]) -> bool:
    for pattern in patterns:
        if "{" in pattern and "}" in pattern:
            left, remainder = pattern.split("{", 1)
            choices, right = remainder.split("}", 1)
            if any(fnmatchcase(path, left + choice + right) for choice in choices.split(",")):
                return True
        elif fnmatchcase(path, pattern.split("#", 1)[0]):
            return True
    return False


def validate_snapshot(path: Path, receipt: JsonMap, baseline_paths: set[str]) -> tuple[list[str], JsonMap]:
    raw = path.read_bytes()
    data = mapping(load_json(path), str(path))
    canonical = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    if raw not in (canonical, canonical + b"\n"):
        raise AuditFailure(path, "snapshot is not canonical compact sorted-key JSON")
    if hashlib.sha256(raw).hexdigest() != hash_field(receipt, "snapshot_sha256", str(path)):
        raise AuditFailure(path, "snapshot digest mismatch")
    if data.get("schema_version") != 1 or data.get("plan_sha256") != receipt.get("plan_sha256"):
        raise AuditFailure(path, "snapshot schema/plan binding mismatch")
    if not {"git_head", "git_status_porcelain_v2", "install_tree_sha256", "created_utc"}.issubset(data):
        raise AuditFailure(path, "snapshot required keys missing")
    allowed = [text_field(mapping({"v": item}, str(path)), "v", str(path)) for item in sequence(data.get("allowed_paths"), str(path))]
    if allowed != sorted(allowed):
        raise AuditFailure(path, "allowed_paths must be sorted")
    if not isinstance(status := data.get("git_status_porcelain_v2"), str):
        raise AuditFailure(path, "git_status_porcelain_v2 must be a string")
    dirty_paths = {line.split()[-1] for line in status.splitlines() if line.split()}
    file_paths: list[str] = []
    for item in sequence(data.get("files"), str(path)):
        entry = mapping(item, str(path))
        recorded = text_field(entry, "path", str(path))
        _ = hash_field(entry, "sha256", str(path))
        if recorded not in baseline_paths and recorded not in dirty_paths and not patterns_match(recorded, allowed):
            raise AuditFailure(path, f"snapshot path outside allowed paths: {recorded}")
        file_paths.append(recorded)
    if file_paths != sorted(file_paths) or len(file_paths) != len(set(file_paths)):
        raise AuditFailure(path, "snapshot files must be sorted and unique")
    return file_paths, data


def validate_subcheck(value: JsonValue, label: str, evidence: Path) -> tuple[str, list[str]]:
    subcheck = mapping(value, label)
    subcheck_id = text_field(subcheck, "id", label)
    command = mapping(subcheck.get("command"), label)
    argv = sequence(command.get("argv"), label)
    if not argv or not all(isinstance(arg, str) and arg for arg in argv):
        raise AuditFailure(Path(label), "command.argv must contain strings")
    for key in ("exit", "expected_exit"):
        if type(command.get(key)) is not int:
            raise AuditFailure(Path(label), f"{key} must be an integer")
    if command.get("passed") is not True or command.get("exit") != command.get("expected_exit"):
        raise AuditFailure(Path(label), "command semantic success mismatch")
    start = command.get("started_utc", command.get("start"))
    end = command.get("ended_utc", command.get("end"))
    if not isinstance(start, str) or not isinstance(end, str) or RFC3339.fullmatch(start) is None or RFC3339.fullmatch(end) is None:
        raise AuditFailure(Path(label), "command timestamps must be RFC3339 UTC")
    environment = mapping(subcheck.get("environment"), label)
    for key in ("os", "ros", "gazebo", "ros_domain_id", "gz_partition", "temp_root"):
        if not isinstance(environment.get(key), str):
            raise AuditFailure(Path(label), f"environment.{key} must be a string")
    temp_root = environment.get("temp_root")
    if not isinstance(temp_root, str) or re.fullmatch(r"/tmp/[^/]+\.[A-Za-z0-9]{6,}", temp_root) is None:
        raise AuditFailure(Path(label), "environment.temp_root must record an exact fresh mktemp path")
    cleanup = mapping(subcheck.get("cleanup"), label)
    if len(cleanup) < 2 or any(value is not True for value in cleanup.values()):
        raise AuditFailure(Path(label), "cleanup booleans must be complete and true")
    if not isinstance(subcheck.get("pids"), list) or not all(type(pid) is int for pid in sequence(subcheck.get("pids"), label)):
        raise AuditFailure(Path(label), "pids must be integers")
    artifacts = sequence(subcheck.get("artifacts"), label)
    if not artifacts:
        raise AuditFailure(Path(label), "artifacts must be nonempty")
    for item in artifacts:
        artifact = mapping(item, label)
        recorded = text_field(artifact, "path", label)
        expected = hash_field(artifact, "sha256", label)
        actual_path = resolve_artifact(evidence, recorded)
        if not actual_path.is_file() or actual_path.stat().st_size == 0:
            raise AuditFailure(actual_path, "artifact missing or empty")
        if hashlib.sha256(actual_path.read_bytes()).hexdigest() != expected:
            raise AuditFailure(actual_path, "artifact hash mismatch")
    allocations = [f"{environment['ros_domain_id']}|{environment['gz_partition']}|{temp_root}"]
    return subcheck_id, allocations


def validate_receipt(path: Path, evidence: Path, expected_task: str, baseline_paths: set[str]) -> tuple[str, list[str], list[str], str]:
    receipt = mapping(load_json(path), str(path))
    if receipt.get("schema_version") != 1 or receipt.get("task") != expected_task:
        raise AuditFailure(path, "receipt schema/task mismatch")
    plan_sha256 = hash_field(receipt, "plan_sha256", str(path))
    worker = mapping(receipt.get("worker"), str(path))
    identity = "|".join(text_field(worker, key, str(path)) for key in ("agent", "process", "thread", "session"))
    file_paths, _snapshot = validate_snapshot(path.with_name("snapshot.json"), receipt, baseline_paths)
    runs = sequence(receipt.get("runs"), str(path))
    if len(runs) != 2:
        raise AuditFailure(path, "runs must contain exactly nominal and fault")
    run_ids: list[str] = []
    subcheck_ids: list[str] = []
    allocations: list[str] = []
    for value in runs:
        run = mapping(value, str(path))
        run_ids.append(text_field(run, "run_id", str(path)))
        subs = sequence(run.get("subchecks"), str(path))
        if not subs:
            raise AuditFailure(path, "run subchecks must be nonempty")
        validated = [validate_subcheck(item, str(path), evidence) for item in subs]
        subcheck_ids.extend(item[0] for item in validated)
        allocations.extend(token for item in validated for token in item[1])
    if set(run_ids) != {"nominal", "fault"} or len(subcheck_ids) != len(set(subcheck_ids)):
        raise AuditFailure(path, "run/subcheck identifiers must be unique")
    return identity, file_paths, allocations, plan_sha256


def evidence_audit(args: Args) -> JsonMap:
    if None in (args.plan, args.evidence, args.handoff, args.expected_task_receipts):
        raise AuditFailure(Path(args.json), "evidence mode arguments are incomplete")
    assert args.plan is not None and args.evidence is not None and args.handoff is not None and args.expected_task_receipts is not None
    evidence = Path(args.evidence)
    plan_bytes = Path(args.plan).read_bytes()
    if not plan_bytes:
        raise AuditFailure(Path(args.plan), "plan is empty")
    plan_sha256 = hashlib.sha256(plan_bytes).hexdigest()
    baseline_paths = {text_field(mapping(item, "baseline.json"), "path", "baseline.json") for item in sequence(mapping(load_json(evidence / "task-1/baseline.json"), "baseline.json").get("pre_edit_files"), "baseline.json")}
    identities: list[str] = []
    allocations: list[str] = []
    receipt_plan_sha256s: set[str] = set()
    mapped_files: set[str] = set()
    latest_files: list[str] = []
    for number in range(1, args.expected_task_receipts + 1):
        identity, latest_files, allocated, receipt_plan_sha256 = validate_receipt(evidence / f"task-{number}/receipt.json", evidence, f"task-{number}", baseline_paths)
        identities.append(identity)
        allocations.extend(allocated)
        receipt_plan_sha256s.add(receipt_plan_sha256)
        mapped_files.update(latest_files)
    if len(list(evidence.glob("task-*/receipt.json"))) != args.expected_task_receipts:
        raise AuditFailure(evidence, "task receipt count mismatch")
    for value in sequence(mapping(load_json(evidence / f"task-{args.expected_task_receipts}/snapshot.json"), "latest snapshot").get("files"), "latest snapshot"):
        entry = mapping(value, "latest snapshot")
        current = Path(text_field(entry, "path", "latest snapshot"))
        if not current.is_file() or hashlib.sha256(current.read_bytes()).hexdigest() != hash_field(entry, "sha256", "latest snapshot"):
            raise AuditFailure(current, "current file hash mismatch")
    if len(identities) != len(set(identities)):
        raise AuditFailure(evidence, "worker identity collision")
    if len(allocations) != len(set(allocations)):
        raise AuditFailure(evidence, "environment allocation collision")
    if plan_sha256 not in receipt_plan_sha256s:
        raise AuditFailure(Path(args.plan), "plan digest is not bound by any receipt/snapshot")
    handoff_text = Path(args.handoff).read_text(encoding="utf-8")
    coverage: list[str] = []
    for requirement, artifact in HANDOFF_REQUIREMENTS:
        if re.search(rf"^## {re.escape(requirement)}(?:\s|$)", handoff_text, re.MULTILINE) is None:
            raise AuditFailure(Path(args.handoff), f"Handoff {requirement} requirement mapping missing")
        if not Path(artifact).is_file() or (args.expected_task_receipts >= 9 and artifact not in mapped_files):
            raise AuditFailure(Path(artifact), f"Handoff {requirement} artifact mapping missing")
        coverage.append(requirement)
    return {"passed": True, "mode": "evidence", "task_receipts": args.expected_task_receipts, "identities": identities, "requirement_coverage": coverage, "errors": []}


def compare_audit(args: Args) -> JsonMap:
    if None in (args.compare_baseline, args.current, args.allowed_paths):
        raise AuditFailure(Path(args.json), "compare mode requires --compare-baseline, --current, and --allowed-paths")
    assert args.compare_baseline is not None and args.current is not None and args.allowed_paths is not None
    baseline = mapping(load_json(Path(args.compare_baseline)), str(args.compare_baseline))
    manifest = [line.strip() for line in Path(args.allowed_paths).read_text(encoding="utf-8").splitlines() if line.strip()]
    if manifest != [item for item in sequence(baseline.get("allowed_paths"), str(args.compare_baseline)) if isinstance(item, str)]:
        raise AuditFailure(Path(args.allowed_paths), "allowed-path manifest differs from baseline")
    current = Path(args.current)
    if not current.is_dir():
        raise AuditFailure(current, "current must be a directory")
    files = [path for path in current.rglob("*") if path.is_file()]
    for item in sequence(baseline.get("checks"), str(args.compare_baseline)):
        check = mapping(item, str(args.compare_baseline))
        check_id = text_field(check, "id", str(args.compare_baseline))
        log = current / COMPARE_LOGS[check_id] if check_id in COMPARE_LOGS else None
        if log is not None and log.is_file() and (normalizer := RUNTIME_FINGERPRINT_NORMALIZERS.get(check_id)) is not None:
            log_text = normalizer[0].sub(normalizer[1], log.read_text(encoding="utf-8"))
        elif log is not None and log.is_file():
            log_text = log.read_text(encoding="utf-8")
        else:
            log_text = ""
        if log is not None and (not log.is_file() or text_field(check, "fingerprint", str(args.compare_baseline)) not in log_text):
            raise AuditFailure(log, f"baseline fingerprint mismatch: {check_id}")
    for path in files:
        relative = path.relative_to(current).as_posix()
        if relative not in COMPARE_LOGS.values() and not patterns_match(relative, manifest):
            raise AuditFailure(path, f"forbidden path: {relative}")
        if path.stat().st_size == 0:
            raise AuditFailure(path, "current artifact is empty")
    return {"passed": True, "mode": "compare-baseline", "checked_files": sorted(path.relative_to(current).as_posix() for path in files), "errors": []}


def parse_args() -> Args:
    parser = argparse.ArgumentParser(description="Audit intermediate-stage evidence without executing evidence text.")
    for name in ("--plan", "--evidence", "--handoff", "--compare-baseline", "--current", "--allowed-paths", "--json"):
        _ = parser.add_argument(name, required=name == "--json")
    _ = parser.add_argument("--expected-task-receipts", type=int)
    args = Args()
    _ = parser.parse_args(namespace=args)
    return args


def main() -> int:
    args = parse_args()
    output = Path(args.json)
    try:
        if args.compare_baseline is not None or args.current is not None or args.allowed_paths is not None:
            result = compare_audit(args)
        else:
            if args.expected_task_receipts not in (9, 10):
                raise AuditFailure(output, "expected task receipt count must be 9 or 10")
            result = evidence_audit(args)
    except (AuditFailure, OSError) as error:
        result = {"passed": False, "mode": "audit", "errors": [str(error)]}
    output.parent.mkdir(parents=True, exist_ok=True)
    _ = output.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["passed"] is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
