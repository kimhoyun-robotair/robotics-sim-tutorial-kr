# 93. Tracy로 계산 시간과 앱 업데이트 시간 구분하기

## 이번에 배우는 것

**Python 계산에 이름 붙인 측정 구간을 만들고, 계산량 하나를 바꿔 Tracy에서 소요 시간의 변화를 비교합니다.**

앱이 느리다고 느껴질 때 전체 실행 시간만 재면 어느 부분이 오래 걸리는지 알기 어렵습니다. 프로파일러는 코드 구간별 시작과 끝을 기록합니다. Tracy에서 이 이름 붙인 구간을 **zone**이라고 부릅니다.

| 항목 | 의미 | 기본값 또는 결과 |
|---|---|---|
| `--items` | 한 번의 계산에 사용하는 항목 수 | 20000 |
| `--frames` | 콘솔 출력 한 배치의 업데이트 수 | 600 |
| `--steps` | 전체 앱 업데이트 한도 | GUI에서는 생략 시 계속 실행 |
| `lesson_cpu_batch` | 직접 표시한 CPU 계산 구간 | Tracy zone |
| `checksum` | 계산 결과의 누적합 | 콘솔 숫자, 시간 단위 없음 |

매 업데이트 전에 `sin` 값의 합을 계산합니다. 계산량과 앱 업데이트가 같은 반복문에 있으므로 전체 프레임과 특정 함수의 시간을 나누어 읽는 연습을 할 수 있습니다.

## 1. 계측한 프로그램과 Tracy 연결하기

Isaac Sim 5.1, 지원 NVIDIA GPU, GUI 세션과 `omni.kit.profiler.tracy`가 필요합니다. 저장소 루트에서 시작하세요.

```bash
python3 src/93_tools_profiling_performance/run.py --help
~/isaacsim/python.sh src/93_tools_profiling_performance/run.py \
  --frames 600 --items 20000
```

코드는 Tracy backend와 관련 확장을 활성화합니다. 최초 사용에 확장 다운로드가 필요하다면 registry 연결도 준비해야 합니다.

1. 실행 중인 앱의 **Profiler > Launch and Connect**로 함께 제공되는 Tracy UI를 엽니다.
2. 연결한 프로세스가 지금 실행한 standalone인지 확인합니다.
3. 초기 로딩이 지난 뒤 반복되는 CPU 구간을 확대합니다.
4. `lesson_cpu_batch`와 그 안의 `compute_values`를 찾습니다.
5. Tracy에서 수집을 Stop하고 Save trace로 기록을 저장합니다.

다른 Tracy 버전을 임의로 사용하는 것보다 설치에 포함된 UI를 사용하면 수집 프로토콜 버전을 맞추기 쉽습니다. 측정 후 앱 창을 닫으면 `finally`에서 앱을 정리합니다.

### 실행 결과 확인하기

기본 설정은 600번의 업데이트마다 다음 형태를 출력합니다.

```text
frames 600 items 20000 checksum ...
```

**checksum은 실행한 연산의 결과이며 밀리초나 FPS가 아닙니다.** 시간은 Tracy의 zone 표시에서 읽으세요. 짧게 끝난 마지막 배치가 있다면 출력의 frames도 600보다 작을 수 있습니다.

GUI에서 `--frames 600`은 출력 간격을 정할 뿐 창을 닫지 않습니다. `--steps 600`을 추가하면 전체 업데이트 600회 후 종료합니다. `--headless`에서 `--steps`를 생략하면 `--frames`에 지정한 한 배치 후 종료하므로 Tracy가 연결되기 전에 끝나지 않도록 실행 한도를 잡으세요.

## 2. 코드에서 측정 구간의 경계 읽기

### 코드에서 볼 부분

앱 생성 시 backend를 지정합니다.

```python
app = SimulationApp({
    "headless": args.headless,
    "profiler_backend": ["tracy"],
})
```

