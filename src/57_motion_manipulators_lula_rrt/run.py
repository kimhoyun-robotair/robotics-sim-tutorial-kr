"""Lula RRT로 장애물이 있는 Franka 경로를 계획하고 시각화합니다."""
import argparse
import json
from pathlib import Path
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--steps", type=int, default=None,
                        help="Physics step limit; omitted/0: GUI until closed, headless default: 600")
    parser.add_argument("--output", type=Path, help="새 결과 디렉터리; 기존 경로는 거부")
    parser.add_argument('--target', nargs=3, type=float, default=[0.45, 0.5, 0.7])
    parser.add_argument('--max-iterations', type=int, default=5000)
    parser.add_argument('--max-cspace-dist', type=float, default=0.01)
    args = parser.parse_args()
    if args.steps is None:
        args.steps = 600 if args.headless else 0
    if args.steps < 0 or (args.headless and args.steps == 0):
        parser.error("--steps must be nonnegative; headless requires positive steps")
    if args.output is None:
        parent = Path(__file__).resolve().parent / "output"
        parent.mkdir(exist_ok=True)
        output = Path(tempfile.mkdtemp(prefix="run_", dir=parent))
    else:
        output = args.output.resolve()
        output.mkdir(parents=True, exist_ok=False)
    from isaacsim import SimulationApp
    # SimulationApp은 Python에서 Isaac Sim의 Kit 애플리케이션을 시작하고 갱신·종료하는 클래스이다.
    # headless=True는 창 없이 실행한다는 뜻이며, omni와 Isaac Sim 확장 모듈은 앱 생성 후 import한다.
    app = SimulationApp({"headless": args.headless})
    try:
        import numpy as np
        from isaacsim.core.api import World
        # World는 Stage의 객체와 작업을 관리하고 물리·렌더링 시간 간격, 초기화, 시뮬레이션 진행을 제어한다.
        from isaacsim.core.api.objects import VisualCuboid, FixedCuboid
        # VisualCuboid는 강체·충돌 속성 없이 외형만 만드는 큐브로, 목표 위치 표시 등에 사용한다.
        # FixedCuboid는 충돌 가능한 고정 큐브로, 바닥이나 움직이지 않는 장애물을 만들 때 사용한다.
        from isaacsim.core.prims import SingleArticulation
        # SingleArticulation은 하나의 관절 구조를 감싸 관절 위치·속도·힘을 읽고 제어한다.
        from isaacsim.core.utils.stage import add_reference_to_stage
        # add_reference_to_stage는 외부 USD 자산을 현재 Stage의 지정한 Prim 경로에 참조로 연결한다.
        from isaacsim.storage.native import get_assets_root_path
        # get_assets_root_path는 Isaac Sim 기본 자산의 루트 경로를 찾는다.
        # 반환 경로에 로봇·환경 USD의 상대 경로를 붙여 사용할 수 있다.
        from isaacsim.robot_motion.motion_generation import interface_config_loader
        # interface_config_loader는 지원 로봇의 기구학·모션 정책 설정 파일 경로와 매개변수를 불러온다.
        assets = get_assets_root_path()
        if assets is None:
            raise RuntimeError('Isaac Sim 5.1 Assets 경로를 찾을 수 없습니다')
        # stage_units_in_meters는 장면 길이 단위이고, physics_dt·rendering_dt는 각각 물리·렌더링 시간 간격(초)이다.
        world = World(stage_units_in_meters=1.0, physics_dt=1./60.)
        # 기본 바닥을 Scene에 추가한다. 이 바닥은 강체가 떨어졌을 때 충돌할 표면이다.
        world.scene.add_default_ground_plane()
        add_reference_to_stage(assets + '/Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd', '/World/panda')
        # 생성한 객체를 World의 Scene에 등록하여 이름으로 찾고 초기화할 수 있게 한다.
        robot = world.scene.add(SingleArticulation('/World/panda', name='panda'))
        target = world.scene.add(VisualCuboid('/World/target', name='target', size=0.04,
            position=np.array(args.target), color=np.array([1., 0.2, 0.2])))
        # World를 초기화하고 등록된 객체의 물리 핸들을 준비한다. 관절·강체 상태를 읽기 전에 호출한다.
        world.reset()

        from isaacsim.robot_motion.motion_generation import PathPlannerVisualizer
        # PathPlannerVisualizer는 경로 계획 결과를 로봇에 적용할 관절 명령 시퀀스로 변환하는 기능을 제공한다.
        from isaacsim.robot_motion.motion_generation.lula import RRT
        # RRT는 관절 공간을 샘플링하여 시작 상태에서 말단 목표로 가는 충돌 회피 경로를 탐색한다.
        if args.max_iterations < 1 or args.max_cspace_dist <= 0:
            raise ValueError('RRT iterations와 interpolation 간격은 양수여야 합니다')
        config = interface_config_loader.load_supported_path_planner_config('Franka', 'RRT')
        planner = RRT(**config)
        planner.set_max_iterations(args.max_iterations)
        obstacle = world.scene.add(VisualCuboid('/World/wall', name='wall', size=1.,
            scale=np.array([0.1, 0.4, 0.4]), position=np.array([0.3, 0.6, 0.6])))
        planner.add_obstacle(obstacle)
        visualizer = PathPlannerVisualizer(robot, planner)
        actions = []
        action_index = 0
        last_target = None
        plans = []
        step = 0
        while app.is_running() and (args.steps == 0 or step < args.steps):
            current, _ = target.get_world_pose()
            if step % 60 == 0 and (last_target is None or np.linalg.norm(current-last_target) > 0.01):
                # 로봇의 월드 위치와 회전 쿼터니언을 읽는다.
                planner.set_robot_base_pose(*robot.get_world_pose())
                planner.set_end_effector_target(current)
                planner.update_world()
                actions = visualizer.compute_plan_as_articulation_actions(max_cspace_dist=args.max_cspace_dist)
                action_index = 0
                last_target = current.copy()
                record = {'step': step, 'target_m': current.tolist(), 'success': bool(actions),
                          'joint_positions': [np.asarray(a.joint_positions).tolist() for a in actions],
                          'joint_indices': [] if not actions else np.asarray(actions[0].joint_indices).tolist()}
                plans.append(record)
                print('RRT plan:', len(actions), 'interpolated actions; success:', bool(actions))
            if action_index < len(actions):
                # 관절 제어기에 명령을 전달한다. 실제 관절의 움직임은 이후 물리 step에서 계산된다.
                robot.apply_action(actions[action_index])
                action_index += 1
            # 물리 시뮬레이션을 한 step 진행한다. render는 이 호출에서 렌더링도 수행할지 지정한다.
            world.step(render=not args.headless)
            step += 1
        (output / 'plans.json').write_text(json.dumps(plans, indent=2))
        print('Output:', output)
        if not any(plan['success'] for plan in plans):
            raise RuntimeError('RRT가 경로를 찾지 못했습니다. plans.json과 목표/장애물/반복 제한을 확인하세요')
    finally:
        # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
        app.close()


if __name__ == "__main__":
    main()
