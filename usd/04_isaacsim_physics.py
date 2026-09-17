"""USD에 물리 속성을 기록하고 Isaac Sim 5.1에서 큐브의 낙하를 측정한다.

실행: ~/isaacsim/python.sh usd/04_isaacsim_physics.py --headless
개념과 출처: 같은 디렉터리의 ISAAC_SIM.md
"""

import argparse
import csv
from datetime import datetime
from pathlib import Path


def main() -> None:
    """인자를 검사한 뒤 앱 생성 → USD 작성 → 물리 실행 → 종료를 진행한다."""
    # 표준 라이브러리만으로 인자를 처리하여 일반 Python에서도 --help가 동작한다.
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--headless", action="store_true", help="GUI 없이 실행")
    parser.add_argument(
        "--steps", type=int,
        help="물리 스텝 수(양수); 생략하면 GUI는 창을 닫을 때까지, headless는 240회",
    )
    parser.add_argument("--output", type=Path, help="새 출력 디렉터리; 기존 경로는 거부")
    args = parser.parse_args()
    if args.steps is not None and args.steps < 1:
        parser.error("--steps에는 양수를 지정하세요.")
    step_limit = args.steps if args.steps is not None else (240 if args.headless else None)

    # 실행마다 새 디렉터리를 사용하므로 앞선 실험 결과를 덮어쓰지 않는다.
    output = args.output or (
        Path(__file__).resolve().parents[1] / "outputs" / "usd"
        / "04_isaacsim_physics" / datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    )
    output.mkdir(parents=True, exist_ok=False)

    # Isaac Sim은 Kit 확장을 먼저 시작해야 omni, Core API 등을 가져올 수 있다.
    from isaacsim import SimulationApp

    app = SimulationApp({"headless": args.headless})
    try:
        import omni.usd
        from isaacsim.core.api import World
        from isaacsim.core.prims import RigidPrim
        from isaacsim.core.utils.viewports import set_camera_view
        from pxr import Gf, UsdGeom, UsdLux, UsdPhysics

        # World는 실행 관리자이다. /World라는 USD Prim과 같은 객체가 아니다.
        # 이 예제는 물리와 렌더링 간격을 모두 1/60초로 설정한다.
        world = World(stage_units_in_meters=1.0, physics_dt=1 / 60, rendering_dt=1 / 60)
        stage = omni.usd.get_context().get_stage()
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
        UsdPhysics.SetStageKilogramsPerUnit(stage, 1.0)
        world.get_physics_context().set_gravity(-9.81)
        root = UsdGeom.Xform.Define(stage, "/World")
        stage.SetDefaultPrim(root.GetPrim())

        # Cube는 모양을 정의하는 typed schema다. 이 호출만으로는 떨어지지 않는다.
        cube = UsdGeom.Cube.Define(stage, "/World/FallingCube")
        cube.CreateSizeAttr(0.5)
        cube.AddTranslateOp().Set(Gf.Vec3d(0.0, 0.0, 2.0))
        cube.CreateDisplayColorAttr([Gf.Vec3f(0.15, 0.55, 0.9)])

        # API schema를 기존 Prim에 적용하여 서로 다른 물리 역할을 기록한다.
        # RigidBodyAPI: 힘에 따라 움직이는 강체, CollisionAPI: 접촉을 계산할 형상.
        # MassAPI: 질량 정보. 여기서는 1 kg이며 관성은 엔진이 형상에서 계산한다.
        prim = cube.GetPrim()
        UsdPhysics.RigidBodyAPI.Apply(prim)
        UsdPhysics.CollisionAPI.Apply(prim)
        UsdPhysics.MassAPI.Apply(prim).CreateMassAttr(1.0)

        # 외부 자산 없이 넓고 얇은 상자를 바닥으로 만든다. 윗면 높이는 z=0이다.
        floor = UsdGeom.Cube.Define(stage, "/World/Floor")
        floor.CreateSizeAttr(1.0)
        floor.AddTranslateOp().Set(Gf.Vec3d(0.0, 0.0, -0.1))
        floor.AddScaleOp().Set(Gf.Vec3f(6.0, 6.0, 0.2))
        floor.CreateDisplayColorAttr([Gf.Vec3f(0.35, 0.35, 0.35)])
        # 강체 API가 없는 이 충돌체는 정적 바닥으로 동작한다.
        UsdPhysics.CollisionAPI.Apply(floor.GetPrim())

        # 텍스처 파일이 없는 조명과 뷰포트 시점을 설정하여 GUI에서 관찰한다.
        light = UsdLux.DomeLight.Define(stage, "/World/Light")
        light.CreateIntensityAttr(800.0)
        if not args.headless:
            set_camera_view(eye=[4.0, 4.0, 3.0], target=[0.0, 0.0, 0.8])

        # RigidPrim은 이미 작성한 큐브에 접근하는 Python 래퍼이며 새 큐브가 아니다.
        # scene에 등록하면 world.reset()이 물리 핸들을 초기화한다.
        body = world.scene.add(RigidPrim("/World/FallingCube", name="falling_cube"))

        # 실행 전 설계값을 저장한다. 따라서 파일의 큐브 시작 높이는 항상 2 m이다.
        # 이번 예제는 모든 장면 데이터를 root layer에 직접 작성했으므로 이 한 파일로 충분하다.
        scene_path = output / "initial_scene.usda"
        if not stage.GetRootLayer().Export(str(scene_path)):
            raise RuntimeError(f"USD 저장 실패: {scene_path}")
        world.reset()

        # 물리 실행 중에는 USD 속성 대신 Core API로 실제 강체 상태를 읽는다.
        # get_world_poses()의 위치 배열은 (물체 수, 3)이라 첫 물체의 z는 [0, 2]다.
        def read_motion() -> tuple[float, float]:
            positions, _ = body.get_world_poses()
            velocities = body.get_linear_velocities()
            return float(positions[0, 2]), float(velocities[0, 2])

        with (output / "heights.csv").open("x", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream)
            writer.writerow(["step", "time_s", "z_m", "vz_m_s"])
            step = 0
            z, vz = read_motion()
            writer.writerow([step, world.current_time, z, vz])
            print(f"시작: z={z:.4f} m, vz={vz:.4f} m/s", flush=True)
            while app.is_running() and (step_limit is None or step < step_limit):
                # GUI에서 일시정지하면 화면만 갱신하고 물리 스텝 수는 늘리지 않는다.
                if not world.is_playing():
                    app.update()
                    continue
                world.step(render=not args.headless)
                step += 1
                z, vz = read_motion()
                writer.writerow([step, world.current_time, z, vz])
                if step % 60 == 0 or step == step_limit:
                    stream.flush()
                    print(f"step={step}: z={z:.4f} m, vz={vz:.4f} m/s", flush=True)

            # 0.5 m 큐브가 바닥에 놓이면 중심 높이는 약 0.25 m가 된다.
            # 짧은 --steps 실행에서는 아직 공중에 있을 수 있으므로 실패로 단정하지 않는다.
            print(f"종료: step={step}, z={z:.4f} m, vz={vz:.4f} m/s", flush=True)
        print(f"설계 USD와 측정 CSV: {output.resolve()}", flush=True)
    finally:
        # USD 작성이나 물리 계산 중 예외가 발생해도 앱 자원을 정리한다.
        app.close()


if __name__ == "__main__":
    main()
