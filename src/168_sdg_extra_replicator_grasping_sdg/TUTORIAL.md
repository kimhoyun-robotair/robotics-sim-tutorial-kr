# 168. 잡을 수 있는 자세와 실제로 닫힌 손가락은 어떻게 다른가요?

## 이번에 배우는 것

**캔을 잡을 후보 자세를 만들고, 각 자세에서 그리퍼를 닫은 뒤 관절 상태를 비교합니다.**

손가락이 물체 양쪽에 놓이는 자세를 찾았다고 해서 집기가 성공한 것은 아닙니다. 실제로 손가락을 닫으면 접촉 때문에 움직임이 달라질 수 있기 때문입니다. 이번에는 후보를 찾는 기하 계산과 후보를 시험하는 물리 계산을 차례로 실행합니다.

| 구성 | 이 실습에서 사용하는 값 | 확인할 질문 |
|---|---|---|
| 장면 | 공식 `sdg_grasping_xarm.usd` | 그리퍼와 캔이 어디에 있나요? |
| 후보 생성 | antipodal sampler, 기본 5개 요청 | 양쪽 표면을 잡을 자세가 있나요? |
| 평가 동작 | `grasp_config.yaml`의 `Close` | 접촉 후 손가락은 어디까지 닫히나요? |
| 기록 | `capture_*.yaml`, `summary.json` | 어느 후보를 몇 개 평가했나요? |

Antipodal은 물체의 서로 마주 보는 표면을 이용해 두 손가락의 접촉 후보를 찾는 방식입니다. 이 설정에는 물체를 들어 올리는 단계가 없으므로, 기록을 **중력 아래에서 물체를 유지한 집기 성공 라벨**로 읽으면 안 됩니다.

## 1. 먼저 후보 5개를 평가하기

Isaac Sim 5.1, RTX GPU와 드라이버, `isaacsim.replicator.grasping` 확장이 필요합니다. sampler가 사용하는 `libspatialindex`도 설치되어 있어야 합니다. Ubuntu에서 해당 라이브러리가 없다면 시스템 패키지 관리 방식에 맞게 `libspatialindex-dev`를 준비하세요.

기본 장면은 다음 원격 자산이며, 그 안에서 참조하는 그리퍼와 물체 자산에도 접근할 수 있어야 합니다.

```text
https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/5.1/Isaac/Samples/Replicator/Stage/sdg_grasping_xarm.usd
```

저장소 루트에서 실행하세요. 설치 위치가 다르면 `~/isaacsim`을 바꾸세요.

```bash
~/isaacsim/python.sh src/168_sdg_extra_replicator_grasping_sdg/run.py \
  --headless --samples 5 --steps 10000 \
  --output src/168_sdg_extra_replicator_grasping_sdg/output/first
```

기존 출력 폴더는 사용할 수 없습니다. 재실행할 때는 새 이름을 지정하세요. 로컬 자산팩을 사용한다면 `--scene /절대경로/sdg_grasping_xarm.usd`를 추가합니다.

화면에서 관찰하려면 `--headless --steps 10000`을 모두 빼세요. 평가는 한 번 수행하며, 끝난 뒤 창은 직접 닫을 때까지 남습니다. 여기서 `--steps`는 **평가를 기다리는 동안과 이후 GUI 관찰 동안의 Kit 업데이트 상한**입니다. 실제 손가락 닫힘 시간은 YAML 안의 물리 설정으로 결정합니다.

### 코드에서 볼 부분

`run.py`는 앱을 시작하고 장면을 연 뒤 아래 순서로 후보를 준비합니다.

```python
manager.sampler_config["num_candidates"] = args.samples
manager.generate_grasp_poses()
poses = manager.get_grasp_poses(in_world_frame=True)[:args.samples]
```

`--samples 5`가 설정 파일의 `num_candidates`를 덮어씁니다. 따라서 YAML의 후보 수만 바꾸고 같은 명령을 실행하면 요청 수는 여전히 5개입니다. `in_world_frame=True`는 물체 기준으로 찾은 자세를 실제 장면에 배치할 수 있는 세계 좌표로 받겠다는 뜻입니다.

