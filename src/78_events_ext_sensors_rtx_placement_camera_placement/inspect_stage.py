"""Run in Isaac Sim 5.1 Window > Script Editor after opening room.usda."""
import omni.kit.app
import omni.usd
from pxr import UsdGeom

stage = omni.usd.get_context().get_stage()
if stage is None:
    raise RuntimeError("먼저 room.usda를 여세요.")
assert UsdGeom.GetStageMetersPerUnit(stage) == 1, "stage unit must be meters"
assert UsdGeom.GetStageUpAxis(stage) == "Z", "stage up axis must be Z"
manager = omni.kit.app.get_app().get_extension_manager()
for name in ("isaacsim.sensors.rtx.placement", "omni.anim.navigation.bundle"):
    if not manager.is_extension_enabled(name):
        raise RuntimeError(f"Window > Extensions에서 {name} 활성화 필요")
import omni.anim.navigation.core as nav
mesh = nav.acquire_interface().get_navmesh()
if mesh is None:
    raise RuntimeError("Window > Navigation > Navmesh > Bake를 먼저 실행하세요.")
paths = [str(p.GetPath()) for p in stage.Traverse() if p.IsA(UsdGeom.Camera)]
print({"meters_per_unit": 1, "up_axis": "Z", "navmesh_available": True, "camera_paths": paths})
