"""미니 프로젝트 2: PhysX에서 상자의 낙하, 정착, 초기화를 검사하다.

Isaac Lab v3.0.0-beta2.patch1 전용. GPU 실측 결과는 실행 후에만 얻을 수 있다.
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
    parser.error("--steps는 두 번의 낙하와 정착을 위해 240 이상이어야 한다.")
app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

# AppLauncher가 Kit와 확장을 준비한 다음 시뮬레이션 모듈을 가져오다.
import torch

import isaaclab.sim as sim_utils
from isaaclab.assets import RigidObject, RigidObjectCfg
from isaaclab_physx.physics import PhysxCfg
from isaaclab_physx.sim.schemas import PhysxCollisionPropertiesCfg, PhysxRigidBodyPropertiesCfg
from isaaclab_physx.sim.spawners.materials import PhysxRigidBodyMaterialCfg


def require(condition: bool, message: str) -> None:
    """python -O에서도 생략되지 않는 실행 중 검사이다."""
    if not condition:
        raise RuntimeError(message)


def main() -> None:
    sim = sim_utils.SimulationContext(
        sim_utils.SimulationCfg(dt=1.0 / 120.0, device=args_cli.device, physics=PhysxCfg())
    )
    sim.set_camera_view(eye=[1.6, 1.6, 1.2], target=[0.0, 0.0, 0.15])
    material = PhysxRigidBodyMaterialCfg(static_friction=0.8, dynamic_friction=0.6, restitution=0.0)
    # 외부 ground USD를 내려받지 않는 정적 충돌 상자이다. 윗면은 z=0이다.
    ground = sim_utils.CuboidCfg(
        size=(6.0, 6.0, 0.1),
        collision_props=PhysxCollisionPropertiesCfg(),
        physics_material=material,
        visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.45, 0.45, 0.45)),
    )
    ground.func("/World/Ground", ground, translation=(0.0, 0.0, -0.05))
    light = sim_utils.DomeLightCfg(intensity=2000.0)
    light.func("/World/Light", light)
    cfg = RigidObjectCfg(
        prim_path="/World/Box",
        spawn=sim_utils.CuboidCfg(
            size=(0.2, 0.2, 0.2),
            rigid_props=PhysxRigidBodyPropertiesCfg(
                disable_gravity=False,
                linear_damping=0.05,
                angular_damping=0.05,
                max_depenetration_velocity=1.0,
                solver_position_iteration_count=8,
                solver_velocity_iteration_count=2,
            ),
            collision_props=PhysxCollisionPropertiesCfg(contact_offset=0.002, rest_offset=0.0),
            mass_props=sim_utils.MassPropertiesCfg(mass=1.0),
            physics_material=material,
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.15, 0.6, 0.3)),
        ),
        init_state=RigidObjectCfg.InitialStateCfg(pos=(0.0, 0.0, 0.5), rot=(0.0, 0.0, 0.0, 1.0)),
    )
    box = RigidObject(cfg)
    sim.reset()
    dt = sim.get_physics_dt()
    reset_at = args_cli.steps // 2
    resets = {0, reset_at}
    completed = 0
    settled = []
    window_height_error = 0.0
    window_linear_speed = 0.0
    window_angular_speed = 0.0
    for step in range(args_cli.steps):
        require(simulation_app.is_running(), "검사 도중 앱이 닫혀 전체 검사를 완료하지 못하다.")
        if step in resets:
            window_height_error = 0.0
            window_linear_speed = 0.0
            window_angular_speed = 0.0
            pose = box.data.default_root_pose.torch.clone()
            velocity = torch.zeros_like(box.data.default_root_vel.torch)
            box.write_root_pose_to_sim_index(root_pose=pose)
            box.write_root_velocity_to_sim_index(root_velocity=velocity)
            box.reset()
            print(f"[RESET] step={step}")
        box.write_data_to_sim()
        sim.step()
        box.update(dt)
        pose = box.data.root_pose_w.torch
        velocity = box.data.root_vel_w.torch
        require(bool(torch.isfinite(pose).all()), "상자 자세에 NaN 또는 inf가 있다.")
        require(bool(torch.isfinite(velocity).all()), "상자 속도에 NaN 또는 inf가 있다.")
        z = float(pose[0, 2])
        require(0.07 < z < 0.65, f"상자 높이가 허용 범위를 벗어나다: z={z:.6f}")
        quat_norm = torch.linalg.vector_norm(pose[:, 3:7], dim=-1)
        require(bool(torch.all(torch.abs(quat_norm - 1.0) < 0.01)), "단위 quaternion이 아니다.")
        phase_end = reset_at if step < reset_at else args_cli.steps
        # 두 낙하 구간 각각의 마지막 30스텝 전체를 검사하다.
        if step >= phase_end - 30:
            speed = float(torch.linalg.vector_norm(velocity[0, :3]))
            angular_speed = float(torch.linalg.vector_norm(velocity[0, 3:6]))
            window_height_error = max(window_height_error, abs(z - 0.1))
            window_linear_speed = max(window_linear_speed, speed)
            window_angular_speed = max(window_angular_speed, angular_speed)
            require(abs(z - 0.1) < 0.015, f"정착 높이를 확인하다: z={z:.6f}")
            require(speed < 0.1, f"상자가 정착하지 않다: speed={speed:.6f}")
            require(angular_speed < 0.2, f"상자가 계속 회전하다: angular_speed={angular_speed:.6f}")
        if step in {reset_at - 1, args_cli.steps - 1}:
            settled.append({"step": step + 1, "height_m": z, "window_steps": 30,
                            "max_height_error_m": window_height_error,
                            "max_linear_speed_m_s": window_linear_speed,
                            "max_angular_speed_rad_s": window_angular_speed})
            print(f"[SETTLED] step={step + 1} z={z:.6f} "
                  f"window_max_speed={window_linear_speed:.6f} "
                  f"window_max_angular_speed={window_angular_speed:.6f}")
        completed += 1
    require(completed == args_cli.steps, "실행한 스텝 수가 요청과 다르다.")
    if args_cli.output is not None:
        args_cli.output.parent.mkdir(parents=True, exist_ok=True)
        args_cli.output.write_text(
            json.dumps({"project": "p02", "status": "PASS", "steps": completed, "dt": dt,
                        "settled": settled}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    print(f"[PASS] p02 stable rigid: steps={completed}, resets=2, dt={dt}")


if __name__ == "__main__":
    try:
        main()
    finally:
        simulation_app.close()
