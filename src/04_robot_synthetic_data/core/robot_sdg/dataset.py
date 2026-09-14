"""Scene/annotator/writer의 수명을 공유하고, step 실행은 호출자에게 맡긴다."""

import json
from pathlib import Path

import numpy as np
import omni.replicator.core as rep
from isaacsim.core.api.objects import FixedCuboid
from isaacsim.core.utils.rotations import euler_angles_to_quat
from isaacsim.core.utils.semantics import add_labels
from isaacsim.sensors.camera import Camera
from pxr import Gf, UsdLux

from .randomization import EpisodeParameters, sample_episode
from .robot import create_robot


class DatasetScene:
    def __init__(
        self,
        world,
        seed: int = 7,
        resolution: tuple[int, int] = (320, 240),
        assets_root: str | None = None,
    ):
        self.world = world
        self.seed = seed
        self.writer = None
        self.stream = None
        self.episode_parameters: EpisodeParameters | None = None
        self.frames_written = 0
        self.root = "/World/LearningSDG"
        if world.stage.GetPrimAtPath(self.root).IsValid():
            raise RuntimeError(
                "LearningSDG scene이 이미 있습니다. 새 Stage에서 시작하세요."
            )
        world.scene.add_default_ground_plane()
        self.robot, chassis, self.drive = create_robot(
            world, self.root + "/Robot", assets_root
        )
        add_labels(
            world.stage.GetPrimAtPath(self.root + "/Robot"),
            labels=["mobile_robot"],
            instance_name="class",
        )
        self.camera = Camera(
            prim_path=chassis + "/DatasetCamera",
            name="sdg_camera",
            resolution=resolution,
            translation=np.array([0.08, 0.0, 0.25]),
        )
        self.camera.set_local_pose(
            translation=np.array([0.08, 0.0, 0.25]),
            orientation=np.array([1.0, 0.0, 0.0, 0.0]),
            camera_axes="world",
        )
        self.camera.set_clipping_range(near_distance=0.01, far_distance=20.0)
        self.boxes = []
        for index in range(6):
            box = world.scene.add(
                FixedCuboid(
                    prim_path=f"{self.root}/Box_{index}",
                    name=f"sdg_box_{index}",
                    size=0.3,
                    position=np.array([1.0, 0.5 * (index + 1), 0.15]),
                    color=np.array([0.5, 0.3, 0.1]),
                )
            )
            add_labels(box.prim, labels=["box"], instance_name="class")
            self.boxes.append(box)
        self.light = UsdLux.DomeLight.Define(world.stage, self.root + "/Light")
        self.light.CreateIntensityAttr(1000.0)
        rep.orchestrator.set_capture_on_play(False)
        rep.set_global_seed(seed)

    def initialize_camera(self) -> None:
        # RGB는 BasicWriter만 소유해야 writer detach가 Camera의 별도 RGB reader를 끊지 않는다.
        self.camera.initialize(attach_rgb_annotator=False)

    def randomize(self, episode: int) -> EpisodeParameters:
        params = sample_episode(self.seed, episode, len(self.boxes))
        self.robot.set_world_pose(
            position=np.array([*params["robot_xy"], 0.05]),
            orientation=euler_angles_to_quat(np.array([0.0, 0.0, params["robot_yaw"]])),
        )
        self.robot.set_linear_velocity(np.zeros(3))
        self.robot.set_angular_velocity(np.zeros(3))
        self.robot.set_joint_velocities(np.zeros(self.robot.num_dof))
        for box, setting in zip(self.boxes, params["objects"]):
            box.set_world_pose(position=np.array(setting["position"]))
            box.get_applied_visual_material().set_color(np.array(setting["color"]))
        self.light.GetIntensityAttr().Set(params["light_intensity"])
        self.light.CreateColorAttr().Set(Gf.Vec3f(*params["light_color"]))
        self.camera.set_local_pose(
            translation=np.array([0.08, 0.0, params["camera_height"]]),
            orientation=euler_angles_to_quat(
                np.array([0.0, params["camera_pitch"], 0.0])
            ),
            camera_axes="world",
        )
        # 5.1 camera_ros.py 공식 예제와 같이 mm 값을 API 입력으로 변환한다.
        self.camera.set_focal_length(params["focal_length_mm"] / 10.0)
        self.episode_parameters = params
        return params

    def drive_forward(self) -> None:
        self.robot.apply_wheel_actions(self.drive.forward(command=[0.15, 0.0]))

    def attach_writer(self, output: Path) -> None:
        if self.writer is not None:
            raise RuntimeError("Writer가 이미 연결되어 있습니다.")
        output.mkdir(parents=True, exist_ok=False)
        self.stream = (output / "metadata.jsonl").open("w", encoding="utf-8")
        self.writer = rep.writers.get("BasicWriter")
        self.writer.initialize(
            output_dir=str(output),
            rgb=True,
            distance_to_image_plane=True,
            semantic_segmentation=True,
            bounding_box_2d_tight=True,
            colorize_semantic_segmentation=False,
        )
        self.writer.attach([self.camera.get_render_product_path()])

    def record_metadata(self, episode: int, frame: int) -> None:
        if self.stream is None:
            raise RuntimeError("먼저 writer를 연결하세요.")
        position, orientation = self.robot.get_world_pose()
        camera_position, camera_orientation = self.camera.get_world_pose(
            camera_axes="ros"
        )
        self.stream.write(
            json.dumps(
                {
                    "capture_index": self.frames_written,
                    "episode": episode,
                    "frame": frame,
                    "sim_time_s": self.world.current_time,
                    "robot_position_m": position.tolist(),
                    "robot_orientation_wxyz": orientation.tolist(),
                    "camera_position_m": camera_position.tolist(),
                    "camera_orientation_wxyz": camera_orientation.tolist(),
                    "camera_intrinsics": self.camera.get_intrinsics_matrix().tolist(),
                    "randomization": self.episode_parameters,
                },
                ensure_ascii=False,
                allow_nan=False,
            )
            + "\n"
        )
        self.stream.flush()
        self.frames_written += 1

    def detach_writer(self) -> None:
        if self.writer is not None:
            self.writer.detach()
            self.writer = None
        if self.stream is not None:
            self.stream.close()
            self.stream = None
