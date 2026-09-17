"""RMP 항목을 순서대로 활성화하며 Franka 추종 오차를 비교합니다."""
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
    parser.add_argument('--target', nargs=3, type=float, default=[0.5, 0., 0.7])
    parser.add_argument('--phase', choices=['baseline', 'cspace', 'target', 'collision', 'directional', 'orientation', 'limits', 'damping'], default='baseline')
    parser.add_argument('--target-gain', type=float, help='target_rmp.accel_p_gain 한 값만 덮어쓰기')
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

        from copy import deepcopy
        import yaml
        from isaacsim.robot_motion.motion_generation import RmpFlow, ArticulationMotionPolicy, ArticulationKinematicsSolver
        # RmpFlow는 말단 목표 추종과 등록된 장애물 회피를 결합해 로봇의 움직임을 계산하는 모션 정책이다.
        # ArticulationMotionPolicy는 모션 정책을 로봇 관절 구조에 연결해 다음 step의 ArticulationAction을 만든다.
        # ArticulationKinematicsSolver는 시뮬레이터의 로봇 관절과 기구학 계산기를 연결한다.
        # 말단 자세를 계산하거나 역기구학 결과를 로봇에 적용할 ArticulationAction으로 받을 수 있다.
        config = interface_config_loader.load_supported_motion_policy_config('Franka', 'RMPflow')
        with open(config['rmpflow_config_path']) as stream:
            tuning = yaml.safe_load(stream)
        original = deepcopy(tuning['rmp_params'])
        params = tuning['rmp_params']
        if args.phase != 'baseline':
            # 모든 항목의 metric와 inertia를 끈 뒤 필요한 항목만 복구한다.
            for values in params.values():
                for key in list(values):
                    if key in ('metric_weight', 'metric_scalar', 'min_metric_scalar', 'max_metric_scalar', 'min_metric_alpha', 'inertia', 'weight'):
                        values[key] = 0.0
            phases = ['cspace', 'target', 'collision', 'directional', 'orientation', 'limits', 'damping']
            level = phases.index(args.phase)
            active = ['cspace_target_rmp']
            if level >= 1:
                active.append('target_rmp')
            if level >= 2:
                active.append('collision_rmp')
            if level >= 4:
                active.append('axis_target_rmp')
            if level >= 5:
                active.extend(['joint_limit_rmp', 'joint_velocity_cap_rmp'])
            if level >= 6:
                active.append('damping_rmp')
            for key in active:
                params[key] = deepcopy(original[key])
            params['cspace_target_rmp']['inertia'] = original['cspace_target_rmp']['inertia'] if level >= 6 else 0.0
            if 1 <= level < 3:
                params['target_rmp']['min_metric_alpha'] = 0.0
                params['target_rmp']['metric_alpha_length_scale'] = 100000.0
                params['target_rmp']['proximity_metric_boost_scalar'] = 1.0
        if args.target_gain is not None:
            if args.target_gain < 0:
                raise ValueError('--target-gain must be nonnegative')
            params['target_rmp']['accel_p_gain'] = args.target_gain
        local_config = output / 'rmpflow.yaml'
        local_config.write_text(yaml.safe_dump(tuning, sort_keys=False))
        config['rmpflow_config_path'] = str(local_config)
        policy = RmpFlow(**config)
        obstacle = world.scene.add(FixedCuboid('/World/obstacle', name='obstacle', size=1.,
            scale=np.array([0.1, 0.2, 0.4]), position=np.array([0.4, 0.15, 0.4])))
        # 장애물을 모션 정책에 등록하여 회피 계산에 포함한다.
        policy.add_obstacle(obstacle)
        policy.visualize_collision_spheres()
        motion = ArticulationMotionPolicy(robot, policy, default_physics_dt=1./60.)
        kinematics = ArticulationKinematicsSolver(robot, policy.get_kinematics_solver(), 'right_gripper')
        trace = []
        step = 0
        while app.is_running() and (args.steps == 0 or step < args.steps):
            position, _ = target.get_world_pose()
            # 시뮬레이션의 로봇 베이스 자세를 정책에 알려 목표와 로봇의 좌표계를 맞춘다.
            policy.set_robot_base_pose(*robot.get_world_pose())
            # 모션 정책이 추종할 로봇 말단의 목표 위치·자세를 갱신한다.
            policy.set_end_effector_target(position, np.array([0., 0., 1., 0.]))
            # 등록된 장애물의 상태를 모션 정책의 내부 충돌 모델에 반영한다.
            policy.update_world()
            # 관절 제어기에 명령을 전달한다. 실제 관절의 움직임은 이후 물리 step에서 계산된다.
            robot.apply_action(motion.get_next_articulation_action())
            # 물리 시뮬레이션을 한 step 진행한다. render는 이 호출에서 렌더링도 수행할지 지정한다.
            world.step(render=not args.headless)
            if not app.is_running():
                break
            if step % 15 == 0:
                # 현재 관절 상태로부터 말단 위치·회전을 계산한다.
                ee_position, _ = kinematics.compute_end_effector_pose()
                # 현재 관절 속도를 읽는다. 배열 순서는 로봇의 관절 순서에 대응한다.
                trace.append({'step': step, 'end_effector_m': ee_position.tolist(),
                              'error_m': float(np.linalg.norm(ee_position-position)),
                              'joint_velocities_rad_s': robot.get_joint_velocities().tolist()})
            step += 1
        (output / 'tuning_trace.json').write_text(json.dumps({'phase': args.phase, 'trace': trace}, indent=2))
        print('Phase:', args.phase, 'last sample:', trace[-1] if trace else None)
        print('Output:', output)
    finally:
        # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
        app.close()


if __name__ == "__main__":
    main()
