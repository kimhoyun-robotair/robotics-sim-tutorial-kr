# 138. 가까이서 찍는 물체 데이터셋에 가림과 움직임 더하기

## 이번에 배우는 것

**표적 주변에 방해 물체를 배치하고, 물리·카메라·모션 블러가 합쳐진 촬영 흐름을 이해합니다.**

137번은 창고의 물체 관계를 넓게 보았습니다. 이번에는 작은 표적을 가까이서 촬영합니다. 카메라가 표적을 바라보더라도 다른 물체에 가리거나 화면 가장자리에서 잘릴 수 있습니다. 이런 다양한 관찰 조건을 만드는 것이 물체 중심 데이터 생성의 핵심입니다.

| 기본 구성 | 값과 의미 |
|---|---|
| 표적 | `pudding_box`, `mustard_bottle` 각 3개 |
| 방해 물체 | 기본 도형 40개와 창고 메시 12개 |
| 작업 공간 | 4×4×3 m, 보이지 않는 충돌 벽으로 둘러쌉니다. |
| 카메라 | 2대, 각각 512×512 |
| 캡처 | 6회, BasicWriter의 RGB·분할·2D box·깊이 |
| 실행 파일 | 런처 `run.py`, 본체 `object_based_sdg.py`, 관련 `_utils.py` |

`floating=true`인 표적도 움직입니다. 이 설정은 중력을 끄며 충돌과 속도까지 제거하지는 않습니다.

## 1. 실제 자산을 불러오기 전에 설정 확인하기

저장소 루트에서 일반 Python으로 먼저 확인하세요.

```bash
python3 src/138_replicator_replicator_object_based_sdg/run.py --check-config --headless --frames 6 --output /tmp/tutorial138-first
```

이 단계는 런처가 적용할 JSON을 출력합니다. 자산 다운로드, PhysX 계산, 렌더러 실행은 수행하지 않습니다. 실제 생성을 위해서는 Isaac Sim 5.1 전체 설치와 RTX GPU, 5.1 자산 라이브러리 접근이 필요합니다.

```bash
python3 src/138_replicator_replicator_object_based_sdg/run.py --isaac-sim ~/isaacsim --headless --frames 6 --output /tmp/tutorial138-first
```

런처가 설치의 `python.sh`로 로컬 본체를 실행합니다. 출력은 새 폴더여야 하며 `effective_config.json`에 요청 설정을 보관합니다. `--frames`가 JSON의 `num_frames`보다 우선합니다.

GUI를 보려면 `--headless`를 빼세요. 생성과 저장이 끝난 뒤 창을 닫을 때까지 유지합니다. `--steps N`은 **저장 후 GUI 갱신 한도**이며 캡처 수나 물리 단계 수가 아닙니다.

### 설정에서 볼 부분

```json
"num_cameras": 2,
"camera_distance_to_target_min_max": [0.25, 0.75],
"camera_look_at_target_offset": 0.15,
"simulation_duration_between_captures": 0.05
```

카메라는 임의의 표적을 골라 0.25~0.75 m 거리에서 바라봅니다. 주시점에 최대 0.15 m의 축별 오프셋을 더해 매번 물체 중심만 찍지 않도록 합니다. 카메라가 가까워질수록 표적이 크게 보이지만 잘림과 가림 가능성도 커집니다.

**현재 설정의 표적 배율 키에는 불일치가 있습니다.** `config.json`의 표적별 `scale_min_max`를 본체는 읽지 않고 `randomize_scale`을 읽습니다. 따라서 기본 실행에서 표적 배율은 `(1, 1)`을 사용합니다. `effective_config.json`에 범위가 보인다고 실제 적용된 것으로 판단하지 마세요. 방해 물체의 `shape_distractors_scale_min_max` 등은 별도 키입니다.

### 실행 결과 확인하기

완료했다면 기본 RGB는 6캡처 × 2카메라, 총 12장을 기준으로 확인합니다. `Actual PNG files`는 분할 PNG까지 셀 수 있으므로 RGB 개수와 다를 수 있습니다.

| 결과 | 해석할 내용 |
|---|---|
| RGB | 카메라별 표적 크기·가림·잘림을 비교합니다. |
| 의미 분할과 라벨 정보 | 보이는 표적이 `pudding_box`, `mustard_bottle`과 맞는지 확인합니다. |
| 2D tight box | 가려진 표적의 보이는 경계와 검출 정답을 비교합니다. |
| `distance_to_image_plane` | 카메라 광축 방향의 깊이입니다. RGB 색과 별도 수치입니다. |
| 콘솔 캡처 로그 | 프레임 번호·시뮬레이션 시간·무작위화 요청을 확인합니다. |

