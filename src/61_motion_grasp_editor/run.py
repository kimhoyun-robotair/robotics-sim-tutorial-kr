"""Open the official gripper/object stage and enable the native Grasp Editor."""
import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', required=True, type=Path, help='Local USD extracted from the official tutorial ZIP')
    parser.add_argument('--steps', type=int, default=None,
                        help='App update limit; omitted/0 keeps the GUI open until closed')
    parser.add_argument('--frames', type=int, default=0,
                        help='Legacy headless update limit when --steps is omitted; does not limit GUI')
    parser.add_argument('--headless', action='store_true')
    args = parser.parse_args()
    if not args.stage.is_file():
        parser.error(f'Missing USD: {args.stage}')
    if args.steps is None:
        args.steps = args.frames if args.headless else 0
    if args.frames < 0 or args.steps < 0 or (args.headless and args.steps == 0):
        parser.error('nonnegative limits required; headless requires positive --steps (or legacy --frames)')
    from isaacsim import SimulationApp
    # SimulationApp은 Python에서 Isaac Sim의 Kit 애플리케이션을 시작하고 갱신·종료하는 클래스이다.
    # headless=True는 창 없이 실행한다는 뜻이며, omni와 Isaac Sim 확장 모듈은 앱 생성 후 import한다.

    app = SimulationApp({'headless': args.headless})
    try:
        import omni.usd
        # omni.usd는 현재 Kit 애플리케이션의 USD 문맥에 접근하는 모듈이다.
        # get_context().get_stage()로 객체·조명 등이 들어 있는 현재 Stage를 얻는다.
        from isaacsim.core.utils.extensions import enable_extension
        # enable_extension은 이름으로 지정한 Kit 확장을 활성화하여 해당 기능과 명령을 사용할 수 있게 한다.
        enable_extension('isaacsim.robot_setup.grasp_editor')
        # USD 파일을 Kit의 현재 Stage로 연다.
        if not omni.usd.get_context().open_stage(str(args.stage.resolve())):
            raise RuntimeError('Could not open tutorial stage')
        count = 0
        while app.is_running() and (args.steps == 0 or count < args.steps):
            # Kit의 한 프레임을 갱신하여 렌더링·이벤트·비동기 작업을 처리한다.
            # 물리 진행 여부는 현재 타임라인의 재생 상태와 설정에 따라 달라진다.
            app.update()
            count += 1
    finally:
        # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
        app.close()


if __name__ == '__main__':
    main()
