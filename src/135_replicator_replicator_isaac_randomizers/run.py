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
    app = SimulationApp({'headless': args.headless})
    try:
        import numpy as np
        import omni.kit.commands
        import omni.replicator.core as rep
        import omni.usd
        from isaacsim.core.utils.semantics import add_labels
        from pxr import Gf, Sdf, Usd, UsdGeom, UsdLux, UsdShade
        omni.usd.get_context().new_stage()
        stage = omni.usd.get_context().get_stage()
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
        UsdGeom.SetStageMetersPerUnit(stage, 1.0)
        rng = random.Random(args.seed)
        rep.orchestrator.set_capture_on_play(False)
        dome = UsdLux.DomeLight.Define(stage, '/World/Dome')
        dome.CreateIntensityAttr(600)

        def cube(path, position, size):
            shape = UsdGeom.Cube.Define(stage, path)
            shape.CreateSizeAttr(1.0)
            transform = UsdGeom.Xformable(shape)
            transform.AddTranslateOp().Set(position)
            transform.AddRotateXYZOp()
            transform.AddScaleOp().Set(size)
            add_labels(shape.GetPrim(), labels=['cube'], instance_name='class')
            return shape.GetPrim()

        camera = UsdGeom.Camera.Define(stage, '/World/Camera')
        camera_transform = UsdGeom.Xformable(camera)
        camera_position = camera_transform.AddTranslateOp()
        camera_orientation = camera_transform.AddOrientOp()

        def look_at(eye, target):
            camera_position.Set(Gf.Vec3d(*eye))
            rotation = Gf.Matrix4d().SetLookAt(Gf.Vec3d(*eye), Gf.Vec3d(*target), Gf.Vec3d(0, 0, 1)).GetInverse().ExtractRotationQuat()
            camera_orientation.Set(Gf.Quatf(rotation))

        look_at((5, 5, 4), (0, 0, 0.8))
        product = rep.create.render_product('/World/Camera', (480, 360))
        writer = rep.WriterRegistry.get('BasicWriter')
        writer.initialize(output_dir=str(output / 'rgb'), rgb=True)
        writer.attach(product)
        if args.example == 'simready':
            import simready_lab
            simready_lab.run(app, stage, product, args.frames, capture_steps, args.seed, output)
            rep.orchestrator.wait_until_complete()
            writer.detach()
            product.destroy()
            while keep_open and app.is_running():
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
                omni.kit.commands.execute('CreateMdlMaterialPrim', mtl_url='OmniPBR.mdl', mtl_name='OmniPBR', mtl_path=path)
                material = UsdShade.Material(stage.GetPrimAtPath(path))
                shader = UsdShade.Shader(omni.usd.get_shader_from_material(material.GetPrim(), get_prim=True))
                for name, typename in [('diffuse_texture', Sdf.ValueTypeNames.Asset), ('texture_scale', Sdf.ValueTypeNames.Float2), ('texture_rotate', Sdf.ValueTypeNames.Float), ('project_uvw', Sdf.ValueTypeNames.Bool)]:
                    shader.CreateInput(name, typename)
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
            from isaacsim.core.api.objects import DynamicCuboid, FixedCuboid
            stage.RemovePrim('/World/Target')
            stage.RemovePrim('/World/Floor')
            world = World(stage_units_in_meters=1.0, physics_dt=1 / 60, rendering_dt=1 / 60)
            world.scene.add_default_ground_plane()
            for index, (position, scale) in enumerate([((1.1, 0, 1), (0.2, 2.4, 2)), ((-1.1, 0, 1), (0.2, 2.4, 2)), ((0, 1.1, 1), (2, 0.2, 2)), ((0, -1.1, 1), (2, 0.2, 2))]):
                wall = world.scene.add(FixedCuboid(prim_path=f'/World/Wall_{index}', name=f'wall{index}', position=np.array(position), scale=np.array(scale), size=1))
                wall.set_visibility(False)
            for index in range(10):
                body = world.scene.add(DynamicCuboid(prim_path=f'/World/Box_{index}', name=f'box{index}', position=np.array([rng.uniform(-0.7, 0.7), rng.uniform(-0.7, 0.7), 0.5 + 0.45 * index]), scale=np.array([0.3, 0.3, 0.3]), size=1, mass=0.1))
                bodies.append(body)
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
                    world.step(render=False)
                row['bodies'] = [{'position': body.get_world_pose()[0].tolist(), 'speed_m_s': float(np.linalg.norm(body.get_linear_velocity()))} for body in bodies]
            rep.orchestrator.step(rt_subframes=8, delta_time=0.0, pause_timeline=False)
            rows.append(row)
            print(json.dumps(row))
        rep.orchestrator.wait_until_complete()
        stage.GetRootLayer().Export(str(output / 'scene.usda'))
        (output / 'measurements.json').write_text(json.dumps(rows, indent=2))
        writer.detach()
        product.destroy()
        while keep_open and app.is_running():
            app.update()
    finally:
        app.close()


if __name__ == '__main__':
    main()
