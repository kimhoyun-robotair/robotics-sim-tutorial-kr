# 144. YAML 한 장이 큐브 낙하와 학습 데이터가 되기까지

## 이번에 배우는 것

**여섯 큐브의 초기 상태를 무작위로 정하고, 물리 계산을 거친 장면에서 영상과 정답 데이터를 함께 만듭니다.**

합성 데이터를 만들려면 물체를 화면에 보이게 하는 것만으로는 부족합니다. 어디에 놓을지, 얼마나 움직인 뒤 촬영할지, 어떤 물체에 정답을 붙일지까지 정해야 합니다. Isaac Sim Replicator Object, 줄여서 **IRO**는 이 규칙을 YAML 파일로 받아 장면을 구성합니다.

| 이 실습의 요소 | 담당하는 일 |
|---|---|
| `scene.yaml` | 여섯 큐브의 색·초기 자세·물리·카메라·출력 규칙 |
| `run.py` | 출력 경로를 만들고 IRO에 넘길 `prepared.yaml` 준비 |
| `floor`의 `physics: collision` | 움직이지 않으면서 큐브를 받치는 바닥 |
| `subject`의 `physics: rigidbody` | 중력과 충돌로 움직이는 큐브 |
| `tracked: true` | 해당 물체를 정답 수집 대상으로 지정 |

이 장면은 **Y축이 위쪽이고, 길이 1단위는 1 cm**입니다. 기본 큐브의 한 변은 100 cm이며 배율 0.6을 적용하면 60 cm가 됩니다. 미터와 Z-up을 쓰는 로봇 예제의 좌표를 그대로 옮기면 크기와 낙하 방향이 달라집니다.

## 1. 설정을 준비하고 장면 실행하기

Isaac Sim 5.1, NVIDIA RTX GPU와 호환 드라이버, `isaacsim.replicator.object` 확장이 필요합니다. 아래 명령은 저장소 루트에서 시작합니다. 설치 경로가 다르면 `~/isaacsim`을 바꾸세요.

```bash
cd src/144_events_replicator_object
~/isaacsim/python.sh run.py --frames 3
```

터미널에 `configuration:`, `output:`, `native command:`가 출력됩니다. 이 호출은 **YAML 준비 후 종료**합니다. `output/<UTC시간>-<고유값>/prepared.yaml`이 생겨도 아직 큐브를 떨어뜨리거나 이미지를 촬영한 것은 아닙니다.

이번에는 같은 폴더에서 GUI를 엽니다.

```bash
~/isaacsim/python.sh run.py --launch --frames 3
```

1. 이번 호출이 출력한 `configuration:`의 절대 경로를 복사합니다. 호출마다 새 출력 폴더가 생깁니다.
2. **Tools > Action and Event Data Generation > Object SDG**를 엽니다. 메뉴가 없으면 **Window > Extensions**에서 `isaacsim.replicator.object`를 확인하세요.
3. **Description File**에 복사한 `prepared.yaml` 경로를 넣습니다.
4. **Initialize scene randomization**으로 초기화하고 **Randomize scene**으로 다른 초기 배치를 살펴봅니다.
5. **Simulate**를 눌러 세 프레임을 생성합니다. 기존 stage를 교체하므로 편집 중인 장면은 먼저 저장하세요.

미리보기와 저장은 별도 동작입니다. 창 없이 데이터를 생성하고 종료하려면 다음 명령을 사용하세요.

```bash
~/isaacsim/python.sh run.py --launch --headless --frames 3
```

GUI는 생성 후에도 창을 유지합니다. `--steps`는 데이터 수가 아니라 앱 업데이트 횟수 제한이며, 짧게 지정하면 로딩 중 종료될 수 있습니다. 이 실습에서는 생략하세요. 설치 위치를 바꾼 경우에는 Python 실행 경로와 함께 `--isaac-root /설치/경로`도 지정합니다.

### 설정에서 볼 부분

`scene.yaml`의 `subject`에서 다음 항목을 찾아보세요. 전체 설정 중 낙하에 필요한 부분만 발췌했습니다.

