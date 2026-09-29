# Property, Metadata, Schema
먼저, 간단하게 내용을 요약해보자.
> **Prim**은 Scene의 구성요소.  
> **Property**는 그 구성요소의 값(attribute)과 relationship을 표현  
> **Metadata**는 Prim과 Property 등의 설명 및 설정 정보를 표현  
> **Schema**는 데이터들이 어떤 구조와 의미를 가져야 하는지 정하고, 그에 맞는 API를 제공  

## 시작
| 개념 | 핵심 질문 | 예시 |
| -- | -- | -- |
| **Property** | 이 Prim에는 어떤 데이터 항목이 있는가? | 큐브의 크기, 온도, 다른 Prim을 가리키는 연결 등 |
| **Metadata** | 이 Prim이나 데이터 항목에는 어떤 설명, 설정 정보가 들어있는가? | Prim 타입, 적용된 API Schema, 설명문, 사용자 정의 관리 정보 |
| **Schema** | 어떤 데이터 항목을 어떤 이름과 타입으로 제공하고, 어떻게 해석해야하는가? | 예를 들어, Cube의 `size`는 모서리 길이를 나타내는 `double` 타입의 Attribute라는 규칙 |
앞선 자료에서 다루었듯, Property에는 **Attribute**와 **Relationship**이라는 두 종류가 있다. Metadata와 Schema는 완전히 다른 개념이고 말이다.  
  
다음과 같은 개념의 예제로 한번 3가지를 공부해보자.
```
Body Prim
│
├─ Prim 자체의 Metadata
│  ├─ typeName = "Cube"
│  ├─ 적용된 API Schema 목록
│  └─ 이 Prim에 대한 설명
│
├─ Attribute: size
│  ├─ 데이터 타입: double
│  ├─ 값: 1.0
│  └─ 이 Attribute에 붙는 Metadata
│
├─ Attribute: demo:temperature
│  ├─ 데이터 타입: float
│  ├─ 값: 20.0
│  └─ 이 Attribute에 붙는 Metadata
│     └─ "학습용 온도 데이터"라는 설명
│
└─ Relationship: demo:camera
   ├─ 대상 경로: /World/Camera
   └─ 이 Relationship에 붙는 Metadata
```

## Scene 만들기
```
from pxr import Usd, UsdGeom, UsdPhysics, Sdf, Gf

# 현재 화면의 Stage와는 별개인, 학습용 메모리 Stage입니다.
stage = Usd.Stage.CreateInMemory()

world = UsdGeom.Xform.Define(stage, "/World").GetPrim()
robot = UsdGeom.Xform.Define(stage, "/World/Robot").GetPrim()

cube = UsdGeom.Cube.Define(stage, "/World/Robot/Body")
body = cube.GetPrim()

camera = UsdGeom.Camera.Define(stage, "/World/Camera").GetPrim()
```
앞선 자료를 공부했다면 쉽게 이해가 가는 코드일 것이다. `body`는 일반적인 `Usd.Prim` 객체, `cube`는 같은 Prim을 Cube 규격으로 다루는 `UsdGeom.Cube` 객체이다.

# Property : Prim에 속한 데이터 항목
OpenUSD에서는 `UsdProperty`를 다음과 같이 정의한다.  
> **Base class for UsdAttribute and UsdRelationship scenegraph objects.**  
즉 Property는 기술적으로 쉽게 말하면, **Attribute와 Relationship이 공통으로 사용하는 클래스**라고 볼 수 있다. 따라서 코드를 읽을 때 다음과 같이 보면 된다.  
```
Property를 다루는 코드
    ├─ 값이 필요하면 Attribute로 접근
    └─ 대상 연결이 필요하면 Relationship으로 접근
```
Property는 Prim 안에서 자신만의 이름을 가지며, 해당 이름을 포함하는 경로를 통해 식별이 가능하다.
```
/World/Robot/Body
    → Prim 경로

/World/Robot/Body.size
    → Property 경로

/World/Robot/Body.demo:temperature
    → 네임스페이스를 사용한 Property 경로
```
`/`은 Prim 계층 구조를, `.`은 Prim과 Property 사이의 구분을, `:`은 Property 이름 안의 네임스페이스 구분을 위해서 사용한다.

