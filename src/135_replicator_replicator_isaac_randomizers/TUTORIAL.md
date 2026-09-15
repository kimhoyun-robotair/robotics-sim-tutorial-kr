# 135. 무엇을 먼저 바꾸어야 자연스러운 장면이 될까요?

## 이번에 배우는 것

**조명·텍스처·좌표계·물리 배치를 바꾸면서, 무작위화의 순서가 결과에 미치는 영향을 확인합니다.**

조명 세기는 숫자를 바꾸면 되지만 팔레트 위의 상자는 부모의 회전까지 고려해야 합니다. 물체를 쌓는 경우에는 위치를 고르는 일만으로 충분하지 않고 충돌과 낙하를 기다려야 합니다. 이번 실습은 이 차이를 다섯 모드로 나눕니다.

| `--example` | 바꾸는 대상 | 기록에서 확인할 값 |
|---|---|---|
| `lights` | SphereLight 세 개의 위치·색·강도·색온도 | `lights`의 위치, intensity, `temperature_K` |
| `textures` | 상자·바닥에 연결한 격자 텍스처 | 파일, `scale`, `rotation_deg` |
| `sequential` | 회전한 팔레트 위 Bin과 관찰 카메라 | `bin_world_position`, `camera_position` |
| `volume` | 벽 안에서 떨어지는 작은 강체 상자 10개 | 위치, `speed_m_s` |
| `simready` | 검색한 table·plate·fruit 자산의 구성 | 선택된 자산 이름과 URL |

처음 네 모드는 로컬 도형과 생성 텍스처를 사용합니다. `simready`만 별도 카탈로그와 실제 자산을 읽습니다.

## 1. 조명과 텍스처의 변화부터 관찰하기

Isaac Sim 5.1과 RTX GPU 환경에서 저장소 루트에서 실행하세요. 모든 출력 경로는 새 폴더여야 합니다.

```bash
~/isaacsim/python.sh src/135_replicator_replicator_isaac_randomizers/run.py --example lights --headless --frames 3 --output /tmp/tutorial135-lights
~/isaacsim/python.sh src/135_replicator_replicator_isaac_randomizers/run.py --example textures --headless --frames 3 --output /tmp/tutorial135-textures
```

각 실행은 세 장을 촬영한 뒤 종료합니다. GUI에서 `--headless`와 `--steps`를 모두 생략하면 저장 후 창이 남습니다. `--steps`를 명시하면 생성 작업 후 닫힙니다. 조명·텍스처 모드에서는 `--steps`가 촬영 장수나 조명 변경 횟수를 정하지 않습니다.

### 코드에서 볼 부분

`lights`는 색온도 사용을 켠 SphereLight 세 개에 다음 값을 작성합니다.

```python
intensity = rng.uniform(3000, 18000)
temperature = rng.uniform(2800, 8000)
light.CreateIntensityAttr(intensity)
light.CreateColorTemperatureAttr(temperature)
```

색온도의 단위는 K입니다. 조명 색 자체도 함께 무작위화하므로 사진의 색을 색온도 하나로 설명할 수는 없습니다. 같은 상자를 고정해 두었기 때문에 물체 이동 없이도 외관이 달라지는 모습을 확인할 수 있습니다.

`textures`는 64×64 격자 PNG 세 개를 만들고 상자와 바닥에 OmniPBR 재질을 연결합니다. `diffuse_texture`는 파일 선택, `texture_scale`은 반복 크기, `texture_rotate`는 격자 회전, `project_uvw`는 투영 매핑 설정입니다. **재질을 물체에 연결하는 일과 재질 내부 입력을 바꾸는 일은 다릅니다.**

### 실행 결과 확인하기

각 출력의 `rgb/` 이미지와 `measurements.json`을 같은 프레임 번호로 맞춰 보세요. `lights`는 조명 세 개의 수치, `textures`는 두 재질의 텍스처 선택과 배율·각도를 기록합니다. 픽셀 밝기는 조명 외에도 재질·노출·톤 매핑의 영향을 받으므로 intensity가 두 배라고 RGB 값까지 두 배가 되지는 않습니다.

`scene.usda`는 마지막 장면 상태입니다. 텍스처 모드에서 만든 `texture_*.png`를 지우거나 옮기면 USD가 참조하는 이미지가 끊길 수 있으므로 결과 폴더를 함께 보관하세요.

## 2. 좌표계와 물리 진행이 필요한 배치 만들기

```bash
~/isaacsim/python.sh src/135_replicator_replicator_isaac_randomizers/run.py --example sequential --headless --frames 3 --output /tmp/tutorial135-sequential
~/isaacsim/python.sh src/135_replicator_replicator_isaac_randomizers/run.py --example volume --headless --frames 3 --steps 180 --output /tmp/tutorial135-volume
```

### 코드에서 볼 부분

`sequential`은 먼저 `/World/Pallet`을 회전시키고 자식 `/World/Pallet/Bin`을 팔레트의 좌표계 안에서 움직입니다.

```python
pallet.GetAttribute('xformOp:rotateXYZ').Set((0, 0, rng.uniform(-90, 90)))
target.GetAttribute('xformOp:translate').Set(
    (rng.uniform(-0.9, 0.9), rng.uniform(-0.5, 0.5), 0.45))
world_position = UsdGeom.Xformable(target).ComputeLocalToWorldTransform(
    Usd.TimeCode.Default()).ExtractTranslation()
```

팔레트 Deck은 2.4×1.6×0.3 m, Bin은 0.5×0.4×0.6 m입니다. Bin의 이동 범위를 Deck보다 작게 잡아 가장자리 여유를 둡니다. 저장된 translate는 **부모 기준 위치**이고, 카메라가 바라볼 위치는 부모 회전까지 누적한 **월드 위치**여야 합니다. 카메라는 그 위치 주변의 지면 위 상반구에서 시점을 선택합니다.

