"""Configure the 5.1 native gantry gripper, close, lift, release, and log actual state."""
import argparse
import csv
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--steps", type=int, default=None,
                        help="Physics step limit; omitted/0: GUI until closed, headless default: 420")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--grip-distance", type=float, default=0.02)
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "output" / "gripper.csv")
    args = parser.parse_args()
    if args.steps is None:
        args.steps = 420 if args.headless else 0
    if args.steps < 0 or (args.headless and args.steps == 0):
        parser.error("--steps must be nonnegative; headless requires positive steps")
    if args.grip_distance <= 0:
        parser.error("--grip-distance must be positive")
    if args.output.exists():
        parser.error("Output exists; choose another --output")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    from isaacsim import SimulationApp

    app = SimulationApp({"headless": args.headless})
    try:
        from isaacsim.core.api import World
        from isaacsim.core.utils.extensions import enable_extension, get_extension_path_from_name
        from isaacsim.core.utils.stage import add_reference_to_stage, get_current_stage
        enable_extension("isaacsim.robot.surface_gripper")
        from isaacsim.robot.surface_gripper import GripperView
        from isaacsim.robot.surface_gripper._surface_gripper import GripperStatus
        from usd.schema.isaac import robot_schema

        world = World(stage_units_in_meters=1.0, physics_dt=1 / 60, rendering_dt=1 / 60)
        scene = Path(get_extension_path_from_name("isaacsim.robot.surface_gripper")) / "data" / "SurfaceGripper_gantry.usda"
        if not scene.is_file():
            raise FileNotFoundError(scene)
        add_reference_to_stage(str(scene), "/World")
        stage = get_current_stage()
        path = "/World/SurfaceGripper"
        robot_schema.CreateSurfaceGripper(stage, path)
        joints = stage.GetPrimAtPath("/World/Surface_Gripper_Joints")
        stage.GetPrimAtPath(path).GetRelationship(robot_schema.Relations.ATTACHMENT_POINTS.name).SetTargets(
            [joint.GetPath() for joint in joints.GetChildren()]
        )
        gripper = GripperView(paths=path)
        gripper.set_surface_gripper_properties(
            max_grip_distance=[args.grip_distance], coaxial_force_limit=[0.005],
            shear_force_limit=[5], retry_interval=[1.0],
        )
        world.reset()
        for axis, target in (("x", 0.0), ("y", 0.0), ("z", 0.140)):
            stage.GetPrimAtPath(f"/World/Joints/{axis}_joint").GetAttribute(
                "drive:linear:physics:targetPosition"
            ).Set(target)
        closed_seen = False
        with args.output.open("x", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(["step", "status", "gripped_objects"])
            step = 0
            while app.is_running() and (args.steps == 0 or step < args.steps):
                if step == 120:
                    gripper.apply_gripper_action([0.5])
                if step == 240:
                    stage.GetPrimAtPath("/World/Joints/z_joint").GetAttribute(
                        "drive:linear:physics:targetPosition"
                    ).Set(0.05)
                if step == 360:
                    gripper.apply_gripper_action([-0.5])
                world.step(render=not args.headless)
                if not app.is_running():
                    break
                if step % 10 == 0:
                    state = GripperStatus(gripper.get_surface_gripper_status()[0])
                    objects = gripper.get_gripped_objects()[0]
                    closed_seen |= state == GripperStatus.Closed and bool(objects)
                    writer.writerow([step, str(state), "|".join(objects)])
                    print(step, state, objects)
                step += 1
        if step >= 400 and not closed_seen:
            raise RuntimeError("No attached object was observed; inspect grip distance and joint contact geometry")
    finally:
        app.close()


if __name__ == "__main__":
    main()
