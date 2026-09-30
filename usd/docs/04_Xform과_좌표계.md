# Xfrom과 좌표계
USD를 다룰 때, Xform과 좌표계는 **물체가 공간 상에서 어떻게 배치되는지**에 대해서 다루는 거싱라고 보면 된다. 당연한 것이, 어떠한 숫자로 좌표가 주어져 있다고 가정하자. 그 좌표만으로 공간 상의 어떤 지점을 가리키는지 확언할 수 있는가? 불가능하다. 우리는 좌표계를 통해서 물체의 위치를 나타내기 위해서는 **원점과 기준축**이 존재해야함을 이미 수학 등에서 공부해서 뼈저리게 알고 있다.  
 
USD에서는 보통 3가지 관점으로 구분을 한다.
| 표현 | 의미 |
| -- | -- |
| **Object Space/Local Space** | 해당 Object Assset의 좌표계 | 
| **Parent Space** | 부모 좌표계 |
| **World Space** | Scene 전체의 전역 좌표계 |
USD의 로컬 변환은 일반적으로 해당 Prim의 국소적 좌표계를 부모 좌표계와 연결하고, 이걸 반복해서 전역 좌표계에 연결하는 것으로 구성한다. 뭐, 사실 이것만 보면 ROS든 URDF든 다 비슷하기는 하다.  
  
여기서 한가지 혼동을 가질 수 있는 것은, Stage 내의 일반적으로 가장 상위에 위치하는 Prim인 `/World`는 World 좌표계 그 자체를 의미하는 것이 아니라는 것이다. World 좌표계로 착각하고, `/World`에 이것저것 이상한 변환들을 막 부여하면 scene이 의도하지 않은 형태로 동작할 것이다.

# Xform이란 무엇인가?
OpenUSD의 Xform 관련 공식 API는 `UsdGeomXform`을 다음과 같이 정의한다.  
> **Concrete prim schema for a transform, which implements Xformable.**  
  
다시 설명하면 공간 변환을 표현하는 Prim Schema이며, Xformable의 기능을 구현하는데 사용된다: 즉, 공간에 어떻게 구성요소들을 배치할지에 대해서 사용하는 Prim 타입이다.

## 이동, 회전, 스케일링(크기 변경)
공간 변환에서 자주 사용되는 3가지 요소는 다음과 같다.
| 요소 | 의미 |
| -- | -- |
| Translation | 위치 이동 |
| Rotation | 방향 회전 |
| Scale | 크기 변경 |
USD에서는 이 3가지 외에도 쿼터니언 회전, 행렬 변환 등 다양한 좌표 변환 연산을 제공한다고 안내하고 있다. 로보틱스에서 **pose**는 보통 Translation과 Rotaion을 이용해서 로봇의 위치를 기술하는데 사용하는 표현이지만, USD에서는 크기 변환인 스케일링이 포함되어있을 수 있기 때문에 마냥 pose로 일반화할 수는 없다.
```
def Xform "Robot"
{
    def Cube "Body"
    {
    }
}
```
보통 이런 식으로 튜토리얼에서는 작성한다.

## Xform, Xformable, XformOp의 차이
| 이름 | 의미 |
| `UsdGeom.Xform` | 변환, Grouping을 위한 Prim 타입 |
| `UsdGeom.Xformable` | 공간 변환이 가능한 Prim들을 공통으로 다루는 schema |
| `UseGeom.XformOp` | 이동, 회전, 크기 변경과 같은 변환 연산 하나를 다루는 객체 |
| `UsdGeom.XformCommonAPI` | 일반적인 이동, 회전, 크기 변환 등을 편하게 다루기 위한 API |
기본적인 schema들 중에선 이미 변환 schema를 상속받아서, 자체적으로 `Xformable`한 schema들이 있다. 예를 들어서 `Cube`가 그러며, `Cube` 자체에 직접 변환 코드를 작성할 수 있다.
```
cube = UsdGeom.Cube.Define(stage, "/World/Body")
cube.AddTranslateOp().Set(Gf.Vec3d(1,0,0))
```
## 변환은 Prim의 Attribute로 작성한다.
```
def Xform "Robot"
{
    double3 xformOp:translate = (10, 0, 0)
    float xformOp:rotateZ = 90

    uniform token[] xformOpOrder = [
        "xformOp:translate",
        "xformOp:rotateZ"
    ]
}
```
앞에서 Prim과 Attribute에 대해서 공부를 잘했다면, 이 코드에 대해서 추가적인 설명 없어도 이해하기 쉬울 것이다.

