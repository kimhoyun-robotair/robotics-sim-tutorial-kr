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
    app = SimulationApp({'headless': args.headless})
    task = None
    try:
        import carb.settings
        import numpy as np
        import omni.kit.app
        import omni.replicator.core as rep
        import omni.timeline
        import omni.usd
        from isaacsim.core.utils.extensions import enable_extension
        from PIL import Image
        from pxr import Gf, Sdf, UsdGeom, UsdLux
        carb.settings.get_settings().set_bool('/app/scripting/ignoreWarningDialog', True)
        enable_extension('isaacsim.replicator.behavior')
        from isaacsim.replicator.behavior.behaviors import LightRandomizer, LocationRandomizer, LookAtBehavior, RotationRandomizer, TextureRandomizer, VolumeStackRandomizer
        from isaacsim.replicator.behavior.utils.behavior_utils import add_behavior_script_with_parameters_async, publish_event_and_wait_for_completion_async

        async def attach(prim, cls, parameters):
            prefix = f'exposedVar:{cls.BEHAVIOR_NS}:'
            await add_behavior_script_with_parameters_async(prim, inspect.getfile(cls), {prefix + k: v for k, v in parameters.items()})

        async def run():
            await omni.usd.get_context().new_stage_async()
            stage = omni.usd.get_context().get_stage()
            UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
            UsdGeom.SetStageMetersPerUnit(stage, 1.0)
            cube = UsdGeom.Cube.Define(stage, '/World/Target')
            cube.CreateSizeAttr(0.6)
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
            rep.orchestrator.set_capture_on_play(False)
            product = rep.create.render_product('/World/Camera', (480, 360))
            writer = rep.WriterRegistry.get('BasicWriter')
            writer.initialize(output_dir=str(output / 'rgb'), rgb=True)
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
                await rep.orchestrator.step_async(rt_subframes=4, delta_time=0.0, pause_timeline=False)
                record = {'frame': frame, 'time_s': timeline.get_current_time(),
                          'target_position': list(cube.GetPrim().GetAttribute('xformOp:translate').Get()),
                          'orbit_position': list(moving.GetPrim().GetAttribute('xformOp:translate').Get()),
                          'light_intensity': light.GetIntensityAttr().Get()}
                records.append(record)
                print(json.dumps(record))
            await rep.orchestrator.wait_until_complete_async()
            stage.GetRootLayer().Export(str(output / 'behaviors.usda'))
            (output / 'measurements.json').write_text(json.dumps(records, indent=2))
            timeline.stop()
            writer.detach()
            product.destroy()
        task = asyncio.ensure_future(run())
        while app.is_running() and not task.done():
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
            app.close()


if __name__ == '__main__':
    main()
