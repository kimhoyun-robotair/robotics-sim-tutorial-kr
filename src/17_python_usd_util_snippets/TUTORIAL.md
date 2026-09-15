# 17. 유틸리티: Points, Instancer, DebugDraw와 카메라

권장 학습 순서 **17** · Python 실행 환경과 USD 기초 · 출처 ID `t096`

## 독립 패키지 준비와 실행 규칙

이 폴더 하나만 복사해도 실행되도록 작성했다. 다른 튜토리얼, 공통 Python 모듈, 저장소 루트 자산을 가져오지 않는다. Isaac Sim **5.1.0**과 지원 NVIDIA GPU/드라이버가 필요하다. 아래 Linux 명령의 `~/isaacsim`을 실제 설치 경로로 바꾼다. Windows에서는 설치 폴더의 `python.bat`을 사용한다.

이 패키지 폴더에서 `python3 run.py --help`로 옵션을 확인한다. 실제 실행은 `~/isaacsim/python.sh run.py`로 한다. 기본 출력은 이 폴더의 `output/날짜-시간/`이다. `--output /새/폴더`로 지정할 수 있고 기존 경로를 덮어쓰지 않는다. `--steps`를 생략한 GUI 실행은 사용자가 창을 닫을 때까지 유지됩니다. 양수 `--steps N`을 지정하면 최대 N단계 실행 후 종료합니다. `--headless`에서 생략하면 기존 기본값 120단계를 사용합니다. 기본 120프레임의 위치와 USD를 저장한 뒤에도 점 애니메이션은 계속 움직입니다. 저장 파일은 최초 관찰 구간의 스냅샷입니다. `--headless`는 창을 숨기며 GPU가 필요 없다는 뜻은 아니다.

## 목표와 예상 결과

같은 점 위치 데이터를 세 표현으로 갱신한다. USD Points, cube PointInstancer, viewport DebugDraw가 저장·렌더링·물리에서 어떻게 다른지 확인한다. `rendering.json`에는 실제 작성한 위치와 카메라 속성에서 계산한 내부 파라미터가 기록되고 `geometry.usda`에는 USD 장면이 저장된다.

## 순서대로 실습

```bash
~/isaacsim/python.sh run.py --mode points --count 200
~/isaacsim/python.sh run.py --mode instancer --count 200
~/isaacsim/python.sh run.py --mode debug --count 200
```

1. 같은 난수 시드 7로 위치 200개를 만든다. 각 업데이트에서 Z에 작은 사인파 변화를 주어 움직임을 관찰한다.
2. Points 모드의 `CreatePointsAttr`, `CreateWidthsAttr`를 읽는다. 점이 renderer가 읽는 USD geometry가 된다.
3. Instancer 모드의 `prototypes`, `protoIndices`, `positions`를 읽는다. 하나의 Cube prototype을 여러 위치에 인스턴싱한다. 이 실습은 geometry 갱신에 집중하므로 강체/충돌 스키마를 추가하지 않았다. PointInstancer를 썼다는 이유만으로 물리가 생기지는 않는다.
4. Debug 모드는 `isaacsim.util.debug_draw` 확장을 활성화하고 매번 `clear_points` 후 다시 그린다. USD geometry가 아니므로 파일에 그 점들이 저장되지 않는다. GUI viewport에서만 확인하며 `--headless` 조합은 거부한다.
5. Points와 Instancer의 `geometry.usda`를 새 GUI에서 연다. Debug 모드의 파일에는 debug 점이 없음을 비교한다. `finally`는 이 스크립트가 남긴 debug 점을 정리한다.
6. `/World/CalibrationCamera`는 focalLength=35, horizontalAperture=36, verticalAperture=24인 별도 계산용 카메라다. 해상도를 960×640으로 가정한 결과에서 `fx=width*focal/aperture_x`, `fy=height*focal/aperture_y`를 확인한다. **실제 viewport나 센서 프레임에서 추정한 값은 아니다.**

## 현재 viewport 카메라 읽기

GUI **Window > Script Editor**에서 아래를 실행한다. viewport를 선택하고 해상도가 변경될 다음 앱 프레임까지 기다린 후 다시 읽으면 카메라 속성과 픽셀 크기를 연결할 수 있다.

```python
from omni.kit.viewport.utility import get_active_viewport
import omni.usd
from pxr import UsdGeom
viewport = get_active_viewport()
viewport.set_texture_resolution((960, 640))
print(viewport.get_texture_resolution(), viewport.camera_path)
camera = UsdGeom.Camera(omni.usd.get_context().get_stage().GetPrimAtPath(viewport.camera_path))
print(camera.GetFocalLengthAttr().Get(), camera.GetHorizontalApertureAttr().Get(), camera.GetVerticalApertureAttr().Get(), camera.GetClippingRangeAttr().Get())
```

USD camera focal length와 aperture는 동일한 단위 체계이므로 비율로 FOV를 계산한다. 중심점 `(width/2,height/2)`는 offset이 없는 카메라 가정이다. 원문의 예제처럼 width/height를 뒤섞지 말고 축에 대응시키며, 비정사각 픽셀이나 aperture offset이 있으면 별도로 반영한다.

## 비동기 task와 렌더 지연

새 GUI의 Script Editor에서 `pause_after_update.py`를 실행한다. 타임라인을 Play하고 **앱 업데이트 한 번**을 기다린 뒤 Pause한다. 앱 업데이트와 물리 스텝을 같은 것으로 단정하지 않는다.

`~/isaacsim/python.sh run.py --mode points --zero-delay`는 원문이 제시한 `waitIdle`, Hydra 완료 대기, ROS 2 bridge 발행 threading 설정을 앱 시작 인자로 전달한다. 원문의 오래된 경험 파일 이름 대신 설정값을 명시했다. 이 옵션을 실행했다고 카메라 동기화가 측정·검증된 것은 아니며 처리량과 최신 프레임 대응 사이의 영향을 실제 센서 출력으로 별도 비교해야 한다.

## 한 가지 변수 실험과 문제 해결

`--count`만 200에서 2000으로 바꾸고 화면 반응을 비교한다. 본 패키지는 벤치마크 FPS를 자동으로 측정하지 않는다. Debug 점이 저장 파일에서 안 보이는 것은 의도된 차이다. 검은 화면은 조명과 카메라를 확인한다. 뷰포트가 없는 headless 환경에서는 viewport API 자체가 없을 수 있다.

## 출처와 검증 범위

- NVIDIA Isaac Sim **5.1.0**, [Util Snippets](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/python_scripting/util_snippets.html): 이 패키지가 대응하는 공식 페이지. 문장과 실행 코드는 초심자용으로 재구성했다.
- 구현 API는 로컬 Isaac Sim 5.1 설치의 해당 `isaacsim`/Kit/USD 소스와 대조했다. 원문의 외부 최신 버전 링크는 5.1 설치와 UI/API가 다를 수 있다.

Python 구문 컴파일과 일반 Python의 `--help`는 앱 없이 확인할 수 있다. 이 검사는 GPU, 자산 로딩, GUI 표현, 물리 결과의 실제 실행 검증을 대신하지 않는다. `tutorial.json`의 verification이 `not_run`이면 해당 시뮬레이터 실행은 아직 검증되지 않은 상태다.
