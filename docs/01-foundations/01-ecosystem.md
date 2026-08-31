# NVIDIA 로보틱스 시뮬레이션 생태계 이해하기

이 장에서는 Isaac Sim을 둘러싼 이름을 정확히 구분한다. 처음에는 Omniverse, Kit, OpenUSD, Nucleus, Isaac Sim, Isaac Lab이 하나의 제품처럼 보이지만 실제로는 서로 다른 계층이다. 이 관계를 이해하면 설치 오류, USD 오류, 물리 오류, ROS 오류 중 어디를 먼저 조사해야 하는지 판단할 수 있다.

> 이 문서는 Isaac Sim 5.1.0에 맞추어 작성한다. NVIDIA의 5.1.0 문서에는 현재 지원 종료 버전이라는 경고가 표시되므로, 예제와 API를 다른 버전 문서와 섞지 않는 것이 중요하다.

## 한 문장으로 구분하기

| 이름 | 정체 | 이 튜토리얼에서 맡는 역할 |
|---|---|---|
| OpenUSD | 계층형 3D 장면을 표현하고 조합하는 오픈 소스 데이터 모델과 런타임 | 로봇, 환경, 재질, 물리 속성, 센서 배치를 저장하고 조합한다 |
| pxr | OpenUSD의 C++ 네임스페이스이자 Python 바인딩의 최상위 패키지 이름 | Python/C++에서 Stage와 Prim을 읽고 쓴다 |
| NVIDIA Omniverse | OpenUSD 데이터 교환, 앱·서비스 개발, 배포를 위한 NVIDIA 플랫폼 | Isaac Sim이 올라가는 공통 3D 플랫폼과 기술 묶음을 제공한다 |
| Omniverse Kit SDK | 확장 기능을 조립해 OpenUSD 앱과 서비스를 만드는 SDK | Isaac Sim의 창, 메뉴, 확장, Python 런타임, RTX 뷰포트를 구성한다 |
| Nucleus | OpenUSD 자산을 여러 도구와 사용자가 공유하는 서버·협업 엔진 | 팀 자산 저장소와 단일 기준 원본을 제공한다. 로컬 실습에는 필수가 아니다 |
| Isaac Sim | Kit 기반의 로보틱스 시뮬레이션 애플리케이션 | PhysX 물리, RTX 렌더링 센서, 로봇 제어, 합성 데이터, ROS 2 연동을 제공한다 |
| Isaac Lab | Isaac Sim 위에서 동작하는 오픈 소스 로봇 학습 프레임워크 | 병렬 환경, 강화학습, 모방학습, 모션 플래닝 연구 흐름을 구조화한다 |
| ROS 2 | 프로세스와 장치 사이의 메시지·서비스·액션 미들웨어 | 실제 로봇용 노드와 Isaac Sim 사이에서 토픽, TF, Clock, 명령을 교환한다 |
| Isaac ROS | ROS 2용 NVIDIA 가속 패키지 모음 | GPU 가속 인지·매핑 파이프라인을 구성한다. Isaac Sim과 같은 제품은 아니다 |

핵심은 다음과 같다.

- OpenUSD는 파일 확장자 하나가 아니라 장면 데이터 모델과 조합 시스템이다.
- Omniverse는 시뮬레이터 이름이 아니라 OpenUSD 기반 기술 플랫폼이다.
- Kit는 그 플랫폼으로 애플리케이션을 만드는 SDK이며 Isaac Sim은 Kit 애플리케이션이다.
- Isaac Lab은 시뮬레이터가 아니라 Isaac Sim을 이용하는 로봇 학습 프레임워크다.
- ROS 2는 장면을 저장하지 않는다. 실행 중인 Isaac Sim과 외부 로봇 소프트웨어를 연결한다.

## 계층 구조로 보기

~~~text
사용자 애플리케이션
  ├─ ROS 2 Jazzy 노드, Nav2, MoveIt 2, 자체 제어기
  └─ Isaac Lab의 학습·평가 스크립트
                 │
          ROS 2 Bridge / Python API
                 │