평가 작업은 비동기로 실행됩니다. `app.update()`로 앱이 일을 처리하게 하면서 완료를 기다린 뒤 `task.result()`를 호출합니다. 이 마지막 호출은 작업 내부의 오류를 확인하는 역할도 합니다. 제한 횟수까지 끝나지 않으면 부분 출력은 남지만 완료 요약을 쓰지 않고 시간 초과를 알립니다.

### 실행 결과 확인하기

`output/first/summary.json`과 같은 폴더의 `capture_*.yaml`을 열어 보세요.

| 항목 | 읽는 방법 |
|---|---|
| `sampled_poses` | sampler가 실제로 얻은 후보 수입니다. 요청한 5개보다 적을 수 있습니다. |
| `evaluated_poses` | 그중 실제로 평가한 수입니다. |
| `result_files` | 평가 결과 파일 목록입니다. 길이가 `evaluated_poses`와 같아야 합니다. |
| capture의 `grasp_result` | 그리퍼·물체 경로, 그리퍼 위치·방향, `joint_states`를 연결해 읽습니다. |

후보가 0개이면 실행기는 오류로 종료합니다. 파일 수를 확인한 다음, 한 capture의 자세와 관절 값을 함께 읽어 **그 위치에서 닫기를 시도한 결과**임을 확인하세요. 평가 후 그리퍼가 초기 위치로 복귀할 수 있으므로 마지막 화면만으로 평가 자세를 판단하지 않습니다.

## 2. 닫힘 설정을 GUI와 연결해 보기

이번에는 어떤 조건으로 손가락을 닫았는지 살펴봅니다. `grasp_config.yaml`은 JSON 표기로 작성된 YAML이며 그대로 로드할 수 있습니다.

### 설정에서 볼 부분

`Close` 단계의 핵심은 다음과 같습니다.

```text
"joint_drive_targets": {
  "/World/Grippers/xarm_gripper/joints/drive_joint": 48.0
},
"simulation_step_dt": 0.016666666666666666,
"simulation_steps": 32
```

초기 `joint_pregrasp_states`는 열린 상태인 0이고, `drive_joint`의 닫힘 목표는 48도입니다. **목표 각도와 실제 관절 각도는 다릅니다.** 캔에 손가락이 닿으면 목표까지 이동하지 못할 수 있습니다. 닫힘에 배정한 물리 시간은 `32 × 1/60 ≈ 0.533초`입니다.

sampler의 `gripper_maximum_aperture=0.08`은 최대 입 벌림 0.08 m, `gripper_standoff_fingertips=0.17`은 손끝에 대한 접근 거리 0.17 m입니다. `grasp_align_axis=[0,1,0]`와 `gripper_approach_direction=[0,0,1]`은 **그리퍼의 로컬 축**입니다. 세계 좌표의 Y/Z 방향이라고 해석하면 그리퍼가 어느 쪽으로 접근하는지 이해하기 어렵습니다.

GUI에서 이 설정을 직접 확인하려면 다음 순서로 진행하세요.

1. 새 Isaac Sim 창에서 위 공식 장면을 엽니다.
2. `isaacsim.replicator.grasping.ui`를 켜고 **Tools > Replicator > Grasping**을 엽니다.
3. Config의 File Path에 이 폴더의 `grasp_config.yaml` 절대 경로를 넣고 Load합니다.
4. Gripper Path와 Object Path가 Stage의 `/World/Grippers/xarm_gripper`, `/World/Objects/_05_tomato_soup_can`을 가리키는지 확인합니다.
5. Grasp Pose Sampler에서 후보를 생성하고 자세를 하나씩 넘겨 보세요. Grasp Poses의 world/object-local 표시를 바꾸면 같은 후보가 다른 기준 좌표로 표현되는 것을 비교할 수 있습니다. Trimesh 표시로 실제 샘플링 표면도 확인합니다.
6. Grasp Phases에서 Close를 시험한 뒤 Workflow의 Number of Grasps Samples를 5로, Output Path를 새 폴더로 지정합니다. Overwrite Results를 끄고 Render each simulation step을 켠 뒤 **Start Workflow**를 누릅니다. 표본 수 -1은 생성된 후보 전체를 평가하는 선택입니다.
7. 같은 후보를 다시 시험하려면 Config Includes의 **Generated Grasp Poses**를 포함해 새 YAML로 저장합니다. sampler seed만 기록하는 것과 실제 생성된 자세 목록을 보관하는 것은 다릅니다.

