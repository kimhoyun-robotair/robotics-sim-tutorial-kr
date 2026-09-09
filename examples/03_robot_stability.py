"""Import the supplied URDF, fix its base, drive one DOF and fail on instability.

Isaac Sim 6.0.1 APIs are checked against the official reference. GPU runtime
validation must still be performed on a supported Isaac Sim workstation.
"""
from __future__ import annotations
import argparse
import itertools
import json
from pathlib import Path
import traceback


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--headless', action='store_true')
    parser.add_argument('--output-dir', '--output', dest='output_dir', default='artifacts/robot')
    parser.add_argument('--steps', type=int, default=720)
    args = parser.parse_args()
    if args.steps < 600:
        parser.error('--steps must be at least 600 for ramp, hold and observation')
    out = Path(args.output_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    report = {'passed': False, 'isaac_sim_target': '6.0.1', 'fixture': 'one_joint_arm'}
    app = None
    try:
        from isaacsim import SimulationApp
        app = SimulationApp({'headless': args.headless, 'multi_gpu': False, 'fast_shutdown': False})
        import numpy as np
        import omni.kit.app
        import omni.usd
        import omni.timeline
        from pxr import Gf, Sdf, UsdGeom, UsdPhysics, UsdLux, PhysxSchema
        manager = omni.kit.app.get_app().get_extension_manager()
        for extension in ('isaacsim.asset.importer.urdf', 'isaacsim.core.experimental.prims'):
            manager.set_extension_enabled_immediate(extension, True)
        from isaacsim.asset.importer.urdf import URDFImporter, URDFImporterConfig
        from isaacsim.core.experimental.prims import Articulation, RigidPrim
        from isaacsim.core.simulation_manager import SimulationManager
        from sensor_metrics import quaternion_tilt_deg
        urdf = Path(__file__).resolve().parents[1] / 'assets/one_joint_arm.urdf'
        imported = URDFImporter(URDFImporterConfig(
            urdf_path=str(urdf), usd_path=str(out / 'imported'),
            collision_from_visuals=False, merge_mesh=False, allow_self_collision=False,
        )).import_urdf()
        if not imported:
            raise RuntimeError('URDF importer returned no output path')
        omni.usd.get_context().new_stage()
        app.reset_render_settings()
        stage = omni.usd.get_context().get_stage()
        UsdGeom.SetStageMetersPerUnit(stage, 1.0)
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
        root = UsdGeom.Xform.Define(stage, '/World').GetPrim()
        stage.SetDefaultPrim(root)
        robot_prim = UsdGeom.Xform.Define(stage, '/World/Robot').GetPrim()
        robot_prim.GetReferences().AddReference(str(imported))
        # Resolve actual importer paths; fail on ambiguity instead of guessing a hierarchy.
        links = {}
        for name in ('base_link', 'arm_link'):
            candidates = [p for p in stage.Traverse() if p.GetName() == name and p.HasAPI(UsdPhysics.RigidBodyAPI)]
            if len(candidates) != 1:
                raise RuntimeError(f'Expected one rigid {name}, found {[str(p.GetPath()) for p in candidates]}')
            links[name] = candidates[0]
        for prim in list(stage.Traverse()):
            if prim.HasAPI(UsdPhysics.ArticulationRootAPI):
                prim.RemoveAPI(UsdPhysics.ArticulationRootAPI)
        fixed = UsdPhysics.FixedJoint.Define(stage, '/World/Robot/world_fixed_joint')
        fixed.CreateBody1Rel().SetTargets([links['base_link'].GetPath()])
        fixed.CreateLocalPos0Attr(Gf.Vec3f(0, 0, 0))
        fixed.CreateLocalPos1Attr(Gf.Vec3f(0, 0, 0))
        UsdPhysics.ArticulationRootAPI.Apply(fixed.GetPrim())
        physics = PhysxSchema.PhysxArticulationAPI.Apply(fixed.GetPrim())
        physics.CreateEnabledSelfCollisionsAttr(False)
        physics.CreateSolverPositionIterationCountAttr(16)
        physics.CreateSolverVelocityIterationCountAttr(4)
        scene = UsdPhysics.Scene.Define(stage, '/World/PhysicsScene')
        scene.CreateGravityDirectionAttr(Gf.Vec3f(0, 0, -1))
        scene.CreateGravityMagnitudeAttr(9.81)
        ground = UsdGeom.Cube.Define(stage, '/World/Ground')
        ground.CreateSizeAttr(1.)
        ground.AddTranslateOp().Set(Gf.Vec3d(0, 0, -.05))
        ground.AddScaleOp().Set(Gf.Vec3f(4, 4, .1))
        UsdPhysics.CollisionAPI.Apply(ground.GetPrim())
        UsdLux.DomeLight.Define(stage, '/World/Light').CreateIntensityAttr(1000.)
        articulation = Articulation('/World/Robot')
        bodies = RigidPrim([str(links[n].GetPath()) for n in ('base_link', 'arm_link')])
        SimulationManager.set_physics_dt(1/120)
        timeline = omni.timeline.get_timeline_interface()
        timeline.play()
        for _ in range(20):
            app.update()
        if list(articulation.dof_names) != ['shoulder']:
            raise RuntimeError(f'Unexpected DOF order: {articulation.dof_names}')
        articulation.set_dof_gains(stiffnesses=[40.], dampings=[8.])
        articulation.set_dof_max_efforts([20.])
        articulation.set_dof_max_velocities([1.])
        articulation.set_dof_position_targets([0.])
        stage.Export(str(out / 'robot_scene.usda'))
        history = []
        start = SimulationManager.get_simulation_time()
        failure = None
        # Known local collision-box corners allow a geometry-aware floor check.
        boxes = [([0., 0., .15], [.15, .15, .15]), ([.35, 0., 0.], [.3, .04, .04])]
        for tick in range(args.steps):
            elapsed = SimulationManager.get_simulation_time() - start
            # Hold for 1 s, ramp over 2 s, then hold at 0.4 rad.
            target = .4 * min(max((elapsed-1.)/2., 0.), 1.)
            articulation.set_dof_position_targets([target])
            app.update()
            q = articulation.get_dof_positions().numpy().copy().reshape(-1)
            qd = articulation.get_dof_velocities().numpy().copy().reshape(-1)
            p_w, r_w = bodies.get_world_poses()
            positions, orientations = p_w.numpy().copy(), r_w.numpy().copy()
            if not all(np.isfinite(a).all() for a in (q, qd, positions, orientations)):
                failure = 'Non-finite joint or link state'
                break
            bottom = []
            for p, quat, (center, half) in zip(positions, orientations, boxes):
                rotation = Gf.Rotation(Gf.Quatd(float(quat[0]), Gf.Vec3d(*map(float, quat[1:]))))
                corners = [np.asarray(center)+np.asarray(sign)*half for sign in itertools.product((-1, 1), repeat=3)]
                bottom.append(min(float((rotation.TransformDir(Gf.Vec3d(*map(float, c)))+Gf.Vec3d(*map(float, p)))[2]) for c in corners))
            tilt = quaternion_tilt_deg(orientations[0])
            drift = float(np.linalg.norm(positions[0]))
            sample_time = SimulationManager.get_simulation_time() - start
            history.append([float(sample_time), target, float(q[0]), float(qd[0]), drift, tilt, *bottom])
            if abs(q[0]) > np.pi/2+.02 or abs(qd[0]) > 1.2 or min(bottom) < -.005 or drift > .005 or tilt > 1.:
                failure = 'Joint limit, velocity, base drift, tilt or floor penetration check failed'
                break
        data = np.asarray(history, dtype=float).reshape(-1, 8)
        np.save(out / 'joint_history.npy', data)
        np.savetxt(out / 'joint_history.csv', data, delimiter=',',
                   header='time_s,target_rad,position_rad,velocity_rad_s,base_drift_m,base_tilt_deg,base_bottom_m,arm_bottom_m')
        if failure:
            raise RuntimeError(failure)
        final_error = float(abs(data[-1, 2]-.4)) if len(data) else None
        if not len(data) or data[-1, 0] < 5 or final_error > .03:
            raise RuntimeError(f'Insufficient simulated time or final tracking error: {final_error}')
        report.update(passed=True, samples=len(data), final_error_rad=final_error,
                      max_base_drift_m=float(data[:, 4].max()), max_base_tilt_deg=float(data[:, 5].max()),
                      minimum_bottom_m=float(data[:, 6:].min()),
                      note='Pass applies to sampled app-update states after 20 warmup updates; intermediate physics steps and startup transients are not exhaustively checked.')
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
