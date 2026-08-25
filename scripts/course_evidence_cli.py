from __future__ import annotations

import argparse


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    result.add_argument("--evidence-index", required=True)
    for option in (
        "--evidence-root",
        "--manifest",
        "--source-sha",
        "--source-tree-digest",
        "--fixture",
        "--output",
    ):
        result.add_argument(option)
    result.add_argument("--bind-task-commit", type=int)
    result.add_argument("--commit")
    result.add_argument("--attempt-dir")
    result.add_argument("--print-task-baseline-sha", type=int)
    result.add_argument("--plan")
    result.add_argument("--require-tasks")
    result.add_argument("--require-modes")
    result.add_argument("--require-cleanup-for-process-scenarios", action="store_true")
    result.add_argument("--require-tdd-task", action="append")
    return result
