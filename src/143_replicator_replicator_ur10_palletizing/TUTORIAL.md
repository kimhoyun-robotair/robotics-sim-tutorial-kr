# 143. 상자를 놓는 순간을 멈추고 여러 모습으로 촬영하기

## 이번에 배우는 것

**UR10 팔레타이징의 특정 사건에서 물리를 멈추고, 외관을 바꾸어 촬영한 뒤 작업을 이어가는 구조를 이해합니다.**

UR10은 컨베이어의 상자를 집어 팔레트에 놓습니다. 뒤집힌 상자는 보조 구조물로 방향을 바로잡습니다. 이번 SDG는 그 과정 전체를 동영상처럼 저장하는 대신, 보조 구조물 또는 팔레트 부근에 상자가 도달한 순간을 골라 여러 시점·재질로 관찰합니다.

| 시나리오 | 촬영 조건 | 데이터 경로 |
|---|---|---|
| Bin flip | active bin이 flip helper와 겹치는 영역에 들어옵니다. | annotator를 직접 읽어 RGB·인스턴스 분할을 저장합니다. |
| Bin on pallet | 팔레트 또는 다른 bin과 겹치는 영역에 들어옵니다. | BasicWriter로 RGB·인스턴스 분할을 저장합니다. |
| 로컬 `run.py` | BinStacking 실행과 완료 확인을 연결합니다. | 현재 코드에 초기화·출력 경로 결함이 있습니다. |
| `palletizing.py` | 사건 감지와 두 캡처 시나리오를 구현합니다. | 아래 코드 읽기의 중심 파일입니다. |

인스턴스 분할은 같은 종류의 상자도 개체별로 구분하는 정답입니다. 장면 속 상자의 재질 색과 분할 이미지의 색은 역할이 다릅니다.

## 1. 실행 경로와 현재 한계 확인하기

Isaac Sim 5.1 전체 설치, RTX GPU, interactive·Cortex 확장과 5.1 자산 라이브러리가 필요합니다. **현재 로컬 `run.py`는 초기화와 출력 경로 결함으로 정상 완료가 막혀 있습니다.** 아래 도움말로 실제 옵션을 확인하고, 장면과 데이터 생성을 관찰하려면 이어지는 공식 Script Editor 경로를 사용하세요.

```bash
python3 src/143_replicator_replicator_ur10_palletizing/run.py --help
```

### 코드에서 볼 부분

로컬 `run.py`는 `demo.start()` 직후 `demo._capture_task`를 읽지만 `palletizing.py`의 생성자는 이 속성을 초기화하지 않습니다. 첫 캡처 사건 전에는 `AttributeError`가 발생할 수 있고 정리 경로에서도 같은 속성을 읽습니다.

또한 `PalletizingSDGDemo(output_dir)`는 전달받은 출력 인자를 사용하지 않고 다음 경로를 만듭니다.

```python
self._output_dir = os.path.join(os.getcwd(), "_out_palletizing_sdg_demo")
```

따라서 캡처가 진행되더라도 런처의 `--output` 검사 경로와 실제 저장 경로가 다릅니다. 저장소 루트에서 실행하면 본체가 사용할 경로는 루트의 `_out_palletizing_sdg_demo`입니다. `--output`만 새 경로로 바꿔도 이 본체 경로의 기존 결과는 보호되지 않습니다.

로컬 명령의 인수 의미는 다음과 같습니다. 이는 **현재 실행 성공을 뜻하는 표가 아닙니다.**

| 옵션 | 런처가 의도하는 제어 |
|---|---|
| `--bins 2` | 팔레트 캡처를 완료할 상자 수, 허용 범위 1~36 |
| `--flip-frames 4` | flip 사건 하나에서 촬영할 수 |
| `--pallet-frames 16` | pallet 사건 하나에서 촬영할 수 |
| `--steps N` | 생성 중 앱 갱신 최대 횟수 |
| `--headless` | 창 없이 실행하며 steps 생략 시 60000회 한도 |

GUI에서 steps를 생략하면 의도상 생성 완료 후 창을 유지합니다. 그러나 현재 결함을 해결하기 전에 그 완료 동작과 출력 검사를 통과한다고 가정해서는 안 됩니다.

### 공식 Script Editor 예제로 실행하기

