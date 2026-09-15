# 141. 물체에 행동을 붙이고 USD 속성으로 조절하기

## 이번에 배우는 것

**각 prim에 행동 스크립트를 붙이고, 타임라인과 이벤트가 그 행동을 어떻게 진행시키는지 확인합니다.**

140번에서는 그래프에 위치 계산을 넣었습니다. 이번에는 물체마다 자기 행동을 갖게 만듭니다. Cube의 위치·회전·텍스처, 조명 변화, 카메라 추적을 나누어 붙이고 Sphere에는 직접 만든 원 궤도 행동을 사용합니다.

| prim | 부착하는 행동 |
|---|---|
| `/World/Target` | LocationRandomizer, RotationRandomizer, TextureRandomizer |
| `/World/Light` | LightRandomizer |
| `/World/Camera` | Target을 바라보는 LookAtBehavior |
| `/World/Moving` | 로컬 `orbit_behavior.py`의 OrbitBehavior |
| `/World/StackSurface` | `--stack`에서만 VolumeStackRandomizer |

**노출 속성**은 Python 설정값을 USD에 저장하여 Property 창에서도 읽고 바꿀 수 있게 만든 값입니다. 코드와 GUI가 같은 장면 속성을 사용하게 됩니다.

## 1. 행동을 붙인 장면 실행하기

Isaac Sim 5.1과 RTX GPU 환경에서 저장소 루트에서 실행하세요.

```bash
~/isaacsim/python.sh src/141_replicator_replicator_modular_scripting/run.py --frames 8 --interval 3 --output /tmp/tutorial141-first
```

출력은 새 폴더여야 합니다. 코드는 `isaacsim.replicator.behavior`를 활성화하고 로컬 격자 PNG 두 개를 생성하므로 기본 실행에는 외부 창고 자산이 필요하지 않습니다.

8캡처를 저장한 뒤 타임라인을 Stop하고 창은 유지합니다. 따라서 완료 후 Sphere가 멈춰 있어도 정상입니다. 창을 닫으면 종료하며 `--headless`를 추가하면 저장 후 바로 종료합니다. `--steps N`은 생성 후 GUI 갱신 수이고 행동의 interval이나 캡처 수를 바꾸지 않습니다.

### 코드에서 볼 부분

```python
prefix = f'exposedVar:{cls.BEHAVIOR_NS}:'
await add_behavior_script_with_parameters_async(
    prim, inspect.getfile(cls), {prefix + k: v for k, v in parameters.items()})
```

행동 소스 파일을 prim에 연결한 뒤 노출 속성이 준비될 때까지 기다리고 값을 설정합니다. 예를 들어 Cube의 행동에는 `interval=3`, 조명에는 intensity 범위 8000~30000을 전달합니다. `interval`은 **양의 시간 간격으로 호출된 행동 update의 횟수**에 적용됩니다. 저장한 사진 세 장마다 한 번 또는 3초마다 한 번이라는 뜻은 아닙니다.

기본 행동은 Play에서 초기값을 적용할 수 있고 캡처 과정에도 앱 갱신이 있습니다. 따라서 `--interval 3`이라고 JSON에서 동일 값이 반드시 세 행씩 반복된다고 예상하지 마세요.

### 실행 결과 확인하기

`rgb/` 이미지와 `measurements.json`을 같은 프레임 번호로 확인합니다.

| 기록 | 해석 |
|---|---|
| `time_s` | 해당 관찰의 타임라인 시간입니다. |
| `target_position` | Cube의 현재 translate입니다. |
| `orbit_position` | Sphere의 현재 translate입니다. |
| `light_intensity` | 그 시점에 읽은 조명 세기입니다. |
| `behaviors.usda` | 캡처 후, Stop 직전에 내보낸 장면입니다. |

Sphere는 초기 중심 `(0, 0, 1.8)`에서 반지름 0.8 m의 수평 궤도를 따릅니다. 기록의 z가 1.8 m를 유지하고 `sqrt(x²+y²)`가 약 0.8인지 확인하세요. 짧은 여덟 캡처로 한 바퀴 전체를 반드시 보게 되는 것은 아닙니다.

## 2. 로컬 행동의 시간과 완료 이벤트 따라가기

### 코드에서 볼 부분

`orbit_behavior.py`는 생명주기 콜백을 사용합니다.

```python
angle = speed * current_time + self._phase
self.prim.GetAttribute('xformOp:translate').Set(
    self._origin + Gf.Vec3d(radius * math.cos(angle), radius * math.sin(angle), 0))
```

`on_play()`가 `_origin`에 재생 시작 위치를 저장합니다. `on_update()`는 그 기준점에 원 궤도 오프셋을 더합니다. `speed`는 각도를 초당 얼마나 늘릴지 정하며 기본 1.0 rad/s, `radius`는 거리입니다. `on_stop()`은 처음 저장한 위치로 복원합니다. `on_destroy()`는 이벤트 구독을 해제합니다.

