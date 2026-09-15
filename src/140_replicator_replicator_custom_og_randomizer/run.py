"""Sample prim locations through direct USD, manual OmniGraph, or Replicator wrapper."""
import argparse
import json
import math
from pathlib import Path
import random


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--method', choices=['direct', 'manual', 'replicator'], default='replicator')
    parser.add_argument('--frames', type=int, default=3)
    parser.add_argument('--count', type=int, default=30, help='Prims per region')
    parser.add_argument('--seed', type=int, default=17)
    parser.add_argument('--headless', action='store_true')
    parser.add_argument('--output', type=Path, default=Path(__file__).parent / 'output')
    parser.add_argument("--steps", type=int, default=None,
                        help="GUI app updates after generation; omitted: keep GUI open; headless: no inspection")
    args = parser.parse_args()
    if args.steps is not None and args.steps < 1:
        parser.error("--steps must be positive")
    if min(args.frames, args.count) < 1:
        parser.error('frames and count must be positive')
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    from isaacsim import SimulationApp
    app = SimulationApp({'headless': args.headless})
    try:
        import carb.settings
        import omni.graph.core as og
        import omni.replicator.core as rep
        import omni.usd
        from isaacsim.core.utils.extensions import enable_extension
        from omni.replicator.core.scripts.utils import ReplicatorWrapper, create_node, set_target_prims
        from pxr import UsdGeom, UsdLux
        enable_extension('omni.graph.scriptnode')
        carb.settings.get_settings().set_bool('/app/omni.graph.scriptnode/opt_in', True)
        omni.usd.get_context().new_stage()
        stage = omni.usd.get_context().get_stage()
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
        UsdGeom.SetStageMetersPerUnit(stage, 1.0)
        UsdLux.DomeLight.Define(stage, '/World/Light').CreateIntensityAttr(800)
        regions = [('inside', 0.0, 0.7, 'Cube'), ('surface', 1.4, 1.4, 'Sphere'), ('shell', 2.1, 2.6, 'Cylinder')]
        groups = {}
        for name, _, _, shape in regions:
            groups[name] = []
            for index in range(args.count):
                prim = stage.DefinePrim(f'/World/{name}/item_{index}', shape)
                transform = UsdGeom.Xformable(prim)
                transform.AddTranslateOp()
                transform.AddScaleOp().Set((0.08, 0.08, 0.08))
                groups[name].append(str(prim.GetPath()))
        script = (Path(__file__).parent / 'sphere_node.py').read_text()

        def configure(node, paths, inner, outer, seed):
            for attribute, typename, value in [('prims', 'target', None), ('inner', 'double', inner), ('outer', 'double', outer), ('seed', 'int', seed)]:
                created = og.Controller.create_attribute(node, f'inputs:{attribute}', typename)
                if value is not None:
                    og.Controller.set(created, value)
            set_target_prims(node, 'inputs:prims', paths)
            og.Controller.set(node.get_attribute('inputs:script'), script)
            return node

        @ReplicatorWrapper
        def sample_region(paths, inner, outer, seed):
            return configure(create_node('omni.graph.scriptnode.ScriptNode'), paths, inner, outer, seed)

        graph = None
        if args.method == 'manual':
            graph, nodes, _, _ = og.Controller.edit(
                {'graph_path': '/World/SamplingGraph', 'evaluator_name': 'push'},
                {og.Controller.Keys.CREATE_NODES: [(name, 'omni.graph.scriptnode.ScriptNode') for name, *_ in regions]},
            )
            for index, ((name, inner, outer, _), node) in enumerate(zip(regions, nodes)):
                configure(node, groups[name], inner, outer, args.seed + index)
        elif args.method == 'replicator':
            with rep.trigger.on_frame():
                for index, (name, inner, outer, _) in enumerate(regions):
                    sample_region(groups[name], inner, outer, args.seed + index)
        camera = rep.create.camera(position=(7, 7, 5), look_at=(0, 0, 0))
        product = rep.create.render_product(camera, (480, 360))
        writer = rep.WriterRegistry.get('BasicWriter')
        writer.initialize(output_dir=str(output / 'rgb'), rgb=True)
        writer.attach(product)
        rep.orchestrator.set_capture_on_play(False)
        rng = random.Random(args.seed)
        measurements = []
        for frame in range(args.frames):
            if args.method == 'direct':
                for name, inner, outer, _ in regions:
                    for path in groups[name]:
                        z, angle = rng.uniform(-1, 1), rng.uniform(0, 2 * math.pi)
                        radius = rng.uniform(inner ** 3, outer ** 3) ** (1 / 3)
                        xy = math.sqrt(1 - z * z)
                        stage.GetPrimAtPath(path).GetAttribute('xformOp:translate').Set((radius * xy * math.cos(angle), radius * xy * math.sin(angle), radius * z))
            elif graph is not None:
                og.Controller.evaluate_sync(graph)
            rep.orchestrator.step(rt_subframes=4, delta_time=0.0)
            for name, inner, outer, _ in regions:
                positions = [list(stage.GetPrimAtPath(path).GetAttribute('xformOp:translate').Get()) for path in groups[name]]
                distances = [math.sqrt(sum(v * v for v in point)) for point in positions]
                if not all(inner - 1e-6 <= d <= outer + 1e-6 for d in distances):
                    raise RuntimeError(f'{name}: sample outside required radius range; node execution may have failed')
                measurements.append({'frame': frame, 'region': name, 'min_radius': min(distances), 'max_radius': max(distances), 'positions': positions})
                print(f'{frame=} {name}: radius [{min(distances):.4f}, {max(distances):.4f}]')
        rep.orchestrator.wait_until_complete()
        stage.GetRootLayer().Export(str(output / 'sampling.usda'))
        (output / 'samples.json').write_text(json.dumps(measurements, indent=2))
        writer.detach()
        product.destroy()
        inspection_updates = 0
        while not args.headless and app.is_running() and (args.steps is None or inspection_updates < args.steps):
            app.update()
            inspection_updates += 1
    finally:
        app.close()


if __name__ == '__main__':
    main()
