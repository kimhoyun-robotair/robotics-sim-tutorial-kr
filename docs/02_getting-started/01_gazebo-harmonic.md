# Harmonic 소개

> **난이도:** 초급  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** 없음

## 학습 목표

- Gazebo Sim의 server, GUI, Transport의 역할을 구분합니다.
- Harmonic에서 사용하는 `gz` CLI의 기본 명령을 확인합니다.
- ROS 2가 Gazebo의 내부 통신을 대체하지 않는 이유를 이해합니다.

## 배경 지식

Gazebo Sim은 물리 계산과 센서 시뮬레이션을 담당하는 server와, 렌더링 및 조작을 담당하는 GUI를 분리할 수 있습니다. World와 model은 SDF로 기술하고, Gazebo 내부 통신은 Gazebo Transport가 담당합니다.

ROS 2 노드가 Gazebo 데이터에 접근할 때는 기본적으로 `ros_gz_bridge`가 두 미들웨어 사이에서 메시지를 변환합니다. 즉, Gazebo Transport와 ROS 2 DDS는 같은 시스템이 아니며, 토픽 방향과 메시지 형식을 각각 명시해야 합니다.

## 실습

사용 가능한 하위 명령을 먼저 확인합니다.

```bash
gz --commands
gz sim --help
gz topic --help
```

자주 쓰는 명령은 다음과 같습니다.

| 명령 | 용도 |
| --- | --- |
| `gz sim` | 시뮬레이터 실행·관리 |
| `gz topic` | Gazebo Transport 토픽 조회·발행 |
| `gz service` | Gazebo 서비스 조회·호출 |
| `gz model` | model 정보 조회 |

## 결과 확인

`gz --commands` 목록에 `sim`, `topic`, `service`, `model`이 보이면 Gazebo Tools가 설치되어 있습니다.

## 다음 단계

[Jazzy 환경 설치](02_installation-jazzy.md)를 확인한 뒤, [SDF 기초](../03_beginner/03-sdf-basics.md)와 [첫 World](../03_beginner/04-first-world.md)를 실행합니다.
