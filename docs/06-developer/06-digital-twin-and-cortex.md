# Digital Twin, Cortex와 응용 도구

Digital twin workflow는 warehouse를 예쁘게 그리는 작업에 그치지 않는다. layout, static asset, conveyor, robot fleet, task, sensor, 운영 data 사이의 contract를 USD와 application logic으로 유지하다.

## warehouse를 계층화하다

```text
/World
├── Environment          # 바닥, 벽, rack, 조명
├── Infrastructure       # conveyor, gate, charger
├── Robots               # AMR, manipulator
├── Sensors              # 고정 camera, safety sensor
└── Looks                # material library
```

환경 layer와 동적 robot/session layer를 분리하다. static asset은 collider와 semantic label을 검증하고, conveyor는 surface velocity·방향·단위를 작은 test object로 먼저 확인하다. Warehouse Creator, Conveyor Belt Utility, Static Warehouse Assets는 초기 구성을 빠르게 하지만 결과 USD의 hierarchy와 physics 설정을 반드시 검토하다.

## Cortex의 역할

Cortex는 perception/context monitor, behavior와 decider network를 조합해 robot behavior를 구성하는 framework이다. `DfNetwork`의 decision은 상태를 읽고 child behavior를 선택하며, monitor는 world context를 갱신하다. 긴 절차를 거대한 tick 함수 하나에 넣는 대신 조건·행동·recovery를 분리하다.

```python
# 개념 예시이다. 실제 class import와 context는 5.1 Cortex 예제를 따르다.
class PickOrRecover:
    def decide(self):
        if self.context.grasp_failed:
            return "recover"
        if self.context.object_ready:
            return "pick"
        return "wait"
```

공식 walkthrough는 Franka block stacking과 UR10 bin stacking을 통해 decider network, behavior state, motion generation을 연결하다. 제품화할 때는 success뿐 아니라 timeout, unreachable target, lost object, emergency stop 경로를 먼저 설계하다.

## mapping과 fleet optimization 경계

- sensor simulation과 ROS 2로 map을 생성·검증하는 것은 Isaac Sim 영역이다.
- robot behavior와 manipulation orchestration은 Cortex/extension으로 구성할 수 있다.
- fleet route 최적화는 cuOpt 같은 별도 solver와 연결하다.
- 실제 운영 시스템의 인증·안전 판단을 simulator 결과만으로 대체하지 않다.

## application template

동일한 extension 집합과 setting으로 전용 application을 반복 배포해야 할 때 Application Template을 사용하다. 실험 한두 개 때문에 app 전체를 fork하기보다 먼저 작은 extension을 만들다. template을 선택했다면 experience file, extension dependency, asset path, default setting을 버전 관리하다.

## 출처

- [Digital Twin](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/digital_twin/index.html)
- [Warehouse Creator Extension](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/digital_twin/warehouse_logistics/ext_omni_warehouse_creator.html)
- [Conveyor Belt Utility](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/digital_twin/warehouse_logistics/ext_isaacsim_asset_gen_conveyor.html)
- [Isaac Cortex: Overview](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/cortex_tutorials/tutorial_cortex_1_overview.html)
- [Building Cortex Based Extensions](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/cortex_tutorials/tutorial_cortex_7_cortex_extension.html)
- [Application Template](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/app_template/index.html)
