# 132. Replicator 도구를 한 장면으로 연결하기

권장 학습 순서 **132** · Replicator 합성 데이터 기초와 확장 · 출처 ID `t035`

이 실습은 같은 모양의 상자 두 개를 만들되 왼쪽에만 `carton` 의미 라벨을 붙입니다. RGB에는 둘 다 보이고, 의미 분할·검출 정답에는 라벨이 있는 물체가 포함되는 차이를 관찰합니다. 공식 Overview의 다섯 도구를 작은 로컬 장면에서 연결한 입문용 구현입니다.

## GUI 실행과 종료

GUI에서 `--steps`를 생략하면 정해진 데이터 생성과 저장을 마친 뒤 사용자가 창을 닫을 때까지 장면을 유지합니다. 양수 `--steps N`은 **생성 완료 후 GUI를 관찰하는 app update 횟수**입니다. 생성 작업 자체나 데이터 프레임 수를 제한하는 값은 아니며, `--frames` 등으로 요청한 데이터가 무한히 늘어나지 않습니다. `--headless`는 관찰 대기 없이 기존 유한 작업을 마치면 종료합니다.

이 패키지 폴더에서 다음과 같이 실행합니다. 설치 경로는 자신의 환경에 맞추고, 이미 사용한 출력 폴더는 새 경로로 바꿉니다.

```bash
~/isaacsim/python.sh run.py --output output/gui
```

## 준비와 실행

Isaac Sim **5.1.0** 전체 설치, 지원되는 NVIDIA RTX GPU/드라이버, GUI 실습 시 데스크톱이 필요합니다. 이 패키지는 외부 USD 자산이나 다른 로컬 패키지를 쓰지 않습니다. 일반 Python은 `--help`에만 사용하고 렌더링은 설치본의 `python.sh`로 실행합니다.

```bash
export ISAAC_SIM_PATH="$HOME/isaacsim"
cd src/132_replicator_replicator_overview
"$ISAAC_SIM_PATH/python.sh" run.py
# 화면 없이 데이터만 생성할 때; 기존 output을 보존하도록 새 경로 사용
"$ISAAC_SIM_PATH/python.sh" run.py --headless --frames 3 --output output_headless
```

명령은 새 출력 폴더만 허용합니다. 기본 실행은 세 번 캡처하고 창을 직접 닫을 때까지 유지합니다. 기존 `--interactive` 옵션은 호환용이며 명시한 `--steps` 제한을 무시하지 않습니다. `output/labels.usda`는 검사할 수 있는 텍스트 USD입니다.

## 직접 해보기

1. Stage에서 `/World/Labeled`와 `/World/Unlabeled`를 각각 선택합니다. 둘의 크기와 높이는 같고 x 위치만 다릅니다. USD의 prim은 장면 트리의 한 항목이며 경로는 해당 항목의 주소입니다.
2. **Tools > Replicator > Semantics Schema Editor**를 엽니다. `/World/Labeled`의 class 값 `carton`을 확인합니다. `/World/Unlabeled`에는 class가 없습니다. 오른쪽 물체에도 `carton`을 추가한 뒤 다시 기록하면 두 물체의 정답이 생깁니다. 동일 class는 동일 물체 인스턴스를 의미하지 않습니다.
3. Viewport의 **Synthetic Data Visualizer** 아이콘에서 RGB 다음 Semantic Segmentation을 선택합니다. 라벨과 RGB 색은 별개입니다. 라벨 변경 후 렌더를 갱신합니다. Cross Correspondence는 두 카메라의 대응 관계가 필요한 별도 센서라 이 단일 카메라 실습의 성공 기준에 넣지 않습니다.
4. **Tools > Replicator > Synthetic Data Recorder**를 엽니다. **Add New Render Product**로 카메라를 추가하고 Stage의 Camera prim 경로를 입력합니다. 해상도는 512×512, RGB와 Semantic Segmentation, Number of Frames는 3으로 둡니다. Output은 이 패키지 아래 새 폴더로 지정하고 Start를 누릅니다.
5. `output`의 RGB PNG, 의미 분할 이미지와 라벨 JSON, 2D bounding box 배열을 비교합니다. 색으로 보이는 상자와 학습 정답에 포함된 상자는 다를 수 있습니다.
6. YAML 방식을 체험하려면 **새 장면**에서 `workflow.yaml`을 엽니다. 파일의 `output_dir`를 이 패키지 아래 **아직 없는 절대경로**로 먼저 변경합니다. 기본 예시 경로를 그대로 여러 번 쓰면 이전 데이터와 충돌할 수 있습니다. **Tools > Replicator > Replicator YAML**에서 이 YAML을 불러오고 생성/실행합니다. 세 프레임 동안 carton의 z 회전만 달라집니다. YAML 파서가 `create.camera`, `writers.get`, `trigger.on_frame`을 Replicator API 호출로 연결합니다.

