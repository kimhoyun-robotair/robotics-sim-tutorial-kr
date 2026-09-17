"""Two independent RTX sensors publish 3-D PointCloud2 and 2-D LaserScan."""
import argparse


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--steps', type=int, default=None, help='Simulation steps before exit; omitted: GUI until closed, headless uses --frames')
    parser.add_argument('--frames', type=int, default=1800, help='Legacy headless step limit when --steps is omitted; does not close the GUI')
    parser.add_argument('--headless',action='store_true')
    parser.add_argument('--profile',choices=['Example_Rotary','Example_Solid_State'],default='Example_Rotary',help='3-D lidar profile; 2-D remains Example_Rotary_2D')
    parser.add_argument('--full-scan',action='store_true',help='Accumulate a full 3-D scan before publishing')
    args=parser.parse_args()
    if args.frames<1: parser.error('--frames must be positive')
    if args.steps is not None and args.steps < 1:
        parser.error('--steps must be positive')
    if args.steps is None and args.headless:
        args.steps = args.frames
    from isaacsim import SimulationApp
    # SimulationApp은 Python에서 Isaac Sim의 Kit 애플리케이션을 시작하고 갱신·종료하는 클래스이다.
    # headless=True는 창 없이 실행한다는 뜻이며, omni와 Isaac Sim 확장 모듈은 앱 생성 후 import한다.
    app=SimulationApp({'headless':args.headless,'renderer':'RaytracedLighting'})
    try:
        import omni.usd
        # omni.usd는 현재 Kit 애플리케이션의 USD 문맥에 접근하는 모듈이다.
        # get_context().get_stage()로 객체·조명 등이 들어 있는 현재 Stage를 얻는다.
        import omni.graph.core as og
        # omni.graph.core는 노드와 연결로 실행 흐름을 구성하는 OmniGraph API이다.
        # Controller.edit에서 노드 생성, 입력값 설정, 출력과 입력의 연결을 정의한다.
        import omni.kit.commands
        # omni.kit.commands는 이름으로 등록된 Kit 명령을 실행하는 모듈이다.
        # execute에 명령 이름과 인자를 전달해 Prim 생성·가져오기 등의 작업을 수행한다.
        import omni.replicator.core as rep
        # omni.replicator.core는 장면 무작위화와 합성 데이터 생성을 위한 API이다.
        # render product는 카메라의 렌더링 출력이며, annotator는 데이터를 추출하고 writer는 결과를 저장한다.
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
        UsdGeom.SetStageMetersPerUnit(stage,1); UsdGeom.SetStageUpAxis(stage,UsdGeom.Tokens.z)
        # 지정한 경로에 변환용 Xform Prim을 정의한다. 자식 객체를 묶어 함께 이동·회전시킬 때 사용할 수 있다.
        UsdGeom.Xform.Define(stage,'/World')
        # 주변을 둘러싸는 DomeLight를 생성하여 장면의 환경 조명을 설정한다.
        UsdLux.DomeLight.Define(stage,'/World/Light').CreateIntensityAttr(1200)
        for name,pos,size in [('Floor',(0,0,-.1),(12,12,.2)),('North',(0,5,1.5),(10,.2,3)),('South',(0,-5,1.5),(10,.2,3)),('East',(5,0,1.5),(.2,10,3)),('West',(-5,0,1.5),(.2,10,3)),('Target',(2,0,1),(1,1,2))]:
            # USD Stage에 Cube 형상을 직접 정의한다. 물리 동작이 필요하면 강체·충돌 API를 별도로 적용한다.
            cube=UsdGeom.Cube.Define(stage,'/World/'+name); cube.CreateSizeAttr(1)
            xf=UsdGeom.XformCommonAPI(cube); xf.SetTranslate(Gf.Vec3d(*pos)); xf.SetScale(Gf.Vec3f(*size))
        products=[]
        for name,profile in [('Lidar3D',args.profile),('Lidar2D','Example_Rotary_2D')]:
            # 센서 프로파일을 사용하는 RTX LiDAR Prim을 생성한다. 이후 render product와 출력 처리를 연결한다.
            ok,sensor=omni.kit.commands.execute('IsaacSensorCreateRtxLidar',path='/World/'+name,parent=None,config=profile,translation=(0,0,1),orientation=Gf.Quatd(1,0,0,0))
            if not ok or sensor is None: raise RuntimeError('RTX sensor creation failed: '+profile)
            # 카메라와 해상도를 연결한 render product를 만든다. 이후 annotator나 writer를 여기에 연결한다.
            products.append(rep.create.render_product(sensor.GetPath(),[1,1],name=name))
        keys=og.Controller.Keys
        # OmniGraph의 노드와 입력값을 만들고 포트를 연결한다.
        # 실행 포트는 처리 순서를, 데이터 포트는 시간·센서·관절 값의 전달 경로를 정한다.
        og.Controller.edit({'graph_path':'/World/LidarGraph','evaluator_name':'execution'},{
            keys.CREATE_NODES:[('Tick','omni.graph.action.OnPlaybackTick'),('Context','isaacsim.ros2.bridge.ROS2Context'),('Cloud','isaacsim.ros2.bridge.ROS2RtxLidarHelper'),('Scan','isaacsim.ros2.bridge.ROS2RtxLidarHelper'),('Time','isaacsim.core.nodes.IsaacReadSimulationTime'),('Clock','isaacsim.ros2.bridge.ROS2PublishClock')],
            keys.SET_VALUES:[('Context.inputs:useDomainIDEnvVar',True),('Cloud.inputs:renderProductPath',products[0].path),('Cloud.inputs:type','point_cloud'),('Cloud.inputs:topicName','point_cloud'),('Cloud.inputs:frameId','base_scan'),('Cloud.inputs:fullScan',args.full_scan),('Scan.inputs:renderProductPath',products[1].path),('Scan.inputs:type','laser_scan'),('Scan.inputs:topicName','scan'),('Scan.inputs:frameId','base_scan')],
            keys.CONNECT:[('Tick.outputs:tick',node+'.inputs:execIn') for node in ['Cloud','Scan','Clock']]+[('Context.outputs:context',node+'.inputs:context') for node in ['Cloud','Scan','Clock']]+[('Time.outputs:simulationTime','Clock.inputs:timeStamp')]
        })
        sim=SimulationContext(physics_dt=1/60,rendering_dt=1/60,stage_units_in_meters=1)
        # 물리 엔진과 시뮬레이션 핸들을 초기화한다.
        # 타임라인을 재생 상태로 전환하여 물리 시뮬레이션이 진행되게 한다.
        sim.initialize_physics(); sim.play()
        print('RViz Fixed Frame: base_scan; PointCloud2: /point_cloud; LaserScan: /scan')
        print('Sensor origin is (0,0,1) in USD; both messages use its local base_scan frame.')
        frame = 0
        while app.is_running() and (args.steps is None or frame < args.steps):
            # SimulationContext의 시간 간격으로 시뮬레이션을 한 step 진행한다.
            sim.step(render=True)
            frame += 1
        sim.stop()
    finally:
        # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
        app.close()


if __name__=='__main__':
    main()
