"""Standalone Python: Cloner로 복제한 Spot에서 NVIDIA의 학습된 policy를 평가한다."""

import argparse
import csv
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tutorial_common.runtime import (
    add_common_arguments,
    close_app,
    launch_app,
    output_directory,
    positive_float,
    positive_int,
    write_json,
)
from metrics import episode_success, upright


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_arguments(parser)
    parser.add_argument("--num-envs", type=positive_int, default=4)
    parser.add_argument("--steps", type=positive_int, default=2500)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--speed", type=positive_float, default=0.3)
    parser.add_argument(
        "--render-every",
        type=positive_int,
        default=10,
        help="GUI rendering 간격 (physics steps)",
    )
    parser.add_argument("--log-every", type=positive_int, default=25)
    args = parser.parse_args()
    if args.speed * args.steps / 500 > 4:
        parser.error(
            "이번 flat tile은 10m입니다. speed * steps / 500을 4m 이하로 설정하세요."
        )
    output = output_directory("05_policy", args.output)
    app = launch_app(args.headless)
    try:
        import numpy as np
        from isaacsim.core.api import World
        from isaacsim.core.api.materials import PhysicsMaterial
        from isaacsim.core.api.objects import FixedCuboid
        from isaacsim.core.cloner import GridCloner
        from isaacsim.robot.policy.examples.robots import SpotFlatTerrainPolicy
        from pxr import UsdGeom

        # 정책과 함께 배포된 Spot 예제의 physics_dt를 그대로 사용한다.
        dt = 1 / 500
        world = World(stage_units_in_meters=1.0, physics_dt=dt, rendering_dt=dt)
        cloner = GridCloner(spacing=12.0)
        cloner.define_base_env("/World/envs")
        UsdGeom.Xform.Define(world.stage, "/World/envs/env_0")
        FixedCuboid(
            prim_path="/World/envs/env_0/Floor",
            name="source_floor",
            size=1.0,
            scale=np.array([10.0, 10.0, 0.2]),
            position=np.array([0.0, 0.0, -0.1]),
        )
        first = SpotFlatTerrainPolicy(
            prim_path="/World/envs/env_0/Robot",
            name="spot_0",
            position=np.array([0.0, 0.0, 0.8]),
        )
        paths = cloner.generate_paths("/World/envs/env", args.num_envs)
        offsets = cloner.clone(
            source_prim_path=paths[0],
            prim_paths=paths,
            copy_from_source=True,
            replicate_physics=False,
        )
        cloner.filter_collisions(
            world.get_physics_context().prim_path,
            "/World/collisionGroups",
            paths,
            [],
        )
        policies = [first]
        for index, path in enumerate(paths[1:], start=1):
            policies.append(
                SpotFlatTerrainPolicy(prim_path=path + "/Robot", name=f"spot_{index}")
            )
        rng = random.Random(args.seed)
        frictions = []
        for index, path in enumerate(paths):
            friction = rng.uniform(0.3, 1.2)
            frictions.append(friction)
            material = PhysicsMaterial(
                prim_path=f"/World/Materials/Floor_{index}",
                static_friction=friction,
                dynamic_friction=friction,
                restitution=0.0,
            )
            FixedCuboid(
                prim_path=path + "/Floor", name=f"floor_{index}"
            ).apply_physics_material(material)
        world.reset()
        for policy in policies:
            policy.initialize()
            policy.robot.set_joint_positions(np.array(policy.default_pos))
        for _ in range(250):
            for policy in policies:
                policy.forward(dt, np.zeros(3))
            world.step(render=False)

        starts = [policy.robot.get_world_pose()[0].copy() for policy in policies]
        fallen = [False] * args.num_envs
        command = np.array([args.speed, 0.0, 0.0])
        inference_s = physics_s = logging_s = 0.0
        samples = 0
        begin = time.perf_counter()
        with (output / "trajectory.csv").open(
            "w", newline="", encoding="utf-8"
        ) as stream:
            log = csv.writer(stream)
            log.writerow(
                [
                    "step",
                    "time_s",
                    "env",
                    "friction",
                    "local_x_m",
                    "local_y_m",
                    "z_m",
                    "vx_m_s",
                    "vy_m_s",
                    "upright_cos",
                    "fell",
                ]
            )
            for step in range(args.steps):
                if not app.is_running() or not world.is_playing():
                    break
                timer = time.perf_counter()
                for policy in policies:
                    policy.forward(dt, command)
                inference_s += time.perf_counter() - timer
                timer = time.perf_counter()
                world.step(render=not args.headless and step % args.render_every == 0)
                physics_s += time.perf_counter() - timer
                timer = time.perf_counter()
                for index, policy in enumerate(policies):
                    position, rotation = policy.robot.get_world_pose()
                    velocity = policy.robot.get_linear_velocity()
                    if (
                        not np.isfinite(position).all()
                        or not np.isfinite(velocity).all()
                    ):
                        raise RuntimeError(
                            f"env {index}에 NaN/Inf 상태가 발생했습니다."
                        )
                    vertical = upright(rotation)
                    fallen[index] |= bool(position[2] < 0.25 or vertical < 0.5)
                    if step % args.log_every == 0:
                        local = position - offsets[index]
                        log.writerow(
                            [
                                step,
                                (step + 1) * dt,
                                index,
                                frictions[index],
                                *local,
                                velocity[0],
                                velocity[1],
                                vertical,
                                fallen[index],
                            ]
                        )
                logging_s += time.perf_counter() - timer
                samples += 1
        elapsed_wall = time.perf_counter() - begin
        results = []
        for index, policy in enumerate(policies):
            position, _ = policy.robot.get_world_pose()
            distance = float(position[0] - starts[index][0])
            results.append(
                {
                    "env": index,
                    "friction": frictions[index],
                    "distance_x_m": distance,
                    "mean_vx_m_s": distance / (samples * dt) if samples else 0.0,
                    "fell": fallen[index],
                    "success": samples == args.steps
                    and episode_success(
                        distance, samples * dt, args.speed, fallen[index]
                    ),
                }
            )
        write_json(
            output / "summary.json",
            {
                "isaac_sim": "5.1.0",
                "policy": "NVIDIA SpotFlatTerrainPolicy",
                "seed": args.seed,
                "num_envs": args.num_envs,
                "steps": samples,
                "completed": samples == args.steps,
                "physics_dt_s": dt,
                "command_m_s": args.speed,
                "headless": args.headless,
                "render_every": args.render_every,
                "wall_time_s": elapsed_wall,
                "env_steps_per_second": samples * args.num_envs / elapsed_wall,
                "real_time_factor": samples * dt / elapsed_wall,
                "timing_s": {
                    "policy_and_control": inference_s,
                    "physics_and_render": physics_s,
                    "state_and_logging": logging_s,
                },
                "results": results,
            },
        )
        world.stop()
        print(f"Policy 평가: {output}", flush=True)
    finally:
        close_app(app)


if __name__ == "__main__":
    main()
