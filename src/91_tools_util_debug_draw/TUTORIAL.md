# 91. Debug Drawing Extension API

권장 학습 순서 **91** · OmniGraph와 확장 개발 · 출처 ID `t168`

32개 점, XYZ 축 선분, 실선/점선 spline을 그려 persistent debug geometry를 확인한다. 같은 점 데이터를 다른 스타일로 관찰하는 작은 API 실습이다.

## 이 실습의 의도

센서 위치나 경로를 확인할 때 사용할 수 있는 debug draw API로 점·선·spline의 표현과 수명을 비교한다. 원형 점, RGB 축, 서로 떨어진 두 spline은 위치·색·굵기·실선/점선 설정을 화면에서 구별하기 위한 구성이다. `draw.py`는 열린 Kit의 drawer에 한 번 그리며 USD prim, collider나 저장 파일을 생성하지 않는다.

## 실행 후 확인할 것

- **점과 축:** 빈 drawer에서 실행한 뒤 원점 주변을 보면 z=0.5, 반지름 1의 청록색 점 32개와 +X 빨강/+Y 초록/+Z 파랑 축 선분이 보여야 한다. Script Editor의 `draw.get_num_points()`도 32인지 확인한다.
- **spline 스타일:** y=-1 부근의 노란 실선과 그보다 y가 0.3 작은 자홍 점선을 비교한다. spline은 여러 선분으로 표현될 수 있으므로 `get_num_lines()`가 축 개수인 3보다 크다고 오류로 보지 않는다.
- **유지와 장면 트리:** Play/Pause 뒤에도 그림이 유지되고 Stage에 대응 Cube/Curve prim이 생기지 않는지 확인한다. USD Save로 저장되는 장면 geometry와 다른 데이터다.
- **선택적 삭제:** `draw.clear_points()` 뒤에는 선과 spline이 남고, 이어 `draw.clear_lines()`를 실행하면 나머지도 사라져야 한다.
- **재실행 조건:** 데이터가 남은 채 `draw.py`를 다시 실행하면 `Debug drawer already contains data` 오류로 중단되는 것이 의도된 보호 동작이다. 두 종류를 모두 clear한 뒤 다시 실행하면 처음과 같은 구성이 생긴다.

## 실행 환경

Isaac Sim **5.1.0** GUI와 지원 NVIDIA GPU가 필요하다. 이 폴더를 어디로 복사해도 다른 로컬 튜토리얼 없이 실행한다. 아래처럼 시작한 뒤 **Window > Script Editor**를 연다.

```bash
export ISAAC_SIM_PATH="$HOME/isaacsim"
"$ISAAC_SIM_PATH/isaac-sim.sh"
```

Script Editor의 **File > Open**으로 본문의 Python 파일을 열고 **Run**을 누른다. 이 코드는 이미 실행 중인 Kit 안에서 동작하므로 별도의 `SimulationApp`을 만들지 않는다. 일반 시스템 `python3`에서 실행하는 파일이 아니다. Stage는 현재 USD 장면, prim은 장면의 경로로 식별되는 요소다. 이 예제는 prim의 존재 여부 대신 drawer에 기존 점이나 선이 있는지 검사하고, 있으면 에러를 낸다.

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
