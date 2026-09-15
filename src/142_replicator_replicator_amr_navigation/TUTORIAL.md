# 142. 로봇이 목적지에 가까워졌을 때만 촬영하기

## 이번에 배우는 것

**Nova Carter가 이동하다가 거리 조건을 만족하면 멈추고, 좌·우 카메라를 한 쌍으로 저장하도록 구성합니다.**

주행 중 모든 순간을 기록할 필요는 없습니다. 목적지의 물체가 충분히 가까워진 순간을 골라 촬영하면 관심 있는 관찰을 모을 수 있습니다. 이번 실습은 dolly를 목적지로 정하고, 접근 → 촬영 → 재배치 → 다음 접근을 반복합니다.

| 구성 | 역할 |
|---|---|
| `navigation.py`의 NavSDGDemo | 목적지 배치, 거리 감지, 촬영 상태를 관리합니다. |
| Nova Carter 자산 | 내장 OmniGraph로 목표 위치를 향해 움직입니다. |
| Dolly와 YCB 소품 15개 | 촬영할 목적지 주변을 구성합니다. |
| left_sensor·right_sensor | 로봇 전방의 좌·우 카메라, 각각 1024×1024입니다. |
| `environments.json` | Grid → Warehouse → Full Warehouse의 배경 순서를 정합니다. |

