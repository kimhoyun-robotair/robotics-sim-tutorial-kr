# 141. Prim에 붙는 행동 스크립트와 노출 속성

권장 학습 순서 **141** · Replicator 합성 데이터 기초와 확장 · 출처 ID `t046`

이 패키지는 Isaac Sim 5.1.0의 **Modular Behavior Scripting**을 독립 실행형 실습으로 구성합니다. Cube에는 위치·회전·텍스처 무작위화를, Light에는 밝기·색 무작위화를, Camera에는 Cube를 바라보는 행동을 붙입니다. 별도의 Sphere에는 이 패키지에 포함된 `OrbitBehavior`를 붙여 **직접 만든 행동, USD 속성 설정, timeline 콜백, 이벤트 완료 응답**까지 실행합니다.

기본 실습은 외부 환경 장면 없이 동작하도록 작은 도형과 로컬 생성 격자 텍스처를 사용합니다. 선택 사항인 `--stack`은 공식 `VolumeStackRandomizer`를 실제로 실행하므로 NVIDIA 자산 라이브러리가 필요합니다. 원문의 창고 장면 전체를 그대로 복제한 실습은 아닙니다.

## 이 실습의 의도

각 prim에 부착한 행동 스크립트가 노출된 USD 속성과 timeline·이벤트를 통해 동작하는 구조를 배우는 실습입니다. Cube에는 위치·회전·텍스처, 조명에는 밝기, 카메라에는 목표 추적, Sphere에는 직접 만든 원 궤도 행동을 맡겨 변화를 구분합니다. 기본 실행은 8프레임의 RGB와 속성 기록을 저장하며, 물리 상자 쌓기는 자산이 필요한 `--stack`을 선택해야 수행합니다.

## 실행 후 확인할 것

- **행동과 기록 대응:** `rgb/`와 `measurements.json`의 `target_position`, `orbit_position`, `light_intensity`를 비교합니다. 기본 조명 설정 범위는 8000–30000이며 `--interval 3`은 행동 update 간격이므로 모든 저장 이미지에서 모든 값이 달라질 필요는 없습니다.
- **원 궤도:** 기본 Sphere `/World/Moving`의 기록은 z=1.8 m를 유지하며 초기 중심 `(0,0,1.8)`에서 수평 반지름 약 0.8 m의 궤도에 있어야 합니다. 특정 x·y 좌표나 한 장의 이미지로 이동 주기 전체를 검증하지 않습니다.
- **노출 속성:** `behaviors.usda`에서 `/World/Target`의 `omni:scripting:scripts`와 `/World/Moving`의 `exposedVar:orbit:radius`, `speed`를 확인합니다. Play 중 radius를 바꾸면 궤도 크기가 바뀌며 Stop은 그 재생을 시작한 위치로 복원합니다.
- **완료 뒤 정지:** 데이터 저장 후 코드가 timeline을 Stop하므로 GUI가 남아 있어도 Sphere가 계속 돌지 않는 것이 정상입니다. 저장 USD를 다시 열면 그 파일의 위치를 다음 Play의 기준점으로 삼으며, 행동 파일·텍스처 참조가 유효해야 합니다.
- **이벤트 응답:** 캡처 루프는 `/World/Moving`의 `lesson.orbit.done` 응답에서 `state_name=RANDOMIZED`를 받은 뒤 시작합니다. 이 응답은 별도 성공 로그로 출력되지 않으며, 수신하지 못하면 30 update 뒤 timeout이 발생합니다. `--stack`도 RESET→SETUP→FINISHED 응답을 순서대로 기다리는 별도 작업입니다.

## GUI 실행과 종료

GUI에서 `--steps`를 생략하면 정해진 데이터 생성과 저장을 마친 뒤 사용자가 창을 닫을 때까지 장면을 유지합니다. 양수 `--steps N`은 **생성 완료 후 GUI를 관찰하는 app update 횟수**입니다. 생성 작업 자체나 데이터 프레임 수를 제한하는 값은 아니며, `--frames` 등으로 요청한 데이터가 무한히 늘어나지 않습니다. `--headless`는 관찰 대기 없이 기존 유한 작업을 마치면 종료합니다.

이 패키지 폴더에서 다음과 같이 실행합니다. 설치 경로는 자신의 환경에 맞추고, 이미 사용한 출력 폴더는 새 경로로 바꿉니다.

```bash
~/isaacsim/python.sh run.py --output output/gui
```

## 준비와 실행

Isaac Sim 5.1.0, 지원 NVIDIA RTX GPU/드라이버가 필요합니다. 설치에 포함된 `isaacsim.replicator.behavior`, `omni.kit.scripting`, Replicator, Pillow를 사용합니다. 확장은 실행 중 활성화합니다. 이 폴더만 복사해도 Python 파일 두 개와 가이드가 함께 이동하므로 형제 튜토리얼을 참조하지 않습니다.

