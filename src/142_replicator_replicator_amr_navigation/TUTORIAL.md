# 142. AMR 내비게이션 중 목적지 이벤트로 SDG 기록하기

권장 학습 순서 **142** · Replicator 합성 데이터 기초와 확장 · 출처 ID `t041`

실제 Nova Carter와 공식 OmniGraph navigation 자산이 dolly 목적지를 향해 주행합니다. 목적지에 가까워지면 잠깐 정지해 **로봇 전방 좌/우 카메라**를 기록하고 dolly와 props를 다시 배치합니다. 일정 캡처 간격으로 배경도 바뀝니다. 공식 5.1 `NavSDGDemo`를 `navigation.py`에 포함했고 CLI 제한·출력 보호와 캡처 delta_time=0을 추가했습니다.

## 이 실습의 의도

로봇이 목적지에 접근한 순간을 데이터 수집 조건으로 삼아, 주행과 촬영을 번갈아 수행하는 실습입니다. Nova Carter의 좌·우 전방 센서를 사용하므로 외부 고정 카메라와 다른 로봇 관점의 이미지가 생깁니다. 기본 실행은 목적지 9곳을 촬영하고 3곳마다 환경을 바꾸며, 자산에 포함된 OmniGraph 주행을 사용하므로 ROS Nav2나 장애물 회피 성능의 검증은 범위에 들어가지 않습니다.

## 실행 후 확인할 것

- **주행 목표:** GUI의 `/NavWorld/CarterNav/targetXform`과 dolly 위치를 대조하고 Carter가 그쪽으로 이동하는지 봅니다. 로봇과 dolly 사이 평면 거리가 최초 2 m, 이후 선택된 1.75–2.5 m 미만일 때 `Starting SDG for frame no.` 로그가 나옵니다. dolly 중심까지 완전히 도달해야 촬영하는 것은 아닙니다.
- **촬영 중 정지:** 위 로그 뒤에는 timeline을 잠시 멈추고 촬영하며, 다음 dolly·props 배치 후 주행을 재개합니다. 캡처 때 로봇이 멈추는 것은 의도한 동작이고, `--frames`는 이동 스텝 수가 아닌 이 캡처 사건의 수입니다.
- **스테레오 파일:** `left_sensor`, `right_sensor` 식별자의 동일 캡처 RGB를 짝지어 비교합니다. 기본 9목적지 완료 시 1024×1024 PNG가 18개이며, 최종 JSON의 `destinations=9`, `stereo_pngs=18`과 맞아야 합니다. 이 Writer는 RGB만 요청하므로 깊이·검출 라벨은 생성하지 않습니다.
- **환경 전환:** 기본 `--env-interval 3`이면 처음 3목적지는 Grid, 다음 3곳은 Warehouse, 마지막 3곳은 Full Warehouse인지 확인합니다. 목적지 수를 3 이하로 줄인 실행에서 세 배경이 모두 보일 필요는 없습니다.
- **완료와 제한:** `--use-temp-rp` 사용 시 주행 중 센서 렌더 업데이트가 꺼지는 것은 정상이며, 촬영 결과는 계속 저장되어야 합니다. `--steps` 초과 오류나 부족한 좌·우 파일은 완료가 아니며, 출력 개수가 맞아도 충돌 회피가 입증된 것은 아닙니다.

## GUI 실행과 종료

GUI에서 `--steps`를 생략하면 app update 횟수로 실행을 끊지 않습니다. 요청한 `--frames` 목적지의 데이터 기록과 파일 저장을 마친 뒤에도 사용자가 창을 닫을 때까지 장면을 유지하며, 추가 데이터를 무한히 생성하지 않습니다. 양수 `--steps N`은 생성 작업을 기다리는 최대 app update 수이고, 작업이 먼저 끝나면 바로 종료합니다. 제한 안에 요청한 데이터가 완성되지 않으면 실패합니다. `--headless`에서 생략하면 기존 40000회 제한을 사용합니다.

이 패키지 폴더에서 다음과 같이 실행합니다. 설치 경로는 자신의 환경에 맞추고, 이미 사용한 출력 폴더는 새 경로로 바꿉니다.

```bash
~/isaacsim/python.sh run.py --output output/gui
```

## 준비와 실행

Isaac Sim 5.1.0 전체 설치, 지원 RTX GPU/드라이버, 5.1 자산 서버 또는 미러가 필요합니다. `/Isaac/Samples/Replicator/OmniGraph/nova_carter_nav_only.usd`, `/Isaac/Props/Dolly/dolly.usd`, `/Isaac/Props/YCB/Axis_Aligned_Physics`, `environments.json`의 세 환경을 읽습니다. 다른 로컬 패키지나 ROS 설치는 필요 없습니다. 이 예제의 navigation은 ROS Nav2가 아니라 자산에 포함된 OmniGraph입니다.

```bash
export ISAAC_SIM_PATH="$HOME/isaacsim"
cd src/142_replicator_replicator_amr_navigation
"$ISAAC_SIM_PATH/python.sh" run.py --headless --frames 9 --env-interval 3 --use-temp-rp
# GUI 관찰; 기존 결과 보존
"$ISAAC_SIM_PATH/python.sh" run.py --frames 3 --output output_gui
```

