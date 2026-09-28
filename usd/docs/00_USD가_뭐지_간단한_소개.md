# USD
USD란 뭘까? Universal Scene Description의 줄임말.  
Pixar에서 개발한 기술로, 3D 장면을 표현하기 위한 포맷이다.  
[**Pixar의 자료**](https://openusd.org/files/USD_Quickstart_Guide.pdf)에 의하면, USD는 다음과 같은 배경과 목적을 가지고 개발되었다.

## 참고로 알아놓으면 좋은 것 -- Scene Description이란 무엇인가?
단순히 하나의 3D CAD 모델링이나 이런 것을 의미하는게 아니고, 한 Scene 안에 어떤 물체가 존재하는지, 각 물체들이 어떻게 연결되어있는지, 어떤 데이터를 어디서 가져오는지, 각 데이터에 어떤 수정과 변형이 적용되는지를 통합적으로 기술하는 구조라고 생각하면 된다.  
  
USD에서는 이런 3D Scene에 대해서 묘사하기 위해서 여러 파일과 Asset을 Layer, Reference, Variant, Override 등의 방식으로 조합해, 단일 3D `Stage` / Scenegraph를 만들어낸다. 실제로 USD를 다루고 있는 메인스트림인 **OpenUSD**의 공식 문서도 USD는 여러 asset으로 이루어진 복잡한 Scene을 구성하고, 어플리케이션 사이에서 Scene을 전달하고, 가역 + 비파괴적인 방식으로 파일을 수정할 수 있는 능력을 지원하기 위해서 개발되었다고 얘기하고 있다.  
  
따라서 한 줄 요약을 한다면, **USD = 3D scene data의 공통 포맷 + Layer 시스템 + Reference 시스템 + Scene Composition Engine**이다.

## USD는 어떤 역사적 배경을 가지고 있는가?
- **1994년, Marionnette**
  - 토이 스토리를 촬영할 때만 하더라도 한 Shot에서의 장면 정보는 기본적으로 하나의 프로그램 파일 형태로 기술되었다 (즉 하나를 모사하기 위해서 하나의 파일이 필요한 구조) : Shots described as single, linear program file for **Toy Story** in proprietary animation system, Marionette.
  - 픽사에서는 이를 개선하기 위해서 각종 개념을 추가하기 시작했다 : Started to add and evolve concepts for referencing, layering, editing, and variation.
- **2004년, Presto**
  - 기존의 방식의 scene-composition 기능들이 여러 포맷과 여러 composition engine에 나뉘어 있어서 일관적으로 조립하기 어렵다는 단점, 그리고 당시 등장하던 멀티코어 시스템과 같이 새로운 하드웨어를 사용하기 어렵다는 단점이 드러났다. 이에 따라서 새롭게 개발된 시스템이 **Presto**이다.
  - Unified Referencing, overriding, variation, and other operations at all granularities into a single text format evlauated with a single composition engine. 라는 설명에서 알 수 있듯 그동안 분산되어있던 composition engine을 통합했다는 것이 중요한 개념이다.
- **2008년, TidScene**
  - 애니메이션 영화를 제작할 때, rigging이 완료된 결과물을 계속 가지고 있는 것은 무겁고 불필요하다는 점이 있었다. 이미 모든 작업이 끝난 캐릭터의 최종 vertex 위치와 transform만 time-series로 저장해서 다음 후처리 부서들에게 넘기면 보다 간단하게 작업을 할 수 있다.
  - 따라서 TidScene은 이런 요구사항을 반영해, geometry schema와 binary database, scenegraph를 활용해서 time-sampled data를 빠르게 읽고 처리 간으하도록 구성되었다.
  - 여기서 **time-sampled data**는 속성 값이 시간에 따라 변화하는 데이터를 의미하고,
  - **Lazy-Acess**는 모든 데이터를 처음부터 메모리에 올리는 것이 아니라, 필요할 때 필요한 부분만 읽도록 구성하는 방식을 의미한다.
  - 이를 요약한 영어 설명은 다음과 같다: A geometry schema with a lightweight scenegraph that enabled preview rendering across pipeline, and had a referencing featrue used for layering, scenegraph "isolation", asset referencing, and some variation support.
- **2012년, Universal Scene Description**
  - 여기서 픽사는 다음과 같은 시스템을 가지게 되었다.
    - **Presto** : 강력한 단일 Scene Composition 시스템
    - **TidScene** : Scenegraph와 schema 등을 통한 대규모 데이터 처리 시스템
  - 이 2가지 시스템을 합치는 것은 목표로 개발된 것이 USD이다. 다음과 같은 설명에서 확인 가능하듯, Presto의 composition engine과 low-level data model과 TidScene의 lazy-access, time-sampled data model, lightweight scenegraph을 결합하기 위해서 개발되었다: Married the composition engine and low-level data model from Presto with the lazy-access, and time-sampled data model and lightweight scenegraph from TidScene, introducing parallel computation.

## USD로 뭘 할 수 있는데?
- Represent scene description and 3D graphics concepts.
  - 그냥 Vertex만 저장하는 또 다른 3D 포맷이 아니라, **Prim**을 중심으로 Geometry, Transform, Material, Shading, Light, Animation/Time-Sampled Data를 모두 표현 가능하게 한 시스템이다. 각 Prim별로 Attribute와 Relationship 같은, Property가 붙고 이런 데이터들을 활용해서 Scene Graph를 생성하는 것이 USD이다.
  - 예를 들면 다음과 같은 구조이다.
    ```
    /World
      /Character
        /Body
        /Hair
      /Environment
      /Camera
      /Lights
    ```
  - 따라서 `.obj` 파일처럼 단순히 Mesh 하나만 표현하고 끝내는 것이 아니라, **어떤 물체가 있고, 그 물체의 material은 어떤 것이고, 어디에 위치하며, 시간에 따라 움직이고, 다른 이런이런 asset들을 reference해서 사용하고 있다** 라는 내용을 한번에 묘사할 수 있다는 것이 장점이다.
- Combine layers of artistic decisions through a versatile set of provided mechanism (e.g. layer stacks, variantt sets, payloads, etc.)
  - 여러 명이 작업한 데이터를 단순히 하나의 파일로 통합해버리는게 아니라, 마치 그림그릴때 레이어를 쌓아서 그리는거처럼 원본 파일을 유지한 채로 레이어처럼 겹칠 수 있다.
  - 따라서 각 레이어r별 데이터를 파괴하고 그냥 합쳐버리는게 아니라, 필요한 레이어만 지정해서 수정하거나 하는 식의 장점을 취할 수 있다. USD는 **non-destructive editing**이라고 표현한다.
  - 그리고 이렇게 합치는 과정을 **Composition**이라고 표현한다.
    - 이때 **Layer Stack**: 여러 USD Layer를 순서대로 겹쳐서 하나로 만드는 구조
    - **Variant Set**: 하나의 asset 아래 여러가지 property 선택지를 부여 (예: Car라는 Asset에 red/blue/black 선택지 set 부여)
    - **Payload**:  필요한 시점까지 실제 데이터를 로딩하지 않을 수 있는 Deferred reference.
- Image (with Hydra) to provide a "ground truth" rendering of any scene
  - 여기서 **Image**는 USD Scene을 렌더링 해서 보여준다는 뜻이다.
  - **Hydra**는 렌디렁 아키텍쳐/프레임워크를 의미한다.
- Be extended/customized with asset resolvers, file format plugins, custom schemas and metadata
  - core에 대해서 수정하지 않고도 위에 나열된 것처럼 다양한 확장 플러그인을 제공한다.

### USD를 왜 써야 하는데?
- Facilitates the use of multiple digital content creation(DCC) applications by extensively and flexibly preserving data through the 3d pipeline.
  - 여기서 DCC는 3D 제작 프로그램을 의미한다(예: 블렌더).
  - 이런 DCC들 사이에서 Interchangable한 Scene description을 만드는게 USD의 목표라 볼 수 있다.
- Allows multiple artists to collaborate on the same assets and scenes.
  - Layering이 가능하기 때문에, 각자 맡은 파트에 따라서 각자의 Layer만 수정하고 Composition 할 수 있다.
- Maximizes artistic iteration by minimizing latency.
  - multi-core를 사용하며, scene graph 방식, payload를 활용해 필요한 부분만 메모리에 올리는 방식, Hydra 기반 Groud-Truth preview 기능을 활용해 빠른 작업 속도를 지원한다.