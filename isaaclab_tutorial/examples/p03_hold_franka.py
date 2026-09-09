"""미니 프로젝트 3: 고정된 Franka가 초기 관절 자세를 유지하는지 검사하다.

공식 FRANKA_PANDA_HIGH_PD_CFG에 맞춘 중력 비활성화 시운전이다.
실제 중력 보상, 하중 운반, 강화학습 정책의 검증을 대신하지 않는다.
Isaac Lab v3.0.0-beta2.patch1 전용이다.
"""

import argparse
import json
from pathlib import Path

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--steps", type=int, default=600, help="총 물리 스텝 수, 240 이상")
parser.add_argument("--output", type=Path, help="성공 시 검사 지표를 저장할 JSON 파일")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()
if args_cli.steps < 240:
    parser.error("--steps는 두 번의 자세 유지 검사를 위해 240 이상이어야 한다.")
app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

import torch

import isaaclab.sim as sim_utils
from isaaclab.assets import Articulation
from isaaclab_assets import FRANKA_PANDA_HIGH_PD_CFG
from isaaclab_physx.physics import PhysxCfg
from isaaclab_physx.sim.schemas import (
    PhysxArticulationRootPropertiesCfg,
    PhysxCollisionPropertiesCfg,
    PhysxRigidBodyPropertiesCfg,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> None:
    sim = sim_utils.SimulationContext(
        sim_utils.SimulationCfg(dt=1.0 / 120.0, device=args_cli.device, physics=PhysxCfg())
    )
    sim.set_camera_view(eye=[2.2, 2.2, 1.8], target=[0.0, 0.0, 0.5])
    ground = sim_utils.CuboidCfg(
        size=(6.0, 6.0, 0.1),
        collision_props=PhysxCollisionPropertiesCfg(),
        visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.45, 0.45, 0.45)),
    )
    ground.func("/World/Ground", ground, translation=(0.0, 0.0, -0.05))
    light = sim_utils.DomeLightCfg(intensity=2000.0)
    light.func("/World/Light", light)
    robot_cfg = FRANKA_PANDA_HIGH_PD_CFG.replace(prim_path="/World/Franka")
    # 공식 초기 자세와 actuator 설정을 유지하고 backend 속성 타입을 명시하다.
    robot_cfg.spawn.rigid_props = PhysxRigidBodyPropertiesCfg(
        disable_gravity=True, max_depenetration_velocity=1.0
    )
    robot_cfg.spawn.articulation_props = PhysxArticulationRootPropertiesCfg(
        fix_root_link=True,
        enabled_self_collisions=True,
        solver_position_iteration_count=8,
        solver_velocity_iteration_count=2,
    )
    robot_cfg.init_state.rot = (0.0, 0.0, 0.0, 1.0)
    robot = Articulation(robot_cfg)
    sim.reset()
    require(robot.is_fixed_base, "Franka의 root가 고정되지 않다. USD와 fix_root_link를 확인하다.")
    dt = sim.get_physics_dt()
    q_target = robot.data.default_joint_pos.torch.clone()
    qd_zero = torch.zeros_like(robot.data.default_joint_vel.torch)
    arm_ids, arm_names = robot.find_joints("panda_joint[1-7]")
    finger_ids, finger_names = robot.find_joints("panda_finger_joint.*")
    require(len(arm_ids) == 7 and len(finger_ids) == 2, "팔 7개와 손가락 2개 관절 이름을 확인하다.")
    reset_at = args_cli.steps // 2
    max_arm_error = 0.0
    max_finger_error = 0.0
    max_arm_speed = 0.0
    max_finger_speed = 0.0
    max_root_drift = 0.0
    baseline_root = robot.data.root_pos_w.torch.clone()
    print(f"[INFO] joints={robot.joint_names}")
    print("[INFO] fixed_base=True, gravity_on_robot=False, quaternion=xyzw")
    print(f"[INFO] arm={arm_names}, fingers={finger_names}, velocity_warmup_steps=60")
    for step in range(args_cli.steps):
        require(simulation_app.is_running(), "검사 도중 앱이 닫혀 전체 검사를 완료하지 못하다.")
        if step in {0, reset_at}:
            robot.write_joint_position_to_sim_index(position=q_target.clone())
            robot.write_joint_velocity_to_sim_index(velocity=qd_zero.clone())
            robot.reset()
            print(f"[RESET] step={step}")
        robot.set_joint_position_target_index(target=q_target)
        robot.set_joint_velocity_target_index(target=qd_zero)
        robot.write_data_to_sim()
        sim.step()
        robot.update(dt)
        q = robot.data.joint_pos.torch
        qd = robot.data.joint_vel.torch
        root_pose = robot.data.root_pose_w.torch
        require(bool(torch.isfinite(q).all()), "관절 위치에 NaN 또는 inf가 있다.")
        require(bool(torch.isfinite(qd).all()), "관절 속도에 NaN 또는 inf가 있다.")
        require(bool(torch.isfinite(root_pose).all()), "root 자세에 NaN 또는 inf가 있다.")
        arm_error = float(torch.max(torch.abs(q[:, arm_ids] - q_target[:, arm_ids])))
        finger_error = float(torch.max(torch.abs(q[:, finger_ids] - q_target[:, finger_ids])))
        max_arm_error = max(max_arm_error, arm_error)
        max_finger_error = max(max_finger_error, finger_error)
        require(arm_error < 0.05, f"팔의 초기 자세 오차가 크다: {arm_error:.6f} rad")
        require(finger_error < 0.005, f"손가락의 초기 위치 오차가 크다: {finger_error:.6f} m")
        phase_step = step if step < reset_at else step - reset_at
        # 각 reset 뒤 60스텝은 준비 구간이다. 아래 값은 이 실습의 시운전 기준이며
        # GPU에서 측정해 보정한 안정성 인증 기준은 아니다.
        if phase_step >= 60:
            arm_speed = float(torch.max(torch.abs(qd[:, arm_ids])))
            finger_speed = float(torch.max(torch.abs(qd[:, finger_ids])))
            max_arm_speed = max(max_arm_speed, arm_speed)
            max_finger_speed = max(max_finger_speed, finger_speed)
            require(arm_speed < 0.5, f"정지 목표에서 팔이 계속 움직이다: {arm_speed:.6f} rad/s")
            require(finger_speed < 0.05, f"정지 목표에서 손가락이 계속 움직이다: {finger_speed:.6f} m/s")
        root_drift = float(torch.max(torch.abs(robot.data.root_pos_w.torch - baseline_root)))
        max_root_drift = max(max_root_drift, root_drift)
        require(root_drift < 0.005, f"고정 root가 이동하다: {root_drift:.6f} m")
        if (step + 1) % 120 == 0:
            print(f"[HOLD] step={step + 1} arm_error_rad={arm_error:.6f} "
                  f"finger_error_m={finger_error:.6f} root_drift_m={root_drift:.6f}")
    if args_cli.output is not None:
        args_cli.output.parent.mkdir(parents=True, exist_ok=True)
        args_cli.output.write_text(
            json.dumps({"project": "p03", "status": "PASS", "steps": args_cli.steps,
                        "max_arm_error_rad": max_arm_error, "max_finger_error_m": max_finger_error,
                        "max_arm_speed_after_warmup_rad_s": max_arm_speed,
                        "max_finger_speed_after_warmup_m_s": max_finger_speed,
                        "max_root_drift_m": max_root_drift, "velocity_warmup_steps": 60,
                        "gravity_on_robot": False, "fixed_base": True},
                       ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    print(f"[PASS] p03 Franka hold: steps={args_cli.steps}, arm_error_rad={max_arm_error:.6f}, "
          f"finger_error_m={max_finger_error:.6f}")


if __name__ == "__main__":
    try:
        main()
    finally:
        simulation_app.close()
