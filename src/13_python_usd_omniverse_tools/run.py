import argparse
from itertools import count
from datetime import datetime
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Commands")
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
        import omni.kit.actions.core
        # omni.kit.actions.core는 Kit action을 등록하고 이름으로 찾아 실행하는 API이다.
        import omni.kit.commands
        # omni.kit.commands는 이름으로 등록된 Kit 명령을 실행하는 모듈이다.
        # execute에 명령 이름과 인자를 전달해 Prim 생성·가져오기 등의 작업을 수행한다.
        import omni.kit.undo
        # omni.kit.undo는 명령 기록에 대한 실행 취소와 다시 실행을 제공한다.
        import omni.usd
        # omni.usd는 현재 Kit 애플리케이션의 USD 문맥에 접근하는 모듈이다.
        # get_context().get_stage()로 객체·조명 등이 들어 있는 현재 Stage를 얻는다.
        from pxr import Gf, UsdGeom
        # pxr은 USD 장면을 직접 다루는 OpenUSD의 Python 바인딩이다.
        # Gf는 벡터·행렬·쿼터니언 등 위치와 회전을 계산하는 수학 자료형을 다룬다.
        # UsdGeom은 형상, 변환, 카메라와 장면 단위·축 설정을 다룬다.

        stage = omni.usd.get_context().get_stage()
        success, path = omni.kit.commands.execute(
            "CreateMeshPrimCommand", prim_type="Cube"
        )
        if not success:
            raise RuntimeError(
                "CreateMeshPrimCommand failed; enable the mesh primitive extension"
            )
        prim = stage.GetPrimAtPath(path)
        color = UsdGeom.Gprim(prim).CreateDisplayColorAttr([Gf.Vec3f(1, 0, 0)])
        registry = omni.kit.actions.core.get_action_registry()
        extension_id = "tutorial.commands.local"
        action_id = "make_blue"

        def make_blue():
            success, _ = omni.kit.commands.execute(
                "ChangeProperty",
                prop_path=color.GetPath(),
                value=[Gf.Vec3f(0, 0, 1)],
                prev=color.Get(),
            )
            if not success:
                raise RuntimeError("ChangeProperty failed")

        registry.register_action(extension_id, action_id, make_blue)
        try:
            before = list(color.Get()[0])
            omni.kit.actions.core.execute_action(extension_id, action_id)
            changed = list(color.Get()[0])
            omni.kit.undo.undo()
            undone = list(color.Get()[0])
            omni.kit.undo.redo()
            redone = list(color.Get()[0])
            if (before, changed, undone, redone) != (
                [1, 0, 0],
                [0, 0, 1],
                [1, 0, 0],
                [0, 0, 1],
            ):
                raise RuntimeError(
                    "Command undo/redo did not restore the expected colors"
                )
            report = {
                "prim_path": str(path),
                "before": before,
                "after_action": changed,
                "after_undo": undone,
                "after_redo": redone,
            }
            (output / "command_history.json").write_text(json.dumps(report, indent=2))
            # Stage의 루트 레이어를 USD 파일로 내보낸다. 참조 자산 자체를 모두 복사하는 것은 아니다.
            stage.GetRootLayer().Export(str(output / "commands.usda"))
            for step in count():
                if not app.is_running() or (args.steps is not None and step >= args.steps):
                    break
                # Kit의 한 프레임을 갱신하여 렌더링·이벤트·비동기 작업을 처리한다.
                # 물리 진행 여부는 현재 타임라인의 재생 상태와 설정에 따라 달라진다.
                app.update()
        finally:
            registry.deregister_action(extension_id, action_id)
        print(json.dumps(report, indent=2))
        print(f"Outputs: {output.resolve()}")
    finally:
        # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
        app.close()


if __name__ == "__main__":
    main()
