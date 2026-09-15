"""Run in Isaac Sim Script Editor on a new stage, then call the functions below."""

import asyncio

import numpy as np
import omni.usd
from isaacsim.core.api import World
from isaacsim.core.prims import Articulation
from isaacsim.core.utils.stage import add_reference_to_stage
from isaacsim.storage.native import get_assets_root_path
from pxr import UsdLux


async def setup_robot():
    global tutorial_world, arm_handle
    if World.instance() is not None:
        raise RuntimeError(
            "A World already exists. Restart this GUI instance before this exercise."
        )
    root = get_assets_root_path()
    if root is None:
        raise RuntimeError(
            "Isaac Sim 5.1 assets are unavailable. Configure the asset root first."
        )
    tutorial_world = World(stage_units_in_meters=1.0)
    await tutorial_world.initialize_simulation_context_async()
    tutorial_world.scene.add_default_ground_plane()
    UsdLux.DistantLight.Define(
        omni.usd.get_context().get_stage(), "/World/Light"
    ).CreateIntensityAttr(1500)
    add_reference_to_stage(
        root + "/Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd", "/World/Arm"
    )
    arm_handle = tutorial_world.scene.add(Articulation("/World/Arm", name="arm"))
    await tutorial_world.reset_async()
    inspect_robot()
    print(
        "Ready. Use move_robot(), start_logging(), stop_logging() in this same Script Editor tab."
    )


def inspect_robot():
    print("DOF names:", arm_handle.dof_names)
    print("Joint count:", arm_handle.num_joints, "DOF count:", arm_handle.num_dof)
    print("DOF limits:", arm_handle.get_dof_limits())
    print("Joint positions:", arm_handle.get_joint_positions())


def move_robot():
    arm_handle.set_joint_positions(
        np.array([[-1.5, 0.0, 0.0, -1.5, 0.0, 1.5, 0.5, 0.04, 0.04]]),
        joint_names=[f"panda_joint{i}" for i in range(1, 8)]
        + ["panda_finger_joint1", "panda_finger_joint2"],
    )


def start_logging():
    if not tutorial_world.physics_callback_exists("quickstart_robot_state"):
        tutorial_world.add_physics_callback(
            "quickstart_robot_state",
            lambda dt: print(dt, arm_handle.get_joint_positions()),
        )


def stop_logging():
    if tutorial_world.physics_callback_exists("quickstart_robot_state"):
        tutorial_world.remove_physics_callback("quickstart_robot_state")


tutorial_task = asyncio.ensure_future(setup_robot())


def report_setup_result(task):
    task.result()


tutorial_task.add_done_callback(report_setup_result)
