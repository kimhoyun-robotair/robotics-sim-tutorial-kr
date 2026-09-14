"""Standalone Python: Franka의 IK, RRT, RMPflow pick & place와 실제 접촉 관측."""

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
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
    parser.add_argument(
        "--mode", choices=["pick-place", "ik", "rrt"], default="pick-place"
    )
    parser.add_argument("--steps", type=positive_int, default=2400)
    args = parser.parse_args()
    output = output_directory("03_manipulator", args.output)
    app = launch_app(args.headless)
    try:
        import numpy as np
        from isaacsim.core.api import World
        from isaacsim.core.api.objects import DynamicCuboid, FixedCuboid, VisualCuboid
        from isaacsim.core.utils.rotations import euler_angles_to_quat
        from isaacsim.robot.manipulators.controllers import PickPlaceController
        from isaacsim.robot.manipulators.examples.franka import Franka, KinematicsSolver
        from isaacsim.robot.manipulators.examples.franka.controllers.rmpflow_controller import (
            RMPFlowController,
        )
        from isaacsim.robot_motion.motion_generation import (
            PathPlannerVisualizer,
            interface_config_loader,
        )
        from isaacsim.robot_motion.motion_generation.lula import RRT
        from isaacsim.sensors.physics import ContactSensor

        dt = 1 / 60
        world = World(stage_units_in_meters=1.0, physics_dt=dt, rendering_dt=dt)
        world.scene.add_default_ground_plane()
        robot = world.scene.add(Franka(prim_path="/World/Franka", name="franka"))
        cube = world.scene.add(
            DynamicCuboid(
                prim_path="/World/Cube",
                name="cube",
                position=np.array([0.45, 0.25, 0.026]),
                size=0.0515,
                mass=0.05,
                color=np.array([0.1, 0.3, 0.9]),
            )
        )
        place = np.array([0.45, -0.25, 0.026])
        world.scene.add(
            VisualCuboid(
                prim_path="/World/Target",
                name="target",
                position=place - np.array([0.0, 0.0, 0.024]),
                size=1.0,
                scale=np.array([0.14, 0.14, 0.002]),
                color=np.array([0.1, 0.8, 0.2]),
            )
        )
        obstacle = world.scene.add(
            FixedCuboid(
                prim_path="/World/Obstacle",
                name="obstacle",
                position=np.array([0.50, 0.0, 0.12]),
                size=1.0,
                scale=np.array([0.10, 0.10, 0.24]),
                color=np.array([0.9, 0.3, 0.1]),
            )
        )
        # Cube의 raw contact에서 상대 body를 확인해야 바닥 접촉을 grasp로 오인하지 않는다.
        contact = world.scene.add(
            ContactSensor(
                prim_path="/World/Cube/Contact",
                name="cube_contact",
                dt=dt,
                min_threshold=0.0,
                max_threshold=10000.0,
                radius=-1,
            )
        )
        contact.add_raw_contact_data_to_frame()
        robot.gripper.set_default_state(robot.gripper.joint_opened_positions)
        world.reset()
        for _ in range(60):
            world.step(render=not args.headless)

        high_target = np.array([0.45, -0.25, 0.40])
        orientation = euler_angles_to_quat(np.array([0.0, np.pi, 0.0]))
        ik = KinematicsSolver(robot)
        rmp = RMPFlowController("rmp", robot, physics_dt=dt)
        rmp.rmp_flow.add_obstacle(obstacle)
        pick_place = PickPlaceController(
            name="pick_place",
            cspace_controller=rmp,
            gripper=robot.gripper,
            end_effector_initial_height=0.40,
            events_dt=[
                0.008,
                0.005,
                0.05,
                0.01,
                0.005,
                0.005,
                0.005,
                0.01,
                0.008,
                0.02,
            ],
        )
        plan = []
        if args.mode == "rrt":
            planner = RRT(
                **interface_config_loader.load_supported_path_planner_config(
                    "Franka", "RRT"
                )
            )
            planner.add_obstacle(obstacle)
            planner.set_max_iterations(5000)
            planner.set_end_effector_target(high_target, orientation)
            planner.update_world()
            plan = PathPlannerVisualizer(
                robot, planner
            ).compute_plan_as_articulation_actions(max_cspace_dist=0.02)
            if not plan:
                raise RuntimeError(
                    "RRT가 경로를 찾지 못했습니다. target과 장애물 위치를 확인하세요."
                )

        start_height = float(cube.get_world_pose()[0][2])
        grasp_confirmed = False
        max_height = start_height
        finished_at = None
        ik_success = False
        samples = 0
        with (output / "manipulation.csv").open(
            "w", newline="", encoding="utf-8"
        ) as stream:
            log = csv.writer(stream)
            log.writerow(
                [
                    "step",
                    "time_s",
                    "event",
                    "cube_x",
                    "cube_y",
                    "cube_z",
                    "contact_force_N",
                    "finger_contact",
                    "grasp_confirmed",
                    "joint7_effort_Nm",
                ]
            )
            for step in range(args.steps):
                if not app.is_running() or not world.is_playing():
                    break
                if args.mode == "pick-place":
                    action = pick_place.forward(
                        picking_position=cube.get_world_pose()[0],
                        placing_position=place,
                        current_joint_positions=robot.get_joint_positions(),
                        end_effector_offset=np.array([0.0, 0.005, 0.0]),
                    )
                    robot.apply_action(action)
                    if pick_place.is_done() and finished_at is None:
                        finished_at = step
                elif args.mode == "ik":
                    action, ik_success = ik.compute_inverse_kinematics(
                        high_target, orientation
                    )
                    if not ik_success:
                        raise RuntimeError("IK가 수렴하지 않았습니다.")
                    robot.apply_action(action)
                else:
                    # 한 waypoint를 여러 step 유지한다. 이것은 속도 제한을 보장하는 trajectory retiming은 아니다.
                    robot.apply_action(plan[min(step // 4, len(plan) - 1)])
                world.step(render=not args.headless)
                position, _ = cube.get_world_pose()
                frame = contact.get_current_frame()
                finger_contact = any(
                    "panda_leftfinger" in item[body]
                    or "panda_rightfinger" in item[body]
                    for item in frame.get("contacts", [])
                    for body in ("body0", "body1")
                )
                max_height = max(max_height, float(position[2]))
                grasp_confirmed |= bool(
                    finger_contact and position[2] > start_height + 0.05
                )
                effort = robot.get_measured_joint_efforts(
                    joint_indices=np.array([robot.get_dof_index("panda_joint7")])
                )
                log.writerow(
                    [
                        step,
                        (step + 1) * dt,
                        pick_place.get_current_event()
                        if args.mode == "pick-place"
                        else -1,
                        *position,
                        frame.get("force", 0.0),
                        finger_contact,
                        grasp_confirmed,
                        float(effort[0]),
                    ]
                )
                samples += 1
                if finished_at is not None and step - finished_at >= 120:
                    break
        position, _ = cube.get_world_pose()
        ee, _ = ik.compute_end_effector_pose()
        placement_error = float(np.linalg.norm(position - place))
        target_error = float(np.linalg.norm(ee - high_target))
        success = (
            grasp_confirmed and finished_at is not None and placement_error < 0.08
            if args.mode == "pick-place"
            else target_error < 0.05
        )
        write_json(
            output / "summary.json",
            {
                "isaac_sim": "5.1.0",
                "mode": args.mode,
                "steps": samples,
                "success": bool(success),
                "controller_done": finished_at is not None,
                "grasp_confirmed": grasp_confirmed,
                "max_cube_height_m": max_height,
                "placement_error_m": placement_error,
                "end_effector_target_error_m": target_error,
                "rrt_waypoints": len(plan),
                "ik_converged": bool(ik_success),
                "dt_s": dt,
            },
        )
        world.stop()
        print(f"조작 결과: {output}; success={success}")
        if not success:
            raise RuntimeError(
                "완료 판정을 통과하지 못했습니다. summary.json과 접촉 로그를 확인하세요."
            )
    finally:
        close_app(app)


if __name__ == "__main__":
    main()
