# 디버깅, 성능 측정과 배포

성능 문제는 “GPU가 느리다” 하나로 설명되지 않는다. physics step, render, sensor readback, ROS serialization, Python callback, asset streaming을 분리해 측정하다.

## 재현 가능한 진단 순서

1. 빈 stage가 시작되는지 확인하다.
2. 동일 stage에서 sensor와 ROS Bridge를 끄고 real-time factor를 재다.
3. rendering을 끄거나 resolution을 낮춰 차이를 재다.
4. robot 수와 sensor 수를 각각 하나씩 늘려 scaling을 기록하다.
5. log의 첫 오류부터 해결하고 뒤따르는 연쇄 오류를 원인으로 오해하지 않다.

## VS Code와 running app에 attach하다

standalone debugging은 Linux에서 지원하다. Isaac Sim App Selector 또는 설치 디렉터리 terminal에서 VS Code를 열고 제공되는 launch configuration을 사용하다. GUI application에 attach할 때는 `omni.kit.debug.vscode_debugger` extension을 활성화하고, listening port를 외부 네트워크에 무방비로 열지 않다.

## Tracy profiler를 사용하다

```bash
"$ISAACSIM_PATH/python.sh" my_script.py \
  --enable omni.kit.profiler.tracy
```

스크립트도 profiler backend를 활성화하다.

```python
from isaacsim import SimulationApp

simulation_app = SimulationApp(
    {"headless": False, "profiler_backend": ["tracy"]}
)
```

관심 함수에 zone을 추가하다.

```python
import carb


@carb.profiler.profile
def update_controller():
    ...
```

평균 frame time만 보지 말고 spike, GPU/CPU overlap, sensor 주기, Python garbage collection을 함께 보다.

## 안전한 최적화 순서

- headless batch에서 불필요한 viewport update를 끄다.
- camera resolution과 동시 render product 수를 요구사항까지 줄이다.
- static/shared asset은 reference, payload, instanceable 구조를 검토하다.
- collision mesh 복잡도와 solver iteration을 필요 수준으로 낮추다.
- sensor publish rate와 physics rate를 분리하고 무조건 매 frame publish하지 않다.
- Python per-prim loop를 batch API 또는 vectorized operation으로 바꾸다.

```python
simulation_app = SimulationApp(
    {"headless": True, "disable_viewport_updates": True}
)
```

이 option은 headless에 사용하다. streaming workflow에서는 viewport가 필요하므로 그대로 적용하지 않다. texture streaming을 끄면 일부 workload가 빨라질 수 있지만 VRAM 사용과 missing texture 위험이 커지므로 측정 없이 기본값을 바꾸지 않다.

## container와 cloud

Isaac Sim container는 Linux에서 지원하다. host driver와 NVIDIA Container Toolkit, GPU 전달, EULA 동의, asset cache/output volume, network port를 명시하다. image 안에 학습 결과를 저장하지 말고 volume에 기록하다.

```bash
docker run --rm --gpus all \
  --network host \
  -e ACCEPT_EULA=Y \
  -v "$ISAACSIM_COURSE/outputs:/workspace/outputs" \
  nvcr.io/nvidia/isaac-sim:5.1.0 \
  ./runheadless.sh -v
```

명령의 NGC image는 Isaac Sim 5.1.0으로 고정되어 있다. 먼저 `docker login nvcr.io`를 공식 절차대로 완료하되 credential을 Dockerfile이나 repository에 기록하지 않다.

WebRTC livestream은 instance당 한 방식·한 client 제약을 고려하고 NVENC 지원 GPU를 사용하다. aarch64와 일부 data-center GPU는 공식 제한을 확인하다.

## 출처

- [Debugging With Visual Studio Code](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/utilities/debugging/tutorial_advanced_python_debugging.html)
- [Profiling Performance Using Tracy](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/utilities/debugging/profiling_performance.html)
- [Performance Optimization Handbook](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/reference_material/sim_performance_optimization_handbook.html)
- [Container Installation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_container.html)
- [Livestream Clients](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/manual_livestream_clients.html)
