# Fuel model 추가하기

> **난이도:** 초급  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** 센서

## 학습 목표

- Gazebo Fuel의 model URI가 가리키는 대상을 이해합니다.
- Fuel model을 SDF world의 `<include>`로 추가합니다.
- 다운로드 cache와 `GZ_SIM_RESOURCE_PATH`의 역할을 구분합니다.

## 배경 지식

Gazebo Fuel은 Gazebo용 model과 world를 제공하는 온라인 자산 저장소입니다. world에 URI를 넣으면 Gazebo는 필요한 자산을 내려받아 Fuel cache에 보관하고, 다음 실행에서는 cache를 재사용합니다.

이 장에서는 OpenRobotics의 `Coke` model을 사용합니다. 다음 URI는 사용자 계정, 자산 종류, model 이름을 차례로 나타냅니다.

```text
https://fuel.gazebosim.org/1.0/OpenRobotics/models/Coke
```

처음 실행할 때는 네트워크 연결이 필요합니다. 이 저장소에는 내려받은 Fuel 자산을 넣지 않습니다. 모델의 라이선스, 크기, 버전은 Fuel 페이지에서 확인한 뒤 필요한 자산만 사용합니다.

<figure class="course-figure" markdown="span">
  ![Fuel HTTPS URI와 cache 및 로컬 resource path가 월드 모델로 해석되는 흐름](../assets/beginner/fuel-resource-flow.svg)
  <figcaption>그림 5. Fuel HTTPS URI는 download cache를 거치고, <code>model://</code> URI는 resource path를 검색합니다. 두 경로의 역할을 섞지 않습니다.</figcaption>
</figure>

## 예제 파일

Fuel model을 include하는 world는 다음 파일입니다.

`examples/gazebo/worlds/fuel-world.sdf`

이 장의 headless 검증 스크립트는 임시 Fuel cache에 model을 내려받고, 실행 중인 world에서 model 이름을 확인합니다.

`scripts/check_fuel_world.sh`

## 실습

### 1. Fuel URI를 world에 포함하기

`fuel-world.sdf`의 `<include>`는 온라인 model을 `fuel_coke`라는 인스턴스 이름으로 world에 배치합니다.

```xml
<include>
  <name>fuel_coke</name>
  <pose>0 0 0 0 0 0</pose>
  <static>true</static>
  <uri>https://fuel.gazebosim.org/1.0/OpenRobotics/models/Coke</uri>
</include>
```

`<name>`은 world 안에서 사용하는 인스턴스 이름입니다. 같은 Fuel model을 여러 번 배치할 때는 각 `<include>`에 다른 이름과 pose를 지정합니다. `<static>true</static>`는 이 예제의 can이 중력 때문에 움직이지 않게 합니다.

### 2. 다운로드와 cache 확인하기

model을 명시적으로 내려받으려면 다음 명령을 사용합니다.

```bash
gz fuel download -u 'https://fuel.gazebosim.org/1.0/OpenRobotics/models/Coke'
```

기본 cache 위치는 `GZ_FUEL_CACHE_PATH`가 설정되지 않았을 때 `~/.gz/fuel`입니다. 위치를 바꾸려면 원하는 cache 디렉터리를 환경 변수로 지정합니다.

```bash
export GZ_FUEL_CACHE_PATH="$PWD/.fuel-cache"
gz fuel download -u 'https://fuel.gazebosim.org/1.0/OpenRobotics/models/Coke'
```

이 cache는 로컬 실행용이므로 Git에 추가하지 않습니다. 이 저장소의 검증 스크립트도 임시 cache를 사용하고 종료할 때 제거합니다.

다운로드가 실제로 끝났는지는 성공 문구만 보지 말고 cache 아래의 `model.config`와 `model.sdf`를 확인합니다.

```bash
find "$GZ_FUEL_CACHE_PATH" -type f \( -name model.config -o -name model.sdf \) -print
```

### 3. 로컬 model resource path 이해하기

Fuel에서 model을 직접 내려받아 별도 디렉터리에 보관했다면, `model://` URI를 찾을 수 있도록 부모 디렉터리를 `GZ_SIM_RESOURCE_PATH`에 추가합니다.

```bash
export GZ_SIM_RESOURCE_PATH="$PWD/local_models${GZ_SIM_RESOURCE_PATH:+:${GZ_SIM_RESOURCE_PATH}}"
```

예를 들어 `local_models/Coke/model.config`와 `local_models/Coke/model.sdf`가 있다면 SDF에서 `model://Coke`를 사용할 수 있습니다. `GZ_FUEL_CACHE_PATH`는 Fuel downloader의 cache이고, `GZ_SIM_RESOURCE_PATH`는 `model://` 같은 로컬 resource URI 탐색 경로라는 차이가 있습니다.

## 실행

저장소 루트에서 다음 명령을 실행합니다.

```bash
./scripts/check_fuel_world.sh
```

스크립트는 임시 cache에 Fuel model을 내려받은 뒤 `fuel-world.sdf`를 headless로 시작합니다. 실행 중인 world에 `fuel_coke`가 있으면 다음과 같은 model 목록과 완료 메시지가 출력됩니다.

```text
Requesting state for world [fuel_world]...

Available models:
    - ground
    - fuel_coke
Fuel model include verified.
```

GUI로 world를 열려면 다음을 실행합니다. 처음에는 모델 다운로드 때문에 시작 시간이 더 걸릴 수 있습니다.

```bash
gz sim examples/gazebo/worlds/fuel-world.sdf
```

## 결과 확인

`gz model --list`에 `fuel_coke`가 보이고 cache에 `model.config`가 있으면 두 관찰값이 이어집니다. URI가 자산을 cache에 내려받았고, Gazebo가 그 자산을 해석해 world instance를 만들었다는 뜻입니다. 이 model은 이 예제의 SDF에 복사된 것이 아니라 Fuel cache에서 찾아집니다.

```text
Fuel URI → GZ_FUEL_CACHE_PATH/model.config → SDF 해석 → world의 fuel_coke
model://Coke → GZ_SIM_RESOURCE_PATH 검색 → 로컬 model.sdf
```

## 자주 발생하는 문제

### 다운로드가 실패합니다

네트워크 연결과 Fuel URI의 owner·model 이름을 확인합니다. `gz fuel download -u <URI>`를 먼저 실행하면 URI와 cache 문제를 world 실행과 분리해 확인할 수 있습니다.

### model URI를 찾지 못합니다

`model://...`를 사용한다면 `GZ_SIM_RESOURCE_PATH`가 model 디렉터리의 부모를 가리키는지 확인합니다. Fuel의 HTTPS URI와 로컬 `model://` URI를 같은 용도로 혼용하지 않습니다.

### cache를 Git에 넣어도 되나요?

넣지 않습니다. `.gz/fuel` 또는 별도 Fuel cache는 사용자 환경에 속하고, model은 URI와 라이선스 정보를 통해 다시 내려받을 수 있어야 합니다.

## 정리

Fuel URI는 외부 model을 world에 포함하는 간단한 방법이고, cache는 반복 다운로드를 줄입니다. 다음 장에서는 Gazebo Transport topic을 ROS 2 topic으로 연결하는 `ros_gz_bridge`를 다룹니다.

[이전: 센서](08-sensors.md) · [다음: ROS 2와 연결](10-ros-gz-bridge.md)