이 장면의 주행은 로봇 자산에 포함된 OmniGraph를 사용합니다. 이 주행 그래프에는 **충돌 회피 기능이 없습니다.** 목표를 향해 이동하다가 장애물에 막히면 캡처 거리 조건에도 도달하지 못할 수 있습니다. ROS 설치나 Nav2 노드를 실행하는 튜토리얼은 아닙니다. 이 제한은 [공식 예제의 Scenario](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_amr_navigation.html#scenario)에도 명시되어 있습니다.

## 1. 목적지 아홉 곳의 스테레오 데이터 생성하기

Isaac Sim 5.1 전체 설치, RTX GPU, 5.1 자산 라이브러리 접근이 필요합니다. 저장소 루트에서 실행하세요.

```bash
~/isaacsim/python.sh src/142_replicator_replicator_amr_navigation/run.py --headless --frames 9 --env-interval 3 --output /tmp/tutorial142-first
```

새 출력 폴더를 지정합니다. `--frames 9`는 **목적지 접근 사건 아홉 번**이며 물리 단계 아홉 번이 아닙니다. 기본 headless 실행은 최대 40000번 앱 갱신 안에서 생성 완료를 기다립니다. 로딩·주행이 끝나지 않으면 오류로 종료합니다.

GUI로 보려면 `--headless`를 빼세요. `--steps`를 생략한 GUI에는 생성 대기 횟수 제한이 없고 완료 후에도 창을 유지합니다. `--steps N`은 생성 중 앱 갱신의 상한이며 작업이 끝나면 바로 종료합니다. 저장 후 창을 N번 갱신하는 옵션과는 다릅니다.

### 준비할 자산

`get_assets_root_path()`가 찾는 루트 아래 다음 경로가 있어야 합니다.

- `/Isaac/Samples/Replicator/OmniGraph/nova_carter_nav_only.usd`
- `/Isaac/Props/Dolly/dolly.usd`
- `/Isaac/Props/YCB/Axis_Aligned_Physics`의 USD 목록
- `environments.json`의 세 `/Isaac/Environments/...` 경로

루트 주소만 읽히는 것과 하위 자산 목록·텍스처까지 열리는 것은 다릅니다. 특히 YCB 소품은 폴더 목록을 조회해 순환 선택하므로 개별 USD 파일 하나만 준비해서는 같은 구성이 되지 않습니다.

### 실행 결과 확인하기

완료 로그의 JSON은 `destinations`, `stereo_pngs`, `app_updates`를 출력합니다. 기본 성공 기준은 목적지 9곳과 RGB PNG 18개입니다. `app_updates`는 실행에서 실제 사용한 횟수로 고정값을 기대하지 마세요.

`left_sensor`, `right_sensor` 식별자와 프레임 번호를 맞춰 RGB를 짝지어 보세요. 두 이미지는 같은 순간을 로봇의 좌·우 시점에서 봅니다. 이 BasicWriter는 **RGB만 요청**하므로 깊이와 검출 라벨은 생성하지 않습니다. 스테레오 사진이 있다는 사실만으로 시차·깊이 계산까지 수행한 것은 아닙니다.

## 2. 거리 사건이 주행과 캡처를 연결하는 방식

### 코드에서 볼 부분

첫 목적지는 로봇으로부터 4 m 넘게 떨어진 후보를 고릅니다. 목적지의 dolly 위치와 로봇의 `/NavWorld/CarterNav/targetXform`을 같은 좌표로 설정합니다. 타임라인이 진행하면 현재 로봇과 dolly의 **XY 평면 거리**를 계산합니다.

```python
dist = (Gf.Vec2f(dolly_loc[0], dolly_loc[1])
        - Gf.Vec2f(carter_loc[0], carter_loc[1])).GetLength()
if dist < self._trigger_distance:
    self._timeline.pause()
    self._timeline_sub.unsubscribe()
```

첫 기준은 2 m, 다음 목적지부터는 1.75~2.5 m 범위에서 고릅니다. dolly 중심에 정확히 도착할 때까지 기다리는 것이 아닙니다. 높이 차이도 이 거리 조건에 포함하지 않습니다.

조건을 만족하면 타임라인을 멈추고 사건 구독을 잠시 해제합니다. 계속 같은 근접 상태를 읽어서 중복 촬영을 예약하지 않도록 하기 위해서입니다.

```python
rep.orchestrator.step(rt_subframes=16, delta_time=0.0)
```

시간을 추가하지 않은 상태에서 좌·우 render product를 함께 촬영합니다. 파일 쓰기 후 다음 dolly 위치·조명·소품 배치를 정하고 Play와 구독을 재개합니다. 화면에서 잠깐 멈추었다가 다음 목표로 움직이는 것은 이 순서에 따른 동작입니다.

### 카메라와 환경 확인하기

좌측 카메라의 정확한 prim 경로는 다음과 같습니다.

```text
/NavWorld/CarterNav/chassis_link/sensors/front_hawk/left/camera_left
```

우측은 `front_hawk/right/camera_right`입니다. 외부에서 로봇을 내려다보는 카메라가 아니라 로봇에 부착된 센서입니다. 두 센서에 별도 render product를 붙여 출력 식별자를 나눕니다.

기본 `--env-interval 3`에서는 첫 세 캡처가 Grid, 다음 세 캡처가 Warehouse, 마지막 세 캡처가 Full Warehouse입니다. `/Environment` 참조만 교체하며 로봇·dolly와 캡처 흐름은 이어집니다.

`--use-temp-rp`는 이름과 달리 매 목적지에서 render product를 새로 만들고 버리는 방식이 아닙니다. 이 구현에서는 주행 중 센서 렌더 업데이트를 끄고 촬영할 때 다시 켭니다. 센서 렌더 부하를 줄여도 저장할 목적지 수와 좌·우 해상도는 유지합니다.

## 3. 주행 단계와 캡처 사건 정리

```text
dolly와 소품 배치 → targetXform 갱신 → 로봇 주행
    → XY 거리 조건 만족 → Pause·구독 해제
    → 좌/우 동시 캡처 → 다음 목적지·필요한 배경 교체 → Play
```

`--frames`는 이 흐름의 촬영 횟수이고, `--steps`는 완료를 기다리는 앱 갱신 예산입니다. 캡처 한 번에 카메라 두 대가 있으므로 RGB 두 장이 생깁니다. 앱 갱신 횟수에 2를 곱해 이미지 장수를 계산하는 것은 맞지 않습니다.

목적지에 접근하고 파일 개수가 맞는다는 것은 이 수집 흐름의 확인입니다. 장애물을 피하는 주행이 필요하다면 충돌 회피를 갖춘 별도의 제어 구성이 필요합니다. 현재 예제의 출력 개수로 그 기능을 평가할 수는 없습니다.

## 4. 간단한 확인 실험

첫 명령에서 **`--env-interval`만 3에서 1로 바꾸어** 새 출력 경로에 실행하세요. 목적지 수는 9로 유지합니다.

이미지는 계속 18장이어야 합니다. 달라지는 것은 배경 순서입니다. 세 장씩 묶이는 대신 Grid → Warehouse → Full Warehouse가 목적지마다 바뀌며 반복됩니다. 같은 프레임의 좌·우 사진에서는 동일한 환경이 보여야 합니다.

## 실행할 때 막히면

- **`Navigation did not finish within --steps`**: 자산 로딩과 실제 목표 접근 여부를 먼저 확인하세요. 한도를 늘리는 것만으로 잘못된 목표나 주행 문제를 해결할 수는 없습니다.
- **카메라 prim을 찾지 못함**: `nova_carter_nav_only.usd`와 전방 센서 경로를 확인하세요. 다른 Carter 자산의 경로가 같다고 가정하지 마세요.
- **YCB 목록 조회 오류**: 소품 폴더의 접근 권한과 목록 조회 가능 여부를 확인하세요.
- **주행 중 센서 화면이 갱신되지 않음**: `--use-temp-rp`를 사용했다면 의도된 상태일 수 있습니다. 실제 촬영 결과를 확인하세요.
- **PNG가 18개보다 부족함**: 목적지 완료 로그와 좌·우 짝을 확인하세요. 창을 중간에 닫은 실행은 전체 완료가 아닙니다.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Randomization in Simulation – AMR Navigation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_amr_navigation.html)에 대응합니다. 포함한 NVIDIA 구현의 출처는 [NOTICE.txt](NOTICE.txt)에 있습니다. 로컬 런처는 유한한 목적지 수와 출력 검사를 추가합니다.

[VERIFICATION.md](VERIFICATION.md)는 문법·도움말·JSON 확인을 기록하며 `tutorial.json`은 `not_run`입니다. 실제 로봇 주행·스테레오 내용·환경 전환은 이번 문서 개정에서 실행하지 않았습니다. 제시한 장수와 상태 변화는 해당 실행에서 확인할 기준입니다.
