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
    app = SimulationApp({'headless': args.headless, 'renderer': 'RaytracedLighting'})
    try:
        import omni.graph.core as og
        import omni.usd
        from isaacsim.core.api import SimulationContext
        from isaacsim.core.utils.extensions import enable_extension
        from pxr import Gf, Sdf, UsdGeom, UsdLux
        enable_extension('isaacsim.ros2.bridge')
        app.update()
        stage = omni.usd.get_context().get_stage()
        UsdGeom.SetStageMetersPerUnit(stage, 1.0)
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
        UsdGeom.Xform.Define(stage, '/World')
        light = UsdLux.DomeLight.Define(stage, '/World/Light')
        light.CreateIntensityAttr(1500)
        for name, pos, scale, color in [
            ('Floor',(0,0,-.1),(8,8,.2),(.3,.3,.3)),
            ('Red',(0,0,.5),(1,1,1),(.8,.1,.1)),
            ('Blue',(1.8,0,.5),(.5,.5,1),(.1,.2,.9)),
            ('Wall',(0,-3,1.5),(8,.2,3),(.5,.6,.5))]:
            cube = UsdGeom.Cube.Define(stage, '/World/'+name)
            cube.CreateSizeAttr(1)
            xf = UsdGeom.XformCommonAPI(cube)
            xf.SetTranslate(Gf.Vec3d(*pos)); xf.SetScale(Gf.Vec3f(*scale))
            cube.CreateDisplayColorAttr([Gf.Vec3f(*color)])
            if args.perception != 'none' and name in ('Red','Blue'):
                from isaacsim.core.utils.semantics import add_update_semantics
                add_update_semantics(cube.GetPrim(), semantic_label=name.lower())
        keys = og.Controller.Keys
        for number, x in [(1,0.0),(2,1.0)]:
            camera_path = f'/World/Camera_{number}'
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
            og.Controller.edit({'graph_path':f'/World/CameraGraph_{number}','evaluator_name':'execution'},{keys.CREATE_NODES:nodes,keys.SET_VALUES:values,keys.CONNECT:connections})
        sim=SimulationContext(physics_dt=1/60,rendering_dt=1/60,stage_units_in_meters=1)
        sim.initialize_physics(); sim.play()
        print('Inspect /camera_1/{rgb,depth,depth_pcl,camera_info} and /camera_2 equivalents from ROS 2.')
        frame = 0
        while app.is_running() and (args.steps is None or frame < args.steps):
            sim.step(render=True)
            frame += 1
        sim.stop()
    finally:
        app.close()


if __name__ == '__main__':
    main()
