# Isaac Sim GUI와 핵심 인터페이스

Isaac Sim의 GUI는 단순한 3D 뷰어가 아니다. **USD Stage를 편집하는 저작 도구**, **PhysX 시뮬레이션 제어기**, **확장 기반 개발 환경**, **OmniGraph 시각 프로그래밍 도구**가 한 창에 모여 있다. 이 장에서는 각 패널이 어떤 데이터를 보여 주는지 구분하다.

## 화면을 읽는 기본 지도

기본 레이아웃은 대략 다음 역할로 나뉘다.

| 영역 | 무엇을 보여 주는가 | 주된 작업 |
|---|---|---|
| Menu Bar | 앱과 확장이 등록한 명령 | 생성, 창 열기, 로봇·센서 도구 실행 |
| Viewport | 현재 Stage의 렌더링 결과 | 선택, 카메라 이동, Transform 조작 |
| Main Toolbar | 편집 도구와 Timeline 제어 | 이동·회전·크기, Play·Pause·Stop |
| Stage | USD prim 계층 | 경로·부모자식·활성/가시성 구조 확인 |
| Property | 선택한 prim의 속성·적용 API | Transform, 물리, 재질, 센서 파라미터 수정 |
| Content Browser | 로컬·온라인 에셋과 USD 파일 | 검색, 참조·payload로 Stage에 추가 |
| Layer | USD 레이어 스택과 편집 대상 | root/sublayer 선택, 비파괴 override 관리 |
| Timeline | 시간과 재생 상태 | 시뮬레이션 시작, 일시정지, 정지 |
| Console | Kit·확장의 로그 | 오류, 경고, Python 출력 확인 |
| Extensions | 기능 모듈 관리 | 검색, Enable, Autoload, 의존성 확인 |
| Action Graph | OmniGraph 노드 그래프 | 센서·ROS·제어·이벤트 데이터 흐름 연결 |

기본 창이 보이지 않으면 `Window` 메뉴에서 이름을 찾아 다시 열다. Content Browser는 보통 `Window > Browsers > Content`, Action Graph는 `Window > Graph Editors > Action Graph`, Extensions는 `Window > Extensions`에 있다. 작업공간 배치가 심하게 꼬였으면 앱을 종료하고 `./isaac-sim.sh --reset-user`로 기본 설정을 무시해 시작하다.

## Viewport: 장면을 보는 창

### 선택과 카메라 이동

- 왼쪽 클릭으로 prim을 선택하다.
- 선택 후 `F`를 누르면 그 prim에 카메라 초점을 맞추다.
- 선택을 해제한 뒤 `F`를 누르면 전체 장면을 프레이밍하다.
- 마우스 가운데 버튼을 누른 채 움직이면 팬하다.
- 마우스 오른쪽 버튼을 누른 채 움직이면 카메라 방향을 바꾸다.
- 오른쪽 버튼을 누른 채 `W/A/S/D`, `Q/E`를 사용하면 자유 비행하다.
- 휠로 확대·축소하다.
- `Esc`로 선택을 해제하다.

뷰포트 상단의 카메라 메뉴에서 Perspective와 Stage의 Camera prim 사이를 전환하다. 눈 모양 표시 메뉴에서는 카메라 아이콘, 조명, 물리 collider 같은 보조 표시를 켜고 끌 수 있다. 렌더링되지 않는 collider를 확인하려면 `Show By Type > Physics > Colliders > All` 계열 항목을 사용하다.

### Transform 기즈모

| 키 | 도구 | 주의점 |
|---|---|---|
| `W` | 이동 | 화살표는 한 축, 색 사각형은 두 축 이동 |
| `E` | 회전 | 로컬/월드 좌표 모드를 확인하다 |
| `R` | 크기 | 로봇 링크를 임의 스케일하면 물리와 관성이 망가질 수 있다 |

정확한 값은 마우스로 맞추지 말고 Property의 Transform 숫자 필드에 입력하다. Stage의 단위와 up axis를 확인하지 않은 채 좌표를 해석하지 않다. Isaac Sim 로봇 워크플로는 일반적으로 미터와 Z-up을 사용하다.

