#!/usr/bin/env python3
"""프로젝트 1: 외부 USD 없이 조명, 바닥, 기본 도형을 만드는 첫 Isaac Lab 장면.

Isaac Lab v3.0.0-beta2.patch1 / Isaac Sim 6.0.1 / Python 3.12 기준.
공식 create_empty.py와 spawn_prims.py의 AppLauncher 수명 주기와 spawner API를 참고하다.
GPU 실행 결과를 대신하는 스크립트가 아니며, 화면 판정은 문서의 실습 기준을 적용하다.
"""

import argparse

from isaaclab.app import AppLauncher


def nonnegative_int(value: str) -> int:
    number = int(value)
    if number < 0:
        raise argparse.ArgumentTypeError("0 이상의 정수를 사용하다.")
    return number


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--steps", type=nonnegative_int, default=0, help="실행 스텝 수. 0이면 창을 닫을 때까지 실행하다.")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()
app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

# Kit와 연결되는 모듈은 AppLauncher가 실행된 뒤 import하다.
import omni.usd

import isaaclab.sim as sim_utils
from isaaclab.sim.schemas import CollisionBaseCfg
from isaaclab_physx.physics import PhysxCfg


def design_scene() -> None:
    """미터 단위의 고정 도형과 텍스처 없는 조명을 구성하다."""
    floor_cfg = sim_utils.CuboidCfg(
        size=(4.0, 4.0, 0.1),
        collision_props=CollisionBaseCfg(collision_enabled=True),
        visual_material=sim_utils.PreviewSurfaceCfg(
            diffuse_color=(0.35, 0.35, 0.35), roughness=0.8, metallic=0.0
        ),
    )
    floor_cfg.func("/World/Floor", floor_cfg, translation=(0.0, 0.0, -0.05))

    light_cfg = sim_utils.DomeLightCfg(intensity=1500.0, color=(1.0, 1.0, 1.0))
    light_cfg.func("/World/Light", light_cfg)

    cube_cfg = sim_utils.CuboidCfg(
        size=(0.4, 0.4, 0.4),
        visual_material=sim_utils.PreviewSurfaceCfg(
            diffuse_color=(0.15, 0.35, 0.8), roughness=0.8, metallic=0.0
        ),
    )
    cube_cfg.func("/World/Cube", cube_cfg, translation=(0.0, 0.0, 0.2))

    sphere_cfg = sim_utils.SphereCfg(
        radius=0.18,
        visual_material=sim_utils.PreviewSurfaceCfg(
            diffuse_color=(0.8, 0.2, 0.15), roughness=0.8, metallic=0.0
        ),
    )
    sphere_cfg.func("/World/Sphere", sphere_cfg, translation=(-0.7, 0.4, 0.18))

    cone_cfg = sim_utils.ConeCfg(
        radius=0.18,
        height=0.4,
        visual_material=sim_utils.PreviewSurfaceCfg(
            diffuse_color=(0.2, 0.7, 0.25), roughness=0.8, metallic=0.0
        ),
    )
    cone_cfg.func("/World/Cone", cone_cfg, translation=(0.7, 0.4, 0.2))

    stage = omni.usd.get_context().get_stage()
    for path in ("/World/Floor", "/World/Light", "/World/Cube", "/World/Sphere", "/World/Cone"):
        if not stage.GetPrimAtPath(path).IsValid():
            raise RuntimeError(f"필수 prim 생성 실패: {path}")


def main() -> None:
    sim = sim_utils.SimulationContext(
        sim_utils.SimulationCfg(dt=1.0 / 120.0, device=args_cli.device, physics=PhysxCfg())
    )
    sim.set_camera_view([2.8, 2.8, 2.2], [0.0, 0.0, 0.25])
    design_scene()
    sim.reset()
    print("[P01] 장면 생성 완료: 바닥·조명·파란 상자·빨간 구·초록 원뿔을 확인하다.")
    count = 0
    while simulation_app.is_running() and (args_cli.steps == 0 or count < args_cli.steps):
        sim.step()
        count += 1
    print(f"[P01] 종료: {count}회 step 호출. 실제 영상 품질은 GUI에서 확인하다.")


if __name__ == "__main__":
    try:
        main()
    finally:
        simulation_app.close()
