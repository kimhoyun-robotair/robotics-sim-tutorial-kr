"""센서를 붙일 rigid body를 USD에서 확인하고 Jetbot의 바퀴를 구동한다."""

import numpy as np
from isaacsim.robot.wheeled_robots.controllers.differential_controller import (
    DifferentialController,
)
from isaacsim.robot.wheeled_robots.robots import WheeledRobot
from isaacsim.storage.native import get_assets_root_path
from pxr import Usd, UsdPhysics


def create_robot(world, path: str, assets_root: str | None = None):
    root = assets_root if assets_root is not None else get_assets_root_path()
    if root is None:
        raise RuntimeError("Isaac Sim 5.1 asset root를 찾을 수 없습니다.")
    robot = world.scene.add(
        WheeledRobot(
            prim_path=path,
            name="sdg_robot",
            wheel_dof_names=["left_wheel_joint", "right_wheel_joint"],
            create_robot=True,
            usd_path=root + "/Isaac/Robots/NVIDIA/Jetbot/jetbot.usd",
            position=np.array([-0.8, 0.0, 0.05]),
        )
    )
    bodies = [
        prim
        for prim in Usd.PrimRange(world.stage.GetPrimAtPath(path))
        if prim.HasAPI(UsdPhysics.RigidBodyAPI)
    ]
    chassis = [
        prim for prim in bodies if prim.GetName().lower() in ("chassis", "base_link")
    ]
    if len(chassis) != 1:
        raise RuntimeError(
            f"Jetbot chassis를 확인하세요: {[str(p.GetPath()) for p in bodies]}"
        )
    drive = DifferentialController(
        name="sdg_drive", wheel_radius=0.03, wheel_base=0.1125
    )
    return robot, str(chassis[0].GetPath()), drive
