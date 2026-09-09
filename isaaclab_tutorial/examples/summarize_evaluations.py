#!/usr/bin/env python3
"""Compare paired Cartpole evaluation JSONs; no simulator dependency.

Metrics are episode means (each seed has equal weight), with paired changes
computed as candidate minus reference. Short failed episodes can have small
error/effort values: always interpret these alongside duration and termination.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
from pathlib import Path
import statistics
import tempfile

SCHEMA = "isaaclab-cartpole-evaluation-v1"
METRICS = (
    "duration_s", "pole_angle_rms_rad", "cart_position_rms_m",
    "cart_travel_m", "command_force_rms_n", "action_change_rms",
)


def write_json_atomic(path, data):
    """Publish a complete strict JSON file, never a partially written result."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(data, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def validate_report(report):
    """Reject interrupted runs, duplicate seeds, non-finite data and bad flags."""
    if report.get("schema") != SCHEMA or report.get("status") != "complete":
        raise ValueError("Only complete evaluation-v1 reports may be compared.")
    episodes = report.get("episodes", [])
    if not episodes or len(episodes) != report.get("requested_episodes"):
        raise ValueError("Episode count is empty or does not match requested_episodes.")
    seeds = set()
    for episode in episodes:
        seed = episode["seed"]
        if type(seed) is not int or seed in seeds:
            raise ValueError("Every episode must have one unique integer seed.")
        seeds.add(seed)
        if type(episode["terminated"]) is not bool or type(episode["truncated"]) is not bool:
            raise ValueError("terminated and truncated must be booleans.")
        if not (episode["terminated"] or episode["truncated"]):
            raise ValueError("Every episode must reach a genuine task boundary.")
        if type(episode["steps"]) is not int or episode["steps"] <= 0:
            raise ValueError("steps must be a positive integer.")
        values = [episode[key] for key in METRICS] + list(episode["initial_state"].values())
        if not values or not all(type(value) in (int, float) and math.isfinite(value) for value in values):
            raise ValueError("Non-finite or non-numeric episode metric/state.")
        if any(episode[key] < 0 for key in METRICS):
            raise ValueError("RMS, duration and path length must be non-negative.")
    return {episode["seed"]: episode for episode in episodes}


def describe(values):
    return {
        "mean": statistics.mean(values),
        "sample_std": statistics.stdev(values) if len(values) > 1 else None,
        "min": min(values),
        "max": max(values),
    }


def compare_reports(reference, candidate):
    left, right = validate_report(reference), validate_report(candidate)
    if reference["protocol"] != candidate["protocol"]:
        raise ValueError("Evaluation protocols differ; re-evaluate with identical software/settings.")
    if left.keys() != right.keys():
        raise ValueError("Seed sets differ; paired evaluation requires identical seeds.")
    for seed in left:
        a, b = left[seed]["initial_state"], right[seed]["initial_state"]
        if a.keys() != b.keys() or not a:
            raise ValueError(f"Initial state fields differ for seed {seed}.")
        if any(not math.isclose(a[key], b[key], rel_tol=0.0, abs_tol=1e-6) for key in a):
            raise ValueError(f"Initial states differ for seed {seed}; this is not a paired comparison.")
    result = {
        "schema": "isaaclab-cartpole-comparison-v1",
        "reference": reference["label"], "candidate": candidate["label"],
        "checkpoint_hashes": {
            "reference": reference.get("checkpoint_sha256"),
            "candidate": candidate.get("checkpoint_sha256"),
        },
        "episode_count": len(left), "seeds": sorted(left),
        "protocol": reference["protocol"], "metrics": {},
        "interpretation": "candidate minus reference; duration is higher-is-better. Other metrics need termination context.",
        "limitations": "Paired evaluation seeds do not replace independent training seeds or prove hardware determinism.",
    }
    for metric in METRICS:
        result["metrics"][metric] = {
            "reference": describe([episode[metric] for episode in left.values()]),
            "candidate": describe([episode[metric] for episode in right.values()]),
            "paired_delta": describe([right[seed][metric] - left[seed][metric] for seed in sorted(left)]),
        }
    result["outcomes"] = {}
    for label, episodes in (("reference", left), ("candidate", right)):
        result["outcomes"][label] = {
            "terminated": sum(item["terminated"] for item in episodes.values()),
            "truncated_without_termination": sum(item["truncated"] and not item["terminated"] for item in episodes.values()),
            "both_flags": sum(item["truncated"] and item["terminated"] for item in episodes.values()),
        }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--csv-output", type=Path)
    args = parser.parse_args()
    if args.output.resolve() in {args.reference.resolve(), args.candidate.resolve()}:
        parser.error("Output must not overwrite an evaluation input.")
    if args.csv_output and args.csv_output.resolve() in {
        args.reference.resolve(), args.candidate.resolve(), args.output.resolve()
    }:
        parser.error("CSV path must differ from JSON inputs and output.")
    reference = json.loads(args.reference.read_text(encoding="utf-8"))
    candidate = json.loads(args.candidate.read_text(encoding="utf-8"))
    result = compare_reports(reference, candidate)
    write_json_atomic(args.output, result)
    if args.csv_output:
        args.csv_output.parent.mkdir(parents=True, exist_ok=True)
        with args.csv_output.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(["metric", "reference_mean", "candidate_mean", "paired_delta_mean", "paired_delta_sample_std"])
            for metric, values in result["metrics"].items():
                writer.writerow([metric, values["reference"]["mean"], values["candidate"]["mean"],
                                 values["paired_delta"]["mean"], values["paired_delta"]["sample_std"]])
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
