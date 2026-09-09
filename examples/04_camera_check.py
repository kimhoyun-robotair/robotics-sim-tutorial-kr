"""Isaac Sim 6.0.1 RGB + ideal depth fixture; save raw frames and fail on bad data.

Run with Isaac Sim's python.sh. No external scene assets are required.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import traceback


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--headless', action='store_true')
    parser.add_argument('--output-dir', '--output', dest='output_dir', default='artifacts/camera')
    parser.add_argument('--warmup', type=int, default=120)
    parser.add_argument('--samples', type=int, default=10)
    args = parser.parse_args()
    if args.warmup < 60 or args.samples < 3:
        parser.error('Use --warmup >= 60 and --samples >= 3')
    out = Path(args.output_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    report = {'passed': False, 'isaac_sim_target': '6.0.1', 'frames': [], 'warmup_ticks': args.warmup,
              'measurement': 'RGB + ideal distance_to_image_plane; not a physical stereo-noise model'}
    app = None
    try:
        from isaacsim import SimulationApp
        app = SimulationApp({'headless': args.headless, 'multi_gpu': False, 'fast_shutdown': False, 'renderer': 'RealTimePathTracing'})
        import numpy as np
        import omni.kit.app
        import omni.usd
        import omni.timeline
        from pxr import Gf, UsdGeom, UsdLux, UsdPhysics
        from sensor_metrics import camera_metrics
        manager = omni.kit.app.get_app().get_extension_manager()
        manager.set_extension_enabled_immediate('isaacsim.sensors.experimental.rtx', True)
        from isaacsim.sensors.experimental.rtx import RtxCamera, CameraSensor
        from isaacsim.core.simulation_manager import SimulationManager
        omni.usd.get_context().new_stage()
        app.reset_render_settings()
        stage = omni.usd.get_context().get_stage()
        UsdGeom.SetStageMetersPerUnit(stage, 1.)
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
        stage.SetDefaultPrim(UsdGeom.Xform.Define(stage, '/World').GetPrim())
        UsdPhysics.Scene.Define(stage, '/World/PhysicsScene')
        def box(path, center, scale, color):
            prim = UsdGeom.Cube.Define(stage, path)
            prim.CreateSizeAttr(1.)
            prim.AddTranslateOp().Set(Gf.Vec3d(*center))
            prim.AddScaleOp().Set(Gf.Vec3f(*scale))
            prim.CreateDisplayColorAttr([Gf.Vec3f(*color)])
            return prim
        box('/World/Floor', (0, 0, -.05), (10, 10, .1), (.45, .45, .45))
        box('/World/Red', (-.45, 0, .2), (.5, .5, .4), (.8, .05, .05))
        box('/World/Blue', (.45, 0, .3), (.5, .5, .6), (.05, .1, .8))
        UsdLux.DomeLight.Define(stage, '/World/Light').CreateIntensityAttr(1000.)
        # USD camera axes: optical direction -Z, image up +Y. Identity looks down.
        camera = RtxCamera('/World/Camera', tick_rate=30., translations=[[0., 0., 3.]],
                           orientations=[[1., 0., 0., 0.]])
        usd_camera = UsdGeom.Camera(stage.GetPrimAtPath('/World/Camera'))
        usd_camera.CreateClippingRangeAttr(Gf.Vec2f(.05, 20.))
        usd_camera.CreateFocalLengthAttr(24.)
        usd_camera.CreateHorizontalApertureAttr(20.955)
        usd_camera.CreateVerticalApertureAttr(15.71625)
        sensor = CameraSensor(camera, resolution=(240, 320),
                              annotators=['rgb', 'distance_to_image_plane'])
        stage.Export(str(out / 'camera_scene.usda'))
        timeline = omni.timeline.get_timeline_interface()
        timeline.play()
        for _ in range(args.warmup):
            app.update()
        rgb_frames, depth_frames = [], []
        for sample in range(args.samples):
            for _ in range(12):
                app.update()
            rgb, rgb_info = sensor.get_data('rgb')
            depth, depth_info = sensor.get_data('distance_to_image_plane')
            rgb_np = np.asarray([]) if rgb is None else rgb.numpy().copy()
            depth_np = np.asarray([]) if depth is None else depth.numpy().copy()
            # Preserve failure evidence as well as passing frames.
            np.save(out / f'rgb_{sample:03d}.npy', rgb_np)
            np.save(out / f'depth_{sample:03d}.npy', depth_np)
            frame = camera_metrics(rgb_np, depth_np)
            frame.update(sample=sample, simulation_time_s=float(SimulationManager.get_simulation_time()),
                         rgb_info=str(rgb_info), depth_info=str(depth_info))
            report['frames'].append(frame)
            if frame['passed']:
                rgb_frames.append(rgb_np[..., :3])
                depth_frames.append(np.squeeze(depth_np))
        if len(rgb_frames) != args.samples:
            raise RuntimeError('One or more post-warmup frames failed; inspect frames in report.json')
        rgb_stack, depth_stack = np.stack(rgb_frames), np.stack(depth_frames)
        np.savez_compressed(out / 'camera_frames.npz', rgb=rgb_stack, depth=depth_stack)
        # A static-scene diagnostic; recorded separately from geometry/blackout gates.
        temporal_rgb_mae = float(np.mean(np.abs(np.diff(rgb_stack.astype(float), axis=0))))
        valid_pairs = np.isfinite(depth_stack[1:]) & np.isfinite(depth_stack[:-1])
        depth_changes = np.abs(depth_stack[1:][valid_pairs] - depth_stack[:-1][valid_pairs])
        temporal_depth_mae = float(depth_changes.mean()) if depth_changes.size else None
        report.update(captured_samples=len(rgb_frames), temporal_rgb_mae=temporal_rgb_mae,
                      temporal_depth_mae_m=temporal_depth_mae)
        if temporal_rgb_mae > 15 or temporal_depth_mae is None or temporal_depth_mae > .02:
            raise RuntimeError('Excessive temporal variation in the static RGB/ideal-depth fixture')
        report.update(passed=True,
                      note='Static fixture does not prove timestamp freshness or real-sensor noise accuracy.')
        from PIL import Image
        Image.fromarray(rgb_stack[-1]).save(out / 'rgb_preview.png')
        timeline.stop()
    except Exception as error:
        report.update(passed=False, error=str(error), traceback=traceback.format_exc())
    finally:
        (out / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
        print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)
        if app is not None:
            try:
                app.close(skip_cleanup=False, exit_code=0 if report['passed'] else 1)
            except Exception as error:
                report.update(passed=False, error=f'Application shutdown failed: {error}',
                              traceback=traceback.format_exc())
                (out / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