### 단, 변환 순서를 혼동하면 안된다.
실제 변환이 적용되는 순서는 `xfromOpOrder`에 들어있는 이름과 순서가 결정한다. 어떤 `xformOp:` 형태의 변환 Attribute가 존재하더라도, `xformOpOrder`에 포함되지 않으면 그 변환 연산은 최종 변환에서 사용되지 않는다.

### 자주 만나는 변환 Attribute
| Attribute 형태 | 의미 |
|---|---|
| `xformOp:translate` | 세 축의 이동 |
| `xformOp:rotateZ` | Z축 회전 |
| `xformOp:rotateXYZ` | 지정된 순서의 오일러 회전 |
| `xformOp:orient` | 쿼터니언으로 표현한 회전 |
| `xformOp:scale` | 세 축의 크기 변경 |
| `xformOp:transform` | 4×4 행렬로 표현한 변환 |

## `xformOpOrder`는 어떻게 읽지?
```
["xformOp:translate", "xformOp:rotateZ"]
```
이렇게 구성된 코드는 **변환 스택에 어떻게 변환을 적용할지 쌓는 순서**이다. 따라서 뒤쪽의 연산이 먼저 적용된다고 해석해야 한다.
```
xformOpOrder = [Translate, Rotate, Scale]

점에 적용하는 순서:
    Scale → Rotate → Translate
```
당연한 얘기지만, Rotation과 Translation의 순서를 바꾸면 결과가 바뀔 수 있으므로 주의해서 사용해야 한다.

## 예시를 하나 만들어보자.
예시는 다음과 같이 구성된다.
```
/World                  변환 없음
└─ Robot                이동 (10, 0, 0), Z축 회전 90도
   └─ Body              부모 기준 이동 (1, 0, 0.5)
```
이것을 파이썬 코드로 작성하면 다음과 같다.
```
from pxr import Usd, UsdGeom, Gf, Sdf

# 별도의 학습용 Stage입니다.
stage = Usd.Stage.CreateInMemory()

UsdGeom.SetStageMetersPerUnit(stage, 1.0)
UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)

world = UsdGeom.Xform.Define(stage, "/World")
stage.SetDefaultPrim(world.GetPrim())

# Robot: xformOpOrder = [translate, rotateZ]
robot = UsdGeom.Xform.Define(stage, "/World/Robot")

robot_translate = robot.AddTranslateOp()
robot_translate.Set(Gf.Vec3d(10, 0, 0))

robot_rotate = robot.AddRotateZOp()
robot_rotate.Set(90.0)

# Body: xformOpOrder = [translate]
cube = UsdGeom.Cube.Define(stage, "/World/Robot/Body")
cube.CreateSizeAttr(1.0)
cube.CreateExtentAttr([
    Gf.Vec3f(-0.5, -0.5, -0.5),
    Gf.Vec3f(0.5, 0.5, 0.5),
])

body_translate = cube.AddTranslateOp()
body_translate.Set(Gf.Vec3d(1, 0, 0.5))

body = cube.GetPrim()
```
여기서 World 좌표계 기준 Body의 위치는 `(10, 1, 0.5)`가 될 것이다. 왜인지는 생각해보자.

## USD에서 행렬은 어떻게 다루는가?
OpenUSD의 수학 연산 라이브러리인 `Gf`는 행벡터가 행렬 왼쪽에서 곱해지도록 연산 체계를 사용한다. 예를 들면 다음과 같다: `p' = pM`  
따라서 크기 변경 → 회전 → 이동을 차례로 적용한다고 하면 다음과 같다: `p' = pSRT`  
파이썬에서는 다음과 같이 표현한다.
```
result = (S * R * T).Transform(point)
```
그리고 `Gf.Matrix4d`의 Transformation Matrix에서 Translation 성분은 **마지막 열이 아니라 마지막 행에 위치한다**.  
이런 USD의 규약 아래에서 다음과 같은 예시를 정의한다면
```
L_body    Body의 로컬 → 부모 변환
W_robot   Robot의 로컬 → 월드 변환
W_body    Body의 로컬 → 월드 변환
```
이렇게 작성이 된다.
$$
W_{\text{body}} = L_{\text{body}} W_{\text{robot}}
$$
즉, 먼저 Body 좌표계의 로컬 변환을 적용하고, 그 결과에 Robot 좌표계의 변환을 적용하는 것이다.  
위에서 언급한 것처럼, 우리 예제의 Body의 World 행렬은 다음과 같이 쓰일 수 있을 것이다.  
$$
\begin{bmatrix}
0 & 1 & 0 & 0 \\
-1 & 0 & 0 & 0 \\
0 & 0 & 1 & 0 \\
10 & 1 & 0.5 & 1
\end{bmatrix}
$$
## 코드를 통해서 USD의 변환 읽어보기
앞에 예제에 붙여서 실행하면 된다.
```
time = Usd.TimeCode.Default()

xformable = UsdGeom.Xformable(body)

local_matrix = xformable.GetLocalTransformation(time)
world_matrix = xformable.ComputeLocalToWorldTransform(time)

print(local_matrix.ExtractTranslation())
# 예상: (1, 0, 0.5)

print(world_matrix.ExtractTranslation())
# 예상: (10, 1, 0.5)
```
| 코드 | 반환하는 값 |
|---|---|
| `GetAttribute("xformOp:translate").Get()` | 특정 이동 연산 하나의 값 |
| `GetLocalTransformation()` | 이 Prim의 여러 연산을 합친 로컬 변환 |
| `ComputeLocalToWorldTransform()` | root까지 부모들의 변환까지 반영한 월드 변환 |

