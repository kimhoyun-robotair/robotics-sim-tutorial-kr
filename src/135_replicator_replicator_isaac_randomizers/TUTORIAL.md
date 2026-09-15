# 135. USD와 Isaac API로 직접 장면 무작위화하기

권장 학습 순서 **135** · Replicator 합성 데이터 기초와 확장 · 출처 ID `t047`

Replicator의 미리 정의된 randomizer만으로 표현하기 어려운 **조명, 재질, 순서가 있는 배치, 물리 기반 채우기, SimReady 자산 검색**을 한 패키지에서 실행합니다. 서로 다른 예제는 `--example`로 선택하며, 각 실행은 새 장면을 만들어 독립적으로 시작합니다. 이미지와 함께 변경한 실제 값/물리 상태를 `measurements.json`에 저장합니다.

## 이 실습의 의도

장면의 조명·재질·부모 좌표계·물리 상태를 직접 바꾼 다음, 그 결과를 촬영 이미지와 함께 해석하는 실습입니다. 기본 `lights` 실행은 고정된 Cube와 바닥을 세 조명으로 비추며 3회 캡처하므로, 사진이 달라지는 원인을 물체 이동과 구분할 수 있습니다. 나머지 네 모드는 `--example`로 별도 선택하며, SimReady 검색까지 기본 실행에서 수행하지는 않습니다.

## 실행 후 확인할 것

- **기본 조명 비교:** `rgb/`의 3프레임에서 Cube의 배치는 유지되고 표면과 바닥의 조명이 달라지는지 봅니다. `measurements.json`의 프레임마다 조명 기록이 3개이며, `intensity`는 3000–18000, `temperature_K`는 2800–8000 범위여야 합니다. 특정 난수값이나 밝기 비율은 성공 기준이 아닙니다.
- **텍스처 선택 시:** `textures`의 생성 PNG와 기록의 `file`, `scale`, `rotation_deg`를 대조합니다. 반복 크기는 0.25–2, 회전은 0–90도 범위이고, 형상 이동 없이 격자 표현이 바뀌는 것을 확인합니다.
- **순차 배치 선택 시:** `scene.usda`의 `/World/Pallet/Bin`은 회전한 Deck 위에 남아야 합니다. 기록의 `bin_world_position`과 `camera_position`은 서로 다른 좌표이며, 카메라는 Bin에서 4 m 떨어진 상반구에 배치됩니다.
- **부피 채우기 선택 시:** `/World/Box_0`부터 10개 상자의 낙하와 `bodies[].speed_m_s`를 봅니다. 보이지 않는 `/World/Wall_0` 등 네 벽에 막히는 것은 정상이며, 캡처 전 180스텝이 지났다는 이유만으로 모든 상자가 정착했다고 판단하지 않습니다.
- **SimReady 선택 시:** `measurements.json`의 실제 자산 URL과 `simready_0000.usda` 등 프레임별 장면을 확인합니다. 시나리오가 끝나면 임시 자산 레이어를 제거하므로 마지막 GUI에 table·plate·fruit가 남지 않을 수 있습니다. 빈 검색 결과나 `RigidBody` variant 누락은 별도 준비 실패입니다.

## GUI 실행과 종료

GUI 실행에서 `--steps`를 생략하면 정해진 캡처와 파일 저장을 끝낸 뒤 사용자가 창을 닫을 때까지 장면을 유지합니다. 추가 이미지를 무한히 생성하지 않습니다. `--steps`는 volume/simready 모드에서 캡처 전 물리 진행 횟수이며 생략 시 기존 180회를 사용합니다. 양수 `--steps N`을 명시하면 해당 설정으로 작업을 마치고 GUI 대기 없이 종료합니다. `--headless`는 기존 유한 작업을 마치면 종료합니다.

이 패키지 폴더에서 다음과 같이 실행합니다. 설치 경로는 자신의 환경에 맞추고, 이미 사용한 출력 폴더는 새 경로로 바꿉니다.

