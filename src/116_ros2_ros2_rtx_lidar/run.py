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
    app=SimulationApp({'headless':args.headless,'renderer':'RaytracedLighting'})
    try:
        import omni.usd
        import omni.graph.core as og
        import omni.kit.commands
        import omni.replicator.core as rep
        from isaacsim.core.api import SimulationContext
        from isaacsim.core.utils.extensions import enable_extension
        from pxr import Gf, UsdGeom, UsdLux
        enable_extension('isaacsim.ros2.bridge'); app.update()
        stage=omni.usd.get_context().get_stage()
        UsdGeom.SetStageMetersPerUnit(stage,1); UsdGeom.SetStageUpAxis(stage,UsdGeom.Tokens.z)
        UsdGeom.Xform.Define(stage,'/World')
        UsdLux.DomeLight.Define(stage,'/World/Light').CreateIntensityAttr(1200)
        for name,pos,size in [('Floor',(0,0,-.1),(12,12,.2)),('North',(0,5,1.5),(10,.2,3)),('South',(0,-5,1.5),(10,.2,3)),('East',(5,0,1.5),(.2,10,3)),('West',(-5,0,1.5),(.2,10,3)),('Target',(2,0,1),(1,1,2))]:
            cube=UsdGeom.Cube.Define(stage,'/World/'+name); cube.CreateSizeAttr(1)
            xf=UsdGeom.XformCommonAPI(cube); xf.SetTranslate(Gf.Vec3d(*pos)); xf.SetScale(Gf.Vec3f(*size))
        products=[]
        for name,profile in [('Lidar3D',args.profile),('Lidar2D','Example_Rotary_2D')]:
            ok,sensor=omni.kit.commands.execute('IsaacSensorCreateRtxLidar',path='/World/'+name,parent=None,config=profile,translation=(0,0,1),orientation=Gf.Quatd(1,0,0,0))
            if not ok or sensor is None: raise RuntimeError('RTX sensor creation failed: '+profile)
            products.append(rep.create.render_product(sensor.GetPath(),[1,1],name=name))
        keys=og.Controller.Keys
        og.Controller.edit({'graph_path':'/World/LidarGraph','evaluator_name':'execution'},{
            keys.CREATE_NODES:[('Tick','omni.graph.action.OnPlaybackTick'),('Context','isaacsim.ros2.bridge.ROS2Context'),('Cloud','isaacsim.ros2.bridge.ROS2RtxLidarHelper'),('Scan','isaacsim.ros2.bridge.ROS2RtxLidarHelper'),('Time','isaacsim.core.nodes.IsaacReadSimulationTime'),('Clock','isaacsim.ros2.bridge.ROS2PublishClock')],
            keys.SET_VALUES:[('Context.inputs:useDomainIDEnvVar',True),('Cloud.inputs:renderProductPath',products[0].path),('Cloud.inputs:type','point_cloud'),('Cloud.inputs:topicName','point_cloud'),('Cloud.inputs:frameId','base_scan'),('Cloud.inputs:fullScan',args.full_scan),('Scan.inputs:renderProductPath',products[1].path),('Scan.inputs:type','laser_scan'),('Scan.inputs:topicName','scan'),('Scan.inputs:frameId','base_scan')],
            keys.CONNECT:[('Tick.outputs:tick',node+'.inputs:execIn') for node in ['Cloud','Scan','Clock']]+[('Context.outputs:context',node+'.inputs:context') for node in ['Cloud','Scan','Clock']]+[('Time.outputs:simulationTime','Clock.inputs:timeStamp')]
        })
        sim=SimulationContext(physics_dt=1/60,rendering_dt=1/60,stage_units_in_meters=1)
        sim.initialize_physics(); sim.play()
        print('RViz Fixed Frame: base_scan; PointCloud2: /point_cloud; LaserScan: /scan')
        print('Sensor origin is (0,0,1) in USD; both messages use its local base_scan frame.')
        frame = 0
        while app.is_running() and (args.steps is None or frame < args.steps):
            sim.step(render=True)
            frame += 1
        sim.stop()
    finally:
        app.close()


if __name__=='__main__':
    main()