## 코드와 개념 해설

`SimulationApp`은 Kit와 렌더러의 수명을 관리하므로 `omni`나 `pxr`를 import하기 전에 생성합니다. `UsdGeom.SetStageMetersPerUnit(..., 1)`은 숫자 1을 1m로 해석하도록 기록하고 z-up은 중력/높이 축을 명확히 합니다. `add_labels(..., instance_name="class")`는 학습용 class 라벨을 prim에 작성합니다.

Camera prim은 투영 조건을 정의합니다. `rep.create.render_product`는 그 카메라를 어떤 해상도로 렌더할지 정의합니다. **Annotator**는 렌더 결과에서 RGB·분할·상자 같은 데이터를 만들고 **Writer**는 annotator 결과를 파일로 보냅니다. **OmniGraph**는 이러한 처리와 trigger를 연결하는 실행 그래프입니다. YAML, GUI Recorder, Python은 같은 SDG 개념에 접근하는 서로 다른 입력 방식입니다.

`set_capture_on_play(False)`로 타임라인 Play와 파일 기록을 분리했습니다. `step(delta_time=0.0)`은 시뮬레이션 시간을 멈춘 상태의 캡처입니다. `wait_until_complete()`는 비동기 디스크 쓰기가 끝날 때까지 기다리며 writer를 detach한 후 render product를 destroy합니다. `.usda`는 장면 설명이고 PNG/JSON은 해당 장면을 관찰한 결과라 역할이 다릅니다.

## 확인과 한 가지 실험

성공 기준은 RGB에 두 상자가 보이고 첫 실행의 의미 정답에는 `carton`이 있는 상자만 포함되는 것입니다. **라벨 하나만** 추가하고 카메라·조명·해상도는 유지해 다시 녹화합니다. 두 캡처의 label mapping과 bounding box 개수를 비교합니다. 왼쪽/오른쪽 화면 위치는 카메라 방향에 따라 달라지므로 반드시 prim 경로로 구분합니다.

메뉴가 없으면 Window > Extensions에서 `isaacsim.replicator.synthetic_recorder`, `omni.replicator.replicator_yaml`과 Semantics 관련 확장을 검색해 활성화합니다. RGB가 검으면 카메라 경로와 조명을 확인합니다. 상자는 보이는데 bounding box가 비면 class 라벨과 카메라 시야를 확인합니다. `--help`와 문법 검사는 렌더·GUI 성공을 증명하지 않으며 실제 실행 상태는 `tutorial.json`을 따릅니다.

## 출처와 버전

이 해설은 NVIDIA Isaac Sim **5.1.0** 문서와 해당 설치본을 기준으로 새로 작성했습니다. 원문의 전체 문장을 번역 복제한 것이 아니라 해당 워크플로를 독립적으로 실습하도록 설명했습니다.

- [공식 Overview](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_overview.html)
- [the semantics schema editor](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_overview.html#the-semantics-schema-editor)
- [the synthetic data visualizer](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_overview.html#the-synthetic-data-visualizer)
- [the synthetic data recorder](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_overview.html#the-synthetic-data-recorder)
- [replicator yaml](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_overview.html#replicator-yaml)
- [getting started scripts](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_overview.html#getting-started-scripts)
