"""Cloner와 GridCloner로 환경 복제, 일괄 포즈 변경, 충돌 필터를 관찰합니다."""
import argparse
from itertools import count
import json
from pathlib import Path
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--steps", type=int, default=None, help="GUI: omitted keeps the window open; headless default: 600")
    parser.add_argument("--output", type=Path, help="새 결과 디렉터리; 기존 경로는 거부")
    parser.add_argument('--layout', choices=['grid', 'line'], default='grid')
    parser.add_argument('--count', type=int, default=4)
    parser.add_argument('--spacing', type=float, default=3.0)
    parser.add_argument('--copy', action='store_true', help='USD Inherits 대신 독립 복사')
    parser.add_argument('--replicate-physics', action='store_true')
    args = parser.parse_args()
    if args.steps is None and args.headless:
        args.steps = 600
    if args.steps is not None and args.steps < 1:
        parser.error("--steps must be positive")
    if args.output is None:
        parent = Path(__file__).resolve().parent / "output"
        parent.mkdir(exist_ok=True)
        output = Path(tempfile.mkdtemp(prefix="run_", dir=parent))
    else:
        output = args.output.resolve()
        output.mkdir(parents=True, exist_ok=False)
    from isaacsim import SimulationApp
    # SimulationApp은 Python에서 Isaac Sim의 Kit 애플리케이션을 시작하고 갱신·종료하는 클래스이다.
    # headless=True는 창 없이 실행한다는 뜻이며, omni와 Isaac Sim 확장 모듈은 앱 생성 후 import한다.
    app = SimulationApp({"headless": args.headless})
    try:
        import numpy as np
        from pxr import UsdGeom
        # pxr은 USD 장면을 직접 다루는 OpenUSD의 Python 바인딩이다.
        # UsdGeom은 형상, 변환, 카메라와 장면 단위·축 설정을 다룬다.
        from isaacsim.core.api import World
        # World는 Stage의 객체와 작업을 관리하고 물리·렌더링 시간 간격, 초기화, 시뮬레이션 진행을 제어한다.
        from isaacsim.core.api.objects import DynamicCuboid
        # DynamicCuboid는 큐브 형상에 강체와 충돌 속성을 함께 부여하므로 중력과 접촉에 반응한다.
        from isaacsim.core.cloner import Cloner, GridCloner
        # Cloner는 원본 Prim을 여러 경로로 복제하여 반복되는 시뮬레이션 환경을 만든다.
        # GridCloner는 복제한 환경들을 일정 간격의 격자 위치에 배치한다.
        from isaacsim.core.prims import XFormPrim
        # XFormPrim은 경로로 선택한 Prim의 위치, 회전, 스케일을 배열 단위로 다룬다.
        # Prim은 USD 장면의 객체 단위이며 같은 경로의 Prim을 감싸도 새 객체를 복제하는 것은 아니다.
        if args.count < 1 or args.spacing <= 0:
            raise ValueError('count와 spacing은 양수여야 합니다')
        # stage_units_in_meters는 장면 길이 단위이고, physics_dt·rendering_dt는 각각 물리·렌더링 시간 간격(초)이다.
        world = World(stage_units_in_meters=1.0)
        # 기본 바닥을 Scene에 추가한다. 이 바닥은 강체가 떨어졌을 때 충돌할 표면이다.
        world.scene.add_default_ground_plane()
        cloner = GridCloner(spacing=args.spacing) if args.layout == 'grid' else Cloner()
        cloner.define_base_env('/World/envs')
        # 복제본마다 사용할 서로 다른 Prim 경로를 생성한다.
        paths = cloner.generate_paths('/World/envs/env', args.count)
        # 지정한 경로에 변환용 Xform Prim을 정의한다. 자식 객체를 묶어 함께 이동·회전시킬 때 사용할 수 있다.
        UsdGeom.Xform.Define(world.stage, paths[0])
        source = DynamicCuboid(paths[0] + '/cube', name='source', size=0.5,
                               position=np.array([0., 0., 1.0]), color=np.array([0.2, 0.6, 1.0]))
        kwargs = {'source_prim_path': paths[0], 'prim_paths': paths,
                  'copy_from_source': args.copy, 'replicate_physics': args.replicate_physics}
        if args.layout == 'line':
            kwargs['positions'] = np.array([[i * args.spacing, 0., 0.] for i in range(args.count)])
        # 원본 Prim을 지정한 대상 경로들로 복제한다. 위치 배열로 각 복제본의 배치를 지정할 수 있다.
        cloner.clone(**kwargs)
        cloner.filter_collisions('/physicsScene', '/World/collisionGroups', paths,
                                 global_paths=['/World/defaultGroundPlane'])
        # 5.1 설치본의 복수 prim 래퍼는 XFormPrim이다. 문서의 XFormPrimView는 이전 이름이다.
        boxes = XFormPrim('/World/envs/env_.*/cube', name='all_boxes')
        positions, orientations = boxes.get_world_poses()
        positions[:, 2] += 1.5
        boxes.set_world_poses(positions, orientations)
        # World를 초기화하고 등록된 객체의 물리 핸들을 준비한다. 관절·강체 상태를 읽기 전에 호출한다.
        world.reset()
        initial, _ = boxes.get_world_poses()
        final = initial.copy()
        scene_path = str(output / 'cloned_scene.usda')
        # World가 사용하는 Stage의 루트 레이어를 USD 파일로 저장한다.
        world.stage.GetRootLayer().Export(scene_path)
        for step in count():
            if args.steps is not None and step >= args.steps:
                break
            if not app.is_running():
                break
            # 물리 시뮬레이션을 한 step 진행한다. render는 이 호출에서 렌더링도 수행할지 지정한다.
            world.step(render=not args.headless)
            if app.is_running():
                final, _ = boxes.get_world_poses()
        records = {'paths': paths, 'initial_positions_m': initial.tolist(),
                   'final_positions_m': final.tolist(), 'copy_from_source': args.copy,
                   'replicate_physics': args.replicate_physics}
        (output / 'poses.json').write_text(json.dumps(records, indent=2))
        if app.is_running():
            world.stage.GetRootLayer().Export(scene_path)
        print(json.dumps(records, indent=2))
        print('Output:', output)
    finally:
        # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
        app.close()


if __name__ == "__main__":
    main()
