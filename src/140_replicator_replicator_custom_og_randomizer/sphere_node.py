"""Compute callback used by an actual OmniGraph ScriptNode."""
import math
import random

import omni.graph.core as og
import omni.usd
from pxr import Sdf, UsdGeom


def setup(db):
    db.per_instance_state.rng = random.Random(db.inputs.seed)


def compute(db):
    inner, outer = db.inputs.inner, db.inputs.outer
    if inner < 0 or outer <= 0 or inner > outer:
        db.log_error('Expected 0 <= inner <= outer and outer > 0')
        db.outputs.execOut = og.ExecutionAttributeState.DISABLED
        return False
    stage = omni.usd.get_context().get_stage()
    prims = [stage.GetPrimAtPath(str(path)) for path in db.inputs.prims]
    if not prims or any(not prim.IsValid() or not UsdGeom.Xformable(prim) for prim in prims):
        db.log_error('Every target must be an existing Xformable prim')
        db.outputs.execOut = og.ExecutionAttributeState.DISABLED
        return False
    rng = db.per_instance_state.rng
    with Sdf.ChangeBlock():
        for prim in prims:
            z = rng.uniform(-1, 1)
            azimuth = rng.uniform(0, 2 * math.pi)
            radius = rng.uniform(inner ** 3, outer ** 3) ** (1 / 3)
            xy = math.sqrt(max(0, 1 - z * z))
            translation = prim.GetAttribute('xformOp:translate')
            if not translation:
                translation = UsdGeom.Xformable(prim).AddTranslateOp().GetAttr()
            translation.Set((radius * xy * math.cos(azimuth), radius * xy * math.sin(azimuth), radius * z))
    db.outputs.execOut = og.ExecutionAttributeState.ENABLED
    return True