Isaac Sim 5.1
  ├─ 로봇·센서·Replicator·OmniGraph 확장
  ├─ PhysX 물리
  └─ RTX 렌더링
                 │
Omniverse Kit SDK
  ├─ Extension과 Plugin 시스템
  ├─ omni.ui, Script Editor, Viewport
  └─ omni.usd와 Omniverse Client
                 │
OpenUSD
  ├─ Stage, Layer, Prim, Schema, Composition
  └─ pxr C++/Python API
                 │
로컬 파일 시스템 또는 선택적인 Nucleus 서버
~~~

이 그림은 소프트웨어 의존 관계를 단순화한 것이다. 예를 들어 PhysX 스키마는 USD Prim에 물리 의미를 기록하고, 실행 중에는 PhysX 엔진이 이를 해석한다. RTX 센서는 USD로 배치한 센서 Prim과 장면을 읽어 GPU에서 측정값을 계산한다.

## OpenUSD와 pxr

OpenUSD는 Pixar가 공개한 Universal Scene Description 프로젝트다. 정적 값과 시간 샘플 값을 계층적으로 표현하고, 여러 파일과 작업자의 수정 사항을 비파괴적으로 합성하는 데 초점을 둔다. 다음과 같은 데이터를 하나의 Stage에서 함께 다룰 수 있다.

- Xform, Mesh, Camera, Light와 같은 장면 객체
- 재질과 셰이더 연결
- 애니메이션과 시간 샘플
- 강체, 충돌체, Joint 같은 UsdPhysics 데이터
- PhysX와 Isaac Sim이 추가한 API Schema 및 속성
- 다른 USD 자산에 대한 Reference와 지연 로딩용 Payload
- 로봇 외형이나 LOD를 선택하는 Variant

Python에서 다음처럼 import하는 pxr은 별도 경쟁 라이브러리가 아니다. OpenUSD가 제공하는 Python 바인딩 패키지다.

~~~python
from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics

stage = Usd.Stage.CreateNew("hello.usda")
world = UsdGeom.Xform.Define(stage, Sdf.Path("/World"))
cube = UsdGeom.Cube.Define(stage, Sdf.Path("/World/Cube"))
cube.CreateSizeAttr(0.2)
cube.AddTranslateOp().Set(Gf.Vec3d(0.0, 0.0, 0.5))
UsdPhysics.CollisionAPI.Apply(cube.GetPrim())
stage.GetRootLayer().Save()
~~~

OpenUSD는 일반적인 장면 의미를 정의하고, Isaac Sim은 그 위에 로보틱스 실행 의미와 도구를 더한다. 따라서 순수 OpenUSD 프로그램은 USD 파일을 읽을 수 있어도 NVIDIA 전용 PhysX Schema나 MDL 재질을 모두 실행·표시하지 못할 수 있다.

## Omniverse 플랫폼

Omniverse는 하나의 실행 파일이나 클라우드 서비스만을 뜻하지 않는다. NVIDIA의 현재 개발자 문서는 플랫폼 기능을 크게 다음 세 범주로 구분한다.

1. OpenUSD 데이터를 교환·저작·집계한다.
2. OpenUSD 기반 애플리케이션과 서비스를 만든다.
3. 만든 애플리케이션과 서비스를 배포한다.

Isaac Sim 사용자가 자주 만나는 Omniverse 구성 요소는 다음과 같다.

### Kit SDK

Kit는 Python 또는 C++ 확장을 조립해 OpenUSD 애플리케이션을 만드는 SDK다. Isaac Sim의 메뉴, 패널, 뷰포트, Extension Manager, Script Editor는 Kit의 기능이다. Kit는 OpenUSD/Hydra, RTX 렌더러, Carbonite 플러그인 시스템, omni.ui, Python 런타임을 함께 제공한다.