직접 stepping과 timeline 모드는 물리 진행 방식의 선택입니다. GUI의 **Simulate using timeline** 또는 실행기의 `--timeline`이 타임라인 진행을 선택합니다. `--physics-scene`을 사용하려면 그 경로에 실제 PhysicsScene이 있어야 하며, 별도 장면으로 평가할 대상을 격리하는 설정까지 이해한 뒤 사용하세요. timeline 모드와 격리된 physics scene의 직접 stepping을 같은 동작으로 취급하지 않습니다. 기본 실습에는 두 옵션이 필요하지 않습니다.

## 3. 후보 생성과 물리 평가의 차이 정리

```text
캔의 표면 + 손가락 폭/접근 축
    → 기하적으로 가능한 후보 자세
    → 그 자세로 그리퍼 이동
    → 약 0.533초 동안 닫힘 목표 적용
    → 실제 자세와 관절 상태 저장
```

후보 수가 줄었다면 먼저 표면과 입 벌림 조건을 살펴봅니다. 후보는 만들어졌지만 관절 상태가 예상과 다르다면 접촉과 joint drive 설정을 확인합니다. 두 단계가 답하는 질문이 다르기 때문입니다.

또한 제공된 장면은 물체 중력이 꺼진 조건을 사용합니다. 물체를 들어 올리고 유지하는 성능을 알고 싶다면 중력, Lift 동작, 유지 시간, 성공 판정 기준을 별도로 구성해야 합니다. phase 이름만 `Lift`로 바꾸는 것으로 동작이 추가되지는 않습니다.

## 4. 간단한 확인 실험

`grasp_config.yaml`을 별도 파일로 복사해 `gripper_maximum_aperture`만 **0.08 → 0.03 m**로 바꾸세요. 새 설정을 `--config`로 전달하고 출력 이름도 바꿉니다.

다른 조건은 유지했으므로 바뀌는 것은 손가락이 벌어질 수 있는 폭입니다. 캔의 해당 표면 사이 거리가 너무 크면 후보가 줄거나 0개가 될 수 있습니다. `sampled_poses` 또는 후보가 없다는 오류를 관찰하세요. 이는 닫힘 물리 시간이 부족한 상황과 구분할 수 있는 결과입니다.

## 실행할 때 막히면

- **`libspatialindex` 관련 오류**: sampler의 CPU 라이브러리 의존성을 확인하세요. 렌더링 설정을 바꾸는 것으로 해결되지 않습니다.
- **장면이나 물체를 찾지 못함**: 기본 USD뿐 아니라 참조 자산의 접근 가능 여부와 YAML의 prim 경로를 확인하세요.
- **후보가 없음**: 물체 mesh, 최대 입 벌림, 접근 축, standoff 순서로 점검하세요. 임의의 그리퍼에 xArm 설정을 그대로 적용하지 않습니다.
- **손가락이 움직이지 않음**: phase가 실제 drive joint를 가리키는지, 그 joint에 구동 설정이 있는지 확인하세요.
- **평가 시간 초과**: 로그와 부분 capture를 확인한 뒤 새 출력 경로에서 상한을 늘리세요. `--steps`를 물리 단계 수로 해석하지 않습니다.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [Grasping Synthetic Data Generation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/synthetic_data_generation/tutorial_replicator_grasping_sdg.html)에 대응합니다. 공식 GraspingManager 흐름에 로컬 설정, 후보 수 제한, 결과 개수 확인을 연결한 실습입니다.

문서 개정에서는 실행기와 설정을 대조했습니다. GPU 후보 생성·물리 평가를 새로 실행하지 않았으며, `tutorial.json`의 상태는 `not_run`입니다. 위 결과는 직접 실행할 때 사용할 확인 기준입니다.