`volume`에서는 네 개의 보이지 않는 벽이 상자가 옆으로 빠져나가는 것을 막습니다. 벽의 표시를 끄는 것은 충돌을 끄는 일이 아닙니다. 각 상자는 0.3 m 크기의 강체이며 매 촬영 전 `world.step(render=False)`로 물리만 진행합니다. 첫 촬영 이후에는 상자에 중심 방향의 작은 속도를 주어 다시 섞습니다.

이 모드의 `--steps 180`은 **촬영 전 물리 단계 수**입니다. 물리 간격이 1/60초이므로 한 구간은 3초입니다. `--frames 3`은 이런 구간 뒤에 사진을 세 번 저장한다는 뜻입니다.

### 실행 결과 확인하기

`sequential`의 `bin_world_position`과 `camera_position`을 확인하세요. 부모가 회전해도 Bin이 Deck 위에 남고 카메라가 Bin을 바라보는지가 핵심입니다.

`volume`의 `bodies`에는 각 상자 위치와 속력 `speed_m_s`가 있습니다. 시간이 3초 지났다는 사실만으로 모든 상자가 정착했다고 판단하지 마세요. 실제 속력을 확인해야 합니다. 마지막 캡처 뒤 `scene.usda`를 열어 숨은 벽의 prim과 충돌 설정도 살펴볼 수 있습니다.

SimReady는 다음 명령으로 별도 실행합니다.

```bash
~/isaacsim/python.sh src/135_replicator_replicator_isaac_randomizers/run.py --example simready --headless --frames 1 --steps 180 --output /tmp/tutorial135-simready
```

`omni.simready.explorer`와 접근 가능한 카탈로그가 필요합니다. `simready_lab.py`는 table·plate·fruit를 검색하고 각 자산의 `PhysicsVariant=RigidBody`를 선택합니다. table의 강체 운동은 끄고 접시와 과일을 위로 배치합니다. 이 모드의 `--steps`는 **타임라인을 재생한 상태의 앱 갱신 횟수**이므로 volume의 고정 물리 단계와 같은 시간으로 환산하지 마세요.

각 시나리오는 임시 USD 레이어에 만들어지고 캡처 후 제거됩니다. `simready_0000.usda`는 합쳐서 저장한 캡처 시점의 장면이며, `measurements.json`에는 실제 선택한 자산 URL이 남습니다. 카탈로그가 비거나 필요한 variant가 없으면 오류로 끝납니다.

## 3. 무작위화의 순서 정리

```text
lights / textures : 속성 값 선택 → 현재 장면 촬영
sequential        : 부모 회전 → 자식 배치 → 월드 위치 계산 → 카메라 배치 → 촬영
volume            : 물리 진행 → 속도·위치 읽기 → 시간 추가 없이 촬영
simready          : 자산 검색 → variant 선택 → 임시 레이어 배치 → 재생 → 촬영·정리
```

무작위화의 목적은 숫자를 많이 바꾸는 것이 아니라, 서로 맞아야 하는 조건을 유지하면서 다양한 상태를 만드는 것입니다. 이 코드의 캡처는 `delta_time=0.0`으로 요청하므로 배치나 물리 진행을 준비하는 구간과 사진을 얻는 구간을 구분할 수 있습니다.

## 4. 간단한 확인 실험

`volume`에서 seed=31, frames=1을 유지하고 **`--steps`만 60과 300으로 바꾸어** 각각 새 폴더에 실행하세요.

초기 배치는 같고 첫 촬영 전 물리 시간은 1초와 5초입니다. RGB의 높이뿐 아니라 `bodies`의 속력을 비교해 어느 쪽에서 상자가 더 안정되었는지 확인하세요. 충돌 상태에 따라 결과가 달라질 수 있으므로 “300단계면 무조건 정착”을 기대값으로 두지는 않습니다.

## 실행할 때 막히면

- **격자가 검게 나옴**: 생성된 텍스처 파일과 OmniPBR의 파일 입력을 확인하세요. USD만 다른 폴더로 옮겼는지도 살펴보세요.
- **Bin을 바라보는 카메라가 빗나감**: local translate와 월드 위치를 혼동하지 않았는지 확인하세요.
- **volume 상자가 공중에 남음**: 높이와 속력을 함께 보세요. 아직 떨어지는 중이거나 다른 상자·벽에 걸렸을 수 있습니다.
- **SimReady 검색 timeout 또는 빈 결과**: 카탈로그 연결을 확인하세요. 검색 대기는 최대 10000 앱 갱신입니다.
- **`PhysicsVariant=RigidBody` 오류**: 선택된 자산이 제공하는 variant를 확인하세요. 모든 USD가 이 선택지를 갖지는 않습니다.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Randomization Snippets](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_isaac_randomizers.html)에 대응합니다. 조명·텍스처·순차 배치·물리 채우기를 자체 도형으로 축소하고, SimReady는 실제 검색과 variant 경로를 사용합니다. 물리 채우기는 원문의 힘 기반 흔들기 대신 속도 변경을 사용하며 숨은 벽을 유지합니다.

[RUNTIME_CHECK.md](RUNTIME_CHECK.md)는 기본 `lights` 한 프레임에서 프로세스 종료와 조명 기록을 확인한 사례입니다. 텍스처·물리 정착·SimReady 실행 전체를 확인한 기록은 아니며 이번 문서 개정에서도 그 결과를 새로 실행했다고 주장하지 않습니다.
