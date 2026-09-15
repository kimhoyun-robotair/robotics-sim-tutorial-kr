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
    app=SimulationApp({'headless':args.headless,'renderer':'RaytracedLighting'})
    writers=[]
    try:
        import omni.usd
        import omni.replicator.core as rep
        from omni.syntheticdata import SyntheticData
        from isaacsim.core.api import SimulationContext
        from isaacsim.core.utils.extensions import enable_extension
        from pxr import Gf, UsdGeom, UsdLux
        enable_extension('isaacsim.ros2.bridge'); app.update()
        stage=omni.usd.get_context().get_stage()
        UsdGeom.SetStageMetersPerUnit(stage,1.0); UsdGeom.SetStageUpAxis(stage,UsdGeom.Tokens.z)
        UsdGeom.Xform.Define(stage,'/World')
        UsdLux.DomeLight.Define(stage,'/World/Light').CreateIntensityAttr(1500)
        for i,(x,y,color) in enumerate([(0,0,(.7,.15,.1)),(2,0,(.1,.7,.2)),(-2,0,(.1,.2,.8)),(0,3,(.6,.6,.1))]):
            cube=UsdGeom.Cube.Define(stage,f'/World/Cube_{i}')
            cube.CreateSizeAttr(1)
            UsdGeom.XformCommonAPI(cube).SetTranslate(Gf.Vec3d(x,y,.5))
            cube.CreateDisplayColorAttr([Gf.Vec3f(*color)])
        floor=UsdGeom.Cube.Define(stage,'/World/Floor'); floor.CreateSizeAttr(1)
        xf=UsdGeom.XformCommonAPI(floor); xf.SetTranslate(Gf.Vec3d(0,0,-.1)); xf.SetScale(Gf.Vec3f(12,12,.2))
        camera=UsdGeom.Camera.Define(stage,'/World/Camera')
        transform=UsdGeom.XformCommonAPI(camera)
        transform.SetTranslate(Gf.Vec3d(0,4,1.5)); transform.SetRotate(Gf.Vec3f(75,0,180))
        camera.CreateFocalLengthAttr(18)
        product=rep.create.render_product('/World/Camera',(640,480))
        if args.device=='cuda':
            from noise_warp import gaussian_noise
            augmentation=rep.annotators.Augmentation.from_function(gaussian_noise,sigma=args.sigma,seed=args.seed,data_out_shape=(-1,-1,3))
        else:
            from noise import gaussian_noise
            augmentation=rep.annotators.Augmentation.from_function(gaussian_noise,sigma=args.sigma*255,seed=args.seed)
        rep.annotators.register(name='lesson_rgb_noise',annotator=rep.annotators.augment_compose(source_annotator=rep.annotators.get('rgb',device=args.device),augmentations=[augmentation]))
        rep.writers.register_node_writer(name='LessonROS2Noise',node_type_id='isaacsim.ros2.bridge.ROS2PublishImage',annotators=['lesson_rgb_noise',SyntheticData.NodeConnectionTemplate('IsaacReadSimulationTime',attributes_mapping={'outputs:simulationTime':'inputs:timeStamp'})],category='custom')
        for writer_name,topic in [('RgbROS2PublishImage','rgb_clean'),('LessonROS2Noise','rgb_augmented')]:
            writer=rep.writers.get(writer_name)
            writer.initialize(topicName=topic,frameId='sim_camera')
            writer.attach([product]); writers.append(writer)
        sim=SimulationContext(physics_dt=1/60,rendering_dt=1/60,stage_units_in_meters=1)
        sim.initialize_physics(); sim.play()
        print(f'Publishing /rgb_clean and /rgb_augmented; sigma={args.sigma}, device={args.device}')
        frame = 0
        while app.is_running() and (args.steps is None or frame < args.steps):
            transform.SetRotate(Gf.Vec3f(75,0,180+frame/4))
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
