"""Script Editor: set_actor_behavior(character='/absolute/path/behavior.py')."""
from pathlib import Path
import carb


def set_actor_behavior(character=None, nova_carter=None, iw_hub=None):
    paths = {
        "behavior_script_path": character,
        "nova_carter_behavior_script_path": nova_carter,
        "iw_hub_behavior_script_path": iw_hub,
    }
    selected = {key: Path(value).expanduser().resolve() for key, value in paths.items() if value}
    if not selected:
        raise ValueError("Supply at least one behavior script")
    for path in selected.values():
        if not path.is_file() or path.suffix != ".py":
            raise ValueError(f"Expected an existing Python behavior script: {path}")
    settings = carb.settings.get_settings()
    prefix = "/exts/isaacsim.replicator.agent/behavior_script_settings/"
    for key in selected:
        if settings.get(prefix + key) is None:
            raise RuntimeError("Enable the Isaac Sim 5.1 IRA extension first")
    for key, path in selected.items():
        settings.set(prefix + key, str(path))
        print(key, settings.get(prefix + key))
