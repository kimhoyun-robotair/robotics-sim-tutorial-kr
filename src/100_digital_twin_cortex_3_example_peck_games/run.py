"""Run the local Cortex behavior in a complete Franka workcell."""
import argparse
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--headless", action="store_true")
parser.add_argument("--interactive", action="store_true", help="Wait for viewport Play before running")
parser.add_argument("--steps", type=int, default=None,
                    help="Physics steps before exit; omitted: GUI until closed, headless 1800")
parser.add_argument("--behavior", choices=['peck_state_machine', 'peck_decider_network', 'peck_game'], default='peck_state_machine')
args = parser.parse_args()
if (args.steps is not None and args.steps < 1) or (args.headless and args.interactive):
    parser.error("Use positive steps; interactive mode requires a window")
if args.steps is None and args.headless:
    args.steps = 1800
from isaacsim import SimulationApp
# SimulationApp은 Python에서 Isaac Sim의 Kit 애플리케이션을 시작하고 갱신·종료하는 클래스이다.
# headless=True는 창 없이 실행한다는 뜻이며, omni와 Isaac Sim 확장 모듈은 앱 생성 후 import한다.
app = SimulationApp({"headless": args.headless})
try:
    import numpy as np
    from isaacsim.core.api.objects import DynamicCuboid
    # DynamicCuboid는 큐브 형상에 강체와 충돌 속성을 함께 부여하므로 중력과 접촉에 반응한다.
    from isaacsim.cortex.framework.cortex_utils import load_behavior_module
    # load_behavior_module은 Python 파일에서 Cortex 행동 모듈을 불러온다.
    from isaacsim.cortex.framework.cortex_world import CortexWorld
    # CortexWorld는 물리 시뮬레이션과 로봇의 행동 의사결정을 함께 진행하는 World이다.
    from isaacsim.cortex.framework.robot import add_franka_to_stage
    # add_franka_to_stage는 Cortex에서 제어할 Franka 로봇을 Stage에 추가한다.
    world = CortexWorld()
    robot = world.add_robot(add_franka_to_stage(name="franka", prim_path="/World/Franka"))
    specs = [("RedCube", [0.7, 0, 0]), ("BlueCube", [0, 0, 0.7]),
             ("YellowCube", [0.7, 0.7, 0]), ("GreenCube", [0, 0.7, 0])]
    width = 0.0515
    for x, (name, color) in zip(np.linspace(0.3, 0.7, 4), specs):
        # 생성한 객체를 World의 Scene에 등록하여 이름으로 찾고 초기화할 수 있게 한다.
        cube = world.scene.add(DynamicCuboid(prim_path=f"/World/Obs/{name}", name=name,
                  size=width, color=np.array(color), position=np.array([x, -0.4, width / 2])))
        robot.register_obstacle(cube)
    # 기본 바닥을 Scene에 추가한다. 이 바닥은 강체가 떨어졌을 때 충돌할 표면이다.
    world.scene.add_default_ground_plane()
    module = load_behavior_module(str(Path(__file__).resolve().parent / (args.behavior + ".py")))
    network = module.make_decider_network(robot)
    # Cortex 행동 네트워크를 등록하여 시뮬레이션 중 의사결정을 갱신한다.
    world.add_decider_network(network)
    # CortexWorld의 실행 루프를 시작하여 물리와 행동 네트워크를 함께 진행한다.
    world.run(app, play_on_entry=not args.interactive,
              is_done_cb=lambda: args.steps is not None and world.current_time_step_index >= args.steps)
    print(f"Cortex loop ended at physics step {world.current_time_step_index}; inspect task behavior separately")
finally:
    # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
    app.close()
