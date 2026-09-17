"""Isaac Sim 5.1 standalone sensor lab; see TUTORIAL.md for interpretation."""
import argparse
import json
from datetime import datetime
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--steps', type=int, default=None, help='Positive acquisition frame limit; omitted: record 240 frames, then keep GUI open (headless: exit after 240)')
parser.add_argument('--headless', action='store_true')
parser.add_argument('--interactive', action='store_true', help='Compatibility option: GUI stays open by default; explicit --steps still exits')
parser.add_argument('--output', type=Path, help='New output directory; existing paths are refused')
parser.add_argument('--height', type=float, default=2)
parser.add_argument('--ccd', action='store_true')

args = parser.parse_args()
if (args.steps is not None and args.steps < 1) or (args.headless and args.interactive):
    parser.error('steps must be positive; interactive requires GUI')
acquisition_steps = args.steps if args.steps is not None else 240
keep_gui_open = not args.headless and args.steps is None
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

    from pxr import UsdPhysics,PhysxSchema
    # pxr은 USD 장면을 직접 다루는 OpenUSD의 Python 바인딩이다.
    # UsdPhysics는 강체·충돌·관절·물리 재질의 USD 스키마를 다룬다.
    # PhysxSchema는 PhysX 전용 물리 설정을 USD Prim에 기록하는 스키마를 다룬다.
    # 기본 바닥을 Scene에 추가한다. 이 바닥은 강체가 떨어졌을 때 충돌할 표면이다.
    world.scene.add_default_ground_plane()
    # 생성한 객체를 World의 Scene에 등록하여 이름으로 찾고 초기화할 수 있게 한다.
    with_collision=world.scene.add(DynamicCuboid('/World/WithCollider',name='with_collision',position=np.array([-1.,0.,args.height]),size=.5,mass=1))
    without_collision=world.scene.add(DynamicCuboid('/World/WithoutCollider',name='without_collision',position=np.array([1.,0.,args.height]),size=.5,mass=1))
    UsdPhysics.CollisionAPI(without_collision.prim).GetCollisionEnabledAttr().Set(False)
    if args.ccd:
        scene=world.get_physics_context().get_current_physics_scene_prim()
        PhysxSchema.PhysxSceneAPI.Apply(scene).CreateEnableCCDAttr(True)
        PhysxSchema.PhysxRigidBodyAPI.Apply(with_collision.prim).CreateEnableCCDAttr(True)
    # World를 초기화하고 등록된 객체의 물리 핸들을 준비한다. 관절·강체 상태를 읽기 전에 호출한다.
    world.reset()
    rows=[]
    for _ in range(acquisition_steps):
        if not app.is_running():
            break
        # 물리 시뮬레이션을 한 step 진행한다. render는 이 호출에서 렌더링도 수행할지 지정한다.
        world.step(render=True)
        rows.append({'time_s':float(world.current_time),'with_collider_z':float(with_collision.get_world_pose()[0][2]),'without_collider_z':float(without_collision.get_world_pose()[0][2])})
    (output/'fall.json').write_text(json.dumps(rows,indent=2))
    # Stage의 루트 레이어를 USD 파일로 내보낸다. 참조 자산 자체를 모두 복사하는 것은 아니다.
    stage.GetRootLayer().Export(str(output/'scene.usda'))
    print(f'Output: {output.resolve()}')
    while keep_gui_open and app.is_running():
        world.step(render=True)
finally:
    # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
    app.close()