```yaml
count: 6
physics: rigidbody
transform_operators:
- translate:
    distribution_type: range
    start: [-180, 130, -100]
    end: [180, 230, 100]
- rotateXYZ:
    distribution_type: range
    start: [-30, -180, -30]
    end: [30, 180, 30]
- scale: [0.6, 0.6, 0.6]
```

`count`는 여섯 개체를 만듭니다. `translate`의 세 성분은 X·Y·Z 순서이며, 중심의 초기 Y 높이는 130~230 cm입니다. 회전 범위는 도 단위입니다. 위치와 회전을 함께 바꾸므로 어떤 큐브는 평평한 면으로, 어떤 큐브는 모서리 쪽으로 먼저 닿습니다.

장면 전역의 `gravity: 981`은 981 cm/s², 즉 9.81 m/s²입니다. `simulation_time: 1.5`만큼 물리를 계산한 다음 촬영합니다. 마찰 `friction: 0.6`과 선형·각 감쇠 값 1은 접촉 후 미끄러짐과 운동에 영향을 줍니다. **1.5초가 지났다는 사실만으로 모든 큐브가 완전히 정지했다고 판단하지는 마세요.**

## 2. 생성된 파일을 같은 장면으로 연결하기

`output:`으로 표시된 폴더를 엽니다. 기본 설정은 한 카메라로 세 장면을 촬영합니다.

### 실행 결과 확인하기

| 위치 | 확인할 내용 |
|---|---|
| `images/` | 640×480 RGB 영상, 바닥에 닿거나 아직 움직이는 큐브 |
| `labels/`, `3d_labels/` | 영상의 2D 경계 상자와 3D 정답 |
| `segmentation/` | 물체 영역을 구분하는 분할 결과 |
| `descriptions/` | 촬영 시점의 장면을 다시 구성할 설정 |

파일명은 `frame_11_default_camera.jpg`처럼 seed와 카메라 이름을 연결합니다. description은 카메라별 사진이 아니라 장면 전체를 저장하므로 `frame_11_GLOBAL.yaml`과 짝을 맞춥니다.

바닥에도 `tracked: true`가 있으므로 라벨 수를 무조건 6이라고 기대하면 안 됩니다. 큐브끼리 가려지는 경우도 있습니다. RGB에서 보이는 물체와 해당 경계 상자·분할 영역을 하나씩 대조해 보세요.

**저장 description의 변환은 초기 낙하 설정과 다릅니다.** IRO 0.4.13은 촬영 직전 월드 변환을 `global_transform`과 단일 `transform` 연산으로 기록합니다. 따라서 원래의 `translate`나 `rotateXYZ` 난수 범위를 이 파일에서 다시 찾는 대신, `prepared.yaml`의 초기 규칙과 저장된 최종 위치를 비교하세요. 변환 행렬의 마지막 행 앞 세 값이 X·Y·Z 이동입니다. 정착한 큐브도 자세와 쌓임에 따라 중심 높이가 달라집니다.

한 장면을 다시 구성하려면 description의 실제 경로를 사용합니다.

```bash
~/isaacsim/python.sh run.py --config /절대/출력경로/descriptions/frame_11_GLOBAL.yaml --frames 1 --launch --headless
```

복원용 description은 물리 속성을 제거하고 촬영 당시 배치를 저장합니다. 이 재실행은 원래 난수에서 다시 낙하시키는 실험과 목적이 다릅니다.

### GUI에서 한 영역의 물체 숨겨 보기

Object SDG의 **Scene Editing**은 현재 Stage를 살펴보는 보조 기능입니다. GUI 실행에서 장면을 초기화한 뒤 다음 순서로 확인해 보세요.

1. **Create > Mesh > Cube**로 영역 표시용 큐브를 추가합니다.
2. 이동과 배율을 조정해 기존 큐브 두 개의 **중심**을 포함하는 상자를 만듭니다. 영역 표시용 큐브는 회전시키지 마세요.
3. 영역 표시용 큐브를 선택한 채 **Scene Editing > Toggle visibility of selected region**을 누릅니다.
4. 영역 안에 있던 물체가 숨겨지는지 확인하고, 같은 버튼을 다시 눌러 되돌립니다.

