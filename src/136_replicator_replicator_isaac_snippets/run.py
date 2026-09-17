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
    # SimulationApp은 Python에서 Isaac Sim의 Kit 애플리케이션을 시작하고 갱신·종료하는 클래스이다.
    # headless=True는 창 없이 실행한다는 뜻이며, omni와 Isaac Sim 확장 모듈은 앱 생성 후 import한다.
    app = SimulationApp({'headless': args.headless})
    try:
        import carb.eventdispatcher
        # carb.eventdispatcher는 Kit 이벤트를 구독하고 이벤트 발생에 맞춰 콜백을 실행하는 API이다.
        import carb.settings
        # carb.settings는 경로 형태의 키로 Kit의 렌더링·시뮬레이션 설정을 읽고 변경하는 API이다.
        import numpy as np
        import omni.kit.app
        # omni.kit.app은 현재 Kit 앱과 확장 관리자에 접근하며 비동기 프레임 갱신을 기다리는 기능을 제공한다.
        import omni.physx
        # omni.physx는 Isaac Sim의 PhysX 물리 엔진 인터페이스와 물리 step 이벤트에 접근한다.
        import omni.replicator.core as rep
        # omni.replicator.core는 장면 무작위화와 합성 데이터 생성을 위한 API이다.
        # render product는 카메라의 렌더링 출력이며, annotator는 데이터를 추출하고 writer는 결과를 저장한다.
        import omni.timeline
        # omni.timeline은 시뮬레이션 시간과 재생·일시정지·정지를 제어하는 API이다.
        import omni.usd
        # omni.usd는 현재 Kit 애플리케이션의 USD 문맥에 접근하는 모듈이다.
        # get_context().get_stage()로 객체·조명 등이 들어 있는 현재 Stage를 얻는다.
        from isaacsim.core.api import World
        # World는 Stage의 객체와 작업을 관리하고 물리·렌더링 시간 간격, 초기화, 시뮬레이션 진행을 제어한다.
        from isaacsim.core.api.objects import DynamicCuboid
        # DynamicCuboid는 큐브 형상에 강체와 충돌 속성을 함께 부여하므로 중력과 접촉에 반응한다.
        from isaacsim.core.utils.semantics import add_labels
        # add_labels는 Prim에 의미 라벨을 부여하여 합성 데이터에서 객체의 클래스를 구분할 수 있게 한다.
        from PIL import Image
        from pxr import Gf, PhysxSchema, Usd, UsdGeom, UsdPhysics
        # pxr은 USD 장면을 직접 다루는 OpenUSD의 Python 바인딩이다.
        # Gf는 벡터·행렬·쿼터니언 등 위치와 회전을 계산하는 수학 자료형을 다룬다.
        # PhysxSchema는 PhysX 전용 물리 설정을 USD Prim에 기록하는 스키마를 다룬다.
        # Usd는 Stage, Prim, 참조·variant 등의 USD 장면 구성 API를 다룬다.
        # UsdGeom은 형상, 변환, 카메라와 장면 단위·축 설정을 다룬다.
        # UsdPhysics는 강체·충돌·관절·물리 재질의 USD 스키마를 다룬다.
        # 새 USD Stage를 열어 이 예제의 장면을 구성한다.
        omni.usd.get_context().new_stage()
        stage = omni.usd.get_context().get_stage()
        settings = carb.settings.get_settings()
        settings.set_bool('/app/omni.graph.scriptnode/opt_in', True)
        # 타임라인 재생에 따른 자동 캡처 여부를 설정한다. False이면 아래의 명시적 캡처 호출로 제어한다.
        rep.orchestrator.set_capture_on_play(False)
        rep.settings.set_stage_up_axis('Z')
        rep.settings.set_stage_meters_per_unit(1.0)
        rep.create.light(light_type='dome', intensity=800)
        rep.create.light(light_type='distant', rotation=(315, 0, 0), intensity=1800)
        world = None
        body = None
        if args.example in ['settled', 'custom-fps', 'events']:
            # stage_units_in_meters는 장면 길이 단위이고, physics_dt·rendering_dt는 각각 물리·렌더링 시간 간격(초)이다.
            world = World(stage_units_in_meters=1.0, physics_dt=1 / args.stage_fps, rendering_dt=1 / args.stage_fps)
            # 기본 바닥을 Scene에 추가한다. 이 바닥은 강체가 떨어졌을 때 충돌할 표면이다.
            world.scene.add_default_ground_plane()
            # 생성한 객체를 World의 Scene에 등록하여 이름으로 찾고 초기화할 수 있게 한다.
            body = world.scene.add(DynamicCuboid(prim_path='/World/FallingCube', name='falling_cube', position=np.array([0, 0, 2]), scale=np.array([0.5, 0.5, 0.5]), size=1.0))
            add_labels(body.prim, labels=['cube'], instance_name='class')
            # World를 초기화하고 등록된 객체의 물리 핸들을 준비한다. 관절·강체 상태를 읽기 전에 호출한다.
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
        # 카메라와 해상도를 연결한 render product를 만든다. 이후 annotator나 writer를 여기에 연결한다.
        products = [rep.create.render_product(camera, (320 + 80 * index, 240), name=f'camera_{index}') for index, camera in enumerate(cameras)]
        product = products[0]
        rgb_annotators = []
        for rp in products:
            # 이름으로 annotator를 가져온다. render product에 연결하면 해당 종류의 측정·주석 데이터를 읽을 수 있다.
            annotator = rep.AnnotatorRegistry.get_annotator('rgb')
            # annotator를 render product에 연결하여 렌더링 결과에서 해당 데이터를 추출하게 한다.
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
            # 사용자 writer 클래스를 등록하여 이름으로 선택하고 합성 데이터 저장에 사용할 수 있게 한다.
            rep.WriterRegistry.register(CameraWriter)
            # 등록된 writer를 이름으로 선택한다. initialize로 출력 설정을 지정한 뒤 render product에 연결한다.
            writer = rep.WriterRegistry.get('CameraWriter')
            writer.initialize(output_dir=str(output / 'custom_writer'))
        elif args.example == 'cosmos':
            writer = rep.WriterRegistry.get('CosmosWriter')
            writer.initialize(output_dir=str(output / 'cosmos'), segmentation_mapping={'floor': [0, 0, 255, 255], 'cube': [255, 0, 0, 255], 'sphere': [0, 255, 0, 255]})
        else:
            writer = rep.WriterRegistry.get('BasicWriter')
            writer.initialize(output_dir=str(output / 'writer'), rgb=True, semantic_segmentation=args.example == 'settled')
        # writer를 render product에 연결하여 캡처한 데이터가 writer로 전달되게 한다.
        writer.attach(products)
        records = []
        timeline = omni.timeline.get_timeline_interface()

        def capture(frame, **values):
            # Replicator의 캡처를 한 번 진행한다. rt_subframes는 캡처를 위한 렌더링 누적 프레임 수이다.
            rep.orchestrator.step(rt_subframes=4, delta_time=0.0, pause_timeline=False)
            row = {'frame': frame, 'time_s': timeline.get_current_time(), **values, 'camera_shapes': []}
            for index, annotator in enumerate(rgb_annotators):
                # 연결한 render product 또는 RTX 센서의 최신 annotator 출력을 읽는다. 데이터 형태는 annotator 종류에 따라 다르다.
                pixels = np.asarray(annotator.get_data())
                if pixels.size == 0:
                    raise RuntimeError(f'Camera {index} produced no pixels')
                Image.fromarray(pixels).save(output / f'{frame:04d}_camera_{index}.png')
                row['camera_shapes'].append(list(pixels.shape))
            records.append(row)
            print(json.dumps(row))

        if args.example == 'multi-camera':
            # 프레임 트리거 안에 정의한 무작위화 작업을 Replicator 캡처 흐름에 연결한다.
            with rep.trigger.on_frame():
                with cube:
                    rep.randomizer.color(colors=rep.distribution.uniform((0, 0, 0), (1, 1, 1)))
            for frame in range(args.frames):
                capture(frame)
        elif args.example == 'custom-event':
            for name, item in [('left', cube), ('right', other)]:
                # 이름을 지정한 이벤트가 발생했을 때 실행할 Replicator 작업을 정의한다.
                with rep.trigger.on_custom_event(event_name=f'lesson.{name}'):
                    with item:
                        rep.randomizer.rotation()
            for frame in range(args.frames):
                name = ['left', 'right'][frame % 2]
                # 등록한 사용자 이벤트를 발생시켜 해당 Replicator 무작위화 그래프를 실행하게 한다.
                rep.utils.send_og_event(event_name=f'lesson.{name}')
                capture(frame, requested_event=f'lesson.{name}')
        elif args.example == 'settled':
            for frame in range(args.frames):
                body.set_world_pose(position=np.array([0, 0, 2 + frame * 0.5]))
                body.set_linear_velocity(np.zeros(3))
                body.set_angular_velocity(np.zeros(3))
                quiet = 0
                for step in range(capture_steps):
                    # 물리 시뮬레이션을 한 step 진행한다. render는 이 호출에서 렌더링도 수행할지 지정한다.
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
                # Kit의 한 프레임을 갱신하여 렌더링·이벤트·비동기 작업을 처리한다.
                # 물리 진행 여부는 현재 타임라인의 재생 상태와 설정에 따라 달라진다.
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
            # 중력 등 물리 시뮬레이션의 공통 설정을 저장할 PhysicsScene을 정의한다.
            physics_scene = UsdPhysics.Scene.Define(stage, '/World/PhysicsScene')
            PhysxSchema.PhysxSceneAPI.Apply(physics_scene.GetPrim()).CreateTimeStepsPerSecondAttr(args.stage_fps * args.subsamples)
            stage.SetTimeCodesPerSecond(args.stage_fps)
            for index, speed in enumerate([0, 2, 4]):
                for native_physics in [False, True]:
                    path = f'/World/{"Physics" if native_physics else "Animation"}_{index}'
                    # USD Stage에 Cube 형상을 직접 정의한다. 물리 동작이 필요하면 강체·충돌 API를 별도로 적용한다.
                    shape = UsdGeom.Cube.Define(stage, path)
                    shape.CreateSizeAttr(0.3)
                    origin = Gf.Vec3d(index - 1, 0.5 if native_physics else -0.5, 1.2)
                    # Prim의 변환 연산에 접근한다. AddTranslateOp·AddRotateXYZOp·AddScaleOp로 이동·회전·스케일을 기록할 수 있다.
                    transform = UsdGeom.Xformable(shape).AddTranslateOp()
                    if native_physics:
                        transform.Set(origin)
                        # Prim에 강체 API를 적용하여 물리 시뮬레이션이 자세와 속도를 계산할 수 있게 한다.
                        rigid = UsdPhysics.RigidBodyAPI.Apply(shape.GetPrim())
                        rigid.CreateVelocityAttr(Gf.Vec3f(0, 0, -speed))
                        physx = PhysxSchema.PhysxRigidBodyAPI.Apply(shape.GetPrim())
                        physx.CreateDisableGravityAttr(True)
                        physx.CreateLinearDampingAttr(0.0)
                        # 형상 Prim에 충돌 API를 적용하여 접촉 계산에 참여하게 한다.
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
        # 예약된 합성 데이터 처리와 writer의 저장 작업이 끝날 때까지 기다린다.
        rep.orchestrator.wait_until_complete()
        if args.example == 'multi-camera':
            (output / 'writer_payloads.json').write_text(json.dumps(writer.records, indent=2))
        (output / 'measurements.json').write_text(json.dumps(records, indent=2))
        # Stage의 루트 레이어를 USD 파일로 내보낸다. 참조 자산 자체를 모두 복사하는 것은 아니다.
        stage.GetRootLayer().Export(str(output / 'scene.usda'))
        timeline.stop()
        # writer와 render product의 연결을 해제한다.
        writer.detach()
        for annotator, rp in zip(rgb_annotators, products):
            annotator.detach(rp)
            rp.destroy()
        while keep_open and app.is_running():
            app.update()
    finally:
        # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
        app.close()


if __name__ == '__main__':
    main()
