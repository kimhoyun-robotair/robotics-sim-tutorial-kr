"""Validate captured modalities and write the Isaac Sim 5.1 documented Cosmos Transfer control JSON."""

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clip", type=Path, required=True)
    parser.add_argument("--prompt", default="A modern warehouse with metal storage racks, cardboard boxes, and an autonomous robot under soft industrial lighting.")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--edge-only", action="store_true")
    args = parser.parse_args()
    clip = args.clip.expanduser().resolve()
    indices = {}
    for modality in ("rgb", "depth", "segmentation", "shaded_seg", "edges"):
        video = clip / f"{modality}.mp4"
        if not video.is_file() or video.stat().st_size == 0:
            parser.error(f"Missing or empty captured video: {video}")
        indices[modality] = {p.stem.removeprefix(modality + "_") for p in (clip / modality).glob(f"{modality}_*.png")}
    if not indices["rgb"] or any(value != indices["rgb"] for value in indices.values()):
        parser.error(f"Frame indices differ across modalities: { {key: len(value) for key, value in indices.items()} }")
    config = {"prompt": args.prompt, "input_video_path": str(clip / "rgb.mp4")}
    if args.edge_only:
        config["edge"] = {"control_weight": 1.0}
    else:
        config.update({"vis": {"control_weight": 0.25}, "edge": {"control_weight": 0.25},
                       "depth": {"input_control": str(clip / "depth.mp4"), "control_weight": 0.25},
                       "seg": {"input_control": str(clip / "segmentation.mp4"), "control_weight": 0.25}})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(config, handle, indent=2)
        handle.write("\n")
    print(f"Matched {len(indices['rgb'])} PNG frame indices in all five modalities. Config: {args.output}")
    print("MP4 existence checked; video decoding and external Cosmos model inference have not run.")


if __name__ == "__main__":
    main()
