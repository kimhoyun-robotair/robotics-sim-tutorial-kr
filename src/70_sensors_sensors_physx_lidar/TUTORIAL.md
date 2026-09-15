# 70. PhysX Lidar의 충돌체와 semantic 경로

권장 학습 순서 **70** · 센서와 측정 데이터 · 출처 ID `t157`

두 collider를 PhysX raycast Lidar로 스캔해 depth, 점군, hit prim 경로를 저장합니다. 원문의 depth 읽기와 segment workflow를 한 독립 실행에 연결했습니다.

## 이 패키지만으로 준비하기

Isaac Sim **5.1.0**, 지원 NVIDIA GPU/드라이버, Isaac Sim 설치의 `python.sh`가 필요합니다. GUI 관찰 단계는 화면과 RTX 렌더링이 가능한 환경에서 수행합니다. 로컬 기본 장면은 코드로 만들며 다른 `src` 패키지, 공통 모듈, 저장소의 asset/에 의존하지 않습니다. 원문의 별도 에셋·설치 예제를 사용하는 추가 단계는 아래에 구체적으로 구분했습니다.

```bash
export ISAAC_SIM_PATH=/path/to/isaacsim
cd src/70_sensors_sensors_physx_lidar
python3 run.py --help
"$ISAAC_SIM_PATH/python.sh" run.py --output output/run-01
```

출력 폴더는 **존재하지 않는 새 경로**를 지정합니다. 이미 있으면 오류로 멈추어 이전 결과를 보호합니다. `--output`을 생략하면 이 패키지의 `output/날짜_시간/`에 저장합니다.

`--steps`를 생략하면 사용자가 창을 닫을 때까지 GUI와 물리·렌더링·센서 갱신이 계속됩니다. 처음 240스텝의 측정 결과를 한 번 저장하며, 이후 관찰 중에는 파일이나 기록 배열을 계속 늘리지 않습니다. `--steps N`에 양수를 주면 N스텝의 결과를 저장하고 종료합니다. `--headless`만 사용하면 기존과 같이 240스텝 후 종료합니다. `--interactive`는 기존 명령 호환용이며 이제 필요하지 않습니다. 명시한 `--steps`의 종료 조건을 해제하지 않고, `--headless`와 함께 사용할 수 없습니다.

run.py는 standalone 실행용이므로 Script Editor에 전체를 붙이지 않습니다. 처음 240스텝을 마치기 전에 창을 닫으면 결과 파일은 완성되지 않을 수 있습니다.

창 없이 유한 실행으로 결과만 만들 때는 별도의 새 출력 경로를 사용합니다.

```bash
"$ISAAC_SIM_PATH/python.sh" run.py --headless --steps 240 --output output/batch-01
```

## 실습 순서와 관찰

1. 기본 실행 후 `lidar.npz`와 `hit_prims.json`을 확인합니다. 물체는 (4,-2,1), (4,2,1) m이고 센서는 (0,0,1)입니다.
2. `--no-colliders --output output/no-collision`으로 collider만 꺼서 비교합니다. 화면에 상자가 남아도 PhysX Lidar는 읽지 못해야 합니다.
3. `--rotation-rate 1 --output output/rotating`으로 별도 실험을 합니다. 기본 0은 모든 방향을 한 번에 쏘고 1은 초당 한 회전입니다.
4. GUI로는 **Create > Physics > Physics Scene**, **Create > Sensors > PhysX Lidar > Rotating**을 사용합니다. Raw USD Properties의 drawLines를 켜고 rotationRate=0으로 디버깅합니다.
5. Stage에서 Xform 또는 Cylinder를 만들고 Lidar를 그 밑에 넣은 뒤 local translate=(0.5,0.5,0)을 줍니다. 부모를 움직이면 센서도 따라가는지 확인합니다. 저장한 센서 데이터의 좌표계도 함께 기록해야 합니다.

## API와 USD 개념

PhysX Lidar는 collision geometry의 ground-truth 거리를 읽습니다. 투명하게 렌더링되는 유리도 collider가 있으면 광선이 막힙니다. 비가시 재질로 투과나 반사 강도를 모델링하는 RTX Lidar와 다릅니다.

`RangeSensorCreateLidar`의 FOV/resolution은 degree이고 `_range_sensor`가 depth/azimuth/zenith/point-cloud를 읽습니다. `world.pause()` 뒤 app update로 마지막 sweep의 버퍼를 확인합니다. `enable_semantics=True`와 prim의 SemanticsAPI class 라벨을 함께 설정했습니다. `get_prim_data()`는 각 hit의 prim 데이터를 제공하므로 JSON 경로를 Stage 라벨과 연결합니다. 이를 임의 정수 class ID로 간주하지 마세요.

Lidar prim을 부모 밑에 옮기면 USD local transform과 월드 transform이 달라집니다. 원점 offset을 월드 위치와 혼동하면 측정점을 잘못 표시합니다.

## 확장 실습·성공 기준·문제 해결

원문의 이동 로봇 실습은 `/Isaac/Robots/NVIDIA/Carter/carter_v1.usd`를 열어 `carter/chassis_link/left_wheel`, `right_wheel` drive target velocity를 각각 100으로 설정합니다. Lidar를 `/carter/chassis_link` 밑에 두고 local translate=(-0.06,0,0.38), drawLines=true, rotationRate=0으로 설정합니다. 별도 NVIDIA robot 자산이 필요하며 기본 실행에는 필요 없습니다.

점이 없으면 대상 ColliderAPI, min/max range, 재생 상태를 확인합니다. `depth<20` 개수는 max-range 미만 광선 수이며 유효성·입사각까지 검증한 품질 점수는 아닙니다. semantic output은 배열 형태가 구현에 따라 달라질 수 있어 npz 점군과 JSON hit 경로를 함께 저장합니다.

## 출처와 검증 범위

- [NVIDIA Isaac Sim 5.1.0 — PhysX SDK Lidar](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_physx_lidar.html)
- 구현 API는 설치된 5.1 `exts/`와 해당 `standalone_examples/` 원본을 함께 확인했습니다. 원문과 다른 작은 장면·GUI 관찰 루프·측정 스냅샷 저장은 이 패키지에서 추가했습니다.

Python 문법·도움말과 파일 구성을 검사했으며, RTX 영상/점군과 PhysX 런타임·GUI 상호작용은 작성 작업에서 실행하지 않았습니다. 실제 성공 여부는 위 단계의 **측정 파일과 화면 결과**로 확인합니다. `tutorial.json`의 verification은 그 이유로 `not_run`입니다.
