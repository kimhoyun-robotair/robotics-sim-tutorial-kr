# 154. 난수 범위가 만드는 공간을 점구름으로 보기

## 이번에 배우는 것

**Distribution Visualizer에서 회전·이동 범위가 합쳐진 위치 분포를 보고, 같은 범위를 YAML 장면으로 생성합니다.**

장면 한 장만 보면 물체가 그곳에 놓인 것은 알 수 있지만 어디까지 놓일 수 있는지는 알기 어렵습니다. Distribution Visualizer는 여러 가능한 위치를 점구름으로 표시해 난수 규칙의 공간적 모양을 살펴보게 합니다.

| 비교 대상 | 보여 주는 것 | 저장 데이터와의 관계 |
|---|---|---|
| Visualizer 점구름 | 변환 범위로 만들 수 있는 위치 표본 | 분포를 살피는 GUI 표시 |
| 선택한 Torus | 현재 변환값을 적용한 물체 | 편집 중인 한 사례 |
| `scene.yaml`의 `subject` | 프레임마다 선택한 Torus 한 개 | Object SDG가 영상·정답으로 저장 |

점 하나마다 실제 Torus 객체가 생기거나 물리 계산이 수행되는 것은 아닙니다. 이번 실습에서는 **가능한 배치의 범위와 한 번 뽑은 배치**를 구분해서 봅니다.

## 1. Visualizer에서 분포 범위 조절하기

Isaac Sim 5.1, RTX GPU, `isaacsim.replicator.object` 확장을 사용합니다. 저장소 루트에서 다음 명령으로 새 GUI를 여세요.

```bash
cd src/154_events_ext_replicator_object_distribution_visualizer
~/isaacsim/python.sh run.py --launch
```

이 호출은 `prepared.yaml`을 준비하고 앱을 열지만 Visualizer를 자동 조작하지는 않습니다. 다음 절차를 직접 진행하세요. 기존 stage를 사용하고 있다면 먼저 저장합니다.

1. **Window > Extensions**에서 `isaacsim.replicator.object`가 켜졌는지 확인합니다.
2. **Tools > Action and Event Data Generation > Distribution Visualizer**를 엽니다.
3. 빈 장면에서 **Create > Mesh > Torus**, **Create > Light > Dome Light**를 만듭니다.
4. Torus를 선택하고 **F**로 초점을 맞춥니다. viewport를 **Path Tracing** 모드로 바꿉니다.
5. 빈 곳을 클릭해 선택을 해제한 뒤 Torus를 다시 선택합니다.
6. **Apply Preset xformOps**를 누른 다음 선택을 다시 해제하고 Torus를 재선택합니다.

preset 이후에는 바깥쪽부터 `rotateY`, `rotateX`, `translate` 순서가 표시됩니다. `translate`에 `local` 접미사가 붙어 보일 수 있습니다. UI와 Stage 선택이 같은 Torus를 가리키는지 확인하세요.

### 설정에서 볼 부분

각 연산에는 `value`, `start`, `end`가 있습니다. `value`는 현재 물체의 자세이고 `start`·`end`는 무작위 표본을 뽑을 범위입니다. 아래처럼 입력해 보세요.

| 연산 | start | end |
|---|---:|---:|
| `rotateY` | -120° | 120° |
| `rotateX` | -30° | 30° |
| `translate` X | 0 | 0 |
| `translate` Y | 0 | 0 |
| `translate` Z | 150 | 300 |

IRO 장면은 Y-up·cm를 사용합니다. 회전이 정한 방향으로 로컬 Z 이동을 하므로 위치의 원점 거리에는 150~300 cm 범위가 생깁니다. 앞의 회전 각도 범위가 방향을 제한해 완전한 구 전체가 아닌 껍질 일부를 만듭니다.

### 실행 결과 확인하기

점구름이 두께 있는 구 껍질 일부처럼 펼쳐지는지 보세요. 현재 Torus는 `value`의 자세에 있을 수 있으므로 점구름 전체 모양과 물체 하나의 위치를 같은 것으로 읽지 않습니다.

`rotateY`와 `rotateX`의 `value`만 조절하면 현재 물체 자세를 살펴볼 수 있습니다. 가능한 배치 영역을 바꾸려면 `start`·`end`를 편집해야 합니다. 이 차이를 확인한 뒤 원래 범위로 맞추고 다음 절로 진행하세요.

## 2. 같은 범위를 YAML로 생성하기

이 폴더의 `scene.yaml`은 위 범위를 저장 가능한 장면에 넣은 설정입니다. GUI의 편집값을 자동으로 내보내는 기능을 `run.py`가 제공하는 것은 아니므로, 두 범위를 직접 대조합니다.

### 설정에서 볼 부분

