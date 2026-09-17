# USD 핵심 개념: 파일에서 장면까지

[학습 안내](README.md) · 다음: [라이브러리와 실행 환경](LIBRARIES.md)

## 1. USD는 무엇을 표현하나요?

**USD(Universal Scene Description, OpenUSD)는 3D 장면을 기술하고 여러 자산을 합성하는 프레임워크**입니다. 메시뿐 아니라 물체의 배치, 재질, 조명, 애니메이션, 물리 설정도 표현합니다. Isaac Sim은 이 장면 데이터를 읽어 렌더링하고 물리 시뮬레이션을 실행합니다. 따라서 USD 파일을 만들었다는 것과 시뮬레이션을 실행했다는 것은 별개의 단계입니다. [NVIDIA OpenUSD 소개](https://developer.nvidia.com/openusd), [Isaac Sim 5.1 소개](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/index.html#usd)

## 2. Stage · Prim · Layer를 구분하기

| 개념 | 짧은 정의 | 로봇 장면으로 생각하면 |
|---|---|---|
| **Stage** | 여러 데이터 원천을 합성해 메모리에서 제공하는 장면 | 로봇·바닥·조명을 한꺼번에 조회하는 장면 |
| **Prim** | Stage에서 경로로 식별하는 장면 요소 | 로봇을 묶는 Xform, 메시, 재질, 조명, 관절 |
| **Layer** | Prim과 속성에 대한 작성 내용을 담는 데이터 단위 | 외형 파일, 물리 설정 파일, 실험별 수정 파일 |

Stage는 파일 그 자체가 아닙니다. 하나의 Layer로 시작할 수도 있고, 여러 파일을 reference나 sublayer로 조합할 수도 있습니다. Layer 역시 항상 디스크 파일일 필요는 없으며 임시 메모리 Layer도 가능합니다. [Stage](https://docs.nvidia.com/learn-openusd/latest/stage-setting/stage.html), [Layers](https://docs.nvidia.com/learn-openusd/latest/composition-basics/layers.html)

다음 그림에서 **왼쪽은 데이터의 연결, 오른쪽은 합성 결과의 Prim 계층**입니다. Layer와 Prim을 같은 트리로 생각하지 마세요.

```text
데이터 연결 예시                           Stage의 Prim 계층 예시
scene.usda (root layer)                    /                ← pseudo-root
 ├─ sublayer: experiment.usda              └─ World         ← Xform Prim
 └─ sublayer: layout.usda                     ├─ Robot      ← Xform Prim
       └─ reference: robot.usda               │   ├─ Body   ← Mesh Prim
                                             │   └─ Camera ← Camera Prim
                                             └─ Light      ← Light Prim
```

- `/World/Robot/Body`는 Prim 경로입니다. `/World/Robot/Body.points`는 그 Prim의 속성 경로입니다.
- `/`는 Stage가 제공하는 특별한 **pseudo-root**이고, `/World`는 직접 만드는 일반 Prim입니다. 이름을 반드시 `World`로 정해야 하는 것은 아닙니다.
- Prim은 눈에 보이는 도형만 뜻하지 않습니다. 묶음용 `Xform`, 정리용 `Scope`, 재질과 관절도 Prim입니다. [Prims](https://docs.nvidia.com/learn-openusd/latest/stage-setting/prims.html)

**defaultPrim**은 파일을 참조하면서 내부 Prim 경로를 생략했을 때 사용할 대표 진입점입니다. 재사용할 자산은 보통 최상위 Prim 하나에 필요한 내용을 모으고 이를 defaultPrim으로 설정합니다. `/`나 카메라 시점과는 관계없습니다. [Default Prim](https://docs.nvidia.com/learn-openusd/latest/composition-basics/default-prim.html)

## 3. Prim 안에는 무엇이 있나요?

| 구성 | 의미 | 예 |
|---|---|---|
| Attribute | 자료형이 있는 값. 시간별 값도 기록 가능 | 큐브 `size`, 위치 `xformOp:translate`, 질량 `physics:mass` |
| Relationship | 다른 Prim이나 속성 경로를 가리키는 연결 | 관절의 `physics:body0`, 재질의 `material:binding` |
| Metadata | 데이터의 해석·구성을 설명하는 부가 정보 | Prim의 `typeName`, Stage의 `metersPerUnit` |

Attribute와 Relationship을 합쳐 **Property**라고 합니다. Relationship에 경로를 기록하는 것만으로 물리 동작이 생기지는 않습니다. 예를 들어 임의의 `tutorial:target` 연결은 학습용 데이터이며, 실제 관절은 관절 스키마와 물리 엔진의 해석이 필요합니다. [Attributes](https://docs.nvidia.com/learn-openusd/latest/stage-setting/properties/attributes.html), [Relationships](https://docs.nvidia.com/learn-openusd/latest/stage-setting/properties/relationships.html)

### Schema: 데이터의 이름과 의미를 정하는 규칙

- **Typed schema**: Prim이 무엇인지를 정합니다. `UsdGeom.Cube.Define(...)`은 `Cube` 타입의 Prim을 작성합니다.
- **Applied API schema**: 기존 Prim에 기능에 필요한 데이터를 추가합니다. `UsdPhysics.RigidBodyAPI.Apply(prim)`은 강체로 해석할 설정을 붙입니다. 타입은 여전히 `Cube`일 수 있습니다.
- 모든 `...API`가 `Apply()` 대상은 아닙니다. `UsdGeom.XformCommonAPI`처럼 기존 데이터를 다루는 편의 API도 있습니다.

스키마가 정한 기본값(fallback)은 파일에 직접 적지 않아도 조회될 수 있습니다. 또한 **`UsdPhysics`는 물리 데이터를 정의하며 물리 엔진을 포함하지 않습니다.** [Schemas](https://docs.nvidia.com/learn-openusd/latest/scene-description-blueprints/schemas.html)

## 4. Xform · 좌표 · 시간

`Xform`은 위치·회전·크기 변환을 담는 Prim입니다. 자식의 좌표는 기본적으로 부모 좌표계에 상대적입니다. 부모가 `(1, 0, 0)`, 자식이 `(0, 0, 0.5)`만큼 이동했다면, 다른 변환이 없을 때 자식의 월드 위치는 `(1, 0, 0.5)`입니다.

회전·스케일이 있으면 단순 덧셈으로 구할 수 없습니다. `UsdGeom.XformCache`로 누적 변환을 조회하세요. 여러 변환의 순서는 `xformOpOrder`에 기록됩니다. `resetXformStack`으로 부모 변환 상속을 끊는 경우도 있습니다. [Xform](https://docs.nvidia.com/learn-openusd/latest/scene-description-blueprints/xform.html)

이 튜토리얼에서는 다음 기준을 명시합니다.

| 설정 | 의미 |
|---|---|
| `metersPerUnit = 1.0` | 길이 값 1을 1 m로 해석 |
| `upAxis = "Z"` | Z축이 위쪽 |
| `timeCodesPerSecond = 24` | 시간 코드 24의 간격이 1초 |

`metersPerUnit`이나 `upAxis`만 바꾼다고 기존 좌표·메시가 자동 변환되지는 않습니다. 다른 단위·축의 자산을 조립할 때는 변환 보정이 필요합니다. `UsdGeom`의 `RotateXYZ` 각도는 **도(degree)**이며, 사용하는 다른 API의 각도 단위도 확인해야 합니다. [Units in OpenUSD](https://docs.nvidia.com/learn-openusd/latest/beyond-basics/units.html), [UsdGeomXformOp](https://openusd.org/release/api/class_usd_geom_xform_op.html)

Isaac Sim 5.1은 자산의 단위·축 보정을 돕는 **Metrics Assembler**를 기본 활성화합니다. 이것은 앱의 확장 기능이며, 일반 `pxr`만 사용하는 예제 01–03에 자동 단위 변환이 있다는 뜻은 아닙니다. [Isaac Sim 5.1: Units in USD](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/omniverse_usd/open_usd.html#units-in-usd)

Attribute의 **time sample**은 특정 시간 코드에 기록한 값입니다. 시간에 따른 위치를 저장하면 애니메이션을 표현할 수 있습니다. `Usd.TimeCode.Default()`는 숫자 시간 `0`과 다르며, time sample 보간과 물리 계산도 별개입니다. 시간 코드를 조회하는 것만으로 물체가 중력에 따라 움직이지는 않습니다. [Time Codes and Time Samples](https://docs.nvidia.com/learn-openusd/latest/stage-setting/timecodes-timesamples.html)

## 5. Composition: 여러 작성 내용을 합치는 규칙

**Opinion**은 어떤 Layer에 작성한 데이터입니다. 같은 Prim의 같은 속성에 여러 opinion이 있으면 합성 규칙에 따라 강한 쪽의 값이 선택됩니다. 파일을 마지막으로 수정한 시간이 기준이 아닙니다. [Composition Arcs and Strength Ordering](https://docs.nvidia.com/learn-openusd/latest/composition-basics/strength-ordering.html)

| 방법 | 언제 쓰나요? | 핵심 차이 |
|---|---|---|
| **Sublayer** | 같은 장면의 배치·물리·실험 수정 분리 | 같은 Prim 경로 공간에 Layer를 겹침 |
| **Reference** | 로봇 자산을 장면의 특정 경로에 배치 | 참조한 Prim 하위 트리를 대상 경로로 가져옴 |
| **Override** | 원본을 유지하며 특정 값 변경 | 별도 Layer 등에 더 강한 opinion을 작성하는 편집 방식 |
| **Variant set** | 그리퍼 종류·색상 등 대안 선택 | 같은 variant set에서 선택한 한 대안을 합성 |
| **Payload** | 무거운 자산을 필요할 때 로드 | reference와 비슷하지만 load/unload 제어 가능 |

Override는 별도의 composition arc 이름이 아닙니다. USDA의 `over`는 해당 경로에 수정 사항을 작성하는 specifier이며, 이것만으로 독립적인 정의(`def`)가 생기는 것은 아닙니다. [Specifiers](https://docs.nvidia.com/learn-openusd/latest/composition-basics/specifiers.html)

기초 실습에서는 다음 두 규칙을 관찰합니다.

1. root Layer 자체의 opinion은 그 sublayer보다 강합니다. 같은 `subLayerPaths` 목록에서는 **앞의 Layer가 더 강합니다**. 따라서 `[overrides.usda, layout.usda]` 순서를 씁니다.
2. 이 예제처럼 대상 Prim에 직접 작성한 local opinion은 reference에서 가져온 값보다 강합니다. 모든 자산 파일을 수정할 필요 없이 특정 배치만 바꿀 수 있습니다.

전체 우선순위는 참조 내부에서도 재귀적으로 적용됩니다. “위 파일이 무조건 이긴다”로 일반화하지 말고, 복잡한 경우 원문의 strength ordering을 확인하세요. [Sublayers](https://docs.nvidia.com/learn-openusd/latest/creating-composition-arcs/sublayers/what-are-sublayers.html), [Strength Ordering](https://docs.nvidia.com/learn-openusd/latest/composition-basics/strength-ordering.html)

`reference` 두 개를 만들었다고 자동으로 scenegraph **instancing**이 된 것은 아닙니다. Instancing은 공유할 하위 구조를 명시해 메모리 등을 절약하는 별도 개념이며, instance 내부 자식의 개별 편집에 제약이 있습니다. [What Is Instancing?](https://docs.nvidia.com/learn-openusd/latest/asset-modularity-instancing/what-is-instancing.html)

## 6. Edit Target과 저장: 어디를 수정했나요?

Stage에서 조회하는 값은 합성 결과지만, `Set()`으로 **작성하는 위치는 현재 Edit Target**입니다. 원본을 보존하려면 수정 Layer를 합성에 포함한 뒤 `Usd.EditContext(stage, layer)` 안에서 편집합니다. Layer를 분리해 놓기만 하고 원본 Layer에 쓰면 비파괴 편집이 되지 않습니다.

| 코드 | 저장하는 것 |
|---|---|
| `stage.GetRootLayer().Save()` | root Layer 자체 |
| `layer.Save()` | 지정한 Layer 자체 |
| `stage.Save()` | Stage에 기여하는 수정된 Layer들. session Layer 계열 제외 |
| `stage.Flatten().Export(path)` | 현재 합성된 장면을 한 Layer로 내보냄 |

Session Layer는 임시 선택·수정 등에 쓰는 Layer입니다. root Layer 저장만으로 session이나 수정 sublayer까지 저장되지는 않습니다. 익명 Layer는 별도 파일로 내보내고 연결을 정리해야 지속적으로 사용할 수 있습니다.

**Flatten은 편집 구조를 보존하는 저장 방식이 아닙니다.** 선택된 variant와 로드된 payload 등 현재 합성 내용을 펼치므로 원래의 자산 연결·대안 선택 구조가 사라집니다. 텍스처 같은 외부 파일까지 모두 포장하는 작업도 아닙니다. 배포용 묶음과 단일 합성 결과를 구분하세요. [UsdStage API: Save, Edit Target, Flatten](https://openusd.org/release/api/class_usd_stage.html)

파일 경로와 Prim 경로도 구분해야 합니다. `./robot.usda`는 자산 파일 식별자이고 `/World/Robot`은 Stage 안의 Prim 경로입니다. 이 실습의 파일 상대경로는 **그 경로를 작성한 Layer 파일의 위치**를 기준으로 해석됩니다. scene 파일만 옮기면 참조가 끊길 수 있으므로 출력 폴더를 통째로 옮기세요. [References](https://docs.nvidia.com/learn-openusd/latest/creating-composition-arcs/references-payloads/what-are-references.html)

## 7. 확장자가 다른 이유

| 확장자 | 용도 |
|---|---|
| `.usda` | 사람이 읽을 수 있는 텍스트. 실습과 diff 확인에 사용 |
| `.usdc` | 효율적인 바이너리 Crate 형식. 큰 메시 등에 사용 |
| `.usd` | 내부 데이터는 텍스트 또는 바이너리일 수 있음 |
| `.usdz` | USD와 텍스처 등의 자산을 담는 제약이 있는 비압축 ZIP 패키지 |

확장자가 물리 지원 여부를 결정하지는 않습니다. 이 실습은 결과 파일을 텍스트 편집기로 읽을 수 있도록 `.usda`를 사용합니다. [OpenUSD File Formats](https://docs.nvidia.com/learn-openusd/latest/stage-setting/usd-file-formats.html)

## 출처 및 더 읽기

NVIDIA 공식 설명을 바탕으로 실습에 필요한 개념만 재구성했습니다. 아래에는 생략한 심화 주제도 포함합니다.

- [NVIDIA Learn OpenUSD 전체 과정](https://docs.nvidia.com/learn-openusd/latest/index.html): 개념에서 자산 제작·변환·검증까지.
- [Stage](https://docs.nvidia.com/learn-openusd/latest/stage-setting/stage.html), [Prims](https://docs.nvidia.com/learn-openusd/latest/stage-setting/prims.html), [Layers](https://docs.nvidia.com/learn-openusd/latest/composition-basics/layers.html): 세 핵심 개념의 원문.
- [Properties](https://docs.nvidia.com/learn-openusd/latest/stage-setting/properties/index.html), [Schemas](https://docs.nvidia.com/learn-openusd/latest/scene-description-blueprints/schemas.html): 속성과 스키마의 데이터 모델.
- [Composition Arcs and Strength Ordering](https://docs.nvidia.com/learn-openusd/latest/composition-basics/strength-ordering.html): LIVRPS/LIVERPS와 상세한 합성 우선순위. 최신 학습 문서는 relocates를 포함한 표기도 다룹니다.
- [Isaac Sim 5.1 OpenUSD Fundamentals](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/omniverse_usd/open_usd.html): Isaac Sim 관점의 기초 개념 정리.
- [NVIDIA Learn OpenUSD: Asset Modularity and Instancing](https://docs.nvidia.com/learn-openusd/latest/asset-modularity-instancing/index.html): 인스턴스 생성·편집 제약.
- [OpenUSD 공식 용어집](https://openusd.org/release/glossary.html), [UsdStage API](https://openusd.org/release/api/class_usd_stage.html): 엄밀한 정의와 저장·합성 API.
