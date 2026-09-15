# 71. 여러 광선으로 지나가는 물체 감지하기

## 이번에 배우는 것

**수직으로 늘어선 광선 앞을 상자가 지나갈 때, 광선별 차단 여부와 맞힌 표면까지의 거리를 함께 읽습니다.**

한 개의 광선은 물체가 그 선을 지나갈 때만 맞힐 수 있습니다. 여러 광선을 높이 방향으로 배치하면 문 앞의 장막처럼 통과를 감지할 수 있습니다. 이번에는 상자를 좌우로 움직여 어느 광선이 언제 차단되는지 기록합니다.

| 구성 | 기본 설정 |
|---|---|
| `/World/Curtain` | 위치 `(0,0,0.25)` m의 Lightbeam 센서 |
| 광선 진행 방향 | +x 방향 |
| 광선 배치 방향 | +z 방향, 길이 1.5 m |
| 광선 수 | 기본 9개 |
| 대상 상자 | 한 변 0.5 m, 중심 x=3 m와 z=1 m 유지 |
| 기록 | `lightbeam.json`의 시간별 `beam_hit`, `depth_m` 배열 |

여기서 장막은 연속된 면이 아니라 **서로 떨어진 광선들의 집합**입니다. 광선 개수와 물체 크기의 관계가 검출 결과를 정합니다.

## 1. 움직이는 상자와 광선 장막 실행하기

Isaac Sim 5.1과 지원 NVIDIA GPU가 필요합니다. 저장소 루트에서 실행하세요.

```bash
~/isaacsim/python.sh src/71_sensors_sensors_physx_lightbeam/run.py --steps 240 --output src/71_sensors_sensors_physx_lightbeam/output/base
```

설치 위치가 다르면 `~/isaacsim`을 바꿉니다. 물리 240단계 동안 상자의 위치를 갱신하고 광선 결과를 저장한 뒤 종료합니다. 새 출력 폴더를 사용하세요. `--output`을 생략하면 이 튜토리얼의 `output/날짜_시간/`에 만듭니다.

창 없이 측정하려면 `--headless`를 추가하세요. `--steps 240`을 빼면 첫 기록을 저장한 뒤에도 GUI에서 상자가 계속 움직이지만 JSON은 늘어나지 않습니다. 저장 전에 창을 닫으면 결과 파일이 완성되지 않을 수 있습니다.

### 실행 결과 확인하기

`lightbeam.json`의 각 행을 다음 순서로 읽어 보세요.

| 필드 | 의미 | 확인 순서 |
|---|---|---|
| `time_s` | 물리 경과 시간(초) | 통과 전후 행의 순서 확인 |
| `beam_hit` | 광선별 맞힘 여부 | 어느 인덱스가 0/1로 바뀌는지 확인 |
| `depth_m` | 해당 광선의 거리(m) | hit가 있는 인덱스만 표면 거리로 해석 |

기본 설정에서 두 배열은 각각 9개 광선에 대응합니다. 상자가 y=0 부근을 지날 때 일부 광선이 맞고, 옆으로 충분히 벗어나면 모두 miss가 될 수 있습니다. 마지막 행만 보지 말고 처음부터 시간순으로 읽으세요.

상자 중심의 x는 3 m이고 한 변의 절반은 0.25 m입니다. 따라서 +x 방향 광선이 상자 앞면에 맞으면 거리는 **`3 - 0.25 = 2.75 m`** 부근입니다. miss인 광선의 거리값을 실제 표면 거리로 포함하면 이 비교가 흐려집니다.

## 2. 광선의 두 축과 상자 움직임 따라가기

### 코드에서 볼 부분

센서 생성에는 진행 방향과 배치 방향이 따로 있습니다.

```python
success, sensor = omni.kit.commands.execute(
    'IsaacSensorCreateLightBeamSensor', path='/World/Curtain',
    translation=Gf.Vec3d(0,0,.25),
    num_rays=args.rays, curtain_length=1.5,
    forward_axis=Gf.Vec3d(1,0,0),
    curtain_axis=Gf.Vec3d(0,0,1),
    min_range=.1, max_range=10, draw_lines=True,
)
```

`forward_axis`는 각 광선이 뻗는 방향입니다. `curtain_axis`는 광선들을 늘어놓는 방향입니다. 둘 다 +x로 주는 것이 아니라, 이 예제처럼 서로 다른 두 축을 사용해야 수직 장막을 만들 수 있습니다. `num_rays`를 늘리면 같은 1.5 m 범위에 더 많은 선이 배치됩니다.

상자의 이동은 다음 코드가 만듭니다.

```python
cube.set_world_pose(position=np.array([3., np.sin(i/30), 1.]))
world.step(render=True)
```

x와 z는 고정하고 y만 -1~1 m 사이에서 바뀝니다. `i`는 0부터 시작하는 물리 반복문 번호입니다. 물리 간격이 1/60초이므로 명목상 `y = sin(2t)` m이고 왕복 주기는 약 π초입니다. 이동 폭과 센서 장막의 폭을 혼동하지 마세요. 장막의 광선 원점은 y=0이고 상자가 그 앞을 가로지릅니다.

