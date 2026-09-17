"""Publish RGB, depth, depth-derived PointCloud2, CameraInfo, TF and simulation clock."""
import argparse


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--steps', type=int, default=None, help='Simulation steps before exit; omitted: GUI until closed, headless uses --frames')
    parser.add_argument('--frames', type=int, default=1800, help='Legacy headless step limit when --steps is omitted; does not close the GUI')
    parser.add_argument('--headless',action='store_true')
    parser.add_argument('--frequency',type=float,default=30,help='Requested frequency in simulation seconds (0..60 Hz)')
    args=parser.parse_args()
    if args.frames<1 or not 0<args.frequency<=60:
        parser.error('frames must be positive and frequency must be in (0,60]')
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
        import numpy as np
        import omni.usd
        # omni.usd는 현재 Kit 애플리케이션의 USD 문맥에 접근하는 모듈이다.
        # get_context().get_stage()로 객체·조명 등이 들어 있는 현재 Stage를 얻는다.
        import omni.graph.core as og
        # omni.graph.core는 노드와 연결로 실행 흐름을 구성하는 OmniGraph API이다.
        # Controller.edit에서 노드 생성, 입력값 설정, 출력과 입력의 연결을 정의한다.
        import omni.replicator.core as rep
        # omni.replicator.core는 장면 무작위화와 합성 데이터 생성을 위한 API이다.
        # render product는 카메라의 렌더링 출력이며, annotator는 데이터를 추출하고 writer는 결과를 저장한다.
        from omni.syntheticdata import SyntheticData
        # SyntheticData는 렌더링 데이터 처리 노드와 템플릿을 다루며 센서·annotator 연결에 사용한다.
        from isaacsim.core.api import SimulationContext
        # SimulationContext는 물리 및 렌더링 시간 간격과 시뮬레이션의 재생·정지·step을 관리한다.
        from isaacsim.core.utils.extensions import enable_extension
        # enable_extension은 이름으로 지정한 Kit 확장을 활성화하여 해당 기능과 명령을 사용할 수 있게 한다.
        from isaacsim.core.utils.numpy.rotations import euler_angles_to_quats
        # euler_angles_to_quats는 여러 Euler 회전을 NumPy 배열로 받아 쿼터니언 배열로 변환한다.
        from isaacsim.sensors.camera import Camera
        # Camera는 USD 카메라와 렌더링 출력을 연결하여 RGB·깊이 등의 센서 데이터를 얻는 클래스이다.
        from pxr import Gf, Sdf, UsdGeom, UsdLux
        # pxr은 USD 장면을 직접 다루는 OpenUSD의 Python 바인딩이다.
        # Gf는 벡터·행렬·쿼터니언 등 위치와 회전을 계산하는 수학 자료형을 다룬다.
        # Sdf는 USD 경로, 레이어, 속성 값의 자료형을 다룬다.
        # UsdGeom은 형상, 변환, 카메라와 장면 단위·축 설정을 다룬다.
        # UsdLux는 조명 Prim과 빛의 속성을 다룬다.
        # Kit의 한 프레임을 갱신하여 렌더링·이벤트·비동기 작업을 처리한다.
        # 물리 진행 여부는 현재 타임라인의 재생 상태와 설정에 따라 달라진다.
        enable_extension('isaacsim.ros2.bridge'); app.update()
        from isaacsim.ros2.bridge import read_camera_info
        # read_camera_info는 카메라의 보정 정보를 읽어 ROS 2 CameraInfo 발행에 필요한 값을 얻는다.
        stage=omni.usd.get_context().get_stage()
        # USD 좌표 한 단위가 몇 미터인지 지정하여 장면의 길이 단위를 맞춘다.
        # USD 장면에서 위쪽으로 사용할 축을 지정한다.
        UsdGeom.SetStageMetersPerUnit(stage,1); UsdGeom.SetStageUpAxis(stage,UsdGeom.Tokens.z)
        # 지정한 경로에 변환용 Xform Prim을 정의한다. 자식 객체를 묶어 함께 이동·회전시킬 때 사용할 수 있다.
        UsdGeom.Xform.Define(stage,'/World')
        # 주변을 둘러싸는 DomeLight를 생성하여 장면의 환경 조명을 설정한다.
        UsdLux.DomeLight.Define(stage,'/World/Light').CreateIntensityAttr(1500)
        for name,pos,scale,color in [('Floor',(0,0,-.1),(12,12,.2),(.3,.3,.3)),('Cube',(0,0,.5),(1,1,1),(.8,.2,.1)),('Wall',(-3,0,1.5),(.2,8,3),(.2,.4,.7))]:
            # USD Stage에 Cube 형상을 직접 정의한다. 물리 동작이 필요하면 강체·충돌 API를 별도로 적용한다.
            cube=UsdGeom.Cube.Define(stage,'/World/'+name); cube.CreateSizeAttr(1)
            xf=UsdGeom.XformCommonAPI(cube); xf.SetTranslate(Gf.Vec3d(*pos)); xf.SetScale(Gf.Vec3f(*scale))
            cube.CreateDisplayColorAttr([Gf.Vec3f(*color)])
        camera=Camera(prim_path='/World/camera',name='camera',position=np.array([4.,0.,2.]),orientation=euler_angles_to_quats(np.array([0.,15.,180.]),degrees=True),resolution=(640,480),frequency=60)
        # 카메라의 렌더링·데이터 수집 연결을 초기화한다.
        app.update(); camera.initialize(); app.update()
        product=camera.get_render_product_path()
        # The renderer runs at 60 Hz; a gate forwards every N-th render frame.
        step=max(1,int(60/args.frequency))
        for writer_name,topic,gate in [('RgbROS2PublishImage','camera_rgb','Rgb'),('DistanceToImagePlaneROS2PublishImage','camera_depth','DistanceToImagePlane'),('DistanceToImagePlaneROS2PublishPointCloud','camera_pointcloud','DistanceToImagePlane')]:
            # 등록된 writer를 선택하여 이미지와 주석 데이터의 저장 형식을 정한다.
            writer=rep.writers.get(writer_name)
            writer.initialize(frameId='camera',nodeNamespace='',queueSize=1,topicName=topic)
            # writer를 render product에 연결하여 캡처한 데이터가 writer로 전달되게 한다.
            writer.attach([product]); writers.append(writer)
            path=SyntheticData._get_node_path(gate+'IsaacSimulationGate',product)
            og.Controller.attribute(path+'.inputs:step').set(step)
        info,_=read_camera_info(render_product_path=product)
        writer=rep.writers.get('ROS2PublishCameraInfo')
        writer.initialize(frameId='camera',topicName='camera_camera_info',queueSize=1,width=info.width,height=info.height,projectionType=info.distortion_model,k=info.k.reshape([1,9]),r=info.r.reshape([1,9]),p=info.p.reshape([1,12]),physicalDistortionModel=info.distortion_model,physicalDistortionCoefficients=info.d)
        writer.attach([product]); writers.append(writer)
        path=SyntheticData._get_node_path('PostProcessDispatchIsaacSimulationGate',product)
        og.Controller.attribute(path+'.inputs:step').set(step)
        keys=og.Controller.Keys
        # OmniGraph의 노드와 입력값을 만들고 포트를 연결한다.
        # 실행 포트는 처리 순서를, 데이터 포트는 시간·센서·관절 값의 전달 경로를 정한다.
        og.Controller.edit({'graph_path':'/World/CameraTF','evaluator_name':'execution'},{
            keys.CREATE_NODES:[('Tick','omni.graph.action.OnPlaybackTick'),('Time','isaacsim.core.nodes.IsaacReadSimulationTime'),('Clock','isaacsim.ros2.bridge.ROS2PublishClock'),('Pose','isaacsim.ros2.bridge.ROS2PublishTransformTree'),('Axes','isaacsim.ros2.bridge.ROS2PublishRawTransformTree')],
            keys.SET_VALUES:[('Pose.inputs:targetPrims',[Sdf.Path(camera.prim_path)]),('Pose.inputs:topicName','/tf'),('Axes.inputs:topicName','/tf'),('Axes.inputs:parentFrameId','camera'),('Axes.inputs:childFrameId','camera_world'),('Axes.inputs:rotation',[.5,-.5,.5,.5])],
            keys.CONNECT:[('Tick.outputs:tick',node+'.inputs:execIn') for node in ['Clock','Pose','Axes']]+[('Time.outputs:simulationTime',node+'.inputs:timeStamp') for node in ['Clock','Pose','Axes']]
        })
        sim=SimulationContext(physics_dt=1/60,rendering_dt=1/60,stage_units_in_meters=1)
        # 물리 엔진과 시뮬레이션 핸들을 초기화한다.
        # 타임라인을 재생 상태로 전환하여 물리 시뮬레이션이 진행되게 한다.
        sim.initialize_physics(); sim.play()
        print(f'Gate step={step}; theoretical render-relative rate={60/step:g} Hz. Measure ROS receive rate separately.')
        print(f'CameraInfo: {info.width}x{info.height}, fx={info.k[0,0]:.3f}, fy={info.k[1,1]:.3f}')
        frame = 0
        while app.is_running() and (args.steps is None or frame < args.steps):
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
