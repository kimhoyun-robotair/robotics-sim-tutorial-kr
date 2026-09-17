"""Configure the 5.1 native gantry gripper, close, lift, release, and log actual state."""
import argparse
import csv
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--steps", type=int, default=None,
                        help="Physics step limit; omitted/0: GUI until closed, headless default: 420")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--grip-distance", type=float, default=0.02)
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "output" / "gripper.csv")
    args = parser.parse_args()
    if args.steps is None:
        args.steps = 420 if args.headless else 0
    if args.steps < 0 or (args.headless and args.steps == 0):
        parser.error("--steps must be nonnegative; headless requires positive steps")
    if args.grip_distance <= 0:
        parser.error("--grip-distance must be positive")
    if args.output.exists():
        parser.error("Output exists; choose another --output")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    from isaacsim import SimulationApp
    # SimulationApp은 Python에서 Isaac Sim의 Kit 애플리케이션을 시작하고 갱신·종료하는 클래스이다.
    # headless=True는 창 없이 실행한다는 뜻이며, omni와 Isaac Sim 확장 모듈은 앱 생성 후 import한다.

    app = SimulationApp({"headless": args.headless})
    try:
        from isaacsim.core.api import World
        # World는 Stage의 객체와 작업을 관리하고 물리·렌더링 시간 간격, 초기화, 시뮬레이션 진행을 제어한다.
        from isaacsim.core.utils.extensions import enable_extension, get_extension_path_from_name
        # enable_extension은 이름으로 지정한 Kit 확장을 활성화하여 해당 기능과 명령을 사용할 수 있게 한다.
        # get_extension_path_from_name은 확장의 설치 경로를 찾아 내부 설정·예제 파일에 접근할 때 사용한다.
        from isaacsim.core.utils.stage import add_reference_to_stage, get_current_stage
        # add_reference_to_stage는 외부 USD 자산을 현재 Stage의 지정한 Prim 경로에 참조로 연결한다.
        # get_current_stage는 현재 Isaac Sim에서 열려 있는 USD Stage를 반환한다.
        enable_extension("isaacsim.robot.surface_gripper")
        from isaacsim.robot.surface_gripper import GripperView
        # GripperView는 Surface Gripper들을 묶어 열기·닫기 명령과 부착 상태를 다루는 API이다.
        from isaacsim.robot.surface_gripper._surface_gripper import GripperStatus
        # GripperStatus는 Surface Gripper의 상태 값을 구분하는 열거형이다.
        from usd.schema.isaac import robot_schema
        # robot_schema는 USD Prim에 로봇·링크·관절·부착점 등의 의미와 관계를 기록하는 Isaac 로봇 스키마이다.

        # stage_units_in_meters는 장면 길이 단위이고, physics_dt·rendering_dt는 각각 물리·렌더링 시간 간격(초)이다.
        world = World(stage_units_in_meters=1.0, physics_dt=1 / 60, rendering_dt=1 / 60)
        scene = Path(get_extension_path_from_name("isaacsim.robot.surface_gripper")) / "data" / "SurfaceGripper_gantry.usda"
        if not scene.is_file():
            raise FileNotFoundError(scene)
        add_reference_to_stage(str(scene), "/World")
        stage = get_current_stage()
        path = "/World/SurfaceGripper"
        robot_schema.CreateSurfaceGripper(stage, path)
        joints = stage.GetPrimAtPath("/World/Surface_Gripper_Joints")
        stage.GetPrimAtPath(path).GetRelationship(robot_schema.Relations.ATTACHMENT_POINTS.name).SetTargets(
            [joint.GetPath() for joint in joints.GetChildren()]
        )
        gripper = GripperView(paths=path)
        # 흡착 가능한 거리와 부착을 유지할 힘의 한계 등을 설정한다. 배열의 각 값은 해당 그리퍼에 대응한다.
        gripper.set_surface_gripper_properties(
            max_grip_distance=[args.grip_distance], coaxial_force_limit=[0.005],
            shear_force_limit=[5], retry_interval=[1.0],
        )
        # World를 초기화하고 등록된 객체의 물리 핸들을 준비한다. 관절·강체 상태를 읽기 전에 호출한다.
        world.reset()
        for axis, target in (("x", 0.0), ("y", 0.0), ("z", 0.140)):
            stage.GetPrimAtPath(f"/World/Joints/{axis}_joint").GetAttribute(
                "drive:linear:physics:targetPosition"
            ).Set(target)
        closed_seen = False
        with args.output.open("x", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(["step", "status", "gripped_objects"])
            step = 0
            while app.is_running() and (args.steps == 0 or step < args.steps):
                if step == 120:
                    # Surface Gripper에 닫기·열기 명령을 전달한다. 이 예제에서는 양수로 닫고 음수로 연다.
                    gripper.apply_gripper_action([0.5])
                if step == 240:
                    stage.GetPrimAtPath("/World/Joints/z_joint").GetAttribute(
                        "drive:linear:physics:targetPosition"
                    ).Set(0.05)
                if step == 360:
                    gripper.apply_gripper_action([-0.5])
                # 물리 시뮬레이션을 한 step 진행한다. render는 이 호출에서 렌더링도 수행할지 지정한다.
                world.step(render=not args.headless)
                if not app.is_running():
                    break
                if step % 10 == 0:
                    state = GripperStatus(gripper.get_surface_gripper_status()[0])
                    # 실제로 부착된 객체 경로를 읽어 닫기 명령이 실제 부착으로 이어졌는지 확인한다.
                    objects = gripper.get_gripped_objects()[0]
                    closed_seen |= state == GripperStatus.Closed and bool(objects)
                    writer.writerow([step, str(state), "|".join(objects)])
                    print(step, state, objects)
                step += 1
        if step >= 400 and not closed_seen:
            raise RuntimeError("No attached object was observed; inspect grip distance and joint contact geometry")
    finally:
        # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
        app.close()


if __name__ == "__main__":
    main()
