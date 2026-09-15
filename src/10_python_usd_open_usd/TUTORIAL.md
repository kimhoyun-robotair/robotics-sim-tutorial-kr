# 10. OpenUSD 기초: 속성, 계층, 레이어, 재질, 변환

권장 학습 순서 **10** · Python 실행 환경과 USD 기초 · 출처 ID `t173`

## 독립 패키지 준비와 실행 규칙

이 폴더 하나만 복사해도 실행되도록 작성했다. 다른 튜토리얼, 공통 Python 모듈, 저장소 루트 자산을 가져오지 않는다. Isaac Sim **5.1.0**과 지원 NVIDIA GPU/드라이버가 필요하다. 아래 Linux 명령의 `~/isaacsim`을 실제 설치 경로로 바꾼다. Windows에서는 설치 폴더의 `python.bat`을 사용한다.

이 패키지 폴더에서 `python3 run.py --help`로 옵션을 확인한다. 실제 실행은 `~/isaacsim/python.sh run.py`로 한다. 기본 출력은 이 폴더의 `output/날짜-시간/`이다. `--output /새/폴더`로 지정할 수 있고 기존 경로를 덮어쓰지 않는다. `--steps`를 생략하면 사용자가 창을 닫을 때까지 GUI가 유지된다. 양수 `--steps N`을 지정하면 N번 실행 후 종료한다. `--headless`에서 `--steps`를 생략하면 기존 기본값인 120번 실행 후 종료한다. `--headless`는 창을 숨기며 GPU가 필요 없다는 뜻은 아니다.

## 목표와 예상 결과

`/hello/world`에 구를 만들고 속성 수정, 부모/자식 이동, 재질 연결, Stage 순회, sublayer/session layer, 변환 분해를 실습한다. 물리 시뮬레이션 없이 USD를 작성·재개방하며 `hello.usda`, `details.usda`, `inspection.json`을 만든다. 이 예제의 구가 중력으로 떨어지지 않는 것은 정상이다.

## 순서대로 실습

1. `~/isaacsim/python.sh run.py --radius 0.5`을 실행한다. 열린 GUI에서 장면을 살펴본 뒤 창을 닫는다. 저장한 `hello.usda`를 나중에 다시 열 수도 있다.
2. 텍스트 편집기로 `hello.usda`를 열어 `def Xform "hello"`, `def Sphere "world"`, `radius`와 xform 연산을 찾는다. USDA는 USD의 텍스트 인코딩이다.
3. `/hello`를 Z로 1 m, 자식 sphere를 X로 1 m 이동한다. `inspection.json`의 월드 위치가 `(1,0,1)`인지 확인한다. 자식 local transform과 월드 transform이 다름을 이해한다.
4. `GetPropertyNames()` 출력에는 작성한 값뿐 아니라 스키마가 정의한 속성도 포함된다. `radius`는 `UsdGeom.Sphere`의 타입 속성이다.
5. 기본 재질은 `UsdPreviewSurface`이며 `Material.surface → Shader.surface` 연결과 구의 `MaterialBindingAPI`를 확인한다. 원문의 MDL 예제를 가볍게 비교할 수 있도록 외부 텍스처 없이 구현했다.
6. `details.usda`는 root layer의 subLayerPaths로 합성되고 `Usd.EditContext` 안에서 `tutorial:label` 속성을 작성한다. root와 layer 파일을 함께 보관한다.
7. session layer에서 반지름을 두 배로 바꾸고 root를 저장한다. 별도 session으로 재개방한 `saved_radius`는 원래 값이고 `session_radius`는 두 배인지 확인한다. Session 변경이 자동으로 원본에 저장되는 것은 아니다.
8. `stage.Traverse()`는 전체 Stage, `Usd.PrimRange(defaultPrim)`은 선택한 루트의 하위 계층을 순회한다. `inspection.json`에서 `/Light`가 전체 순회에만 있는지 확인한다.
9. MatrixExample의 4×4 행렬을 translate/orient/scale 연산으로 분해한다. 행렬 오차가 1e−6 이내인지 실제 계산해 검사한다. 예제는 양의 균일 스케일이고 shear가 없다. 임의 shear/음수 스케일 변환에도 이 단순 절차가 그대로 성립한다고 가정하지 않는다.

## MDL 재질을 직접 비교

생성된 장면을 GUI로 열고 Script Editor에서 실행한다. NVIDIA 기본 MDL 재질 라이브러리가 설치되어 있어야 한다.

```python
import omni.kit.commands
import omni.usd
from pxr import Gf, Sdf, UsdShade
created = []
omni.kit.commands.execute("CreateAndBindMdlMaterialFromLibrary", mdl_name="OmniPBR.mdl", mtl_name="OmniPBR", mtl_created_list=created)
stage = omni.usd.get_context().get_stage()
material = stage.GetPrimAtPath(created[0])
omni.usd.create_material_input(material, "diffuse_color_constant", Gf.Vec3f(0,0,1), Sdf.ValueTypeNames.Color3f)
UsdShade.MaterialBindingAPI.Apply(stage.GetPrimAtPath("/hello/world")).Bind(UsdShade.Material(material))
```

`OmniSurface.mdl`/`OmniSurface`로 같은 생성 명령을 바꾸면 원문의 재바인딩 실습도 할 수 있다. Shader 입력 이름은 재질마다 다르므로 Property에서 확인한다.

## 단위와 한 가지 변수 실험

USD의 거리 단위는 `metersPerUnit`, 상향 축은 `upAxis` 메타데이터로 표현한다. 이 패키지는 1.0 m/unit, Z-up을 명시한다. 다른 단위 파일을 reference한다고 자동 변환되는 것은 아니므로 스케일 정책을 정해야 한다. `--radius`만 0.5에서 0.25로 바꾸고 saved/session radius와 화면 크기를 비교한다.

파일을 옮겼더니 label이 사라지면 `details.usda`의 상대 경로를 확인한다. Session 반지름이 재개방 후 사라지는 것은 의도된 결과다. 단위 quaternion의 순서는 Gf/Usd API 타입에 맞춰 쓰고 Euler 도/라디안과 섞지 않는다.

## 출처와 검증 범위

- NVIDIA Isaac Sim **5.1.0**, [OpenUSD Fundamentals](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/omniverse_usd/open_usd.html): 이 패키지가 대응하는 공식 페이지. 문장과 실행 코드는 초심자용으로 재구성했다.
- 구현 API는 로컬 Isaac Sim 5.1 설치의 해당 `isaacsim`/Kit/USD 소스와 대조했다. 원문의 외부 최신 버전 링크는 5.1 설치와 UI/API가 다를 수 있다.

현재 확인한 실행 조건과 실제 측정 결과는 [RUNTIME_CHECK.md](RUNTIME_CHECK.md)에 기록했습니다. `tutorial.json`의 `partial_runtime_verified`는 그 조건에 한정된 검증이며, 다른 모드와 GUI·외부 통합 전체의 검증을 뜻하지 않습니다.
