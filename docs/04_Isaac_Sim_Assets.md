# Isaac Sim Asset
로봇 시뮬레이션을 만든다고 가정하자. 그러면 제일 귀찮은게 뭘까?  
개인적인 입장으로는 로봇 Asset과 World/Scene Asset을 구하는 것이라고 생각한다.  
물론 CAD나 블렌더 고수여서 30분도 안되는 시간에 원하는 로봇 모델링을 뚝딱 만들어낼 수 있는 능력자도 있겠지만..  
본인은 그러지 못하기 때문에..  
  
다행스럽게도 엔비디아에서는 Isaac Sim용으로 굉장히 많은 Asset을 제공해준다.  
해당 Asset을 활용하기만 하더라도 어지간한 로봇 시뮬레이션은 모두 가능한 수준이라고 할 수 있다.

모든 Asset에 대해서 사진과 함께 작성하는 것은 문서가 너무 길어지고,  
영어가 짧더라도 엔비디아에서 이미 잘 작성을 해두었기 때문에 본 문서에서는 
대표적인 Asset들만 몇가지 예시로 기술하고, 링크로 첨부한다.  
  
엔비디아에서 제공하는 Isaac Sim Asset 링크 : [**링크**](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/assets/usd_assets_overview.html)  
  
| 대분류 | 세부 분류 | 용도 / 설명 | 대표 예시 |
|---|---|---|---|
| Robots | Wheeled Robot | 바퀴 기반 모바일 로봇 | TurtleBot3, iRobot Create3, JetBot |
| Robots | Holonomic Robot | Mecanum/Omni wheel 등 전방향 이동 로봇 | NVIDIA Kaya |
| Robots | Manipulator | 산업용/연구용 로봇 팔 | Franka, UR 계열, Yaskawa 등 |
| Robots | Mobile Manipulator | 이동 베이스 + Manipulator가 결합된 로봇 | Clearpath 계열 |
| Robots | Humanoid | 인간형 로봇 | PX5, Humanoid 계열 |
| Robots | Quadruped | 4족 보행 로봇 | Unitree Go1, Go2, Laikago, ANYmal |
| Robots | Aerial Robot | 드론 및 비행 로봇 | Crazyflie, NASA Ingenuity, Quadcopter |
| Robots | Simple / Reference Robot | API 및 물리 실습용 단순 로봇/Articulation | Cartpole, SimpleArticulation, DifferentialBase |
| Sensors | Camera / Depth | RGB, Depth 등 시각 센서 | Camera, Depth Camera |
| Sensors | RTX LiDAR / Radar | RTX 기반 광선 추적 센서 | RTX LiDAR, RTX Radar |
| Sensors | Physics-based Sensor | 물리 시뮬레이션 기반 센서 | IMU, Contact, Effort, Joint Sensor |
| Environments | Simple Environment | 기본 테스트용 환경 | Flat Grid, Simple Room |
| Environments | Warehouse | 물류/AMR 실험 환경 | Warehouse, Full Warehouse |
| Environments | Indoor Environment | 실내 navigation 및 service robot 환경 | Hospital, Office |
| Environments | Track / Test Environment | 주행 및 controller 테스트용 환경 | JetRacer Track |
| Environments | Digital Twin | 실제 공간을 재현한 simulation 환경 | Small Warehouse Digital Twin |
| Props | Industrial Props | 물류/산업 환경 구성용 물체 | Pallet, Box, Rack, Container 등 |
| Props | Furniture / Indoor Props | 실내 환경 구성용 물체 | Table, Chair 등 |
| Props | Miscellaneous Objects | 로봇 manipulation / perception용 일반 물체 | Box, Cylinder, Object 등 |
| People | Human Characters | 사람/서비스 로봇/SDG 시뮬레이션용 캐릭터 | Doctor, Police Officer, Construction Worker 등 |
| Materials | Visual Materials | 물체 외관 및 렌더링용 Material | Metal, Plastic, Concrete 등 |
| Materials | Sensor / Physics-related Materials | 센서 반사 특성이나 물리 특성 표현에 사용하는 Material | RTX sensor material 등 |
  
그 외에도 다음과 같은 Asset들을 같이 지원한다.
| Asset 종류  | 설명 |
| -- | -- |
| [써드파티 Asset](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/assets/usd_assets_third_party.html) | 써드파티에서 Simulation-ready로 제공하는 Asset Fab. 다만 개중에 유료도 있으니 라이센스와 비용을 확인해서 조심해서 사용해야한다.<br>생각보다 이것저것 엄청나게 많기 때문에 명세서만 잘 작성한다면 시뮬레이션을 만드는게 그렇게 어렵지 않다. |
| [Neural Volume Rendering](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/assets/usd_assets_nurec.html) | Isaac Sim에서는 현실 세계를 촬영한 것을 Gaussian Splatting 등 Neural Rendering 해서 isaac sim에 통합하는 것을 지원한다.<br>이와 관련된 기술 문서로 [**NuRec**](https://github.com/NVIDIA/instant-nurec)을 참고하면 좋을 것 같다. |