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
    # SimulationApp은 Python에서 Isaac Sim의 Kit 애플리케이션을 시작하고 갱신·종료하는 클래스이다.
    # headless=True는 창 없이 실행한다는 뜻이며, omni와 Isaac Sim 확장 모듈은 앱 생성 후 import한다.
    app = SimulationApp({'headless': args.headless})
    try:
        import carb.settings
        # carb.settings는 경로 형태의 키로 Kit의 렌더링·시뮬레이션 설정을 읽고 변경하는 API이다.
        import omni.graph.core as og
        # omni.graph.core는 노드와 연결로 실행 흐름을 구성하는 OmniGraph API이다.
        # Controller.edit에서 노드 생성, 입력값 설정, 출력과 입력의 연결을 정의한다.
        import omni.replicator.core as rep
        # omni.replicator.core는 장면 무작위화와 합성 데이터 생성을 위한 API이다.
        # render product는 카메라의 렌더링 출력이며, annotator는 데이터를 추출하고 writer는 결과를 저장한다.
        import omni.usd
        # omni.usd는 현재 Kit 애플리케이션의 USD 문맥에 접근하는 모듈이다.
        # get_context().get_stage()로 객체·조명 등이 들어 있는 현재 Stage를 얻는다.
        from isaacsim.core.utils.extensions import enable_extension
        # enable_extension은 이름으로 지정한 Kit 확장을 활성화하여 해당 기능과 명령을 사용할 수 있게 한다.
        from omni.replicator.core.scripts.utils import ReplicatorWrapper, create_node, set_target_prims
        # ReplicatorWrapper는 사용자 함수를 Replicator의 노드 기반 호출 방식에 연결하는 데 사용한다.
        # create_node는 Replicator에서 사용할 OmniGraph 노드를 생성한다.
        # set_target_prims는 노드가 처리할 대상 Prim을 연결한다.
        from pxr import UsdGeom, UsdLux
        # pxr은 USD 장면을 직접 다루는 OpenUSD의 Python 바인딩이다.
        # UsdGeom은 형상, 변환, 카메라와 장면 단위·축 설정을 다룬다.
        # UsdLux는 조명 Prim과 빛의 속성을 다룬다.
        enable_extension('omni.graph.scriptnode')
        carb.settings.get_settings().set_bool('/app/omni.graph.scriptnode/opt_in', True)
        # 새 USD Stage를 열어 이 예제의 장면을 구성한다.
        omni.usd.get_context().new_stage()
        stage = omni.usd.get_context().get_stage()
        # USD 장면에서 위쪽으로 사용할 축을 지정한다.
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
        # USD 좌표 한 단위가 몇 미터인지 지정하여 장면의 길이 단위를 맞춘다.
        UsdGeom.SetStageMetersPerUnit(stage, 1.0)
        # 주변을 둘러싸는 DomeLight를 생성하여 장면의 환경 조명을 설정한다.
        UsdLux.DomeLight.Define(stage, '/World/Light').CreateIntensityAttr(800)
        regions = [('inside', 0.0, 0.7, 'Cube'), ('surface', 1.4, 1.4, 'Sphere'), ('shell', 2.1, 2.6, 'Cylinder')]
        groups = {}
        for name, _, _, shape in regions:
            groups[name] = []
            for index in range(args.count):
                prim = stage.DefinePrim(f'/World/{name}/item_{index}', shape)
                # Prim의 변환 연산에 접근한다. AddTranslateOp·AddRotateXYZOp·AddScaleOp로 이동·회전·스케일을 기록할 수 있다.
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
            # OmniGraph의 노드와 입력값을 만들고 포트를 연결한다.
            # 실행 포트는 처리 순서를, 데이터 포트는 시간·센서·관절 값의 전달 경로를 정한다.
            graph, nodes, _, _ = og.Controller.edit(
                {'graph_path': '/World/SamplingGraph', 'evaluator_name': 'push'},
                {og.Controller.Keys.CREATE_NODES: [(name, 'omni.graph.scriptnode.ScriptNode') for name, *_ in regions]},
            )
            for index, ((name, inner, outer, _), node) in enumerate(zip(regions, nodes)):
                configure(node, groups[name], inner, outer, args.seed + index)
        elif args.method == 'replicator':
            # 프레임 트리거 안에 정의한 무작위화 작업을 Replicator 캡처 흐름에 연결한다.
            with rep.trigger.on_frame():
                for index, (name, inner, outer, _) in enumerate(regions):
                    sample_region(groups[name], inner, outer, args.seed + index)
        camera = rep.create.camera(position=(7, 7, 5), look_at=(0, 0, 0))
        # 카메라와 해상도를 연결한 render product를 만든다. 이후 annotator나 writer를 여기에 연결한다.
        product = rep.create.render_product(camera, (480, 360))
        # 등록된 writer를 이름으로 선택한다. initialize로 출력 설정을 지정한 뒤 render product에 연결한다.
        writer = rep.WriterRegistry.get('BasicWriter')
        writer.initialize(output_dir=str(output / 'rgb'), rgb=True)
        # writer를 render product에 연결하여 캡처한 데이터가 writer로 전달되게 한다.
        writer.attach(product)
        # 타임라인 재생에 따른 자동 캡처 여부를 설정한다. False이면 아래의 명시적 캡처 호출로 제어한다.
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
                # 지정한 OmniGraph를 동기적으로 평가하여 노드의 계산 결과를 갱신한다.
                og.Controller.evaluate_sync(graph)
            # Replicator의 캡처를 한 번 진행한다. rt_subframes는 캡처를 위한 렌더링 누적 프레임 수이다.
            rep.orchestrator.step(rt_subframes=4, delta_time=0.0)
            for name, inner, outer, _ in regions:
                positions = [list(stage.GetPrimAtPath(path).GetAttribute('xformOp:translate').Get()) for path in groups[name]]
                distances = [math.sqrt(sum(v * v for v in point)) for point in positions]
                if not all(inner - 1e-6 <= d <= outer + 1e-6 for d in distances):
                    raise RuntimeError(f'{name}: sample outside required radius range; node execution may have failed')
                measurements.append({'frame': frame, 'region': name, 'min_radius': min(distances), 'max_radius': max(distances), 'positions': positions})
                print(f'{frame=} {name}: radius [{min(distances):.4f}, {max(distances):.4f}]')
        # 예약된 합성 데이터 처리와 writer의 저장 작업이 끝날 때까지 기다린다.
        rep.orchestrator.wait_until_complete()
        # Stage의 루트 레이어를 USD 파일로 내보낸다. 참조 자산 자체를 모두 복사하는 것은 아니다.
        stage.GetRootLayer().Export(str(output / 'sampling.usda'))
        (output / 'samples.json').write_text(json.dumps(measurements, indent=2))
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
