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
    # SimulationApp은 Python에서 Isaac Sim의 Kit 애플리케이션을 시작하고 갱신·종료하는 클래스이다.
    # headless=True는 창 없이 실행한다는 뜻이며, omni와 Isaac Sim 확장 모듈은 앱 생성 후 import한다.
    app = SimulationApp({"headless": args.headless})
    try:
        import numpy as np
        import omni.kit.app
        # omni.kit.app은 현재 Kit 앱과 확장 관리자에 접근하며 비동기 프레임 갱신을 기다리는 기능을 제공한다.
        from isaacsim.core.api import World
        # World는 Stage의 객체와 작업을 관리하고 물리·렌더링 시간 간격, 초기화, 시뮬레이션 진행을 제어한다.
        from isaacsim.core.utils.stage import close_stage
        # close_stage는 현재 열려 있는 USD Stage를 닫는다.
        manager = omni.kit.app.get_app().get_extension_manager()
        manager.set_extension_enabled_immediate("isaacsim.replicator.scene_blox", True)
        from isaacsim.replicator.scene_blox.generation.scene_generator import SceneGenerator
        # SceneGenerator는 Scene Blox의 격자 배치 결과를 USD 장면으로 생성한다.
        from isaacsim.replicator.scene_blox.grid_utils import config
        # config는 Scene Blox의 격자 생성에 사용하는 공통 설정을 제공한다.
        from isaacsim.replicator.scene_blox.grid_utils.grid import Grid
        # Grid는 Scene Blox에서 타일을 배치할 격자와 배치 상태를 관리한다.
        from isaacsim.replicator.scene_blox.grid_utils.grid_constraints import GridConstraints
        # GridConstraints는 Scene Blox 타일 배치에 적용할 제약을 불러온다.
        from isaacsim.replicator.scene_blox.grid_utils.tile import tile_loader
        # tile_loader는 Scene Blox 타일 정의와 이웃 배치 정보를 불러온다.
        from isaacsim.replicator.scene_blox.grid_utils.tile_superposition import TileSuperposition
        # TileSuperposition은 한 셀에 배치할 수 있는 타일 후보들을 표현한다.
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
                # 타일 인접 규칙과 제약을 만족하는 격자 배치를 탐색한다. 실패하면 초기화 후 다시 시도한다.
                if grid.solve(constraints, args.display):
                    solved = True
                    break
                grid.reset(superposition)
                constraints.reset()
            if not solved:
                raise RuntimeError(f"No consistent grid after {args.max_tries} tries; inspect constraints or change seed")
            # stage_units_in_meters는 장면 길이 단위이고, physics_dt·rendering_dt는 각각 물리·렌더링 시간 간격(초)이다.
            world = World(stage_units_in_meters=1.0)
            # World를 초기화하고 등록된 객체의 물리 핸들을 준비한다. 관절·강체 상태를 읽기 전에 호출한다.
            world.reset()
            destination = output / f"generated_{variant}.usd"
            # 해결된 타일 배치를 World에 구성하고 지정한 USD 파일로 생성한다.
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
            # Kit의 한 프레임을 갱신하여 렌더링·이벤트·비동기 작업을 처리한다.
            # 물리 진행 여부는 현재 타임라인의 재생 상태와 설정에 따라 달라진다.
            app.update()
            inspection_updates += 1
    finally:
        # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
        app.close()


if __name__ == "__main__":
    main()
