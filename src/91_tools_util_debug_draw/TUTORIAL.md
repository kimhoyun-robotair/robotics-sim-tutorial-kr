# 91. 점과 선으로 좌표를 확인하고 필요한 그림만 지우기

## 이번에 배우는 것

**Debug Draw로 원형 점과 좌표축·곡선을 그리고, 그림의 위치·스타일·수명이 USD 장면과 어떻게 다른지 확인합니다.**

센서가 측정한 점이나 로봇의 목표 경로를 잠시 보고 싶을 때 모든 점을 USD 객체로 만들 필요는 없습니다. Debug Draw는 위치 데이터를 화면에 그리는 별도의 인터페이스를 제공합니다. 이 실습은 한 번 그린 데이터가 프레임을 넘어 유지되고 명시적으로 지워지는 과정을 다룹니다.

| 그릴 데이터 | 위치와 모양 | 확인할 값 |
|---|---|---|
| 점 32개 | Z=0.5, 반지름 1의 원 | `get_num_points()` |
| 축 선분 3개 | 원점에서 +X/+Y/+Z 방향 | 빨강·초록·파랑 |
| 노란 spline | Y=-1.0의 제어점 | 마지막 인수 `False` |
| 자홍 spline | 같은 제어점을 Y로 -0.3 이동 | 마지막 인수 `True` |

좌표는 장면의 위치를 나타내지만 점 크기와 선 두께는 그리기 스타일입니다. 큰 점이 보인다고 물리 공간에서 큰 구체가 생긴 것은 아닙니다.

## 1. Script Editor에서 그림 만들기

Isaac Sim 5.1 GUI와 지원 NVIDIA GPU가 필요합니다. 저장소 루트의 터미널에서 앱을 시작하세요.

```bash
~/isaacsim/isaac-sim.sh
```

1. 다른 Debug Draw 데이터를 사용하지 않는 새 앱을 준비합니다.
2. **Window > Extensions**에서 `isaacsim.util.debug_draw`를 활성화합니다.
3. **Window > Script Editor**를 엽니다.
4. `src/91_tools_util_debug_draw/draw.py` 전체를 붙여 넣고 실행합니다.
5. Viewport 카메라를 원점 근처로 옮겨 원형 점, 세 축과 두 곡선을 봅니다.

이 파일은 **이미 실행 중인 앱 안에서** 사용합니다. `SimulationApp`을 만들지 않으며 일반 `python3 draw.py`로 실행하는 독립 프로그램이 아닙니다.

### 실행 결과 확인하기

Script Editor 출력에 다음 형태가 나타납니다.

```text
point count 32 line count ...
```

점은 32개입니다. 곡선을 여러 선분으로 그리므로 line count는 축 개수인 3보다 많을 수 있습니다. **제어점 수와 실제로 그린 선분 수는 다른 값**입니다.

Play/Pause를 반복하고 Stage 트리를 확인해 보세요. 그림은 계속 남지만 대응하는 Cube나 Curve prim이 추가되지는 않습니다. 이 코드는 USD 파일이나 이미지도 자동 저장하지 않습니다.

## 2. 좌표 배열과 그리기 인터페이스 읽기

### 코드에서 볼 부분

먼저 앱의 Debug Draw 인터페이스를 가져오고 기존 데이터가 있는지 검사합니다.

```python
draw = _debug_draw.acquire_debug_draw_interface()
if draw.get_num_points() or draw.get_num_lines():
    raise RuntimeError("Debug drawer already contains data; use a clean session")
```

같은 drawer를 여러 코드가 사용할 수 있으므로 기존 그림을 임의로 지우지 않도록 한 검사입니다. 새 Stage를 만드는 일만으로 drawer가 비워졌다고 가정하지 마세요.

원형 점은 다음 좌표식으로 만듭니다.

```python
points = [
    (math.cos(i * math.tau / 32), math.sin(i * math.tau / 32), 0.5)
    for i in range(32)
]
draw.draw_points(
    points,
    [(0.2, 0.8, 1.0, 1.0)] * len(points),
    [8.0] * len(points),
)
```

`math.tau`는 한 바퀴의 각도인 `2π`입니다. 32개 각도를 같은 간격으로 나누고 `(cos θ, sin θ)`를 사용하므로 XY 평면의 반지름 1인 원이 됩니다. Z는 모두 0.5입니다.

`draw_points`의 세 배열은 **같은 인덱스의 점끼리 대응**합니다. 첫 배열은 위치, 두 번째는 RGBA 색, 세 번째는 표시 크기입니다. 색의 마지막 값 1.0은 완전한 불투명도를 뜻합니다. 위치가 32개라면 색과 크기도 각각 32개가 필요합니다.

