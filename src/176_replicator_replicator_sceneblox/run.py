"""Generate a constrained labyrinth through Isaac Sim 5.1 SceneBlox APIs."""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=int, default=7)
    parser.add_argument("--cols", type=int, default=7)
    parser.add_argument("--variants", type=int, default=1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-tries", type=int, default=20)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--display", action="store_true", help="Show matplotlib WFC solving window (requires GUI)")
    parser.add_argument("--no-collisions", action="store_true")
    parser.add_argument("--config", type=Path, default=Path(__file__).with_name("config"))
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("output"))
    parser.add_argument("--steps", type=int, default=None,
                        help="GUI app updates after generation; omitted: keep GUI open; headless: no inspection")
    args = parser.parse_args()
    if args.steps is not None and args.steps < 1:
        parser.error("--steps must be positive")
    if min(args.rows,args.cols) < 4 or min(args.variants,args.max_tries) < 1:
        parser.error("rows/cols must be >= 4, variants/max-tries positive")
    if args.headless and args.display:
        parser.error("--display requires GUI; remove --headless")
    cfg = args.config.resolve()
    for filename in ["rules.yaml", "generation.yaml", "constraints.yaml"]:
        if not (cfg / filename).is_file():
            parser.error(f"Missing local configuration: {cfg / filename}")
    output = args.output.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=False)
    from isaacsim import SimulationApp
    app = SimulationApp({"headless": args.headless})
    try:
        import numpy as np
        import omni.kit.app
        from isaacsim.core.api import World
        from isaacsim.core.utils.stage import close_stage
        manager = omni.kit.app.get_app().get_extension_manager()
        manager.set_extension_enabled_immediate("isaacsim.replicator.scene_blox", True)
        from isaacsim.replicator.scene_blox.generation.scene_generator import SceneGenerator
        from isaacsim.replicator.scene_blox.grid_utils import config
        from isaacsim.replicator.scene_blox.grid_utils.grid import Grid
        from isaacsim.replicator.scene_blox.grid_utils.grid_constraints import GridConstraints
        from isaacsim.replicator.scene_blox.grid_utils.tile import tile_loader
        from isaacsim.replicator.scene_blox.grid_utils.tile_superposition import TileSuperposition
        config.GlobalRNG().rng = np.random.default_rng(args.seed)
        tiles, weights = tile_loader(str(cfg / "rules.yaml"))
        superposition = TileSuperposition(tiles, weights)
        generator = SceneGenerator(str(cfg / "generation.yaml"), not args.no_collisions)
        reports = []
        for variant in range(args.variants):
            constraints = GridConstraints.from_yaml(str(cfg / "constraints.yaml"), args.rows, args.cols)
            grid = Grid(args.rows, args.cols, superposition)
            solved = False
            for attempt in range(1, args.max_tries + 1):
                if grid.solve(constraints, args.display):
                    solved = True
                    break
                grid.reset(superposition)
                constraints.reset()
            if not solved:
                raise RuntimeError(f"No consistent grid after {args.max_tries} tries; inspect constraints or change seed")
            world = World(stage_units_in_meters=1.0)
            world.reset()
            destination = output / f"generated_{variant}.usd"
            generator.generate_scene(grid, world, str(destination))
            if not destination.is_file():
                raise RuntimeError(f"SceneBlox did not write {destination}")
            reports.append({"variant": variant, "attempts": attempt, "rows": args.rows, "cols": args.cols, "usd": str(destination)})
            if variant < args.variants - 1:
                close_stage()
                World.clear_instance()
        (output / "generation.json").write_text(json.dumps(reports, indent=2))
        inspection_updates = 0
        while not args.headless and app.is_running() and (args.steps is None or inspection_updates < args.steps):
            app.update()
            inspection_updates += 1
    finally:
        app.close()


if __name__ == "__main__":
    main()
