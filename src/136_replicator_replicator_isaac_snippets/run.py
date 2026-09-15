"""Replicator camera, timing, event, motion-blur, and Cosmos writer exercises."""
import argparse
import json
from pathlib import Path
import re
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--example', choices=['multi-camera', 'settled', 'custom-event', 'motion-blur', 'events', 'custom-fps', 'cosmos'], default='multi-camera')
    parser.add_argument('--frames', type=int, default=3)
    parser.add_argument('--steps', type=int, default=None, help="Maximum physics/app updates for settled/events mode; omitted: 600 for capture, then GUI stays open")
    parser.add_argument('--stage-fps', type=int, default=60)
    parser.add_argument('--sensor-fps', type=int, default=10)
    parser.add_argument('--renderer', choices=['rt', 'pt'], default='rt')
    parser.add_argument('--subsamples', type=int, default=8)
    parser.add_argument('--headless', action='store_true')
    parser.add_argument('--output', type=Path, default=Path(__file__).parent / 'output')
    args = parser.parse_args()
    keep_open = args.steps is None and not args.headless
    capture_steps = args.steps if args.steps is not None else 600
    if min(args.frames, capture_steps, args.stage_fps, args.sensor_fps, args.subsamples) < 1:
        parser.error('Counts and rates must be positive')
    if args.sensor_fps > args.stage_fps or args.stage_fps % args.sensor_fps:
        parser.error('stage-fps must be an integer multiple of sensor-fps')
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    from isaacsim import SimulationApp
    app = SimulationApp({'headless': args.headless})
    try:
        import carb.eventdispatcher
        import carb.settings
        import numpy as np
        import omni.kit.app
        import omni.physx
        import omni.replicator.core as rep
        import omni.timeline
        import omni.usd
        from isaacsim.core.api import World
        from isaacsim.core.api.objects import DynamicCuboid
        from isaacsim.core.utils.semantics import add_labels
        from PIL import Image
        from pxr import Gf, PhysxSchema, Usd, UsdGeom, UsdPhysics
        omni.usd.get_context().new_stage()
        stage = omni.usd.get_context().get_stage()
        settings = carb.settings.get_settings()
        settings.set_bool('/app/omni.graph.scriptnode/opt_in', True)
        rep.orchestrator.set_capture_on_play(False)
        rep.settings.set_stage_up_axis('Z')
        rep.settings.set_stage_meters_per_unit(1.0)
        rep.create.light(light_type='dome', intensity=800)
        rep.create.light(light_type='distant', rotation=(315, 0, 0), intensity=1800)
        world = None
        body = None
        if args.example in ['settled', 'custom-fps', 'events']:
            world = World(stage_units_in_meters=1.0, physics_dt=1 / args.stage_fps, rendering_dt=1 / args.stage_fps)
            world.scene.add_default_ground_plane()
            body = world.scene.add(DynamicCuboid(prim_path='/World/FallingCube', name='falling_cube', position=np.array([0, 0, 2]), scale=np.array([0.5, 0.5, 0.5]), size=1.0))
            add_labels(body.prim, labels=['cube'], instance_name='class')
            world.reset()
        elif args.example == 'cosmos':
            floor = rep.functional.create.plane(scale=(5, 5, 1), semantics={'class': 'floor'})
            rep.functional.physics.apply_collider(floor)
            cube = rep.functional.create.cube(position=(0, 0, 2), scale=0.5, semantics={'class': 'cube'})
            sphere = rep.functional.create.sphere(position=(1, 0, 2), scale=0.4, semantics={'class': 'sphere'})
            for prim in [cube, sphere]:
                rep.functional.physics.apply_collider(prim)
                rep.functional.physics.apply_rigid_body(prim)
        elif args.example != 'motion-blur':
            cube = rep.create.cube(position=(-0.7, 0, 0.6), scale=0.7, semantics=[('class', 'cube')])
            other = rep.create.cube(position=(0.7, 0, 0.4), scale=0.4, semantics=[('class', 'cube')])
            rep.create.plane(scale=4)
        cameras = [rep.create.camera(position=(4, 4, 3), look_at=(0, 0, 1))]
        if args.example == 'multi-camera':
            cameras += [rep.create.camera(position=(-3, 3, 2), look_at=(0, 0, 0.6)), rep.create.camera(position=(0, -4, 3), look_at=(0, 0, 0.6))]
        products = [rep.create.render_product(camera, (320 + 80 * index, 240), name=f'camera_{index}') for index, camera in enumerate(cameras)]
        product = products[0]
        rgb_annotators = []
        for rp in products:
            annotator = rep.AnnotatorRegistry.get_annotator('rgb')
            annotator.attach(rp)
            rgb_annotators.append(annotator)

        class CameraWriter(rep.Writer):
            def __init__(self, output_dir=None):
                self.annotators = [rep.AnnotatorRegistry.get_annotator('rgb')]
                self._directory = Path(output_dir) if output_dir else output / 'custom_writer'
                self._directory.mkdir(parents=True, exist_ok=True)
                self._frame = 0
                self.records = []

            def write(self, data):
                for key, pixels in data.items():
                    if key.startswith('rgb'):
                        name = re.sub(r'[^a-zA-Z0-9_-]', '_', key)
                        pixels = np.asarray(pixels)
                        Image.fromarray(pixels).save(self._directory / f'{self._frame:04d}_{name}.png')
                        self.records.append({'frame': self._frame, 'key': key, 'shape': list(pixels.shape)})
                self._frame += 1

        if args.example == 'multi-camera':
            rep.WriterRegistry.register(CameraWriter)
            writer = rep.WriterRegistry.get('CameraWriter')
            writer.initialize(output_dir=str(output / 'custom_writer'))
        elif args.example == 'cosmos':
            writer = rep.WriterRegistry.get('CosmosWriter')
            writer.initialize(output_dir=str(output / 'cosmos'), segmentation_mapping={'floor': [0, 0, 255, 255], 'cube': [255, 0, 0, 255], 'sphere': [0, 255, 0, 255]})
        else:
            writer = rep.WriterRegistry.get('BasicWriter')
            writer.initialize(output_dir=str(output / 'writer'), rgb=True, semantic_segmentation=args.example == 'settled')
        writer.attach(products)
        records = []
        timeline = omni.timeline.get_timeline_interface()

        def capture(frame, **values):
            rep.orchestrator.step(rt_subframes=4, delta_time=0.0, pause_timeline=False)
            row = {'frame': frame, 'time_s': timeline.get_current_time(), **values, 'camera_shapes': []}
            for index, annotator in enumerate(rgb_annotators):
                pixels = np.asarray(annotator.get_data())
                if pixels.size == 0:
                    raise RuntimeError(f'Camera {index} produced no pixels')
                Image.fromarray(pixels).save(output / f'{frame:04d}_camera_{index}.png')
                row['camera_shapes'].append(list(pixels.shape))
            records.append(row)
            print(json.dumps(row))

        if args.example == 'multi-camera':
            with rep.trigger.on_frame():
                with cube:
                    rep.randomizer.color(colors=rep.distribution.uniform((0, 0, 0), (1, 1, 1)))
            for frame in range(args.frames):
                capture(frame)
        elif args.example == 'custom-event':
            for name, item in [('left', cube), ('right', other)]:
                with rep.trigger.on_custom_event(event_name=f'lesson.{name}'):
                    with item:
                        rep.randomizer.rotation()
            for frame in range(args.frames):
                name = ['left', 'right'][frame % 2]
                rep.utils.send_og_event(event_name=f'lesson.{name}')
                capture(frame, requested_event=f'lesson.{name}')
        elif args.example == 'settled':
            for frame in range(args.frames):
                body.set_world_pose(position=np.array([0, 0, 2 + frame * 0.5]))
                body.set_linear_velocity(np.zeros(3))
                body.set_angular_velocity(np.zeros(3))
                quiet = 0
                for step in range(capture_steps):
                    world.step(render=False)
                    speed = float(np.linalg.norm(body.get_linear_velocity()))
                    angular = float(np.linalg.norm(body.get_angular_velocity()))
                    height = float(body.get_world_pose()[0][2])
                    quiet = quiet + 1 if step >= 30 and speed < 0.05 and angular < 0.1 and height < 1.0 else 0
                    if quiet >= 10:
                        capture(frame, physics_steps=step + 1, speed_m_s=speed, height_m=height)
                        break
                else:
                    raise TimeoutError(f'Cube did not settle within {capture_steps} physics steps')
        elif args.example == 'custom-fps':
            depth = rep.AnnotatorRegistry.get_annotator('distance_to_camera')
            depth.attach(product)
            stride = args.stage_fps // args.sensor_fps
            product.hydra_texture.set_updates_enabled(False)
            for step in range(1, args.frames * stride + 1):
                world.step(render=False)
                if step % stride == 0:
                    product.hydra_texture.set_updates_enabled(True)
                    frame = step // stride - 1
                    capture(frame, physics_time_s=world.current_time, requested_sensor_fps=args.sensor_fps)
                    np.save(output / f'{frame:04d}_depth.npy', depth.get_data())
                    product.hydra_texture.set_updates_enabled(False)
            depth.detach(product)
        elif args.example == 'events':
            settings.set('/app/player/useFixedTimeStepping', True)
            timeline.set_play_every_frame(True)
            timeline.set_time_codes_per_second(args.stage_fps)
            counters = {'timeline_times': [], 'physics_dt': [], 'render_events': 0, 'app_events': 0}
            def on_time(event):
                if event.type == omni.timeline.TimelineEventType.CURRENT_TIME_TICKED.value:
                    counters['timeline_times'].append(float(event.payload['currentTime']))
            def on_physics(dt):
                counters['physics_dt'].append(float(dt))
            def on_render(event):
                counters['render_events'] += 1
            def on_app(event):
                counters['app_events'] += 1
            subscriptions = [timeline.get_timeline_event_stream().create_subscription_to_pop(on_time), omni.physx.get_physx_interface().subscribe_physics_step_events(on_physics)]
            observers = [carb.eventdispatcher.get_eventdispatcher().observe_event(event_name=omni.usd.get_context().stage_rendering_event_name(omni.usd.StageRenderingEventType.NEW_FRAME, True), on_event=on_render, observer_name='lesson.render'), carb.eventdispatcher.get_eventdispatcher().observe_event(event_name=omni.kit.app.GLOBAL_EVENT_UPDATE, on_event=on_app, observer_name='lesson.app')]
            timeline.play()
            timeline.commit()
            started = time.perf_counter()
            for _ in range(capture_steps):
                app.update()
            counters['wall_seconds'] = time.perf_counter() - started
            timeline.pause()
            for subscription in subscriptions:
                subscription.unsubscribe()
            for observer in observers:
                observer.reset()
            if not counters['physics_dt'] or not counters['timeline_times']:
                raise RuntimeError('No physics/timeline events were observed')
            records.append(counters)
            print(json.dumps(counters))
        elif args.example == 'motion-blur':
            settings.set('/omni/replicator/captureMotionBlur', True)
            settings.set('/rtx/rendermode', 'PathTracing' if args.renderer == 'pt' else 'RayTracedLighting')
            settings.set('/rtx/pathtracing/spp', 32)
            settings.set('/rtx/pathtracing/totalSpp', 32)
            settings.set('/omni/replicator/pathTracedMotionBlurSubSamples', args.subsamples)
            settings.set('/rtx/post/motionblur/exposureFraction', 1.0)
            settings.set('/rtx/post/motionblur/numSamples', 8)
            settings.set('/rtx/post/aa/op', 2)
            physics_scene = UsdPhysics.Scene.Define(stage, '/World/PhysicsScene')
            PhysxSchema.PhysxSceneAPI.Apply(physics_scene.GetPrim()).CreateTimeStepsPerSecondAttr(args.stage_fps * args.subsamples)
            stage.SetTimeCodesPerSecond(args.stage_fps)
            for index, speed in enumerate([0, 2, 4]):
                for native_physics in [False, True]:
                    path = f'/World/{"Physics" if native_physics else "Animation"}_{index}'
                    shape = UsdGeom.Cube.Define(stage, path)
                    shape.CreateSizeAttr(0.3)
                    origin = Gf.Vec3d(index - 1, 0.5 if native_physics else -0.5, 1.2)
                    transform = UsdGeom.Xformable(shape).AddTranslateOp()
                    if native_physics:
                        transform.Set(origin)
                        rigid = UsdPhysics.RigidBodyAPI.Apply(shape.GetPrim())
                        rigid.CreateVelocityAttr(Gf.Vec3f(0, 0, -speed))
                        physx = PhysxSchema.PhysxRigidBodyAPI.Apply(shape.GetPrim())
                        physx.CreateDisableGravityAttr(True)
                        physx.CreateLinearDampingAttr(0.0)
                        UsdPhysics.CollisionAPI.Apply(shape.GetPrim())
                    else:
                        transform.Set(origin, Usd.TimeCode(0))
                        transform.Set(origin + Gf.Vec3d(0, 0, -speed * 5), Usd.TimeCode(args.stage_fps * 5))
            timeline.play()
            for frame in range(args.frames):
                rep.orchestrator.step(delta_time=1 / args.stage_fps, pause_timeline=False)
                records.append({'frame': frame, 'time_s': timeline.get_current_time(), 'renderer': args.renderer, 'subsamples': args.subsamples})
        else:
            timeline.play()
            for frame in range(args.frames):
                app.update()
                capture(frame)
        rep.orchestrator.wait_until_complete()
        if args.example == 'multi-camera':
            (output / 'writer_payloads.json').write_text(json.dumps(writer.records, indent=2))
        (output / 'measurements.json').write_text(json.dumps(records, indent=2))
        stage.GetRootLayer().Export(str(output / 'scene.usda'))
        timeline.stop()
        writer.detach()
        for annotator, rp in zip(rgb_annotators, products):
            annotator.detach(rp)
            rp.destroy()
        while keep_open and app.is_running():
            app.update()
    finally:
        app.close()


if __name__ == '__main__':
    main()
