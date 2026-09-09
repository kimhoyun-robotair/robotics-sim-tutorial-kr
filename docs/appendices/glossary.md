# 핵심 용어집

영문 이름은 GUI와 API에서 다시 찾기 쉽도록 함께 적었다. 처음 읽을 때는 오른쪽 설명을 이해하고, 실습 중에는 왼쪽 이름으로 메뉴·문서를 검색한다.

| 용어 | 이 과정에서의 의미 |
| --- | --- |
| Asset · 자산 | 로봇이나 환경처럼 다시 사용할 수 있는 장면 구성 요소다. USD뿐 아니라 메시, 재질, 텍스처 등 의존 파일을 함께 포함한다. |
| Articulation · 관절 구조 | 조인트로 연결한 강체들의 구조다. PhysX가 링크와 관절 사이의 운동을 함께 계산한다. |
| Extension · 확장 | Kit에 메뉴, 창, 명령 또는 Python/C++ 기능을 추가하는 모듈이다. 필요한 기능을 켜거나 별도 패키지로 배포할 수 있다. |
| Kit | 여러 Extension을 조합해 OpenUSD 애플리케이션을 만드는 NVIDIA SDK이자 실행 환경이다. |
| Nucleus | USD와 관련 자산을 여러 사용자가 공유하는 서버다. 로컬 파일만으로 실습할 때는 필요하지 않다. |
| OmniGraph | 노드와 연결선으로 계산 순서와 데이터 흐름을 구성하는 도구다. Action Graph는 이벤트에 따라 노드를 실행하는 방식이다. |
| OpenUSD | 장면 구조, 속성, 파일 조합 규칙과 이를 읽고 쓰는 API를 제공하는 오픈 소스 기술이다. |
| Prim · 프림 | `/World/Robot` 같은 경로로 식별하는 USD 장면 객체다. 타입, 속성, 자식 Prim을 가질 수 있다. |
| Replicator | 장면 조건을 바꾸고 이미지·정답 데이터를 추출해 저장하는 합성 데이터 도구다. |
| RTX sensor · RTX 센서 | NVIDIA RTX 렌더링 기술로 관측값을 계산하는 센서다. 카메라와 RTX LiDAR·Radar는 출력 종류와 설정 방법이 서로 다르다. |
| SimulationApp | 독립 실행형 Python에서 Isaac Sim을 시작하고 종료하는 객체다. `omni.*` 등 Kit 모듈을 불러오기 전에 생성한다. |
| Stage · 스테이지 | 여러 Layer와 참조를 조합해 만든 전체 장면이다. GUI에서 편집하거나 시뮬레이션하는 대상이다. |
| Layer · 레이어 | 장면의 구조와 속성 값을 기록하는 단위다. 파일로 저장하거나 메모리에 임시로 만들 수 있다. |
| Opinion | 특정 Layer에 기록한 값이나 설정을 뜻하는 USD 용어다. 같은 속성에 여러 값이 있으면 조합 규칙과 우선순위로 최종 값을 정한다. |
| Edit Target | 현재 수정한 값을 기록할 Layer다. Stage에 보이는 최종 결과와 실제로 수정할 파일을 구분할 때 중요하다. |
| Reference · 참조 | 다른 자산을 지정한 Prim 아래에 불러오는 연결이다. 원본 파일을 복사하지 않고 재사용한다. |
| Payload | 필요할 때만 내용을 불러올 수 있는 참조다. 물리 계산에 필요한 링크나 충돌체는 시뮬레이션 전에 불러와야 한다. |
| Render Product | 특정 카메라와 해상도로 영상을 계산하는 출력 설정이다. 센서 데이터가 나오는 경로를 Viewport 표시와 구분한다. |
| Annotator | 렌더링 결과에서 RGB, 깊이, 분할 레이블 같은 데이터를 추출하는 모듈이다. |
| Writer | 추출한 데이터와 메타데이터를 파일로 저장하는 모듈이다. |
| Isaac Lab | Isaac Sim 위에서 병렬 환경과 로봇 강화학습·모방학습을 구성하는 별도 프레임워크다. |
| Isaac Sim | OpenUSD, Kit, PhysX, RTX에 로봇·센서·제어·ROS 2 기능을 결합한 로봇 시뮬레이터다. |

## 출처

- [Isaac Sim Glossary](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/reference_material/reference_glossary.html)
- [Omniverse and USD](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/omniverse_usd/index.html)
- [OpenUSD Glossary](https://openusd.org/release/glossary.html)
