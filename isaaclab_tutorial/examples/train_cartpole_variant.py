#!/usr/bin/env python3
"""Register two comparable Cartpole tasks, then run the tagged official workflow.

Use Isaac Lab v3.0.0-beta2.patch1's Python environment.  The wrapper accepts
--variant baseline|smooth and --mode train|play; remaining flags are forwarded
to the official RSL-RL entrypoint.  No upstream source file is edited.
"""

from __future__ import annotations

import argparse
import importlib
import os
from pathlib import Path
import runpy
import sys

TASK_IDS = {
    "baseline": "Isaac-Tutorial-Cartpole-Baseline-v0",
    "smooth": "Isaac-Tutorial-Cartpole-Smooth-v0",
}


def action_change_cost(env):
    """One non-negative normalized-action change cost per parallel environment."""
    delta = env.action_manager.action - env.action_manager.prev_action
    return delta.square().sum(dim=-1)


def get_baseline_cfg():
    """Use the official manager-based Cartpole dynamics, observations and rewards."""
    from isaaclab_tasks.manager_based.classic.cartpole.cartpole_env_cfg import CartpoleEnvCfg

    return CartpoleEnvCfg()


def get_smooth_cfg():
    """Add only action-change regularization, keeping every other setting equal."""
    from isaaclab.managers import RewardTermCfg
    from isaaclab.utils.configclass import configclass
    from isaaclab_tasks.manager_based.classic.cartpole.cartpole_env_cfg import (
        CartpoleEnvCfg,
        RewardsCfg,
    )

    @configclass
    class SmoothRewardsCfg(RewardsCfg):
        action_change = RewardTermCfg(func=action_change_cost, weight=-0.002)

    cfg = CartpoleEnvCfg()
    cfg.rewards = SmoothRewardsCfg()
    return cfg


def get_agent_cfg():
    from isaaclab_tasks.manager_based.classic.cartpole.agents.rsl_rl_ppo_cfg import (
        CartpolePPORunnerCfg,
    )

    cfg = CartpolePPORunnerCfg()
    cfg.experiment_name = "tutorial_cartpole"
    return cfg


def register_tasks():
    """Register tasks in the current Python process; safe to call more than once."""
    import gymnasium as gym
    import isaaclab_tasks  # noqa: F401

    for variant, cfg_factory in (
        ("baseline", get_baseline_cfg),
        ("smooth", get_smooth_cfg),
    ):
        task_id = TASK_IDS[variant]
        if task_id in gym.registry:
            existing = gym.spec(task_id).kwargs["env_cfg_entry_point"]
            if existing is not cfg_factory:
                raise RuntimeError(f"Task ID already registered by another module: {task_id}")
            continue
        gym.register(
            id=task_id,
            entry_point="isaaclab.envs:ManagerBasedRLEnv",
            disable_env_checker=True,
            kwargs={
                "env_cfg_entry_point": cfg_factory,
                "rsl_rl_cfg_entry_point": get_agent_cfg,
            },
        )
    return dict(TASK_IDS)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--variant", choices=TASK_IDS, required=True)
    parser.add_argument("--mode", choices=("train", "play"), default="train")
    parser.add_argument(
        "--isaaclab-root",
        type=Path,
        default=Path(os.environ.get("ISAACLAB_ROOT", str(Path.home() / "IsaacLab"))),
    )
    args, forwarded = parser.parse_known_args(argv)
    if any(token.split("=", 1)[0] in {"--task", "--rl_library"} for token in forwarded):
        parser.error("--variant selects the task; this example uses --rl_library rsl_rl.")
    workflow = args.isaaclab_root.expanduser().resolve() / "scripts" / "reinforcement_learning" / f"{args.mode}.py"
    if not workflow.is_file():
        parser.error(f"Official workflow does not exist: {workflow}")

    # Import under a stable module name so saved YAML reward references can be
    # resolved later; registering in a subprocess would lose the Gym registry.
    module = importlib.import_module("train_cartpole_variant")
    module.register_tasks()
    original_argv = sys.argv
    original_path = list(sys.path)
    try:
        sys.path.insert(0, str(workflow.parent))
        sys.argv = [
            str(workflow),
            "--rl_library", "rsl_rl",
            "--task", TASK_IDS[args.variant],
            *forwarded,
        ]
        runpy.run_path(str(workflow), run_name="__main__")
    finally:
        sys.argv = original_argv
        sys.path[:] = original_path


if __name__ == "__main__":
    main()