## Stage: USD prim 계층

Stage 패널의 각 행은 파일이 아니라 **prim**이다. 예를 들어 다음 경로는 부모자식 관계를 나타내다.

- `/World`
  - `/World/PhysicsScene`
  - `/World/GroundPlane`
  - `/World/Robot`
    - `/World/Robot/base_link`
    - `/World/Robot/camera_link`

`/World/Robot/camera_link`는 센서 노드나 Python API에서 그대로 사용하는 안정적인 주소이다. 이름을 바꾸면 그 경로를 참조하던 Action Graph, ROS publisher, 스크립트가 끊길 수 있다.

Stage에서 익혀야 할 작업은 다음과 같다.

- 우클릭 `Create`로 Xform, Scope, Mesh 등의 prim을 만들다.
- 드래그로 부모를 바꾸다. 부모 Transform이 자식 좌표에 영향을 주므로 결과를 확인하다.
- 눈 아이콘은 가시성을 바꾸지만, 물리 비활성화와 같은 의미가 아니다.
- 참조로 불러온 에셋의 내부 속성이 잠긴 것처럼 보이면 해당 레이어가 읽기 전용이거나 현재 편집 대상이 아닌지 확인하다.
- 같은 이름의 prim을 만들면 자동으로 경로가 바뀔 수 있으므로 최종 경로를 확인하다.

### 선택한 것과 물리가 움직이는 것이 다를 수 있다

Rigid Body API가 부모 Xform에 있고 시각 Mesh가 자식이라면, 시뮬레이션 중 부모 Xform의 좌표가 갱신되다. 자식 Mesh만 선택하고 Transform 값이 변하지 않는다고 물리가 멈췄다고 판단하지 않다. Stage를 위로 올라가 Rigid Body API가 적용된 prim을 선택하다.

## Property: 선택한 prim의 사실표

Property 패널은 선택한 prim에 저작된 USD 속성과 적용된 API를 보여 주다. 자주 보는 섹션은 다음과 같다.

- `Transform`: Translate, Orient/Rotate, Scale
- `Physics`: Rigid Body, Collider, Mass, Joint, Articulation 설정
- `Material and Shader`: 재질 바인딩, 색과 표면 파라미터
- `Camera`: focal length, clipping range 등
- 센서별 속성: 주기, 범위, 해상도, 노이즈 등

위쪽의 `+ Add`를 이용해 `Physics > Rigid Body`, `Physics > Collider`, `Physics > Articulation Root` 같은 API를 적용하다. 메뉴에서 API를 추가하는 행위는 새 Mesh를 만드는 것과 다르다. 하나의 prim에 여러 API가 함께 적용될 수 있다.

속성 필드 옆에 파란색·강조 표시나 작은 상태 아이콘이 보이면 해당 값이 현재 레이어에 override되었거나 연결·애니메이션의 영향을 받는지 살피다. 정확한 표시는 테마와 속성 종류에 따라 다르므로 툴팁을 확인하다.

## Content Browser: 에셋을 장면에 넣는 방법

`Window > Browsers > Content`를 열다. Isaac Sim 에셋 루트에서 로봇, 환경, 센서와 샘플 USD를 탐색하다.

에셋을 사용하는 방식은 결과가 다르다.

| 동작 | 결과 | 언제 쓰는가 |
|---|---|---|
| 파일을 더블클릭해 Open | 현재 Stage를 그 파일로 교체 | 원본 에셋 자체를 열어 검사할 때 |
| Stage/Viewport로 드래그 | 보통 reference 또는 payload로 현재 Stage에 추가 | 환경에 로봇·소품을 배치할 때 |
| Load as Reference | 외부 USD를 참조하는 prim 생성 | 원본과 인스턴스 구성을 분리할 때 |

원본 로봇 USD를 실수로 수정하지 않도록 학습 장면에는 reference로 배치하고, override는 별도 root layer 또는 sublayer에 저장하는 습관을 들이다. 온라인 에셋은 첫 로드가 느릴 수 있다. 로그에서 `Isaac Sim assets found`와 에셋 루트 경로를 확인하다.

