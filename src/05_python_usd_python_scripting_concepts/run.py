import argparse
from itertools import count
from datetime import datetime
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Python Scripting Concepts")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument(
        "--steps", type=int, default=None, help="Positive step limit; omitted: keep GUI open (headless: 120 steps)"
    )
    parser.add_argument(
        "--output", type=Path, help="New output directory; existing paths are rejected"
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
    app = SimulationApp({"headless": args.headless})
    try:
        import csv
        import numpy as np
        import omni.usd
        # omni.usd는 현재 Kit 애플리케이션의 USD 문맥에 접근하는 모듈이다.
        # get_context().get_stage()로 객체·조명 등이 들어 있는 현재 Stage를 얻는다.
        from isaacsim.core.api import World
        # World는 Stage의 객체와 작업을 관리하고 물리·렌더링 시간 간격, 초기화, 시뮬레이션 진행을 제어한다.
        from isaacsim.core.api.objects import DynamicCuboid
        # DynamicCuboid는 큐브 형상에 강체와 충돌 속성을 함께 부여하므로 중력과 접촉에 반응한다.
        from pxr import UsdLux
        # pxr은 USD 장면을 직접 다루는 OpenUSD의 Python 바인딩이다.
        # UsdLux는 조명 Prim과 빛의 속성을 다룬다.

        # stage_units_in_meters는 장면 길이 단위이고, physics_dt·rendering_dt는 각각 물리·렌더링 시간 간격(초)이다.
        world = World(stage_units_in_meters=1.0, physics_dt=1 / 60, rendering_dt=1 / 60)
        # 기본 바닥을 Scene에 추가한다. 이 바닥은 강체가 떨어졌을 때 충돌할 표면이다.
        world.scene.add_default_ground_plane()
        # 평행한 방향의 빛을 내는 DistantLight를 생성하고 강도를 설정한다.
        UsdLux.DistantLight.Define(
            omni.usd.get_context().get_stage(), "/World/Light"
        ).CreateIntensityAttr(1500)
        # 생성한 객체를 World의 Scene에 등록하여 이름으로 찾고 초기화할 수 있게 한다.
        cube = world.scene.add(
            DynamicCuboid(
                prim_path="/World/FallingCube",
                name="cube",
                position=np.array([0, 0, 2.0]),
                size=0.4,
            )
        )
        # World를 초기화하고 등록된 객체의 물리 핸들을 준비한다. 관절·강체 상태를 읽기 전에 호출한다.
        world.reset()
        callback_count = 0
        elapsed_time = 0.0

        def on_physics(dt):
            nonlocal callback_count, elapsed_time
            callback_count += 1
            elapsed_time += float(dt)

        # 물리 step마다 실행할 콜백을 등록한다. 콜백의 시간 간격으로 제어 계산을 맞출 수 있다.
        world.add_physics_callback("count_physics", on_physics)
        with (output / "timeline.csv").open("x", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(
                [
                    "loop_iteration",
                    "physics_callbacks",
                    "simulated_time_s",
                    "cube_height_m",
                ]
            )
            for i in count():
                if not app.is_running() or (args.steps is not None and i >= args.steps):
                    break
                # 물리 시뮬레이션을 한 step 진행한다. render는 이 호출에서 렌더링도 수행할지 지정한다.
                world.step(render=not args.headless)
                writer.writerow(
                    [
                        i + 1,
                        callback_count,
                        elapsed_time,
                        float(cube.get_world_pose()[0][2]),
                    ]
                )
        # 이름으로 등록한 물리 콜백을 해제하여 이후 step에서는 호출되지 않게 한다.
        world.remove_physics_callback("count_physics")
        print(
            f"Physics callbacks: {callback_count}, elapsed simulation time: {elapsed_time:.3f} s"
        )
        print(f"Outputs: {output.resolve()}")
    finally:
        # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
        app.close()


if __name__ == "__main__":
    main()
