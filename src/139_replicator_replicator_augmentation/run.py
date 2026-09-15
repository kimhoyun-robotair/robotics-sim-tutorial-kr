"""Compare actual Replicator annotator and writer augmentations."""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=['annotator', 'writer'], default='annotator')
    parser.add_argument('--backend', choices=['numpy', 'warp'], default='numpy')
    parser.add_argument('--frames', type=int, default=3)
    parser.add_argument('--sigma', type=float, default=0.1, help='Depth noise standard deviation in metres')
    parser.add_argument('--seed', type=int, default=23)
    parser.add_argument('--headless', action='store_true')
    parser.add_argument('--output', type=Path, default=Path(__file__).parent / 'output')
    parser.add_argument("--steps", type=int, default=None,
                        help="GUI app updates after generation; omitted: keep GUI open; headless: no inspection")
    args = parser.parse_args()
    if args.steps is not None and args.steps < 1:
        parser.error("--steps must be positive")
    if args.frames < 1 or args.sigma < 0:
        parser.error('frames must be positive; sigma must be nonnegative')
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    from isaacsim import SimulationApp
    app = SimulationApp({'headless': args.headless})
    try:
        import carb.settings
        import numpy as np
        import omni.replicator.core as rep
        import omni.usd
        from PIL import Image
        import filters

        carb.settings.get_settings().set_bool('/app/omni.graph.scriptnode/opt_in', True)
        rep.orchestrator.set_capture_on_play(False)
        rep.set_global_seed(args.seed)
        omni.usd.get_context().new_stage()
        rep.settings.set_stage_up_axis('Z')
        rep.settings.set_stage_meters_per_unit(1.0)
        rep.create.light(light_type='dome', intensity=800)
        red = rep.create.material_omnipbr(diffuse=(0.9, 0.03, 0.03))
        cube = rep.create.cube(position=(0, 0, 0.6), scale=0.7, material=red)
        rep.create.plane(scale=5)
        camera = rep.create.camera(position=(3, 3, 3), look_at=(0, 0, 0.6))
        product = rep.create.render_product(camera, (320, 240))
        augmentation = rep.annotators.Augmentation.from_function
        gpu = args.backend == 'warp'
        swap = augmentation(filters.swap_red_blue_gpu if gpu else filters.swap_red_blue)
        depth = augmentation(filters.depth_noise_gpu if gpu else filters.depth_noise, sigma=args.sigma, seed=args.seed)
        rep.AnnotatorRegistry.register_augmentation('lesson_depth_noise', depth)
        original_rgb = rep.AnnotatorRegistry.get_annotator('rgb')
        original_depth = rep.AnnotatorRegistry.get_annotator('distance_to_camera')
        original_rgb.attach(product)
        original_depth.attach(product)
        with rep.trigger.on_frame():
            with cube:
                rep.randomizer.rotation()
        writer = None
        modified = []
        if args.mode == 'annotator':
            rgb = rep.AnnotatorRegistry.get_annotator('rgb').augment(swap, name='lesson_bgr')
            depth_small = rep.AnnotatorRegistry.get_annotator('distance_to_camera').augment(depth, name='lesson_depth_small')
            depth_large = rep.AnnotatorRegistry.get_annotator('distance_to_camera').augment(depth, name='lesson_depth_large', sigma=args.sigma * 5)
            modified = [rgb, depth_small, depth_large]
            for annotator in modified:
                annotator.attach(product)
        else:
            writer = rep.WriterRegistry.get('BasicWriter')
            writer.initialize(output_dir=str(output / 'writer'), rgb=True, distance_to_camera=True)
            hsv = augmentation(rep.augmentations_default.aug_rgb_to_hsv)
            noise = augmentation(filters.channel_noise_gpu if gpu else filters.channel_noise, sigma=6.0, seed=args.seed)
            rgb = augmentation(rep.augmentations_default.aug_hsv_to_rgb)
            composed = rep.annotators.get('rgb').augment_compose([hsv, noise, rgb], name='rgb')
            writer.add_annotator(composed)
            writer.augment_annotator('distance_to_camera', rep.AnnotatorRegistry.get_augmentation('lesson_depth_noise'))
            writer.attach(product)
        report = []
        for frame in range(args.frames):
            rep.orchestrator.step(rt_subframes=8, delta_time=0.0)
            clean_rgb = np.asarray(original_rgb.get_data()).copy()
            clean_depth = np.asarray(original_depth.get_data()).copy()
            if clean_rgb.size == 0 or clean_depth.size == 0:
                raise RuntimeError('Renderer returned empty annotator data')
            Image.fromarray(clean_rgb).save(output / f'{frame:04d}_original.png')
            np.save(output / f'{frame:04d}_depth_original.npy', clean_depth)
            row = {'frame': frame, 'shape': list(clean_rgb.shape)}
            if modified:
                data = [a.get_data() for a in modified]
                data = [a.numpy() if hasattr(a, 'numpy') else np.asarray(a) for a in data]
                Image.fromarray(data[0]).save(output / f'{frame:04d}_bgr.png')
                finite = np.isfinite(clean_depth)
                if not finite.any():
                    raise RuntimeError('No finite depth pixels were observed')
                for label, values in zip(['small', 'large'], data[1:]):
                    np.save(output / f'{frame:04d}_depth_{label}.npy', values)
                    row[f'{label}_noise_std_m'] = float(np.std((values - clean_depth)[finite]))
                row['red_blue_swap_exact'] = bool(np.array_equal(clean_rgb[..., [2, 1, 0, 3]], data[0]))
                if not row['red_blue_swap_exact']:
                    raise RuntimeError('RGB augmentation did not swap the expected channels')
            report.append(row)
            print(json.dumps(row))
        rep.orchestrator.wait_until_complete()
        (output / 'measurements.json').write_text(json.dumps(report, indent=2))
        for annotator in [original_rgb, original_depth, *modified]:
            annotator.detach(product)
        if writer is not None:
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
