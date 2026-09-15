"""Script Editor: give each direct child of the selected warehouse pile its own rigid body."""
import omni.usd
from pxr import Usd, UsdGeom, UsdPhysics

context = omni.usd.get_context()
paths = context.get_selection().get_selected_prim_paths()
if len(paths) != 1:
    raise ValueError("Select the warehouse pile root prim, with one direct child per box")
stage = context.get_stage()
root = stage.GetPrimAtPath(paths[0])
boxes = [prim for prim in root.GetChildren() if prim.IsA(UsdGeom.Xformable)]
if not boxes:
    raise ValueError("Selected root has no transformable box children")
for box in boxes:
    UsdPhysics.RigidBodyAPI.Apply(box).CreateRigidBodyEnabledAttr(True)
    for prim in Usd.PrimRange(box):
        if prim.IsA(UsdGeom.Mesh) or prim.IsA(UsdGeom.Cube):
            UsdPhysics.CollisionAPI.Apply(prim).CreateCollisionEnabledAttr(True)
            if prim.IsA(UsdGeom.Mesh):
                UsdPhysics.MeshCollisionAPI.Apply(prim).CreateApproximationAttr("convexHull")
    print(f"Rigid box: {box.GetPath()}")
print("Physics authored in the current edit layer. Save As a new USD variant, then test against a ground plane.")