```yaml
transform_operators:
- rotateY:
    distribution_type: range
    start: -120
    end: 120
- rotateX:
    distribution_type: range
    start: -30
    end: 30
- translate:
    distribution_type: range
    start: [0, 0, 150]
    end: [0, 0, 300]
- scale: [0.3, 0.3, 0.3]
```

마지막 배율은 Torus의 크기만 바꿉니다. 앞선 회전·이동이 정한 중심 위치 범위는 유지합니다. `subject`에 count를 늘리는 설정은 없으므로 프레임마다 Torus 한 개가 만들어집니다.

GUI의 **Tools > Action and Event Data Generation > Object SDG**를 열고 첫 명령이 출력한 `configuration:` 경로를 **Description File**에 넣으세요. **Initialize scene randomization → Randomize scene**으로 실제 Torus 배치를 비교하고 **Simulate**로 세 장을 저장합니다. 이 초기화는 앞의 수동 장면을 교체합니다.

창 없이 YAML 장면만 생성하려면 GUI를 종료한 뒤 다음 명령을 사용합니다.

```bash
~/isaacsim/python.sh run.py --launch --headless --frames 3
```

`--launch`가 없는 호출은 경로를 해소한 YAML만 만듭니다. Headless 실행은 영상 생성을 수행하지만 앞 절의 Visualizer 선택·슬라이더·점구름을 검사하는 방식은 아닙니다. GUI는 직접 닫을 때까지 유지되며 `--steps`를 생략하세요. 설치 위치를 바꿀 때는 Python 경로와 `--isaac-root`를 함께 지정합니다.

### 실행 결과 확인하기

콘솔의 이번 `output:` 폴더에서 `images/`의 640×480 RGB와 `descriptions/`를 봅니다. 카메라는 원점에서 1000 cm 물러나 있고 Y 30도·X -15도로 배치됩니다. 저장 영상의 Torus가 가려지면 Stage와 description으로 실제 위치도 확인하세요.

description에서는 최종 변환이 단일 행렬로 저장됩니다. `global_transform` 마지막 행의 중심 `(x,y,z)`로 `sqrt(x²+y²+z²)`를 계산해 150~300 cm 범위와 비교할 수 있습니다. 원래 두 각도의 개별 범위는 `prepared.yaml`이나 초기화 Stage에서 확인합니다.

## 3. 점구름과 데이터 프레임의 차이 정리

```text
범위 설정 → 여러 표본의 합성 변환 → Visualizer 점구름
같은 범위 설정 → 한 프레임의 변환 선택 → Torus 하나와 RGB·정답
```

점구름의 모양은 어느 영역을 덮는지 이해하는 데 도움이 됩니다. 그러나 각도를 균등하게 선택했다고 구면의 면적마다 같은 밀도로 물체가 배치되는 것은 아닙니다. 눈으로 본 점구름이나 세 장의 RGB만으로 확률 밀도의 균일성까지 결론 내리지는 마세요.

## 4. 간단한 확인 실험

1절의 GUI를 다시 열어 같은 Torus와 범위를 준비한 뒤, Visualizer에서 **`translate` Z의 `end`만 300에서 150으로** 바꿔 보세요. start는 이미 150입니다.

반지름이 150 cm로 고정되므로 점구름의 반지름 방향 두께가 사라지고 얇은 곡면에 가까워집니다. 두 회전의 범위는 같아 방향으로 펼쳐진 영역은 유지됩니다. 현재 물체를 더 작게 만드는 효과와는 다르다는 점을 관찰하세요.

## 실행할 때 막히면

- **Visualizer에 변환 목록이 없음**: Torus 선택을 해제했다가 다시 선택하세요. preset 적용 뒤에도 재선택으로 UI를 동기화합니다.
- **preset 뒤 Torus가 사라짐**: 원점에서 이동한 것입니다. Stage에서 Torus를 선택하고 **F**로 다시 초점을 맞춥니다.
- **value를 바꿨는데 점구름 범위가 그대로임**: value는 현재 자세이고 start·end가 분포 범위입니다.
- **GUI 점구름과 RGB의 개수가 다름**: 점구름은 가능한 위치 표본입니다. YAML은 한 프레임에 Torus 하나를 생성합니다.
- **headless 실행에서 Visualizer를 볼 수 없음**: 해당 명령은 YAML의 데이터 생성용입니다. 앞 절의 GUI 절차로 Visualizer를 관찰하세요.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Distribution Visualizer](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_replicator-object/distribution_visualizer.html)에 대응합니다. 공식 GUI 절차와 같은 변환 개념을 사용하되 이 폴더의 반지름은 150~300 cm로 구성했습니다.

GUI 조작과 YAML 데이터 생성은 별도 확인 대상입니다. 두 경로의 실제 실행 검증 상태는 `tutorial.json`의 `not_run`을 참고하세요.
