# 91. Debug Drawing Extension API

권장 학습 순서 **91** · OmniGraph와 확장 개발 · 출처 ID `t168`

32개 점, XYZ 축 선분, 실선/점선 spline을 그려 persistent debug geometry를 확인한다. 같은 점 데이터를 다른 스타일로 관찰하는 작은 API 실습이다.

## 실행 환경

Isaac Sim **5.1.0** GUI와 지원 NVIDIA GPU가 필요하다. 이 폴더를 어디로 복사해도 다른 로컬 튜토리얼 없이 실행한다. 아래처럼 시작한 뒤 **Window > Script Editor**를 연다.

```bash
export ISAAC_SIM_PATH="$HOME/isaacsim"
"$ISAAC_SIM_PATH/isaac-sim.sh"
```

Script Editor의 **File > Open**으로 본문의 Python 파일을 열고 **Run**을 누른다. 이 코드는 이미 실행 중인 Kit 안에서 동작하므로 별도의 `SimulationApp`을 만들지 않는다. 일반 시스템 `python3`에서 실행하는 파일이 아니다. Stage는 현재 USD 장면, prim은 장면의 경로로 식별되는 요소다. 같은 파일을 재실행할 때 기존 결과를 삭제하거나 덮어쓰지 않도록 해당 prim이 있으면 에러를 내는 예제를 사용한다.

## 실습

1. 다른 debug draw를 쓰지 않는 새 앱에서 `Window > Extensions`의 **isaacsim.util.debug_draw**를 활성화한다.
2. `draw.py`를 Run한다. 원점 근처를 Viewport로 보면 청록색 원형 점, RGB 축, 노랑/자홍 spline이 나타난다. 필요하면 perspective camera를 원점 주변으로 이동한다.
3. Play/Pause를 반복해도 선과 점이 유지되는지 본다. Stage에 대응 Cube/Curve prim이 생기지 않는 것을 확인한다.
4. 같은 Script Editor에서 `print(draw.get_num_points())`를 실행하면 32다. spline tessellation 때문에 line count는 축 선분 3보다 많을 수 있다.
5. 관찰이 끝나면 `draw.clear_points()`로 점만 지우고 선은 남는지 본다. 이어 `draw.clear_lines()`로 선/spline을 지운다. 이 API는 앱의 drawer 전체를 비우므로 실습 전 다른 사용자가 그린 데이터가 없는지 확인한다.

`acquire_debug_draw_interface()`는 drawer handle을 얻는다. `draw_points`는 위치/RGBA/크기 배열을, `draw_lines`는 시작/끝/RGBA/두께 배열을 받으며 각 배열 길이가 같아야 한다. `draw_lines_spline`의 마지막 bool은 실선/점선 선택이다. 이 그림은 USD 장면에 저장되는 물리 geometry가 아니므로 Stage Save로 영속 자산이 되지 않는다. 기본 Omniverse debug drawing과 달리 이 확장의 데이터는 clear 전까지 프레임 간 유지된다.

한 변수 실험: points의 크기 8만 2로 바꾸고 깨끗한 drawer에서 재실행한다. 성공은 32개 점, 선/spline 스타일, frame 간 유지, 선택적 clear다. import 오류는 확장 활성 상태, 안 보이는 그림은 카메라 위치와 renderer viewport를 확인한다.

## 검증 범위

제공된 Python/JSON/TOML의 문법과 5.1 설치 소스/API를 대조했다. GPU/Kit에서 화면과 동작은 아직 실행하지 않았으므로 manifest는 `verification: not_run`이다. 아래 성공 기준을 실제 실행 후 확인해야 한다.

## 출처

- [Isaac Sim 5.1 공식 원문](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/utilities/debugging/ext_isaacsim_util_debug_draw.html).
