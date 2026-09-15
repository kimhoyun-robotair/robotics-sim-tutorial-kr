"""Add real IRC caption output settings to a native IRO configuration."""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="An existing complete IRO YAML exported by its UI")
    parser.add_argument("--output", required=True, type=Path, help="A new YAML path")
    parser.add_argument("--captions", action="store_true")
    parser.add_argument("--caption-only-writer", action="store_true")
    args = parser.parse_args()
    import yaml
    config = yaml.safe_load(args.input.read_text())
    iro = config["isaacsim.replicator.object"]
    if not isinstance(iro, dict):
        raise ValueError("Expected a complete isaacsim.replicator.object mapping")
    caption = json.loads((Path(__file__).parent / "caption_config.json").read_text())["isaacsim.replicator.caption.core"]["caption_configs"]
    caption.update(global_caption=args.captions, brief_caption=args.captions,
                   caption_writer="IROSceneGraphWriter" if args.caption_only_writer else "CombinedIROSceneGraphWriter")
    iro["caption_configs"] = caption
    iro.setdefault("output_switches", {})["caption"] = True
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as stream:
        yaml.safe_dump(config, stream, sort_keys=False)
    print(args.output.resolve())


if __name__ == "__main__":
    main()
