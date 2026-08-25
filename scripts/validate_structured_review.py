from __future__ import annotations

import argparse
import json
from pathlib import Path

import jsonschema


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--schema", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--expect-verdict", default="APPROVE")
    parser.add_argument("--expect-base")
    parser.add_argument("--expect-final")
    parser.add_argument("--expect-routes", type=int)
    parser.add_argument(
        "--expect-all-verdicts", choices=("APPROVE", "REQUEST_CHANGES")
    )
    args = parser.parse_args()
    try:
        schema = json.loads(Path(args.schema).read_text(encoding="utf-8"))
        value = json.loads(Path(args.input).read_text(encoding="utf-8"))
        jsonschema.validate(value, schema)
    except (OSError, json.JSONDecodeError, jsonschema.ValidationError) as error:
        print(f"structured review rejected: {error}")
        return 1
    if value.get("verdict") == "APPROVE" and value.get("findings"):
        print("structured review rejected: APPROVE requires zero findings")
        return 1
    if args.expect_base and value.get("base_sha") != args.expect_base:
        return 1
    if args.expect_final and value.get("final_sha") != args.expect_final:
        return 1
    if value.get("verdict") != args.expect_verdict:
        return 1
    if args.expect_routes is not None:
        reviews = value.get("route_reviews")
        if not isinstance(reviews, list) or len(reviews) != args.expect_routes:
            return 1
        if any(not isinstance(review, dict) for review in reviews):
            return 1
        route_names = [str(review.get("route")) for review in reviews]
        if len(route_names) != len(set(route_names)):
            return 1
        route_verdict = args.expect_all_verdicts or args.expect_verdict
        if any(review.get("verdict") != route_verdict for review in reviews):
            return 1
        approval_fields = (
            "progression_clear",
            "korean_readable",
            "advanced_scope_safe",
            "copyright_safe_assets",
        )
        if route_verdict == "APPROVE" and any(
            review.get(field) is not True
            for review in reviews
            for field in approval_fields
        ):
            return 1
    print("structured review accepted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