표적이 여섯 개라고 모든 이미지에서 여섯 개가 보여야 하는 것은 아닙니다. 이 실습은 가림을 만드는 구성도 포함하므로 각 이미지의 가시성과 라벨을 연결해 읽어야 합니다.

## 2. 물리 공간과 촬영 주기 따라가기

### 코드에서 볼 부분

표적을 만들 때 collider와 강체 설정을 추가한 뒤 라벨을 붙입니다.

```python
object_based_sdg_utils.add_colliders(prim)
object_based_sdg_utils.add_rigid_body_dynamics(prim, disable_gravity=floating)
add_labels(prim, labels=[label], instance_name="class")
```

Collider는 다른 물체와 부딪힐 표면을, 강체 설정은 물리 엔진이 움직일 대상을 정의합니다. 라벨은 이와 별개로 학습용 종류를 나타냅니다. 화면에 안 보이는 작업 공간의 벽도 collider가 유지되므로 물체를 안쪽에 머물게 합니다.

카메라에도 임시 collider가 있습니다. 위치를 바꾼 직후 잠깐 활성화하고 앱을 네 번 갱신해 카메라와 겹친 물체를 밀어낸 뒤 끕니다. 이 준비 단계 역시 시간과 물체 상태에 영향을 주므로 모든 캡처 사이 시간이 정확히 0.05초라고 단정할 수 없습니다.

캡처 반복문의 주요 조건은 다음과 같습니다.

| 주기 | 수행하는 일 |
|---|---|
| `i % 3 == 0` | 카메라 위치·주시점 변경 |
| `i % 5 == 0` | 조명 변경과 PathTracing 모션 블러 촬영 |
| 10·15·17·25프레임 주기 | 중심 방향 속도, 도형 색, 부유 방해 물체 속도, 배경 변경 |

인덱스가 0부터 시작하므로 첫 프레임에서도 모든 주기 조건이 맞습니다. 기본 여섯 프레임에서 카메라는 0·3번, 조명과 블러 촬영은 0·5번에 해당합니다.

```python
if i % 5 == 0:
    capture_with_motion_blur_and_pathtracing(duration=0.025, num_samples=8, spp=128)
else:
    rep.orchestrator.step(delta_time=0.0, rt_subframes=rt_subframes,
                          pause_timeline=False)
```

모션 블러는 정지 이미지에 번짐 필터를 붙이는 과정이 아닙니다. 0.025초 동안 진행한 움직임을 시간 샘플 8개로 렌더합니다. SPP=128은 렌더의 광선 샘플 수이고 `rt_subframes`와도 다른 값입니다. 첫 프레임부터 이 경로를 사용하므로 렌더 시간이 길 수 있습니다.

### 다른 Writer로 확장하기

포함된 `object_based_sdg_config.yaml`, `object_based_sdg_dope_config.yaml`, `object_based_sdg_centerpose_config.yaml`은 더 큰 구성과 포즈 데이터 형식의 예시입니다. JSON 런처와 달리 본체는 YAML도 받습니다. 저장소 루트에서 전체 BasicWriter 설정을 복사하세요.

```bash
cp src/138_replicator_replicator_object_based_sdg/object_based_sdg_config.yaml /tmp/tutorial138-basic.yaml
```

복사본에서 `launch_config.headless`를 `true`, `num_frames`를 `6`, `writer_kwargs.output_dir`를 아직 없는 `/tmp/tutorial138-basic`으로 지정합니다. 이 YAML은 표적 22개, 도형 350개, 메시 75개와 640×480 카메라 두 대를 사용하는 더 큰 예제입니다. 먼저 작은 구성을 유지하려면 `config.json`의 물체 수·해상도와 맞춘 다음 실행하세요.

```bash
~/isaacsim/python.sh src/138_replicator_replicator_object_based_sdg/object_based_sdg.py --config /tmp/tutorial138-basic.yaml
```

직접 실행은 런처의 새 출력 폴더 검사를 거치지 않습니다. `headless: false`에서는 `--steps` 생략 시 저장 후 GUI가 남고, `--steps 120`을 붙이면 저장 후 최대 120번 앱을 갱신합니다. DOPE·CenterPose YAML은 Writer 설정만 담고 있으므로 그대로 직접 실행하면 나머지는 **본체의 기본값**을 사용합니다. 기본 JSON의 작은 구성을 자동 상속하지 않는다는 점에 주의하세요.

`writer_type`과 `writer_kwargs`는 함께 바꿔야 합니다. BasicWriter 파일 이름을 바꾼다고 DOPE나 CenterPose의 포즈 규약이 되지는 않습니다. 자산 크기·원점·카메라 정보와 해당 Writer가 기대하는 라벨 구성을 함께 맞추어야 합니다.