### 위치와 방향에 대해서 변환하기
```
local_point = Gf.Vec3d(0.5, 0, 0)
world_point = world_matrix.Transform(local_point)

print(world_point)
# 예상: (10, 1.5, 0.5)

local_direction = Gf.Vec3d(1, 0, 0)
world_direction = world_matrix.TransformDir(local_direction)

print(world_direction)
# 예상: (0, 1, 0)
```
`Transform()`을 통해서 위치를 변환하고, `TransformDir()`은 방향만 변환한다.

### World 좌표를 다시 내가 원하는 로컬 좌표로 만들수는 없을까?
```
recovered_local_point = world_matrix.GetInverse().Transform(world_point)

print(recovered_local_point)
# 예상: (0.5, 0, 0)
```
USD의 행벡터 표현법으로는 다음과 같이 작성한다 보통.
```
a_to_b = world_from_a * world_from_b.GetInverse()
point_in_b = a_to_b.Transform(point_in_a)
```

### 시간 지정은 불가능한가?
```
world_at_24 = xformable.ComputeLocalToWorldTransform(
    Usd.TimeCode(24)
)
```
가능하다. TimeCode에 대해서는 앞에서 배웠으니 넘어가도록 하겠다.

### 부모의 변환 상속을 없앨 수는 없는가?
```
body_translate.Set(Gf.Vec3d(1, 0, 0.5))
xformable.SetResetXformStack(True)
```
`resetXformStack`을 사용하면 가능하다. 위 예시에서는 결과가 다음과 같이 된다.
```
설정 전 월드 원점 = (10, 1, 0.5)
설정 후 월드 원점 = (1, 0, 0.5)
```
단, 변환만 받지 않는 것이지 Prim 간의 부모-자식 관계는 계속 유지된다.

## 피벗과 XformCommonAPI
물체가 자신의 원점이 아니라 어떤 특정 점을 기준으로 회전해야 한다면 **피벗**이라는 개념을 사용한다.
```
피벗이 원점이 되도록 이동
    → 회전·크기 변경
    → 원래 피벗 위치로 되돌림
```
USD에서는 다음과 같은 연산 순서를 통해서 피벗 변환을 진행한다.
```
[
    "xformOp:translate",
    "xformOp:translate:pivot",
    "xformOp:rotateXYZ",
    "xformOp:scale",
    "!invert!xformOp:translate:pivot"
]
```
여기서 `!invert!`는 해당 연산의 역변환을 사용한다는 의미로 작성되었다.  
일반적인 피벗, 이동, 회전, 크기 변환을 다룰 때는 다음과 같이 사용할 수 있다.
```
tool = UsdGeom.Xform.Define(stage, "/World/Tool")
common = UsdGeom.XformCommonAPI(tool.GetPrim())

common.SetTranslate(Gf.Vec3d(1, 0, 0))
common.SetPivot(Gf.Vec3f(0.5, 0, 0))
common.SetRotate(Gf.Vec3f(0, 0, 90))
common.SetScale(Gf.Vec3f(1, 1, 1))
```
`XformCommonAPI`는 **Non-applied API Schema**로, `.Apply()`를 호출하지 않아도된다.

## USD의 축과 단위
USD에서는 `upAxis`와 `meterPerUnit`을 통해서 축과 단위를 지정한다.
```
UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
UsdGeom.SetStageMetersPerUnit(stage, 1.0)
```
다만, 위 예시처럼 설정된 한 asset에서 다른 asset을 refernce 해서 가져올때, 만약 두 asset 간의 축과 단위가 다르다면 그걸 USD가 자동으로 찝어서 변환해주진 않는다. 그건 내가 직접 해야한다.