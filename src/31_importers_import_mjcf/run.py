"""Convert a local MJCF pendulum or installed humanoid/ant, then inspect real USD joints."""
import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', choices=('local', 'ant', 'humanoid'), default='local')
    parser.add_argument('--steps', type=int, default=None, help='Execution limit; omitted or 0 keeps the GUI open')
    parser.add_argument('--headless', action='store_true')
    parser.add_argument('--output', type=Path, default=Path(__file__).parent / 'output')
    args = parser.parse_args()
    if args.steps is None:
        args.steps = 300 if args.headless else 0
    if args.steps < 0 or (args.headless and args.steps == 0):
        parser.error("--steps must be nonnegative; headless requires a positive limit")
    if args.output.exists():
        parser.error('a new output directory is required')
    args.output.mkdir(parents=True)
    from isaacsim import SimulationApp
    # SimulationApp은 Python에서 Isaac Sim의 Kit 애플리케이션을 시작하고 갱신·종료하는 클래스이다.
    # headless=True는 창 없이 실행한다는 뜻이며, omni와 Isaac Sim 확장 모듈은 앱 생성 후 import한다.

    app = SimulationApp({'headless': args.headless})
    try:
        import omni.kit.commands
        # omni.kit.commands는 이름으로 등록된 Kit 명령을 실행하는 모듈이다.
        # execute에 명령 이름과 인자를 전달해 Prim 생성·가져오기 등의 작업을 수행한다.
        from isaacsim.core.api import World
        # World는 Stage의 객체와 작업을 관리하고 물리·렌더링 시간 간격, 초기화, 시뮬레이션 진행을 제어한다.
        from isaacsim.core.utils.extensions import enable_extension, get_extension_path_from_name
        # enable_extension은 이름으로 지정한 Kit 확장을 활성화하여 해당 기능과 명령을 사용할 수 있게 한다.
        # get_extension_path_from_name은 확장의 설치 경로를 찾아 내부 설정·예제 파일에 접근할 때 사용한다.
        from isaacsim.core.utils.stage import get_current_stage
        # get_current_stage는 현재 Isaac Sim에서 열려 있는 USD Stage를 반환한다.
        from pxr import UsdPhysics
        # pxr은 USD 장면을 직접 다루는 OpenUSD의 Python 바인딩이다.
        # UsdPhysics는 강체·충돌·관절·물리 재질의 USD 스키마를 다룬다.
        enable_extension('isaacsim.asset.importer.mjcf')
        # stage_units_in_meters는 장면 길이 단위이고, physics_dt·rendering_dt는 각각 물리·렌더링 시간 간격(초)이다.
        world = World(stage_units_in_meters=1.0, physics_dt=0.01, rendering_dt=0.01)
        # 기본 바닥을 Scene에 추가한다. 이 바닥은 강체가 떨어졌을 때 충돌할 표면이다.
        world.scene.add_default_ground_plane()
        source = Path(__file__).parent / 'pendulum.xml'
        if args.model != 'local':
            source = Path(get_extension_path_from_name('isaacsim.asset.importer.mjcf')) / 'data/mjcf' / f'nv_{args.model}.xml'
        # MJCF 가져오기 옵션 객체를 만든다. 아래에서 베이스 고정 등의 속성을 설정한다.
        ok, config = omni.kit.commands.execute('MJCFCreateImportConfig')
        if not ok:
            raise RuntimeError('MJCF configuration could not be created')
        config.set_fix_base(args.model == 'local')
        config.set_make_default_prim(False)
        # MJCF 파일의 로봇 모델을 USD 자산으로 가져온다.
        ok, result = omni.kit.commands.execute(
            'MJCFCreateAsset', mjcf_path=str(source.resolve()), import_config=config, prim_path='/World/Imported',
        )
        stage = get_current_stage()
        if not ok or not stage.GetPrimAtPath('/World/Imported').IsValid():
            raise RuntimeError(f'MJCF import failed: {result}')
        # Stage의 Prim 계층을 순회하여 형상·관절·스키마 정보를 검사한다.
        joints = [str(prim.GetPath()) for prim in stage.Traverse() if prim.IsA(UsdPhysics.Joint)]
        if not joints:
            raise RuntimeError('Imported model contains no USD physics joint')
        # Stage의 루트 레이어를 USD 파일로 내보낸다. 참조 자산 자체를 모두 복사하는 것은 아니다.
        stage.GetRootLayer().Export(str(args.output / 'imported.usda'))
        # World를 초기화하고 등록된 객체의 물리 핸들을 준비한다. 관절·강체 상태를 읽기 전에 호출한다.
        world.reset()
        stage_meters_per_unit = stage.GetMetadata("metersPerUnit")
        step = 0
        while app.is_running() and (args.steps == 0 or step < args.steps):
            # 물리 시뮬레이션을 한 step 진행한다. render는 이 호출에서 렌더링도 수행할지 지정한다.
            world.step(render=not args.headless)
            step += 1
        report = {'source': str(source), 'joints': joints, 'stage_meters_per_unit': stage_meters_per_unit}
        (args.output / 'report.json').write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2))
    finally:
        # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
        app.close()


if __name__ == '__main__':
    main()