행동은 `lesson.orbit.randomize` 요청도 받습니다. 요청의 `prim_path`가 자신과 맞으면 위상 `_phase`를 바꾸고 `lesson.orbit.done`에 `state_name=RANDOMIZED`를 보냅니다. 시작점의 각도를 바꾸는 이벤트이며 반지름을 바꾸지는 않습니다.

```text
요청 발행 → 대상 prim이 위상 변경 → 완료 응답
    → run.py가 prim_path와 RANDOMIZED를 확인 → 캡처 시작
```

응답을 받지 못하면 30 앱 갱신 뒤 timeout입니다. 완료 이벤트를 기다리는 이유는 요청을 보냈다는 사실만으로 행동이 적용되었다고 판단하지 않기 위해서입니다.

바깥에서는 `SimulationApp.update()`가 비동기 작업을 진행시키고, 내부 작업은 `await next_update_async()`로 앱에 실행 기회를 줍니다. `step_async(delta_time=0.0, pause_timeline=False)`는 준비된 시점의 데이터를 촬영합니다. 행동의 시간 진행과 저장을 따로 읽어야 합니다.

### 속성과 선택 기능 확인하기

`behaviors.usda`를 열어 `/World/Moving`의 `exposedVar:orbit:radius`, `speed`와 각 prim의 `omni:scripting:scripts`를 확인하세요. 이 USD는 스크립트와 텍스처 경로를 참조하므로 파일만 다른 컴퓨터로 옮겨도 같은 행동이 자동으로 준비되는 것은 아닙니다.

저장된 USD는 Stop 전의 Sphere 위치를 갖습니다. 이를 새로 열어 Play하면 **그 파일에 저장된 위치가 새 궤도의 중심**이 됩니다. 원점 기준의 0.8 m 검사와 다시 연 장면의 기준점을 혼동하지 마세요.

물리 쌓기는 다음 선택 실행입니다.

```bash
~/isaacsim/python.sh src/141_replicator_replicator_modular_scripting/run.py --stack --headless --frames 8 --output /tmp/tutorial141-stack
```

5.1 자산 루트의 `SM_CardBoxC_01.usd`가 필요합니다. VolumeStackRandomizer에 2~3개 상자를 요청하고 `reset → RESET`, `setup → SETUP`, `run → FINISHED` 응답을 순서대로 기다립니다. 각 단계의 대기 한도는 30·500·1500 앱 갱신입니다. 기본 Sphere 행동과 달리 이벤트로 시작하고 완료를 기다리는 물리 작업입니다.

## 3. 행동·속성·캡처의 관계 정리

```text
prim의 스크립트 참조 → 행동 인스턴스 생성
USD 노출 속성 → 행동이 사용할 범위·반지름·속도
타임라인 / 명시적 이벤트 → 실제 상태 변경
Replicator 캡처 → 이미지와 변경된 속성 기록
```

여러 행동을 한 prim에 붙일 수 있지만 같은 속성을 동시에 쓰면 서로 덮어쓸 수 있습니다. 이번 Cube는 위치·회전·텍스처의 담당이 나뉘어 있습니다. 모듈로 나눈다는 것은 파일을 늘리는 것뿐 아니라 **누가 어떤 상태를 쓰는지 명확히 하는 일**입니다.

## 4. 간단한 확인 실험

저장된 `behaviors.usda`를 새로 열고 Play하여 궤도를 확인한 뒤 Stop하세요. `/World/Moving`의 **`exposedVar:orbit:radius`만 0.8에서 0.4로 바꾸고** 다시 Play합니다. speed는 1.0으로 유지합니다.

궤도의 중심에서 Sphere까지 거리는 절반이 되고 한 바퀴의 시간은 유지되어야 합니다. 확인할 중심은 원점이 아니라 이번 Play 전에 저장된 Sphere 위치입니다. Stop했을 때 그 위치로 돌아오는지도 확인하세요.

## 실행할 때 막히면

- **생성 완료 뒤 움직이지 않음**: 코드가 Stop한 상태입니다. GUI에서 다시 Play하면 행동을 관찰할 수 있습니다.
- **`RANDOMIZED` timeout**: `orbit_behavior.py` 로드 오류와 대상 prim 경로를 확인하세요. 완료 로그가 별도로 없다는 것과 응답 실패는 다릅니다.
- **옮긴 USD에서 격자나 행동이 사라짐**: 스크립트·텍스처 참조 경로를 확인하거나 새 위치에서 `run.py`로 다시 생성하세요.
- **stack timeout**: RESET·SETUP·FINISHED 중 어느 단계가 실패했는지 확인한 뒤 자산 접근과 물리 로그를 살펴보세요.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Modular Behavior Scripting](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_modular_scripting.html)에 대응합니다. 공식 내장 행동을 작은 로컬 장면에 적용하고 OrbitBehavior의 시간·이벤트 제어를 추가했습니다.

[RUNTIME_CHECK.md](RUNTIME_CHECK.md)의 기존 기록은 기본 한 프레임에서 행동 출력 위치와 조명 값을 확인한 범위입니다. GUI의 재생·복원·반지름 편집, 선택 stacking 전체와 이번 확인 실험을 검증한 기록은 아닙니다. 문서 개정에서는 소스·설치 행동 구현을 대조했습니다.