이 패키지 폴더에서:

```bash
ISAACSIM="$HOME/isaacsim"
python3 run.py --help
"$ISAACSIM/python.sh" run.py --headless --frames 8 --interval 3 --output output/basic
"$ISAACSIM/python.sh" run.py --headless --frames 8 --interval 1 --output output/every_update
"$ISAACSIM/python.sh" run.py --stack --frames 8 --output output/stack
```

설치 경로를 맞추고 Windows에서는 `python.bat`를 사용합니다. 이미 존재하는 출력 폴더는 재사용하지 않으므로 결과를 덮어쓰지 않습니다. 기본 출력은 이 폴더의 `output/`입니다. `--headless`와 `--steps`를 생략하면 정해진 캡처 후에도 화면을 직접 닫을 때까지 유지합니다.

`--stack`은 Isaac Sim 5.1 자산 루트 아래의 `/Isaac/Environments/Simple_Warehouse/Props/SM_CardBoxC_01.usd`를 사용합니다. Assets Browser에서 같은 자산을 열 수 있는 네트워크/로컬 자산 경로 설정이 필요합니다. 자산이 없는데 임의 상자로 대체하여 공식 stacking이 실행됐다고 처리하지 않습니다.

## 순서대로 실습하기

1. 기본 명령을 실행하고 `rgb/` 이미지를 순서대로 봅니다. Cube의 텍스처·자세·위치와 조명 상태가 바뀌고 Camera는 Cube를 향합니다. Sphere는 수평 궤도를 따라 움직입니다.
2. `measurements.json`에서 시간, Cube 위치, Sphere 위치, 조명 세기를 확인합니다. `interval`은 **behavior의 update 횟수**이며 저장 이미지 개수나 벽시계 초와 같은 단위가 아닙니다. 따라서 모든 이미지에서 모든 항목이 바뀔 필요는 없습니다.
3. `output/basic/behaviors.usda`를 **File > Open**으로 엽니다. Stage에서 `/World/Moving`을 선택하고 Property에서 `exposedVar:orbit:radius`, `exposedVar:orbit:speed`를 찾습니다. radius를 `0.3`, speed를 `2.0`으로 설정하고 **Play**를 눌러 궤도 크기와 속도를 관찰합니다. **Stop**은 시작 위치로 복원합니다.
4. `/World/Target`을 선택해 `omni:scripting:scripts`와 `exposedVar` 아래의 `rotationRandomizer`, `locationRandomizer`, `textureRandomizer`를 확인합니다. 하나의 prim에 여러 스크립트가 붙을 수 있습니다. 같은 transform 속성을 서로 다른 스크립트가 동시에 쓰면 마지막 기록이 이길 수 있으므로 위치와 회전 담당을 나누었습니다.
5. 로컬 `orbit_behavior.py`를 읽습니다. `on_init()`은 속성과 이벤트 구독을 만들고, `on_play()`는 기준 위치를 저장하며, `on_update()`는 시간으로 새 위치를 계산합니다. `on_destroy()`는 구독을 해제해 이미 제거한 prim을 참조하지 않게 합니다.
6. `run.py`의 이벤트 대기와 `orbit_behavior.py`의 응답 처리를 확인합니다. `lesson.orbit.randomize`에 대한 `RANDOMIZED` 응답을 받아야 캡처 루프로 진행합니다. 응답 자체를 별도로 출력하는 로그는 없습니다. 요청에는 `prim_path`가 있어 특정 Sphere만 반응합니다. 응답은 실제 behavior 콜백이 위상 값을 바꾼 다음 보내며, 30 update 내 응답이 없으면 스크립트가 실패합니다.
7. 자산 준비 후 `--stack`을 실행합니다. 코드의 `reset → RESET`, `setup → SETUP`, `run → FINISHED` 요청·응답 순서와 생성된 상자 상태를 확인합니다. 상태가 기대값에 도달한 뒤에만 다음 작업을 진행합니다. `run` 완료는 모델 학습 완료가 아니라 상자를 쌓는 물리 실험 완료입니다.

저장된 stage의 스크립트 참조는 실행한 패키지와 Isaac Sim 설치의 실제 경로를 가리킵니다. **패키지를 다른 경로로 복사했으면 `run.py`를 다시 실행해 새 stage를 생성**하십시오. 기존 결과 USD만 따로 옮기는 경우에는 스크립트/텍스처 경로도 함께 수정해야 합니다.

## API와 Omniverse/USD 개념

