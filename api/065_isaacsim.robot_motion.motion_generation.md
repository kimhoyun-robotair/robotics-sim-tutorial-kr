# isaacsim.robot_motion.motion_generation

첫 등장: [43번 튜토리얼](../src/43_robot_setup_pickplace_example/TUTORIAL.md) · [run.py:37](../src/43_robot_setup_pickplace_example/run.py#L37)

로봇 끝단 목표나 경유점을 실제 articulation에 적용할 관절 명령으로 바꾸는 모션 생성 API입니다. 일부 예제에서는 `mg` 별칭으로 사용합니다.

- `LulaKinematicsSolver`, `ArticulationKinematicsSolver`: 로봇 설정을 읽고 정기구학·역기구학을 계산합니다.
- `RmpFlow`(`mg.lula.motion_policies.RmpFlow`), `ArticulationMotionPolicy`, `MotionPolicyController`: 장애물과 끝단 목표를 받아 매 스텝의 관절 명령을 만듭니다.
- `LulaCSpaceTrajectoryGenerator`, `LulaTaskSpaceTrajectoryGenerator`, `ArticulationTrajectory`: 관절·끝단 경유점으로 궤적을 만들고 action 시퀀스로 변환합니다.
- `PathPlannerVisualizer`: RRT의 경로를 보간한 action 목록으로 바꿔 로봇에 적용합니다.
- `interface_config_loader`: Franka용 기구학, RMPflow, RRT 설정을 불러옵니다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [ArticulationKinematicsSolver](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.robot_motion.motion_generation/docs/index.html#isaacsim.robot_motion.motion_generation.ArticulationKinematicsSolver)
- [RmpFlow](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.robot_motion.motion_generation/docs/index.html#isaacsim.robot_motion.motion_generation.lula.motion_policies.RmpFlow)
- [LulaCSpaceTrajectoryGenerator](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.robot_motion.motion_generation/docs/index.html#isaacsim.robot_motion.motion_generation.lula.LulaCSpaceTrajectoryGenerator)
- [LulaTaskSpaceTrajectoryGenerator](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.robot_motion.motion_generation/docs/index.html#isaacsim.robot_motion.motion_generation.lula.LulaTaskSpaceTrajectoryGenerator)
- [isaacsim.robot_motion.motion_generation 공식 문서](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.robot_motion.motion_generation/docs/index.html)
