import argparse
from itertools import count
from datetime import datetime
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Robot Simulation Snippets")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument(
        "--steps", type=int, default=None, help="Positive step limit; omitted: GUI stays open (headless: 120)"
    )
    parser.add_argument(
        "--output", type=Path, help="New output directory; existing paths are rejected"
    )
    parser.add_argument(
        "--control",
        choices=[
            "position",
            "single-position",
            "velocity",
            "single-velocity",
            "effort",
        ],
        default="position",
    )
    parser.add_argument("--usd", help="Optional local Franka Panda USD path")
    parser.add_argument(
        "--target",
        type=float,
        default=0.2,
        help="Position offset rad, velocity rad/s, or effort Nm",
    )
    args = parser.parse_args()
    if args.steps is not None and args.steps < 1:
        parser.error("--steps must be positive")
    step_limit = args.steps if args.steps is not None else (120 if args.headless else None)
    output = args.output or Path(__file__).parent / "output" / datetime.now().strftime(
        "%Y%m%d-%H%M%S-%f"
    )
    output.mkdir(parents=True, exist_ok=False)
    from isaacsim import SimulationApp

    app = SimulationApp({"headless": args.headless})
    try:
        import csv
        import math
        import numpy as np
        import omni.usd
        from isaacsim.core.api import World
        from isaacsim.core.prims import Articulation
        from isaacsim.core.utils.stage import add_reference_to_stage
        from isaacsim.storage.native import get_assets_root_path
        from pxr import UsdLux, UsdPhysics

        if not math.isfinite(args.target) or abs(args.target) > 0.5:
            raise ValueError(
                "Use a finite --target with magnitude <= 0.5 for this small-motion exercise"
            )
        root = get_assets_root_path() if not args.usd else ""
        if root is None:
            raise RuntimeError(
                "Isaac 5.1 assets unavailable; use --usd for a local Franka USD"
            )
        usd = args.usd or root + "/Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd"
        world = World(stage_units_in_meters=1.0, physics_dt=1 / 60, rendering_dt=1 / 60)
        world.scene.add_default_ground_plane()
        stage = omni.usd.get_context().get_stage()
        UsdLux.DistantLight.Define(stage, "/World/Light").CreateIntensityAttr(1500)
        variants = {}
        for i in (1, 2):
            prim = add_reference_to_stage(usd, f"/World/Franka_{i}")
            variants[str(prim.GetPath())] = {
                name: prim.GetVariantSet(name).GetVariantNames()
                for name in prim.GetVariantSets().GetNames()
            }
        robots = world.scene.add(
            Articulation(
                "/World/Franka_[1-2]",
                name="frankas",
                positions=np.array([[-1, 0, 0], [1, 0, 0]]),
            )
        )
        world.reset()
        if not robots.is_physics_handle_valid():
            raise RuntimeError("Franka articulation initialization failed")
        names = [f"panda_joint{i}" for i in range(1, 8)] + [
            "panda_finger_joint1",
            "panda_finger_joint2",
        ]
        missing = set(names) - set(robots.dof_names)
        if missing:
            raise RuntimeError(f"Franka asset has different joints: {sorted(missing)}")
        home = np.array([[0, -0.4, 0, -1.8, 0, 1.4, 0.5, 0.04, 0.04]] * 2)
        robots.set_joint_positions(home, joint_names=names)
        controlled = (
            ["panda_joint2"] if args.control.startswith("single") else names[:7]
        )
        if args.control in ("velocity", "single-velocity"):
            robots.set_gains(
                kps=np.zeros((2, len(controlled))),
                kds=np.full((2, len(controlled)), 20.0),
                joint_names=controlled,
            )
        elif args.control == "effort":
            controlled = ["panda_joint2"]
            robots.set_gains(
                kps=np.zeros((2, 1)), kds=np.zeros((2, 1)), joint_names=controlled
            )
        report = {
            "count": robots.count,
            "num_dof": robots.num_dof,
            "num_joints": robots.num_joints,
            "dof_names": robots.dof_names,
            "limits": robots.get_dof_limits().tolist(),
            "variants": variants,
            "control": args.control,
            "controlled_joints": controlled,
            "physics_joint_prims": [
                str(p.GetPath()) for p in stage.Traverse() if p.IsA(UsdPhysics.Joint)
            ],
        }
        (output / "robot_info.json").write_text(json.dumps(report, indent=2))
        with (output / "states.csv").open("x", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(
                ["step", "robot", "positions", "velocities", "applied_efforts"]
            )
            for step in count():
                if not app.is_running() or (step_limit is not None and step >= step_limit):
                    break
                if args.control in ("position", "single-position"):
                    targets = np.array(
                        [
                            [
                                home[row, names.index(name)]
                                + args.target * math.sin(step / 60)
                                for name in controlled
                            ]
                            for row in range(2)
                        ]
                    )
                    robots.set_joint_position_targets(targets, joint_names=controlled)
                elif args.control in ("velocity", "single-velocity"):
                    robots.set_joint_velocity_targets(
                        np.full((2, len(controlled)), args.target),
                        joint_names=controlled,
                    )
                else:
                    robots.set_joint_efforts(
                        np.full((2, 1), args.target), joint_names=controlled
                    )
                world.step(render=not args.headless)
                if not app.is_running():
                    break
                q = robots.get_joint_positions()
                qd = robots.get_joint_velocities()
                efforts = robots.get_applied_joint_efforts()
                for row in range(2):
                    writer.writerow(
                        [
                            step + 1,
                            row,
                            json.dumps(q[row].tolist()),
                            json.dumps(qd[row].tolist()),
                            json.dumps(efforts[row].tolist()),
                        ]
                    )
        print(json.dumps(report, indent=2))
        print(f"Outputs: {output.resolve()}")
    finally:
        app.close()


if __name__ == "__main__":
    main()
