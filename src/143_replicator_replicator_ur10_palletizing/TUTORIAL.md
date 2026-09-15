# 143. UR10 팔레타이징의 두 접촉 사건에서 데이터 수집

권장 학습 순서 **143** · Replicator 합성 데이터 기초와 확장 · 출처 ID `t042`

이 패키지는 공식 UR10 bin stacking 시뮬레이션 위에 SDG를 붙입니다. 상자를 뒤집는 helper에 닿을 때는 annotator 배열을 직접 저장하고, 팔레트/이미 쌓인 상자에 닿을 때는 BasicWriter를 사용합니다. NVIDIA 5.1 배포 소스의 `PalletizingSDGDemo`를 로컬 `palletizing.py`에 포함했습니다. `run.py`는 앱 초기화, 실제 로봇 예제 로딩, 생성 작업과 GUI 수명 관리, task 오류 전파와 출력 보호를 추가한 standalone 적용입니다.

## GUI 실행과 종료

GUI에서 `--steps`를 생략하면 app update 횟수로 실행을 끊지 않습니다. 요청한 `--bins` 상자의 데이터 기록과 파일 저장을 마친 뒤에도 사용자가 창을 닫을 때까지 장면을 유지하며, 추가 데이터를 무한히 생성하지 않습니다. 양수 `--steps N`은 생성 작업을 기다리는 최대 app update 수이고, 작업이 먼저 끝나면 바로 종료합니다. 제한 안에 요청한 데이터가 완성되지 않으면 실패합니다. `--headless`에서 생략하면 기존 60000회 제한을 사용합니다.

이 패키지 폴더에서 다음과 같이 실행합니다. 설치 경로는 자신의 환경에 맞추고, 이미 사용한 출력 폴더는 새 경로로 바꿉니다.

```bash
~/isaacsim/python.sh run.py --output output/gui
```

## 준비와 실행

Isaac Sim 5.1.0 **전체 설치**, RTX GPU/드라이버, `isaacsim.examples.interactive` 및 Cortex 관련 배포 확장이 필요합니다. 런처가 interactive 확장을 켜므로 다른 패키지를 실행할 필요가 없습니다. 자산 root 아래 `/Isaac/Samples/Leonardo/Stage/ur10_bin_stacking_short_suction.usd`, `/Isaac/Props/KLT_Bin/small_KLT.usd`, `/Isaac/Environments/Simple_Warehouse/warehouse.usd`와 NVIDIA wood texture가 필요합니다. 네트워크 서버 또는 동일 구조의 로컬 미러에서 읽습니다.

```bash
export ISAAC_SIM_PATH="$HOME/isaacsim"
cd src/143_replicator_replicator_ur10_palletizing
"$ISAAC_SIM_PATH/python.sh" run.py --bins 2
# 화면 없이 동일 실제 로봇 시뮬레이션
"$ISAAC_SIM_PATH/python.sh" run.py --headless --bins 2 --output output_headless
```

출력은 새 폴더만 허용합니다. bins는 1~36이며 기본 2개입니다. flip 시나리오는 사건당 4프레임, pallet 시나리오는 16프레임입니다. `--headless`에서 `--steps` 생략 시 기본 60000회 안에 요청한 bin의 pallet capture가 끝나지 않으면 실패합니다. GUI 기본 실행에는 이 횟수 제한이 없습니다. 카메라 렌더와 자산 로딩도 app update 예산을 사용합니다.

## 관찰 순서

1. UR10이 conveyor에서 상자를 집어 팔레트에 놓는지 확인합니다. 시뮬레이션은 설치 확장의 `BinStacking.load_world_async()`와 `on_event_async()`로 실제 Cortex 동작을 시작합니다. 상자별 뒤집힘 여부는 seed=42로 초기화된 예제의 spawn 자세에 따라 다릅니다.
2. Stage에서 `/World/Ur10Table/bins/bin_0`, `/World/Ur10Table/pallet_holder`, `/World/Ur10Table/pallet/Xform/Mesh_015`를 찾습니다. 이 prim 경로가 두 SDG 사건의 근거입니다.
3. 상자가 flip helper에 접촉하면 timeline이 멈추고 네 카메라 위치를 순서대로 캡처합니다. 조명 위치/강도/색이 바뀌고 PathTracing 모드가 사용됩니다. `annot_bin_0` 같은 폴더에 rgb, instance segmentation, ID mapping JSON이 생깁니다. 뒤집을 필요가 없는 bin에서는 flip 폴더가 없는 것이 정상입니다.
4. pallet 또는 이미 쌓인 bin에 닿으면 `writer_bin_0`가 생성됩니다. RGB와 instance segmentation은 BasicWriter가 기록합니다. bin 재질은 매 캡처, 팔레트 texture와 카메라는 4프레임마다 변경됩니다.
5. SDG가 끝난 뒤 원래 재질로 돌아가고 로봇이 다음 bin을 처리하는지 확인합니다. 요청한 bins 수와 writer_bin 폴더 수가 같아야 합니다.