```bash
~/isaacsim/python.sh run.py --output output/gui
```

## 준비와 실행

Isaac Sim 5.1.0, 지원 NVIDIA RTX GPU/드라이버가 필요합니다. 기본 네 모드는 코드로 생성한 도형과 텍스처를 사용하므로 외부 자산이나 다른 로컬 튜토리얼이 필요 없습니다. `simready`만 공식 SimReady 검색 서비스/카탈로그와 자산 접근이 필요하며 내장 `omni.simready.explorer`를 사용합니다.

이 패키지 폴더의 터미널에서:

```bash
ISAACSIM="$HOME/isaacsim"
python3 run.py --help
"$ISAACSIM/python.sh" run.py --example lights --headless --output output/lights
"$ISAACSIM/python.sh" run.py --example textures --headless --output output/textures
"$ISAACSIM/python.sh" run.py --example sequential --headless --frames 12 --output output/sequential
"$ISAACSIM/python.sh" run.py --example volume --headless --steps 180 --output output/volume
"$ISAACSIM/python.sh" run.py --example simready --frames 2 --output output/simready
```

설치 위치에 맞춰 `ISAACSIM`을 바꾸고 Windows에서는 `python.bat`를 사용합니다. 새 출력 폴더만 허용합니다. 기본 출력은 패키지 내부 `output/`이며 기존 폴더는 덮어쓰지 않습니다. `--headless`와 `--steps`를 생략하면 저장 후에도 GUI에서 계속 관찰할 수 있습니다. 저장한 `scene.usda`는 나중에 **File > Open**으로 다시 열 수 있습니다.

## 1. 조명 속성 바꾸기

1. `lights` 실행의 RGB 세 장을 비교합니다. 대상 Cube는 고정되어 있고 세 SphereLight의 위치, 색온도, 색, 강도만 달라집니다.
2. `measurements.json`의 `temperature_K`, `intensity`, `position`을 봅니다. 색온도는 2800–8000 K, intensity는 3000–18000 범위입니다.
3. 저장한 USD에서 `/World/Light_0`을 선택하고 Property의 Light 값과 Transform을 확인합니다. 색온도 사용 여부는 `enableColorTemperature` 속성입니다.
4. 실제 장면 변화와 자동 노출/톤 매핑의 영향을 구분하기 위해 물체 표면과 배경을 함께 비교합니다. intensity만으로 모든 픽셀 밝기의 선형 비례를 기대하지 마십시오.

## 2. 재질의 텍스처 입력 바꾸기

1. `textures`는 세 격자 PNG를 출력 폴더에 생성한 뒤 Cube와 Floor에 각각 OmniPBR 재질을 붙입니다.
2. RGB에서 격자의 간격과 방향을 비교하고 기록의 `scale`, `rotation_deg`, `file`을 확인합니다.
3. USD에서 `/World/Looks/Material_0`의 shader 입력을 확인합니다. `diffuse_texture`는 텍스처 파일, `texture_scale`은 반복 크기, `texture_rotate`는 각도, `project_uvw`는 투영 매핑 여부입니다.
4. 원문은 기존 장면에 재질을 임시로 할당했다가 원래 binding을 되돌립니다. 이 패키지는 새 장면을 만들기 때문에 원본 사용자 재질을 덮어쓰지 않습니다. 저장된 USD를 다른 곳으로 옮길 때는 생성 텍스처 파일도 함께 옮기고 경로를 갱신하십시오.

## 3. 순서가 있는 배치

