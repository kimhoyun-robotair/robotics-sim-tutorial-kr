# 64. 관절의 명령 effort와 실제 힘·토크

권장 학습 순서 **64** · 센서와 측정 데이터 · 출처 ID `t151`

외부 Ant 자산 없이 만든 한 관절 팔에서 사용자가 설정한 effort, 관절축 방향 측정 effort, 6차원 incoming force/torque를 함께 기록합니다. 원문의 센서 API를 작은 articulation에 적용한 독립 예제입니다.

## 이 실습의 의도

Y축 회전 관절 하나로 긴 링크를 지지하여, 사용자가 준 effort와 관절에서 측정한 힘·토크가 서로 다른 정보임을 익힌다. 고정된 base와 중력을 받는 링크, 목표각 0°의 drive를 사용하므로 명시적 effort 명령이 없어도 관절 반력이 생기는 상황을 관찰할 수 있다. 기본 실행은 매 물리 step의 세 종류 측정값과 DOF·link 인덱스를 함께 저장한다.

## 실행 후 확인할 것

- **지지 구조**: Stage에서 `/World/Arm/FixedRoot`가 base를 세계에 고정하고 `/World/Arm/Joint`가 `/World/Arm/Link`를 Y축으로 연결하는지 확인한다. 링크가 중력 아래에서 drive 목표 자세 부근으로 움직이는 과도 구간도 측정 대상이다.
- **명령과 측정의 차이**: `joint_forces.json`의 `samples`에서 `applied_effort_Nm`과 `measured_effort_Nm`을 비교한다. 이 코드에는 `set_joint_efforts()` 호출이 없으므로 명령 effort가 0이어도 측정 토크와 반력이 생길 수 있다.
- **배열과 좌표계**: `incoming_force_torque`는 child link의 incoming joint frame 기준 6성분이며 앞의 3개는 N, 뒤의 3개는 N·m이다. JSON의 `dof_index`는 effort 배열, `link_index`는 force 배열에 사용하므로 두 번호가 같을 것을 요구하지 않는다.
- **질량 비교**: 충분히 진정된 구간을 골라 기본 1 kg과 `--mass 2`의 유지 토크 크기를 비교한다. 중력 부하가 커지는 경향을 확인하되 초기 충격, drive 오차와 실제 관절각 때문에 매 step이 정확히 두 배일 것을 요구하지 않는다.
- **기록 구간**: 기본 `samples`는 처음 240물리 스텝의 시계열이다. 이후 GUI의 관절은 계속 움직여도 파일은 추가되지 않으며, `arm.usda`는 저장 시점의 장면이므로 초기 낙하·진동을 다시 보려면 재실행한다.

## 이 패키지만으로 준비하기

Isaac Sim **5.1.0**, 지원 NVIDIA GPU/드라이버, Isaac Sim 설치의 `python.sh`가 필요합니다. GUI 관찰 단계는 화면과 RTX 렌더링이 가능한 환경에서 수행합니다. 로컬 기본 장면은 코드로 만들며 다른 `src` 패키지, 공통 모듈, 저장소의 asset/에 의존하지 않습니다. 원문의 별도 에셋·설치 예제를 사용하는 추가 단계는 아래에 구체적으로 구분했습니다.

```bash
export ISAAC_SIM_PATH=/path/to/isaacsim
cd src/64_sensors_sensors_physics_articulation_force
python3 run.py --help
"$ISAAC_SIM_PATH/python.sh" run.py --output output/run-01
```

출력 폴더는 **존재하지 않는 새 경로**를 지정합니다. 이미 있으면 오류로 멈추어 이전 결과를 보호합니다. `--output`을 생략하면 이 패키지의 `output/날짜_시간/`에 저장합니다.

`--steps`를 생략하면 사용자가 창을 닫을 때까지 GUI와 물리·렌더링·센서 갱신이 계속됩니다. 처음 240스텝의 측정 결과를 한 번 저장하며, 이후 관찰 중에는 파일이나 기록 배열을 계속 늘리지 않습니다. `--steps N`에 양수를 주면 N스텝의 결과를 저장하고 종료합니다. `--headless`만 사용하면 기존과 같이 240스텝 후 종료합니다. `--interactive`는 기존 명령 호환용이며 이제 필요하지 않습니다. 명시한 `--steps`의 종료 조건을 해제하지 않고, `--headless`와 함께 사용할 수 없습니다.