| 요소 | 의미와 이 실습의 사용 |
|---|---|
| `BehaviorScript` | prim에 붙은 Python 객체이며 Kit의 초기화·재생·정지·update 생명주기 콜백을 받습니다. 단순히 매 프레임 전역 함수를 부르는 구조와 다릅니다. |
| `omni:scripting:scripts` | prim에 붙일 Python 소스 경로를 보관하는 USD 속성입니다. |
| `exposedVar:<behavior>:...` | Python 매개변수를 USD에 저장한 속성 이름입니다. UI와 코드가 같은 값을 읽을 수 있습니다. |
| `add_behavior_script_with_parameters_async()` | 스크립트를 붙인 뒤 속성이 만들어지는 update를 기다리고 값을 설정합니다. |
| `LocationRandomizer` | 범위 내 이동을 만듭니다. 기본 상대 좌표 모드에서는 시작 위치를 기준으로 이동합니다. |
| `RotationRandomizer` | 회전 연산을 갱신합니다. degrees 범위를 사용하며 기존 xform 연산 형식을 고려합니다. |
| `LookAtBehavior` | 카메라의 local -Z 축을 목표로 향하게 합니다. `targetPrimPath`가 지정되면 움직이는 prim을 추적합니다. |
| `LightRandomizer` / `TextureRandomizer` | USD light 속성과 material shader 입력을 바꿉니다. 텍스처 파일을 바꾸는 것은 mesh 자체를 바꾸는 것이 아닙니다. |
| `VolumeStackRandomizer` | 이벤트로 설정·실행·복원하는 별도 물리 작업입니다. timeline 기반 행동과 제어 경로가 다릅니다. |
| `publish_event_and_wait_for_completion_async()` | 요청/응답을 `prim_path`, `state_name`으로 대조하고 최대 update 수를 제한합니다. |

USD Stage는 여러 prim과 그 속성을 담은 장면입니다. 길이 단위는 미터, up axis는 Z입니다. `Gf.Vec3d`는 double 정밀도 3차원 벡터, `Sdf.ValueTypeNames.Double`은 USD 속성 타입입니다. Python 변수만 바꾸는 것과 USD에 값을 기록하는 것은 다릅니다.

`rep.orchestrator.step_async(delta_time=0, pause_timeline=False)`는 현재 시점에서 캡처합니다. 실제 행동을 한 번 더 진행시키는 것은 그 앞의 `next_update_async()`입니다. `rt_subframes`를 높인다고 행동의 시간 진행이 같은 비율로 빨라지는 것은 아닙니다. `wait_until_complete_async()`는 이미지 쓰기 큐를 비운 후 종료하기 위해 사용합니다.

## 한 변수만 바꾸는 실험

`--interval 3`과 `--interval 1`의 결과를 비교합니다. `light_intensity`가 연속해서 유지되는 횟수를 세어 보십시오. 그다음 CLI 인수는 원래대로 두고 `/World/Moving`의 radius만 바꿉니다. Sphere의 궤도 반지름만 변하는지 확인합니다.

## 문제 해결과 검증 범위

- Python 모듈을 못 찾으면 설치의 `python.sh`로 실행했는지 확인합니다. 일반 Python의 `--help`는 Kit를 시작하지 않습니다.
- 행동이 안 움직이면 **Play** 상태와 `delta_time > 0` 여부를 확인합니다. pause 상태에서 이미지 캡처만 해서는 timeline 행동이 실행되지 않습니다.
- `RANDOMIZED` timeout은 로컬 behavior 로드 또는 이벤트 구독이 실패했다는 뜻입니다. Kit 로그의 `orbit_behavior.py` 오류를 확인하십시오.
- `--stack` timeout은 자산/물리 설정/작업 완료 조건을 확인해야 합니다. 대기 시간을 늘리기 전에 `setup`과 `run` 중 어느 상태에서 실패했는지 구분합니다.
- 코드에서는 이 프로세스가 직접 붙이는 스크립트의 초기 경고 대기를 피하도록 `/app/scripting/ignoreWarningDialog`를 설정합니다. 외부 설정 파일을 수정하지 않습니다.
- 기본 도형 구성과 공식 여섯 behavior 사용법, 노출 속성, 로컬 사용자 behavior, 이벤트 제어를 포함합니다. 원문의 창고 환경 경로는 `/Isaac/Samples/Replicator/Stage/warehouse_pallets_behavior_scripts.usd`이며 별도의 대규모 장면 실험을 원할 때 선택할 수 있습니다.

## 출처

- [Isaac Sim 5.1.0: Modular Behavior Scripting](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_modular_scripting.html)
- [노출 USD 속성](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_modular_scripting.html#exposing-variables-through-usd-attributes)
- [이벤트 기반 behavior](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_modular_scripting.html#custom-event-based-behavior-scripts)
- [Volume Stack Randomizer](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_modular_scripting.html#volume-stack-randomizer)
- 설치 구현 위치: `exts/isaacsim.replicator.behavior/isaacsim/replicator/behavior/behaviors/`와 `utils/behavior_utils.py`.

## 실제 실행 기록

확인한 조건과 측정 결과는 [RUNTIME_CHECK.md](RUNTIME_CHECK.md)를 보세요. 검증은 해당 실행 모드에 한정됩니다.