위치는 물리 계산 전에 지정하고 JSON의 `time_s`는 그 계산 후 기록합니다. 따라서 기록 시각으로 정확히 위치를 재구성할 때는 한 물리 단계 차이를 고려해야 합니다. `i=0`에서 y=0을 지정한 결과는 대략 `time_s=1/60`초 행에 대응합니다.

상자는 `FixedCuboid`로 만든 고정 collider의 위치를 코드가 직접 바꿉니다. 공중에 떠 있지만 중력으로 떨어지지 않는 이유입니다. 이 움직임은 힘을 가해 가속하는 동역학 실험이 아니라 **광선과 형상의 교차를 관찰하기 위한 입력**입니다.

```python
hits = np.asarray(interface.get_beam_hit_data(path))
depth = np.asarray(interface.get_linear_depth_data(path))
```

두 배열은 같은 센서 경로에서 읽습니다. 같은 인덱스의 hit와 depth를 짝지어야 “이 광선이 맞았고 거리는 얼마인가”를 알 수 있습니다. 모든 광선의 depth 평균을 먼저 계산하면 미검출 값이 섞입니다.

### 공식 GUI에서 hit 위치도 읽기

현재 실행을 종료하고 새 Isaac Sim 창에서 **Window > Examples > Robotics Examples > Sensors > Lightbeam**을 여세요. Play하면 표에 각 광선의 hit, linear depth, xyz hit position이 표시됩니다. Shift+왼쪽 드래그로 물체나 센서를 움직이며 같은 행의 맞힘 여부와 위치가 함께 바뀌는지 확인하세요.

이 표의 xyz는 광선이 맞은 위치를 직접 살펴보는 추가 정보입니다. 로컬 `lightbeam.json`은 hit와 거리만 저장하므로 xyz 열이 없어도 파일이 잘못 생성된 것은 아닙니다. GUI 예제의 표를 로컬 JSON의 필드와 구분하면 두 읽기 방식의 범위를 이해할 수 있습니다. [공식 Lightbeam 예제](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_physx_lightbeam.html#examples)를 함께 참고하세요.

## 3. 통과 여부와 거리의 관계 정리

```text
광선 높이가 상자의 높이 범위에 들어감
    + 상자가 y=0의 광선 앞을 가로지름
    → 해당 beam_hit 활성화
    → 상자 앞면까지 약 2.75 m

상자가 옆으로 벗어남
    → beam_hit 비활성화
    → 그 광선의 depth를 표면 거리로 사용하지 않음
```

상자는 x를 바꾸지 않으므로 hit가 생기는 시간은 바뀌어도, 맞은 광선의 거리는 비슷할 수 있습니다. **검출 여부의 변화와 거리의 변화는 서로 다른 정보**입니다. 이 모델은 PhysX 광선 교차를 보여 주며 실제 안전 장치의 응답 지연이나 제어 회로를 측정하는 실습은 아닙니다.

## 4. 간단한 확인 실험

광선 수만 9개에서 3개로 줄여 보세요.

```bash
~/isaacsim/python.sh src/71_sensors_sensors_physx_lightbeam/run.py --steps 240 --rays 3 --output src/71_sensors_sensors_physx_lightbeam/output/rays3
```

장막 길이와 상자 크기·경로는 같습니다. 배열 길이가 3으로 줄었는지, 동시에 hit가 되는 광선 개수가 어떻게 달라지는지 비교하세요. 맞은 광선의 거리 기준은 여전히 약 2.75 m입니다.

기본 상자는 중앙 광선에도 걸릴 수 있으므로 광선 수가 줄었다고 전체 검출이 반드시 사라지지는 않습니다. 이 실험에서는 **높이 방향의 샘플 수가 줄어드는 것**을 확인합니다. 더 작은 물체라면 광선 사이를 통과할 수 있다는 점도 여기서 이해할 수 있습니다.

## 실행할 때 막히면

- **모든 행이 miss임**: 대상의 collider, 광선 진행 축, 높이 배치와 0.1~10 m 거리 범위를 확인하세요.
- **마지막 행만 모두 0임**: 상자가 옆으로 벗어난 순간일 수 있습니다. 앞선 행에 hit가 있었는지 먼저 보세요.
- **상자가 떨어지지 않음**: 이 예제는 위치를 직접 바꾸는 고정 collider입니다. 중력 낙하는 구현하지 않습니다.
- **거리가 3 m가 아님**: 3 m는 상자 중심입니다. 앞면까지의 거리는 약 2.75 m입니다.
- **광선 수를 줄였는데 여전히 검출됨**: 남은 광선 중 하나라도 상자를 맞히면 검출됩니다. 전체 hit 유무와 hit 광선 개수를 구별하세요.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [PhysX SDK Lightbeam Sensor](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_physx_lightbeam.html)에 대응합니다. 공식 광선별 hit·거리 개념을 자동 왕복 상자와 JSON 기록으로 구현했습니다.

기존 [RUNTIME_CHECK.md](RUNTIME_CHECK.md)는 기본 광선 수의 headless 30단계에서 2.75 m 검출과 마지막 행의 전 광선 miss를 확인한 과거 기록입니다. 두 관찰은 물체가 지나간 시계열의 서로 다른 상태입니다. 현재 파일의 재실행이나 광선 수 변경·GUI 조작까지 확인한 것은 아니므로, 각 실행의 hit와 거리로 결과를 대조하세요.
