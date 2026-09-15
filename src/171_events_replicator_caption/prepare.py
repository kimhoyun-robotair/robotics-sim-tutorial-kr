"""Create a native IRC YAML config with explicit output and optional model captions."""
import argparse
import json
from pathlib import Path


def main():
    package = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=package / "output" / "graph_01")
    parser.add_argument("--scene", help="USD file/URL; defaults to official 5.1 captioning sample")
    parser.add_argument("--camera", default="/World/Cameras/Camera")
    parser.add_argument("--captions", action="store_true", help="Enable model requests when generated config is executed")
    parser.add_argument("--pruning-ratio", type=float, default=1.0)
    args = parser.parse_args()
    if not 0 <= args.pruning_ratio <= 1:
        parser.error("Pruning ratio must be in [0, 1]")
    output = args.output.expanduser().resolve()
    if output.exists():
        parser.error("Choose a new --output directory")
    config = json.loads((package / "caption_config.json").read_text())
    core = config["isaacsim.replicator.caption.core"]
    if args.scene:
        core["scene_path"] = args.scene
    core["camera_prim_path"] = args.camera
    core["output_path"] = str(output / "capture")
    core["caption_configs"]["pruning_ratio"] = args.pruning_ratio
    core["caption_configs"].update(global_caption=args.captions, brief_caption=args.captions)
    output.mkdir(parents=True)
    target = output / "config.yaml"
    target.write_text(json.dumps(config, indent=2) + "\n")
    print(target)


if __name__ == "__main__":
    main()
