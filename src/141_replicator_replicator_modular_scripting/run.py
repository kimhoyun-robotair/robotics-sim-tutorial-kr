"""Attach real prim behaviors, edit exposed USD attributes, and capture their results."""
import argparse
import asyncio
import inspect
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--frames', type=int, default=8)
    parser.add_argument('--interval', type=int, default=3)
    parser.add_argument('--stack', action='store_true', help='Also run the built-in event-based VolumeStackRandomizer')
    parser.add_argument('--headless', action='store_true')
    parser.add_argument('--output', type=Path, default=Path(__file__).parent / 'output')
    parser.add_argument("--steps", type=int, default=None,
                        help="GUI app updates after generation; omitted: keep GUI open; headless: no inspection")
    args = parser.parse_args()
    if args.steps is not None and args.steps < 1:
        parser.error("--steps must be positive")
    if args.frames < 1 or args.interval < 0:
        parser.error('frames must be positive and interval nonnegative')
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    from isaacsim import SimulationApp
    # SimulationApp은 Python에서 Isaac Sim의 Kit 애플리케이션을 시작하고 갱신·종료하는 클래스이다.
    # headless=True는 창 없이 실행한다는 뜻이며, omni와 Isaac Sim 확장 모듈은 앱 생성 후 import한다.
    app = SimulationApp({'headless': args.headless})
    task = None
    try:
        import carb.settings
        # carb.settings는 경로 형태의 키로 Kit의 렌더링·시뮬레이션 설정을 읽고 변경하는 API이다.
        import numpy as np
        import omni.kit.app
        # omni.kit.app은 현재 Kit 앱과 확장 관리자에 접근하며 비동기 프레임 갱신을 기다리는 기능을 제공한다.
        import omni.replicator.core as rep
        # omni.replicator.core는 장면 무작위화와 합성 데이터 생성을 위한 API이다.
        # render product는 카메라의 렌더링 출력이며, annotator는 데이터를 추출하고 writer는 결과를 저장한다.
        import omni.timeline
        # omni.timeline은 시뮬레이션 시간과 재생·일시정지·정지를 제어하는 API이다.
        import omni.usd
        # omni.usd는 현재 Kit 애플리케이션의 USD 문맥에 접근하는 모듈이다.
        # get_context().get_stage()로 객체·조명 등이 들어 있는 현재 Stage를 얻는다.
        from isaacsim.core.utils.extensions import enable_extension
        # enable_extension은 이름으로 지정한 Kit 확장을 활성화하여 해당 기능과 명령을 사용할 수 있게 한다.
        from PIL import Image
        from pxr import Gf, Sdf, UsdGeom, UsdLux
        # pxr은 USD 장면을 직접 다루는 OpenUSD의 Python 바인딩이다.
        # Gf는 벡터·행렬·쿼터니언 등 위치와 회전을 계산하는 수학 자료형을 다룬다.
        # Sdf는 USD 경로, 레이어, 속성 값의 자료형을 다룬다.
        # UsdGeom은 형상, 변환, 카메라와 장면 단위·축 설정을 다룬다.
        # UsdLux는 조명 Prim과 빛의 속성을 다룬다.
        carb.settings.get_settings().set_bool('/app/scripting/ignoreWarningDialog', True)
        enable_extension('isaacsim.replicator.behavior')
        from isaacsim.replicator.behavior.behaviors import LightRandomizer, LocationRandomizer, LookAtBehavior, RotationRandomizer, TextureRandomizer, VolumeStackRandomizer
        # LightRandomizer는 조명 속성을 무작위로 바꾸는 Replicator behavior이다.
        # LocationRandomizer는 객체 위치를 무작위로 바꾸는 behavior이다.
        # LookAtBehavior는 객체가 지정한 대상을 바라보게 하는 behavior이다.
        # RotationRandomizer는 객체 회전을 무작위로 바꾸는 behavior이다.
        # TextureRandomizer는 재질 텍스처를 무작위로 바꾸는 behavior이다.
        # VolumeStackRandomizer는 지정한 공간에서 물체를 쌓는 배치를 생성하는 behavior이다.
        from isaacsim.replicator.behavior.utils.behavior_utils import add_behavior_script_with_parameters_async, publish_event_and_wait_for_completion_async
        # add_behavior_script_with_parameters_async는 Prim에 behavior 스크립트와 매개변수를 비동기로 연결한다.
        # publish_event_and_wait_for_completion_async는 작업 이벤트를 보내고 완료 이벤트를 비동기로 기다린다.

        async def attach(prim, cls, parameters):
            prefix = f'exposedVar:{cls.BEHAVIOR_NS}:'
            await add_behavior_script_with_parameters_async(prim, inspect.getfile(cls), {prefix + k: v for k, v in parameters.items()})

        async def run():
            await omni.usd.get_context().new_stage_async()
            stage = omni.usd.get_context().get_stage()
            # USD 장면에서 위쪽으로 사용할 축을 지정한다.
            UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
            # USD 좌표 한 단위가 몇 미터인지 지정하여 장면의 길이 단위를 맞춘다.
            UsdGeom.SetStageMetersPerUnit(stage, 1.0)
            # USD Stage에 Cube 형상을 직접 정의한다. 물리 동작이 필요하면 강체·충돌 API를 별도로 적용한다.
            cube = UsdGeom.Cube.Define(stage, '/World/Target')
            cube.CreateSizeAttr(0.6)
            # Prim의 변환 연산에 접근한다. AddTranslateOp·AddRotateXYZOp·AddScaleOp로 이동·회전·스케일을 기록할 수 있다.
            UsdGeom.Xformable(cube).AddTranslateOp().Set((0, 0, 1))
            moving = UsdGeom.Sphere.Define(stage, '/World/Moving')
            moving.CreateRadiusAttr(0.2)
            UsdGeom.Xformable(moving).AddTranslateOp().Set((0, 0, 1.8))
            floor = UsdGeom.Cube.Define(stage, '/World/Floor')
            floor.CreateSizeAttr(1)
            UsdGeom.Xformable(floor).AddScaleOp().Set((4, 4, 0.1))
            light = UsdLux.SphereLight.Define(stage, '/World/Light')
            light.CreateIntensityAttr(15000)
            light.CreateRadiusAttr(0.2)
            UsdGeom.Xformable(light).AddTranslateOp().Set((1, 1, 4))
            # USD 카메라 Prim을 정의한다. 센서 이미지 출력은 별도의 render product나 Camera API로 연결한다.
            camera = UsdGeom.Camera.Define(stage, '/World/Camera')
            UsdGeom.Xformable(camera).AddTranslateOp().Set((4, 4, 3))
            texture_paths = []
            for index, color in enumerate([(230, 170, 50), (40, 110, 210)]):
                texture = np.full((64, 64, 3), color, dtype=np.uint8)
                texture[::8] = 255
                texture[:, ::8] = 255
                path = output / f'grid_{index}.png'
                Image.fromarray(texture).save(path)
                texture_paths.append(path.as_uri())
            await attach(cube.GetPrim(), RotationRandomizer, {'interval': args.interval})
            await attach(cube.GetPrim(), LocationRandomizer, {
                'interval': args.interval, 'range:minPosition': Gf.Vec3d(-0.2, -0.2, -0.1),
                'range:maxPosition': Gf.Vec3d(0.2, 0.2, 0.1)})
            await attach(cube.GetPrim(), TextureRandomizer, {'interval': args.interval, 'textures:csv': ','.join(texture_paths)})
            await attach(light.GetPrim(), LightRandomizer, {'interval': args.interval, 'range:intensity': Gf.Vec2f(8000, 30000)})
            await attach(camera.GetPrim(), LookAtBehavior, {'targetPrimPath': '/World/Target'})
            await add_behavior_script_with_parameters_async(
                moving.GetPrim(), str(Path(__file__).parent.resolve() / 'orbit_behavior.py'), {'exposedVar:orbit:radius': 0.8})
            if args.stack:
                from isaacsim.storage.native import get_assets_root_path
                # get_assets_root_path는 Isaac Sim 기본 자산의 루트 경로를 찾는다.
                # 반환 경로에 로봇·환경 USD의 상대 경로를 붙여 사용할 수 있다.
                root = get_assets_root_path()
                if not root:
                    raise RuntimeError('Volume stacking needs the Isaac Sim 5.1 asset library')
                pallet = UsdGeom.Cube.Define(stage, '/World/StackSurface')
                pallet.CreateSizeAttr(1)
                UsdGeom.Xformable(pallet).AddTranslateOp().Set((-2, 0, 0.1))
                UsdGeom.Xformable(pallet).AddScaleOp().Set((1.5, 1.5, 0.2))
                assets = root + '/Isaac/Environments/Simple_Warehouse/Props/SM_CardBoxC_01.usd'
                await attach(pallet.GetPrim(), VolumeStackRandomizer, {'assets:csv': assets, 'assets:numRange': Gf.Vec2i(2, 3)})
                for action, state_name, maximum in [('reset', 'RESET', 30), ('setup', 'SETUP', 500), ('run', 'FINISHED', 1500)]:
                    ok = await publish_event_and_wait_for_completion_async(
                        publish_payload={'prim_path': '/World/StackSurface', 'action': action},
                        expected_payload={'prim_path': '/World/StackSurface', 'state_name': state_name},
                        publish_event_name=VolumeStackRandomizer.EVENT_NAME_IN,
                        subscribe_event_name=VolumeStackRandomizer.EVENT_NAME_OUT, max_wait_updates=maximum)
                    if not ok:
                        raise TimeoutError(f'Stacking did not reach {state_name}')
            # 타임라인 재생에 따른 자동 캡처 여부를 설정한다. False이면 아래의 명시적 캡처 호출로 제어한다.
            rep.orchestrator.set_capture_on_play(False)
            # 카메라와 해상도를 연결한 render product를 만든다. 이후 annotator나 writer를 여기에 연결한다.
            product = rep.create.render_product('/World/Camera', (480, 360))
            # 등록된 writer를 이름으로 선택한다. initialize로 출력 설정을 지정한 뒤 render product에 연결한다.
            writer = rep.WriterRegistry.get('BasicWriter')
            writer.initialize(output_dir=str(output / 'rgb'), rgb=True)
            # writer를 render product에 연결하여 캡처한 데이터가 writer로 전달되게 한다.
            writer.attach(product)
            timeline = omni.timeline.get_timeline_interface()
            timeline.play()
            await omni.kit.app.get_app().next_update_async()
            ok = await publish_event_and_wait_for_completion_async(
                publish_payload={'prim_path': '/World/Moving'},
                expected_payload={'prim_path': '/World/Moving', 'state_name': 'RANDOMIZED'},
                publish_event_name='lesson.orbit.randomize', subscribe_event_name='lesson.orbit.done', max_wait_updates=30)
            if not ok:
                raise TimeoutError('Local orbit behavior did not acknowledge the event')
            records = []
            for frame in range(args.frames):
                await omni.kit.app.get_app().next_update_async()
                # Replicator 캡처를 비동기로 진행하고 완료를 기다린다.
                await rep.orchestrator.step_async(rt_subframes=4, delta_time=0.0, pause_timeline=False)
                record = {'frame': frame, 'time_s': timeline.get_current_time(),
                          'target_position': list(cube.GetPrim().GetAttribute('xformOp:translate').Get()),
                          'orbit_position': list(moving.GetPrim().GetAttribute('xformOp:translate').Get()),
                          'light_intensity': light.GetIntensityAttr().Get()}
                records.append(record)
                print(json.dumps(record))
            # 합성 데이터 처리와 저장 작업이 끝날 때까지 비동기로 기다린다.
            await rep.orchestrator.wait_until_complete_async()
            # Stage의 루트 레이어를 USD 파일로 내보낸다. 참조 자산 자체를 모두 복사하는 것은 아니다.
            stage.GetRootLayer().Export(str(output / 'behaviors.usda'))
            (output / 'measurements.json').write_text(json.dumps(records, indent=2))
            timeline.stop()
            # writer와 render product의 연결을 해제한다.
            writer.detach()
            product.destroy()
        task = asyncio.ensure_future(run())
        while app.is_running() and not task.done():
            # Kit의 한 프레임을 갱신하여 렌더링·이벤트·비동기 작업을 처리한다.
            # 물리 진행 여부는 현재 타임라인의 재생 상태와 설정에 따라 달라진다.
            app.update()
        if not app.is_running():
            return
        task.result()
        inspection_updates = 0
        while not args.headless and app.is_running() and (args.steps is None or inspection_updates < args.steps):
            app.update()
            inspection_updates += 1
    finally:
        try:
            if task is not None and not task.done():
                task.cancel()
        finally:
            # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
            app.close()


if __name__ == '__main__':
    main()
