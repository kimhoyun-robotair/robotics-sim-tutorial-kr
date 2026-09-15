"""Script Editor: inspect actual forklift joints, limits, drives and stage units."""
import json
import omni.usd
from pxr import UsdGeom, UsdPhysics

stage = omni.usd.get_context().get_stage()
result = {"meters_per_unit": UsdGeom.GetStageMetersPerUnit(stage), "joints": []}
for prim in stage.Traverse():
    if not prim.IsA(UsdPhysics.Joint):
        continue
    joint = UsdPhysics.Joint(prim)
    entry = {"path": str(prim.GetPath()), "type": prim.GetTypeName(),
             "body0": [str(x) for x in joint.GetBody0Rel().GetTargets()],
             "body1": [str(x) for x in joint.GetBody1Rel().GetTargets()]}
    for name in ["physics:axis", "physics:lowerLimit", "physics:upperLimit"]:
        attr = prim.GetAttribute(name)
        if attr:
            entry[name] = attr.Get()
    for kind in ["linear", "angular"]:
        if prim.HasAPI(UsdPhysics.DriveAPI, kind):
            drive = UsdPhysics.DriveAPI(prim, kind)
            entry[kind] = {"stiffness": drive.GetStiffnessAttr().Get(), "damping": drive.GetDampingAttr().Get(),
                           "target_position": drive.GetTargetPositionAttr().Get(), "target_velocity": drive.GetTargetVelocityAttr().Get()}
    result["joints"].append(entry)
print(json.dumps(result, indent=2))
movable = [j for j in result["joints"] if j["type"] in ("PhysicsRevoluteJoint", "PhysicsPrismaticJoint")]
if len(movable) != 7:
    raise RuntimeError(f"Forklift needs seven movable joints; found {len(movable)}")
