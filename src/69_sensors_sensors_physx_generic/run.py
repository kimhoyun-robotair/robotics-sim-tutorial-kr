"""Isaac Sim 5.1 standalone sensor lab; see TUTORIAL.md for interpretation."""
import argparse
import json
from datetime import datetime
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--steps', type=int, default=None, help='Positive simulation step limit; omitted: GUI runs until closed, headless runs 240 steps')
parser.add_argument('--headless', action='store_true')
parser.add_argument('--interactive', action='store_true', help='Compatibility flag: GUI already stays open when --steps is omitted; explicit --steps takes priority')
parser.add_argument('--output', type=Path, help='New output directory; existing paths are refused')
parser.add_argument('--pattern', choices=['zigzag','two-band'], default='zigzag')

args = parser.parse_args()
if (args.steps is not None and args.steps < 1) or (args.headless and args.interactive):
    parser.error('steps must be positive; interactive requires GUI')
sample_steps = args.steps if args.steps is not None else 240
output = args.output or Path(__file__).resolve().parent / 'output' / datetime.now().strftime('%Y%m%d_%H%M%S_%f')
output.mkdir(parents=True, exist_ok=False)
from isaacsim import SimulationApp
# SimulationApp은 Python에서 Isaac Sim의 Kit 애플리케이션을 시작하고 갱신·종료하는 클래스이다.
# headless=True는 창 없이 실행한다는 뜻이며, omni와 Isaac Sim 확장 모듈은 앱 생성 후 import한다.
app = SimulationApp({'headless': args.headless, 'enable_motion_bvh': False})
try:
    import numpy as np
    import omni.usd
    # omni.usd는 현재 Kit 애플리케이션의 USD 문맥에 접근하는 모듈이다.
    # get_context().get_stage()로 객체·조명 등이 들어 있는 현재 Stage를 얻는다.
    from isaacsim.core.api import World
    # World는 Stage의 객체와 작업을 관리하고 물리·렌더링 시간 간격, 초기화, 시뮬레이션 진행을 제어한다.
    from isaacsim.core.api.objects import DynamicCuboid, FixedCuboid, VisualCuboid
    # DynamicCuboid는 큐브 형상에 강체와 충돌 속성을 함께 부여하므로 중력과 접촉에 반응한다.
    # FixedCuboid는 충돌 가능한 고정 큐브로, 바닥이나 움직이지 않는 장애물을 만들 때 사용한다.
    # VisualCuboid는 강체·충돌 속성 없이 외형만 만드는 큐브로, 목표 위치 표시 등에 사용한다.
    from pxr import UsdLux
    # pxr은 USD 장면을 직접 다루는 OpenUSD의 Python 바인딩이다.
    # UsdLux는 조명 Prim과 빛의 속성을 다룬다.
    world = World(stage_units_in_meters=1.0, physics_dt=1/60, rendering_dt=1/60)
    stage = omni.usd.get_context().get_stage()
    # 주변을 둘러싸는 DomeLight를 생성하여 장면의 환경 조명을 설정한다.
    UsdLux.DomeLight.Define(stage, '/World/Light').CreateIntensityAttr(1000)

    import omni.kit.commands
    # omni.kit.commands는 이름으로 등록된 Kit 명령을 실행하는 모듈이다.
    # execute에 명령 이름과 인자를 전달해 Prim 생성·가져오기 등의 작업을 수행한다.
    from isaacsim.core.utils.extensions import enable_extension
    # enable_extension은 이름으로 지정한 Kit 확장을 활성화하여 해당 기능과 명령을 사용할 수 있게 한다.
    from pxr import Gf
    # pxr은 USD 장면을 직접 다루는 OpenUSD의 Python 바인딩이다.
    # Gf는 벡터·행렬·쿼터니언 등 위치와 회전을 계산하는 수학 자료형을 다룬다.
    enable_extension('isaacsim.sensors.physx')
    # Kit의 한 프레임을 갱신하여 렌더링·이벤트·비동기 작업을 처리한다.
    # 물리 진행 여부는 현재 타임라인의 재생 상태와 설정에 따라 달라진다.
    app.update()
    if not app.is_running():
        raise SystemExit(0)
    from isaacsim.sensors.physx import _range_sensor
    # _range_sensor는 PhysX 기반 거리 센서의 인터페이스를 얻어 거리·광선 데이터를 읽는 바인딩이다.
    # 생성한 객체를 World의 Scene에 등록하여 이름으로 찾고 초기화할 수 있게 한다.
    world.scene.add(FixedCuboid('/World/Wall',name='wall',position=np.array([5.,0.,1.]),scale=np.array([.2,8.,4.]),size=1))
    # 광선 패턴을 지정할 수 있는 PhysX 거리 센서를 생성한다. 범위와 샘플링 속도를 인자로 설정한다.
    success,sensor=omni.kit.commands.execute('RangeSensorCreateGeneric',path='/World/Generic',translation=Gf.Vec3d(0,0,1),min_range=.1,max_range=20,draw_points=True,draw_lines=False,sampling_rate=2400)
    if not success:
        raise RuntimeError('Generic sensor creation failed')
    path=str(sensor.GetPath())
    interface=_range_sensor.acquire_generic_sensor_interface()
    phase=np.linspace(0,1,12000,endpoint=False)
    azimuth=.5*(2/np.pi)*np.arcsin(np.sin(2*np.pi*10*phase))
    elevation=.2*np.sin(2*np.pi*phase) if args.pattern == 'zigzag' else np.where(phase < .5,-.2,.2)
    pattern=np.stack((azimuth,elevation)).copy()
    offsets=np.zeros((pattern.shape[1],3))
    # World를 초기화하고 등록된 객체의 물리 핸들을 준비한다. 관절·강체 상태를 읽기 전에 호출한다.
    world.reset()
    batches=0
    for _ in range(sample_steps):
        if not app.is_running():
            raise SystemExit(0)
        # 물리 시뮬레이션을 한 step 진행한다. render는 이 호출에서 렌더링도 수행할지 지정한다.
        world.step(render=True)
        if not app.is_running():
            raise SystemExit(0)
        if interface.send_next_batch(path):
            interface.set_next_batch_rays(path,pattern)
            interface.set_next_batch_offsets(path,offsets)
            batches+=1
    world.pause()
    app.update()
    if not app.is_running():
        raise SystemExit(0)
    # 광선 방향으로 측정한 선형 거리를 읽는다. 원시 정규화 깊이 값과 구분되는 거리 데이터이다.
    depth=np.asarray(interface.get_linear_depth_data(path))
    if not depth.size:
        raise RuntimeError('No generic sensor depth; inspect batching and sampling rate')
    np.savez(output/'pattern_and_depth.npz',angles_rad=pattern,origin_offsets_m=offsets,depth_m=depth)
    (output/'measurements.json').write_text(json.dumps({'batches_sent':batches,'rays_in_batch':int(pattern.shape[1]),'last_depth_count':int(depth.size),'min_depth_m':float(depth.min())},indent=2))
    print(f'Output: {output.resolve()}')
    if args.steps is None and not args.headless:
        print('Snapshot saved. Live simulation continues until you close the GUI; files are not appended.')
        world.play()
        while app.is_running():
            world.step(render=True)
            if not app.is_running():
                break
            if world.is_playing():
                if interface.send_next_batch(path):
                    interface.set_next_batch_rays(path, pattern)
                    interface.set_next_batch_offsets(path, offsets)
                depth = np.asarray(interface.get_linear_depth_data(path))
finally:
    # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
    app.close()