계산 함수는 다음과 같습니다.

```python
@carb.profiler.profile
def compute_values(count):
    return sum(math.sin(i * 0.001) for i in range(count))
```

`range(count)`는 0부터 count-1까지 순회합니다. 입력 항목이 많아지면 `sin` 계산과 덧셈도 늘어납니다. decorator는 이 함수 호출 범위를 계측에 연결합니다.

반복문은 더 바깥쪽 zone을 명시적으로 만듭니다.

```python
carb.profiler.begin(1, "lesson_cpu_batch")
try:
    checksum += compute_values(args.items)
finally:
    carb.profiler.end(1)
app.update()
```

`begin`과 `end`의 첫 인수 1은 같은 계측 마스크입니다. `finally`가 있어 계산 중 예외가 나도 열린 구간을 닫습니다. 시작·종료가 짝을 이루어야 다음 구간과 시간 범위가 섞이지 않습니다.

**`app.update()`는 `lesson_cpu_batch`가 끝난 뒤 호출됩니다.** 따라서 이 zone의 시간에는 Python 계산과 checksum 누적이 들어가지만 그 뒤의 Kit 업데이트 전체는 포함되지 않습니다. Tracy에서 두 구간을 무조건 같은 시간으로 읽으면 안 됩니다.

### 실행 결과 확인하기

Tracy에서 반복 구간의 다음 관계를 확인하세요.

```text
lesson_cpu_batch
    └─ compute_values
zone 종료
    → app.update()에서 앱 갱신
```

바깥 zone의 시간은 안쪽 함수의 시간을 포함합니다. 포함 관계에 있는 시간을 더하면 같은 계산을 두 번 세게 됩니다. 특정 프레임이 느릴 때는 CPU 계산 zone이 함께 길어졌는지, 앱 업데이트 쪽이 길어졌는지 살펴보세요.

기록을 보관하려면 저장소 루트에서 출력 폴더를 준비합니다.

```bash
mkdir -p src/93_tools_profiling_performance/output
realpath src/93_tools_profiling_performance/output
```

Tracy의 Save trace에서 위 폴더의 `items20000.tracy`로 저장하세요. 파일을 다시 열어 `lesson_cpu_batch`가 남아 있는지 확인합니다. `run.py` 자체에는 trace 파일 저장 코드가 없습니다.

### 일반 GUI의 CPU/GPU 계측과 C++ 구간 추가하기

로컬 계산 예제를 종료한 뒤 일반 Isaac Sim GUI 자체를 관찰하려면 다음처럼 앱을 시작할 수 있습니다. 이 인자는 `run.py` 뒤가 아니라 **앱 실행 명령**에 전달합니다.

```bash
~/isaacsim/isaac-sim.sh --enable omni.kit.profiler.tracy \
  --/profiler/enabled=true --/app/profilerBackend=tracy \
  --/profiler/gpu=true --/profiler/gpu/tracyInject/enabled=true
```

Profiler > Launch and Connect에서 GUI 프로세스에 연결하고 장면의 렌더링 구간을 관찰하세요. 이 실행에는 로컬 `compute_values`가 없으므로 그 zone을 찾지는 않습니다. CPU 호출 시간과 GPU 작업은 별도 트랙으로 읽고 Stop → Save trace로 `output/gui_capture.tracy`에 보관합니다. GPU 옵션을 켠 사실만으로 데이터가 수집됐다고 판단하지 말고 실제 GPU 트랙을 확인하세요.

C++ 확장에 측정 구간을 추가한다면 설치된 Carbonite의 `<carb/profiler/Profile.h>`를 포함합니다. 아래는 해당 함수 안에 넣을 구간의 형태이며 완전한 확장 프로그램은 아닙니다.

```cpp
{
    CARB_PROFILE_ZONE(1, "lesson_cpp");
    // 이 범위 안에 측정할 기존 C++ 작업을 둡니다.
}
```

