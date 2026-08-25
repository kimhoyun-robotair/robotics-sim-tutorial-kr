#!/usr/bin/env python3
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
    if args.expect_routes is not None:
        reviews = value.get("route_reviews")
        if not isinstance(reviews, list) or len(reviews) != args.expect_routes:
            return 1
        if any(review.get("verdict") != args.expect_verdict for review in reviews if isinstance(review, dict)):
            return 1
    elif value.get("verdict") != args.expect_verdict:
        return 1
    print("structured review accepted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