## Attribute: 특정 타입의 값을 다루는 Property
**Attribute의 핵심은 값이 아니라, 그 값을 다루는 데이터 항목(자료형)이다.**  
Attribute에는 이름과 데이터 타입이 있고, 기본값이나 시간에 따른 값을 기록할 수 있다. NVIDIA 공식 자료에 따르면, 하나의 Attribute에는 특정 데이터 타입이 정해지며, 기본값과 시간 샘플링값을 가질 수 있다고 설명한다.  
예를 들어서 큐브의 `size`를 읽어보자.
```
size_attr = body.GetAttribute("size")
size_value = size_attr.Get()

print(size_attr.GetName())      # 예상: size
print(size_attr.GetTypeName())  # 예상: double
print(size_value)               # 예상: 2.0
```
여기서 `body`는 Body라는 scene의 구성요소 중 하나이고, `size_attr`는 Body의 크기를 나타내는 Attribute 객체이다. 그리고 `size_value`는 그 Attribute 객체 안에서 읽어온 실제 값(숫자)를 의미한다.  
따라서 2개 표현은 다르다는 것을 알 수 있다.
```
body.GetAttribute("size")        # Usd.Attribute 객체

body.GetAttribute("size").Get()  # 해당 Attribute에서 조회한 값
```
최종적으로, 어떤 Prim의 Property 중 Attribute 값을 읽어오고 싶으면 다음 3단계를 거치면 되는 것을 알 수 있다.  
1. Stage에서 Prim을 찾는다.
2. Prim에서 Attribute를 찾는다.
3. Attribute의 값을 읽는다.
  
그렇다면 **Attribute의 값을 설정하려면?** `Set()` 함수를 사용하면 된다.
```
size_attr.Set(1.0)

print(size_attr.Get())  # 예상: 1.0
```
`Set()`을 사용하면 Attribute의 값을 현재 편집 대상에게 기록할 수 있다. 여기에서 **기록하다(Author or Authoring)**라는 표현이 공식적으로 등장하는데, 간단하게 생각해서 **레이어에 명시적으로 작성한다**라는 의미로 받아들이면 된다.  
여기서 또 하나 주의해야 하는 점은, Attribute 값을 바꾼다고 관련된 모든 데이터가 자동으로 변환되는 것은 아니라는 점이다. 예를 들어서, Cube 예제 문서를 확인해보면, Cube의 `size`를 작성하게 될 경우 그에 맞는 **`extent`(로컬 공간에서 특정한 형상을 감싸는 범위)**도 별개로 작성해야 한다고 명시한다. 예를 들면 다음과 같이 코드를 작성할 수 있다.
```
cube.CreateExtentAttr([
    Gf.Vec3f(-0.5, -0.5, -0.5),
    Gf.Vec3f(0.5, 0.5, 0.5),
])
```

### 사용자 정의 Attribute 만들기
Schema에 정의되지 않은 사용자 정의 Attribute를 만들어보자. Temperature를 주제로 만들 것이다.
```
temperature_attr = body.CreateAttribute(
    "demo:temperature",
    Sdf.ValueTypeNames.Float,
    custom=True,
    variability=Sdf.VariabilityVarying,
)

print(bool(temperature_attr))  # 예상: True
print(temperature_attr.Get())  # 예상: None

temperature_attr.Set(20.0)

print(temperature_attr.Get())  # 예상: 20.0
```
여기서 인자들을 해석하면 다음과 같다.
| 코드 | 의미 |
| -- | -- |
| `"demo:temperature"` | Attribute의 이름. `demo`는 예제에서 정한 네임스페이스 |
| `Sdf.ValueTypeNames.Float` | 이 Attribute가 저장하는 값의 USD 타입은 `float`라는 뜻이다 |
| `custom=True` | 사용자 정의 Property라는 뜻이다 |
| `Sdf.VariabilityVarying` | 시간에 따른 값 변화를 허용한다는 의미이다 |
  
