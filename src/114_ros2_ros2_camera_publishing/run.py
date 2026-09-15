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
    app=SimulationApp({'headless':args.headless,'renderer':'RaytracedLighting'})
    writers=[]
    try:
        import numpy as np
        import omni.usd
        import omni.graph.core as og
        import omni.replicator.core as rep
        from omni.syntheticdata import SyntheticData
        from isaacsim.core.api import SimulationContext
        from isaacsim.core.utils.extensions import enable_extension
        from isaacsim.core.utils.numpy.rotations import euler_angles_to_quats
        from isaacsim.sensors.camera import Camera
        from pxr import Gf, Sdf, UsdGeom, UsdLux
        enable_extension('isaacsim.ros2.bridge'); app.update()
        from isaacsim.ros2.bridge import read_camera_info
        stage=omni.usd.get_context().get_stage()
        UsdGeom.SetStageMetersPerUnit(stage,1); UsdGeom.SetStageUpAxis(stage,UsdGeom.Tokens.z)
        UsdGeom.Xform.Define(stage,'/World')
        UsdLux.DomeLight.Define(stage,'/World/Light').CreateIntensityAttr(1500)
        for name,pos,scale,color in [('Floor',(0,0,-.1),(12,12,.2),(.3,.3,.3)),('Cube',(0,0,.5),(1,1,1),(.8,.2,.1)),('Wall',(-3,0,1.5),(.2,8,3),(.2,.4,.7))]:
            cube=UsdGeom.Cube.Define(stage,'/World/'+name); cube.CreateSizeAttr(1)
            xf=UsdGeom.XformCommonAPI(cube); xf.SetTranslate(Gf.Vec3d(*pos)); xf.SetScale(Gf.Vec3f(*scale))
            cube.CreateDisplayColorAttr([Gf.Vec3f(*color)])
        camera=Camera(prim_path='/World/camera',name='camera',position=np.array([4.,0.,2.]),orientation=euler_angles_to_quats(np.array([0.,15.,180.]),degrees=True),resolution=(640,480),frequency=60)
        app.update(); camera.initialize(); app.update()
        product=camera.get_render_product_path()
        # The renderer runs at 60 Hz; a gate forwards every N-th render frame.
        step=max(1,int(60/args.frequency))
        for writer_name,topic,gate in [('RgbROS2PublishImage','camera_rgb','Rgb'),('DistanceToImagePlaneROS2PublishImage','camera_depth','DistanceToImagePlane'),('DistanceToImagePlaneROS2PublishPointCloud','camera_pointcloud','DistanceToImagePlane')]:
            writer=rep.writers.get(writer_name)
            writer.initialize(frameId='camera',nodeNamespace='',queueSize=1,topicName=topic)
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
        og.Controller.edit({'graph_path':'/World/CameraTF','evaluator_name':'execution'},{
            keys.CREATE_NODES:[('Tick','omni.graph.action.OnPlaybackTick'),('Time','isaacsim.core.nodes.IsaacReadSimulationTime'),('Clock','isaacsim.ros2.bridge.ROS2PublishClock'),('Pose','isaacsim.ros2.bridge.ROS2PublishTransformTree'),('Axes','isaacsim.ros2.bridge.ROS2PublishRawTransformTree')],
            keys.SET_VALUES:[('Pose.inputs:targetPrims',[Sdf.Path(camera.prim_path)]),('Pose.inputs:topicName','/tf'),('Axes.inputs:topicName','/tf'),('Axes.inputs:parentFrameId','camera'),('Axes.inputs:childFrameId','camera_world'),('Axes.inputs:rotation',[.5,-.5,.5,.5])],
            keys.CONNECT:[('Tick.outputs:tick',node+'.inputs:execIn') for node in ['Clock','Pose','Axes']]+[('Time.outputs:simulationTime',node+'.inputs:timeStamp') for node in ['Clock','Pose','Axes']]
        })
        sim=SimulationContext(physics_dt=1/60,rendering_dt=1/60,stage_units_in_meters=1)
        sim.initialize_physics(); sim.play()
        print(f'Gate step={step}; theoretical render-relative rate={60/step:g} Hz. Measure ROS receive rate separately.')
        print(f'CameraInfo: {info.width}x{info.height}, fx={info.k[0,0]:.3f}, fy={info.k[1,1]:.3f}')
        frame = 0
        while app.is_running() and (args.steps is None or frame < args.steps):
            sim.step(render=True)
            frame += 1
        sim.stop()
    finally:
        try:
            for writer in writers:
                writer.detach()
        finally:
            app.close()


if __name__=='__main__':
    main()