## 사건 감지와 캡처 API

`create_bbox_cache`로 active bin의 local bounding box 반크기를 구합니다. 월드 변환에서 위치·회전 quaternion을 얻어 `get_physx_scene_query_interface().overlap_box`로 주변 강체를 조회합니다. 이는 메쉬의 렌더 픽셀 충돌을 검사하는 것이 아니라 PhysX scene query입니다. 자기 자신은 건너뛰고 helper/pallet/다른 bin의 rigid_body 경로를 분류합니다.

타임라인 CURRENT_TIME_TICKED를 구독해 사건을 검사합니다. 접촉 시 pause하고 구독을 일시 해제해 재진입을 막습니다. 캡처 코루틴은 `await step_async(delta_time=0.0)`을 사용하므로 여러 랜덤 시점을 저장하는 동안 bin 물리가 진행되지 않습니다. 원문처럼 Script Editor의 비동기 방식으로 내부 SDG를 수행하지만 이 패키지는 바깥 `SimulationApp.update()`가 그 코루틴을 실행시킵니다.

flip 모드의 `rgb_annot.get_data()`는 RGBA 배열이고 instance segmentation은 `data`와 `info`를 포함합니다. 색으로 인코딩된 segmentation은 uint8 채널로 변환해 저장하고 ID 의미는 JSON으로 보존합니다. pallet 모드의 Writer는 동일 데이터를 파일 형식으로 조직해주는 고수준 기능입니다. 둘 중 하나가 더 정확한 센서를 뜻하지 않습니다.

USD material은 mesh에 binding되어 있습니다. `UsdShade.MaterialBindingAPI.ComputeBoundMaterial`로 원래 material을 저장하고 랜덤화 후 Bind로 되돌립니다. render mode도 PathTracing에서 RayTracedLighting으로 돌립니다. `wait_until_complete_async` 뒤에 graph와 render product를 정리해 아직 쓰는 데이터를 먼저 파괴하지 않습니다. 이 패키지는 새 예제 장면을 열어 `/Replicator`를 자체 SDG 용도로 사용합니다. 작업 중인 사용자 장면에 import해서 실행하지 않습니다.

## 한 가지 실험과 확인

**--pallet-frames만 16→8**로 줄여 bin 재질 8회와 카메라/texture의 4프레임 간격을 관찰합니다. flip 프레임, seed, bin 수는 그대로 둡니다. 각 캡처가 다른 시간의 로봇 동작인지, 같은 물리 순간의 다른 외관인지 구분합니다.

정상 출력의 최소 기준은 각 bin에 writer 폴더와 실제 PNG가 존재하는 것입니다. flip 폴더 개수를 bins 수와 같다고 강제하지 않습니다. 이미지 결과 외에도 SDG 전후 로봇이 계속 동작하고 임시 material이 복구되는지 GUI로 확인해야 원문의 비간섭 목표를 검증할 수 있습니다. 파일 개수 검사는 그 GUI 확인을 대신하지 않습니다.

UR10 import 오류면 전체 설치의 interactive/Cortex 확장을 확인합니다. bin_0를 찾지 못하면 asset load와 world startup 상태를 확인합니다. 접촉이 발생하지 않거나 로봇이 멈추면 --steps를 무작정 늘리기 전에 물리·로봇 로그를 확인합니다. task 실패는 런처로 전파되며 자동으로 성공 처리하지 않습니다. 문법/--help 검사와 실제 GPU 실행은 별도로 기록합니다. 저작권과 Apache-2.0 수정 고지는 NOTICE를 확인합니다.

## 출처와 버전

이 해설은 NVIDIA Isaac Sim **5.1.0** 문서와 해당 설치본을 기준으로 새로 작성했습니다. 원문의 전체 문장을 번역 복제한 것이 아니라 해당 워크플로를 독립적으로 실습하도록 설명했습니다.

- [공식 Randomization in Simulation – UR10 Palletizing](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_ur10_palletizing.html)
- [scenario](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_ur10_palletizing.html#scenario)
- [implementation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_ur10_palletizing.html#implementation)