USD에서 사용하는 데이터 타입과 파이썬의 데이터 타입을 매칭해보면 다음과 같다.
| USD에서의 타입  | Python에서 사용하는 방법  | 의미 |
| -- | -- | -- |
| `bool` | `Sdf.ValueTypeNames.Bool` | 참,거짓|
| `int` | `Sdf.ValueTypeNames.Int` | 정수 |
| `float`, `double` | `Sdf.ValueTypeNames.{Float, Double}` | 실수 |
| `string` | `.String` | 문자열 |
| `token` | `.Token` | 이름, 상태 식별 등에 사용하는 문자열 계열의 타입 |
| `float3` | `.Float3` | 실수 3개로 구성된 벡터 |
| `float[]` | `.FloatArray` | 실수 배열 |
| `asset` | `.Asset` | 외부 자산을 식별하고 해석할 수 있는 경로 |
더 많은 타입 시스템과 배열 표기법은 [**다음 링크**](https://openusd.org/release/api/_usd__page__datatypes.html)에 정리되어있다.  
예를 하나 들어보자.
```
direction_attr = body.CreateAttribute(
    "demo:direction",
    Sdf.ValueTypeNames.Float3,
    custom=True,
)

direction_attr.Set(Gf.Vec3f(1, 0, 0))
```
이는 벡터 형태의 사용자 정의 Attribute를 만든다는 것을 알 수 있다.  
### Attribute의 특징: 시간에 따른 값을 가질 수 있다.
```
stage.SetTimeCodesPerSecond(24.0)
stage.SetInterpolationType(Usd.InterpolationTypeLinear)

temperature_attr.Set(20.0, Usd.TimeCode(0))
temperature_attr.Set(30.0, Usd.TimeCode(24))

print(temperature_attr.Get(Usd.TimeCode(0)))   # 예상: 20.0
print(temperature_attr.Get(Usd.TimeCode(12)))  # 예상: 25.0
print(temperature_attr.Get(Usd.TimeCode(24)))  # 예상: 30.0

print(temperature_attr.GetTimeSamples())
# 예상: [0.0, 24.0]
```
위 예제는 다음과 같은 구조를 가지고 있다고 보면 이해하기가 쉽다.
```
USD Attribute
│
├─ Default Value
│    └─ 시간과 관계없는 기본값
│
└─ Time Samples
     ├─ TimeCode 0  → 20.0
     └─ TimeCode 24 → 30.0
```
여기서 중요한 것은 다음 4가지이다.  
1. **TimeCode는 시간의 단위가 아니다**
   1. OpenUSD에서는 `UsdTimeCode`를 Unitless time coordinate라고 설명하고 있다.
   2. 따라서 단위가 존재하지 않는 개념이며, 이를 실제 초(second) 단위와 연결하기 위해서 사용하는 것이 바로 `timeCodePerSecond`이다. 1로 설정하면 1:1 비율인거고, 위 예제에서는 24로 설정했기 때문에 TimeCode가 24일때마다 1초가 지난다는 의미이다.
   3. FPS랑도 다른 개념이다. TimeCode 좌표를 초로 환산하는 스케일 축이기 때문.
2. `Set(value)`와 `Set(value, TimeCode)`는 완전히 다른 의미이다.
   1. 예를 들어서 `temperature_attr.Set(20.0)`은 **Default Value**를 설정한다.
   2. 반면, `temperature_attr.Set(20,0, Usd.TimeCode(0))`은 **TimeCode 0에 Time Sample을 설정**하는 것이다.
   3. USD 텍스트를 예시로 들면 다음과 같다.
        ```
        custom float temperature = 18.0
        custom float temperature.timeSamples = {
            0: 20.0,
            24: 30.0,
        }
        ```
    4. Default와 Time Sample은 서로 별개의 value source이며, 같은 attribute에 동시에 존재할 수 있다.
3. 그래서 `Get()`이 매우 중요하다.
   1. 예를 들어서 다음 코드가 있다고 가정하자.
        ```
        temperature_attr.Set(18.0)

        temperature_attr.Set(20.0, Usd.TimeCode(0))
        temperature_attr.Set(30.0, Usd.TimeCode(24))
        ```
    2. 여기서 `temperature_attr.Get()`을 한다면, 이건 사실상 `temperature_attr.Get(Usd.TimeCode.Default())`를 한 것과 동일하다.
    3. 반대로 `temperature_attr.Get(Usd.TimeCode(0))`이라고 한다면 TimeCode가 0일 때의 Time Sample을 읽어오는 것이다.
4. Isaac Sim Timeline과 `Get()`은 또 자동 연결되지는 않는다.
   1. 예를 들어서 Isaac Sim 화면에서 Timeline이 현재 0.5초에 있다고 가정하자.
   2. 만약에 `timeCodePerSecond=24`라면 이에 대응되는 TimeCode는 12이다.
   3. 그런데 파이썬에서 그냥 `temperature_attr.Get()`을 해버리면, OpenUSD가 알아서 Isaac Sim에서 0.5초니 TimeCode 12 값을 읽어서 반환해야겠다! 이런 식으로 작동하지는 않는다.
   4. Isaac Sim/Omniverse Timeline API는 시간을 초 단위롤 관리하며, `get_current_time()`은 현재의 animation time을 seconds 단위로 반환한다. 따라서 현재 화면 시간에 맞춰 Attribute를 직접 읽고 싶다면 개념적으로 이렇게 작성해야 한다.
    ```
    import omni.timeline
    from pxr import Usd

    timeline = omni.timeline.get_timeline_interface()
    current_seconds = timeline.get_current_time()

    tcps = stage.GetTimeCodesPerSecond()
    current_time_code = current_seconds * tcps
    
    temperature = temperature_attr.Get(Usd.TimeCode(current_time_code))
    ```
5. `Usd.InterpolationTypeLinear`는 Time Code 사이 값을 선형 보간해서 반환한다(다만 문자열 등 애초에 보간의 개념이 없는 타입들은 적용되지 않는다). 반면 `Usd.InterpolationTypeHeld`를 사용한다면, 다음 Time Sample에서 새로운 값이 지정되기 전까지는 Time Code가 변화하더라도 계속 같은 값을 가지고 간다.
    ```
    TC 0     → 20
    TC 1     → 20
    TC 6     → 20
    TC 12    → 20
    TC 23.9  → 20
    TC 24    → 30
    ```

### `uniform`과 `varying`?
Attribute에는 **variability**라는 설정이 존재한다.
```
uniform
    시간에 따라 변하지 않는 값으로 사용하겠다는 선언

varying
    시간 샘플을 가질 수 있는 값으로 사용하겠다는 선언
```
다만 `varying`이라고 해서 반드시 시간에 따라 애니메이션 되어야 하는 것은 아니고, `uniform`이라고 해서 constant 취급이라 읽기 전용인 것은 아니다 (코드를 통해 값 수정 가능).

## Relationship
Relationship은 Prim이 다른 Prim, Attribute, Relationship을 대상으로 가리키게 하는 Property이다. 그리고 하나의 Relationship에 여러 대상을 지정할 수도 있다.  
```
camera_rel = body.CreateRelationship(
    "demo:camera",
    custom=True,
)

camera_rel.SetTargets([
    camera.GetPath()
])

print(camera_rel.GetPath())
# 예상: /World/Robot/Body.demo:camera

print([str(path) for path in camera_rel.GetTargets()])
# 예상: ['/World/Camera']
```
여기서 경로 2개의 역할이 서로 다르다.
```
/World/Robot/Body.demo:camera
    → Relationship 자신의 주소

/World/Camera
    → Relationship이 가리키는 대상의 주소
```
카메라 Prim을 Body 아래로 옮기거나 복사한 것은 아니고, **Body에 저 카메라를 가리킨다**라는 정보가 추가된 것이다.

### GetTargets()는 Prim의 경로를 반환한다.
```
target_paths = camera_rel.GetTargets()

for path in target_paths:
    target_prim = stage.GetPrimAtPath(path)

    if not target_prim:
        raise RuntimeError(f"대상 Prim이 없습니다: {path}")

    print(target_prim.GetTypeName())
    # 이 예제에서는 Camera
```
위 코드의 흐름은 다음과 같다.
```
Relationship
    ↓ GetTargets()
대상 경로
    ↓ stage.GetPrimAtPath()
대상 Prim
```
### 그냥 문자열로 경로를 지정하면 안되는거임?
```
custom string demo:cameraPath = "/World/Camera"
```
이렇게 써버리면 그냥 문자열 데이터로 취급된다. USD에서는 문자열을 Relationship의 대상으로 취급하지 않는다. Relationship의 대상은 USD의 조합 과정에서 Scene Path의 대응 관계에 따라서 해석이 되기 때문에, 문자열로 단순히 기술한다고 이루어지지는 않는다.

### Relationship을 연결하면 자동으로 모든게 다 처리되는거임?
Relationship을 연결한다고 자동으로 물리 연산이 붙고, 물리 엔진이 작동하고 이런건 아니다. 위 예제에서 Body에 카메라를 붙이게 되었다고 카메라가 Body를 추적하거나, 함께 움직이거나, 이미지를 자동으로 publish 하거나 이러지는 않는다. 이 연결의 의미를 마치 그래프를 해석하듯 읽어들여서 직접 사용하는 코드가 있어야만 실제 동작으로 이어지게 된다.

# Metadata : 객체마다 존재하는 설명과 설정 정보
공식자료에서는 Metadata는 공식적으로 다음과 같이 설명한다.  
> **Additional, non-animatable information**  
  
Prim, Property, Later 등에 붙는, 애니메이션 되지않는(시간의 흐름에 따라 변하지 않는) 추가 정보이다.
| Metadata가 붙는 대상 | 예시 | 역할 |
| -- | -- | -- |
| Prim | `typeName` | Prim의 타입을 지정한다 |
| Prim | `apiSchemas` | 적용된 API Schema를 기록하는데 사용한다 |
| Prim 또는 Property | `documentation` | 설명문을 기록한다 |
| Prim 또는 Property | `customData` | 사용자 정의 관리 정보를 담는다 |
| Attribute | `custom`, `variability` | 사용자 정의 여부, 시간 변화 의도 등을 나타낸다 |
| Stage 수준 | `timeCodePerSecond` | Time Code와 초(second) 사이 관계를 지정 |
Metadata는 Scene을 어떻게 해석할지에 대한 정보를 담고 있다고 생각하면 된다.

## Prim의 Metadata와 Attribute의 Metadata는 서로 다르다는 것을 유념해야 한다
```
body.SetMetadata(
    "documentation",
    "Cube used in the USD lesson.",
)

temperature_attr.SetMetadata(
    "documentation",
    "Teaching value; not a thermal simulation.",
)
```
같은 이름의 Metadata를 사용하지만, 서로 다른 객체에 authoring 되는 Metadata이다.
```
print(body.GetMetadata("documentation"))
# 예상: Cube used in the USD lesson.

print(temperature_attr.GetMetadata("documentation"))
# 예상: Teaching value; not a thermal simulation.

print(temperature_attr.Get())
# 예상: 20.0
```
여기서 `temperature_attr.Get()`은 온도 값(value)을 읽고, `temperature_attr.GetMetadata("documentation")`은 Temperature Attribute의 documentation Metadata를 읽어온다.

## 사용자 정의 Metadata는 `customData`를 사용한다.
OpenUSD에서 Metadata 필드는, 미리 정해져있는 이름과 타입 체계를 사용하기 때문에 막 지정해서 사용할수는 없다. 공식적으로 제공되는 내용 이외에 직접 추가하고 싶은 정보가 있다면, `customData` 딕셔너리를 이용해서 작성할 수 있다.
```
body.SetCustomDataByKey(
    "demo:assetId",
    "body-001",
)

temperature_attr.SetCustomDataByKey(
    "demo:unit",
    "degC",
)

print(body.GetCustomDataByKey("demo:assetId"))
# 예상: body-001

print(temperature_attr.GetCustomDataByKey("demo:unit"))
# 예상: degC
```
개념적으로 위 커스텀 Metadata는 다음과 같은 구조를 갖는다.
```
{
    "demo": {
        "assetId": "body-001"
    }
}
```
## `custom=True`와 `customData`를 혼동하지 말 것
```
body.CreateAttribute(
    "demo:temperature",
    Sdf.ValueTypeNames.Float,
    custom=True,
)
```
이건 **사용자 정의 Attribute**를 만드는 것.
```
body.SetCustomDataByKey(
    "demo:assetId",
    "body-001",
)
```
이거는 **사용자 정의 Metadata를 기록하는 것**이다.

# Schema : 데이터에 구조와 의미를 부여하는 규격
## 왜 Schema가 필요한가?
Schema는 **데이터 구조와 해석 규칙**을 제공한다. NVIDIA 공식 자료에서는 Schema를 데이터 모델과, 사용자가 선택할 수 있는 API를 정의하는 것이라고 설명한다.  
예를 들어 예제의 Cube의 `size`는 공식적으로 다음과 같이 정의가 된다.  
```
double size = 2
```
이는 Cube schema에서 다음을 정한다는 뜻이다.
```
이름             size
데이터 타입      double
의미             큐브의 각 모서리 길이
fallback 값      2
```
따라서 Schema는 **Scene Data에 대한 규격을 정하고, 그 규격에 맞는 파이썬 API를 제공하는 것**이라고 총체적으로 이해하면 될 듯 하다.

## Schema의 종류
### Typed Schema : 이 Prim은 어떤 것인가?
`Cube`, `Camera`, `Xform` 등이 대표적인 예시이다.
```
def Cube "Body"
{
}
```
여기서 `Body`는 이름이고 `Cube`는 Prim의 타입이다.  
**Typed Schema**는 Prim의 기본적인 종류를 정의하며, 하나의 Prim에는 하나의 `typeName`을 가지게 된다. 다만, Schema 사이에는 상속 관계가 존재할 수 있으므로 하나의 구체적인 타입이 여러 상위 타입의 성질을 같이 가질 수 있다.  
다만 주의해야할 점은 **Schema의 상속 관계와 Stage의 부모-자식 계층은 별개**라는 것이다.
```
Stage 계층
    /World/Robot/Body

Schema 계층
    Cube가 상위 스키마의 성질을 물려받음
```
![02_Stage랑_Prim은.md](02_Stage와_Prim은.md)에서의 예제를 보면, Body가 `Xformable`인 이유는 부모 Prim의 이름이 Robot이라서가 아니라, `Cube` 스키마가 상속을 받았기 때문이다.  
또 다른 주의점으로 Typed Schema가 항상 명확한 타입을 부여하지는 않는다는 것인데, 예를 들어서 `UsdGeom.Xformable`처럼 추상적인 스키마도 존재한다.  
  
스키마까지 공부했다면, OpenUSD에서는 동일한 데이터를 서로 다른 API로 접근할 수 있다는 것의 의미를 알 수 있다.
```
body = stage.GetPrimAtPath("/World/Robot/Body")
cube = UsdGeom.Cube(body)
```
위의 두 접근법은 다음과 같이 해석될 수 있다.
```
Usd.Prim API
    이름, 경로, 부모, 일반 Property, Metadata 등을 다룸

UsdGeom.Cube API
    같은 Prim을 Cube 규격에 맞는 함수로 다룸
```
OpenUSD에서는 Schema 객체가 내부적으로 `UsdPrim`을 보유하고, 그 위에 각 schema에 걸맞는 API를 제공한다고 설명하고 있다. 예를 들어서, 다음 두 코드는 같은 Attribute를 가리킨다.
```
attr_a = body.GetAttribute("size")
attr_b = cube.GetSizeAttr()

print(attr_a == attr_b)
# 예상: True
```
즉, 차이점은 **Property 이름을 내가 직접 알고 문자열로 쓰느냐, 아니면 Schema가 제공하는 전용 함수를 통해 접근하냐** 이다. OpenUSD의 공식 튜토리얼도 Schema API를 사용하면, 내부 Property 이름과 같은 세부 사항을 코드에서 일일히 기술하지 않아도 된다고 얘기하고 있다.  
> **참고**. `GetTypeName()`을 사용할 때 Prim이냐 Attribute이냐 혼동하지 말자.
```
print(body.GetTypeName())
# Cube

print(body.GetAttribute("size").GetTypeName())
# double
```
> 이러면 첫번째는 Prim이 어떤 종류인가 이고, 두번째는 Attribute가 어떤 타입의 값을 담는가 이다.

### API Schema : 기존 Prim에 추가적인 규격을 적용하거나, 특정 정보에 접근하기
예를 들어보자. 로봇 시뮬레이션에서라면 이런 요구를 할 수 있다.  
> 이 물체는 Cube이면서 강체이고, 질량도 넣고 싶다.  
  
이때 Cube의 Prim 타입을 `RigidBody`로 변경하는 대신, 기존 Prim을 유지하면서 물리와 관련된 내용을 담은 API Schema를 적용할 수 있다.
```
rigid_body_api = UsdPhysics.RigidBodyAPI.Apply(body)
rigid_body_api.CreateRigidBodyEnabledAttr(True)

mass_api = UsdPhysics.MassAPI.Apply(body)
mass_api.CreateMassAttr(2.0)
```
이후에도 Prim 타입은 계속 `Cube`로 유지된다.
```
print(body.GetTypeName())
# 예상: Cube

print(body.HasAPI(UsdPhysics.RigidBodyAPI))
# 예상: True

print(body.HasAPI(UsdPhysics.MassAPI))
# 예상: True
```
여기에서 사용된 API 중 `RigidBody`는 강체 관련 데이터를, `MassAPI`는 질량 관련 데이터를 제공한다. 실제로 OpenUSD 공식 튜토리얼 역시 기존 컨텐츠에 물리 정보를 추가적으로 더할 수 있도록 API Schema를 활용하라고 소개하고 있다.  
  
그렇다면 실제로 `Apply()`는 무엇을 Authoring 할까?  
위의 예제를 기준으로 얘기한다면, `RigidBodyAPI.Apply(body)`는 Prim의 `apiSchemas` Metadata에 `PhysicsRigidBodyAPI`를 추가해서 적용 사실을 더한다. USDA 텍스트에서는 다음과 같이 나타난다.
```
def Cube "Body" (
    prepend apiSchemas = [
        "PhysicsRigidBodyAPI",
        "PhysicsMassAPI"
    ]
)
{
    bool physics:rigidBodyEnabled = true
    float physics:mass = 2
}
```
이를 해설하면 다음과 같다.
```
apiSchemas
    → 어떤 API Schema가 적용되어 있는지 기록하는 Metadata

physics:rigidBodyEnabled
    → 그 규격에서 제공하는 Attribute

physics:mass
    → 질량을 기록하는 Attribute
```
여기서 조심해야 할 것은, `.Apply()`와 단순 API를 사용한 객체 호출은 다르다는 점이다.
```
rigid_body_api = UsdPhysics.RigidBodyAPI(body)
```
이건 기존 Prim을 강체 API로 다루기 위한 객체를 구성하는 것이고
```
rigid_body_api = UsdPhysics.RigidBodyAPI.Apply(body)
```
이건 기존 Prim에 강체 속성을 추가하는 것이다.

### API Schema도 결국엔 Prim의 Attribute를 다룬다.
```
mass_api.GetMassAttr().Get()
body.GetAttribute("physics:mass").Get()
```
이 두 함수는 모두 같은 질량 값을 읽어 들인다 (공식 Mass API 문서를 보면 `GetMassAttr()`가 가리키는 Attribute 이름은 `physics:mass`, 타입은 `float`로 정의되어있다).  
이를 결합하면 다음과 같이 적을 수 있다.
```
UsdPhysics.MassAPI(body).GetMassAttr().Set(2.0)
```
이걸 풀어서 해석하면 다음과 같다.  
> 이 Prim을 Mass API로 다룬다 → 질량 Attribute를 얻는다 → 값 2를 작성한다.

### 근데 모든 API Schema가 `.Apply()` 하나만 쓰는건 아니다
API Schema는 다음과 같이 구성할 수 있다.
- **Single-apply API Schema**
  - 한 Prim에 해당 API Schema의 한 묶음을 적용한다. 위에서 다룬 예제가 그런 내용이다.
- **Multiple-apply API Schema**
  - 한 Prim에 이름을 달리하여 여러 API Schema 묶음을 적용할 수 있다.  
  
예를 들면 Robot Prim에 2종류의 Collection을 만들 수 있다.
```
parts = Usd.CollectionAPI.Apply(robot, "parts")
sensors = Usd.CollectionAPI.Apply(robot, "sensors")

parts.CreateIncludesRel().SetTargets([body.GetPath()])
sensors.CreateIncludesRel().SetTargets([camera.GetPath()])
```
그러면 같은 Robot Prim에 다음 이름의 Relationship이 존재할 수 있다.
```
collection:parts:includes
collection:sensors:includes
```
그 외에 Metadata(정확히는 `apiSchemas`)에 적용되었다는 사실은 남기지 않고, 그냥 내가 원하는 속성의 API Schema 작업을 적용할 수 있게만 해주는 **Non-applied API Schema**도 있다.
```
transform_api = UsdGeom.XformCommonAPI(robot)
transform_api.SetTranslate(Gf.Vec3d(1, 0, 0))
```
`XformCommonAPI`는 Non-applied API Schema로, 이를 사용하기 위해서 `XformCommonAPI.Apply()`를 사용해야 하는 것은 아니다.

# 최종 정리 : Property, Metadata, Schema
먼저 다음 예제 코드를 보자.
```
def Cube "Body" (
    prepend apiSchemas = [
        "PhysicsRigidBodyAPI",
        "PhysicsMassAPI"
    ]

    doc = "Cube used in the USD lesson."

    customData = {
        dictionary demo = {
            string assetId = "body-001"
        }
    }
)
{
    double size = 1

    float3[] extent = [
        (-0.5, -0.5, -0.5),
        (0.5, 0.5, 0.5)
    ]

    custom float demo:temperature = 20 (
        doc = "Teaching value; not a thermal simulation."

        customData = {
            dictionary demo = {
                string unit = "degC"
            }
        }
    )

    custom rel demo:camera = </World/Camera>

    bool physics:rigidBodyEnabled = true
    float physics:mass = 2
}
```
이제 이 예제 코드에서 Metadata, Schema 적용, Property( Attribute), Relationship에 대해서 읽을 수 있겠는가?  
  
결국 USD 파일을 본다고 하면, 다음 순서로 읽으면 된다.  
> 어떤 Prim인가 → 어떤 Schema가 연결되어 있는가 → 어떤 Property가 작성되어 있는가 → Prim과 Property 각각에 어떤 Metadata가 붙어 있는가.

# USD와 관련된 코드 해석하기
## 먼저 변수를 잘 구분해보자
```
prim = stage.GetPrimAtPath("/World/Robot/Body")
mass_api = UsdPhysics.MassAPI(prim)
mass_attr = mass_api.GetMassAttr()
mass = mass_attr.Get()
```
이 코드는 다음과 같이 구성되있다.
| 변수 | 역할 |
| -- | -- |
| `stage` | 전체 scene에 접근하는 객체 |
| `prim` | 장면 안의 Body Prim |
| `mass_api` | 그 Prim을 mass schema로 다루는 객체 |
| `mass_attr` | Property 중 Mass Attribute 객체 |
| `mass` | Attribute에서 읽은 실제 질량 값 |
이렇게 장면 객체 → Schema 접근 객체 → Property 객체 → 실제 값로 구분하면, USD 관련해서 긴 코드도 명확하게 구조를 파악해서 읽을 수 있다.

## 함수 이름으로 작업 종류를 구분해보자.
당연히 자세한 내용은 OpenUSD API 문서를 참고하면 되지만, 기본적으로 다음과 같은 구조를 참고하면 편하다.
| 코드 형태 | 대체로 하는 작업 |
| --- | --- |
| `GetPrimAtPath(...)` | Scene에서 Prim을 조회 |
| `GetAttribute(...)`, `Get..Attr()` | Attribute 객체를 반환 |
| `CreateAttribute(...)`, `Create...Attr(...)` | Attribute 정의나 값을 작성 |
| `attr.Get(...)`, `attr.Set(...)` | Attribute 값을 읽거나 작성 |
| `GetRelationship(...)`, `Get...Rel(..)` | Relationship 객체를 반환 |
| `rel.GetTargets()`, `rel.SetTargets(...)` | Relationship의 대상 경로를 읽거나 작성 |
| `GetMetadata(...)`, `SetMetadata(...)` | 호출 대상 객체의 Metadata를 읽거나 작성 |
| `SomeAPI.apply(prim)` | Applied API Schema의 적용 사실을 metadata에 작성 |

## Prim을 수정하지 않고 조사하는 꿀팁 코드
```
def inspect_prim(stage, prim_path):
    prim = stage.GetPrimAtPath(prim_path)

    if not prim:
        raise ValueError(f"Prim을 찾을 수 없습니다: {prim_path}")

    print("=== Prim ===")
    print("path:", prim.GetPath())
    print("type:", prim.GetTypeName())
    print("applied schemas:", prim.GetAppliedSchemas())

    print("\n=== Prim에 작성된 Metadata ===")
    print(prim.GetAllAuthoredMetadata())

    print("\n=== Attributes ===")
    for attr in prim.GetAttributes():
        print(
            attr.GetName(),
            "type =", attr.GetTypeName(),
            "custom =", attr.IsCustom(),
            "authored value =", attr.HasAuthoredValue(),
            "default =", attr.Get(),
            "time samples =", attr.GetTimeSamples(),
        )

    print("\n=== Relationships ===")
    for rel in prim.GetRelationships():
        print(
            rel.GetName(),
            "targets =", [str(path) for path in rel.GetTargets()],
        )


inspect_prim(stage, "/World/Robot/Body")
```