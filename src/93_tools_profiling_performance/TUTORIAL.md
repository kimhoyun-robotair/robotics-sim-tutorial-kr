# 93. Profiling Performance Using Tracy

권장 학습 순서 **93** · OmniGraph와 확장 개발 · 출처 ID `t171`

Tracy로 실제 CPU 계산과 Kit 프레임을 관찰한다. 제공 script의 zone은 실제 sin 합계를 계산하며 preset 시간이나 가짜 성능값을 출력하지 않는다.

## 준비와 GUI 연결

Isaac Sim 5.1.0과 GPU, 그래픽 화면이 있는 컴퓨터가 필요하다. 이 폴더는 외부 자산 없이 실행한다. Isaac Sim을 켜고 `Window > Extensions`에서 **omni.kit.profiler.tracy**를 검색해 켠다. registry에서 extension을 가져오는 최초 실행에는 인터넷이 필요할 수 있다.

1. **Profiler > Launch and Connect**로 Isaac Sim에 포함된 Tracy를 연다. 외부 임의 버전보다 이 binary를 사용하여 protocol 버전을 맞춘다.
2. 타임라인에서 구간을 선택해 CPU thread/zone과 frame 시간을 확대한다. Tracy **Stop**으로 수집을 중지하고 **Save trace**로 이 폴더 `output/gui_capture.tracy`에 새 이름으로 저장한다.
3. Isaac Sim을 종료해도 Tracy UI를 열어 두면 다음 standalone에 연결할 수 있다.

## standalone 계측

```bash
python3 run.py --help
export ISAAC_SIM_PATH="$HOME/isaacsim"
"$ISAAC_SIM_PATH/python.sh" run.py --frames 600 --items 20000
```

`--steps`를 생략한 GUI 실행은 창을 직접 닫을 때까지 측정을 반복한다. `--frames 600`은 체크섬을 출력하고 다음 측정을 시작하는 배치 크기이며 창의 수명을 제한하지 않는다. `--steps 600`을 추가하면 전체 `app.update()` 600회 후 종료한다. 물리 시뮬레이션 시간이 아니라 Kit 업데이트 횟수다. `--headless`에서 `--steps`를 생략하면 `--frames`에 지정한 한 배치만 실행하고 종료한다.

1. 실행 중 Tracy의 **Connect**로 연결한다. 기본 GUI 실행은 연결을 기다리는 동안에도 측정 배치를 계속 반복한다.
2. `lesson_cpu_batch`와 `compute_values` zone을 찾아 표시되는 nested scope를 확인한다. 체크섬은 연산이 실제 수행되었다는 관측용 값이지 성능 기준이 아니다.
3. Stop/Save trace로 `output/items20000.tracy`에 저장한다. 두 번째는 **items만 40000**으로 바꾸고 같은 frames로 실행하여 `output/items40000.tracy`에 저장한다.
4. startup(shader/extension 로드) 구간을 제외한 반복 구간에서 zone 시간 분포를 비교한다. 절대 시간은 하드웨어/부하에 따라 달라지며 정확히 두 배라고 가정하지 않는다.

## Python/C++ zone과 옵션

`SimulationApp({"profiler_backend": ["tracy"]})`는 profiler backend를 시작한다. `@carb.profiler.profile`는 함수 범위를, `carb.profiler.begin(1, "...")`/`end(1)`는 작은 구간을 계측한다. `finally`로 end를 보장하여 zone stack이 깨지지 않게 한다.

C++ 확장에서는 `<carb/profiler/Profile.h>`를 포함하고 해당 SDK의 `CARB_PROFILE_ZONE` macro 시그니처에 맞춰 scope를 만든다. 5.1 포함 Carbonite header에서는 `CARB_PROFILE_ZONE(mask, ...)`이므로 `CARB_PROFILE_ZONE(1, "lesson_cpp")`처럼 mask와 이름을 함께 사용한다. 원문 축약 예제의 include/인자보다 실제 설치 header가 기준이다.

고급 CLI는 `--/profiler/enabled=true`, `--/app/profilerBackend=tracy`가 핵심이며 GPU 계측에는 `--/profiler/gpu=true`, `--/profiler/gpu/tracyInject/enabled=true`를 사용할 수 있다. 원문에는 channels/fibers/clock calibration 옵션도 제시하지만 먼저 기본 trace를 확보한다. 제공 script는 argparse가 정의한 학습 인자를 사용하므로 임의 Kit 인자를 붙이는 대신 `SimulationApp` 설정이나 확장 GUI를 사용한다.

성공 기준은 실제 zone이 trace에 나타나고 한 변수 변경에 따른 구간 시간 차이를 관찰·저장하는 것이다. 빈 trace는 backend 활성, protocol 버전, Connect 대상과 실행 지속 시간을 확인한다. headless에도 Tracy 연결은 가능하지만 trace UI는 별도 켜 두어야 한다.

## 검증 범위

제공된 Python/JSON/TOML의 문법과 5.1 설치 소스/API를 대조했다. GPU/Kit에서 화면과 동작은 아직 실행하지 않았으므로 manifest는 `verification: not_run`이다. 아래 성공 기준을 실제 실행 후 확인해야 한다.

## 출처

- [Isaac Sim 5.1 공식 원문](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/utilities/debugging/profiling_performance.html).
