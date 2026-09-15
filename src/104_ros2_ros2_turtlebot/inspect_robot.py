"""Run in Isaac Sim Script Editor after importing the TurtleBot."""
import omni.usd
from pxr import UsdPhysics
stage = omni.usd.get_context().get_stage()
roots = []
wheels = []
for prim in stage.Traverse():
    if prim.HasAPI(UsdPhysics.ArticulationRootAPI):
        roots.append(str(prim.GetPath()))
    if prim.GetName() in ("wheel_left_joint", "wheel_right_joint"):
        drive = UsdPhysics.DriveAPI.Get(prim, "angular")
        if not drive:
            raise RuntimeError(f"No angular drive at {prim.GetPath()}")
        row = {"path": str(prim.GetPath()), "stiffness": drive.GetStiffnessAttr().Get(),
               "damping": drive.GetDampingAttr().Get(), "target_velocity": drive.GetTargetVelocityAttr().Get()}
        wheels.append(row)
        print(row)
print("articulation_roots=", roots)
if len(wheels) != 2:
    raise RuntimeError(f"Expected two TurtleBot wheel joints; found {len(wheels)}")
