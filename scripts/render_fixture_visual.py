#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from enum import StrEnum
from pathlib import Path
from typing import Final, assert_never

ROOT: Final = Path(__file__).resolve().parents[1]


class Scene(StrEnum):
    FIXTURE = "fixture"
    BEGINNER_INDEX = "beginner-index"
    BEGINNER_01 = "beginner-01"
    BEGINNER_02 = "beginner-02"
    BEGINNER_03 = "beginner-03"
    BEGINNER_04 = "beginner-04"


def scene_content(scene: Scene) -> tuple[str, str, tuple[str, ...]]:
    match scene:
        case Scene.FIXTURE:
            return (
                "로봇 이동 좌표계",
                "로봇과 x축, 진행 방향을 구분한 재현 가능한 도식",
                (
                    '<path d="M120 410H840M160 430V110" stroke="#607d8b" stroke-width="8"/>',
                    '<rect x="350" y="270" width="210" height="100" rx="20" fill="#1976d2"/>',
                    '<circle cx="390" cy="385" r="32" fill="#263238"/><circle cx="520" cy="385" r="32" fill="#263238"/>',
                    '<path d="M560 320H730" stroke="#ef6c00" stroke-width="14"/>',
                    '<text x="350" y="245">로봇</text><text x="585" y="295">진행 방향</text><text x="850" y="420">x축</text>',
                ),
            )
        case Scene.BEGINNER_INDEX:
            return (
                "초급 과정 학습 경로",
                "Gazebo GUI 관찰에서 SDF world 실행까지 이어지는 다섯 단계",
                (
                    '<path d="M135 310H825" stroke="#90a4ae" stroke-width="12"/>',
                    '<g fill="#1565c0"><circle cx="150" cy="310" r="45"/><circle cx="320" cy="310" r="45"/><circle cx="490" cy="310" r="45"/><circle cx="660" cy="310" r="45"/><circle cx="820" cy="310" r="45"/></g>',
                    '<g fill="#fff" font-size="28"><text x="141" y="320">1</text><text x="311" y="320">2</text><text x="481" y="320">3</text><text x="651" y="320">4</text><text x="811" y="320">5</text></g>',
                    '<g font-size="24"><text x="105" y="390">개요</text><text x="280" y="390">GUI</text><text x="455" y="390">SDF</text><text x="610" y="390">검사</text><text x="780" y="390">실행</text></g>',
                ),
            )
        case Scene.BEGINNER_01:
            return (
                "Gazebo 실행 모델과 RTF",
                "GUI와 Server가 simulation time과 상태를 주고받는 구조",
                (
                    '<rect x="90" y="175" width="250" height="210" rx="18" fill="#263238"/><rect x="620" y="175" width="250" height="210" rx="18" fill="#1565c0"/>',
                    '<text x="155" y="245" fill="#fff">Server</text><text x="695" y="245" fill="#fff">GUI</text>',
                    '<path d="M350 245H605M605 315H350" stroke="#ef6c00" stroke-width="10"/>',
                    '<path d="M605 245l-24-15v30zM350 315l24-15v30z" fill="#ef6c00"/>',
                    '<text x="390" y="220">상태·시간</text><text x="405" y="365">사용자 명령</text>',
                    '<rect x="385" y="405" width="190" height="55" rx="12" fill="#fff3e0"/><text x="420" y="442" font-size="24">RTF = 1.00</text>',
                ),
            )
        case Scene.BEGINNER_02:
            return (
                "Gazebo GUI 관찰 지점",
                "Entity Tree, 3D View, Component Inspector를 표시한 주석 화면",
                (
                    '<rect x="45" y="150" width="870" height="340" rx="16" fill="#263238"/>',
                    '<rect x="60" y="190" width="210" height="280" fill="#37474f"/><rect x="285" y="190" width="390" height="280" fill="#cfd8dc"/><rect x="690" y="190" width="210" height="280" fill="#37474f"/>',
                    '<text x="78" y="230" fill="#fff" font-size="22">Entity Tree</text><text x="380" y="230" font-size="22">3D View</text><text x="705" y="230" fill="#fff" font-size="22">Inspector</text>',
                    '<rect x="415" y="325" width="105" height="90" fill="#d84315"/><ellipse cx="565" cy="365" rx="30" ry="65" fill="#1565c0"/>',
                    '<path d="M180 255L350 300M785 255L580 300" stroke="#ffb300" stroke-width="8"/><circle cx="475" cy="170" r="18" fill="#66bb6a"/><text x="505" y="178" font-size="22">Play / Pause / Step</text>',
                ),
            )
        case Scene.BEGINNER_03:
            return (
                "SDF 계층과 pose",
                "world에서 model, link, visual과 collision으로 이어지는 구조",
                (
                    '<g fill="#1565c0"><rect x="375" y="150" width="210" height="60" rx="12"/><rect x="375" y="250" width="210" height="60" rx="12"/><rect x="375" y="350" width="210" height="60" rx="12"/></g>',
                    '<g fill="#fff"><text x="430" y="190">world</text><text x="430" y="290">model</text><text x="445" y="390">link</text></g>',
                    '<path d="M480 210V250M480 310V350M375 380H245M585 380H715" stroke="#607d8b" stroke-width="8"/>',
                    '<rect x="80" y="350" width="165" height="60" rx="12" fill="#ef6c00"/><rect x="715" y="350" width="165" height="60" rx="12" fill="#00897b"/>',
                    '<text x="115" y="390" fill="#fff" font-size="24">visual</text><text x="735" y="390" fill="#fff" font-size="24">collision</text><text x="290" y="470" font-size="22">pose: x y z roll pitch yaw</text>',
                ),
            )
        case Scene.BEGINNER_04:
            return (
                "first_world 예상 화면",
                "회색 ground 위의 빨간 training_box와 파란 beacon",
                (
                    '<path d="M80 420L310 270L880 350L650 500Z" fill="#607d8b"/>',
                    '<path d="M390 300L500 275L570 330L455 360Z" fill="#e64a19"/><path d="M455 360V445L570 410V330Z" fill="#bf360c"/><path d="M390 300V390L455 445V360Z" fill="#d84315"/>',
                    '<ellipse cx="725" cy="325" rx="36" ry="18" fill="#42a5f5"/><rect x="689" y="325" width="72" height="105" fill="#1976d2"/><ellipse cx="725" cy="430" rx="36" ry="18" fill="#0d47a1"/>',
                    '<path d="M455 270L330 185M725 290L820 195" stroke="#ffb300" stroke-width="8"/>',
                    '<text x="140" y="175">training_box</text><text x="755" y="175">beacon</text><text x="120" y="465" fill="#fff" font-size="24">ground · static</text>',
                ),
            )
        case unreachable:
            assert_never(unreachable)


def render_svg(scene: Scene) -> str:
    title, description, body = scene_content(scene)
    lines = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 540" role="img" aria-labelledby="title description" style="color-scheme:light">',
        f'  <title id="title">{title}</title>',
        f'  <desc id="description">{description}</desc>',
        '  <rect width="960" height="540" rx="24" fill="#eef4f8"/>',
        '  <rect width="960" height="105" rx="24" fill="#102a43"/>',
        f'  <text x="48" y="58" fill="#fff" font-family="sans-serif" font-size="34" font-weight="700">{title}</text>',
        f'  <text x="48" y="88" fill="#d9e2ec" font-family="sans-serif" font-size="18">{description}</text>',
        '  <g fill="#17324d" font-family="sans-serif" font-size="30" font-weight="700">',
        *body,
        "  </g>",
        "</svg>",
        "",
    )
    return "\n".join(lines)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    result.add_argument("--output", required=True)
    result.add_argument("--scene", type=Scene, choices=tuple(Scene), default=Scene.FIXTURE)
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
    output.write_text(render_svg(arguments.scene), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
