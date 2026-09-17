"""Create two camera render products and ROS 2 image/depth/perception helper graphs."""
import argparse


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--steps', type=int, default=None, help='Simulation steps before exit; omitted: GUI until closed, headless uses --frames')
    parser.add_argument('--frames', type=int, default=1800, help='Legacy headless step limit when --steps is omitted; does not close the GUI')
    parser.add_argument('--headless', action='store_true')
    parser.add_argument('--perception', choices=['none', 'semantic_segmentation', 'instance_segmentation', 'bbox_2d_tight', 'bbox_2d_loose', 'bbox_3d'], default='none')
    args = parser.parse_args()
    if args.frames < 1:
        parser.error('--frames must be positive')
    if args.steps is not None and args.steps < 1:
        parser.error('--steps must be positive')
    if args.steps is None and args.headless:
        args.steps = args.frames
    from isaacsim import SimulationApp
    # SimulationApp은 Python에서 Isaac Sim의 Kit 애플리케이션을 시작하고 갱신·종료하는 클래스이다.
    # headless=True는 창 없이 실행한다는 뜻이며, omni와 Isaac Sim 확장 모듈은 앱 생성 후 import한다.
    app = SimulationApp({'headless': args.headless, 'renderer': 'RaytracedLighting'})
    try:
        import omni.graph.core as og
        # omni.graph.core는 노드와 연결로 실행 흐름을 구성하는 OmniGraph API이다.
        # Controller.edit에서 노드 생성, 입력값 설정, 출력과 입력의 연결을 정의한다.
        import omni.usd
        # omni.usd는 현재 Kit 애플리케이션의 USD 문맥에 접근하는 모듈이다.
        # get_context().get_stage()로 객체·조명 등이 들어 있는 현재 Stage를 얻는다.
        from isaacsim.core.api import SimulationContext
        # SimulationContext는 물리 및 렌더링 시간 간격과 시뮬레이션의 재생·정지·step을 관리한다.
        from isaacsim.core.utils.extensions import enable_extension
        # enable_extension은 이름으로 지정한 Kit 확장을 활성화하여 해당 기능과 명령을 사용할 수 있게 한다.
        from pxr import Gf, Sdf, UsdGeom, UsdLux
        # pxr은 USD 장면을 직접 다루는 OpenUSD의 Python 바인딩이다.
        # Gf는 벡터·행렬·쿼터니언 등 위치와 회전을 계산하는 수학 자료형을 다룬다.
        # Sdf는 USD 경로, 레이어, 속성 값의 자료형을 다룬다.
        # UsdGeom은 형상, 변환, 카메라와 장면 단위·축 설정을 다룬다.
        # UsdLux는 조명 Prim과 빛의 속성을 다룬다.
        enable_extension('isaacsim.ros2.bridge')
        # Kit의 한 프레임을 갱신하여 렌더링·이벤트·비동기 작업을 처리한다.
        # 물리 진행 여부는 현재 타임라인의 재생 상태와 설정에 따라 달라진다.
        app.update()
        stage = omni.usd.get_context().get_stage()
        # USD 좌표 한 단위가 몇 미터인지 지정하여 장면의 길이 단위를 맞춘다.
        UsdGeom.SetStageMetersPerUnit(stage, 1.0)
        # USD 장면에서 위쪽으로 사용할 축을 지정한다.
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
        # 지정한 경로에 변환용 Xform Prim을 정의한다. 자식 객체를 묶어 함께 이동·회전시킬 때 사용할 수 있다.
        UsdGeom.Xform.Define(stage, '/World')
        # 주변을 둘러싸는 DomeLight를 생성하여 장면의 환경 조명을 설정한다.
        light = UsdLux.DomeLight.Define(stage, '/World/Light')
        light.CreateIntensityAttr(1500)
        for name, pos, scale, color in [
            ('Floor',(0,0,-.1),(8,8,.2),(.3,.3,.3)),
            ('Red',(0,0,.5),(1,1,1),(.8,.1,.1)),
            ('Blue',(1.8,0,.5),(.5,.5,1),(.1,.2,.9)),
            ('Wall',(0,-3,1.5),(8,.2,3),(.5,.6,.5))]:
            # USD Stage에 Cube 형상을 직접 정의한다. 물리 동작이 필요하면 강체·충돌 API를 별도로 적용한다.
            cube = UsdGeom.Cube.Define(stage, '/World/'+name)
            cube.CreateSizeAttr(1)
            xf = UsdGeom.XformCommonAPI(cube)
            xf.SetTranslate(Gf.Vec3d(*pos)); xf.SetScale(Gf.Vec3f(*scale))
            cube.CreateDisplayColorAttr([Gf.Vec3f(*color)])
            if args.perception != 'none' and name in ('Red','Blue'):
                from isaacsim.core.utils.semantics import add_update_semantics
                # add_update_semantics는 Prim의 의미 정보를 추가하거나 갱신하여 분할·검출 주석에 사용할 수 있게 한다.
                add_update_semantics(cube.GetPrim(), semantic_label=name.lower())
        keys = og.Controller.Keys
        for number, x in [(1,0.0),(2,1.0)]:
            camera_path = f'/World/Camera_{number}'
            # USD 카메라 Prim을 정의한다. 센서 이미지 출력은 별도의 render product나 Camera API로 연결한다.
            camera = UsdGeom.Camera.Define(stage, camera_path)
            xf = UsdGeom.XformCommonAPI(camera)
            xf.SetTranslate(Gf.Vec3d(x,4,1.5)); xf.SetRotate(Gf.Vec3f(75,0,180))
            camera.CreateHorizontalApertureAttr(20.955)
            camera.CreateVerticalApertureAttr(15.71625)
            camera.CreateFocalLengthAttr(18)
            camera.CreateClippingRangeAttr(Gf.Vec2f(.1,100))
            nodes = [('Tick','omni.graph.action.OnPlaybackTick'),('Context','isaacsim.ros2.bridge.ROS2Context'),('Once','isaacsim.core.nodes.OgnIsaacRunOneSimulationFrame'),('Render','isaacsim.core.nodes.IsaacCreateRenderProduct'),('Info','isaacsim.ros2.bridge.ROS2CameraInfoHelper')]
            values = [('Render.inputs:cameraPrim',[Sdf.Path(camera_path)]),('Render.inputs:width',640),('Render.inputs:height',480),('Context.inputs:useDomainIDEnvVar',True),('Info.inputs:topicName',f'camera_{number}/camera_info'),('Info.inputs:frameId',f'camera_{number}')]
            connections=[('Tick.outputs:tick','Once.inputs:execIn'),('Once.outputs:step','Render.inputs:execIn'),('Render.outputs:execOut','Info.inputs:execIn'),('Render.outputs:renderProductPath','Info.inputs:renderProductPath'),('Context.outputs:context','Info.inputs:context')]
            for dtype in ['rgb','depth','depth_pcl'] + ([] if args.perception=='none' else [args.perception]):
                name = 'Publish_'+dtype
                nodes.append((name,'isaacsim.ros2.bridge.ROS2CameraHelper'))
                values.extend([(name+'.inputs:type',dtype),(name+'.inputs:topicName',f'camera_{number}/{dtype}'),(name+'.inputs:frameId',f'camera_{number}')])
                if dtype == args.perception:
                    values.extend([(name+'.inputs:enableSemanticLabels',True),(name+'.inputs:semanticLabelsTopicName',f'camera_{number}/labels')])
                connections.extend([('Render.outputs:execOut',name+'.inputs:execIn'),('Render.outputs:renderProductPath',name+'.inputs:renderProductPath'),('Context.outputs:context',name+'.inputs:context')])
            # OmniGraph의 노드와 입력값을 만들고 포트를 연결한다.
            # 실행 포트는 처리 순서를, 데이터 포트는 시간·센서·관절 값의 전달 경로를 정한다.
            og.Controller.edit({'graph_path':f'/World/CameraGraph_{number}','evaluator_name':'execution'},{keys.CREATE_NODES:nodes,keys.SET_VALUES:values,keys.CONNECT:connections})
        sim=SimulationContext(physics_dt=1/60,rendering_dt=1/60,stage_units_in_meters=1)
        # 물리 엔진과 시뮬레이션 핸들을 초기화한다.
        # 타임라인을 재생 상태로 전환하여 물리 시뮬레이션이 진행되게 한다.
        sim.initialize_physics(); sim.play()
        print('Inspect /camera_1/{rgb,depth,depth_pcl,camera_info} and /camera_2 equivalents from ROS 2.')
        frame = 0
        while app.is_running() and (args.steps is None or frame < args.steps):
            # SimulationContext의 시간 간격으로 시뮬레이션을 한 step 진행한다.
            sim.step(render=True)
            frame += 1
        sim.stop()
    finally:
        # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
        app.close()


if __name__ == '__main__':
    main()
