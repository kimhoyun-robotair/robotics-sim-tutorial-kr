"""UR10의 c-space, timestamped, task-space, composite 궤적을 생성합니다."""
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
    parser.add_argument('--trajectory', choices=['cspace', 'timestamped', 'taskspace', 'composite'], default='cspace')
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
        import lula
        # lula는 로봇 기구학과 경로·궤적 계산에 사용하는 라이브러리이며 여기서는 말단 경로를 구성한다.
        from isaacsim.core.api import World
        # World는 Stage의 객체와 작업을 관리하고 물리·렌더링 시간 간격, 초기화, 시뮬레이션 진행을 제어한다.
        from isaacsim.core.api.objects import VisualCuboid
        # VisualCuboid는 강체·충돌 속성 없이 외형만 만드는 큐브로, 목표 위치 표시 등에 사용한다.
        from isaacsim.core.prims import SingleArticulation
        # SingleArticulation은 하나의 관절 구조를 감싸 관절 위치·속도·힘을 읽고 제어한다.
        from isaacsim.core.utils.stage import add_reference_to_stage
        # add_reference_to_stage는 외부 USD 자산을 현재 Stage의 지정한 Prim 경로에 참조로 연결한다.
        from isaacsim.core.utils.extensions import get_extension_path_from_name
        # get_extension_path_from_name은 확장의 설치 경로를 찾아 내부 설정·예제 파일에 접근할 때 사용한다.
        from isaacsim.storage.native import get_assets_root_path
        # get_assets_root_path는 Isaac Sim 기본 자산의 루트 경로를 찾는다.
        # 반환 경로에 로봇·환경 USD의 상대 경로를 붙여 사용할 수 있다.
        from isaacsim.robot_motion.motion_generation import (LulaCSpaceTrajectoryGenerator,
            LulaTaskSpaceTrajectoryGenerator, LulaKinematicsSolver, ArticulationTrajectory)
        # LulaCSpaceTrajectoryGenerator는 관절 공간의 경유점을 따라가는 시간 기반 궤적을 생성한다.
        # LulaTaskSpaceTrajectoryGenerator는 말단의 위치·자세 경로를 따라가는 로봇 궤적을 생성한다.
        # LulaKinematicsSolver는 로봇 모델을 이용해 정기구학과 역기구학을 계산한다.
        # ArticulationTrajectory는 계산한 궤적을 시뮬레이션 시간 간격에 맞는 관절 명령 시퀀스로 변환한다.
        assets = get_assets_root_path()
        if assets is None:
            raise RuntimeError('Isaac Sim 5.1 Assets 경로를 찾을 수 없습니다')
        # stage_units_in_meters는 장면 길이 단위이고, physics_dt·rendering_dt는 각각 물리·렌더링 시간 간격(초)이다.
        world = World(stage_units_in_meters=1.0, physics_dt=1./60.)
        # 공식 관절 경로는 로봇 원점 아래도 지나므로 바닥을 작업영역 밖에 둔다.
        floor_z = -2.0
        # 기본 바닥을 Scene에 추가한다. 이 바닥은 강체가 떨어졌을 때 충돌할 표면이다.
        world.scene.add_default_ground_plane(z_position=floor_z)
        add_reference_to_stage(assets + '/Isaac/Robots/UniversalRobots/ur10/ur10.usd', '/World/ur10')
        # 생성한 객체를 World의 Scene에 등록하여 이름으로 찾고 초기화할 수 있게 한다.
        robot = world.scene.add(SingleArticulation('/World/ur10', name='ur10'))
        # World를 초기화하고 등록된 객체의 물리 핸들을 준비한다. 관절·강체 상태를 읽기 전에 호출한다.
        world.reset()
        configs = Path(get_extension_path_from_name('isaacsim.robot_motion.motion_generation')) / 'motion_policy_configs/universal_robots/ur10'
        kwargs = {'robot_description_path': str(configs / 'rmpflow/ur10_robot_description.yaml'),
                  'urdf_path': str(configs / 'ur10_robot.urdf')}
        kinematics = LulaKinematicsSolver(**kwargs)
        if args.trajectory in ('cspace', 'timestamped'):
            generator = LulaCSpaceTrajectoryGenerator(**kwargs)
            points = np.array([[-0.41, 0.5, -2.36, -1.28, 5.13, -4.71], [-1.43, 1., -2.58, -1.53, 6., -4.74],
                               [-2.83, 0.34, -2.11, -1.38, 1.26, -4.71], [-0.41, 0.5, -2.36, -1.28, 5.13, -4.71]])
            if args.trajectory == 'timestamped':
                trajectory = generator.compute_timestamped_c_space_trajectory(points, np.array([0., 5., 10., 13.]))
            else:
                trajectory = generator.compute_c_space_trajectory(points)
            targets = [kinematics.compute_forward_kinematics('ee_link', point)[0] for point in points]
        elif args.trajectory == 'taskspace':
            generator = LulaTaskSpaceTrajectoryGenerator(**kwargs)
            targets = np.array([[0.3, -0.3, 0.1], [0.3, 0.3, 0.1], [0.3, 0.3, 0.5], [0.3, -0.3, 0.5], [0.3, -0.3, 0.1]])
            orientations = np.tile(np.array([0., 1., 0., 0.]), (len(targets), 1))
            trajectory = generator.compute_task_space_trajectory_from_points(targets, orientations, 'ee_link')
        else:
            generator = LulaTaskSpaceTrajectoryGenerator(**kwargs)
            rotation = lula.Rotation3(np.pi/2, np.array([1., 0., 0.]))
            path = lula.create_task_space_path_spec(lula.Pose3(rotation, np.array([0.3, -0.1, 0.3])))
            path.add_translation(np.array([0.3, -0.1, 0.5]))
            path.add_rotation(lula.Rotation3(np.pi/3, np.array([1., 0., 0.])))
            path.add_three_point_arc(np.array([0.3, 0.3, 0.3]), np.array([0.3, 0., 0.5]), constant_orientation=True)
            composite = lula.create_composite_path_spec(np.zeros(6))
            composite.add_task_space_path_spec(path, lula.CompositePathSpec.TransitionMode.FREE)
            joint_path = lula.create_c_space_path_spec(np.zeros(6))
            joint_path.add_c_space_waypoint(np.array([0., 0.5, -2., -1.28, 5.13, -4.71]))
            composite.add_c_space_path_spec(joint_path, lula.CompositePathSpec.TransitionMode.FREE)
            trajectory = generator.compute_task_space_trajectory_from_path_spec(composite, 'ee_link')
            targets = [np.array([0.3, -0.1, 0.3]), np.array([0.3, -0.1, 0.5]), np.array([0.3, 0.3, 0.3])]
        if trajectory is None:
            raise RuntimeError('Lula가 궤적을 만들지 못했습니다. joint limit/waypoint/시간 제한을 확인하세요')
        for index, position in enumerate(targets):
            world.scene.add(VisualCuboid(f'/World/waypoint_{index}', name=f'waypoint_{index}', size=0.025,
                position=position, color=np.array([1., 0.2, 0.2])))
        actions = ArticulationTrajectory(robot, trajectory, physics_dt=1./60.).get_action_sequence()
        if not actions:
            raise RuntimeError('생성된 action sequence가 비어 있습니다')
        # 시작 상태 설정에만 teleport를 사용한다. 재생 중에는 drive target을 적용한다.
        robot.set_joint_positions(actions[0].joint_positions, joint_indices=actions[0].joint_indices)
        trace = []
        executed_steps = 0
        step = 0
        while app.is_running() and (args.steps == 0 or step < args.steps):
            action = actions[min(step, len(actions)-1)]
            # 관절 제어기에 명령을 전달한다. 실제 관절의 움직임은 이후 물리 step에서 계산된다.
            robot.apply_action(action)
            # 물리 시뮬레이션을 한 step 진행한다. render는 이 호출에서 렌더링도 수행할지 지정한다.
            world.step(render=not args.headless)
            if not app.is_running():
                break
            executed_steps += 1
            if step % 15 == 0:
                # 현재 관절 위치를 읽는다. 회전 관절은 라디안, 직선 관절은 장면 길이 단위를 사용한다.
                measured = robot.get_joint_positions()[action.joint_indices]
                trace.append({'step': step, 'target_positions': np.asarray(action.joint_positions).tolist(),
                              'measured_positions': measured.tolist()})
            step += 1
        result = {'mode': args.trajectory, 'physics_dt_s': 1./60., 'ground_plane_z_m': floor_z, 'action_count': len(actions),
                  'duration_s': (len(actions)-1)/60., 'completed_sequence': executed_steps >= len(actions), 'trace': trace}
        (output / 'trajectory.json').write_text(json.dumps(result, indent=2))
        print('Trajectory:', args.trajectory, 'actions:', len(actions), 'full playback:', result['completed_sequence'])
        print('Output:', output)
    finally:
        # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
        app.close()


if __name__ == "__main__":
    main()
