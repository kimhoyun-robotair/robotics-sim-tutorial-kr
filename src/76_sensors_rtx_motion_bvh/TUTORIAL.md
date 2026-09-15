# 76. Motion BVH의 활성화와 움직이는 RTX 표적

권장 학습 순서 **76** · 센서와 측정 데이터 · 출처 ID `t179`

움직이는 Radar 표적을 만들고 Motion BVH를 켠/끈 두 실행을 비교합니다. 설정을 실제 SimulationApp 생성 시 적용하며 point cloud와 표적 상태를 기록합니다.

## 이 실습의 의도

높이 1 m의 `/World/Radar` 앞에서 `/World/Target`을 X축 방향으로 움직여, Motion BVH 설정을 렌더러 생성 시 적용하는 방법과 동일 조건의 비교 실행을 배웁니다. 표적에는 중력을 끄고 기본 X 속도 -0.5 m/s를 주어 낙하 대신 수평 이동을 관찰하게 했습니다. 기본 실행은 BVH를 켜고 처음 240스텝의 반환 수·표적 위치와 마지막으로 비어 있지 않았던 점군을 저장하지만, Doppler 속도나 성능 차이를 직접 측정하지는 않습니다.

## 실행 후 확인할 것

- Stage/뷰포트에서 `/World/Target`이 초기 `(8, 0, 1)` m 부근에서 X가 감소하는 방향으로 이동하는지 봅니다. 중력을 끈 표적이 바닥으로 떨어지지 않는 것은 이 비교 장면의 의도입니다.
- `measurements.json`에서 기본 `motion_bvh=true`, `target_speed_m_s=-0.5`와 `target_final_position`을 확인합니다. 위치는 수집 종료 시점의 기록이므로 이후 계속 열린 GUI의 현재 위치와 구별합니다.
- `returns_per_frame` 중 비어 있지 않은 반환이 생겼는지, `points.npy`에 실제 점 배열이 있는지 확인합니다. `points.npy`는 **마지막 비어 있지 않은 프레임**을 보존하므로 마지막 항목의 점 수가 0이어도 저장 점군이 있을 수 있습니다. 모든 프레임이 비면 코드는 오류로 종료합니다.
- `--no-motion-bvh` 실행에서는 출력 폴더를 분리하고 속도·스텝 수를 같게 두어 `motion_bvh=false`, 표적 이동, 반환 기록을 대조합니다. 두 실행 모두 점이 나와도 이 파일에는 Doppler 측정값이 없으므로 속도 추정의 정확성을 입증한 결과는 아닙니다.
- `points.npy`, `measurements.json`, `scene.usda`가 수집 구간 후 생성되는지 확인합니다. 기본 GUI는 저장 후에도 계속 실행되며, 표적이 나중에 센서 시야를 벗어나는 현상과 이미 저장된 측정 구간을 구분합니다.

## 이 패키지만으로 준비하기

Isaac Sim **5.1.0**, 지원 NVIDIA GPU/드라이버, Isaac Sim 설치의 `python.sh`가 필요합니다. GUI 관찰 단계는 화면과 RTX 렌더링이 가능한 환경에서 수행합니다. 로컬 기본 장면은 코드로 만들며 다른 `src` 패키지, 공통 모듈, 저장소의 asset/에 의존하지 않습니다. 원문의 별도 에셋·설치 예제를 사용하는 추가 단계는 아래에 구체적으로 구분했습니다.

```bash
export ISAAC_SIM_PATH=/path/to/isaacsim
cd src/76_sensors_rtx_motion_bvh
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

1. 기본 명령은 `enable_motion_bvh=True`로 실행합니다. `measurements.json`의 motion_bvh, target_speed_m_s, 반환 수를 확인합니다.
2. `--no-motion-bvh --output output/bvh-off`로 **설정 하나만** 바꾸어 다시 실행합니다. 표적 속도·센서·steps는 동일하게 유지합니다.
3. 두 실행에서 반환 점이 생겼다고 Doppler가 같다고 결론 내리지 마세요. 이 패키지의 일반 point-cloud annotator는 Doppler 속도를 직접 내보내지 않습니다. BVH off 실행은 잘못된 Radar 조건을 관찰하는 비교군입니다.
4. GUI 환경에서는 아래 세 command-line 설정을 함께 지정하는 방식도 확인합니다. Settings에서 값이 실제 적용되었는지 보고 같은 target motion 실험을 수행합니다.
5. 속도 효과가 필요한 실험은 BVH On으로 유지하고, 정적 Lidar 성능 측정처럼 필요 없는 경우 비용을 비교한 뒤 선택합니다.

## API와 USD 개념

BVH는 ray가 geometry에 맞는지 빠르게 찾는 공간 가속 구조이고 Motion BVH는 시간에 따른 geometry 변화를 포함합니다. RTX Lidar motion compensation과 Radar Doppler에 필요합니다. Isaac Sim 5.1의 기본값은 성능을 위해 Off입니다.

`SimulationApp({'enable_motion_bvh':True})`는 렌더러 초기화 시 관련 설정을 적용합니다. 뒤늦게 Python bool만 바꾸어 이미 생성된 렌더러가 바뀌었다고 가정하지 않습니다. renderer 노출 시간 중 움직임과 단순 frame 사이 transform 변화는 별개입니다.

이 예제는 Radar Cartesian 점군과 물리 target 위치를 기록합니다. 정확한 Doppler/속도 성능을 검증하려면 Radar GMO의 해당 필드를 확인하고 radial velocity 기준으로 독립 평가해야 합니다. 반환 count 차이만으로 물리 정확도를 증명할 수 없습니다.

## 확장 실습·성공 기준·문제 해결

GUI/다른 workflow에서 사용하는 공식 설정은 다음과 같습니다.

```bash
"$ISAAC_SIM_PATH/isaac-sim.sh" --/renderer/raytracingMotion/enabled=true --/renderer/raytracingMotion/enableHydraEngineMasking=true --/renderer/raytracingMotion/enabledForHydraEngines='0,1,2,3,4'
```

Motion BVH는 모든 관련 센서의 VRAM과 render time을 늘릴 수 있습니다. 비교 시 첫 로딩·shader compilation 시간을 steady-state 비용으로 섞지 마세요. BVH Off에서도 화면상 표적은 움직일 수 있으며 Radar 전체 물리 모델이 올바르다는 근거가 되지 않습니다. 반환이 없으면 timeline·RTX GPU·FOV도 별도로 검사합니다. 작성 시 실제 GPU 비교 실행은 수행하지 않았습니다.

## 출처와 검증 범위

- [NVIDIA Isaac Sim 5.1.0 — RTX Sensors](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_rtx.html)
- 구현 API는 설치된 5.1 `exts/`와 해당 `standalone_examples/` 원본을 함께 확인했습니다. 원문과 다른 작은 장면·GUI 관찰 루프·측정 스냅샷 저장은 이 패키지에서 추가했습니다.

Python 문법·도움말과 파일 구성을 검사했으며, RTX 영상/점군과 PhysX 런타임·GUI 상호작용은 작성 작업에서 실행하지 않았습니다. 실제 성공 여부는 위 단계의 **측정 파일과 화면 결과**로 확인합니다. `tutorial.json`의 verification은 그 이유로 `not_run`입니다.
