# Stage와 Prim
![Stage](../asset/image.png)
USD의 가장 기초가 되는 개념인 **Stage**와 **Prim**에 대해서 배워보자.  
**Stage**는 여러 장면 데이터를 조합(composition)해서 보여주는 전체 3D Scene이라고 보면 되고  
**Prim**은 한 장면 안에서 고유한 이름과 경로를 가지는, 장면의 구성요소라고 보면 된다.

## Stage의 정의
OpenUSD의 공식 정의는 다음과 같이 기술한다.
> A stage is a fully composed scenegraph.
> The stage always presents a composed view of scene description, managing prim composition, value resoulution and change processing. A stage is created by opening a root layer and composing all referenced/layered files it specifies. Stage provide the primary API for querying and authoring USD data through UsdPrim and UsdProperty objects. Multiple stages can be open simultaneously, and stages support both read-only and editable modes.  

이에 대해서 간단히 요약하면 다음과 같이 쓸 수 있다: **Scene Description을 담고 있는 최상위 컨테이너, 내부에 다수의 Prim들을 조합하고 계층화 시킨 다음에 Scene Graph로 제공하는 것**.

- **Scene Description** : 픽셀을 직접적으로 기술하는 것이 아니라, 장면 내에 어떤 물체가 있고, 어떤 계층 구조가 있으며, 어떤 속성이 설정되어 있는지 표현하는 데이터
- **Scene Graph** : 장면의 구성요소와 연결 구조를 노드와 엣지 형태로 표현한 데이터 구조. USD의 Prim들은 계층 구조로 구성이 되며, Stage 내부에 그 계층이 존재하고 / 탐색 및 읽기 기능을 지원한다.
    ```
    Stage
    └─ /World                  ← Prim
    ├─ /World/Car           ← Prim
    │  ├─ /Body             ← Prim
    │  └─ /Wheel            ← Prim
    ├─ /World/Camera        ← Prim
    └─ /World/Light         ← Prim
    ```
    - 이 구조 자체가 Scene Graph이다.
- **Composition** : Stage는 여러 파일이나 데이터 소스의 내용을 (작업 내용에 따라) 여러 Prim 등을 조합해서 사용한다.

기본적으로 다음과 같은 구조라고 구분지으면 된다.
```
장면을 기술한 파일·데이터
          ↓ USD가 해석하고 조합한다
Stage: 프로그램이 조회하고 편집하는 장면
          ↓ 렌더링 시스템이 사용한다
화면에 보이는 이미지
```
다만 오해하면 안되는건 Stage가 파일이나 이미지를 의미하는건 아니다. Stage는 그냥 3D 프로그램 안에서, 조합된 여러 장면들을 다루기 위한 객체로서 만들어져있고, 여러 방식으로 접근이 가능한 객체일 뿐이다. 예를 들어서 파이썬에서는 `Usd.Stage`로 Stage 그 자체에 접근해서 사용한다.

## Prim의 정의
Prim의 공식적인 정의는 다음과 같다.
> A Prim (primitive) is the primary container object in USD that can hold other prims and properties.
> Prim create a namespace hierachy on a stage and contain ordered properties (attributes and relationship) that hold meaningful data. Prims always have a resolved specifier (def, over, or class) that deteremines their role, and may have a schema typeName that dictates what data they contain. Prims provide the granularity for instancing, load/unload behavior, and activation/deactivation. The `UsdPrim` class provides the API for interacting with prims.

Prim은 USD의 가장 기본적인 컨테이너 객체라고 이해하면 된다. Prim은 다른 Prim을 포함해서 계층 구조를 만들 수 있고, 각 객체의 실제 데이터를 담는 Property도 내부에 담을 수 있도록 구성된다.
```
어떤 Prim
├─ 이 Prim을 설명하는 데이터
├─ 이 Prim의 속성들
└─ 이 Prim 아래에 배치된 다른 Prim들
```
이러한 특성 때문에 Prim은 기본 도형, 형상 뿐 아니라 재질, 조명, 카메라, 좌표 변환을 위한 구성요소도 모두 Prim으로 취급해서 다룰 수 있다.

## Stage와 Prim 구분해보기
먼저 간단한 예시를 하나 들어보자.
```
Stage
└─ /                          ← Pseudo-root
   └─ World                   ← Xform Prim
      ├─ Robot                ← Xform Prim
      │  └─ Body              ← Cube Prim
      └─ Camera               ← Camera Prim
```
이 예시에서 우리는 4개의 Prim을 정의한다.
| 이름 | 전체 경로 | 타입 | 이 예제에서의 역할 |
| -- | -- | -- | -- |
| World | /World | Xfrom | 장면의 구성요소들을 통합한다. |
| Robot | /World/Robot | Xform | 로봇에 속할 구성요소들을 한데 묶어 통합한다. |
| Body | /World/Robot/Body | Cube | 큐브 형상을 의미한다. |
| Camera | /World/Camera | Camera | 카메라 데이터를 의미한다. |

