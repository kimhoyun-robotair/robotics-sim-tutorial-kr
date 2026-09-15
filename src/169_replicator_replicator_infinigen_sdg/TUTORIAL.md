# 169. t040 · Infinigen 식당에서 물체 데이터셋 만들기

권장 학습 순서 **169** · 고급 데이터 생성과 외부 시스템 통합 · 출처 ID `t040`

식탁이 있는 방을 바꾸면서 공중에 있는 물체와 바닥에 놓인 물체를 두 카메라로 촬영한다. 같은 장면에서 RGB/의미 분할과 경계 상자 시각화를 함께 저장한다. 방을 만드는 Infinigen과 촬영하는 Isaac Sim은 별도 프로그램이며, 둘 사이의 파일 계약은 **USD 환경과 그 텍스처**이다.

이 패키지는 공식 설치본의 `standalone_examples/replicator/infinigen/infinigen_sdg.py`를 실행하는 **native workflow**다. `run.py`가 설정·경로를 검사하고 이 패키지의 `sdg_config.json`을 전달한다. 원본의 복잡한 충돌 처리, 단위 조정, 카메라 무작위화 코드를 다른 로컬 튜토리얼에 의존하지 않고 사용할 수 있다. 사용자 저장소의 공통 모듈은 사용하지 않는다. Infinigen 생성기나 NVIDIA 샘플 자산을 패키지에 포함한 것은 아니다.

## 준비

