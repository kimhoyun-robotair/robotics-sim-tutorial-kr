"""Five USD/Isaac randomization workflows with captured data and scene measurements."""
import argparse
import json
import math
from pathlib import Path
import random


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--example', choices=['lights', 'textures', 'sequential', 'volume', 'simready'], default='lights')
    parser.add_argument('--frames', type=int, default=3)
    parser.add_argument('--steps', type=int, default=None, help="Physics steps per capture in volume/simready mode; omitted: 180 for capture, then GUI stays open")
    parser.add_argument('--seed', type=int, default=31)
    parser.add_argument('--headless', action='store_true')
    parser.add_argument('--output', type=Path, default=Path(__file__).parent / 'output')
    args = parser.parse_args()
    keep_open = args.steps is None and not args.headless
    capture_steps = args.steps if args.steps is not None else 180
    if min(args.frames, capture_steps) < 1:
        parser.error('frames and steps must be positive')
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    from isaacsim import SimulationApp
    # SimulationApp은 Python에서 Isaac Sim의 Kit 애플리케이션을 시작하고 갱신·종료하는 클래스이다.
    # headless=True는 창 없이 실행한다는 뜻이며, omni와 Isaac Sim 확장 모듈은 앱 생성 후 import한다.
    app = SimulationApp({'headless': args.headless})
    try:
        import numpy as np
        import omni.kit.commands
        # omni.kit.commands는 이름으로 등록된 Kit 명령을 실행하는 모듈이다.
        # execute에 명령 이름과 인자를 전달해 Prim 생성·가져오기 등의 작업을 수행한다.
        import omni.replicator.core as rep
        # omni.replicator.core는 장면 무작위화와 합성 데이터 생성을 위한 API이다.
        # render product는 카메라의 렌더링 출력이며, annotator는 데이터를 추출하고 writer는 결과를 저장한다.
        import omni.usd
        # omni.usd는 현재 Kit 애플리케이션의 USD 문맥에 접근하는 모듈이다.
        # get_context().get_stage()로 객체·조명 등이 들어 있는 현재 Stage를 얻는다.
        from isaacsim.core.utils.semantics import add_labels
        # add_labels는 Prim에 의미 라벨을 부여하여 합성 데이터에서 객체의 클래스를 구분할 수 있게 한다.
        from pxr import Gf, Sdf, Usd, UsdGeom, UsdLux, UsdShade
        # pxr은 USD 장면을 직접 다루는 OpenUSD의 Python 바인딩이다.
        # Gf는 벡터·행렬·쿼터니언 등 위치와 회전을 계산하는 수학 자료형을 다룬다.
        # Sdf는 USD 경로, 레이어, 속성 값의 자료형을 다룬다.
        # Usd는 Stage, Prim, 참조·variant 등의 USD 장면 구성 API를 다룬다.
        # UsdGeom은 형상, 변환, 카메라와 장면 단위·축 설정을 다룬다.
        # UsdLux는 조명 Prim과 빛의 속성을 다룬다.
        # UsdShade는 셰이더·재질과 형상에 대한 재질 연결을 다룬다.
        # 새 USD Stage를 열어 이 예제의 장면을 구성한다.
        omni.usd.get_context().new_stage()
        stage = omni.usd.get_context().get_stage()
        # USD 장면에서 위쪽으로 사용할 축을 지정한다.
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
        # USD 좌표 한 단위가 몇 미터인지 지정하여 장면의 길이 단위를 맞춘다.
        UsdGeom.SetStageMetersPerUnit(stage, 1.0)
        rng = random.Random(args.seed)
        # 타임라인 재생에 따른 자동 캡처 여부를 설정한다. False이면 아래의 명시적 캡처 호출로 제어한다.
        rep.orchestrator.set_capture_on_play(False)
        # 주변을 둘러싸는 DomeLight를 생성하여 장면의 환경 조명을 설정한다.
        dome = UsdLux.DomeLight.Define(stage, '/World/Dome')
        dome.CreateIntensityAttr(600)

        def cube(path, position, size):
            # USD Stage에 Cube 형상을 직접 정의한다. 물리 동작이 필요하면 강체·충돌 API를 별도로 적용한다.
            shape = UsdGeom.Cube.Define(stage, path)
            shape.CreateSizeAttr(1.0)
            # Prim의 변환 연산에 접근한다. AddTranslateOp·AddRotateXYZOp·AddScaleOp로 이동·회전·스케일을 기록할 수 있다.
            transform = UsdGeom.Xformable(shape)
            transform.AddTranslateOp().Set(position)
            transform.AddRotateXYZOp()
            transform.AddScaleOp().Set(size)
            add_labels(shape.GetPrim(), labels=['cube'], instance_name='class')
            return shape.GetPrim()

        # USD 카메라 Prim을 정의한다. 센서 이미지 출력은 별도의 render product나 Camera API로 연결한다.
        camera = UsdGeom.Camera.Define(stage, '/World/Camera')
        camera_transform = UsdGeom.Xformable(camera)
        camera_position = camera_transform.AddTranslateOp()
        camera_orientation = camera_transform.AddOrientOp()

        def look_at(eye, target):
            camera_position.Set(Gf.Vec3d(*eye))
            rotation = Gf.Matrix4d().SetLookAt(Gf.Vec3d(*eye), Gf.Vec3d(*target), Gf.Vec3d(0, 0, 1)).GetInverse().ExtractRotationQuat()
            camera_orientation.Set(Gf.Quatf(rotation))

        look_at((5, 5, 4), (0, 0, 0.8))
        # 카메라와 해상도를 연결한 render product를 만든다. 이후 annotator나 writer를 여기에 연결한다.
        product = rep.create.render_product('/World/Camera', (480, 360))
        # 등록된 writer를 이름으로 선택한다. initialize로 출력 설정을 지정한 뒤 render product에 연결한다.
        writer = rep.WriterRegistry.get('BasicWriter')
        writer.initialize(output_dir=str(output / 'rgb'), rgb=True)
        # writer를 render product에 연결하여 캡처한 데이터가 writer로 전달되게 한다.
        writer.attach(product)
        if args.example == 'simready':
            import simready_lab
            simready_lab.run(app, stage, product, args.frames, capture_steps, args.seed, output)
            # 예약된 합성 데이터 처리와 writer의 저장 작업이 끝날 때까지 기다린다.
            rep.orchestrator.wait_until_complete()
            # writer와 render product의 연결을 해제한다.
            writer.detach()
            product.destroy()
            while keep_open and app.is_running():
                # Kit의 한 프레임을 갱신하여 렌더링·이벤트·비동기 작업을 처리한다.
                # 물리 진행 여부는 현재 타임라인의 재생 상태와 설정에 따라 달라진다.
                app.update()
            return
        floor = cube('/World/Floor', (0, 0, -0.1), (5, 5, 0.2))
        target = cube('/World/Target', (0, 0, 0.6), (0.8, 0.8, 1.2))
        lights, shaders, bodies = [], [], []
        world = None
        if args.example == 'lights':
            for index in range(3):
                light = UsdLux.SphereLight.Define(stage, f'/World/Light_{index}')
                UsdGeom.Xformable(light).AddTranslateOp()
                light.CreateRadiusAttr(0.3)
                light.CreateEnableColorTemperatureAttr(True)
                lights.append(light)
        elif args.example == 'textures':
            from PIL import Image
            textures = []
            for index, color in enumerate([(190, 70, 40), (20, 120, 190), (80, 170, 60)]):
                pixels = np.full((64, 64, 3), color, dtype=np.uint8)
                pixels[::8, :] = 240
                pixels[:, ::8] = 240
                path = output / f'texture_{index}.png'
                Image.fromarray(pixels).save(path)
                textures.append(str(path))
            for index, prim in enumerate([target, floor]):
                path = f'/World/Looks/Material_{index}'
                # MDL 재질 Prim을 만들고 아래에서 텍스처·셰이더 입력을 설정한다.
                omni.kit.commands.execute('CreateMdlMaterialPrim', mtl_url='OmniPBR.mdl', mtl_name='OmniPBR', mtl_path=path)
                material = UsdShade.Material(stage.GetPrimAtPath(path))
                shader = UsdShade.Shader(omni.usd.get_shader_from_material(material.GetPrim(), get_prim=True))
                for name, typename in [('diffuse_texture', Sdf.ValueTypeNames.Asset), ('texture_scale', Sdf.ValueTypeNames.Float2), ('texture_rotate', Sdf.ValueTypeNames.Float), ('project_uvw', Sdf.ValueTypeNames.Bool)]:
                    shader.CreateInput(name, typename)
                # Prim에 재질 연결 API를 적용한다. 이어지는 Bind에서 실제 사용할 재질을 지정한다.
                UsdShade.MaterialBindingAPI.Apply(prim).Bind(material)
                shaders.append(shader)
        elif args.example == 'sequential':
            stage.RemovePrim('/World/Target')
            pallet = cube('/World/Pallet', (0, 0, 0.15), (1, 1, 1))
            cube('/World/Pallet/Deck', (0, 0, 0), (2.4, 1.6, 0.3))
            UsdGeom.Imageable(pallet).GetVisibilityAttr().Set('inherited')
            # Replace the parent Cube with Xform so it contributes only a coordinate frame.
            pallet.SetTypeName('Xform')
            target = cube('/World/Pallet/Bin', (0, 0, 0.45), (0.5, 0.4, 0.6))
        elif args.example == 'volume':
            from isaacsim.core.api import World
            # World는 Stage의 객체와 작업을 관리하고 물리·렌더링 시간 간격, 초기화, 시뮬레이션 진행을 제어한다.
            from isaacsim.core.api.objects import DynamicCuboid, FixedCuboid
            # DynamicCuboid는 큐브 형상에 강체와 충돌 속성을 함께 부여하므로 중력과 접촉에 반응한다.
            # FixedCuboid는 충돌 가능한 고정 큐브로, 바닥이나 움직이지 않는 장애물을 만들 때 사용한다.
            stage.RemovePrim('/World/Target')
            stage.RemovePrim('/World/Floor')
            # stage_units_in_meters는 장면 길이 단위이고, physics_dt·rendering_dt는 각각 물리·렌더링 시간 간격(초)이다.
            world = World(stage_units_in_meters=1.0, physics_dt=1 / 60, rendering_dt=1 / 60)
            # 기본 바닥을 Scene에 추가한다. 이 바닥은 강체가 떨어졌을 때 충돌할 표면이다.
            world.scene.add_default_ground_plane()
            for index, (position, scale) in enumerate([((1.1, 0, 1), (0.2, 2.4, 2)), ((-1.1, 0, 1), (0.2, 2.4, 2)), ((0, 1.1, 1), (2, 0.2, 2)), ((0, -1.1, 1), (2, 0.2, 2))]):
                # 생성한 객체를 World의 Scene에 등록하여 이름으로 찾고 초기화할 수 있게 한다.
                wall = world.scene.add(FixedCuboid(prim_path=f'/World/Wall_{index}', name=f'wall{index}', position=np.array(position), scale=np.array(scale), size=1))
                wall.set_visibility(False)
            for index in range(10):
                body = world.scene.add(DynamicCuboid(prim_path=f'/World/Box_{index}', name=f'box{index}', position=np.array([rng.uniform(-0.7, 0.7), rng.uniform(-0.7, 0.7), 0.5 + 0.45 * index]), scale=np.array([0.3, 0.3, 0.3]), size=1, mass=0.1))
                bodies.append(body)
            # World를 초기화하고 등록된 객체의 물리 핸들을 준비한다. 관절·강체 상태를 읽기 전에 호출한다.
            world.reset()
        rows = []
        for frame in range(args.frames):
            row = {'frame': frame, 'example': args.example}
            if lights:
                row['lights'] = []
                for light in lights:
                    position = (rng.uniform(-2, 2), rng.uniform(-2, 2), rng.uniform(2, 4))
                    intensity = rng.uniform(3000, 18000)
                    temperature = rng.uniform(2800, 8000)
                    light.GetPrim().GetAttribute('xformOp:translate').Set(position)
                    light.CreateIntensityAttr(intensity)
                    light.CreateColorTemperatureAttr(temperature)
                    light.CreateColorAttr(Gf.Vec3f(*(rng.uniform(0.3, 1) for _ in range(3))))
                    row['lights'].append({'position': position, 'intensity': intensity, 'temperature_K': temperature})
            if shaders:
                row['textures'] = []
                for shader in shaders:
                    texture = rng.choice(textures)
                    scale, angle = rng.uniform(0.25, 2), rng.uniform(0, 90)
                    shader.GetInput('diffuse_texture').Set(Sdf.AssetPath(texture))
                    shader.GetInput('texture_scale').Set((scale, scale))
                    shader.GetInput('texture_rotate').Set(angle)
                    shader.GetInput('project_uvw').Set(True)
                    row['textures'].append({'file': texture, 'scale': scale, 'rotation_deg': angle})
            if args.example == 'sequential':
                pallet.GetAttribute('xformOp:rotateXYZ').Set((0, 0, rng.uniform(-90, 90)))
                target.GetAttribute('xformOp:translate').Set((rng.uniform(-0.9, 0.9), rng.uniform(-0.5, 0.5), 0.45))
                world_position = UsdGeom.Xformable(target).ComputeLocalToWorldTransform(Usd.TimeCode.Default()).ExtractTranslation()
                z = (frame + 0.5) / args.frames
                angle = frame * math.pi * (3 - math.sqrt(5))
                radius = 4.0
                xy = math.sqrt(1 - z * z)
                eye = world_position + Gf.Vec3d(radius * xy * math.cos(angle), radius * xy * math.sin(angle), radius * z)
                look_at(eye, world_position)
                dome.CreateColorAttr(Gf.Vec3f(0.7 + frame % 2 * 0.3, 0.85, 1))
                row['bin_world_position'] = list(world_position)
                row['camera_position'] = list(eye)
            if world is not None:
                for step in range(capture_steps):
                    if step == 1 and frame > 0:
                        for body in bodies:
                            position, _ = body.get_world_pose()
                            velocity = np.array([-position[0], -position[1], 0.2]) * 0.8
                            body.set_linear_velocity(velocity)
                    # 물리 시뮬레이션을 한 step 진행한다. render는 이 호출에서 렌더링도 수행할지 지정한다.
                    world.step(render=False)
                row['bodies'] = [{'position': body.get_world_pose()[0].tolist(), 'speed_m_s': float(np.linalg.norm(body.get_linear_velocity()))} for body in bodies]
            # Replicator의 캡처를 한 번 진행한다. rt_subframes는 캡처를 위한 렌더링 누적 프레임 수이다.
            rep.orchestrator.step(rt_subframes=8, delta_time=0.0, pause_timeline=False)
            rows.append(row)
            print(json.dumps(row))
        rep.orchestrator.wait_until_complete()
        # Stage의 루트 레이어를 USD 파일로 내보낸다. 참조 자산 자체를 모두 복사하는 것은 아니다.
        stage.GetRootLayer().Export(str(output / 'scene.usda'))
        (output / 'measurements.json').write_text(json.dumps(rows, indent=2))
        writer.detach()
        product.destroy()
        while keep_open and app.is_running():
            app.update()
    finally:
        # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
        app.close()


if __name__ == '__main__':
    main()