이것처럼 우리는 Prim을 경로를 통해서 탐색하고, Prim의 타입을 통해 어떤 종류의 데이터인지 해석할 수 있다.

### /World가 Stage인가?
여기서 `/World`는 **Stage 안에 있는 Prim 하나**이다.  
가장 위의 `/`는 **Pseudo-root** 라는 이름의 특별한 Prim이다. 이 Pseudo-root의 정확한 정의는 다음과 같다.
> The pseudo-root is a convenience prim at path `/` that serves as the parent of all root prims on a stage. Each stage contains a pseudo-root prim that allows the stage to contain a single tree of prims rather thas a forest. The pseudo-root facilitates traversal and processing by providing a common ancestor for all authored root prims. It's represented by the path `/` and is accessible via `UsdStage::GetPseudoRoot()`.

Stage의 최상위 Prim들을 하나의 계층 아래에서 쉽게 다룰 수 있도록 제공하는 편의용 Root라고 생각하면 된다. 저기 나와있는건 C++에서 접근할 때의 API고, 파이썬에서는 `stage.GetPseudoRoot()`를 통해서 얻을 수 있다. 위 예시에서, `/World`의 부모는 Stage 객체 자체가 아니라 이 Pseudo-root이다.  
```
Stage : 전체 장면을 제공하는 객체
/ : 그 장면 계층의 편의용 root prim
/World : 일반적인 prim
```

### Prim이 있으면 반드시 시각적 요소가 있어야 하는가?
꼭 그런 것은 아니다. 위 예시에서 알 수 있듯이 `/World`와 `/Robot`은 시각적으로 구성이 되어있지 않은 타입의 Prim들이다 (둘 다 `Xform`). 여기서 `Xform`은 이동, 회전, 크기 변경과 같은 공간 변환을 표현하는 타입이고, 시각적으로 뭔가 보여지는 타입은 아니다.

## Prim의 이름, 타입, 경로, 속성이란?
Prim은 총 4가지 구성요소로 이루어져 있다.

### 이름(name)
이름은 그냥 식별하기 위해서 붙이는거고, 이름에 따라서 타입이나 속성이 자동으로 부여되는건 아니다. 예를 들어서 다음과 같다.
```
def Cube "Camera"
{

}

def Camera "Camera"
{

}
```
둘은 서로 같은 이름이지만 다른 타입의 Prim이다.

### 타입
`Cube`, `Camera`, `Xform` 등은 타입이다.  
USD에서는 `Schema`(후술 예정)가 Prim 데이터의 구조와 의미를 정의한다. 우선 Schema는 "이 종류의 Prim에는 어떤 데이터가 있고, 그 데이터를 어떻게 해석하는지 정한 규칙"이라고 생각하면 된다. 예를 들어서, `Sphere` schema는 `radius`라는 반지름 속성을 정의한다.  
  
다만, 모든 Prim이 반드시 구체적인 타입을 가져야 하는 것은 아니며 타입을 지정하지 않은 Prim도 생성이 가능하다. 실제로 `DefinePrim()` 함수를 사용하면 타입 없는 Prim 정의가 가능하다.

### 경로
Prim 경로는 이 Prim이 장면의 어디에 있는지를 나타내는 정보이다.  
```
/World/Robot/Body
```
이러면 `Body`는 `Robot`의 자식(child)이고, `Robot`은 `World`의 자식이다.  
경로는 Stage 내부에서 각 Prim들이 어디에 위치해 있는지 나타낸다고 보면 된다. 실제로 NVIDIA 공식 문서에서는 `/`를 통해서 Prim의 이름들을 구분하고, 각 Prim을 장면 안에서 경로로 식별한다고 설명하고 있다. 여기서 주의해야 하는 점은 이름이 같아도 경로가 다르면 다른 Prim이라는 것이다.
```
/World/RobotA/Body
/World/RobotB/Body
```
이 2개는 서로 다른 경로고, 서로 다른 Prim이다.

### Property
이 Prim이 어떤 데이터를 가지고 있는가? 에 대한 대답이다. Prim에 속한 데이터를 표현하는 구성요소라고 보면 된다. USD의 Property는 보통 다음과 같이 2종류가 있다.
| 종류 | 의미 | 예시 |
| -- | -- | -- |
| Attribute | 특정 타입의 값 | 크기, 위치, 색상, 문자열 |
| Relationship | 장면의 다른 구성요소를 가리키는 연결  | 특정 재질이나 다른 Prim을 가리키는 경로 |
쉽게 얘기해서, **Attribute**는 값이라고 생각하면 된다. 각 Attribute는 데이터 타입을 가지며, 