설치 IRO 0.4.13은 선택한 큐브의 이동·배율로 축에 나란한 상자 범위를 만들고, 다른 prim의 원점이 그 안에 있는지 검사합니다. 물체 외곽이 조금 걸친다는 이유만으로 선택되는 방식은 아닙니다. 장면 계층의 여러 prim이 검사 대상이므로 부모·자식의 가시성도 함께 살펴보세요. 선택한 영역 표시용 큐브 자체는 토글 대상에서 제외됩니다.

이 조작은 현재 Stage의 가시성을 바꿉니다. `tracked`를 바꾸거나 원본 YAML에 제외 규칙을 저장하지 않습니다. **Simulate**는 입력 description으로 장면을 다시 구성하므로, 숨기기 조작이 다음 데이터 생성에도 유지된다고 기대하지 마세요.

## 3. 초기 규칙과 촬영 결과의 관계 정리

```text
scene.yaml의 확률 규칙
    → run.py가 경로 표식을 치환한 prepared.yaml
    → IRO가 각 큐브의 색·초기 위치·회전 선택
    → 강체 속도 초기화와 1.5초 물리 계산
    → 최종 월드 변환 기록
    → 카메라 촬영과 정답 저장
```

`@OUTPUT@`는 준비 도구가 바꾸는 경로 표식입니다. `$[seed]`는 IRO가 장면을 만들 때 해석하는 매크로입니다. 두 처리를 구분하면 준비된 YAML에 매크로가 남아 있는 이유와, description에는 선택된 값이 들어 있는 이유를 이해할 수 있습니다.

## 4. 간단한 확인 실험

`scene.yaml`을 `before_fall.yaml`로 복사하고 **`simulation_time`만 1.5에서 0으로** 바꿔 보세요.

```bash
~/isaacsim/python.sh run.py --config before_fall.yaml --launch --headless --frames 3
```

같은 seed의 RGB와 `global_transform`을 비교합니다. 물리 시간이 0인 실행에서는 초기 공중 배치를, 1.5초 실행에서는 낙하·충돌을 거친 배치를 관찰하는 것이 목표입니다. 출력 폴더가 서로 다르므로 결과를 덮어쓰지 않고 비교할 수 있습니다.

## 실행할 때 막히면

- **`prepared.yaml`만 있고 RGB가 없음**: 준비 명령만 실행했는지 확인하세요. GUI의 **Simulate** 또는 `--launch --headless`가 실제 생성 단계입니다.
- **큐브가 예상과 다른 방향으로 떨어짐**: 이 장면의 높이는 Z가 아니라 Y입니다. 원본의 중력·좌표 규칙을 확인하세요.
- **큐브가 튀거나 일부가 안 보임**: 초기 난수 배치가 서로 겹칠 수 있습니다. 초기 미리보기와 최종 화면을 비교해 충돌과 카메라 밖 이동을 구분하세요.
- **복원 실행에서 큐브가 다시 낙하하지 않음**: description은 촬영 당시의 배치를 복원합니다. 낙하를 반복하려면 `scene.yaml`을 선택하세요.
- **`ModuleNotFoundError: yaml`**: PyYAML이 포함된 Isaac Sim `python.sh`로 실행하세요.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Object Simulation and Synthetic Data Generation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/tutorial_replicator_object.html)에 대응합니다. 공식 파이프라인을 외부 물체 모델 없이 따라갈 수 있도록 기본 도형 여섯 개로 구성했습니다. 모델 학습과 배포는 포함하지 않습니다.

장면 단위와 description 저장 방식은 설치 IRO 0.4.13을 기준으로 설명했습니다. 위 결과는 실행 시 확인할 기준이며, 실제 RTX 렌더링·물리 검증 상태는 `tutorial.json`의 `not_run`을 참고하세요.
