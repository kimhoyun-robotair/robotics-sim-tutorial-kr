"""Standalone Python: seed가 고정된 robot camera 데이터셋 생성."""

import argparse
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "core"))
sys.path.insert(0, str(PROJECT.parent))
from tutorial_common.runtime import (
    add_common_arguments,
    close_app,
    launch_app,
    output_directory,
    positive_int,
    write_json,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_arguments(parser)
    parser.add_argument("--episodes", type=positive_int, default=3)
    parser.add_argument(
        "--frames", type=positive_int, default=20, help="episode당 capture 수"
    )
    parser.add_argument("--steps-per-frame", type=positive_int, default=4)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--width", type=positive_int, default=320)
    parser.add_argument("--height", type=positive_int, default=240)
    args = parser.parse_args()
    output = output_directory("04_sdg", args.output)
    app = launch_app(args.headless)
    scene = None
    try:
        import omni.replicator.core as rep
        from isaacsim.core.api import World
        from robot_sdg.dataset import DatasetScene

        world = World(stage_units_in_meters=1.0, physics_dt=1 / 60, rendering_dt=1 / 60)
        scene = DatasetScene(world, args.seed, (args.width, args.height))
        world.reset()
        scene.initialize_camera()
        scene.attach_writer(output / "dataset")
        for episode in range(args.episodes):
            scene.randomize(episode)
            for frame in range(args.frames):
                if not app.is_running():
                    raise RuntimeError("생성이 완료되기 전에 앱이 종료되었습니다.")
                for _ in range(args.steps_per_frame):
                    scene.drive_forward()
                    world.step(
                        render=True
                    )  # headless에서도 camera를 위한 rendering은 필요하다.
                rep.orchestrator.step(
                    rt_subframes=4, delta_time=0.0, pause_timeline=False
                )
                scene.record_metadata(episode, frame)
        rep.orchestrator.wait_until_complete()
        write_json(
            output / "summary.json",
            {
                "isaac_sim": "5.1.0",
                "seed": args.seed,
                "episodes": args.episodes,
                "frames_written": scene.frames_written,
                "resolution": [args.width, args.height],
                "physics_dt_s": 1 / 60,
                "steps_per_frame": args.steps_per_frame,
            },
        )
        world.stop()
        print(f"데이터셋: {output}", flush=True)
    finally:
        try:
            if scene is not None:
                try:
                    import omni.replicator.core as rep

                    rep.orchestrator.wait_until_complete()
                finally:
                    scene.detach_writer()
        finally:
            close_app(app)


if __name__ == "__main__":
    main()
