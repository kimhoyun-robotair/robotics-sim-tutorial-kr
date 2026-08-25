#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Final


ROOT: Final = Path(__file__).resolve().parents[1]
SVG: Final = "\n".join(
    (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 480" role="img" aria-labelledby="title description" style="color-scheme:light">',
        '  <title id="title">로봇 이동 좌표계</title>',
        '  <desc id="description">로봇과 x축, 진행 방향을 구분한 재현 가능한 도식</desc>',
        '  <rect width="960" height="480" rx="24" fill="#eef4f8"/>',
        '  <path d="M120 390H840" stroke="#526d82" stroke-width="8"/>',
        '  <path d="M160 410V90" stroke="#526d82" stroke-width="8"/>',
        '  <path d="M840 390l-32-18v36z" fill="#526d82"/>',
        '  <path d="M160 90l-18 32h36z" fill="#526d82"/>',
        '  <rect x="350" y="250" width="210" height="100" rx="20" fill="#1565c0"/>',
        '  <circle cx="390" cy="365" r="34" fill="#263238"/>',
        '  <circle cx="520" cy="365" r="34" fill="#263238"/>',
        '  <path d="M560 300H730" stroke="#e65100" stroke-width="14"/>',
        '  <path d="M730 300l-42-26v52z" fill="#e65100"/>',
        '  <g fill="#17324d" font-family="sans-serif" font-size="30" font-weight="700">',
        '    <text x="865" y="402">x축</text>',
        '    <text x="330" y="225">로봇</text>',
        '    <text x="575" y="275">진행 방향</text>',
        "  </g>",
        "</svg>",
        "",
    )
)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    result.add_argument("--output", required=True)
    result.add_argument("--force-failure", action="store_true")
    result.add_argument("--cleanup-failure", action="store_true")
    return result


def main() -> int:
    arguments = parser().parse_args()
    sys.path.insert(0, str(ROOT))
    from scripts.fixtures.processes._fixture_support import spawn_registered_sentinel

    if arguments.cleanup_failure:
        spawn_registered_sentinel(stale_identity=True)
        return 70
    spawn_registered_sentinel()
    if arguments.force_failure:
        return 1
    output = ROOT / arguments.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(SVG, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