## Layer: 비파괴 편집의 핵심

Stage는 여러 USD Layer의 합성 결과이다.

- **Root Layer**는 현재 저장하는 Stage의 시작점이다.
- **Sublayer**는 root가 합성하는 다른 레이어이다.
- reference/payload는 prim 단위로 외부 USD를 합성하다.
- **Edit Target**은 새 의견(opinion)을 어느 레이어에 기록할지 정하다.

예를 들어 제조사가 제공한 `robot.usd`는 그대로 두고 `robot_tuning.usda`에 joint gain과 센서 위치 override만 저장할 수 있다. Layer 패널에서 현재 Edit Target을 확인하지 않으면 수정이 예상과 다른 파일에 기록될 수 있다.

처음에는 다음 원칙을 지키다.

1. 원본 에셋 레이어는 읽기 전용으로 취급하다.
2. 프로젝트 Stage 또는 명시적인 tuning sublayer를 편집 대상으로 정하다.
3. 저장 전에 Layer 패널에 익명 레이어(`anonymousLayer...`)가 남았는지 확인하다.
4. 파일을 이동할 때 상대 reference 경로가 깨지지 않는지 다시 열어 검증하다.

## Timeline과 Physics

Timeline의 세 상태를 구분하다.

| 상태 | 의미 | 사용 예 |
|---|---|---|
| Play | 시간과 물리 스텝이 진행 | 로봇 제어, 센서, Action Graph 실행 |
| Pause | 현재 시간에서 일시정지 | 중간 상태 검사 |
| Stop | 재생 세션을 종료하고 초기 상태로 복귀 | 구조·물리 속성 편집, 저장 전 정리 |

`Space`는 Play/Pause 단축키이다. 구조를 바꾸거나 physics API를 추가할 때는 Stop 상태에서 작업하는 편이 예측 가능하다. Play 중 Property에 보이는 시뮬레이션 값과 USD에 실제 저장되는 authored 값은 같지 않을 수 있다.

Physics Scene이 없으면 기본 60 physics steps/s가 사용되다. 명시적으로 만들려면 `Create > Physics > Simulation Scene`을 선택하고 Property에서 `Simulation Steps per Second`를 확인하다. 렌더 프레임률과 물리 스텝률은 별개이다. 예를 들어 물리 120 Hz와 렌더 30 Hz라면 한 렌더 프레임 사이에 여러 물리 스텝이 실행되다.

물리 디버깅은 다음 순서로 하다.

1. Rigid Body가 움직여야 할 prim에 적용되었는지 확인하다.
2. 접촉할 Mesh에 Collider가 있는지 확인하다.
3. Collider 시각화를 켜 실제 근사 형상을 확인하다.
4. 질량, 관성, joint limit과 drive gain의 단위를 확인하다.
5. 빠른 물체가 얇은 벽을 통과하면 timestep과 CCD를 검토하다.

## Console: 첫 번째 디버거

Console에는 Kit, RTX, PhysX, USD, 확장과 Python 출력이 모이다. 로그 수준을 필터링할 수 있지만, 학습 중에는 오류를 무조건 숨기지 않다.

진단할 때는 다음 정보를 함께 기록하다.

- 오류의 첫 줄과 그 직전 경고
- 확장 ID
- prim 경로
- 실행 방식(워크스테이션/컨테이너/standalone)
- Isaac Sim 5.1.0과 드라이버 버전
- 재현 직전의 메뉴 또는 코드

`omni.usd LoadModule`처럼 5.1 알려진 이슈에서 무시 가능하다고 명시된 로그도 있지만, 문구가 비슷하다는 이유만으로 모든 오류를 무시하지 않다.

## Extensions: 기능은 모듈로 제공하다

`Window > Extensions`에서 기능 이름이나 확장 ID를 검색하다.

- **Enable**은 현재 세션에서 확장을 켜다.
- **Autoload**는 다음 실행에도 자동으로 불러오도록 사용자 설정에 기록하다.
- 의존 확장은 함께 활성화될 수 있다.
- 검색 결과가 없으면 검색창의 `@feature` 같은 필터를 제거해 보다.

