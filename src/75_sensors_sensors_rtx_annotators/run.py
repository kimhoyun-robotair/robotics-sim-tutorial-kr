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
parser.add_argument('--config', default='Example_Rotary')
parser.add_argument('--scan-hz', type=float, default=10)

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

    from isaacsim.core.utils.extensions import enable_extension
    # enable_extension은 이름으로 지정한 Kit 확장을 활성화하여 해당 기능과 명령을 사용할 수 있게 한다.
    enable_extension('isaacsim.sensors.rtx')
    # Kit의 한 프레임을 갱신하여 렌더링·이벤트·비동기 작업을 처리한다.
    # 물리 진행 여부는 현재 타임라인의 재생 상태와 설정에 따라 달라진다.
    app.update()
    if not app.is_running():
        raise SystemExit(0)
    from isaacsim.sensors.rtx import LidarRtx
    # LidarRtx는 RTX 렌더링을 이용하는 LiDAR를 구성하고 annotator를 통해 측정 데이터를 제공한다.
    # 기본 바닥을 Scene에 추가한다. 이 바닥은 강체가 떨어졌을 때 충돌할 표면이다.
    world.scene.add_default_ground_plane()
    for i, position in enumerate(([5,0,1],[-5,0,1],[0,5,1],[0,-5,1])):
        # 생성한 객체를 World의 Scene에 등록하여 이름으로 찾고 초기화할 수 있게 한다.
        world.scene.add(FixedCuboid(prim_path=f'/World/Wall{i}',name=f'wall{i}',position=np.array(position),scale=np.array([1,1,2]),size=1))
    sensor = LidarRtx('/World/Lidar',translation=np.array([0.,0.,1.]),orientation=np.array([1.,0.,0.,0.]),config_file_name=args.config,**{'omni:sensor:Core:scanRateBaseHz':args.scan_hz})
    # World를 초기화하고 등록된 객체의 물리 핸들을 준비한다. 관절·강체 상태를 읽기 전에 호출한다.
    world.reset()
    sensor.initialize()

    names = ['IsaacExtractRTXSensorPointCloudNoAccumulator','IsaacCreateRTXLidarScanBuffer']
    # 센서에 annotator를 연결하여 필요한 종류의 RTX 측정 데이터를 생성한다.
    sensor.attach_annotator(names[0])
    sensor.attach_annotator(names[1],outputTimestamp=True,outputDistance=True,outputIntensity=True)
    counts=[]
    for _ in range(sample_steps):
        if not app.is_running():
            raise SystemExit(0)
        # 물리 시뮬레이션을 한 step 진행한다. render는 이 호출에서 렌더링도 수행할지 지정한다.
        world.step(render=True)
        if not app.is_running():
            raise SystemExit(0)
        # 센서의 현재 프레임 데이터를 읽는다. 초기화 후 시뮬레이션·렌더링 갱신이 선행되어야 한다.
        frame=sensor.get_current_frame()
        counts.append({name:int(np.asarray(frame.get(name,{}).get('data',[])).shape[0]) for name in names})
    arrays={}
    for name in names:
        data=frame.get(name,{})
        for key,value in data.items():
            if isinstance(value,np.ndarray):
                arrays[name+'__'+key]=value
        if np.asarray(data.get('data',[])).size == 0:
            raise RuntimeError(f'No data in {name}; at least a full rotation is required')
    np.savez(output/'annotators.npz',**arrays)
    (output/'measurements.json').write_text(json.dumps({'counts':counts,'arrays':{k:list(v.shape) for k,v in arrays.items()}},indent=2))
    print(f'Output: {output.resolve()}')
    if args.steps is None and not args.headless:
        print('Snapshot saved. Live simulation continues until you close the GUI; files are not appended.')
        while app.is_running():
            world.step(render=True)
            if not app.is_running():
                break
            if world.is_playing():
                frame = sensor.get_current_frame()
    if app.is_running():
        sensor.detach_all_annotators()
finally:
    # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
    app.close()
