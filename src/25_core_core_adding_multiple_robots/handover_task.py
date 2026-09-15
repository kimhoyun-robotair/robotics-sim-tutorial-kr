"""Jetbot 운반 → 후퇴 → Franka 집기 상태를 소유하는 독립 Task."""
import numpy as np
from isaacsim.core.api.tasks import BaseTask
from isaacsim.core.utils.prims import is_prim_path_valid
from isaacsim.core.utils.string import find_unique_string_name
from isaacsim.robot.manipulators.examples.franka.tasks import PickPlace
from isaacsim.robot.wheeled_robots.robots import WheeledRobot


class HandoverTask(BaseTask):
    def __init__(self, name, jetbot_asset, offset=None, goal_x=1.3, retreat_steps=200):
        super().__init__(name=name, offset=offset)
        self.jetbot_asset = jetbot_asset
        self.goal = np.array([goal_x, 0.3, 0.0]) + self._offset
        self.retreat_steps = retreat_steps
        self.event = 0
        self.arrival_step = None
        self.pick = PickPlace(name=name + "_pick", cube_initial_position=np.array([0.1, 0.3, 0.05]),
                              target_position=np.array([0.7, -0.3, 0.02575]), offset=self._offset)

    def set_up_scene(self, scene):
        super().set_up_scene(scene)
        self.pick.set_up_scene(scene)
        robot_name = find_unique_string_name("jetbot", is_unique_fn=lambda value: not scene.object_exists(value))
        robot_path = find_unique_string_name("/World/Jetbot", is_unique_fn=lambda value: not is_prim_path_valid(value))
        self.jetbot = scene.add(WheeledRobot(prim_path=robot_path, name=robot_name,
            wheel_dof_names=["left_wheel_joint", "right_wheel_joint"], create_robot=True,
            usd_path=self.jetbot_asset, position=np.array([0.0, 0.3, 0.0])))
        self._task_objects[self.jetbot.name] = self.jetbot
        params = self.pick.get_params()
        self.franka = scene.get_object(params["robot_name"]["value"])
        position, _ = self.franka.get_world_pose()
        self.franka.set_world_pose(position=position + np.array([1.0, 0.0, 0.0]))
        self.franka.set_default_state(position=position + np.array([1.0, 0.0, 0.0]))
        self.cube = scene.get_object(params["cube_name"]["value"])
        # PickPlace가 자기 물체에 offset을 적용했다. 여기서는 Jetbot에만 한 번 적용한다.
        self._move_task_objects_to_their_frame()

    def get_params(self):
        params = self.pick.get_params()
        params["jetbot_name"] = {"value": self.jetbot.name, "modifiable": False}
        return params

    def get_observations(self):
        position, orientation = self.jetbot.get_world_pose()
        observations = {self.name + "_event": self.event,
                        self.jetbot.name: {"position": position, "orientation": orientation, "goal_position": self.goal}}
        observations.update(self.pick.get_observations())
        return observations

    def pre_step(self, control_index, simulation_time):
        if self.event == 0 and np.linalg.norm(self.jetbot.get_world_pose()[0][:2] - self.goal[:2]) < 0.04:
            self.event = 1
            self.arrival_step = control_index
            print(self.name, "event=1 RETREAT", "time_s=", simulation_time)
        elif self.event == 1 and control_index - self.arrival_step >= self.retreat_steps:
            self.event = 2
            print(self.name, "event=2 PICK", "time_s=", simulation_time)

    def post_reset(self):
        self.pick.post_reset()
        self.event = 0
        self.arrival_step = None