따라서 다음 코드는 OpenUSD API만 사용하는 첫 번째 형태와, 실행 중인 Kit 애플리케이션의 현재 Stage를 얻는 두 번째 형태로 나뉜다.

~~~python
# 순수 OpenUSD: 파일에서 별도 Stage를 연다.
from pxr import Usd
stage = Usd.Stage.Open("robot.usd")

# Isaac Sim Script Editor: 현재 GUI가 표시하는 Stage를 얻는다.
import omni.usd
stage = omni.usd.get_context().get_stage()
~~~

두 번째 코드는 Kit의 상태, 선택, 이벤트 루프와 연결된다. 순수 OpenUSD 스크립트에서는 omni 모듈을 사용할 수 없다.

### Extension과 Plugin

Kit Extension은 의존성과 버전을 가진 애플리케이션 모듈이다. 실행 중 활성화하거나 비활성화할 수 있으며 Python, C++ 또는 둘의 조합으로 작성한다. 예를 들면 다음과 같다.

- `isaacsim.asset.importer.urdf`: URDF를 USD 로봇 자산으로 가져온다.
- `isaacsim.asset.importer.mjcf`: MJCF를 USD 로봇 자산으로 가져온다.
- `isaacsim.ros2.bridge`: ROS 2 메시지와 OmniGraph 노드를 제공한다.
- `isaacsim.sensors.rtx`: RTX LiDAR·Radar 기능을 제공한다.

Carbonite Plugin은 그보다 낮은 수준의 네이티브 공유 라이브러리다. 초보자는 Extension부터 다루면 충분하다.

### Nucleus

Nucleus는 OpenUSD 데이터의 실시간 교환과 협업을 위한 서버·데이터베이스 엔진이다. 여러 사용자가 DCC 도구와 Omniverse 애플리케이션에서 같은 자산을 공유할 때 단일 기준 원본 역할을 한다.

Nucleus와 USD를 혼동하지 않아야 한다.

- USD는 데이터 모델과 파일·런타임이다.
- Nucleus는 USD와 관련 자산을 저장하고 공유하는 서버다.
- 로컬 경로의 USD만으로도 Isaac Sim을 사용할 수 있다.
- omniverse:// URI가 보이면 Nucleus 또는 호환 서버의 자산을 가리키는 경우가 많다.

## Isaac Sim

Isaac Sim은 OpenUSD 기반 로보틱스 시뮬레이션 애플리케이션이다. 단순 렌더러나 물리 엔진 하나가 아니라 다음 기능을 통합한다.

- PhysX 기반 강체, Articulation, 충돌, Joint, 재질 시뮬레이션
- RTX 기반 카메라, LiDAR, Radar와 사실적 렌더링
- IMU, Contact, Effort 같은 물리 기반 센서
- URDF·MJCF 가져오기와 USD→URDF 내보내기
- Replicator 기반 합성 데이터와 도메인 랜덤화
- OmniGraph 기반 시각적 데이터 흐름
- GUI, Script Editor, 독립 실행형 Python, Headless 실행
- ROS 2 Bridge, Nav2, MoveIt 2 연동

Isaac Sim의 가장 중요한 기준 데이터는 Stage다. GUI에서 Prim을 옮기든 Python으로 속성을 바꾸든 결과적으로 USD Stage에 opinion을 저작한다. 단, 플레이 중의 물리 상태처럼 저장되지 않는 런타임 데이터도 있으므로 무엇을 USD에 기록하고 무엇을 매 프레임 계산하는지 구분해야 한다.

## Isaac Lab

Isaac Lab은 Isaac Sim 위에서 로봇 학습을 구성하는 통합·모듈형 프레임워크다. 주요 사용 사례는 강화학습, 모방학습, 인간 시연 수집, 모션 플래닝, 학습 정책 평가다.

Isaac Lab이 추가하는 대표 기능은 다음과 같다.

