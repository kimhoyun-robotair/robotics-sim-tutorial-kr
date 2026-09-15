"""낙하 큐브로 World, Scene, 물리 콜백 관찰 — Isaac Sim 5.1 standalone lesson."""
import argparse
from itertools import count
import json
from pathlib import Path
import time


def main():
    parser = argparse.ArgumentParser(description='낙하 큐브로 World, Scene, 물리 콜백 관찰')
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--steps", type=int, default=None, help="Positive step limit; omitted: keep GUI open (headless: 300 steps)")
    parser.add_argument("--output", type=Path, help="New output directory; existing paths are rejected")
    parser.add_argument("--height", type=float, default=1.0, help="Initial cube center height in meters")
    args = parser.parse_args()
    if args.steps is not None and args.steps < 1:
        parser.error("--steps must be positive")
    if args.steps is None and args.headless:
        args.steps = 300
    output = args.output or Path(__file__).resolve().parent / "output" / str(time.time_ns())
    output.mkdir(parents=True, exist_ok=False)

    # isaac sim 시뮬레이션 설정 및 시작
    from isaacsim import SimulationApp
    # GUI 모드 사용
    app = SimulationApp({"headless": args.headless})
    try:
        import csv
        import numpy as np
        from isaacsim.core.api import World
        # 기본적인 Scene을 추가하고
        from isaacsim.core.api.objects import DynamicCuboid
        # 이번에는 한번에 Visula+Rigid+Collision을 부여하겠다는 뜻
        world = World(stage_units_in_meters=1.0, physics_dt=1/60, rendering_dt=1/60)
        world.scene.add_default_ground_plane()
        # 파이썬을 통해서 쉽게 Prim을 조작할 수 있도록 변수에 할당한다.
        cube = world.scene.add(DynamicCuboid(
            prim_path="/World/FallingCube", name="falling_cube", size=0.5,
            position=np.array([0.0, 0.0, args.height]), color=np.array([0.1, 0.2, 0.9])))
        world.reset()
        assert World.instance() is world # instance()는 World 객체를 반환한다.
        # 하나의 인스턴스를 공유하는 방식이라 다른 함수나 클래스에서도 instance()로 같은 World 접근이 가능
        sample_count = 0
        with (output / "fall.csv").open("x", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(["time_s", "x_m", "y_m", "z_m", "vx_mps", "vy_mps", "vz_mps"])

            def observe(step_size):
                # 물리 정보를 읽어오기 위한 콜백 함수
                nonlocal sample_count
                position, quaternion = cube.get_world_pose() # 큐브의 현재 위치를 읽어오고
                velocity = cube.get_linear_velocity() # 속도도 읽어오고
                writer.writerow([world.current_time, *position.tolist(), *velocity.tolist()])
                sample_count += 1

            world.add_physics_callback("observe_fall", callback_fn=observe) # callback 함수를 등록한다.
            # 정해진 시점에 내가 정한 프레임워크를 호출하도록 넘기는 방식
            # Isaac Sim의 callback의 경우 물리 시뮬레이션 step이 갱신될때마다 callback을 실행한다.
            try:
                for step in count():
                    if not app.is_running() or (args.steps is not None and step >= args.steps):
                        break
                    world.step(render=not args.headless)
                    if step % 60 == 0:
                        print(f"step={step} position_m={cube.get_world_pose()[0]} velocity_mps={cube.get_linear_velocity()}")
            finally:
                world.remove_physics_callback("observe_fall")
        result = {"samples": sample_count, "final_position_m": cube.get_world_pose()[0].tolist(),
                  "final_velocity_mps": cube.get_linear_velocity().tolist(), "expected_rest_height_m": 0.25}
        (output / "result.json").write_text(json.dumps(result, indent=2))
        print(json.dumps(result), "output=", output)
    finally:
        app.close()


if __name__ == "__main__":
    main()