첫 인수는 마스크이며 이름만 넘기는 호출과 다릅니다. scope를 벗어나면 구간이 자동으로 끝납니다. 사용 중인 C++ 확장을 재빌드하고 계측이 켜진 host에서 실제 함수가 호출될 때 `lesson_cpp`를 찾으세요. 이 튜토리얼에는 C++ 빌드 대상이 포함되어 있지 않으므로 위 발췌를 별도 파일로 실행할 수는 없습니다.

## 3. 연산량·시간·업데이트 수 정리

| 관찰값 | 설명할 수 있는 것 | 직접 설명하지 않는 것 |
|---|---|---|
| items | 한 호출의 반복 계산량 | 하드웨어의 실행 속도 |
| frames | 이번 배치의 앱 업데이트 수 | 시뮬레이션 경과 시간 |
| checksum | 누적한 계산 결과 | 지연 시간이나 FPS |
| zone duration | 선택 구간의 실제 소요 시간 | 모든 앱 작업의 합 |

**성능 비교에는 시간 측정 구간과 비교 조건을 함께 기록해야 합니다.** 이 예제의 CPU zone을 보면 계산 자체의 변화를 읽을 수 있고, 전체 프레임을 함께 보면 그 계산이 앱 진행에 차지하는 비중을 생각할 수 있습니다.

GUI 전체와 사용자 함수의 측정은 대상이 다릅니다. 제공 스크립트는 argparse로 학습 인자를 처리하므로 앱에 쓰는 임의의 Kit 옵션을 `run.py` 뒤에 붙이면 지원하지 않는 인자 오류가 납니다.

## 4. 간단한 확인 실험

일반 GUI 계측까지 진행했다면 그 앱을 종료하고 1절의 `run.py` 실행으로 돌아오세요. **`--items 20000`만 `--items 40000`으로** 바꾸세요. frames는 600으로 유지합니다.

두 번째 기록을 `output/items40000.tracy`로 저장하고 초기 extension·shader 로딩이 끝난 반복 구간을 비교합니다. 계산량이 늘었으므로 CPU zone이 길어지는 경향을 예상할 수 있습니다. 다만 다른 프로세스의 부하와 실행 환경도 영향을 주므로 정확히 두 배의 시간이나 특정 ms를 기대값으로 고정하지 마세요.

한 프레임의 극단적인 값보다 비슷한 길이의 구간에서 여러 호출의 시간 분포를 비교해 보세요. checksum 값도 달라질 수 있지만 그것은 성능 향상이나 저하의 크기를 뜻하지 않습니다.

## 실행할 때 막히면

- **Profiler 메뉴가 없음:** `omni.kit.profiler.tracy` 로드 상태와 Console의 확장 오류를 확인하세요.
- **연결되지만 원하는 zone이 없음:** 실행 중인 standalone에 연결했는지와 앱의 Tracy backend 설정을 확인하세요.
- **Headless trace가 비어 있음:** 수집 연결 전에 실행이 끝났을 수 있습니다. 더 긴 `--steps`로 관찰 시간을 확보하세요.
- **`.tracy` 파일이 없음:** 앱 종료와 trace 저장은 별개입니다. Tracy UI에서 Stop/Save trace를 수행하세요.
- **40000이 매번 정확히 두 배가 아님:** 시작 구간을 제외했는지, 비교 중 하드웨어·다른 부하가 같은지 확인하고 여러 zone을 비교하세요.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Profiling Performance Using Tracy](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/utilities/debugging/profiling_performance.html)에 대응합니다. 로컬 코드는 CPU 연산을 계측하며, C++ zone 추가나 GPU 전용 계측을 구현하지 않습니다.

이번 개정에서는 인자 도움말과 zone·출력·종료 조건을 코드로 대조했습니다. 실제 Tracy 연결, 측정 시간이나 trace 저장은 실행하지 않았습니다. `tutorial.json`의 검증 상태는 `not_run`입니다.