- 수백~수천 개 환경을 복제하고 텐서로 상태를 주고받는 흐름
- Scene, Observation, Action, Reward, Termination, Event 관리자 패턴
- 절차적 지형과 액추에이터 모델
- Gymnasium 환경 등록과 RL 라이브러리 연동
- 학습, 플레이, 정책 내보내기 스크립트

Isaac Lab은 Isaac Sim을 대체하지 않는다. 렌더링, 물리, USD Stage, 센서 구현은 Isaac Sim을 이용한다. GUI로 한 대의 로봇을 조립하고 검증하는 단계는 Isaac Sim의 영역이고, 검증된 자산을 수천 개 복제해 정책을 학습하는 단계는 Isaac Lab의 영역이라고 이해하면 쉽다.

과거의 Isaac Gym, IsaacGymEnvs, OmniIsaacGymEnvs, Orbit 예제를 그대로 새 프로젝트의 기준으로 삼지 않는 것이 좋다. Isaac Lab 공식 문서는 이들을 대체하는 단일 로봇 학습 프레임워크라고 설명한다.

## ROS 2 Jazzy와 Isaac ROS

ROS 2는 Isaac Sim 바깥에서 동작하는 로봇 소프트웨어 미들웨어다. Isaac Sim 5.1 공식 문서는 Humble과 Jazzy를 권장하며, 이 튜토리얼은 Ubuntu 24.04와 ROS 2 Jazzy를 기준으로 한다.

ROS 2 Bridge는 두 세계를 다음처럼 연결한다.

| Isaac Sim 쪽 | ROS 2 쪽 |
|---|---|
| Simulation Time | /clock |
| Camera·RTX 센서 출력 | sensor_msgs/Image, CameraInfo, PointCloud2, LaserScan |
| Articulation Joint 상태 | sensor_msgs/JointState |
| 로봇 Pose와 Prim 계층 | /tf, /tf_static, nav_msgs/Odometry |
| OmniGraph Subscriber | Twist, JointState, AckermannDrive 등 제어 메시지 |
| Generic Publisher/Subscriber | 사용자 정의 메시지 흐름 |

Isaac ROS는 별도 개념이다. Isaac ROS 패키지는 ROS 2 그래프 안에서 GPU 가속 인지, 이미지 처리, Visual SLAM 등을 수행한다. Isaac Sim이 센서 데이터를 생성하고 Isaac ROS가 그 데이터를 처리하는 조합은 가능하지만, Isaac ROS가 시뮬레이터인 것은 아니다.

## 어떤 도구를 언제 사용해야 하는가

| 목표 | 먼저 선택할 도구 | 이유 |
|---|---|---|
| 로봇 한 대를 가져오고 Joint·충돌을 점검한다 | Isaac Sim GUI와 Robot Setup 도구 | Stage 구조와 물리 동작을 눈으로 확인하기 쉽다 |
| 반복 가능한 장면 생성·배치 작업을 만든다 | Isaac Sim Python API와 pxr | 같은 Stage를 코드로 재생성할 수 있다 |
| USD 파일 자체를 검사·변환한다 | OpenUSD CLI와 pxr | Kit를 띄우지 않고 빠르게 자동화할 수 있다 |
| ROS 토픽으로 실제 제어기를 시험한다 | ROS 2 Bridge와 OmniGraph | 실제 노드 인터페이스를 유지한 채 시뮬레이션한다 |
| 많은 병렬 환경에서 정책을 학습한다 | Isaac Lab | 텐서 기반 병렬화와 학습용 구조를 제공한다 |
| 팀이 대형 USD 자산을 공동 관리한다 | Nucleus 또는 조직의 자산 저장 방식 | 경로 해석과 공유 원본 관리가 필요하다 |
| 사용자 전용 패널·워크플로를 제품화한다 | Kit Extension | 앱 생명주기, UI, 의존성을 모듈로 배포할 수 있다 |

## 진단할 계층을 찾는 연습

