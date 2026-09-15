# 49. 로봇 팔과 손은 어떻게 하나로 연결할까?

## 이번에 배우는 것

**UR10e의 말단에 Allegro hand를 고정 관절로 연결하고, 조립한 결과를 저장하는 과정을 배웁니다.**

손을 팔 끝에 옮겨 놓으면 정지 화면에서는 조립된 것처럼 보입니다. 하지만 물리를 재생했을 때도 함께 움직이려면 두 로봇 사이에 연결 조건이 필요합니다. Robot Assembler는 양쪽의 연결 기준점인 **mount frame**을 맞추고, 상대 위치와 방향을 유지하는 fixed joint를 만듭니다.

| 대상 | 이번 장면의 경로 | 역할 |
|---|---|---|
| 기준 로봇 | `/World/ur10e` | 손이 붙을 팔 |
| 팔의 mount | `/World/ur10e/ee_link` | 팔 끝 연결 기준점 |
| 붙일 로봇 | `/World/allegro_hand` | Allegro hand |
| 손의 mount | `/World/allegro_hand/allegro_mount` | 손 쪽 연결 기준점 |
| 저장 결과 | `assembled.usda`, `report.json` | 조립 stage와 fixed joint 목록 |

## 1. 먼저 Python으로 조립하기

Isaac Sim 5.1과 해당 버전 자산이 필요합니다. 코드가 5.1 Assets의 `Isaac/Robots/UniversalRobots/ur10e/ur10e.usd`와 `Isaac/Robots/WonikRobotics/AllegroHand/allegro_hand_instanceable.usd`를 읽습니다. 두 USD의 mesh와 재질 참조까지 접근할 수 있어야 합니다.

**저장소 루트**에서 실행하세요. 설치 위치가 다르면 `~/isaacsim`을 바꿉니다.

```bash
~/isaacsim/python.sh src/49_importers_assemble_robots/run.py \
  --steps 240 --output src/49_importers_assemble_robots/output/assembled
```

코드는 조립 후 240단계의 물리 preview를 진행하고 저장한 뒤 종료합니다. `--headless`를 붙이면 창 없이 실행합니다. GUI에서 `--steps`를 생략하면 240단계 preview와 저장을 마친 뒤 **정지한 장면을 계속 열어 둡니다.** 더 오래 움직임을 시험하려면 양수 `--steps`를 늘리세요. 출력은 기존 폴더를 덮어쓰지 않습니다.

### 코드에서 볼 부분

두 로봇은 새 stage에 reference로 추가합니다. 이어서 양쪽 mount 경로를 검사하고 조립을 시작합니다.

```python
assembler.begin_assembly(
    stage, '/World/ur10e', base_mount,
    '/World/allegro_hand', hand_mount,
    'Gripper', 'allegro_hand')
```

여기서 로봇 경로와 mount 경로는 다른 역할입니다. 로봇 경로는 **무엇을 붙일지**, mount 경로는 **어디를 맞출지**를 지정합니다. `Gripper`는 조립 구성을 구분할 이름입니다.

```text
두 자산 reference → begin_assembly()
    → 손 방향 조정 → assemble() → 물리 preview
    → mount 거리 측정 → stop() → finish_assemble() → 저장
```

방향 조정에서는 Z축 −90도 회전, 이어서 Y축 −90도 회전 행렬을 기존 변환에 곱합니다. 위치를 맞추는 것만으로 손가락이 원하는 방향을 바라보는 것은 아니므로 회전도 따로 맞춥니다. 회전 순서를 바꾸면 결과가 달라질 수 있습니다.

### 실행 결과 확인하기

터미널의 `Measured mounting-frame separation, meters:`는 preview 마지막에 측정한 **두 mount 원점 사이 거리(m)**입니다. 큰 거리가 남거나 손이 튀면 연결과 정렬을 다시 살펴보세요. 작은 거리만으로 손의 방향이나 모든 관절 자세에서의 안정성까지 확인한 것은 아닙니다.

`report.json`의 `fixed_joint_paths`에는 stage를 순회하며 찾은 **모든 fixed joint**가 들어갑니다. 원래 로봇 내부의 고정 관절도 포함되므로 항목 수만 세지 말고, 새 연결의 경로와 연결 대상 body를 `assembled.usda`에서 찾아보세요. JSON에는 mount 거리나 자동 합격 판정은 저장되지 않습니다.

## 2. 같은 연결을 Robot Assembler 창에서 만들기

수동 실습은 두 자산만 준비하는 모드로 시작합니다.

```bash
~/isaacsim/python.sh src/49_importers_assemble_robots/run.py \
  --prepare-only --output src/49_importers_assemble_robots/output/gui
```

