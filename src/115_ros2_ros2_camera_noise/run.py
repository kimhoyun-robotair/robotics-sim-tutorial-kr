"""Publish clean RGB alongside Replicator-augmented RGB from a rotating camera."""
import argparse


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--steps', type=int, default=None, help='Simulation steps before exit; omitted: GUI until closed, headless uses --frames')
    parser.add_argument('--frames', type=int, default=1800, help='Legacy headless step limit when --steps is omitted; does not close the GUI')
    parser.add_argument('--headless', action='store_true')
    parser.add_argument('--sigma', type=float, default=0.1, help='Noise stddev relative to 255; range 0..1')
    parser.add_argument('--seed', type=int, default=1234)
    parser.add_argument('--device', choices=['cpu','cuda'], default='cpu')
    args=parser.parse_args()
    if args.frames < 1 or not 0 <= args.sigma <= 1:
        parser.error('frames must be positive and sigma must be in 0..1')
    if args.steps is not None and args.steps < 1:
        parser.error('--steps must be positive')
    if args.steps is None and args.headless:
        args.steps = args.frames
    from isaacsim import SimulationApp
    # SimulationApp은 Python에서 Isaac Sim의 Kit 애플리케이션을 시작하고 갱신·종료하는 클래스이다.
    # headless=True는 창 없이 실행한다는 뜻이며, omni와 Isaac Sim 확장 모듈은 앱 생성 후 import한다.
    app=SimulationApp({'headless':args.headless,'renderer':'RaytracedLighting'})
    writers=[]
    try:
        import omni.usd
        # omni.usd는 현재 Kit 애플리케이션의 USD 문맥에 접근하는 모듈이다.
        # get_context().get_stage()로 객체·조명 등이 들어 있는 현재 Stage를 얻는다.
        import omni.replicator.core as rep
        # omni.replicator.core는 장면 무작위화와 합성 데이터 생성을 위한 API이다.
        # render product는 카메라의 렌더링 출력이며, annotator는 데이터를 추출하고 writer는 결과를 저장한다.
        from omni.syntheticdata import SyntheticData
        # SyntheticData는 렌더링 데이터 처리 노드와 템플릿을 다루며 센서·annotator 연결에 사용한다.
        from isaacsim.core.api import SimulationContext
        # SimulationContext는 물리 및 렌더링 시간 간격과 시뮬레이션의 재생·정지·step을 관리한다.
        from isaacsim.core.utils.extensions import enable_extension
        # enable_extension은 이름으로 지정한 Kit 확장을 활성화하여 해당 기능과 명령을 사용할 수 있게 한다.
        from pxr import Gf, UsdGeom, UsdLux
        # pxr은 USD 장면을 직접 다루는 OpenUSD의 Python 바인딩이다.
        # Gf는 벡터·행렬·쿼터니언 등 위치와 회전을 계산하는 수학 자료형을 다룬다.
        # UsdGeom은 형상, 변환, 카메라와 장면 단위·축 설정을 다룬다.
        # UsdLux는 조명 Prim과 빛의 속성을 다룬다.
        # Kit의 한 프레임을 갱신하여 렌더링·이벤트·비동기 작업을 처리한다.
        # 물리 진행 여부는 현재 타임라인의 재생 상태와 설정에 따라 달라진다.
        enable_extension('isaacsim.ros2.bridge'); app.update()
        stage=omni.usd.get_context().get_stage()
        # USD 좌표 한 단위가 몇 미터인지 지정하여 장면의 길이 단위를 맞춘다.
        # USD 장면에서 위쪽으로 사용할 축을 지정한다.
        UsdGeom.SetStageMetersPerUnit(stage,1.0); UsdGeom.SetStageUpAxis(stage,UsdGeom.Tokens.z)
        # 지정한 경로에 변환용 Xform Prim을 정의한다. 자식 객체를 묶어 함께 이동·회전시킬 때 사용할 수 있다.
        UsdGeom.Xform.Define(stage,'/World')
        # 주변을 둘러싸는 DomeLight를 생성하여 장면의 환경 조명을 설정한다.
        UsdLux.DomeLight.Define(stage,'/World/Light').CreateIntensityAttr(1500)
        for i,(x,y,color) in enumerate([(0,0,(.7,.15,.1)),(2,0,(.1,.7,.2)),(-2,0,(.1,.2,.8)),(0,3,(.6,.6,.1))]):
            # USD Stage에 Cube 형상을 직접 정의한다. 물리 동작이 필요하면 강체·충돌 API를 별도로 적용한다.
            cube=UsdGeom.Cube.Define(stage,f'/World/Cube_{i}')
            cube.CreateSizeAttr(1)
            UsdGeom.XformCommonAPI(cube).SetTranslate(Gf.Vec3d(x,y,.5))
            cube.CreateDisplayColorAttr([Gf.Vec3f(*color)])
        floor=UsdGeom.Cube.Define(stage,'/World/Floor'); floor.CreateSizeAttr(1)
        xf=UsdGeom.XformCommonAPI(floor); xf.SetTranslate(Gf.Vec3d(0,0,-.1)); xf.SetScale(Gf.Vec3f(12,12,.2))
        # USD 카메라 Prim을 정의한다. 센서 이미지 출력은 별도의 render product나 Camera API로 연결한다.
        camera=UsdGeom.Camera.Define(stage,'/World/Camera')
        transform=UsdGeom.XformCommonAPI(camera)
        transform.SetTranslate(Gf.Vec3d(0,4,1.5)); transform.SetRotate(Gf.Vec3f(75,0,180))
        camera.CreateFocalLengthAttr(18)
        # 카메라와 해상도를 연결한 render product를 만든다. 이후 annotator나 writer를 여기에 연결한다.
        product=rep.create.render_product('/World/Camera',(640,480))
        if args.device=='cuda':
            from noise_warp import gaussian_noise
            # 사용자 함수를 annotator의 출력 변환으로 등록할 수 있는 augmentation으로 감싼다.
            augmentation=rep.annotators.Augmentation.from_function(gaussian_noise,sigma=args.sigma,seed=args.seed,data_out_shape=(-1,-1,3))
        else:
            from noise import gaussian_noise
            augmentation=rep.annotators.Augmentation.from_function(gaussian_noise,sigma=args.sigma*255,seed=args.seed)
        # 이름으로 annotator를 가져와 렌더링 결과에서 필요한 데이터를 추출한다.
        rep.annotators.register(name='lesson_rgb_noise',annotator=rep.annotators.augment_compose(source_annotator=rep.annotators.get('rgb',device=args.device),augmentations=[augmentation]))
        rep.writers.register_node_writer(name='LessonROS2Noise',node_type_id='isaacsim.ros2.bridge.ROS2PublishImage',annotators=['lesson_rgb_noise',SyntheticData.NodeConnectionTemplate('IsaacReadSimulationTime',attributes_mapping={'outputs:simulationTime':'inputs:timeStamp'})],category='custom')
        for writer_name,topic in [('RgbROS2PublishImage','rgb_clean'),('LessonROS2Noise','rgb_augmented')]:
            # 등록된 writer를 선택하여 이미지와 주석 데이터의 저장 형식을 정한다.
            writer=rep.writers.get(writer_name)
            writer.initialize(topicName=topic,frameId='sim_camera')
            # writer를 render product에 연결하여 캡처한 데이터가 writer로 전달되게 한다.
            writer.attach([product]); writers.append(writer)
        sim=SimulationContext(physics_dt=1/60,rendering_dt=1/60,stage_units_in_meters=1)
        # 물리 엔진과 시뮬레이션 핸들을 초기화한다.
        # 타임라인을 재생 상태로 전환하여 물리 시뮬레이션이 진행되게 한다.
        sim.initialize_physics(); sim.play()
        print(f'Publishing /rgb_clean and /rgb_augmented; sigma={args.sigma}, device={args.device}')
        frame = 0
        while app.is_running() and (args.steps is None or frame < args.steps):
            transform.SetRotate(Gf.Vec3f(75,0,180+frame/4))
            # SimulationContext의 시간 간격으로 시뮬레이션을 한 step 진행한다.
            sim.step(render=True)
            frame += 1
        sim.stop()
    finally:
        try:
            for writer in writers:
                # writer와 render product의 연결을 해제한다.
                writer.detach()
        finally:
            # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
            app.close()


if __name__=='__main__':
    main()
