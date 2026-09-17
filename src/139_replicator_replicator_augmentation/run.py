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
    # SimulationApp은 Python에서 Isaac Sim의 Kit 애플리케이션을 시작하고 갱신·종료하는 클래스이다.
    # headless=True는 창 없이 실행한다는 뜻이며, omni와 Isaac Sim 확장 모듈은 앱 생성 후 import한다.
    app = SimulationApp({'headless': args.headless})
    try:
        import carb.settings
        # carb.settings는 경로 형태의 키로 Kit의 렌더링·시뮬레이션 설정을 읽고 변경하는 API이다.
        import numpy as np
        import omni.replicator.core as rep
        # omni.replicator.core는 장면 무작위화와 합성 데이터 생성을 위한 API이다.
        # render product는 카메라의 렌더링 출력이며, annotator는 데이터를 추출하고 writer는 결과를 저장한다.
        import omni.usd
        # omni.usd는 현재 Kit 애플리케이션의 USD 문맥에 접근하는 모듈이다.
        # get_context().get_stage()로 객체·조명 등이 들어 있는 현재 Stage를 얻는다.
        from PIL import Image
        import filters

        carb.settings.get_settings().set_bool('/app/omni.graph.scriptnode/opt_in', True)
        # 타임라인 재생에 따른 자동 캡처 여부를 설정한다. False이면 아래의 명시적 캡처 호출로 제어한다.
        rep.orchestrator.set_capture_on_play(False)
        # Replicator가 사용할 난수 시드를 설정하여 무작위화 결과를 재현하기 쉽게 한다.
        rep.set_global_seed(args.seed)
        # 새 USD Stage를 열어 이 예제의 장면을 구성한다.
        omni.usd.get_context().new_stage()
        rep.settings.set_stage_up_axis('Z')
        rep.settings.set_stage_meters_per_unit(1.0)
        rep.create.light(light_type='dome', intensity=800)
        red = rep.create.material_omnipbr(diffuse=(0.9, 0.03, 0.03))
        cube = rep.create.cube(position=(0, 0, 0.6), scale=0.7, material=red)
        rep.create.plane(scale=5)
        camera = rep.create.camera(position=(3, 3, 3), look_at=(0, 0, 0.6))
        # 카메라와 해상도를 연결한 render product를 만든다. 이후 annotator나 writer를 여기에 연결한다.
        product = rep.create.render_product(camera, (320, 240))
        augmentation = rep.annotators.Augmentation.from_function
        gpu = args.backend == 'warp'
        swap = augmentation(filters.swap_red_blue_gpu if gpu else filters.swap_red_blue)
        depth = augmentation(filters.depth_noise_gpu if gpu else filters.depth_noise, sigma=args.sigma, seed=args.seed)
        rep.AnnotatorRegistry.register_augmentation('lesson_depth_noise', depth)
        # 이름으로 annotator를 가져온다. render product에 연결하면 해당 종류의 측정·주석 데이터를 읽을 수 있다.
        original_rgb = rep.AnnotatorRegistry.get_annotator('rgb')
        original_depth = rep.AnnotatorRegistry.get_annotator('distance_to_camera')
        original_rgb.attach(product)
        original_depth.attach(product)
        # 프레임 트리거 안에 정의한 무작위화 작업을 Replicator 캡처 흐름에 연결한다.
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
                # annotator를 render product에 연결하여 렌더링 결과에서 해당 데이터를 추출하게 한다.
                annotator.attach(product)
        else:
            # 등록된 writer를 이름으로 선택한다. initialize로 출력 설정을 지정한 뒤 render product에 연결한다.
            writer = rep.WriterRegistry.get('BasicWriter')
            writer.initialize(output_dir=str(output / 'writer'), rgb=True, distance_to_camera=True)
            hsv = augmentation(rep.augmentations_default.aug_rgb_to_hsv)
            noise = augmentation(filters.channel_noise_gpu if gpu else filters.channel_noise, sigma=6.0, seed=args.seed)
            rgb = augmentation(rep.augmentations_default.aug_hsv_to_rgb)
            # 이름으로 annotator를 가져와 렌더링 결과에서 필요한 데이터를 추출한다.
            composed = rep.annotators.get('rgb').augment_compose([hsv, noise, rgb], name='rgb')
            writer.add_annotator(composed)
            writer.augment_annotator('distance_to_camera', rep.AnnotatorRegistry.get_augmentation('lesson_depth_noise'))
            # writer를 render product에 연결하여 캡처한 데이터가 writer로 전달되게 한다.
            writer.attach(product)
        report = []
        for frame in range(args.frames):
            # Replicator의 캡처를 한 번 진행한다. rt_subframes는 캡처를 위한 렌더링 누적 프레임 수이다.
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
        # 예약된 합성 데이터 처리와 writer의 저장 작업이 끝날 때까지 기다린다.
        rep.orchestrator.wait_until_complete()
        (output / 'measurements.json').write_text(json.dumps(report, indent=2))
        for annotator in [original_rgb, original_depth, *modified]:
            annotator.detach(product)
        if writer is not None:
            # writer와 render product의 연결을 해제한다.
            writer.detach()
        product.destroy()
        inspection_updates = 0
        while not args.headless and app.is_running() and (args.steps is None or inspection_updates < args.steps):
            # Kit의 한 프레임을 갱신하여 렌더링·이벤트·비동기 작업을 처리한다.
            # 물리 진행 여부는 현재 타임라인의 재생 상태와 설정에 따라 달라진다.
            app.update()
            inspection_updates += 1
    finally:
        # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
        app.close()


if __name__ == '__main__':
    main()
