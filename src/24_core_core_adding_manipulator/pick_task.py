"""이 폴더에 필요한 Franka pick-and-place 작업 정의."""
import numpy as np
from isaacsim.core.api.tasks import BaseTask
from isaacsim.core.api.objects import DynamicCuboid
from isaacsim.robot.manipulators.examples.franka import Franka


class LocalPickTask(BaseTask):
    def __init__(self, name="local_pick", target=None):
        super().__init__(name=name, offset=None)
        self.target = np.array(target if target is not None else [-0.3, -0.3, 0.02575])
        self.achieved = False

    def set_up_scene(self, scene):
        super().set_up_scene(scene)
        scene.add_default_ground_plane()
        self.cube = scene.add(DynamicCuboid(prim_path="/World/Cube", name="cube", size=0.0515,
            position=np.array([0.3, 0.3, 0.3]), color=np.array([0.0, 0.0, 1.0])))
        self.robot = scene.add(Franka(prim_path="/World/Franka", name="franka"))
        self._task_objects[self.cube.name] = self.cube
        self._task_objects[self.robot.name] = self.robot

    def get_params(self):
        return {"robot_name": {"value": self.robot.name, "modifiable": False},
                "cube_name": {"value": self.cube.name, "modifiable": False}}

    def get_observations(self):
        return {self.cube.name: {"position": self.cube.get_world_pose()[0], "target_position": self.target},
                self.robot.name: {"joint_positions": self.robot.get_joint_positions()}}

    def pre_step(self, control_index, simulation_time):
        error = np.linalg.norm(self.cube.get_world_pose()[0] - self.target)
        if not self.achieved and error < 0.03:
            self.cube.get_applied_visual_material().set_color(np.array([0.0, 1.0, 0.0]))
            self.achieved = True

    def post_reset(self):
        self.robot.gripper.set_joint_positions(self.robot.gripper.joint_opened_positions)
        self.cube.get_applied_visual_material().set_color(np.array([0.0, 0.0, 1.0]))
        self.achieved = False
