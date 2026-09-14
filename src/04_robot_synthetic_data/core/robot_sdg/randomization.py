"""Episode 번호와 seed만으로 재현할 수 있는 scene parameter 샘플링."""

import random
from typing import TypedDict


class ObjectParameters(TypedDict):
    position: list[float]
    color: list[float]


class EpisodeParameters(TypedDict):
    episode: int
    seed: int
    robot_xy: list[float]
    robot_yaw: float
    objects: list[ObjectParameters]
    light_intensity: float
    light_color: list[float]
    camera_height: float
    camera_pitch: float
    focal_length_mm: float


def sample_episode(seed: int, episode: int, count: int = 6) -> EpisodeParameters:
    rng = random.Random(seed + episode)
    return {
        "episode": episode,
        "seed": seed + episode,
        "robot_xy": [-0.8, rng.uniform(-0.1, 0.1)],
        "robot_yaw": rng.uniform(-0.1, 0.1),
        "objects": [
            {
                "position": [
                    rng.uniform(0.6, 2.2),
                    (-1 if i % 2 else 1) * rng.uniform(0.45, 1.3),
                    0.15,
                ],
                "color": [rng.uniform(0.15, 0.95) for _ in range(3)],
            }
            for i in range(count)
        ],
        "light_intensity": rng.uniform(500.0, 1600.0),
        "light_color": [rng.uniform(0.7, 1.0) for _ in range(3)],
        "camera_height": rng.uniform(0.22, 0.32),
        "camera_pitch": rng.uniform(0.0, 0.15),
        "focal_length_mm": rng.uniform(14.0, 22.0),
    }