`--headless`에서 `--steps`를 생략하면 최대 40000번 app update 안에 끝나지 않을 때 실패합니다. GUI 기본 실행에는 이 자동 종료 상한이 없습니다. `--frames`는 이동 중의 physics frame 수가 아니라 **목적지 캡처 횟수**입니다. 9번이면 좌/우 RGB PNG 총 18개가 성공 기준이며 런처가 실제 파일 개수를 확인합니다. 출력은 새 폴더만 허용하며, `--output`으로 다른 경로를 지정할 수 있습니다.

## 실습 순서

1. `environments.json`을 열어 Grid, Warehouse, Full Warehouse 순서로 바뀌는 것을 확인합니다. 파일의 값은 asset root 기준 `/Isaac/...` 경로입니다.
2. GUI에서 Stage의 `/NavWorld/CarterNav/targetXform`을 찾습니다. navigation 그래프는 이 Xform 목표의 위치를 읽어 로봇을 제어합니다. 같은 계층의 chassis와 센서도 확인합니다.
3. robot과 dolly 사이 평면 거리가 threshold보다 작아질 때 캡처 로그가 발생하는지 관찰합니다. 최초 기준은 2m이고 다음 목적지에서는 1.75~2.5m 사이로 변합니다. 단순히 매 N physics tick을 저장하는 것과 다릅니다.
4. `left_sensor`/`right_sensor` 출력에서 동일 목적지를 서로 조금 다른 시점으로 보았는지 비교합니다. 멀리 떨어진 임의 외부 카메라의 사진이 아닙니다.
5. env-interval=3이면 세 목적지씩 한 배경을 사용합니다. 9 목적지에서 세 환경이 포함되는지 이미지를 확인합니다. 각 환경의 geometry가 항상 주행 경로 충돌 회피에 쓰이는 것은 아닙니다.

## USD, OmniGraph, Replicator 해설

Xform은 좌표 변환을 표현하는 prim입니다. `add_reference_to_stage`로 로봇 자산을 붙이면 그 아래 센서와 OmniGraph도 함께 구성됩니다. 카메라의 정확한 경로는 `/NavWorld/CarterNav/chassis_link/sensors/front_hawk/left/camera_left`와 대응하는 `right/camera_right`입니다. 오래된 문서 그림의 센서 이름을 현재 자산 경로로 추정해 대체하지 않습니다.

USD API로 dolly 위치/회전, 조명과 YCB props를 무작위화합니다. 처음 dolly를 정할 때 로봇에서 최소 거리를 확보합니다. timeline의 CURRENT_TIME_TICKED 이벤트에서 거리를 검사하고, SDG 중에는 timeline을 pause한 뒤 구독을 잠시 해제해 같은 접점에서 중복 캡처가 생기지 않게 합니다.

`BasicWriter`가 두 1024×1024 render product의 RGB를 저장합니다. `--use-temp-rp`는 이 5.1 구현에서 주로 `hydra_texture.set_updates_enabled`로 **이동 중 렌더 업데이트를 끄고 캡처 때 켜는 방식**입니다. 매 프레임 GPU 렌더를 계속 하지 않아 주행을 빠르게 할 수 있습니다. 최종 정리에서 writer detach, render product destroy, SDG graph 제거가 이루어집니다.

캡처는 `step(delta_time=0.0, rt_subframes=16)`으로 장면 시간을 고정하고 쓰기가 끝나기를 기다립니다. 모든 목적지가 끝나면 구독과 그래프를 정리합니다. `navigation.py`는 NVIDIA 원본의 실제 로봇 제어/배치 구현이며 별도의 가짜 위치 보간 로봇을 만들지 않습니다.

## 제한, 실험, 문제 해결

공식 자산의 navigation에는 **충돌 회피가 없습니다**. 이 실습은 지각 데이터 캡처 조건과 randomization을 배우기 위한 것입니다. 창고에서 물체를 피하는 Nav2 성능을 검증하는 예제로 해석하지 않습니다.

**--use-temp-rp만 켜고 끄며** 동일 seed=22, 목적지 수, 환경으로 두 실행 시간을 비교합니다. 실시간 변화와 초기 asset 로딩이 있어 단 한 번의 소요시간으로 일반화하지 않습니다. threshold나 환경 수까지 동시에 바꾸지 않습니다.

목적지에 도착하지 않으면 asset/OmniGraph 로드 오류와 targetXform 위치를 확인합니다. `--steps` 제한이 발생하면 데이터가 완성된 것으로 보고하지 않습니다. 네트워크 로딩 자체는 app update 수와 별도 비용이므로 로그에서 먼저 구분합니다. runtime 검증 상태는 manifest를 따릅니다. 원본 라이선스와 변경 사항은 NOTICE/Apache-2.0 파일에 있습니다.

## 출처와 버전

이 해설은 NVIDIA Isaac Sim **5.1.0** 문서와 해당 설치본을 기준으로 새로 작성했습니다. 원문의 전체 문장을 번역 복제한 것이 아니라 해당 워크플로를 독립적으로 실습하도록 설명했습니다.

- [공식 Randomization in Simulation – AMR Navigation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_amr_navigation.html)
- [scenario](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_amr_navigation.html#scenario)
- [implementation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_amr_navigation.html#implementation)
