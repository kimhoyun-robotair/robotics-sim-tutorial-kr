"""Script Editor: compare actual scenegraph structure before and after mesh optimization."""
import json
import omni.usd
from pxr import Usd, UsdGeom

stage = omni.usd.get_context().get_stage()
meshes = []
for prim in Usd.PrimRange.Stage(stage, Usd.TraverseInstanceProxies()):
    if prim.IsA(UsdGeom.Mesh):
        mesh = UsdGeom.Mesh(prim)
        meshes.append({"path": str(prim.GetPath()), "faces": len(mesh.GetFaceVertexCountsAttr().Get() or []),
                       "instance_proxy": prim.IsInstanceProxy()})
print(json.dumps({"mesh_occurrences": len(meshes), "prototypes": len(stage.GetPrototypes()),
                  "instance_roots": [str(p.GetPath()) for p in stage.Traverse() if p.IsInstance()],
                  "meshes": meshes}, indent=2))