### 준비한 스캔 USD를 표적으로 쓰기

본인이 준비한 실물 스캔 USD도 `labeled_assets_and_properties`의 표적 항목으로 넣을 수 있습니다. 먼저 USD를 Isaac Sim에서 열고 `metersPerUnit`, `upAxis`, 원점과 피벗, 메시 크기, 재질 참조를 확인하세요. 카메라 거리 0.25~0.75 m와 작업 공간 4×4×3 m에 비해 크기가 맞지 않으면 설정한 개수보다 자산 단위부터 점검해야 합니다.

그다음 `config.json` 복사본에서 표적 항목 하나의 `url`과 `label`을 자신의 자산에 맞춥니다. 현재 본체는 `omniverse://`로 시작하는 URL은 그대로 사용하고, 나머지 문자열에는 자산 루트를 앞에 붙입니다. 따라서 임의의 `/home/.../scan.usd`를 바로 넣지 말고, 읽을 수 있는 `omniverse://...` 주소를 사용하거나 자산 미러에 배치한 뒤 루트 기준 경로를 지정하세요. 필요한 메시·텍스처도 함께 접근할 수 있어야 합니다.

크기를 무작위화하려면 이 복사본에서는 본체가 실제로 읽는 `randomize_scale` 키를 사용합니다. `scale_min_max`만 바꾸는 것으로는 표적 배율이 달라지지 않습니다. 새 출력 폴더에서 작은 프레임 수로 촬영해 RGB의 물체 크기와 새 라벨을 대조한 뒤 데이터를 늘리세요. 이 과정은 준비된 USD를 연결하는 절차이며 스캔 생성이나 모델 학습은 별도입니다.

## 3. 캡처 사이에도 장면이 바뀌는 이유 정리

```text
표적·방해 물체·충돌 벽 생성
    → 필요한 주기의 카메라·조명·속도 변경
    → 센서 렌더 활성화
    → 일반 캡처 또는 움직임을 포함한 블러 캡처
    → 센서 렌더 비활성화 → 물리 진행 → 다음 캡처
```

`disable_render_products_between_captures=true`는 촬영하지 않을 때 센서 렌더 비용을 줄입니다. 물리 장면까지 멈추는 설정은 아닙니다. 가림의 변화는 무작위 배치와 그 이후 충돌·운동이 함께 만든 결과입니다.

## 4. 간단한 확인 실험

`config.json`을 `/tmp/tutorial138-more.json`으로 복사하고 **`shape_distractors_num`만 40에서 80으로 바꾸세요.**

```bash
python3 src/138_replicator_replicator_object_based_sdg/run.py --isaac-sim ~/isaacsim --config /tmp/tutorial138-more.json --headless --frames 6 --output /tmp/tutorial138-more
```

표적 수와 카메라 수, 요청 캡처 수는 유지됩니다. RGB에서 가림 사례가 늘어나는지 보고, 유효한 표적 라벨이 있는 이미지 비율과 처리 시간을 비교하세요. 난수 배치를 고정하는 CLI가 없으므로 단 한 장의 차이를 방해 물체 수만의 효과로 단정하지는 않습니다.

## 실행할 때 막히면

- **첫 캡처가 유난히 느림**: 0번부터 PathTracing 블러 촬영을 수행합니다. 자산 로딩과 렌더 진행 로그를 함께 확인하세요.
- **표적 크기가 바뀌지 않음**: 현재 `scale_min_max`와 `randomize_scale`의 키 불일치를 확인하세요. 렌더 안정화 설정으로 해결할 문제는 아닙니다.
- **물체가 보이지 않는 경계에 부딪힘**: `/World/CollisionWalls`의 충돌이 켜진 정상 구성입니다.
- **메모리 부족**: 방해 물체 수·카메라 수·해상도 중 하나를 줄인 설정 복사본으로 부하를 확인하세요.
- **`--check-config`는 통과했지만 자산 오류 발생**: 설정 읽기는 YCB·창고 메시·배경 텍스처 접근을 검사하지 않습니다.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Object Based Synthetic Dataset Generation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_object_based_sdg.html)에 대응합니다. NVIDIA 본체와 helper의 출처는 [NOTICE.txt](NOTICE.txt)에 있으며, 로컬 기본 JSON은 물체 수와 카메라 수를 줄이고 BasicWriter를 선택했습니다. 실물 스캔이나 검출·포즈 모델의 학습은 실행하지 않습니다.

[VERIFICATION.md](VERIFICATION.md)는 정적 검사와 설정 출력 확인을 기록하며 `tutorial.json`은 `not_run`입니다. 표적 배율 키 불일치는 소스 대조로 확인한 현재 한계이고, 위 GPU 출력은 직접 실행하여 확인할 기준입니다.
