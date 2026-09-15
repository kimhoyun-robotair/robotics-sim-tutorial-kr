# 172. t178 · NuRec 신경 재구성 장면에서 Carter 주행

권장 학습 순서 **172** · 고급 데이터 생성과 외부 시스템 통합 · 출처 ID `t178`

실제 사진으로 재구성한 3D Gaussian 기반 NuRec 장면을 USD로 열고 Nova Carter의 navigation graph를 실행한다. 이 패키지는 **실제 NuRec dataset**을 입력으로 요구한다. 빈 stage나 일반 cube로 신경 렌더링을 대신하지 않는다. `run.py`는 원문의 네 가지 장면 중 하나를 선택하여 bounded simulation을 실행하고 실제 chassis 위치를 `trajectory.json`에 기록한다.

## 준비

- Isaac Sim **5.1.0**, 지원 RTX GPU/드라이버와 NuRec neural volume renderer가 필요하다. 렌더링 요구 사항과 지원 제한은 [NVIDIA NuRec 문서](https://docs.omniverse.nvidia.com/materials-and-rendering/latest/neural-rendering.html)를 확인한다. 일반 mesh viewport가 동작한다고 NuRec 렌더링도 검증된 것은 아니다.
- [NVIDIA PhysicalAI-Robotics-NuRec dataset](https://huggingface.co/datasets/nvidia/PhysicalAI-Robotics-NuRec)을 별도로 준비한다. 이 패키지는 대형 데이터셋을 자동 다운로드하지 않는다. USD/US DZ만 떼어 복사하지 말고 참조하는 volume·texture 리소스를 포함한 구조를 유지한다.
- Isaac Sim asset root에서 `/Isaac/Samples/Replicator/OmniGraph/nova_carter_nav_only.usd`와 참조된 Carter 자산을 읽을 수 있어야 한다. 코드는 이 공식 graph의 Script Node 실행 opt-in을 켠다.
- 자신이 사진을 학습시켜 장면을 만들 때는 [3DGruT](https://github.com/nv-tlabs/3dgrut)의 학습/export 환경을 별도로 준비한다. 이 튜토리얼은 이미 재구성한 dataset을 사용하며 재구성 학습을 실행하지 않는다. 외부 repository의 현재 버전과 Isaac Sim 5.1 호환 export를 기록한다.

## 실행과 장면 선택

```bash
cd /path/to/172_digital_twin_nurec_navigation
python3 run.py --help
python3 run.py --dataset /data/PhysicalAI-Robotics-NuRec --scenario cafe --check
"$HOME/isaacsim/python.sh" run.py --dataset /data/PhysicalAI-Robotics-NuRec \
  --scenario cafe --output output/cafe
```

`--check`는 선택한 로컬 root USD가 존재하는지만 검사한다. renderer·reference 완전성·주행 검증은 실제 실행이 필요하다. 기본 실행은 사용자가 창을 닫을 때까지 주행과 GUI 업데이트를 계속한다. 화면이 필요 없으면 `--headless`를 사용한다. 출력 경로가 이미 있으면 다른 경로를 선택해야 한다.

| scenario | 데이터셋 root 아래 stage | 시작 위치 | targetXform의 상대 이동 | collision ground 추가 |
|---|---|---|---|---|
| cafe | `nova_carter-cafe/stage.usdz` | (0,0,0) | (−3,−1.5,0) | 아니오 |
| galileo | `nova_carter-galileo/stage.usdz` | (−2.5,2.5,0) | (4,0,0) | 아니오 |
| wormhole | `nova_carter-wormhole/stage.usdz` | (0,0,0) | (5,0,0) | 아니오 |
| lounge | `zh_lounge/usd/zh_lounge.usda` | (−1.5,−3,−1.6) | (−0.5,5,−1.6) | 예 |

위 값은 공식 예제의 값을 `scenarios.json`에 옮긴 것이다. target은 parent 아래의 로컬 transform이므로 세계 좌표라고 생각하고 시작 위치와 무조건 같게 계산하지 않는다. 수정할 때 Stage의 transform hierarchy를 먼저 확인한다.

`--steps`를 생략하면 GUI에서 사용자가 창을 닫을 때까지 시뮬레이션을 계속합니다. `--steps 500`처럼 횟수를 지정하면 자동 종료합니다. `--headless` 실행에서 생략하면 500회로 제한됩니다.


## 단계별 관찰

1. cafe를 열어 Gaussian neural volume 배경이 실제로 나타나는지 확인한다. Stage에서 기존 dataset prim들과 추가된 `/World/NovaCarterNav`를 구분한다.
2. robot의 `targetXform`과 `chassis_link`가 존재해야 한다. 코드가 해당 prim을 못 찾으면 즉시 오류를 낸다. 누락 자산을 그대로 두고 simulation을 성공 처리하지 않는다.
3. `Synchronous` physics update로 navigation graph와 물리의 진행 순서를 맞춘다. 원문처럼 기존 PhysicsScene을 찾아 설정하고, 없으면 이 로컬 실행기는 새 scene을 만든다.
4. 주행 중 Carter의 위치 변화를 보고 `output/cafe/trajectory.json`의 `timeline_seconds`와 `chassis_world_position`을 읽는다. 10 update마다 그리고 마지막 update에 실측한 값이다. 설정한 target을 position 결과로 대신 쓰지 않는다.
5. `--scenario galileo`, `wormhole`, `lounge`를 새 출력 경로로 각각 실행한다. lounge는 시작 z=−1.6 위치에 10배 scale의 invisible plane을 만들고 CollisionAPI를 붙인다. 시각적으로 안 보이는 plane도 물리 접촉을 만들 수 있다.
6. 각 장면에 대해 neural rendering 여부, robot가 지면에 지지되는지, 목표 방향으로 진행하는지 기록한다. `--steps 500`으로 제한한 실행의 종료가 반드시 목표 도달을 뜻하지 않는다. pose 변화와 실제 장애물/주행 상태를 함께 확인한다.

## API와 개념

`SimulationApp`을 만든 뒤 Omniverse 모듈을 가져온다. `open_stage()`는 USD(Z) scene을 합성하고, `add_reference_to_stage()`는 로봇을 현재 stage에 추가한다. USDZ는 관련 파일을 포장하는 형식이며 모든 외부 dependency를 반드시 내장한다는 보장은 없다.

`PhysxSchema.PhysxSceneAPI`의 update type은 물리와 앱의 동기 방식을 지정한다. `UsdPhysics.CollisionAPI`는 ground plane에 충돌을 부여한다. Neural volume은 렌더링 표현이며 충돌용 surface와는 별개이다. 사진에서 바닥이 보인다는 이유만으로 PhysX 지면이 있다고 판단하지 않는다.

`UsdGeom.Xformable.ComputeLocalToWorldTransform()`은 실제 chassis의 world transform을 계산한다. `targetXform`은 원문 navigation graph가 읽는 목적지이고, 이 패키지가 별도의 경로 planner를 구현한 것은 아니다. 그래프의 script·asset dependency를 포함해 native behavior를 사용한다.

한 변수 실험은 cafe의 `relative_target` x만 −3에서 −2로 바꾸는 것이다. 동일한 start와 step 수로 주행 궤적을 비교한다. scene과 ground 설정을 동시에 바꾸지 않는다. viewer에 배경이 비어 있으면 dataset 파일·NuRec renderer부터, robot가 떨어지면 collision부터, robot가 멈추면 graph/target/physics synchronous 상태부터 확인한다.

## 출처와 검증

- [Isaac Sim 5.1 · Neural Volume Rendering](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/assets/usd_assets_nurec.html), [전제 조건과 dataset](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/assets/usd_assets_nurec.html#prerequisites)
- 원문의 standalone/Script Editor 예제는 네 장면을 순회한다. 로컬 코드는 `--scenario`로 하나씩 재현하고, 인수·누락 입력 검사·선택적 종료 횟수·관측 궤적 저장을 추가했다. 다른 로컬 패키지의 도움 코드를 필요로 하지 않는다.
- 작성 과정에서는 compile과 일반 Python CLI help만 확인했다. NuRec dataset 로딩, GPU neural rendering, 주행 및 목표 도달은 실행하지 않았고 manifest는 `not_run`이다.
