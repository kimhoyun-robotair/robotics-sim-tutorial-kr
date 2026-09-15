"""Script Editor: apply_camera_settings('/absolute/path/camera_settings.json')."""
import json
from pathlib import Path
import carb


def apply_camera_settings(path):
    values = json.loads(Path(path).read_text())
    for name in ("distance", "focallength", "height", "look_down_angle"):
        if values[f"min_camera_{name}"] > values[f"max_camera_{name}"]:
            raise ValueError(f"min exceeds max: {name}")
    if values["min_camera_height"] <= values["character_focus_height"]:
        raise ValueError("Camera height must exceed character focus height")
    if values["max_camera_height"] >= values["max_camera_distance"]:
        raise ValueError("Maximum camera height must be below maximum camera distance")
    prefix = "/persistent/exts/isaacsim.replicator.agent/"
    settings = carb.settings.get_settings()
    unknown = [name for name in values if settings.get(prefix + name) is None]
    if unknown:
        raise ValueError(f"Enable IRA first; unknown settings: {unknown}")
    for name, value in values.items():
        settings.set(prefix + name, value)
        print(name, settings.get(prefix + name))