다음 질문을 순서대로 적용한다.

1. USD 파일이 열리지 않는가? 경로, Layer, Reference, Asset Resolver를 먼저 확인한다.
2. Prim은 보이지만 물리적으로 움직이지 않는가? UsdPhysics/PhysX Schema, Articulation, Collision, 질량을 확인한다.
3. GUI에서는 되지만 독립 Python에서 모듈을 못 찾는가? Isaac Sim의 Python 런타임과 Kit 초기화 순서를 확인한다.
4. 센서가 보이지만 ROS 토픽이 없는가? ROS 2 Bridge, OmniGraph 실행, Domain ID, QoS를 확인한다.
5. 한 환경은 되지만 학습이 느리거나 복제 시 깨지는가? Isaac Lab의 Cloning, Instancing, GPU pipeline 설정을 확인한다.

## 자주 하는 오해

### Omniverse를 설치해야만 USD를 읽을 수 있다

그렇지 않다. OpenUSD를 별도로 빌드하거나 배포 패키지를 사용하면 pxr API와 usdcat, usdview 같은 도구로 USD를 다룰 수 있다. 다만 NVIDIA 전용 Schema, MDL, RTX 렌더링을 완전히 재현하려면 해당 Omniverse/Isaac Sim 구성 요소가 필요하다.

### Isaac Lab이 Isaac Sim보다 상위 버전의 시뮬레이터다

그렇지 않다. Isaac Lab은 Isaac Sim에 의존하는 학습 프레임워크다. 두 프로젝트의 호환 버전 표를 확인해야 하며 임의로 최신 버전을 섞으면 안 된다.

### Nucleus가 없으면 Isaac Sim을 사용할 수 없다

그렇지 않다. 로컬 파일과 다운로드한 자산만으로도 사용할 수 있다. Nucleus는 협업과 중앙 자산 관리가 필요할 때 선택한다.

### ROS 2가 USD의 로봇 구조를 자동으로 계속 동기화한다

그렇지 않다. ROS 2 Bridge는 선택한 메시지와 그래프를 실행 중 교환한다. USD의 모든 속성이 자동으로 ROS 파라미터가 되는 것은 아니다.

## 확인 문제

1. USD의 Prim 계층을 수정하는 작업과 ROS 2 토픽 이름을 수정하는 작업은 각각 어느 계층에 속하는가?
2. 사용자 정의 메뉴를 추가하면서 현재 Stage도 편집해야 한다면 pxr만으로 충분한가, Kit Extension이 필요한가?
3. 한 대의 로봇 자산 검증과 4096개 환경의 정책 학습에 각각 무엇을 사용하는가?
4. omniverse:// 경로가 끊어졌을 때 PhysX 튜닝보다 먼저 확인할 것은 무엇인가?

정답은 순서대로 USD/ROS 2, Kit Extension, Isaac Sim/Isaac Lab, Nucleus 연결과 Asset Resolver 경로다.

## 출처

- [NVIDIA Isaac Sim 5.1 — Reference Architecture and Task Groupings](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/introduction/reference_architecture.html)
- [NVIDIA Isaac Sim 5.1 — ROS 2](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/ros2_landing_page.html)
- [NVIDIA Isaac Sim 5.1 — OpenUSD Fundamentals](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/omniverse_usd/open_usd.html)
- [NVIDIA Omniverse Developer Overview — Platform Overview](https://docs.omniverse.nvidia.com/dev-overview/latest/platform-overview.html)
- [NVIDIA Omniverse Kit — Overview](https://docs.omniverse.nvidia.com/kit/docs/kit-manual/latest/guide/kit_overview.html)
- [OpenUSD — Introduction](https://openusd.org/release/intro.html)
- [Isaac Lab — Welcome](https://isaac-sim.github.io/IsaacLab/main/index.html)
- [Isaac Lab — Ecosystem](https://isaac-sim.github.io/IsaacLab/main/source/setup/ecosystem.html)
