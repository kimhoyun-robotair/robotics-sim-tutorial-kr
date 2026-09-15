#!/usr/bin/env python3
"""Isaac Sim 설치 없이 공식 5.1 튜토리얼을 찾고 패키지 연결을 검사한다."""

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
MODES = {"standalone", "gui", "script_editor", "extension", "ros2", "external"}


def read_inventory(root: Path = ROOT) -> dict[str, Any]:
    """공식 목차와 패키지의 고정된 대응표를 읽는다."""
    with (root / "official_tutorials.json").open(encoding="utf-8") as stream:
        return json.load(stream)


def package_path(root: Path, relative: str) -> Path:
    path = Path(relative)
    if path.is_absolute() or len(path.parts) != 2 or path.parts[0] != "src":
        raise ValueError(f"패키지 경로는 src/<폴더>여야 합니다: {relative}")
    if path.parts[1] in {".", ".."}:
        raise ValueError(f"잘못된 패키지 경로: {relative}")
    return root / path.parts[1]


def local_file(package: Path, relative: str) -> Path:
    path = Path(relative)
    if path.is_absolute() or not relative or ".." in path.parts:
        raise ValueError(f"패키지 내부 상대 경로가 필요합니다: {relative}")
    result = package / path
    if not result.resolve().is_relative_to(package.resolve()):
        raise ValueError(f"패키지 밖을 가리킵니다: {relative}")
    return result


def check_catalog(root: Path = ROOT) -> list[str]:
    """색인 누락, 중복, 잘못된 출처와 패키지 밖 의존 경로를 보고한다."""
    errors = []
    try:
        inventory = read_inventory(root)
    except (OSError, ValueError) as exc:
        return [f"공식 색인을 읽을 수 없습니다: {exc}"]
    rows = inventory.get("tutorials", [])
    if not rows:
        return ["공식 색인에 튜토리얼이 없습니다."]
    for key in ("id", "package", "source_url"):
        values = [row.get(key) for row in rows]
        if len(values) != len(set(values)):
            errors.append(f"공식 색인에 중복된 {key}가 있습니다.")
    orders = [row.get("learning_order") for row in rows]
    if not all(type(order) is int for order in orders) or sorted(orders) != list(range(len(rows))):
        errors.append("학습 순서는 0부터 누락·중복 없이 이어져야 합니다.")
    stages = inventory.get("learning_stages", [])
    stage_keys = {stage["key"] for stage in stages}
    if len(stage_keys) != len(stages):
        errors.append("학습 단계의 key가 중복됩니다.")
    expected = set()
    for row in rows:
        label = row.get("id", "unknown")
        try:
            package = package_path(root, row["package"])
            expected.add(package.name)
            metadata = json.loads((package / "tutorial.json").read_text(encoding="utf-8"))
            for key in ("id", "category", "source_url", "learning_order", "learning_stage"):
                if metadata.get(key) != row[key]:
                    errors.append(f"{label}: tutorial.json의 {key}가 공식 색인과 다릅니다.")
            order = row["learning_order"]
            if type(order) is not int or not package.name.startswith(f"{order:02d}_"):
                errors.append(f"{label}: 폴더 이름의 번호가 학습 순서와 다릅니다.")
            if row["learning_stage"] not in stage_keys:
                errors.append(f"{label}: 알 수 없는 학습 단계입니다.")
            if metadata.get("mode") not in MODES:
                errors.append(f"{label}: 알 수 없는 실행 방식 {metadata.get('mode')!r}")
            if not metadata.get("requirements"):
                errors.append(f"{label}: requirements가 비어 있습니다.")
            if not metadata.get("verification"):
                errors.append(f"{label}: verification이 없습니다.")
            guide = (package / "TUTORIAL.md").read_text(encoding="utf-8")
            if row["source_url"] not in guide:
                errors.append(f"{label}: 안내서에 해당 공식 출처가 없습니다.")
            artifacts = metadata.get("artifacts", [])
            if not isinstance(artifacts, list) or not artifacts:
                errors.append(f"{label}: artifacts 목록이 없습니다.")
                artifacts = []
            entrypoint = metadata.get("entrypoint")
            if entrypoint is None and metadata.get("mode") != "gui":
                errors.append(f"{label}: GUI 이외 패키지에는 entrypoint가 필요합니다.")
            for relative in artifacts + ([entrypoint] if entrypoint else []):
                if not isinstance(relative, str) or not local_file(package, relative).is_file():
                    errors.append(f"{label}: 실습 파일이 없습니다: {relative}")
        except (OSError, ValueError, KeyError, TypeError) as exc:
            errors.append(f"{label}: {exc}")
    actual = {p.parent.name for p in root.glob("*/tutorial.json")}
    for name in sorted(actual - expected):
        errors.append(f"공식 색인에서 빠진 패키지: {name}")
    for stage in stages:
        members = sorted(
            (row for row in rows if row.get("learning_stage") == stage["key"]),
            key=lambda row: row["learning_order"] if type(row.get("learning_order")) is int else -1,
        )
        if [row["id"] for row in members] != stage.get("tutorial_ids"):
            errors.append(f"{stage['key']}: 학습 단계의 튜토리얼 순서가 색인과 다릅니다.")
    mapped = {r["source_path"] for r in inventory.get("navigation_audit", []) if r["disposition"] == "package"}
    if mapped != {r["source_path"] for r in rows}:
        errors.append("공식 목차 감사와 튜토리얼 출처 목록이 다릅니다.")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    listing = commands.add_parser("list", help="번호·분야·실행 방식·제목으로 검색")
    listing.add_argument("--category")
    listing.add_argument("--stage", help="학습 단계 key로 필터링 (INDEX.md 참조)")
    listing.add_argument("--mode", choices=sorted(MODES))
    listing.add_argument("--search", default="")
    show = commands.add_parser("show", help="한 패키지의 한국어 실습 안내 출력")
    show.add_argument("tutorial", help="00 같은 학습 번호, t001 같은 출처 ID 또는 패키지 폴더 이름")
    commands.add_parser("check", help="공식 목차와 로컬 패키지의 완전성 검사")
    args = parser.parse_args()
    if args.command == "check":
        errors = check_catalog()
        if errors:
            print("\n".join(errors))
            return 1
        print(f"OK: {len(read_inventory()['tutorials'])}개 공식 실습의 패키지·출처·파일 연결 확인")
        return 0
    try:
        rows = sorted(read_inventory()["tutorials"], key=lambda row: row["learning_order"])
        if args.command == "show":
            for row in rows:
                package = package_path(ROOT, row["package"])
                matches_order = args.tutorial.isdecimal() and int(args.tutorial) == row["learning_order"]
                if matches_order or args.tutorial in (row["id"], package.name):
                    print((package / "TUTORIAL.md").read_text(encoding="utf-8"))
                    return 0
            parser.error(f"튜토리얼을 찾을 수 없습니다: {args.tutorial}")
        for row in rows:
            package = package_path(ROOT, row["package"])
            metadata = json.loads((package / "tutorial.json").read_text(encoding="utf-8"))
            haystack = " ".join(str(x) for x in (*row.values(), metadata.get("title_ko", ""))).casefold()
            if args.category and row["category"] != args.category:
                continue
            if args.stage and row["learning_stage"] != args.stage:
                continue
            if args.mode and metadata["mode"] != args.mode:
                continue
            if args.search.casefold() not in haystack:
                continue
            print(f"{row['learning_order']:02d}\t{row['id']}\t{row['category']}\t{metadata['mode']}\t{row['title']}\t{row['package']}")
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(1, f"색인 오류: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
