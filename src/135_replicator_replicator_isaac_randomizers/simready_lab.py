"""Native SimReady search, USD variants, temporary layers, and physics settling."""
import asyncio
import json
import random


def run(app, stage, product, frames, steps, seed, output):
    import omni.kit.actions.core
    import omni.replicator.core as rep
    import omni.timeline
    from isaacsim.core.utils.extensions import enable_extension
    from isaacsim.core.utils.semantics import upgrade_prim_semantics_to_labels
    from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics
    enable_extension('omni.simready.explorer')
    import omni.simready.explorer as explorer
    if explorer.get_instance().browser_model is None:
        omni.kit.actions.core.execute_action('omni.simready.explorer', 'toggle_window')
    rng = random.Random(seed)

    async def search():
        tables = await explorer.find_assets(['table', 'furniture'])
        dishes = await explorer.find_assets(['plate'])
        items = await explorer.find_assets(['fruit'])
        if not tables or not dishes or not items:
            raise RuntimeError('SimReady search returned an empty category; verify the Explorer asset catalog connection')
        return tables, dishes, items

    task = asyncio.ensure_future(search())
    for _ in range(10000):
        if task.done():
            break
        app.update()
    else:
        task.cancel()
        raise TimeoutError('SimReady asset search exceeded 10000 app updates')
    tables, dishes, items = task.result()
    records = []
    timeline = omni.timeline.get_timeline_interface()
    session = stage.GetSessionLayer()
    for frame in range(frames):
        layer = Sdf.Layer.CreateAnonymous('simready_scenario')
        session.subLayerPaths.append(layer.identifier)
        try:
            with Usd.EditContext(stage, layer):
                chosen = [rng.choice(tables), rng.choice(dishes), rng.choice(items)]
                prims = []
                for index, asset in enumerate(chosen):
                    prim = stage.DefinePrim(f'/Assets/Object_{index}', 'Xform')
                    prim.GetReferences().AddReference(asset.main_url)
                    variant = prim.GetVariantSets().GetVariantSet('PhysicsVariant')
                    if not variant or 'RigidBody' not in variant.GetVariantNames():
                        raise RuntimeError(f'{asset.name} does not expose PhysicsVariant=RigidBody')
                    variant.SetVariantSelection('RigidBody')
                    upgrade_prim_semantics_to_labels(prim)
                    prims.append(prim)
                UsdPhysics.RigidBodyAPI.Apply(prims[0]).CreateRigidBodyEnabledAttr(False)
                cache = UsdGeom.BBoxCache(Usd.TimeCode.Default(), [UsdGeom.Tokens.default_])
                table_bounds = cache.ComputeWorldBound(prims[0]).ComputeAlignedRange()
                height = table_bounds.GetMax()[2]
                for prim in prims[1:]:
                    bounds = cache.ComputeWorldBound(prim).ComputeAlignedRange()
                    height += max(bounds.GetSize()[2], 0.05) / 2 + 0.1
                    translate = prim.GetAttribute('xformOp:translate')
                    if not translate:
                        translate = UsdGeom.Xformable(prim).AddTranslateOp().GetAttr()
                    translate.Set(Gf.Vec3d(table_bounds.GetMidpoint()[0], table_bounds.GetMidpoint()[1], height))
                    height += max(bounds.GetSize()[2], 0.05) / 2
                timeline.play()
                for _ in range(steps):
                    app.update()
                timeline.pause()
                camera = stage.GetPrimAtPath('/World/Camera')
                eye = Gf.Vec3d(table_bounds.GetMidpoint()[0], table_bounds.GetMidpoint()[1], height + 2)
                camera.GetAttribute('xformOp:translate').Set(eye)
                # A default USD camera looks down local -Z, directly at the table here.
                camera.GetAttribute('xformOp:orient').Set(Gf.Quatf(1))
                rep.orchestrator.step(rt_subframes=8, delta_time=0.0)
                records.append({'frame': frame, 'assets': [{'name': a.name, 'url': a.main_url} for a in chosen]})
                stage.Flatten().Export(str(output / f'simready_{frame:04d}.usda'))
            timeline.stop()
            app.update()
        finally:
            session.subLayerPaths.remove(layer.identifier)
    (output / 'measurements.json').write_text(json.dumps(records, indent=2))
