"""Measure the step response of a real PhysX prismatic drive and expose it to Gain Tuner."""
import argparse
import csv
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stiffness", type=float, default=100.0, help="Linear drive stiffness, N/m")
    parser.add_argument("--damping", type=float, default=20.0, help="Linear drive damping, N s/m")
    parser.add_argument("--mass", type=float, default=1.0, help="Slider mass, kg")
    parser.add_argument("--target", type=float, default=0.5, help="Target position, m")
    parser.add_argument("--velocity", type=float, default=0.0, help="Target velocity, m/s; use stiffness 0 for velocity control")
    parser.add_argument("--steps", type=int, default=None, help="240 Hz physics step limit; omitted or 0 keeps the GUI open")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("output"))
    args = parser.parse_args()
    if args.steps is None:
        args.steps = 720 if args.headless else 0
    if args.mass <= 0 or min(args.stiffness, args.damping, args.steps) < 0 or not 0 <= args.target <= 1:
        parser.error("mass>0, nonnegative gains/steps, target within [0,1] are required")
    if args.headless and args.steps == 0:
        parser.error("Headless execution needs positive --steps")
    output = args.output.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=False)
    from isaacsim import SimulationApp
    # SimulationApp은 Python에서 Isaac Sim의 Kit 애플리케이션을 시작하고 갱신·종료하는 클래스이다.
    # headless=True는 창 없이 실행한다는 뜻이며, omni와 Isaac Sim 확장 모듈은 앱 생성 후 import한다.
    app = SimulationApp({"headless": args.headless})
    try:
        import omni.usd
        # omni.usd는 현재 Kit 애플리케이션의 USD 문맥에 접근하는 모듈이다.
        # get_context().get_stage()로 객체·조명 등이 들어 있는 현재 Stage를 얻는다.
        import numpy as np
        from pxr import Gf, UsdGeom, UsdLux, UsdPhysics
        # pxr은 USD 장면을 직접 다루는 OpenUSD의 Python 바인딩이다.
        # Gf는 벡터·행렬·쿼터니언 등 위치와 회전을 계산하는 수학 자료형을 다룬다.
        # UsdGeom은 형상, 변환, 카메라와 장면 단위·축 설정을 다룬다.
        # UsdLux는 조명 Prim과 빛의 속성을 다룬다.
        # UsdPhysics는 강체·충돌·관절·물리 재질의 USD 스키마를 다룬다.
        from isaacsim.core.api import World
        # World는 Stage의 객체와 작업을 관리하고 물리·렌더링 시간 간격, 초기화, 시뮬레이션 진행을 제어한다.
        from isaacsim.core.prims import SingleArticulation
        # SingleArticulation은 하나의 관절 구조를 감싸 관절 위치·속도·힘을 읽고 제어한다.
        from isaacsim.core.utils.types import ArticulationAction
        # ArticulationAction은 관절 위치·속도·힘 명령과 적용할 관절 인덱스를 담는 자료형이다.
        # 이 값을 apply_action에 전달하면 관절 제어기가 해당 명령을 적용한다.
        import usd.schema.isaac.robot_schema as rs
        # robot_schema는 USD Prim에 로봇·링크·관절·부착점 등의 의미와 관계를 기록하는 Isaac 로봇 스키마이다.
        world = World(stage_units_in_meters=1, physics_dt=1 / 240, rendering_dt=1 / 60)
        stage = omni.usd.get_context().get_stage()
        # 지정한 경로에 변환용 Xform Prim을 정의한다. 자식 객체를 묶어 함께 이동·회전시킬 때 사용할 수 있다.
        robot = UsdGeom.Xform.Define(stage, "/GainRig").GetPrim()
        stage.SetDefaultPrim(robot)
        for name in ["base", "slider"]:
            prim = UsdGeom.Xform.Define(stage, f"/GainRig/{name}").GetPrim()
            # Prim에 강체 API를 적용하여 물리 시뮬레이션이 자세와 속도를 계산할 수 있게 한다.
            UsdPhysics.RigidBodyAPI.Apply(prim)
            UsdPhysics.MassAPI.Apply(prim).CreateMassAttr(args.mass if name == "slider" else 1.0)
            # USD Stage에 Cube 형상을 직접 정의한다. 물리 동작이 필요하면 강체·충돌 API를 별도로 적용한다.
            geom = UsdGeom.Cube.Define(stage, str(prim.GetPath()) + "/visual")
            geom.CreateSizeAttr(0.1)
            geom.AddTranslateOp().Set(Gf.Vec3d(-0.15 if name == "base" else 0, 0, 1))
            geom.CreateDisplayColorAttr([Gf.Vec3f(0.2, 0.6, 0.9) if name == "slider" else Gf.Vec3f(0.5)])
        # 연결한 두 몸체의 상대 자세를 고정하는 관절을 정의한다.
        fixed = UsdPhysics.FixedJoint.Define(stage, "/GainRig/fixed_joint")
        fixed.CreateBody1Rel().SetTargets(["/GainRig/base"])
        # 관절로 연결된 구조의 articulation 루트를 지정한다.
        UsdPhysics.ArticulationRootAPI.Apply(fixed.GetPrim())
        # 두 몸체 사이의 직선 이동 관절을 정의한다. 연결 대상과 이동 축·제한을 이어서 지정한다.
        joint = UsdPhysics.PrismaticJoint.Define(stage, "/GainRig/slider_joint")
        joint.CreateBody0Rel().SetTargets(["/GainRig/base"])
        joint.CreateBody1Rel().SetTargets(["/GainRig/slider"])
        joint.CreateAxisAttr("X")
        joint.CreateLowerLimitAttr(0)
        joint.CreateUpperLimitAttr(1)
        # 관절에 구동 API를 적용한다. stiffness·damping·목표값으로 관절 구동 방식을 설정한다.
        drive = UsdPhysics.DriveAPI.Apply(joint.GetPrim(), "linear")
        drive.CreateStiffnessAttr(args.stiffness)
        drive.CreateDampingAttr(args.damping)
        drive.CreateMaxForceAttr(200.0)
        drive.CreateTargetPositionAttr(args.target)
        drive.CreateTargetVelocityAttr(args.velocity)
        rs.ApplyRobotAPI(robot)
        for name in ["base", "slider"]:
            prim = stage.GetPrimAtPath(f"/GainRig/{name}")
            rs.ApplyLinkAPI(prim)
            robot.GetRelationship(rs.Relations.ROBOT_LINKS.name).AddTarget(prim.GetPath())
        rs.ApplyJointAPI(joint.GetPrim())
        robot.GetRelationship(rs.Relations.ROBOT_JOINTS.name).AddTarget(joint.GetPath())
        # 주변을 둘러싸는 DomeLight를 생성하여 장면의 환경 조명을 설정한다.
        UsdLux.DomeLight.Define(stage, "/World/Light").CreateIntensityAttr(800)
        # Stage의 루트 레이어를 USD 파일로 내보낸다. 참조 자산 자체를 모두 복사하는 것은 아니다.
        stage.GetRootLayer().Export(str(output / "gain_rig.usda"))
        # 생성한 객체를 World의 Scene에 등록하여 이름으로 찾고 초기화할 수 있게 한다.
        articulation = world.scene.add(SingleArticulation(prim_path="/GainRig", name="gain_rig"))
        # World를 초기화하고 등록된 객체의 물리 핸들을 준비한다. 관절·강체 상태를 읽기 전에 호출한다.
        world.reset()
        articulation.apply_action(ArticulationAction(joint_positions=np.array([args.target]), joint_velocities=np.array([args.velocity])))
        index = articulation.get_dof_index("slider_joint")
        last_sample = None
        peak_position = float("-inf")
        step = 0
        with (output / "response.csv").open("w", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(["time_s", "position_m", "velocity_m_s", "target_position_m", "target_velocity_m_s"])
            while app.is_running() and (args.steps == 0 or step < args.steps):
                # 물리 시뮬레이션을 한 step 진행한다. render는 이 호출에서 렌더링도 수행할지 지정한다.
                world.step(render=not args.headless)
                if not app.is_running():
                    break
                if not world.is_playing():
                    continue
                position = float(articulation.get_joint_positions()[index])
                velocity = float(articulation.get_joint_velocities()[index])
                row = [(step + 1) / 240, position, velocity, args.target, args.velocity]
                writer.writerow(row)
                last_sample = row
                peak_position = max(peak_position, position)
                step += 1
        if last_sample is not None:
            metrics = {"samples": step, "final_position_m": last_sample[1],
                       "final_velocity_m_s": last_sample[2], "final_position_error_m": args.target - last_sample[1],
                       "overshoot_m": max(0.0, peak_position - args.target)}
            (output / "metrics.json").write_text(json.dumps(metrics, indent=2))
            print(json.dumps(metrics, indent=2))
    finally:
        # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
        app.close()


if __name__ == "__main__":
    main()
