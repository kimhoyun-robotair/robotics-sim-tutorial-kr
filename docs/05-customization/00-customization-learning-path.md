# 커스텀 자산 통합 학습 경로

커스텀 자산 통합은 파일을 Stage에 보이게 하는 작업이 아니다. 로봇은 제어 가능한 articulation이어야 하고, 환경은 충돌·조명·semantic 의미가 일치해야 하며, sensor는 frame·rate·noise·lifecycle 계약을 가져야 하다.

## 세 개의 독립된 deliverable

| 문서 | 입력 | 최종 산출물 |
|---|---|---|
| `01-custom-robot` | URDF/Xacro/MJCF, mesh | physics와 control acceptance test를 통과한 `robot.usd` |
| `02-custom-environment` | CAD/mesh/USD, texture | collider·material·semantics·lighting이 분리된 `environment.usd` |
| `03-custom-sensors` | 사양서, calibration, noise model | robot에 reference 가능한 sensor rig와 data pipeline |

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

원본 geometry, physics authoring, sensor configuration과 integration scene을 한 layer에 모두 넣지 않다. entry USD는 reference/sublayer/variant를 조립하고, scene은 각 asset의 transform과 scenario override만 갖게 하다.

## 검증 원칙

1. 보이는 geometry와 collision geometry를 별도로 검사하다.
2. 물리 계산 전에 scale, axis, mass와 inertia를 검사하다.
3. robot은 link→joint→articulation→drive→controller 순으로 활성화하다.
4. sensor는 raw Isaac data를 먼저 검증한 뒤 ROS/Replicator output을 연결하다.
5. Stage reopen, Stop→Play, headless 실행에서 같은 결과가 나와야 하다.
6. screenshot 외에 USD, script, 측정값과 acceptance threshold를 남기다.

## 수료 조건

- [ ] import log의 warning을 분류하고 의도적으로 처리하다.
- [ ] custom robot이 10초 동안 안정적으로 서고 joint step 명령을 추종하다.
- [ ] environment의 visual mesh와 collider가 분리되고 이동 경로가 막히지 않다.
- [ ] semantic label과 sensor non-visual material을 구분하다.
- [ ] camera, RTX LiDAR/Radar, IMU, contact/effort sensor를 frame과 rate 계약에 맞게 장착하다.
- [ ] custom OmniGraph/Python extension이 reload와 shutdown에서 resource를 정리하다.

## 출처

- [Isaac Sim 5.1 — Asset Structure](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup/asset_structure.html)
- [Isaac Sim 5.1 — Robot Setup](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup/index.html)
- [Isaac Sim 5.1 — Sensors](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/index.html)
- [Isaac Sim 5.1 — Physics Simulation Fundamentals](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/physics/simulation_fundamentals.html)