run.py는 standalone 실행용이므로 Script Editor에 전체를 붙이지 않습니다. 처음 240스텝을 마치기 전에 창을 닫으면 결과 파일은 완성되지 않을 수 있습니다.

창 없이 유한 실행으로 결과만 만들 때는 별도의 새 출력 경로를 사용합니다.

```bash
"$ISAAC_SIM_PATH/python.sh" run.py --headless --steps 240 --output output/batch-01
```

## 실습 순서와 관찰

1. 실행한 `joint_forces.json`에서 dof_index와 link_index를 확인합니다. samples의 `applied_effort_Nm`, `measured_effort_Nm`, `incoming_force_torque`를 비교합니다.
2. `--headless`와 `--steps` 없이 실행해 `/World/Arm/FixedRoot`, `/World/Arm/Joint`, `/World/Arm/Link`를 선택합니다. FixedRoot는 세계에 고정되고 Joint의 자유 축은 Y입니다.
3. `incoming_force_torque`의 처음 3값은 힘, 나머지 3값은 토크입니다. 같은 배열 인덱스를 DOF 번호로 해석하지 마세요. 코드에서 child link 이름으로 실제 link index를 구합니다.
4. `--mass 2 --output output/mass2`로 링크 질량만 두 배로 늘리고 유지 토크 변화를 비교합니다. drive 목표각·중력·길이는 그대로입니다.
5. 출력 `arm.usda`는 실행 후 장면입니다. 초기 자세부터 다시 관찰하려면 `run.py`를 재실행하세요.

## API와 USD 개념

Articulation은 관절로 연결된 rigid body tree입니다. 각 link는 부모로부터 들어오는 joint가 하나입니다. `get_applied_joint_efforts()`는 사용자가 설정한 effort, `get_measured_joint_efforts()`는 자유 축으로 투영한 실제 effort, `get_measured_joint_forces()`는 joint 반력의 6성분입니다.

Drive가 gravity를 버티는 경우 사용자가 `set_joint_efforts`로 준 값이 0이어도 실제 반력은 0이 아닐 수 있습니다. revolute effort는 N·m, prismatic effort는 N입니다. 반력은 link incoming joint의 child frame 기준입니다.

5.1의 공개 문서 예제처럼 link index 확인에 `_articulation_view.get_link_index`를 사용합니다. 이는 wrapper 내부 경로이므로 버전 변경 시 확인해야 합니다. 힘 배열은 base 행을 포함하지만 DOF effort 배열은 그렇지 않아 인덱스를 섞으면 다른 관절을 읽습니다.

## 확장 실습·성공 기준·문제 해결

`World.reset()` 전에는 물리 handle이 없어서 측정할 수 없습니다. 힘이 예상과 다르면 Joint body0/body1, Y축, localPos와 kg·m 단위를 확인합니다. 이 예제 링크의 중심은 회전축에서 0.75 m 떨어져 있어 수평 정지 시 중력 토크 크기는 약 m×9.81×0.75 N·m이지만 drive 오차와 동역학 때문에 매 step이 이 값과 같지는 않습니다.

원문의 Ant를 사용할 경우 NVIDIA 에셋 `/Isaac/Robots/IsaacSim/Ant/ant.usd`를 로드해 torso articulation과 `/World/Ant/joints`의 body1 관계로 link index를 찾습니다. joint name→DOF index와 body1→force row 매핑은 별도로 만들어야 합니다. 고정 joint의 6차원 힘도 이 API로 읽어 force/torque sensor처럼 사용할 수 있습니다.

## 출처와 검증 범위

- [NVIDIA Isaac Sim 5.1.0 — Articulation Joint Sensors](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_physics_articulation_force.html)
- 구현 API는 설치된 5.1 `exts/`와 해당 `standalone_examples/` 원본을 함께 확인했습니다. 원문과 다른 작은 장면·GUI 관찰 루프·측정 스냅샷 저장은 이 패키지에서 추가했습니다.

Python 문법·도움말과 파일 구성을 검사했으며, RTX 영상/점군과 PhysX 런타임·GUI 상호작용은 작성 작업에서 실행하지 않았습니다. 실제 성공 여부는 위 단계의 **측정 파일과 화면 결과**로 확인합니다. `tutorial.json`의 verification은 그 이유로 `not_run`입니다.