[공식 5.1.0 문서의 Implementation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_ur10_palletizing.html#implementation)은 앱 안에서 실행하는 **전체 Script Editor 예제**를 제공합니다.

1. `~/isaacsim/isaac-sim.sh`로 새 Isaac Sim 창을 엽니다.
2. Window > Extensions에서 `isaacsim.examples.interactive`를 활성화합니다. 필요한 자산을 읽을 수 있는지 확인합니다.
3. Window > Script Editor를 열고 공식 문서의 Implementation에 있는 **전체 코드**를 준비합니다. 아래 설명용 부분 발췌나 로컬 `run.py`를 붙여 넣는 방식과 다릅니다.
4. 붙여 넣은 예제의 `NUM_CAPTURES`를 2로 설정하고 `_output_dir`를 **아직 없는 절대경로**로 지정합니다. 이 코드는 기본 출력 폴더의 충돌을 검사하는 런처가 아닙니다.
5. 실행합니다. 전체 예제는 `BinStacking` 장면을 불러오고 팔레타이징을 시작한 다음 SDG를 붙입니다. 별도로 만들어 둔 로봇 장면이 필요하지 않습니다.

공식 예제는 로컬 CLI 옵션을 받지 않습니다. 완료 후 앱은 유지되며 사용자가 창을 닫습니다. 이 경로 역시 이번 문서 개정에서 GPU 실행한 결과는 아니므로 아래 관찰 기준으로 확인하세요.

장면 로딩에 필요한 대표 자산은 자산 루트 아래의 `/Isaac/Samples/Leonardo/Stage/ur10_bin_stacking_short_suction.usd`, `/Isaac/Props/KLT_Bin/small_KLT.usd`, `/Isaac/Environments/Simple_Warehouse/warehouse.usd`입니다. 팔레트 외관 변경에는 `/NVIDIA/Materials/Base/Wood/` 아래 Oak·Ash·Plywood·Timber의 `*_BaseColor.png`도 사용합니다. 로봇 USD만 열리는 환경에서는 나중에 상자나 배경·재질 로딩이 실패할 수 있으므로 내부 참조까지 접근할 수 있어야 합니다.

## 2. 사건 감지에서 캡처·복원까지 따라가기

### 코드에서 볼 부분

`palletizing.py`는 active bin의 bounding box 반크기와 월드 위치·회전으로 PhysX `overlap_box()`를 호출합니다. 충돌 충격량을 읽는 센서가 아니라 **주변 공간과 겹치는 강체를 조회하는 방식**입니다. 자기 자신은 건너뛰고 반환된 rigid body 경로를 분류합니다.

```python
if hit.rigid_body.startswith(self.FLIP_HELPER_PATH) and not self._bin_flip_scenario_done:
    self._timeline.pause()
    self._timeline_sub.unsubscribe()
    self._timeline_sub = None
    self._capture_task = asyncio.ensure_future(self._run_bin_flip_scenario())
```

`FLIP_HELPER_PATH`는 `/World/Ur10Table/pallet_holder`입니다. 팔레트는 `/World/Ur10Table/pallet/Xform/Mesh_015`, 상자는 `/World/Ur10Table/bins/bin_0`부터 이어집니다. 타임라인 구독을 해제하는 이유는 정지한 같은 사건에서 캡처 작업을 여러 번 예약하지 않기 위해서입니다.

Flip 시나리오는 PathTracing으로 바꾸고 네 카메라 위치를 순서대로 사용합니다. 조명 위치·색·강도도 바꿉니다. `rgb_annot.get_data()`와 인스턴스 분할의 `data`, `info`를 직접 읽어 저장합니다.

Pallet 시나리오는 현재까지 쌓인 상자와 팔레트의 재질 연결을 먼저 보관합니다. 촬영마다 상자 재질을 바꾸고 4캡처마다 카메라와 팔레트 텍스처를 바꿉니다.

```python
for i in range(self.PALLET_SCENARIO_FRAMES):
    await rep.orchestrator.step_async(rt_subframes=24, delta_time=0.0)
```

`delta_time=0.0`이므로 이 열여섯 장은 서로 다른 로봇 동작 시점이 아니라 **같은 물리 순간의 다른 외관**입니다. 24 subframe은 렌더 안정화용 반복이며 24장의 추가 이미지를 의미하지 않습니다.

촬영 뒤 `MaterialBindingAPI.Bind()`로 원래 재질을 복원하고 임시 그래프·render product를 정리합니다. Flip 촬영의 렌더 모드는 `RayTracedLighting`으로 다시 설정합니다. 임의의 실행 전 렌더 설정을 저장했다가 모두 되돌리는 구현은 아닙니다. 다시 Play하고 다음 bin을 감시합니다. 생성용 변경을 정리하는 단계까지가 이 수집 흐름의 일부입니다.

### 실행 결과 확인하기

공식 경로가 완료되었거나 로컬 결함을 별도 수정한 뒤에는 **실제 본체 출력 경로**에서 다음을 확인하세요.

| 폴더 | 기대하는 결과 |
|---|---|
| `annot_bin_0/` 등 | flip 사건이 있었던 bin의 `rgb_*.png`, `is_*.png`, `is_info_*.json` |
| `writer_bin_0/` 등 | pallet 사건의 BasicWriter RGB와 colorized instance segmentation |

기본 해상도는 512×512입니다. Flip은 필요 없는 bin도 있으므로 `annot_bin_*` 개수가 처리한 bin 수와 같을 필요는 없습니다. 반면 두 bin의 pallet 사건을 완료했다면 `writer_bin_0`, `writer_bin_1`을 기대합니다. PNG 전체 개수에는 분할 이미지도 포함되므로 RGB 장수와 구분하세요.

파일 존재뿐 아니라 촬영 후 재질이 복원되고 로봇이 다음 작업을 이어가는지도 관찰하세요. “SDG가 원래 작업을 방해하지 않는다”는 목표는 PNG만으로 확인할 수 없습니다.

## 3. 로봇 시간과 데이터 다양성의 관계 정리

```text
로봇 작업 → 주변 강체 overlap 조회 → 관심 사건 감지
    → Pause·구독 해제
    → 여러 외관과 시점으로 캡처
    → 원래 재질 복원·RayTracedLighting 재설정·임시 그래프 정리
    → Play → 다음 상자
```

Annotator를 직접 읽는 flip 경로와 Writer를 사용하는 pallet 경로는 데이터 저장을 구성하는 방법이 다릅니다. 한쪽만 더 정확한 센서를 쓰는 것은 아닙니다. 두 경로 모두 사건이 발생한 물리 상태를 공유합니다.

## 4. 간단한 확인 실험

공식 Script Editor 실행에서 **`PALLET_SCENARIO_FRAMES`만 16에서 8로 바꾸어** 새 출력 폴더에 다시 실행하세요. 처리할 bin 수와 flip 설정은 유지합니다. 로컬 코드의 별도 수정이 완료된 환경에서는 대응 옵션이 `--pallet-frames 8`입니다.

Pallet 사건당 RGB가 여덟 장으로 줄어드는지 확인합니다. 카메라·팔레트 텍스처의 변경 간격은 여전히 네 캡처이며 상자 재질은 매 캡처 변경됩니다. 사진 수를 줄였다는 것이 로봇의 팔레타이징 단계를 절반만 실행했다는 뜻은 아닙니다.

## 실행할 때 막히면

- **로컬 `_capture_task` AttributeError**: 현재의 초기화 결함입니다. `--steps`나 GPU 설정으로 해결할 수 없습니다. 위 공식 실행 경로와 구분하세요.
- **`--output`은 비었는데 다른 폴더에 파일이 생김**: 본체가 전달 인자를 무시하고 작업 디렉터리의 `_out_palletizing_sdg_demo`를 사용하는 문제입니다.
- **`bin_0`를 찾지 못함**: 실제 BinStacking 장면과 `/World/Ur10Table/bins` 로딩을 확인하세요. 임의 UR10 장면만으로 같은 사건 경로가 생기지는 않습니다.
- **flip 결과 폴더가 없음**: 해당 bin에 뒤집기 사건이 필요했는지 먼저 확인하세요.
- **로봇이 멈췄는데 캡처도 진행되지 않음**: 비동기 작업 오류와 자산·재질 로딩 로그를 확인하세요. 기다리는 시간만 늘려 성공으로 판단하지 마세요.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Randomization in Simulation – UR10 Palletizing](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_ur10_palletizing.html)에 대응합니다. NVIDIA 구현의 출처와 로컬 변경 고지는 [NOTICE.txt](NOTICE.txt)에 있습니다.

[VERIFICATION.md](VERIFICATION.md)는 문법·도움말 검사만 기록하며 `tutorial.json`은 `not_run`입니다. 이번 개정에서는 로컬 초기화·출력 경로 결함을 소스에서 확인했습니다. 공식 실행 절차와 출력 표는 학습자가 검증할 기준이며 로컬 GPU 실행 성공이나 결함 수정을 의미하지 않습니다.
