# 고급: Gazebo 확장과 자동 검증

> **난이도:** 고급  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** 중급 simulation stack

고급에서는 Gazebo server의 ECS(Entity Component System)와 System Plugin을 사용해 `tutorial_bot`을 확장합니다. Gazebo Transport의 publish/subscribe와 request/reply, 물리 파라미터, 대규모 headless simulation, 로그·디버깅, integration test, GitHub Actions CI를 다룹니다.

완료 시점에는 headless Gazebo에서 로봇을 spawn하고 `/cmd_vel`을 보낸 뒤 odometry 또는 pose 변화를 확인하는 자동 테스트를 갖춥니다.

## 학습 경로

1. [ECS System Plugin](01-ecs-system-plugin.md) (작업 9)
2. [Transport 인터페이스](02-transport-interfaces.md) (작업 10)
3. [물리와 주기 디버깅](03-physics-debugging.md) (작업 11)
4. [Headless 통합 테스트](04-headless-integration.md) (작업 12)
5. [CI 재현성](05-ci-reproducibility.md) (작업 14)
6. [Production Stack 프로젝트](project-production-stack.md) (작업 13)