초보자가 자주 찾는 확장은 ROS 2 Bridge, URDF Importer, Physics 도구, Script Editor 관련 기능이다. 필요하지 않은 확장을 한꺼번에 Autoload하면 시작 시간과 메모리가 늘고 충돌 원인 추적이 어려워지므로 프로젝트에 필요한 것만 켜다.

## Action Graph: 이벤트와 데이터 흐름

OmniGraph는 Omniverse의 시각 프로그래밍·계산 프레임워크이고, Action Graph는 실행 흐름을 구성하는 편집기이다. Isaac Sim에서는 ROS 2, 센서 읽기, 컨트롤러, Replicator와 외부 입출력에 널리 사용하다.

노드 연결은 두 종류로 읽다.

- **Execution 포트**는 언제 실행할지를 전달하다. 보통 `execOut/Tick -> execIn`으로 연결하다.
- **Data 포트**는 숫자, 토큰, prim target, 배열과 메시지 데이터를 전달하다.

### 1분 실습: 매 프레임 Console에 출력

1. `Window > Graph Editors > Action Graph`를 열다.
2. **New Action Graph**를 선택하다.
3. `On Playback Tick`과 `Print Text` 노드를 추가하다.
4. Playback Tick의 `Tick` 실행 출력을 Print Text의 `Exec In`에 연결하다.
5. Print Text의 `Text`에 `Hello Isaac Sim`을 입력하다.
6. Timeline에서 Play를 누르고 Console을 확인하다.
7. 로그가 너무 많이 쌓이기 전에 Stop하다.

이 그래프는 Stage의 prim으로 저장되다. 같은 Stage에서 생성 스크립트를 여러 번 실행하면 중복 그래프가 생길 수 있으므로 `/World` 아래 경로를 확인하다.

## 자주 쓰는 단축키

| 단축키 | 동작 |
|---|---|
| `W`, `E`, `R` | 이동, 회전, 크기 기즈모 |
| `F` | 선택 항목 또는 전체 프레이밍 |
| `Esc` | 선택 해제 |
| `Ctrl+S`, `Ctrl+O` | 저장, 열기 |
| `Ctrl+D` | 선택 prim 복제 |
| `H` | 선택 prim 가시성 전환 |
| `Delete` | 선택 prim 삭제 |
| `Space` | Play/Pause |
| `F10` | 스크린샷 |
| `F11` | 전체 화면 |

## GUI 학습 체크포인트

- [ ] Viewport 선택과 Stage prim 경로가 서로 연결됨을 확인했다.
- [ ] Property에서 Transform과 Physics API를 구분했다.
- [ ] Content Browser의 Open과 Reference 추가 차이를 설명할 수 있다.
- [ ] Layer Edit Target을 확인하고 원본 에셋을 비파괴 편집할 수 있다.
- [ ] Play/Pause/Stop과 렌더·물리 스텝의 차이를 이해했다.
- [ ] Console에서 오류의 확장 ID와 prim 경로를 찾을 수 있다.
- [ ] Extensions와 Action Graph의 기본 역할을 이해했다.

## 출처

- [Isaac Sim 5.1.0 — User Interface Reference](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/gui/reference_user_interface.html)
- [Isaac Sim 5.1.0 — Keyboard Shortcuts Reference](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/gui/reference_keyboard_shortcuts.html)
- [Isaac Sim 5.1.0 — Isaac Sim Basic Usage Tutorial](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/introduction/quickstart_isaacsim.html)
- [Isaac Sim 5.1.0 — Physics Simulation Fundamentals](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/physics/simulation_fundamentals.html)
- [Isaac Sim 5.1.0 — Omnigraph](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/omnigraph/index.html)
- [Isaac Sim 5.1.0 — Isaac Sim Omnigraph Tutorial](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/omnigraph/omnigraph_tutorial.html)
- [Isaac Sim 5.1.0 — Content Browser](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/utilities/content_browser.html)
