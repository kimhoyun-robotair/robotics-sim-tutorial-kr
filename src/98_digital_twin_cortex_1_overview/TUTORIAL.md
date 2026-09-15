# 98. t081 · Cortex의 여섯 단계와 command API

권장 학습 순서 **98** · 환경 구축과 로봇 행동 · 출처 ID `t081`

Franka의 손끝 목표를 유지하면서 팔의 나머지 자세와 gripper 폭을 바꾸는 실제 command API 예제다. 관절 각도를 매번 직접 명령하는 방식에서 목표 pose를 보내는 방식으로 사고를 옮긴다. 로컬 `run.py`는 NVIDIA의 `example_command_api_main.py`를 기반으로 CLI와 종료 조건을 추가했다.

1. `run.py`의 `NullspaceShiftState.target_p=[0.7,0,0.5]`를 확인한다. `config_mean`은 7개 arm joint의 기준 자세다. 손가락 두 관절은 별도 gripper commander가 담당한다.
2. 기본 실행에서 손끝이 목표 주변으로 이동한 뒤 팔 자세가 달라지는지 본다. `<enter> sampling posture config` 로그와 gripper 열림/닫힘을 함께 관찰한다.
3. `send_end_effector(target_position=..., posture_config=...)`는 Cartesian 목표와 선호 관절 자세를 함께 전달한다. `posture_config`는 목표를 이루는 방법의 선호이며 최종 joint 각도를 그대로 강제하는 명령이 아니다.
4. `step()`의 2초 조건이 끝나면 `None`을 반환하여 상태를 끝낸다. 외부 `DfStateSequence(loop=True)`가 다시 진입시키므로 `enter()`에서 새로운 자세를 뽑는다. 이 원본은 wall-clock `time.time()`을 사용한다.
5. 손끝 위치 목표의 z만 0.5에서 0.6으로 바꾸고 다시 실행한다. 자세 noise나 gripper 속도를 동시에 바꾸지 않는다. 목표 높이 변화와 팔 자세 변화를 구분한다.

Cortex는 perception → USD world belief → logical state monitors → decision → command API → control의 여섯 단계로 설명된다. 이 실습은 시뮬레이션의 상태를 직접 사용하므로 카메라 perception이나 실물 제어를 구현한 예제가 아니다. `CortexWorld`가 monitor, decision, commander 순서를 관리하고 `DfStateMachineDecider`는 상태 기계를 decider network에 넣는다. `robot.arm`은 RMPflow 기반 동작 생성기로, `robot.gripper`는 손가락 동작으로 명령을 분리한다.

USD는 장면과 로봇 belief를 표현하는 데이터베이스다. 실제 로봇의 관측을 넣는 world와 화면의 시뮬레이션 world를 동일시하지 않는 것이 이후 시스템 연결의 핵심이다. 회전행렬 `R`의 각 열은 손끝 좌표축을 world에서 표현한 벡터다. `get_fk_R()`, `unpack_R()`, `proj_orth()`로 원하는 z축에 y축을 직교 투영하고 cross product로 x축을 만든다. 축이 평행하면 정규화가 불안정하므로 임의 목표에 수식을 무조건 적용하지 않는다.

성공 기준은 실제 손끝의 목표 유지, posture 변화, gripper 변화가 관측되는 것이다. loop 종료만으로 제어 정확성이 증명되지는 않는다. 움직임이 없으면 Play 상태와 asset 로딩을 먼저 확인한다. 목표가 로봇 작업영역 밖이면 계속 도달하려 할 수 있다.

## 독립 실행 환경

이 디렉터리를 단독으로 복사하여 사용할 수 있다. Isaac Sim **5.1.0** 설치, 지원 RTX GPU/드라이버 및 해당 로봇 자산 접근이 필요하다. `isaacsim.cortex.framework`는 설치된 SDK이며 다른 로컬 튜토리얼 패키지를 import하지 않는다. Python/Kit 초기화와 scene 구성은 각 실행기에 들어 있다. USD Stage는 장면 전체, prim은 `/World/Franka` 같은 경로로 찾는 장면 객체이고, transform은 위치·회전·스케일이다.

```bash
cd /path/to/98_digital_twin_cortex_1_overview
python3 run.py --help
"$HOME/isaacsim/python.sh" run.py
```

기본은 창을 띄우고 자동 Play하며 사용자가 창을 닫을 때까지 계속 실행한다. 사람이 물체를 이동하는 실습은 `--interactive`를 추가하고 창에서 Play를 누른다. `--steps 1800`처럼 양수를 명시하면 interactive 여부와 관계없이 해당 physics step에 도달했을 때 종료한다. 화면 없는 실행은 `--headless`이며 `--steps` 생략 시 1800 step으로 종료한다. `--headless`와 `--interactive`는 동시에 사용할 수 없다. 새 데이터를 저장하는 튜토리얼이 아니며 성공은 위에 명시한 동작 관찰로 판단한다.

## 버전·검증·출처

- [Isaac Sim 5.1 원문](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/cortex_tutorials/tutorial_cortex_1_overview.html)의 모든 주요 하위 실습을 위 단계에 연결했다. 실행 코드는 설치본 5.1의 API와 대조했다.
- NVIDIA 예제를 포함한 파일은 원래 Apache-2.0 copyright header와 `LICENSE-NVIDIA-EXAMPLES`를 보존한다. 변경 내역은 `NOTICE.md`에 있다. 설치본 원본은 `standalone_examples/api/isaacsim.cortex.framework/` 및 `exts/isaacsim.cortex.behaviors/isaacsim/cortex/behaviors/`다.
- 작성 시 compile과 CLI help를 확인했다. GPU의 실제 로봇 동작과 GUI 상호작용은 실행하지 않았으며 `tutorial.json`은 `not_run`이다. 일반 Python에서 `omni`/`isaacsim` import가 없는 것은 `python.sh` 런타임을 쓰지 않았기 때문일 수 있다.
