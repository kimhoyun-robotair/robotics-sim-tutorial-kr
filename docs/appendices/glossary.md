# 핵심 용어집

| 용어 | 이 과정에서의 의미 |
| --- | --- |
| Asset | 파일 하나가 아니라 mesh, material, texture, layer와 metadata가 결합된 재사용 가능한 자산이다. |
| Articulation | joint로 연결된 rigid body tree를 PhysX가 효율적으로 푸는 구조이다. |
| Extension | Kit application에 UI, service, command, Python/C++ 기능을 추가하는 배포 단위이다. |
| Kit | USD 기반 application을 extension 조합으로 만드는 Omniverse SDK/runtime이다. |
| Nucleus | USD와 관련 파일을 협업·버전·권한과 함께 제공하는 Omniverse 데이터 서비스이다. 로컬 학습에 항상 필요한 것은 아니다. |
| OmniGraph | node와 edge로 실행·데이터 흐름을 표현하는 graph engine이다. Action Graph는 그 사용 형태 중 하나이다. |
| OpenUSD | scene description, composition, schema, 파일 형식과 API를 제공하는 오픈소스 기술이다. |
| Prim | USD stage의 namespace에 존재하는 기본 scene object이다. property와 schema를 갖는다. |
| Replicator | randomization, annotator, writer를 조합해 합성 데이터를 생성하는 Isaac Sim/Omniverse 도구 집합이다. |
| RTX sensor | ray tracing pipeline을 이용해 카메라, LiDAR, radar 등의 관측을 생성하는 sensor 계열이다. |
| SimulationApp | standalone Python에서 Kit application을 먼저 시작하고 닫는 lifecycle 진입점이다. |
| Stage | root layer와 composition된 layer들을 평가해 보이는 USD scene이다. |
| USD layer | opinion을 저장하는 독립 파일 또는 익명 layer이다. stage와 같은 뜻이 아니다. |
| Isaac Lab | Isaac Sim 위에서 병렬 환경, task, robot learning과 RL workflow를 제공하는 별도 오픈소스 framework이다. |
| Isaac Sim | OpenUSD, Kit, PhysX, RTX와 로봇용 extension·asset·API를 묶은 로봇 시뮬레이션 application/platform이다. |

## 출처

- [Isaac Sim Glossary](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/reference_material/reference_glossary.html)
- [Omniverse and USD](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/omniverse_usd/index.html)
- [OpenUSD Glossary](https://openusd.org/release/glossary.html)
