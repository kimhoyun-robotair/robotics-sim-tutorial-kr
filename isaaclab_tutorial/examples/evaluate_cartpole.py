#!/usr/bin/env python3
"""Evaluate tutorial RSL-RL checkpoints on one common official Cartpole task.

Run with Isaac Lab v3.0.0-beta2.patch1 and rsl-rl-lib==5.0.1. Visualizers
are omitted by default; add --viz kit for a window. This is a state-policy
evaluation, not an RGB camera/rendering acceptance test.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import inspect
import math
from pathlib import Path

from summarize_evaluations import SCHEMA, write_json_atomic

TASK = "Isaac-Cartpole-v0"


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def make_recorder_cfg():
    """Use the supported recorder callback, which runs before automatic resets."""
    from isaaclab.managers import RecorderTermCfg
    from isaaclab.managers.recorder_manager import DatasetExportMode, RecorderManagerBaseCfg, RecorderTerm
    from isaaclab.utils import configclass

    class TerminalStateRecorder(RecorderTerm):
        def __init__(self, cfg, env):
            super().__init__(cfg, env)
            self.robot = env.scene["robot"]
            self.cart_id = self.robot.find_joints("slider_to_cart")[0][0]
            self.pole_id = self.robot.find_joints("cart_to_pole")[0][0]

        def record_post_step(self):
            # Copy scalar values now: reading robot.data after env.step() would
            # read the NEXT episode's reset state at a terminal transition.
            q = self.robot.data.joint_pos.torch
            qd = self.robot.data.joint_vel.torch
            term = self._env.action_manager.get_term("joint_effort")
            angle = float(q[0, self.pole_id].item())
            self._env.tutorial_evaluation_sample = {
                "pole_angle": math.atan2(math.sin(angle), math.cos(angle)),
                "cart_position": float(q[0, self.cart_id].item()),
                "cart_velocity": float(qd[0, self.cart_id].item()),
                "pole_velocity": float(qd[0, self.pole_id].item()),
                # This is commanded slider force [N], NOT measured force.
                "command_force": float(term.processed_actions[0, 0].item()),
                "action_change": float((self._env.action_manager.action - self._env.action_manager.prev_action)[0, 0].item()),
                "terminated": bool(self._env.reset_terminated[0].item()),
                "truncated": bool(self._env.reset_time_outs[0].item()),
            }
            return None, None

    @configclass
    class EvaluationRecorderCfg(RecorderManagerBaseCfg):
        dataset_export_mode = DatasetExportMode.EXPORT_NONE
        export_in_record_pre_reset = False
        metrics = RecorderTermCfg(class_type=TerminalStateRecorder)

    return EvaluationRecorderCfg()


def run(args, report):
    import gymnasium as gym
    import torch
    from rsl_rl.runners import OnPolicyRunner

    from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper, handle_deprecated_rsl_rl_cfg
    from isaaclab_tasks.utils import launch_simulation, load_cfg_from_registry, parse_env_cfg
    import isaaclab_assets.robots.cartpole as cartpole_asset

    installed_rsl = importlib.metadata.version("rsl-rl-lib")
    if installed_rsl != "5.0.1":
        raise RuntimeError(f"This tutorial pins rsl-rl-lib==5.0.1; installed: {installed_rsl}")
    device = args.device or "cuda:0"
    env_cfg = parse_env_cfg(TASK, device=device, num_envs=1)
    env_cfg.seed = args.seed_start
    env_cfg.recorders = make_recorder_cfg()
    agent_cfg = load_cfg_from_registry(TASK, "rsl_rl_cfg_entry_point")
    agent_cfg = handle_deprecated_rsl_rl_cfg(agent_cfg, installed_rsl)
    agent_cfg.device = device
    if agent_cfg.clip_actions is not None or env_cfg.actions.joint_effort.scale != 100.0:
        raise RuntimeError("Official Cartpole action settings changed; review evaluation protocol.")
    # These flags stabilize neural-network inference; PhysX results across
    # GPU/driver versions are still not guaranteed to be bitwise identical.
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True

    with launch_simulation(env_cfg, args):
        env = gym.make(TASK, cfg=env_cfg)
        try:
            wrapped = RslRlVecEnvWrapper(env, clip_actions=agent_cfg.clip_actions)
            base = env.unwrapped
            agent_cfg.device = base.device
            runner = OnPolicyRunner(wrapped, agent_cfg.to_dict(), log_dir=None, device=base.device)
            runner.load(str(args.checkpoint))
            # The public API uses deterministic inference and restores the
            # checkpoint's observation normalization. Do not call actor directly.
            policy = runner.get_inference_policy(device=base.device)
            robot = base.scene["robot"]
            cart_id = robot.find_joints("slider_to_cart")[0][0]
            pole_id = robot.find_joints("cart_to_pole")[0][0]
            report["protocol"] = {
                "task": TASK, "isaaclab_tag": "v3.0.0-beta2.patch1",
                "isaaclab_version": importlib.metadata.version("isaaclab"),
                "rsl_rl_version": installed_rsl, "torch_version": torch.__version__,
                "torch_cuda_version": torch.version.cuda,
                "task_config_sha256": sha256_file(inspect.getfile(type(env_cfg))),
                "robot_asset_config_sha256": sha256_file(inspect.getfile(cartpole_asset)),
                "evaluator_sha256": sha256_file(__file__), "physics": "physx",
                "num_envs": 1, "device": str(base.device),
                "gpu": torch.cuda.get_device_name(base.device) if str(base.device).startswith("cuda") else None,
                "physics_dt_s": env_cfg.sim.dt, "decimation": env_cfg.decimation,
                "horizon_s": env_cfg.episode_length_s, "max_steps": base.max_episode_length,
                "action_scale_n": 100.0, "clip_actions": None,
                "pole_angle": "wrapped [-pi, pi]; measured after each control step before reset",
                "control_effort": "RMS commanded slider force [N]; not measured force or energy",
                "cart_travel": "sum of absolute control-step position differences [m], starting at reset position",
                "action_change": "normalized action difference; first step includes change from reset action zero",
                "metric_weighting": "equal weight per episode; failed short episodes retained",
                "termination": "cart outside [-3,3] m; pole angle is not a termination condition",
                "success_definition": "none; timeout only means the cart stayed within bounds for the horizon",
            }
            reset_mask = torch.ones(1, device=base.device, dtype=torch.long)
            with torch.inference_mode():
                for index in range(args.episodes):
                    seed = args.seed_start + index
                    base.reset(seed=seed)
                    policy.reset(reset_mask)
                    obs = wrapped.get_observations()
                    initial = {
                        "cart_position_m": float(robot.data.joint_pos.torch[0, cart_id].item()),
                        "pole_angle_rad": float(robot.data.joint_pos.torch[0, pole_id].item()),
                        "cart_velocity_m_s": float(robot.data.joint_vel.torch[0, cart_id].item()),
                        "pole_velocity_rad_s": float(robot.data.joint_vel.torch[0, pole_id].item()),
                    }
                    if not all(math.isfinite(value) for value in initial.values()):
                        raise FloatingPointError(f"Non-finite reset state, seed={seed}")
                    previous_cart = initial["cart_position_m"]
                    sums = dict(pole_angle=0.0, cart_position=0.0, command_force=0.0, action_change=0.0)
                    travel = 0.0
                    for step in range(1, base.max_episode_length + 2):
                        if not bool(torch.isfinite(obs["policy"]).all().item()):
                            raise FloatingPointError(f"Non-finite observation, seed={seed}, step={step}")
                        actions = policy(obs)
                        if tuple(actions.shape) != (1, 1) or not bool(torch.isfinite(actions).all().item()):
                            raise FloatingPointError(f"Invalid policy action, seed={seed}, step={step}")
                        base.tutorial_evaluation_sample = None
                        obs, _, dones, _ = wrapped.step(actions)
                        sample = base.tutorial_evaluation_sample
                        if sample is None:
                            raise RuntimeError("Post-step recorder did not run; refusing incomplete metrics.")
                        if not all(math.isfinite(value) for value in sample.values()):
                            raise FloatingPointError(f"Non-finite transition, seed={seed}, step={step}")
                        for key in sums:
                            sums[key] += sample[key] ** 2
                        travel += abs(sample["cart_position"] - previous_cart)
                        previous_cart = sample["cart_position"]
                        done = sample["terminated"] or sample["truncated"]
                        if bool(dones[0].item()) != done:
                            raise RuntimeError("Wrapper boundary flags disagree with the recorder.")
                        if done:
                            episode = {
                                "seed": seed, "steps": step, "initial_state": initial,
                                "duration_s": step * base.step_dt,
                                "terminated": sample["terminated"], "truncated": sample["truncated"],
                                "pole_angle_rms_rad": math.sqrt(sums["pole_angle"] / step),
                                "cart_position_rms_m": math.sqrt(sums["cart_position"] / step),
                                "cart_travel_m": travel,
                                "command_force_rms_n": math.sqrt(sums["command_force"] / step),
                                "action_change_rms": math.sqrt(sums["action_change"] / step),
                            }
                            report["episodes"].append(episode)
                            print(f"seed={seed} steps={step} terminated={episode['terminated']} truncated={episode['truncated']}")
                            break
                    else:
                        raise RuntimeError(f"No episode boundary by horizon, seed={seed}")
        finally:
            env.close()


def main():
    # This tag supports importing task configuration before launch_simulation.
    import isaaclab_tasks  # noqa: F401
    from isaaclab_tasks.utils import add_launcher_args

    parser = argparse.ArgumentParser(description=__doc__)
    # This tag's AppLauncher performs an early parse_known_args(). Add its
    # options before required evaluation options so --help remains usable.
    add_launcher_args(parser)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--episodes", type=int, default=20)
    parser.add_argument("--seed_start", type=int, default=1000)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.checkpoint = args.checkpoint.expanduser().resolve()
    args.output = args.output.expanduser().resolve()
    if not args.checkpoint.is_file() or args.output == args.checkpoint:
        parser.error("Provide an existing trusted checkpoint and a different output path.")
    if args.episodes <= 0 or args.seed_start < 0 or args.seed_start + args.episodes > 2**31:
        parser.error("Use a positive episode count and seeds in [0, 2**31).")
    if args.output.exists():
        parser.error("Output already exists; choose a new path to preserve prior measurements.")
    report = {
        "schema": SCHEMA, "status": "running", "label": args.label,
        "checkpoint": str(args.checkpoint), "checkpoint_sha256": sha256_file(args.checkpoint),
        "requested_episodes": args.episodes, "episodes": [],
    }
    try:
        run(args, report)
    except BaseException as error:
        report["status"] = "failed"
        report["error"] = f"{type(error).__name__}: {error}"
        write_json_atomic(args.output, report)
        raise
    report["status"] = "complete"
    write_json_atomic(args.output, report)
    print(f"Complete evaluation: {args.output}")


if __name__ == "__main__":
    main()
