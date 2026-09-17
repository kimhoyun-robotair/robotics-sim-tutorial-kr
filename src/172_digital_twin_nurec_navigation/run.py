"""Load a real local NuRec scene and run the official Nova Carter navigation graph."""
import argparse
from itertools import count
import json
from pathlib import Path


def main():
    package = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--scenario", choices=["cafe", "galileo", "wormhole", "lounge"], default="cafe")
    parser.add_argument("--steps", type=int, default=None, help="GUI: omitted keeps the window open; headless default: 500")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--output", type=Path, default=package / "output")
    parser.add_argument("--check", action="store_true", help="Check dataset paths without starting Kit")
    args = parser.parse_args()
    if args.steps is None and args.headless:
        args.steps = 500
    config = json.loads((package / "scenarios.json").read_text())[args.scenario]
    scene = args.dataset.expanduser().resolve() / config["stage"]
    if not scene.is_file():
        parser.error(f"NuRec dataset scene is missing: {scene}")
    if args.steps is not None and args.steps < 1:
        parser.error("steps must be positive")
    if args.check:
        print(json.dumps({"scene": str(scene), **config}, indent=2))
        print("Local root scene exists; referenced resources, GPU rendering, and navigation are not verified")
        return
    output = args.output.expanduser().resolve()
    if output.exists():
        parser.error(f"Output exists; use another path: {output}")
    from isaacsim import SimulationApp
    # SimulationApp은 Python에서 Isaac Sim의 Kit 애플리케이션을 시작하고 갱신·종료하는 클래스이다.
    # headless=True는 창 없이 실행한다는 뜻이며, omni와 Isaac Sim 확장 모듈은 앱 생성 후 import한다.
    app = SimulationApp({"headless": args.headless})
    try:
        import carb
        # carb는 Kit 기반 실행 환경의 설정·로그 등 공통 기능을 제공하는 Carbonite 바인딩이다.
        import omni.kit.commands
        # omni.kit.commands는 이름으로 등록된 Kit 명령을 실행하는 모듈이다.
        # execute에 명령 이름과 인자를 전달해 Prim 생성·가져오기 등의 작업을 수행한다.
        import omni.timeline
        # omni.timeline은 시뮬레이션 시간과 재생·일시정지·정지를 제어하는 API이다.
        import omni.usd
        # omni.usd는 현재 Kit 애플리케이션의 USD 문맥에 접근하는 모듈이다.
        # get_context().get_stage()로 객체·조명 등이 들어 있는 현재 Stage를 얻는다.
        from isaacsim.core.utils.stage import add_reference_to_stage
        # add_reference_to_stage는 외부 USD 자산을 현재 Stage의 지정한 Prim 경로에 참조로 연결한다.
        from isaacsim.storage.native import get_assets_root_path
        # get_assets_root_path는 Isaac Sim 기본 자산의 루트 경로를 찾는다.
        # 반환 경로에 로봇·환경 USD의 상대 경로를 붙여 사용할 수 있다.
        from pxr import PhysxSchema, UsdGeom, UsdPhysics
        # pxr은 USD 장면을 직접 다루는 OpenUSD의 Python 바인딩이다.
        # PhysxSchema는 PhysX 전용 물리 설정을 USD Prim에 기록하는 스키마를 다룬다.
        # UsdGeom은 형상, 변환, 카메라와 장면 단위·축 설정을 다룬다.
        # UsdPhysics는 강체·충돌·관절·물리 재질의 USD 스키마를 다룬다.
        context = omni.usd.get_context()
        if not context.open_stage(str(scene)):
            raise RuntimeError(f"Failed to open NuRec scene: {scene}")
        # Kit의 한 프레임을 갱신하여 렌더링·이벤트·비동기 작업을 처리한다.
        # 물리 진행 여부는 현재 타임라인의 재생 상태와 설정에 따라 달라진다.
        app.update()
        stage = context.get_stage()
        # Stage의 Prim 계층을 순회하여 형상·관절·스키마 정보를 검사한다.
        for prim in stage.Traverse():
            if prim.IsA(UsdPhysics.Scene):
                PhysxSchema.PhysxSceneAPI.Apply(prim).GetUpdateTypeAttr().Set("Synchronous")
                break
        else:
            # 중력 등 물리 시뮬레이션의 공통 설정을 저장할 PhysicsScene을 정의한다.
            physics = UsdPhysics.Scene.Define(stage, "/World/PhysicsScene")
            PhysxSchema.PhysxSceneAPI.Apply(physics.GetPrim()).CreateUpdateTypeAttr("Synchronous")
        assets = get_assets_root_path()
        if not assets:
            raise RuntimeError("Isaac Sim asset root unavailable")
        carb.settings.get_settings().set_bool("/app/omni.graph.scriptnode/opt_in", True)
        robot_path = "/World/NovaCarterNav"
        robot = add_reference_to_stage(assets + "/Isaac/Samples/Replicator/OmniGraph/nova_carter_nav_only.usd", robot_path)
        app.update()
        target = stage.GetPrimAtPath(robot_path + "/targetXform")
        chassis = stage.GetPrimAtPath(robot_path + "/chassis_link")
        if not target.IsValid() or not chassis.IsValid():
            raise RuntimeError("Carter target/chassis is missing from the referenced navigation asset")
        for prim, position in [(robot, config["start"]), (target, config["relative_target"])]:
            attr = prim.GetAttribute("xformOp:translate")
            if not attr:
                # Prim의 변환 연산에 접근한다. AddTranslateOp·AddRotateXYZOp·AddScaleOp로 이동·회전·스케일을 기록할 수 있다.
                attr = UsdGeom.Xformable(prim).AddTranslateOp().GetAttr()
            attr.Set(tuple(position))
        if config["collision_ground"]:
            path = "/World/CollisionPlane"
            omni.kit.commands.execute("CreateMeshPrimWithDefaultXform", prim_path=path, prim_type="Plane")
            plane = stage.GetPrimAtPath(path)
            plane.GetAttribute("xformOp:scale").Set((10, 10, 1))
            plane.GetAttribute("xformOp:translate").Set(tuple(config["start"]))
            plane.GetAttribute("visibility").Set("invisible")
            # 형상 Prim에 충돌 API를 적용하여 접촉 계산에 참여하게 한다.
            UsdPhysics.CollisionAPI.Apply(plane).CreateCollisionEnabledAttr(True)
        timeline = omni.timeline.get_timeline_interface()
        timeline.play()
        records = []
        for step in count():
            if args.steps is not None and step >= args.steps:
                break
            if not app.is_running():
                break
            app.update()
            if not app.is_running():
                break
            if step % 10 == 0 or (args.steps is not None and step == args.steps - 1):
                position = UsdGeom.Xformable(chassis).ComputeLocalToWorldTransform(0).ExtractTranslation()
                records.append({"step": step, "timeline_seconds": timeline.get_current_time(),
                                "chassis_world_position": list(position)})
        if app.is_running():
            timeline.pause()
        output.mkdir(parents=True, exist_ok=False)
        (output / "trajectory.json").write_text(json.dumps(records, indent=2) + "\n")
        print(f"Recorded {len(records)} observed chassis positions at {output}; assess goal reach from trajectory")
    finally:
        # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
        app.close()


if __name__ == "__main__":
    main()
