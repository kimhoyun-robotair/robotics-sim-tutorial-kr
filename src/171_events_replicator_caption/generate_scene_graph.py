"""Script Editor: awaitable run_caption_config(path, model_url=None, model_name=None)."""
import json
import os
from pathlib import Path
import carb
import omni.usd
from pxr import UsdGeom
from isaacsim.replicator.caption.core.settings import ReplicatorCaptionSettings
from isaacsim.replicator.caption.core.stage_info_manager import StageInfoManager


async def run_caption_config(path, model_url=None, model_name=None):
    config_path = Path(path).resolve()
    config = json.loads(config_path.read_text())["isaacsim.replicator.caption.core"]
    caption_flags = config["caption_configs"]
    wants_model = any(caption_flags[name] for name in ("global_caption", "brief_caption", "qa_caption"))
    key = os.environ.get("NIM_API_KEY")
    if wants_model and (not key or not model_url or not model_name):
        raise ValueError("Model captions require NIM_API_KEY plus explicit model_url and model_name")
    output = Path(config["output_path"])
    if output.exists():
        raise FileExistsError("Choose a fresh prepared configuration/output directory")
    ok, error = await omni.usd.get_context().open_stage_async(config["scene_path"])
    if not ok:
        raise RuntimeError(error)
    stage = omni.usd.get_context().get_stage()
    if not stage.GetPrimAtPath(config["camera_prim_path"]).IsA(UsdGeom.Camera):
        raise ValueError("Configured camera prim does not exist; inspect the stage camera path")
    settings = carb.settings.get_settings()
    settings.set(ReplicatorCaptionSettings.CACHE_CONFIG_FILE_PATH, str(config_path))
    ReplicatorCaptionSettings.set_target_camera_prim_path(config["camera_prim_path"])
    manager = StageInfoManager.get_instance()
    manager.refresh_configs()
    manager.refresh_camera_path()
    if wants_model:
        manager.set_model_params(model_url, model_name, key)
    graph = await manager.async_generate_camera_scene_graph_stage()
    if graph is None:
        raise RuntimeError("No scene graph was produced")
    generated = list(output.rglob("*scene_graph.json"))
    if not generated:
        raise RuntimeError("No exported scene graph files were found")
    print("Exported real scene graphs:", [str(file) for file in generated])
    return graph
