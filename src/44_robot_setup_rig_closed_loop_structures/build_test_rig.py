"""Script Editor: add the source lesson's two-axis gripper support and test cylinder."""
import omni.usd
from pxr import Gf, UsdGeom, UsdPhysics, PhysxSchema, PhysicsSchemaTools

stage = omni.usd.get_context().get_stage()
bases = [p for p in stage.Traverse() if p.GetName() == "base_link" and p.HasAPI(UsdPhysics.RigidBodyAPI)]
if len(bases) != 1:
    raise RuntimeError(f"Expected one gripper base_link, found {[str(p.GetPath()) for p in bases]}")
if stage.GetPrimAtPath("/TestRig"):
    raise RuntimeError("/TestRig exists; inspect the current test rig before recreating it")
base = bases[0]
transform = UsdGeom.XformCache().GetLocalToWorldTransform(base)
UsdGeom.Xform.Define(stage, "/TestRig")
for name in ["anchor", "slide"]:
    body = UsdGeom.Xform.Define(stage, f"/TestRig/{name}")
    body.AddTransformOp().Set(transform)
    UsdPhysics.RigidBodyAPI.Apply(body.GetPrim())
    UsdPhysics.MassAPI.Apply(body.GetPrim()).CreateMassAttr(0.1)
fixed = UsdPhysics.FixedJoint.Define(stage, "/TestRig/fixed")
fixed.CreateBody1Rel().SetTargets(["/TestRig/anchor"])
fixed.CreateLocalPos0Attr(Gf.Vec3f(transform.ExtractTranslation()))
q = transform.ExtractRotationQuat()
fixed.CreateLocalRot0Attr(Gf.Quatf(q.GetReal(), Gf.Vec3f(q.GetImaginary())))
for name, axis, parent, child in [("lift", "Z", "/TestRig/anchor", "/TestRig/slide"),
                                  ("reach", "X", "/TestRig/slide", str(base.GetPath()))]:
    joint = UsdPhysics.PrismaticJoint.Define(stage, "/TestRig/" + name)
    joint.CreateBody0Rel().SetTargets([parent])
    joint.CreateBody1Rel().SetTargets([child])
    joint.CreateAxisAttr(axis)
    joint.CreateLowerLimitAttr(0)
    joint.CreateUpperLimitAttr(1)
    drive = UsdPhysics.DriveAPI.Apply(joint.GetPrim(), "linear")
    drive.CreateStiffnessAttr(10000)
    drive.CreateDampingAttr(10000)
    drive.CreateTargetPositionAttr(0)
    PhysxSchema.PhysxJointAPI.Apply(joint.GetPrim()).CreateMaxJointVelocityAttr(5)
cylinder = UsdGeom.Cylinder.Define(stage, "/TestRig/Load")
cylinder.CreateRadiusAttr(0.025)
cylinder.CreateHeightAttr(0.2)
cylinder.AddTranslateOp().Set(Gf.Vec3d(0.12, 0, 0))
UsdPhysics.RigidBodyAPI.Apply(cylinder.GetPrim())
UsdPhysics.CollisionAPI.Apply(cylinder.GetPrim())
UsdPhysics.MassAPI.Apply(cylinder.GetPrim()).CreateMassAttr(0.2)
PhysicsSchemaTools.addGroundPlane(stage, "/TestRig/Ground", "Z", 10, Gf.Vec3f(0, 0, -0.1), Gf.Vec3f(0.4))
scenes = [p for p in stage.Traverse() if p.IsA(UsdPhysics.Scene)]
scene = UsdPhysics.Scene(scenes[0]) if scenes else UsdPhysics.Scene.Define(stage, "/TestRig/PhysicsScene")
physics = PhysxSchema.PhysxSceneAPI.Apply(scene.GetPrim())
physics.CreateEnableGPUDynamicsAttr(False)
physics.CreateTimeStepsPerSecondAttr(80)
print("Created /TestRig; align the load with the actual fingertips, then inspect limits before Play.")
