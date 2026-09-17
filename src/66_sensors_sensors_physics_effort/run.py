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
parser.add_argument('--mass', type=float, default=1)
parser.add_argument('--period', type=float, default=.1)

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

    from pxr import UsdGeom,UsdPhysics,Gf
    # pxr은 USD 장면을 직접 다루는 OpenUSD의 Python 바인딩이다.
    # UsdGeom은 형상, 변환, 카메라와 장면 단위·축 설정을 다룬다.
    # UsdPhysics는 강체·충돌·관절·물리 재질의 USD 스키마를 다룬다.
    # Gf는 벡터·행렬·쿼터니언 등 위치와 회전을 계산하는 수학 자료형을 다룬다.
    from isaacsim.core.prims import SingleArticulation
    # SingleArticulation은 하나의 관절 구조를 감싸 관절 위치·속도·힘을 읽고 제어한다.
    # 기본 바닥을 Scene에 추가한다. 이 바닥은 강체가 떨어졌을 때 충돌할 표면이다.
    world.scene.add_default_ground_plane()
    # 지정한 경로에 변환용 Xform Prim을 정의한다. 자식 객체를 묶어 함께 이동·회전시킬 때 사용할 수 있다.
    UsdGeom.Xform.Define(stage,'/World/Arm')
    root=DynamicCuboid('/World/Arm/Base',name='base',position=np.array([0.,0.,2.]),size=.2,mass=1)
    link=DynamicCuboid('/World/Arm/Link',name='link',position=np.array([.75,0.,2.]),scale=np.array([1.5,.15,.15]),size=1,mass=args.mass)
    # 연결한 두 몸체의 상대 자세를 고정하는 관절을 정의한다.
    fixed=UsdPhysics.FixedJoint.Define(stage,'/World/Arm/FixedRoot')
    fixed.CreateBody1Rel().SetTargets(['/World/Arm/Base'])
    fixed.CreateLocalPos0Attr(Gf.Vec3f(0,0,2))
    # 관절로 연결된 구조의 articulation 루트를 지정한다.
    UsdPhysics.ArticulationRootAPI.Apply(fixed.GetPrim())
    # 두 몸체 사이의 회전 관절을 정의한다. 연결 대상과 관절 축·제한을 이어서 지정한다.
    joint=UsdPhysics.RevoluteJoint.Define(stage,'/World/Arm/Joint')
    joint.CreateBody0Rel().SetTargets(['/World/Arm/Base'])
    joint.CreateBody1Rel().SetTargets(['/World/Arm/Link'])
    joint.CreateLocalPos0Attr(Gf.Vec3f(0,0,0))
    joint.CreateLocalPos1Attr(Gf.Vec3f(-.75,0,0))
    joint.CreateAxisAttr('Y')
    joint.CreateLowerLimitAttr(-80)
    joint.CreateUpperLimitAttr(80)
    # 관절에 구동 API를 적용한다. stiffness·damping·목표값으로 관절 구동 방식을 설정한다.
    drive=UsdPhysics.DriveAPI.Apply(joint.GetPrim(),'angular')
    drive.CreateStiffnessAttr(100)
    drive.CreateDampingAttr(10)
    drive.CreateTargetPositionAttr(0)
    # 생성한 객체를 World의 Scene에 등록하여 이름으로 찾고 초기화할 수 있게 한다.
    robot=world.scene.add(SingleArticulation('/World/Arm',name='arm'))

    from isaacsim.sensors.physics import EffortSensor
    # EffortSensor는 지정한 관절에서 effort를 읽는 센서이며 회전 관절에서는 토크를 측정한다.
    sensor=EffortSensor('/World/Arm/Joint',sensor_period=args.period,use_latest_data=False,enabled=True)
    # World를 초기화하고 등록된 객체의 물리 핸들을 준비한다. 관절·강체 상태를 읽기 전에 호출한다.
    world.reset()
    rows=[]
    for _ in range(sample_steps):
        if not app.is_running():
            raise SystemExit(0)
        # 물리 시뮬레이션을 한 step 진행한다. render는 이 호출에서 렌더링도 수행할지 지정한다.
        world.step(render=True)
        if not app.is_running():
            raise SystemExit(0)
        # 센서 측정값을 읽는다. 값과 함께 유효 여부 및 측정 시점을 확인해야 한다.
        sampled=sensor.get_sensor_reading(use_latest_data=False)
        latest=sensor.get_sensor_reading(use_latest_data=True)
        rows.append({'physics_time_s':float(world.current_time),'sensor_time_s':float(sampled.time),'valid':bool(sampled.is_valid),'sampled_torque_Nm':float(sampled.value),'latest_torque_Nm':float(latest.value)})
    if not any(row['valid'] for row in rows):
        raise RuntimeError('Effort sensor never initialized')
    (output/'effort.json').write_text(json.dumps(rows,indent=2))
    # Stage의 루트 레이어를 USD 파일로 내보낸다. 참조 자산 자체를 모두 복사하는 것은 아니다.
    stage.GetRootLayer().Export(str(output/'arm.usda'))
    print(f'Output: {output.resolve()}')
    if args.steps is None and not args.headless:
        print('Snapshot saved. Live simulation continues until you close the GUI; files are not appended.')
        while app.is_running():
            world.step(render=True)
            if not app.is_running():
                break
            if world.is_playing():
                sampled = sensor.get_sensor_reading(use_latest_data=False)
                latest = sensor.get_sensor_reading(use_latest_data=True)
finally:
    # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
    app.close()
