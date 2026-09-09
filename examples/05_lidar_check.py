"""Isaac Sim 6.0.1 RTX Lidar test room, full-scan and data-quality checks.

Uses documented GMO Python bindings rather than interpreting unknown buffer fields.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import traceback


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--headless', action='store_true')
    parser.add_argument('--output-dir', '--output', dest='output_dir', default='artifacts/lidar')
    parser.add_argument('--warmup', type=int, default=120)
    parser.add_argument('--samples', type=int, default=10)
    args = parser.parse_args()
    if args.warmup < 60 or args.samples < 3:
        parser.error('Use --warmup >= 60 and --samples >= 3')
    out = Path(args.output_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    report = {'passed': False, 'isaac_sim_target': '6.0.1', 'scans': [],
              'config': 'Example_Rotary', 'tick_rate_hz': 10, 'scan_rate_hz': 10}
    app = None
    try:
        from isaacsim import SimulationApp
        app = SimulationApp({'headless': args.headless, 'multi_gpu': False, 'fast_shutdown': False, 'renderer': 'RealTimePathTracing'})
        import numpy as np
        import omni.kit.app
        import omni.usd
        import omni.timeline
        from pxr import Gf, UsdGeom, UsdLux, UsdPhysics
        from sensor_metrics import point_cloud_metrics
        omni.kit.app.get_app().get_extension_manager().set_extension_enabled_immediate(
            'isaacsim.sensors.experimental.rtx', True)
        from isaacsim.sensors.experimental.rtx import Lidar, LidarSensor, parse_generic_model_output_data
        from omni.sensors.generic_model_output import CoordsType, FrameOfReference, ElementFlags
        omni.usd.get_context().new_stage()
        app.reset_render_settings()
        stage = omni.usd.get_context().get_stage()
        UsdGeom.SetStageMetersPerUnit(stage, 1.)
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
        stage.SetDefaultPrim(UsdGeom.Xform.Define(stage, '/World').GetPrim())
        UsdPhysics.Scene.Define(stage, '/World/PhysicsScene')
        # Closed room: every direction has a surface; the sensor is never inside a wall.
        for name, center, scale in [
            ('Floor', (0, 0, -.05), (6.2, 6.2, .1)),
            ('Ceiling', (0, 0, 3.05), (6.2, 6.2, .1)),
            ('West', (-3.05, 0, 1.5), (.1, 6.2, 3.)),
            ('East', (3.05, 0, 1.5), (.1, 6.2, 3.)),
            ('South', (0, -3.05, 1.5), (6.2, .1, 3.)),
            ('North', (0, 3.05, 1.5), (6.2, .1, 3.)),
        ]:
            cube = UsdGeom.Cube.Define(stage, '/World/'+name)
            cube.CreateSizeAttr(1.)
            cube.AddTranslateOp().Set(Gf.Vec3d(*center))
            cube.AddScaleOp().Set(Gf.Vec3f(*scale))
            cube.CreateDisplayColorAttr([Gf.Vec3f(.5, .5, .5)])
            UsdPhysics.CollisionAPI.Apply(cube.GetPrim())
        UsdLux.DomeLight.Define(stage, '/World/Light').CreateIntensityAttr(1000.)
        lidar = Lidar.create('/World/Lidar', config='Example_Rotary', tick_rate=10.,
                             translations=[[0., 0., 1.5]], orientations=[[1., 0., 0., 0.]],
                             accumulate_outputs=True,
                             attributes={'omni:sensor:Core:scanRateBaseHz': 10.})
        sensor = LidarSensor(lidar, annotators=['generic-model-output'])
        stage.Export(str(out / 'lidar_scene.usda'))
        timeline = omni.timeline.get_timeline_interface()
        timeline.play()
        for _ in range(args.warmup):
            app.update()
        last_timestamp = -1
        empty_reads, duplicate_reads = 0, 0
        for attempt in range(args.samples * 20):
            for _ in range(12):
                app.update()
            data, info = sensor.get_data('generic-model-output')
            if data is None or data.size == 0:
                empty_reads += 1
                continue
            gmo = parse_generic_model_output_data(data)
            timestamp = int(gmo.timestampNs)
            if timestamp <= last_timestamp:
                duplicate_reads += 1
                continue
            sample = len(report['scans'])
            np.save(out / f'gmo_{sample:03d}.npy', data.numpy().copy())
            if gmo.frameOfReference != FrameOfReference.SENSOR:
                raise RuntimeError(f'Expected sensor-local coordinates, got {gmo.frameOfReference}')
            x, y, z = (np.array(getattr(gmo, axis), copy=True) for axis in ('x', 'y', 'z'))
            flags = np.array(gmo.flags, copy=True)
            if not (len(x) == len(y) == len(z) == len(flags) == gmo.numElements):
                raise RuntimeError('GMO array lengths do not match numElements')
            valid = (flags & int(ElementFlags.VALID)) != 0
            if gmo.elementsCoordsType == CoordsType.SPHERICAL:
                azimuth, elevation, distance = np.radians(x), np.radians(y), z
                xyz = np.column_stack([distance*np.cos(elevation)*np.cos(azimuth),
                                       distance*np.cos(elevation)*np.sin(azimuth),
                                       distance*np.sin(elevation)])
            elif gmo.elementsCoordsType == CoordsType.CARTESIAN:
                xyz = np.column_stack([x, y, z])
            else:
                raise RuntimeError(f'Unexpected coordinate encoding: {gmo.elementsCoordsType}')
            points = xyz[valid]
            np.savez_compressed(out / f'scan_{sample:03d}.npz',
                                x=x, y=y, z=z, flags=flags, points=points)
            metrics = point_cloud_metrics(points)
            valid_fraction = float(valid.mean()) if len(valid) else 0.
            if valid_fraction < .9:
                metrics['passed'] = False
                metrics['failures'].append('Too few valid GMO returns in the enclosed test room')
            metrics.update(timestamp_ns=timestamp, frame_id=int(gmo.frameId),
                           gmo_valid_fraction=valid_fraction, coordinate_type=str(gmo.elementsCoordsType), info=str(info))
            report['scans'].append(metrics)
            last_timestamp = timestamp
            if len(report['scans']) == args.samples:
                break
        report.update(empty_reads=empty_reads, duplicate_reads=duplicate_reads)
        if len(report['scans']) != args.samples or not all(s['passed'] for s in report['scans']):
            raise RuntimeError('Missing, stale, partial or invalid lidar scans; inspect report.json')
        report.update(passed=True, captured_scans=len(report['scans']),
                      note='Angular coverage checks this enclosed fixture; it does not calibrate a vendor sensor.')
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
