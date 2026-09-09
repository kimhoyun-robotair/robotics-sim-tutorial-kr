# 커스텀 자산 통합 학습 경로

이 과정에서는 직접 준비한 로봇·환경·센서를 하나의 시뮬레이션으로 통합한다. 로봇의 관절과 제어가 정상적으로 동작하고, 환경의 외형과 충돌 형상이 맞으며, 센서가 정해진 좌표계와 주기로 측정값을 내보내는지 확인한다. 장면을 다시 열거나 시뮬레이션을 재시작한 뒤에도 같은 조건으로 실행할 수 있어야 한다.

## 세 개의 독립된 결과물

| 문서 | 입력 | 최종 산출물 |
|---|---|---|
| `01-custom-robot` | URDF/Xacro/MJCF, 메시 | 물리와 제어 검증 시험을 통과한 `robot.usd` |
| `02-custom-environment` | CAD/메시/USD, 텍스처 | 충돌 형상·재질·의미 정보·조명이 분리된 `environment.usd` |
| `03-custom-sensors` | 사양서, 보정, 잡음 모델 | 로봇에 참조 가능한 센서 장착 구조와 데이터 처리 과정 |

## 권장 USD 조립 구조

```text
project_assets/
├── robots/demo_bot/
│   ├── demo_bot.usd
│   ├── configurations/
│   ├── meshes/
│   └── sensors/
├── environments/warehouse/
│   ├── warehouse.usd
│   ├── geometry/
│   ├── materials/
│   └── semantics/
└── stages/integration_scene.usd
```

원본 형상, 물리 속성, 센서 설정은 별도 레이어로 관리한다. 사용자가 여는 대표 USD 파일에서 Reference·Sublayer·Variant로 이들을 조합한다. 통합 장면에는 자산의 배치와 해당 실험에서 바꿀 설정을 기록한다.

## 검증 원칙

1. 시각 형상과 충돌 형상을 별도로 검사한다.
2. 물리 계산 전에 크기, 축, 질량과 관성을 검사한다.
3. 로봇은 링크, 관절 연결, articulation, 관절 드라이브, 외부 제어기 순서로 검증한다.
4. 센서는 Isaac Sim 원본 데이터를 먼저 검증한 뒤 ROS/Replicator 출력을 연결한다.
5. Stage 다시 열기, Stop→Play, 창 없이 실행하는 환경에서 같은 결과가 나와야 한다.
6. 화면 캡처 외에 USD, 스크립트, 측정값과 합격 판정 기준을 남긴다.

## 수료 조건

- [ ] 가져오기 로그의 경고를 분류하고 의도적으로 처리한다.
- [ ] 사용자 로봇이 10초 동안 안정적으로 서고 관절의 계단 입력 명령을 추종한다.
- [ ] 환경의 시각 메시와 충돌 형상이 분리되고 이동 경로가 막히지 않는다.
- [ ] 의미 정보 레이블과 센서 비시각 재질을 구분한다.
- [ ] 카메라, RTX LiDAR/Radar, IMU, 접촉/토크·힘 센서를 정해진 좌표계와 주기에 맞게 장착한다.
- [ ] 사용자 정의 OmniGraph/Python Extension을 다시 불러오거나 종료할 때 자원이 정리된다.

## 출처

- [Isaac Sim 5.1 — Asset Structure](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup/asset_structure.html)
- [Isaac Sim 5.1 — Robot Setup](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup/index.html)
- [Isaac Sim 5.1 — Sensors](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/index.html)
- [Isaac Sim 5.1 — Physics Simulation Fundamentals](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/physics/simulation_fundamentals.html)
