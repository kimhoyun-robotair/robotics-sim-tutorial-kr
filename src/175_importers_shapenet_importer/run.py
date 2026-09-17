"""Use the supported OBJ-to-USD converter; the included OBJ is an original fixture."""
import argparse
import asyncio
import time
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--obj', type=Path, default=Path(__file__).parent / 'sample.obj')
    parser.add_argument('--headless', action='store_true')
    parser.add_argument('--frames', type=int, default=120, help='Legacy headless preview updates; does not limit GUI lifetime')
    parser.add_argument('--steps', type=int, default=None, help='Preview updates after conversion; omitted keeps GUI open')
    parser.add_argument('--timeout', type=float, default=120)
    parser.add_argument('--output', type=Path, default=Path(__file__).parent / 'output')
    args = parser.parse_args()
    if args.steps is None and args.headless:
        args.steps = args.frames
    if args.steps is not None and args.steps < 1:
        parser.error('--steps must be positive')
    if not args.obj.is_file() or args.frames < 1 or args.timeout <= 0 or args.output.exists():
        parser.error('Existing OBJ, positive frames/timeout, and a new output directory are required')
    args.output.mkdir(parents=True)
    from isaacsim import SimulationApp
    # SimulationApp은 Python에서 Isaac Sim의 Kit 애플리케이션을 시작하고 갱신·종료하는 클래스이다.
    # headless=True는 창 없이 실행한다는 뜻이며, omni와 Isaac Sim 확장 모듈은 앱 생성 후 import한다.

    app = SimulationApp({'headless': args.headless})
    try:
        from isaacsim.core.utils.extensions import enable_extension
        # enable_extension은 이름으로 지정한 Kit 확장을 활성화하여 해당 기능과 명령을 사용할 수 있게 한다.
        from isaacsim.core.utils.stage import add_reference_to_stage, get_current_stage
        # add_reference_to_stage는 외부 USD 자산을 현재 Stage의 지정한 Prim 경로에 참조로 연결한다.
        # get_current_stage는 현재 Isaac Sim에서 열려 있는 USD Stage를 반환한다.
        enable_extension('omni.kit.asset_converter')
        import omni.kit.asset_converter
        # omni.kit.asset_converter는 OBJ 등의 모델을 USD로 변환하는 비동기 작업을 제공한다.
        from pxr import UsdGeom
        # pxr은 USD 장면을 직접 다루는 OpenUSD의 Python 바인딩이다.
        # UsdGeom은 형상, 변환, 카메라와 장면 단위·축 설정을 다룬다.
        converted = args.output.resolve() / 'converted.usd'
        context = omni.kit.asset_converter.AssetConverterContext()
        task = omni.kit.asset_converter.get_instance().create_converter_task(
            str(args.obj.resolve()), str(converted), None, context,
        )
        future = asyncio.ensure_future(task.wait_until_finished())
        deadline = time.monotonic() + args.timeout
        while not future.done():
            if time.monotonic() > deadline or not app.is_running():
                future.cancel()
                raise TimeoutError('OBJ conversion did not complete within the requested timeout')
            # Kit의 한 프레임을 갱신하여 렌더링·이벤트·비동기 작업을 처리한다.
            # 물리 진행 여부는 현재 타임라인의 재생 상태와 설정에 따라 달라진다.
            app.update()
        if not future.result():
            raise RuntimeError(f'OBJ conversion failed: {task.get_error_message()}')
        add_reference_to_stage(str(converted), '/World/Imported')
        stage = get_current_stage()
        # Stage의 Prim 계층을 순회하여 형상·관절·스키마 정보를 검사한다.
        meshes = [str(prim.GetPath()) for prim in stage.Traverse() if prim.IsA(UsdGeom.Mesh)]
        if not meshes:
            raise RuntimeError('Conversion produced no meshes')
        print('Converted mesh prims:', meshes)
        step = 0
        while app.is_running() and (args.steps is None or step < args.steps):
            app.update()
            step += 1
    finally:
        # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
        app.close()


if __name__ == '__main__':
    main()