1. `sequential`은 먼저 Pallet 부모 좌표계의 Z 회전을 정한 뒤 그 자식 Bin을 Deck 내부에 배치합니다. **부모의 회전을 확정한 다음** Bin의 월드 위치를 계산해야 Camera가 올바른 곳을 바라봅니다.
2. `/World/Pallet/Deck`은 2.4×1.6×0.3 m, Bin은 0.5×0.4×0.6 m입니다. Bin의 local x는 ±0.9, y는 ±0.5 안이어서 Deck을 벗어나지 않도록 여유를 둡니다.
3. `bin_world_position`과 `camera_position`을 비교합니다. Camera는 golden-angle 방식으로 상반구를 순회하며 Bin을 바라봅니다.
4. 원문의 forklift/pallet/bin 참조 자산, 전체 구 스캔, HDR 배경 교체는 여기서 자체 도형, **지면 위 상반구 스캔**, dome 색 교대로 축소했습니다. 원문의 의존 순서와 local→world 계산은 유지합니다.

## 4. 물리 기반 부피 채우기

1. `volume`을 실행하면 보이지 않는 네 벽으로 둘러싼 공간 위에서 작은 상자 10개가 떨어집니다. 각 상자는 별도의 rigid body이고 벽에는 static collider만 있습니다.
2. 첫 캡처는 지정한 `--steps`만큼 낙하한 뒤 이루어집니다. 이후 캡처 전에는 중심을 향하는 작은 속도 변화를 주어 배치가 재정렬되게 합니다.
3. `bodies`의 `position`과 `speed_m_s`를 읽습니다. **지정한 시간이 지났다는 사실은 완전 정착을 보장하지 않습니다.** 속도가 아직 크면 steps를 늘리고 비교하십시오.
4. 이 패키지는 원문의 weighted USD asset selection, 저마찰 물리 재질, `apply_force_at_pos()`로 흔들기, 임시 벽 제거의 큰 창고 데모를 **기본 rigid cube·속도 변화·유지되는 벽**으로 축소한 실습입니다. 숨겨진 벽도 충돌은 계속 활성화되어 있다는 점을 확인하십시오.
5. 원문과 같은 힘 기반 실험을 확장할 때는 `omni.physx.get_physx_simulation_interface().apply_force_at_pos(stage_id, body_path, force, world_position)`에 StageCache ID와 `PhysicsSchemaTools.sdfPathToInt()`의 body 경로를 전달합니다. 힘은 N, 속도는 m/s이므로 값을 그대로 서로 대입하면 안 됩니다.

## 5. SimReady 자산으로 장면 만들기

1. Isaac Sim UI에서 **Window > Extensions**를 열어 `omni.simready.explorer`가 설치되어 있는지 확인합니다. 검색 창에서 `table`, `plate`, `fruit`를 검색해 카탈로그와 자산을 읽을 수 있는지 먼저 봅니다.
2. `simready`를 실행합니다. 로컬 `simready_lab.py`가 같은 검색 API를 호출하며 빈 검색 결과와 없는 `PhysicsVariant=RigidBody`를 오류로 처리합니다. 임의 도형으로 바꾸어 성공 처리하지 않습니다.
3. 선택된 table, plate, fruit의 URL은 `measurements.json`에 남습니다. table은 rigid-body dynamics를 끄고 collider를 유지하며, plate와 fruit는 물리 상태를 활성화한 variant를 사용합니다.
4. Bounding box로 테이블 높이와 물체 높이를 구한 다음 위로 쌓아 배치하고 `--steps`만큼 실제 timeline을 진행합니다. Camera는 위에서 local -Z 방향으로 내려다봅니다.
5. 각 시나리오는 별도의 임시 USD layer에서 생성되고 끝나면 그 layer만 제거합니다. `simready_0000.usda`는 캡처 시점의 flattened stage이며 다음 시나리오에 물체가 누적되지 않아야 합니다.

## API와 USD 개념