`draw_lines`는 시작점 배열과 끝점 배열을 받습니다. 이 예제에서는 시작점을 원점 세 개로 두고 끝점을 `(1,0,0)`, `(0,1,0)`, `(0,0,1)`로 둡니다. 선마다 빨강·초록·파랑을 지정하여 축 방향을 구별합니다.

곡선 두 개는 동일한 제어점 배치를 사용합니다.

```python
draw.draw_lines_spline(spline, (1.0, 1.0, 0.0, 1.0), 4, False)
draw.draw_lines_spline(
    [(x, y-0.3, z) for x, y, z in spline],
    (1.0, 0.2, 1.0, 1.0), 4, True,
)
```

두 번째 곡선을 옆으로 옮긴 이유는 같은 위치에 겹쳐 보이지 않게 하기 위해서입니다. 마지막 boolean은 5.1 인터페이스에서 `filled`로 정의하는 표현 옵션입니다. 공식 예제는 채운 선과 점선 표현을 비교합니다. **색과 Y 위치로 각 호출을 식별한 뒤 False/True에서 선이 이어지는 모양을 대조**해 보세요. 이 값은 충돌 여부나 물리적 두께를 설정하지 않습니다.

### 실행 결과 확인하기

앞의 코드와 **같은 Script Editor 탭**에서 다음을 실행합니다.

```python
draw.clear_points()
print("points", draw.get_num_points(), "lines", draw.get_num_lines())
```

원형 점만 사라지고 축과 곡선이 남아야 합니다. 이어 다음을 실행하세요.

```python
draw.clear_lines()
print("points", draw.get_num_points(), "lines", draw.get_num_lines())
```

이제 두 수가 모두 0이어야 합니다. `clear_lines`는 직선과 spline이 만든 선분을 함께 지웁니다. 이 인터페이스의 clear는 해당 drawer 전체에 적용되므로 다른 도구의 그림이 있는 세션에서는 먼저 사용 범위를 확인하세요.

## 3. 그림 데이터의 수명 정리

```text
좌표·색·크기 배열 → Debug Draw 인터페이스 → Viewport에 표시
                                                ↓
                                      프레임이 바뀌어도 유지
                                                ↓
                               clear_points / clear_lines로 제거
```

**Debug Draw 데이터는 관찰용 그림입니다.** 장면에 저장할 메시나 물리 collider가 필요하면 USD 객체를 따로 만들어야 합니다. 반대로 매 단계 경로를 다시 그리는 도구라면 이전 그림을 언제 지울지도 코드가 정해야 합니다.

## 4. 간단한 확인 실험

`draw_points`의 크기 배열에서 **8.0만 2.0으로** 바꾸세요. 앞 절의 두 clear를 실행하고 수정한 전체 스크립트를 다시 실행합니다.

점은 더 작게 표시되지만 개수는 32이고 원의 반지름과 높이는 그대로여야 합니다. 축 선의 두께와 곡선도 변하지 않습니다. 카메라 위치를 유지하면 위치 데이터와 표시 스타일의 차이를 더 쉽게 비교할 수 있습니다.

## 실행할 때 막히면

- **`Debug drawer already contains data`:** 이전 그림이 남아 있습니다. 이 실습만 사용하는 세션에서 두 clear를 실행하거나 새 앱에서 시작하세요.
- **import 오류:** `isaacsim.util.debug_draw`가 활성화되었는지 확인하세요. 시스템 Python 대신 Script Editor를 사용합니다.
- **점 개수는 32인데 화면에 안 보임:** 카메라가 원점과 Z=0.5 부근을 보고 있는지 확인하세요. Stage에서 선택할 prim이 생기는 예제가 아닙니다.
- **별도 탭에서 `draw` 이름을 찾지 못함:** 같은 탭에서 실행하거나 import와 `acquire_debug_draw_interface()`를 다시 수행하세요.
- **USD를 다시 열었는데 그림이 없음:** 코드가 USD prim을 작성하지 않으므로 정상입니다. `draw.py`를 다시 실행해 그립니다.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Debug Drawing Extension API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/utilities/debugging/ext_isaacsim_util_debug_draw.html)에 대응합니다. 원형 점과 축·곡선의 좌표는 이 폴더에서 정한 관찰 예제입니다.

로컬 `draw.py`와 5.1 `IDebugDraw.h`, 제공 테스트의 호출 형태를 대조했습니다. 실제 Viewport 렌더링과 spline 표현 차이, 프레임 간 유지·삭제는 이번 개정에서 실행하지 않았습니다. `tutorial.json`의 검증 상태는 `not_run`입니다.