1. **Tools > Robotics > Asset Editors > Robot Assembler**를 여세요.
2. Base Robot은 `/World/ur10e`, Attach Robot은 `/World/allegro_hand`로 선택합니다.
3. 양쪽 Attach Point에는 위 표의 mount 경로를 지정하고 namespace는 `Gripper`로 둡니다.
4. **Begin Assembly**를 누른 뒤 손의 방향을 조절하세요. 자동 코드의 방향과 비교하려면 Z −90도, Y −90도 순서에 맞춰 조정합니다.
5. **Assemble and Simulate**로 연결을 시험합니다. mount가 벌어지는지, 손과 팔의 collider가 겹쳐 튀는지 살펴보세요.
6. **End Simulation and Finish**를 누르고 **File > Save As**로 이 튜토리얼 폴더의 `output/gui/manual_assembled.usda`에 직접 저장하세요. 저장 대화상자에는 절대 경로를 지정합니다.
7. 저장한 stage를 새 창에서 다시 열고 Play하여 연결이 유지되는지 확인합니다.

### 설정에서 볼 부분

두 자산을 새 stage에서 reference하는 방식은 **Stage Editing**입니다. 조립 결과가 현재 stage에 작성됩니다. 기준 로봇 파일을 직접 열어 구성 variant로 저장하는 Direct Asset editing과 저장 위치가 다릅니다. 이 구분은 [공식 조립 절차](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup/assemble_robots.html#using-the-robot-assembler-tool)에서 확인할 수 있습니다.

Direct Asset editing을 비교하려면 기준 로봇 자산의 작업용 복사본을 직접 열고, 붙일 손만 reference로 추가한 뒤 같은 조립 순서를 진행하세요. Finish 시 `configuration/<robot_name>_<assembly_namespace>_<attach_robot_name>.usd`와 namespace에 해당하는 variant 선택이 만들어집니다. 구성 파일은 자동 저장되지만 **variant 선택을 남기려면 기준 stage도 저장해야 합니다.** 현재 `run.py`는 두 자산을 모두 reference하는 Stage Editing이므로 이 자산별 구성 파일을 출력하는 실행은 아닙니다.

`--prepare-only`도 초기에 `assembled.usda`와 `report.json`을 자동 저장합니다. 그러나 그때는 **사용자가 아직 조립하지 않은 준비 장면**일 수 있습니다. 이후 GUI 변경을 프로그램이 다시 자동 저장하지 않으므로 6번의 수동 저장을 마쳐야 합니다. `report.json` 역시 수동 작업 후의 보고서로 자동 갱신되지 않습니다.

## 3. 배치, 물리 연결, 저장의 차이 정리

| 단계 | 확인할 질문 |
|---|---|
| 배치 | 두 mount의 위치와 방향이 맞습니까? |
| 물리 연결 | Play 중에도 두 body의 상대 pose가 유지됩니까? |
| 저장 | 조립 도구 없이 다시 열어도 연결이 남습니까? |

Fixed joint의 연결 조건은 물리 재생 중에 적용됩니다. 정지 상태에서 손을 멀리 옮긴 뒤 Play하면 solver가 큰 오차를 한꺼번에 보정하려고 합니다. 그래서 **조립 전에 가까이 정렬하는 과정**이 물리 안정성에도 중요합니다.

조립 도중에는 임시 layer에 변경을 모아 취소할 수 있습니다. 완료한 조립을 저장하는 단계까지 마쳐야 새 장면에서도 같은 연결을 사용할 수 있습니다.

## 4. 간단한 확인 실험

1절과 같은 조건에서 **`--cancel`만 추가**하고 `--output` 경로 끝의 `assembled`를 `cancelled`로 바꾸세요.

이 분기는 조립을 시작한 뒤 `cancel_assembly()`를 호출합니다. `report.json`의 `cancelled`는 `true`가 되고 완성된 손 연결은 기대하지 않습니다. 두 stage의 새 연결 유무를 비교하세요. 취소된 stage에도 원래 로봇의 fixed joint는 남을 수 있으므로 “목록이 비었는가”를 기준으로 삼지 않습니다.

## 실행할 때 막히면

- **`Missing 5.1 mounting frame`**: 자산 버전과 mount 경로가 맞지 않습니다. 코드가 지정한 5.1 UR10e/Allegro 자산을 사용하세요.
- **GUI 로봇 목록이 비어 있음**: 선택 자산의 Robot Schema와 링크 관계를 확인하세요. 임의의 Xform은 로봇 선택 대상이 아닐 수 있습니다.
- **손이 튀거나 크게 벌어짐**: frame 정렬, collider 중첩, 기존 world 고정 관절을 확인하고 조립을 취소한 뒤 다시 시작하세요.
- **수동 조립이 재실행 때 사라짐**: 준비 단계의 자동 파일을 열었는지 확인하세요. Finish 후 직접 저장한 `manual_assembled.usda`를 열어야 합니다.
- **결과 파일이 없음**: preview가 끝나기 전에 창을 닫으면 저장 전에 반환합니다. 첫 실행은 `--steps 240`으로 완료를 기다리세요.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [Robot Assembler](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup/assemble_robots.html)에 대응합니다. 로컬 코드는 UR10e와 Allegro 조합의 조립, preview, 취소와 저장을 비교하도록 구성되어 있습니다.

`tutorial.json`은 `not_run` 상태입니다. 문서 개정에서는 코드와 공식 절차를 대조했으며, 실제 조립 안정성이나 GUI 저장 후 재로딩을 새로 검증하지 않았습니다.
