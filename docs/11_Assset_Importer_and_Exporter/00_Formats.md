# Formats
> **출처**: [Formats](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/importer_exporter/formats.html)  
  
Omniverse에서 사용하는 표준 형식은 **Scene의 경우 USD, Material의 경우 MDL**이다. 외부 어플리케이션에서 가져온 콘텐츠를 Omniverse에서 사용하려면 해당 콘텐츠를 Omniverse에서 사용할 수 있는 형식으로 변환해야 한다. 다만 사용자 편의를 위해서 Omniverse에서는 외부 콘텐츠를 사용하고 관리하기 위해 다양한 방법을 제공한다.

## Asset Converter
Omniverse의 App에는 [**Asset Converter Extension**](https://docs.omniverse.nvidia.com/extensions/latest/ext_asset-converter.html)이 기본적으로 포함되어있으며, 이를 사용하면 Asset Converter Service를 통해서 모델을 USD 형식으로 변환할 수 있다. 아래는 USD로 변환할 수 있는 주요 포맷들이다.
| Format | Name | Description |
| -- | -- | -- |
| `.fbx` | Autodesk FBX Interchange File | 오토데스트 Filmbox 형식으로 저장되는 일반적인 3D 모델 파일 |
| `.obj` | Object File Format | 블렌더 등에서 널리 사용되는 3D 모델 형식 |
| `.gltf` | GL Transmission Format File | 일반적인 3D Scene description 형식 |

## Materials
엔비디아에서는 Material 할당과 Parameter를 표현하기 위해서 USD에 커스텀 Schema를 새롭게 개발했다. Omniverse에서는 이러한 Material 표현에 사용되는 특수한 USD 데이터를 `.MDL` 확장자를 사용하도록 설계되어있다. 이는 해당 Material이 엔비디아의 오픈소스 **MDL (Material Definition Language)**를 통해 표현된다는 것을 의미한다.