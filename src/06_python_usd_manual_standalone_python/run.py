import argparse
from itertools import count
from datetime import datetime
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Python Environment")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument(
        "--steps", type=int, default=None, help="Positive step limit; omitted: keep GUI open (headless: 120 steps)"
    )
    parser.add_argument(
        "--output", type=Path, help="New output directory; existing paths are rejected"
    )
    parser.add_argument("--width", type=int, default=800)
    parser.add_argument("--height", type=int, default=600)
    parser.add_argument("--stage", type=Path, help="Optional local USD stage to open")
    parser.add_argument(
        "--extension",
        action="append",
        default=[],
        help="Extension ID to enable; repeatable",
    )
    args = parser.parse_args()
    if args.steps is not None and args.steps < 1:
        parser.error("--steps must be positive")
    if args.steps is None and args.headless:
        args.steps = 120
    output = args.output or Path(__file__).parent / "output" / datetime.now().strftime(
        "%Y%m%d-%H%M%S-%f"
    )
    output.mkdir(parents=True, exist_ok=False)
    from isaacsim import SimulationApp
    # SimulationApp은 Python에서 Isaac Sim의 Kit 애플리케이션을 시작하고 갱신·종료하는 클래스이다.
    # headless=True는 창 없이 실행한다는 뜻이며, omni와 Isaac Sim 확장 모듈은 앱 생성 후 import한다.

    app = SimulationApp(
        {"headless": args.headless, "width": args.width, "height": args.height}
    )
    try:
        import os
        import numpy as np
        import omni.usd
        # omni.usd는 현재 Kit 애플리케이션의 USD 문맥에 접근하는 모듈이다.
        # get_context().get_stage()로 객체·조명 등이 들어 있는 현재 Stage를 얻는다.
        from isaacsim.core.api import World
        # World는 Stage의 객체와 작업을 관리하고 물리·렌더링 시간 간격, 초기화, 시뮬레이션 진행을 제어한다.
        from isaacsim.core.api.objects import DynamicCuboid
        # DynamicCuboid는 큐브 형상에 강체와 충돌 속성을 함께 부여하므로 중력과 접촉에 반응한다.
        from isaacsim.core.utils.extensions import enable_extension
        # enable_extension은 이름으로 지정한 Kit 확장을 활성화하여 해당 기능과 명령을 사용할 수 있게 한다.

        for extension in args.extension:
            enable_extension(extension)
        # Kit의 한 프레임을 갱신하여 렌더링·이벤트·비동기 작업을 처리한다.
        # 물리 진행 여부는 현재 타임라인의 재생 상태와 설정에 따라 달라진다.
        app.update()
        if args.stage:
            if not args.stage.is_file():
                raise FileNotFoundError(args.stage)
            # USD 파일을 Kit의 현재 Stage로 연다.
            if not omni.usd.get_context().open_stage(str(args.stage.resolve())):
                raise RuntimeError(f"Could not open {args.stage}")
            app.update()
        # stage_units_in_meters는 장면 길이 단위이고, physics_dt·rendering_dt는 각각 물리·렌더링 시간 간격(초)이다.
        world = World(stage_units_in_meters=1.0, physics_dt=1 / 60, rendering_dt=1 / 30)
        if not args.stage:
            # 기본 바닥을 Scene에 추가한다. 이 바닥은 강체가 떨어졌을 때 충돌할 표면이다.
            world.scene.add_default_ground_plane()
            # 생성한 객체를 World의 Scene에 등록하여 이름으로 찾고 초기화할 수 있게 한다.
            world.scene.add(
                DynamicCuboid(
                    prim_path="/World/Cube",
                    name="cube",
                    position=np.array([0, 0, 2]),
                    size=0.4,
                )
            )
        # World를 초기화하고 등록된 객체의 물리 핸들을 준비한다. 관절·강체 상태를 읽기 전에 호출한다.
        world.reset()
        counts = {"physics_callbacks": 0, "requested_steps": args.steps}

        def count_physics(dt):
            counts["physics_callbacks"] += 1

        # 물리 step마다 실행할 콜백을 등록한다. 콜백의 시간 간격으로 제어 계산을 맞출 수 있다.
        world.add_physics_callback("environment_count", count_physics)
        for step in count():
            if not app.is_running() or (args.steps is not None and step >= args.steps):
                break
            # 물리 시뮬레이션을 한 step 진행한다. render는 이 호출에서 렌더링도 수행할지 지정한다.
            world.step(render=not args.headless)
        # 이름으로 등록한 물리 콜백을 해제하여 이후 step에서는 호출되지 않게 한다.
        world.remove_physics_callback("environment_count")
        counts["physics_time_s"] = float(world.current_time)
        counts["environment"] = {
            key: os.environ.get(key)
            for key in ("ISAAC_PATH", "EXP_PATH", "CARB_APP_PATH")
        }
        counts["enabled_extensions"] = args.extension
        counts["requested_resolution"] = [args.width, args.height]
        (output / "environment.json").write_text(json.dumps(counts, indent=2))
        omni.usd.get_context().get_stage().GetRootLayer().Export(
            str(output / "scene.usda")
        )
        print(json.dumps(counts, indent=2))
        print(f"Outputs: {output.resolve()}")
    finally:
        # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
        app.close()


if __name__ == "__main__":
    main()
