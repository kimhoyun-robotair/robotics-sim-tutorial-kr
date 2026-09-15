"""Run in Isaac Sim's Script Editor after opening this package's stage."""
import omni.usd
from pxr import Gf, UsdGeom, UsdPhysics

stage = omni.usd.get_context().get_stage()
bodies = [p for p in stage.Traverse() if p.GetName() == "body" and p.HasAPI(UsdPhysics.RigidBodyAPI)]
if len(bodies) != 1:
    raise RuntimeError(f"Expected exactly one rigid body named body, found {[str(p.GetPath()) for p in bodies]}")
body = bodies[0]
mount_path = str(body.GetPath()) + "/camera_mount"
if stage.GetPrimAtPath(mount_path):
    raise RuntimeError("camera_mount exists; inspect or remove your previous mount before recreating it")
mount = UsdGeom.Xform.Define(stage, mount_path)
mount.AddTranslateOp().Set(Gf.Vec3d(-6, 0, 2.2))
mount.AddRotateXYZOp().Set(Gf.Vec3f(0, -80, -90))
camera = UsdGeom.Camera.Define(stage, mount_path + "/car_camera")
camera.CreateFocalLengthAttr(24.0)
camera.CreateHorizontalApertureAttr(20.955)
camera.CreateVerticalApertureAttr(15.2908)
camera.CreateClippingRangeAttr(Gf.Vec2f(0.01, 10000))
print("Camera attached:", camera.GetPath(), "parent rigid body:", body.GetPath())
print("The camera's local transform is identity; edit the mount for a recoverable mounting pose.")
