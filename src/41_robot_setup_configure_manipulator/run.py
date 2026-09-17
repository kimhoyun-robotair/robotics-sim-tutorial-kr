"""UR10e solver·Robotiq 마찰·finger effort를 로컬 layer에 설정 — Isaac Sim 5.1 standalone lesson."""
import argparse
import json
from pathlib import Path
import time


def main():
    parser = argparse.ArgumentParser(description='UR10e solver·Robotiq 마찰·finger effort를 로컬 layer에 설정')
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--steps", type=int, default=None, help="Kit update limit; omitted or 0 keeps the GUI open")
    parser.add_argument("--frames", type=int, default=1200, help="Legacy headless update limit when --steps is omitted; does not close the GUI")
    parser.add_argument("--output", type=Path, help="New output directory; existing paths are rejected")
    parser.add_argument("--asset", help="UR10e+Robotiq USD override")
    parser.add_argument("--friction", type=float, default=1.0)
    parser.add_argument("--max-force", type=float, default=200.0)
    args = parser.parse_args()
    if args.steps is None:
        args.steps = args.frames if args.headless else 0
    if args.steps < 0 or (args.headless and args.steps == 0):
        parser.error("--steps must be nonnegative; headless requires a positive limit")
    if args.frames < 1:
        parser.error("--frames must be positive")
    output = args.output or Path(__file__).resolve().parent / "output" / str(time.time_ns())
    output.mkdir(parents=True, exist_ok=False)
    from isaacsim import SimulationApp
    # SimulationApp은 Python에서 Isaac Sim의 Kit 애플리케이션을 시작하고 갱신·종료하는 클래스이다.
    # headless=True는 창 없이 실행한다는 뜻이며, omni와 Isaac Sim 확장 모듈은 앱 생성 후 import한다.
    app = SimulationApp({"headless": args.headless})
    try:
        from pxr import Usd, UsdGeom, UsdPhysics
        # pxr은 USD 장면을 직접 다루는 OpenUSD의 Python 바인딩이다.
        # Usd는 Stage, Prim, 참조·variant 등의 USD 장면 구성 API를 다룬다.
        # UsdGeom은 형상, 변환, 카메라와 장면 단위·축 설정을 다룬다.
        # UsdPhysics는 강체·충돌·관절·물리 재질의 USD 스키마를 다룬다.
        from isaacsim.core.api import World
        # World는 Stage의 객체와 작업을 관리하고 물리·렌더링 시간 간격, 초기화, 시뮬레이션 진행을 제어한다.
        from isaacsim.core.utils.stage import add_reference_to_stage
        # add_reference_to_stage는 외부 USD 자산을 현재 Stage의 지정한 Prim 경로에 참조로 연결한다.
        from isaacsim.storage.native import get_assets_root_path
        # get_assets_root_path는 Isaac Sim 기본 자산의 루트 경로를 찾는다.
        # 반환 경로에 로봇·환경 USD의 상대 경로를 붙여 사용할 수 있다.
        world = World(stage_units_in_meters=1.0)
        asset_root = get_assets_root_path() if not args.asset else None
        if not args.asset and not asset_root:
            raise RuntimeError("Isaac 5.1 asset root unavailable; pass --asset /absolute/path/ur_gripper.usd")
        asset = args.asset or asset_root + "/Isaac/Samples/Rigging/Manipulator/import_manipulator/ur10e/ur/ur_gripper.usd"
        root = add_reference_to_stage(usd_path=asset, prim_path="/ur")
        if not root.GetChildren():
            raise RuntimeError(f"Robot asset did not resolve: {asset}")

        from pxr import PhysxSchema, UsdShade
        # pxr은 USD 장면을 직접 다루는 OpenUSD의 Python 바인딩이다.
        # PhysxSchema는 PhysX 전용 물리 설정을 USD Prim에 기록하는 스키마를 다룬다.
        # UsdShade는 셰이더·재질과 형상에 대한 재질 연결을 다룬다.
        if args.friction < 0 or args.max_force <= 0:
            raise ValueError("Friction must be nonnegative and max force positive")
        # 인스턴스 내부의 collider를 편집할 수 있도록 현재 layer에서만 해제한다.
        for prim in list(Usd.PrimRange(root)):
            if prim.IsInstance():
                # Prim의 instanceable 여부를 설정하여 참조한 자산의 인스턴싱 사용을 제어한다.
                prim.SetInstanceable(False)
        roots = [prim for prim in Usd.PrimRange(root) if prim.HasAPI(UsdPhysics.ArticulationRootAPI)]
        if len(roots) != 1:
            raise RuntimeError(f"Expected one articulation, found {len(roots)}")
        articulation = PhysxSchema.PhysxArticulationAPI.Apply(roots[0])
        articulation.CreateArticulationEnabledAttr(True)
        articulation.CreateSolverPositionIterationCountAttr(64)
        articulation.CreateSolverVelocityIterationCountAttr(4)
        articulation.CreateSleepThresholdAttr(0.00005)
        articulation.CreateStabilizationThresholdAttr(0.00001)
        fingers = [prim for prim in Usd.PrimRange(root) if prim.GetName() == "finger_joint" and prim.IsA(UsdPhysics.Joint)]
        if len(fingers) != 1:
            raise RuntimeError(f"Expected one finger_joint, found {len(fingers)}")
        drive = UsdPhysics.DriveAPI.Get(fingers[0], "angular")
        if not drive:
            raise RuntimeError("finger_joint has no angular drive")
        drive.CreateMaxForceAttr(args.max_force)
        material = UsdShade.Material.Define(world.stage, "/ur/Looks/FingerPhysics")
        physics = UsdPhysics.MaterialAPI.Apply(material.GetPrim())
        physics.CreateStaticFrictionAttr(args.friction)
        physics.CreateDynamicFrictionAttr(args.friction)
        colliders = [prim for prim in Usd.PrimRange(root) if prim.HasAPI(UsdPhysics.CollisionAPI)
                     and any(name in str(prim.GetPath()) for name in ["left_inner_finger", "right_inner_finger"])]
        if len(colliders) < 2:
            raise RuntimeError("Both finger tip colliders must be present; inspect your asset hierarchy")
        for collider in colliders:
            # Prim에 재질 연결 API를 적용한다. 이어지는 Bind에서 실제 사용할 재질을 지정한다.
            UsdShade.MaterialBindingAPI.Apply(collider).Bind(material, materialPurpose="physics")
        report = {"articulation": str(roots[0].GetPath()), "solver_position_iterations": articulation.GetSolverPositionIterationCountAttr().Get(),
                  "solver_velocity_iterations": articulation.GetSolverVelocityIterationCountAttr().Get(),
                  "finger_joint": str(fingers[0].GetPath()), "max_force": drive.GetMaxForceAttr().Get(),
                  "friction": physics.GetStaticFrictionAttr().Get(), "material_bound_colliders": [str(p.GetPath()) for p in colliders]}
        # World가 사용하는 Stage의 루트 레이어를 USD 파일로 저장한다.
        world.stage.GetRootLayer().Export(str(output / "configured.usda"))
        (output / "configuration_report.json").write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2), "output=", output)
        frame = 0
        while app.is_running() and (args.steps == 0 or frame < args.steps):
            # Kit의 한 프레임을 갱신하여 렌더링·이벤트·비동기 작업을 처리한다.
            # 물리 진행 여부는 현재 타임라인의 재생 상태와 설정에 따라 달라진다.
            app.update()
            frame += 1
    finally:
        # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
        app.close()


if __name__ == "__main__":
    main()
