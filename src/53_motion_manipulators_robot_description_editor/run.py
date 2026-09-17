"""Open a non-instanceable Franka reference for the native Lula/XRDF editor."""
import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--steps', type=int, default=None,
                        help='App update limit; omitted/0 keeps the GUI open until closed')
    parser.add_argument('--frames', type=int, default=0,
                        help='Legacy headless update limit when --steps is omitted; does not limit GUI')
    parser.add_argument('--headless', action='store_true')
    args = parser.parse_args()
    if args.steps is None:
        args.steps = args.frames if args.headless else 0
    if args.frames < 0 or args.steps < 0 or (args.headless and args.steps == 0):
        parser.error('nonnegative limits required; headless requires positive --steps (or legacy --frames)')
    from isaacsim import SimulationApp
    # SimulationApp은 Python에서 Isaac Sim의 Kit 애플리케이션을 시작하고 갱신·종료하는 클래스이다.
    # headless=True는 창 없이 실행한다는 뜻이며, omni와 Isaac Sim 확장 모듈은 앱 생성 후 import한다.

    app = SimulationApp({'headless': args.headless})
    try:
        from isaacsim.core.api import World
        # World는 Stage의 객체와 작업을 관리하고 물리·렌더링 시간 간격, 초기화, 시뮬레이션 진행을 제어한다.
        from isaacsim.core.utils.extensions import enable_extension
        # enable_extension은 이름으로 지정한 Kit 확장을 활성화하여 해당 기능과 명령을 사용할 수 있게 한다.
        from isaacsim.core.utils.stage import add_reference_to_stage, get_current_stage
        # add_reference_to_stage는 외부 USD 자산을 현재 Stage의 지정한 Prim 경로에 참조로 연결한다.
        # get_current_stage는 현재 Isaac Sim에서 열려 있는 USD Stage를 반환한다.
        from isaacsim.storage.native import get_assets_root_path
        # get_assets_root_path는 Isaac Sim 기본 자산의 루트 경로를 찾는다.
        # 반환 경로에 로봇·환경 USD의 상대 경로를 붙여 사용할 수 있다.
        enable_extension('isaacsim.robot_setup.xrdf_editor')
        assets = get_assets_root_path()
        if assets is None:
            raise RuntimeError('Isaac Sim 5.1 asset root is unavailable')
        # stage_units_in_meters는 장면 길이 단위이고, physics_dt·rendering_dt는 각각 물리·렌더링 시간 간격(초)이다.
        world = World(stage_units_in_meters=1.0)
        # 기본 바닥을 Scene에 추가한다. 이 바닥은 강체가 떨어졌을 때 충돌할 표면이다.
        world.scene.add_default_ground_plane()
        add_reference_to_stage(assets + '/Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd', '/World/Franka')
        stage = get_current_stage()
        # Stage의 Prim 계층을 순회하여 형상·관절·스키마 정보를 검사한다.
        for prim in list(stage.Traverse()):
            if prim.IsInstanceable():
                # Prim의 instanceable 여부를 설정하여 참조한 자산의 인스턴싱 사용을 제어한다.
                prim.SetInstanceable(False)
        # World를 초기화하고 등록된 객체의 물리 핸들을 준비한다. 관절·강체 상태를 읽기 전에 호출한다.
        world.reset()
        print('Select /World/Franka in Tools > Robotics > Lula Robot Description Editor.')
        frame = 0
        while app.is_running() and (args.steps == 0 or frame < args.steps):
            # Kit의 한 프레임을 갱신하여 렌더링·이벤트·비동기 작업을 처리한다.
            # 물리 진행 여부는 현재 타임라인의 재생 상태와 설정에 따라 달라진다.
            app.update()
            frame += 1
    finally:
        # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
        app.close()


if __name__ == '__main__':
    main()