| API / 개념 | 역할 |
|---|---|
| Stage, Prim, Attribute | 장면 문서, 경로가 있는 요소, 그 요소에 저장된 값입니다. |
| `UsdLux.SphereLight` | USD 조명 schema입니다. intensity/color/temperature를 명시적으로 작성합니다. |
| `UsdShade.MaterialBindingAPI` | 기하 prim에 material을 연결합니다. shader 입력을 바꾸는 것과 binding을 바꾸는 것은 별개입니다. |
| `ComputeLocalToWorldTransform` | 부모 변환이 누적된 월드 행렬을 구합니다. 자식의 translate 속성 자체는 local 좌표입니다. |
| `Gf.Matrix4d.SetLookAt` | 카메라 시점 행렬을 구성합니다. inverse에서 얻은 quaternion을 camera orient에 넣습니다. |
| `DynamicCuboid` / `FixedCuboid` | Isaac Core API의 동적/정적 상자입니다. rigid body와 collider 설정을 함께 이해할 수 있습니다. |
| `World.step(render=False)` | 물리 시간만 진행시키는 단계입니다. 캡처 횟수와 물리 스텝 수를 분리합니다. |
| `Sdf.Layer`, `Usd.EditContext` | 변경을 기록할 레이어를 선택합니다. 시나리오별 임시 레이어는 원래 stage 구조와 분리됩니다. |
| Variant set | 자산 제작자가 미리 정의한 구성 선택지입니다. `PhysicsVariant`는 모든 USD 파일에 존재하는 공통 필수 속성이 아닙니다. |
| `orchestrator.step(delta_time=0)` | 현재 상태를 캡처하며 추가 물리 시간을 의도하지 않습니다. `rt_subframes=8`은 렌더 안정화 반복입니다. |

길이는 미터, 회전은 `rotateXYZ`에서 degrees, up axis는 Z입니다. 모든 코드가 이 폴더 안에 있으며 상위 폴더의 모듈·자산을 import하지 않습니다.

## 한 변수만 바꾸는 실험

`volume`을 `--seed 31 --steps 60`과 `--seed 31 --steps 300`으로 실행해 마지막 프레임의 속도를 비교합니다. 동일한 초기 배치에서 정착 시간이 달라지는지 살펴보십시오. `sequential`에서는 부모 회전을 0으로 고정해도 Bin이 Deck 위에 남는지 확인합니다.

## 문제 해결과 확인 범위

- 일반 Python에서 Kit 모듈이 없으면 설치의 Python으로 실행합니다. `python3 run.py --help`는 GPU 없이 인수만 확인하는 용도입니다.
- SimReady 검색 timeout/빈 결과는 카탈로그 접근 상태를 확인합니다. 검색 대기는 최대 10000 app update로 제한됩니다.
- 검은 텍스처는 `.png` 경로와 OmniPBR shader 입력을 확인합니다. 생성된 텍스처를 삭제하면 저장 stage의 참조가 깨집니다.
- 물체가 공중에 있다면 물리 시간이 아직 짧은지, wall 충돌에 걸렸는지 기록과 뷰포트에서 확인합니다.
- 원문 다섯 절의 제어 흐름을 모두 제공하되 기본 네 모드는 입문용 자체 도형으로 재구성했습니다. 실제 환경/자산 검색을 실행하지 않은 상태에서 SimReady 검증 완료라고 간주하지 않습니다.

## 출처

- [Isaac Sim 5.1.0: Randomization Snippets](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_isaac_randomizers.html)
- [조명](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_isaac_randomizers.html#randomizing-light-sources), [텍스처](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_isaac_randomizers.html#randomizing-textures), [순차 배치](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_isaac_randomizers.html#sequential-randomizations)
- [물리 기반 채우기](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_isaac_randomizers.html#physics-based-randomized-volume-filling), [SimReady](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_isaac_randomizers.html#simready-assets-sdg-example)
- 공식 설치 예제: `standalone_examples/api/isaacsim.replicator.examples/simready_assets_sdg.py`.

## 실제 실행 기록

확인한 조건과 측정 결과는 [RUNTIME_CHECK.md](RUNTIME_CHECK.md)를 보세요. 검증은 해당 실행 모드에 한정됩니다.
