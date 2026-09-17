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
parser.add_argument('--lens', choices=['none','pinhole','fisheye'], default='none')

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

    from isaacsim.sensors.camera import Camera
    # Camera는 USD 카메라와 렌더링 출력을 연결하여 RGB·깊이 등의 센서 데이터를 얻는 클래스이다.
    from isaacsim.core.utils.numpy.rotations import euler_angles_to_quats
    # euler_angles_to_quats는 여러 Euler 회전을 NumPy 배열로 받아 쿼터니언 배열로 변환한다.
    # 기본 바닥을 Scene에 추가한다. 이 바닥은 강체가 떨어졌을 때 충돌할 표면이다.
    world.scene.add_default_ground_plane()
    for i, x in enumerate((-1.0, 0.0, 1.0)):
        # 생성한 객체를 World의 Scene에 등록하여 이름으로 찾고 초기화할 수 있게 한다.
        world.scene.add(FixedCuboid(prim_path=f'/World/Box{i}', name=f'box{i}', position=np.array([x, 0, .5]), size=.8, color=np.array([i/2, .3, 1-i/2])))
    camera = Camera('/World/Camera', position=np.array([0., 0., 5.]), orientation=euler_angles_to_quats(np.array([0.,90.,0.]), degrees=True), resolution=(640,480), frequency=30)
    # World를 초기화하고 등록된 객체의 물리 핸들을 준비한다. 관절·강체 상태를 읽기 전에 호출한다.
    world.reset()
    # 카메라의 렌더링·데이터 수집 연결을 초기화한다.
    camera.initialize()
    camera.add_motion_vectors_to_frame()
    camera.set_focal_length(.018)
    camera.set_horizontal_aperture(.036)
    camera.set_vertical_aperture(.027)
    camera.set_lens_aperture(0)
    if args.lens == 'none':
        camera.set_opencv_pinhole_properties(cx=320, cy=240, fx=320, fy=320, pinhole=[0.0]*12)
    elif args.lens == 'pinhole':
        camera.set_opencv_pinhole_properties(cx=320, cy=240, fx=320, fy=320, pinhole=[.14,-.03,0,0,.009,0,0,0])
    elif args.lens == 'fisheye':
        camera.set_opencv_fisheye_properties(cx=320, cy=240, fx=320, fy=320, fisheye=[.05,.01,-.003,-.0005])
    for _ in range(sample_steps):
        if not app.is_running():
            raise SystemExit(0)
        # 물리 시뮬레이션을 한 step 진행한다. render는 이 호출에서 렌더링도 수행할지 지정한다.
        world.step(render=True)
        if not app.is_running():
            raise SystemExit(0)
    # 카메라에서 RGBA 화소 배열을 읽는다. 유효한 영상을 얻으려면 렌더링 프레임이 필요하다.
    rgba = camera.get_rgba()
    if rgba.size == 0:
        raise RuntimeError('Camera returned no image; increase steps and inspect renderer logs')
    from PIL import Image
    Image.fromarray(rgba.astype(np.uint8)).save(output/'rgba.png')
    points = np.array([[-1.,0.,.9],[0.,0.,.9],[1.,0.,.9]])
    intrinsic = np.array([[320.,0.,320.],[0.,320.,240.],[0.,0.,1.]])
    world_homogeneous = np.column_stack((points,np.ones(len(points))))
    image_homogeneous = (intrinsic @ camera.get_view_matrix_ros()[:3,:] @ world_homogeneous.T).T
    projected = image_homogeneous[:,:2] / image_homogeneous[:,2:3] if args.lens != 'fisheye' else np.empty((0,2))
    # 카메라에 연결된 annotator의 현재 프레임 데이터를 읽는다.
    frame = camera.get_current_frame()
    np.savez(output/'camera.npz', rgba=rgba, projected_points=projected, motion_vectors=frame['motion_vectors'])
    (output/'measurements.json').write_text(json.dumps({'lens':args.lens,'rgba_shape':list(rgba.shape),'projected_points':projected.tolist(),'projection_note':'Ideal pinhole projection of configured K; distorted lens modes require their own distortion mapping','intrinsic_matrix':intrinsic.tolist()},indent=2))
    # Stage의 루트 레이어를 USD 파일로 내보낸다. 참조 자산 자체를 모두 복사하는 것은 아니다.
    stage.GetRootLayer().Export(str(output/'scene.usda'))
    print(f'Output: {output.resolve()}')
    if args.steps is None and not args.headless:
        print('Snapshot saved. Live simulation continues until you close the GUI; files are not appended.')
        while app.is_running():
            world.step(render=True)
            if not app.is_running():
                break
            if world.is_playing():
                frame = camera.get_current_frame()
finally:
    # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
    app.close()
