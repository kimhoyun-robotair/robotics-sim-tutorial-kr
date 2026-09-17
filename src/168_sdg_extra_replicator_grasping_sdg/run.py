"""Generate and physically evaluate antipodal grasps with Isaac Sim 5.1 GraspingManager."""
import argparse
from pathlib import Path


def main():
    package = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=package / "grasp_config.yaml")
    parser.add_argument("--scene", default="https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/5.1/Isaac/Samples/Replicator/Stage/sdg_grasping_xarm.usd")
    parser.add_argument("--output", type=Path, default=package / "output" / "grasps_01")
    parser.add_argument("--samples", type=int, default=5)
    parser.add_argument("--steps", type=int, default=None, help="Kit update limit; omitted: GUI until closed, headless evaluation limit 10000")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--physics-scene", help="Optional existing PhysicsScene prim for isolated evaluation")
    parser.add_argument("--timeline", action="store_true", help="Use timeline rather than direct physics steps")
    args = parser.parse_args()
    if args.steps is None and args.headless:
        args.steps = 10000
    if args.samples < 1 or (args.steps is not None and args.steps < 1):
        parser.error("--samples and --steps must be positive")
    output = args.output.expanduser().resolve()
    if output.exists():
        parser.error("Choose a new --output directory")
    if not args.config.is_file():
        parser.error("Config file does not exist")
    from isaacsim import SimulationApp
    # SimulationApp은 Python에서 Isaac Sim의 Kit 애플리케이션을 시작하고 갱신·종료하는 클래스이다.
    # headless=True는 창 없이 실행한다는 뜻이며, omni와 Isaac Sim 확장 모듈은 앱 생성 후 import한다.
    app = SimulationApp({"headless": args.headless})
    manager = None
    task = None
    try:
        import asyncio
        import json
        import omni.kit.app
        # omni.kit.app은 현재 Kit 앱과 확장 관리자에 접근하며 비동기 프레임 갱신을 기다리는 기능을 제공한다.
        import omni.usd
        # omni.usd는 현재 Kit 애플리케이션의 USD 문맥에 접근하는 모듈이다.
        # get_context().get_stage()로 객체·조명 등이 들어 있는 현재 Stage를 얻는다.
        from pxr import UsdPhysics
        # pxr은 USD 장면을 직접 다루는 OpenUSD의 Python 바인딩이다.
        # UsdPhysics는 강체·충돌·관절·물리 재질의 USD 스키마를 다룬다.
        extensions = omni.kit.app.get_app().get_extension_manager()
        extensions.set_extension_enabled_immediate("isaacsim.replicator.grasping", True)
        from isaacsim.replicator.grasping.grasping_manager import GraspingManager
        # GraspingManager는 grasping 합성 데이터 예제에서 잡기 후보 생성과 평가 작업을 관리한다.
        # USD 파일을 Kit의 현재 Stage로 연다.
        if not omni.usd.get_context().open_stage(args.scene):
            raise RuntimeError(f"Could not open grasping stage: {args.scene}")
        stage = omni.usd.get_context().get_stage()
        if args.physics_scene and not stage.GetPrimAtPath(args.physics_scene).IsA(UsdPhysics.Scene):
            raise ValueError("--physics-scene must name an existing PhysicsScene")
        manager = GraspingManager()
        statuses = manager.load_config(str(args.config.resolve()))
        failures = {key: value for key, value in statuses.items() if value.startswith(("Failed", "Error"))}
        if failures:
            raise RuntimeError(f"Invalid grasp configuration: {failures}")
        if not manager.get_object_prim_path() or not manager.gripper_path:
            raise ValueError("Gripper and target object must both exist")
        manager.sampler_config["num_candidates"] = args.samples
        # 설정한 물체와 그리퍼를 사용해 잡기 자세 후보를 생성한다. 후보 생성만으로 잡기 성공이 보장되지는 않는다.
        if not manager.generate_grasp_poses() or not manager.grasp_locations:
            raise RuntimeError("Antipodal sampler produced no candidates")
        # 생성한 잡기 자세를 읽는다. in_world_frame=True이면 월드 좌표계 기준의 자세를 반환한다.
        poses = manager.get_grasp_poses(in_world_frame=True)[:args.samples]
        if not poses:
            raise RuntimeError("No world-space grasp poses are available")
        output.mkdir(parents=True)
        manager.store_initial_gripper_pose()
        manager.set_results_output_dir(str(output))
        manager.set_overwrite_results_output(False)
        # 잡기 자세 후보들을 물리 시뮬레이션으로 평가하는 비동기 작업을 시작한다.
        task = asyncio.ensure_future(manager.evaluate_grasp_poses(
            grasp_poses=poses, render=True, physics_scene_path=args.physics_scene,
            isolate_simulation=bool(args.physics_scene), simulate_using_timeline=args.timeline,
        ))
        step = 0
        while not task.done() and (args.steps is None or step < args.steps):
            if not app.is_running():
                raise RuntimeError("Application closed before evaluation finished")
            # Kit의 한 프레임을 갱신하여 렌더링·이벤트·비동기 작업을 처리한다.
            # 물리 진행 여부는 현재 타임라인의 재생 상태와 설정에 따라 달라진다.
            app.update()
            step += 1
        if not task.done():
            raise TimeoutError("Evaluation exceeded --steps; partial output is retained")
        task.result()
        captures = sorted(output.glob("capture_*.yaml"))
        if len(captures) != len(poses):
            raise RuntimeError(f"Expected {len(poses)} pose records, got {len(captures)}")
        summary = {"sampled_poses":len(manager.grasp_locations), "evaluated_poses":len(poses),
                   "result_files":[path.name for path in captures],
                   "interpretation":"Gripper state records; no automatic grasp-success label is inferred."}
        (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        print(json.dumps(summary, indent=2), flush=True)
        if not args.headless:
            while app.is_running() and (args.steps is None or step < args.steps):
                app.update()
                step += 1
    finally:
        try:
            if task is not None and not task.done():
                task.cancel()
            if manager is not None:
                manager.clear()
        finally:
            # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
            app.close()


if __name__ == "__main__":
    main()
