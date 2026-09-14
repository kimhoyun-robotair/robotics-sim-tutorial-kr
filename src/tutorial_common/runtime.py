"""CLI, 출력 경로, asset 조회. World와 simulation loop는 각 예제에서 직접 관리한다."""

import argparse
import json
import math
import sys
import traceback
from datetime import datetime
from pathlib import Path


def positive_int(value: str) -> int:
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("0보다 큰 정수를 입력하세요.")
    return number


def positive_float(value: str) -> float:
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError("유한한 양수를 입력하세요.")
    return number


def add_common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--headless", action="store_true", help="GUI 없이 실행")
    parser.add_argument(
        "--output", type=Path, help="새 결과 디렉터리 (이미 존재하면 오류)"
    )


def output_directory(project: str, requested: Path | None) -> Path:
    root = Path(__file__).resolve().parents[2]
    path = requested or root / "outputs" / project / datetime.now().strftime(
        "%Y%m%d-%H%M%S-%f"
    )
    path = path.expanduser().resolve()
    path.mkdir(parents=True, exist_ok=False)
    return path


def write_json(path: Path, data: dict[str, object]) -> None:
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def launch_app(headless: bool):
    # isaacsim/omni/pxr의 나머지 모듈은 SimulationApp 생성 이후에 import한다.
    from isaacsim import SimulationApp

    app = SimulationApp({"headless": headless, "renderer": "RaytracedLighting"})
    from isaacsim.core.version import get_version

    version = get_version()[0]
    if version != "5.1.0":
        try:
            raise RuntimeError(
                f"이 예제는 Isaac Sim 5.1.0용입니다. 현재 버전: {version!r}"
            )
        finally:
            close_app(app)
    return app


def close_app(app) -> None:
    # Kit의 fast shutdown 전에 traceback과 종료 코드를 전달해야 실패가 성공으로 보이지 않는다.
    exception = sys.exc_info()
    if exception[0] is not None:
        import omni.kit.app

        traceback.print_exception(*exception)
        omni.kit.app.get_app().post_quit(
            130 if isinstance(exception[1], KeyboardInterrupt) else 1
        )
    sys.stdout.flush()
    sys.stderr.flush()
    app.close()


def asset_path(relative: str) -> str:
    from isaacsim.storage.native import get_assets_root_path

    root = get_assets_root_path()
    if root is None:
        raise RuntimeError(
            "Isaac Sim 5.1 asset root를 찾지 못했습니다. README의 USD Assets를 확인하세요."
        )
    return root + relative