- Linux의 Isaac Sim **5.1.0** 설치 경로에 `python.sh`와 위 standalone example 및 `infinigen_sdg_utils.py`가 있어야 한다. RTX GPU와 지원 드라이버, GUI 표시 환경이 필요하다. 공식 예제는 창을 생성한다.
- Isaac Sim asset root에서 `/Isaac/Samples/Replicator/Infinigen/dining_rooms/`, YCB 소품, Office 소품을 읽을 수 있어야 한다. 첫 실행 시 원격 자산을 불러올 수 있다. 에셋을 로컬로 준비했다면 Isaac Sim의 asset root 설정으로 연결한다.
- 처음에는 NVIDIA가 제공한 Infinigen 방으로 실행하면 된다. 방을 직접 만들 때만 Infinigen 별도 설치가 필요하다. [공식 설치 안내](https://github.com/princeton-vl/infinigen/blob/main/docs/Installation.md)의 환경을 만들고 [Hello Room](https://github.com/princeton-vl/infinigen/blob/main/docs/HelloRoom.md)에서 요구하는 리소스를 준비한다. 이 외부 프로젝트의 `main`은 5.1 문서의 시점에 고정된 버전이 아니므로 사용한 checkout commit을 함께 기록한다.

## 실행

이 디렉터리만 원하는 곳에 복사해도 같은 명령을 쓸 수 있다. 아래에서 Isaac Sim 경로만 자신의 설치에 맞춘다.

```bash
cd /path/to/169_replicator_replicator_infinigen_sdg
python3 run.py --help
python3 run.py --isaac-root "$HOME/isaacsim" --check
python3 run.py --isaac-root "$HOME/isaacsim" --output output/first
```

`--check`는 JSON·설치 파일 검사다. GPU와 원격 자산 접근 성공을 의미하지 않는다. 마지막 명령은 실제 GPU 작업을 시작한다. 이미 존재하는 출력 경로는 거부한다. 실행 설정의 완전한 사본을 `output/first/resolved_config.json`에 남기며 writer 별 디렉터리를 분리한다. `--steps`를 생략하면 설정한 촬영과 파일 저장을 끝낸 뒤 사용자가 닫을 때까지 GUI를 유지한다. `--steps 120`은 저장 후 GUI를 120회 업데이트하고 종료하며. `--steps`에는 양의 정수를 지정한다. 촬영 수는 `--captures`로 별도 지정하므로 창을 오래 열어도 이미지가 계속 생성되지 않는다. `--headless`는 창 없이 설정한 촬영만 끝내고 종료한다. 기존 `--keep-open`은 호환용으로 남아 있으며 명시한 `--steps`가 우선한다.

## 단계별 실습

1. `sdg_config.json`을 열고 `capture.total_captures=6`, `num_cameras=2`를 확인한다. 하나의 capture는 모든 카메라가 같은 장면을 촬영하는 작업이다. 따라서 카메라별 RGB는 합계 12장이 예상된다. segmentation 및 시각화 이미지를 포함한 전체 파일 개수와 혼동하지 않는다.
2. `num_floating_captures_per_env=1`, `num_dropped_captures_per_env=2`이므로 방 하나당 세 번 촬영하고 다음 방으로 넘어간다. 콘솔의 `Loading environment`와 floating/dropped 진행을 읽는다. 6 capture라면 두 번의 방 배치가 필요하다. 동일한 방만 공급하면 그 방을 순환 재사용한다.
3. `labeled_assets.auto_label`의 `036_wood_block.usd`는 정규식 `^\d+_`가 숫자 접두사를 제거하여 `wood_block` 클래스를 만든다. `manual_label`의 pudding box는 지정한 `pudding_box` 클래스를 쓴다. 이는 파일 이름/클래스 이름을 구분하는 실습이다.
4. `shape_distractors`는 구·원뿔 등 기하 도형, `mesh_distractors`는 책 USD를 배치한다. distractor는 배경 방해물이며 target class를 붙이지 않는다. 이미지에 물체가 보인다고 모두 정답 객체가 되는 것은 아니다.
5. 출력의 `00_BasicWriter`에서 RGB와 colorized semantic segmentation을 비교한다. `01_DataVisualizationWriter`에서는 RGB 위 2D 상자와 normal 이미지 위 3D 상자를 비교한다. 카메라별 하위 구조는 writer가 결정하므로 파일 이름의 카메라 구분도 확인한다.
6. `--steps`를 생략한 GUI 실행에서는 Stage 창의 `/Environment`, `/Cameras/cam_0`, `/Cameras/cam_1`을 선택한다. `debug_mode=true`는 천장 일부를 가리고 위에서 장면을 관찰하기 쉽게 한다. 저장된 카메라 영상은 viewport의 자유 카메라와 다를 수 있다.

## 방 직접 생성 및 연결

`generate_rooms.py`는 실제 Infinigen 환경의 Python으로 `generate_indoors`와 `infinigen.tools.export`를 차례로 실행한다. 기존 출력은 덮어쓰지 않는다. Isaac Sim Python 환경에서 Blender/Infinigen을 가져오려고 하지 않는다.

```bash
python3 generate_rooms.py --infinigen-root /path/to/infinigen \
  --python /path/to/infinigen-environment/bin/python --seeds 1 2 --output rooms/run1
```

생성 단계는 seed, `coarse`, `fast_solve.gin`, `singleroom.gin`, `DiningRoom` 제한을 사용한다. export 단계의 `-f usdc -r 1024 --omniverse`는 binary USD와 1024 해상도 텍스처, Omniverse 호환 출력을 요구한다. 출력되는 USDC 목록에서 방 전체를 담은 루트 stage를 선택한다. 개별 가구 파일을 방으로 지정하지 않는다. 전체 export 폴더를 보관해야 texture reference가 유지된다.

```bash
python3 run.py --isaac-root "$HOME/isaacsim" \
  --environment /absolute/path/to/exported-room-root.usdc --output output/custom-room
```

`--environment`를 반복하면 여러 방을 공급한다. 실행기는 로컬 절대 경로를 `file://` URI로 변환한다. 설치본 helper는 URL scheme이 없는 경로를 NVIDIA asset root에 붙이므로 이 변환이 필요하다. 원본은 `/Environment` 아래 이름에 `TableDining`이 들어가는 prim에서 작업 영역을 찾는다. 생성된 방의 Stage 트리에서 그 prim이 존재하는지 확인한다. 임의의 빈 USD나 다른 종류의 방을 넣으면 식탁을 중심으로 한 촬영 조건이 성립하지 않는다.

## API와 장면 개념

| 코드/설정 | 의미와 이 실습에서의 역할 |
|---|---|
| USD Stage / Prim | Stage는 전체 장면, prim은 장면 트리의 객체다. USD reference는 환경/소품을 합성해 불러온다. |
| Collision / Rigid Body | collider는 접촉 형태, rigid body는 물리 운동 대상이다. 중력 확률 0.25는 해당 자산 일부를 부유 상태로 유지한다. |
| `get_usd_paths`, `load_env` | 설치본 helper가 폴더/파일에서 USD를 수집하고 `/Environment`에 다음 방을 불러온다. |
| `get_matching_prim_location` | `TableDining` 위치를 찾아 물체 배치와 조명의 기준점으로 쓴다. |
| `rep.create.render_product` | Camera prim과 해상도를 연결하는 렌더 출력이다. Writer는 camera 자체가 아니라 render product에 연결된다. |
| `BasicWriter`, `DataVisualizationWriter` | 첫 writer는 실제 학습용 이미지/라벨을, 둘째는 경계 상자 검토 이미지를 저장한다. |
| `rep.utils.send_og_event` | 설치본 5.1은 dome light와 distractor 색상 randomizer의 custom OmniGraph event를 보낸다. 장면 변화 시점과 파일 저장 시점을 분리한다. |
| `run_simulation(4)` / `(200)` | 첫 짧은 물리는 겹침을 완화하고, 뒤의 긴 물리는 물체가 떨어져 정착하도록 한다. |
| `rep.orchestrator.step(delta_time=0.0)` | 물리 시간을 진행하지 않고 현재 배치를 촬영한다. `rt_subframes`는 렌더 안정화를 위한 반복이며 새 물리 표본 수가 아니다. |
| `wait_until_complete()` | 비동기 저장이 끝날 때까지 기다려 종료 시 파일 누락을 방지한다. |

5.1 문서 설명 일부의 helper 이름/trigger 예시는 설치본과 차이가 있다. 이 패키지는 위에 명시한 설치본 실행 경로와 실제 `send_og_event` 흐름을 기준으로 실행한다. `config.update()`는 최상위 사전을 교체하므로 일부 키만 남긴 `capture` 블록을 넣으면 원본의 내부 fallback이 적용된다. 제공한 완전한 설정에서 값을 하나씩 바꾸는 편이 관찰하기 쉽다.

## 한 변수 실험과 문제 해결

`capture.path_tracing`만 `true`로 바꾸고 새 출력 경로에 재실행한다. RGB의 간접광/그림자와 촬영 시간을 비교한다. 카메라 수·해상도·물체 수를 동시에 바꾸지 않는다. `debug_mode=true`에서는 설치본이 난수 seed를 10으로 설정하므로 비교의 무작위성이 줄어든다.

- `StopIteration` 또는 환경 목록이 비었으면 asset root 접근과 Infinigen 폴더를 확인한다. 로컬 방 사용 시 `--environment`는 실제 루트 USD여야 한다.
- 식탁 밖을 찍으면 `TableDining` prim 이름·위치와 USD 단위를 확인한다. 설치본의 metrics assembler는 센티미터/미터 차이를 처리하지만 모든 사용자 export 구조를 보장하지 않는다.
- 검은 이미지/재질 누락은 USD 옆 텍스처 누락 또는 asset 연결 문제부터 확인한다. subframe 증가가 깨진 파일 경로를 고치지는 않는다.
- 물체가 계속 떠 있으면 `gravity_disabled_chance`를 확인한다. 모든 물체가 떨어지는 비교는 해당 값을 0으로 바꿔서 한다.
- `--help`, compile, `--check`만 통과한 상태는 데이터 생성 검증이 아니다. 이 패키지 작성 시 GPU 캡처와 Infinigen 외부 생성은 실행하지 않았다.

`native_runner.py`는 이 패키지 안에서만 사용하는 실행 어댑터다. 설치된 예제의 `SimulationApp.close()` 요청을 잠시 보류해, 유한한 생성 작업과 저장이 성공한 뒤 창을 관찰할 시간을 제공한다. 기본 `headless=False`를 명시하며 `--headless`로만 창을 끈다. 작업 중 오류가 발생하면 관찰 대기 없이 정리하고 오류를 전달한다. Isaac Sim 설치 파일은 수정하지 않는다.

## 출처

- [Isaac Sim 5.1 · 원본 튜토리얼](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_infinigen_sdg.html)
- [환경 생성](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_infinigen_sdg.html#generating-infinigen-environments), [설정 파라미터](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_infinigen_sdg.html#configuration-parameters), [물리와 촬영](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_infinigen_sdg.html#running-physics-simulation)
- API 대조: Isaac Sim 5.1 설치본 `standalone_examples/replicator/infinigen/infinigen_sdg.py`, `infinigen_sdg_utils.py`. 이 문서는 해당 흐름을 독립적으로 설명한 한국어 실습이며 공식 문서 전체 복제본이 아니다.
