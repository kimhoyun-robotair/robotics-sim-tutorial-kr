# Isaac Sim 5.1 권장 학습 순서 — 180개 패키지

**폴더 앞 번호 `00`–`179`가 권장 학습 순서입니다.** 기본 사용 → Hello World → Hello Robot으로 시작해 Python·USD, 물리·로봇 구성·제어, 센서·OmniGraph, ROS 2, 합성 데이터, 정책과 외부 통합으로 진행합니다.

각 패키지는 독립적입니다. 이 순서는 학습을 돕는 안내이며 앞 패키지의 코드나 결과물을 요구하지 않습니다. 관심 주제로 바로 시작해도 필요한 준비·설명은 해당 폴더의 `TUTORIAL.md`에서 확인할 수 있습니다.

기존 `t001` 같은 **출처 ID는 유지**했습니다. 예를 들어 `01_core_core_hello_world`의 학습 번호는 `01`, 출처 ID는 `t098`입니다. 공식 제목과 5.1 원문 링크도 유지합니다.

[저장소 실행 안내](../INSTRUCTION.md) · [공식 목차 대응표](official_tutorials.json) · [검증 범위](VALIDATION.md)

```bash
python3 src/catalog.py list
python3 src/catalog.py show 00
python3 src/catalog.py list --stage ros2_basics
python3 src/catalog.py list --category sensors
python3 src/catalog.py check
```

파일 이름을 터미널에서 번호순으로 보려면 `ls -v src/`를 사용합니다. 색인 도구는 번호를 숫자로 정렬합니다.

## 학습 단계

| 범위 | 단계 | 학습 목표 |
|---|---|---|
| 00–03 | [첫 실행과 로봇 만나기](#first_steps) | 기본 조작, World의 물리 스텝, Jetbot 관절 제어를 먼저 경험하고 기본 로봇 조사 실습으로 연결한다. |
| 04–17 | [Python 실행 환경과 USD 기초](#python_usd) | 실행 방식과 개발 도구를 익힌 뒤 Core API, USD 계층·속성·명령, 장면 작성 코드를 이해한다. |
| 18–28 | [물리 기초와 Core API 확장](#physics_core) | 충돌·강체·물리 검사부터 익히고 컨트롤러, 매니퓰레이터, 여러 로봇과 Task, 데이터 기록으로 확장한다. |
| 29–50 | [로봇 자산 가져오기와 제작](#robot_authoring) | 로봇 스키마와 변환 도구를 익히고 공식 제작 Tutorial 1–13 순서를 유지해 조립·리깅·설정·최적화를 연습한다. 마지막 보행 로봇 수업은 정책 실행 전 USD 설정 실습이다. |
| 51–61 | [로봇 제어와 동작 계획](#motion_control) | 관절·모바일 제어에서 로봇 기술 파일, 운동학·궤적, RMPflow·RRT, 튜닝과 그리퍼로 진행한다. |
| 62–79 | [센서와 측정 데이터](#sensors) | 카메라와 물리 센서에서 RTX Lidar·Radar, 비시각 재질·annotator·Motion BVH로 확장하고 배치·보정을 마무리한다. |
| 80–93 | [OmniGraph와 확장 개발](#omnigraph_extensions) | 그래프 연결과 Python 생성, 확장 등록·템플릿·대화형 예제를 익힌 뒤 Python/C++ custom node와 디버깅·프로파일링을 학습한다. 이후 ROS와 Replicator 사용자 노드의 기반이다. |
| 94–103 | [환경 구축과 로봇 행동](#environments_behaviors) | 창고·컨베이어·Occupancy Map을 만들고 RMPflow와 확장 개발 경험을 Cortex의 의사결정·행동 예제에 적용한다. 지도 작성은 다음 ROS 내비게이션의 배경이 된다. |
| 104–121 | [ROS 2 연결과 기본 통신](#ros2_basics) | TurtleBot 제어와 시계·TF·통신 설정을 익히고 카메라·Lidar·관절 제어를 연결한 뒤 standalone·launch·simulation control을 실습한다. |
| 122–131 | [ROS 2 응용과 사용자 인터페이스](#ros2_applications) | 내비게이션·다중 로봇·MoveIt을 적용한 뒤 generic topic/service, 사용자 메시지, Python/C++ OmniGraph 노드를 구현한다. |
| 132–143 | [Replicator 합성 데이터 기초와 확장](#replicator) | 의미 라벨과 Recorder부터 스크립트·무작위화·캡처 시점·장면 및 물체 데이터셋을 익히고 증강·사용자 노드·행동 스크립트·로봇 응용으로 확장한다. |
| 144–155 | [물체 시뮬레이션과 YAML 무작위화](#object_sdg) | IRO 전체 실행에서 설정·Mutable·카메라·기하·조명·속성·변환을 익히고 Harmonizer·Macro·분포·의존 무작위화로 나아간다. |
| 156–161 | [액터와 공간 이벤트 데이터](#actor_events) | 액터 실행부터 동작·카메라·Writer·사용자 설정을 익히고 물리 공간의 사건 시나리오로 연결한다. |
| 162–167 | [병렬 환경과 학습 정책 활용](#policies_scaling) | Instanceable 자산과 Cloner를 익히고 이미 학습된 정책 예제, 정책 배포, ROS 제어, MobilityGen 궤적 기록·재렌더링을 연결한다. |
| 168–174 | [고급 데이터 생성과 외부 시스템 통합](#advanced_integrations) | 집기 평가에서 Infinigen·Cosmos·VLM 데이터 흐름, NuRec 장면, cuRobo·cuMotion과 cuOpt 서비스로 넓힌다. 별도 데이터·모델·설치·서비스가 필요한 통합 실습을 뒤에 둔다. |
| 175–179 | [사용 중단 문서와 레거시 참고](#legacy_reference) | 공식 원문이 deprecated로 표시된 ShapeNet·SceneBlox·온라인 생성·Pose Estimation 생성 및 학습을 마지막 참고 과정으로 둔다. ShapeNet 실습 자체는 현재 OBJ→USD 변환 경로를 사용한다. |

공식 Tutorial Reference Table의 9개 시리즈와 목차의 추가 실습·하위 페이지를 포함합니다. 설치·릴리스·API/자산 참조와 외부 사이트 전체는 포함 범위에서 제외합니다. 사용 중단된 원문의 실습은 마지막 참고 단계에 배치했습니다.

<a id="first_steps"></a>

## 00–03 · 첫 실행과 로봇 만나기

기본 조작, World의 물리 스텝, Jetbot 관절 제어를 먼저 경험하고 기본 로봇 조사 실습으로 연결한다.

분야별 실행 방식은 각 안내를 따릅니다. 이 단계만 검색: `python3 src/catalog.py list --stage first_steps`

| 순서 | 패키지 / 한국어 실습 안내 | 공식 제목 | 실행 방식 | 출처 |
|---|---|---|---|---|
| 00 | [00_core_quickstart_isaacsim](00_core_quickstart_isaacsim/TUTORIAL.md) | Isaac Sim Basic Usage Tutorial | `standalone` | [t001](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/introduction/quickstart_isaacsim.html) |
| 01 | [01_core_core_hello_world](01_core_core_hello_world/TUTORIAL.md) | Hello World | `standalone` | [t098](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_hello_world.html) |
| 02 | [02_core_core_hello_robot](02_core_core_hello_robot/TUTORIAL.md) | Hello Robot | `standalone` | [t099](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_hello_robot.html) |
| 03 | [03_core_quickstart_isaacsim_robot](03_core_quickstart_isaacsim_robot/TUTORIAL.md) | Basic Robot Tutorial | `standalone` | [t002](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/introduction/quickstart_isaacsim_robot.html) |

<a id="python_usd"></a>

## 04–17 · Python 실행 환경과 USD 기초

실행 방식과 개발 도구를 익힌 뒤 Core API, USD 계층·속성·명령, 장면 작성 코드를 이해한다.

분야별 실행 방식은 각 안내를 따릅니다. 이 단계만 검색: `python3 src/catalog.py list --stage python_usd`

| 순서 | 패키지 / 한국어 실습 안내 | 공식 제목 | 실행 방식 | 출처 |
|---|---|---|---|---|
| 04 | [04_tools_omniverse_script_editor](04_tools_omniverse_script_editor/TUTORIAL.md) | Omniverse Script Editor | `script_editor` | [t090](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/development_tools/omniverse_script_editor.html) |
| 05 | [05_python_usd_python_scripting_concepts](05_python_usd_python_scripting_concepts/TUTORIAL.md) | Python Scripting Concepts | `standalone` | [t092](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/python_scripting/python_scripting_concepts.html) |
| 06 | [06_python_usd_manual_standalone_python](06_python_usd_manual_standalone_python/TUTORIAL.md) | Python Environment | `standalone` | [t094](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/python_scripting/manual_standalone_python.html) |
| 07 | [07_tools_vscode](07_tools_vscode/TUTORIAL.md) | Visual Studio Code (VS Code) | `script_editor` | [t088](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/development_tools/vscode.html) |
| 08 | [08_tools_jupyter_notebook](08_tools_jupyter_notebook/TUTORIAL.md) | Jupyter Notebook | `external` | [t089](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/development_tools/jupyter_notebook.html) |
| 09 | [09_python_usd_core_api_overview](09_python_usd_core_api_overview/TUTORIAL.md) | Core API Overview | `standalone` | [t093](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/python_scripting/core_api_overview.html) |
| 10 | [10_python_usd_open_usd](10_python_usd_open_usd/TUTORIAL.md) | OpenUSD Fundamentals | `standalone` | [t173](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/omniverse_usd/open_usd.html) |
| 11 | [11_python_usd_intro_to_usd](11_python_usd_intro_to_usd/TUTORIAL.md) | Working with USD | `standalone` | [t174](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/omniverse_usd/intro_to_usd.html) |
| 12 | [12_python_usd_usd_tools](12_python_usd_usd_tools/TUTORIAL.md) | USD Tools | `standalone` | [t175](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/omniverse_usd/usd_tools.html) |
| 13 | [13_python_usd_omniverse_tools](13_python_usd_omniverse_tools/TUTORIAL.md) | Commands | `standalone` | [t177](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/omniverse_usd/omniverse_tools.html) |
| 14 | [14_tools_ext_omni_kit_commands](14_tools_ext_omni_kit_commands/TUTORIAL.md) | Omniverse Commands Tool Extension | `gui` | [t169](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/utilities/debugging/ext_omni_kit_commands.html) |
| 15 | [15_tools_carb_settings](15_tools_carb_settings/TUTORIAL.md) | Modify Carb Settings | `extension` | [t091](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/development_tools/carb_settings.html) |
| 16 | [16_python_usd_environment_setup](16_python_usd_environment_setup/TUTORIAL.md) | Scene Setup Snippets | `standalone` | [t095](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/python_scripting/environment_setup.html) |
| 17 | [17_python_usd_util_snippets](17_python_usd_util_snippets/TUTORIAL.md) | Util Snippets | `standalone` | [t096](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/python_scripting/util_snippets.html) |

<a id="physics_core"></a>

## 18–28 · 물리 기초와 Core API 확장

충돌·강체·물리 검사부터 익히고 컨트롤러, 매니퓰레이터, 여러 로봇과 Task, 데이터 기록으로 확장한다.

분야별 실행 방식은 각 안내를 따릅니다. 이 단계만 검색: `python3 src/catalog.py list --stage physics_core`

| 순서 | 패키지 / 한국어 실습 안내 | 공식 제목 | 실행 방식 | 출처 |
|---|---|---|---|---|
| 18 | [18_sensors_simulation_fundamentals](18_sensors_simulation_fundamentals/TUTORIAL.md) | Physics Simulation Fundamentals | `standalone` | [t159](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/physics/simulation_fundamentals.html) |
| 19 | [19_core_core_adding_props](19_core_core_adding_props/TUTORIAL.md) | Adding Props | `standalone` | [t104](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_adding_props.html) |
| 20 | [20_sensors_physics_static_collision](20_sensors_physics_static_collision/TUTORIAL.md) | Physics Static Collision Extension | `standalone` | [t161](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/physics/physics_static_collision.html) |
| 21 | [21_sensors_joint_inspector](21_sensors_joint_inspector/TUTORIAL.md) | Physics Inspector | `standalone` | [t160](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/physics/joint_inspector.html) |
| 22 | [22_sensors_inspect_physics](22_sensors_inspect_physics/TUTORIAL.md) | Simulation Data Visualizer | `standalone` | [t162](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/physics/ext_isaacsim_inspect_physics.html) |
| 23 | [23_core_core_adding_controller](23_core_core_adding_controller/TUTORIAL.md) | Adding a Controller | `standalone` | [t100](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_adding_controller.html) |
| 24 | [24_core_core_adding_manipulator](24_core_core_adding_manipulator/TUTORIAL.md) | Adding a Manipulator Robot | `standalone` | [t101](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_adding_manipulator.html) |
| 25 | [25_core_core_adding_multiple_robots](25_core_core_adding_multiple_robots/TUTORIAL.md) | Adding Multiple Robots | `standalone` | [t102](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_adding_multiple_robots.html) |
| 26 | [26_core_core_multiple_tasks](26_core_core_multiple_tasks/TUTORIAL.md) | Multiple Tasks | `standalone` | [t103](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_multiple_tasks.html) |
| 27 | [27_core_advanced_data_logging](27_core_advanced_data_logging/TUTORIAL.md) | Data Logging | `standalone` | [t105](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_advanced_data_logging.html) |
| 28 | [28_python_usd_robots_simulation](28_python_usd_robots_simulation/TUTORIAL.md) | Robot Simulation Snippets | `standalone` | [t097](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/python_scripting/robots_simulation.html) |

<a id="robot_authoring"></a>

## 29–50 · 로봇 자산 가져오기와 제작

로봇 스키마와 변환 도구를 익히고 공식 제작 Tutorial 1–13 순서를 유지해 조립·리깅·설정·최적화를 연습한다. 마지막 보행 로봇 수업은 정책 실행 전 USD 설정 실습이다.

분야별 실행 방식은 각 안내를 따릅니다. 이 단계만 검색: `python3 src/catalog.py list --stage robot_authoring`

| 순서 | 패키지 / 한국어 실습 안내 | 공식 제목 | 실행 방식 | 출처 |
|---|---|---|---|---|
| 29 | [29_python_usd_robot_schema](29_python_usd_robot_schema/TUTORIAL.md) | Robot Schema | `standalone` | [t176](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/omniverse_usd/robot_schema.html) |
| 30 | [30_importers_import_urdf](30_importers_import_urdf/TUTORIAL.md) | Tutorial: Import URDF | `standalone` | [t111](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/importer_exporter/import_urdf.html) |
| 31 | [31_importers_import_mjcf](31_importers_import_mjcf/TUTORIAL.md) | Tutorial: Import MJCF | `standalone` | [t113](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/importer_exporter/import_mjcf.html) |
| 32 | [32_importers_export_urdf](32_importers_export_urdf/TUTORIAL.md) | Tutorial: Export URDF | `standalone` | [t112](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/importer_exporter/export_urdf.html) |
| 33 | [33_importers_util_merge_mesh](33_importers_util_merge_mesh/TUTORIAL.md) | Merge Mesh Utility | `standalone` | [t116](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup/ext_isaacsim_util_merge_mesh.html) |
| 34 | [34_robot_setup_robot_wizard_tutorials](34_robot_setup_robot_wizard_tutorials/TUTORIAL.md) | Robot Wizard Tutorial | `gui` | [t115](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup/robot_wizard_tutorials.html) |
| 35 | [35_robot_setup_intro_environment_setup](35_robot_setup_intro_environment_setup/TUTORIAL.md) | Tutorial 1: Stage Setup | `gui` | [t119](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/tutorial_intro_environment_setup.html) |
| 36 | [36_robot_setup_intro_assemble_robot](36_robot_setup_intro_assemble_robot/TUTORIAL.md) | Tutorial 2: Assemble a Simple Robot | `gui` | [t120](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/tutorial_intro_assemble_robot.html) |
| 37 | [37_robot_setup_gui_simple_robot](37_robot_setup_gui_simple_robot/TUTORIAL.md) | Tutorial 3: Articulate a Basic Robot | `gui` | [t121](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/tutorial_gui_simple_robot.html) |
| 38 | [38_robot_setup_gui_camera_sensors](38_robot_setup_gui_camera_sensors/TUTORIAL.md) | Tutorial 4: Add Camera and Sensors to a Robot | `gui` | [t122](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/tutorial_gui_camera_sensors.html) |
| 39 | [39_robot_setup_rig_mobile_robot](39_robot_setup_rig_mobile_robot/TUTORIAL.md) | Tutorial 5: Rig a Mobile Robot | `gui` | [t123](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/rig_mobile_robot.html) |
| 40 | [40_robot_setup_import_assemble_manipulator](40_robot_setup_import_assemble_manipulator/TUTORIAL.md) | Tutorial 6: Setup a Manipulator | `gui` | [t124](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/tutorial_import_assemble_manipulator.html) |
| 41 | [41_robot_setup_configure_manipulator](41_robot_setup_configure_manipulator/TUTORIAL.md) | Tutorial 7: Configure a Manipulator | `gui` | [t125](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/tutorial_configure_manipulator.html) |
| 42 | [42_robot_setup_generate_robot_config](42_robot_setup_generate_robot_config/TUTORIAL.md) | Tutorial 8: Generate Robot Configuration File | `gui` | [t126](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/tutorial_generate_robot_config.html) |
| 43 | [43_robot_setup_pickplace_example](43_robot_setup_pickplace_example/TUTORIAL.md) | Tutorial 9: Pick and Place Example | `standalone` | [t127](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/tutorial_pickplace_example.html) |
| 44 | [44_robot_setup_rig_closed_loop_structures](44_robot_setup_rig_closed_loop_structures/TUTORIAL.md) | Tutorial 10: Rig Closed-Loop Structures | `gui` | [t128](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/rig_closed_loop_structures.html) |
| 45 | [45_robot_setup_joint_tuning](45_robot_setup_joint_tuning/TUTORIAL.md) | Tutorial 11: Tuning Joint Drive Gains | `standalone` | [t129](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/joint_tuning.html) |
| 46 | [46_robot_setup_optimizing_asset](46_robot_setup_optimizing_asset/TUTORIAL.md) | Tutorial 12: Asset Optimization | `gui` | [t130](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/optimizing_asset.html) |
| 47 | [47_robot_setup_rig_legged_robot](47_robot_setup_rig_legged_robot/TUTORIAL.md) | Tutorial 13: Rigging a Legged Robot for Locomotion Policy | `standalone` | [t131](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/tutorial_rig_legged_robot.html) |
| 48 | [48_importers_robot_setup_gain_tuner](48_importers_robot_setup_gain_tuner/TUTORIAL.md) | Gain Tuner Extension | `standalone` | [t117](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup/ext_isaacsim_robot_setup_gain_tuner.html) |
| 49 | [49_importers_assemble_robots](49_importers_assemble_robots/TUTORIAL.md) | Robot Assembler | `standalone` | [t118](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup/assemble_robots.html) |
| 50 | [50_importers_asset_validation](50_importers_asset_validation/TUTORIAL.md) | Asset Validation | `standalone` | [t132](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup/asset_validation.html) |

<a id="motion_control"></a>

## 51–61 · 로봇 제어와 동작 계획

관절·모바일 제어에서 로봇 기술 파일, 운동학·궤적, RMPflow·RRT, 튜닝과 그리퍼로 진행한다.

분야별 실행 방식은 각 안내를 따릅니다. 이 단계만 검색: `python3 src/catalog.py list --stage motion_control`

| 순서 | 패키지 / 한국어 실습 안내 | 공식 제목 | 실행 방식 | 출처 |
|---|---|---|---|---|
| 51 | [51_motion_articulation_controller](51_motion_articulation_controller/TUTORIAL.md) | Articulation Controller | `standalone` | [t133](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_simulation/articulation_controller.html) |
| 52 | [52_motion_mobile_robot_controllers](52_motion_mobile_robot_controllers/TUTORIAL.md) | Mobile Robot Controllers | `standalone` | [t134](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_simulation/mobile_robot_controllers.html) |
| 53 | [53_motion_manipulators_robot_description_editor](53_motion_manipulators_robot_description_editor/TUTORIAL.md) | Lula Robot Description and XRDF Editor | `gui` | [t135](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/manipulators/manipulators_robot_description_editor.html) |
| 54 | [54_motion_manipulators_lula_kinematics](54_motion_manipulators_lula_kinematics/TUTORIAL.md) | Lula Kinematics Solver | `standalone` | [t138](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/manipulators/manipulators_lula_kinematics.html) |
| 55 | [55_motion_manipulators_lula_trajectory_generator](55_motion_manipulators_lula_trajectory_generator/TUTORIAL.md) | Lula Trajectory Generator | `standalone` | [t139](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/manipulators/manipulators_lula_trajectory_generator.html) |
| 56 | [56_motion_manipulators_rmpflow](56_motion_manipulators_rmpflow/TUTORIAL.md) | Lula RMPflow | `standalone` | [t136](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/manipulators/manipulators_rmpflow.html) |
| 57 | [57_motion_manipulators_lula_rrt](57_motion_manipulators_lula_rrt/TUTORIAL.md) | Lula RRT | `standalone` | [t137](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/manipulators/manipulators_lula_rrt.html) |
| 58 | [58_motion_manipulators_configure_rmpflow_denso](58_motion_manipulators_configure_rmpflow_denso/TUTORIAL.md) | Configuring RMPflow for a New Manipulator | `gui` | [t140](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/manipulators/manipulators_configure_rmpflow_denso.html) |
| 59 | [59_motion_rmpflow_tuning](59_motion_rmpflow_tuning/TUTORIAL.md) | RMPflow Tuning Guide | `standalone` | [t180](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/manipulators/concepts/rmpflow_tuning_guide.html) |
| 60 | [60_motion_robot_surface_gripper](60_motion_robot_surface_gripper/TUTORIAL.md) | Surface Gripper Extension | `standalone` | [t142](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_simulation/ext_isaacsim_robot_surface_gripper.html) |
| 61 | [61_motion_grasp_editor](61_motion_grasp_editor/TUTORIAL.md) | Grasp Editor | `gui` | [t143](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_simulation/grasp_editor.html) |

<a id="sensors"></a>

## 62–79 · 센서와 측정 데이터

카메라와 물리 센서에서 RTX Lidar·Radar, 비시각 재질·annotator·Motion BVH로 확장하고 배치·보정을 마무리한다.

분야별 실행 방식은 각 안내를 따릅니다. 이 단계만 검색: `python3 src/catalog.py list --stage sensors`

| 순서 | 패키지 / 한국어 실습 안내 | 공식 제목 | 실행 방식 | 출처 |
|---|---|---|---|---|
| 62 | [62_sensors_sensors_camera](62_sensors_sensors_camera/TUTORIAL.md) | Camera Sensors | `standalone` | [t145](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_camera.html) |
| 63 | [63_sensors_sensors_camera_depth](63_sensors_sensors_camera_depth/TUTORIAL.md) | Depth Sensors | `standalone` | [t146](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_camera_depth.html) |
| 64 | [64_sensors_sensors_physics_articulation_force](64_sensors_sensors_physics_articulation_force/TUTORIAL.md) | Articulation Joint Sensors | `standalone` | [t151](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_physics_articulation_force.html) |
| 65 | [65_sensors_sensors_physics_contact](65_sensors_sensors_physics_contact/TUTORIAL.md) | Contact Sensor | `standalone` | [t152](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_physics_contact.html) |
| 66 | [66_sensors_sensors_physics_effort](66_sensors_sensors_physics_effort/TUTORIAL.md) | Effort Sensor | `standalone` | [t153](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_physics_effort.html) |
| 67 | [67_sensors_sensors_physics_imu](67_sensors_sensors_physics_imu/TUTORIAL.md) | IMU Sensor | `standalone` | [t154](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_physics_imu.html) |
| 68 | [68_sensors_sensors_physics_proximity](68_sensors_sensors_physics_proximity/TUTORIAL.md) | Proximity Sensor | `standalone` | [t155](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_physics_proximity.html) |
| 69 | [69_sensors_sensors_physx_generic](69_sensors_sensors_physx_generic/TUTORIAL.md) | PhysX SDK Generic Sensor | `standalone` | [t156](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_physx_generic.html) |
| 70 | [70_sensors_sensors_physx_lidar](70_sensors_sensors_physx_lidar/TUTORIAL.md) | PhysX SDK Lidar | `standalone` | [t157](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_physx_lidar.html) |
| 71 | [71_sensors_sensors_physx_lightbeam](71_sensors_sensors_physx_lightbeam/TUTORIAL.md) | PhysX SDK Lightbeam Sensor | `standalone` | [t158](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_physx_lightbeam.html) |
| 72 | [72_sensors_sensors_rtx_lidar](72_sensors_sensors_rtx_lidar/TUTORIAL.md) | RTX Lidar Sensor | `standalone` | [t147](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_rtx_lidar.html) |
| 73 | [73_sensors_sensors_rtx_radar](73_sensors_sensors_rtx_radar/TUTORIAL.md) | RTX Radar Sensor | `standalone` | [t149](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_rtx_radar.html) |
| 74 | [74_sensors_sensors_rtx_materials](74_sensors_sensors_rtx_materials/TUTORIAL.md) | RTX Sensor Non-Visual Materials | `standalone` | [t148](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_rtx_materials.html) |
| 75 | [75_sensors_sensors_rtx_annotators](75_sensors_sensors_rtx_annotators/TUTORIAL.md) | RTX Sensor Annotators | `standalone` | [t150](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_rtx_annotators.html) |
| 76 | [76_sensors_rtx_motion_bvh](76_sensors_rtx_motion_bvh/TUTORIAL.md) | RTX Sensors | `standalone` | [t179](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_rtx.html) |
| 77 | [77_events_sensors_rtx_placement](77_events_sensors_rtx_placement/TUTORIAL.md) | RTX Sensors Placement and Calibration | `gui` | [t072](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/tutorial_sensors_rtx_placement.html) |
| 78 | [78_events_ext_sensors_rtx_placement_camera_placement](78_events_ext_sensors_rtx_placement_camera_placement/TUTORIAL.md) | Camera Placement | `gui` | [t073](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_sensors_rtx_placement/camera_placement.html) |
| 79 | [79_events_ext_sensors_rtx_placement_camera_calibration](79_events_ext_sensors_rtx_placement_camera_calibration/TUTORIAL.md) | Camera Calibration | `gui` | [t074](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_sensors_rtx_placement/camera_calibration.html) |

<a id="omnigraph_extensions"></a>

## 80–93 · OmniGraph와 확장 개발

그래프 연결과 Python 생성, 확장 등록·템플릿·대화형 예제를 익힌 뒤 Python/C++ custom node와 디버깅·프로파일링을 학습한다. 이후 ROS와 Replicator 사용자 노드의 기반이다.

분야별 실행 방식은 각 안내를 따릅니다. 이 단계만 검색: `python3 src/catalog.py list --stage omnigraph_extensions`

| 순서 | 패키지 / 한국어 실습 안내 | 공식 제목 | 실행 방식 | 출처 |
|---|---|---|---|---|
| 80 | [80_tools_omnigraph_tutorial](80_tools_omnigraph_tutorial/TUTORIAL.md) | Isaac Sim Omnigraph Tutorial | `gui` | [t109](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/omnigraph/omnigraph_tutorial.html) |
| 81 | [81_tools_omnigraph_shortcuts](81_tools_omnigraph_shortcuts/TUTORIAL.md) | Commonly Used Omnigraph Shortcuts | `gui` | [t106](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/omnigraph/omnigraph_shortcuts.html) |
| 82 | [82_tools_omnigraph_scripting](82_tools_omnigraph_scripting/TUTORIAL.md) | OmniGraph via Python Scripting Tutorial | `script_editor` | [t110](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/omnigraph/omnigraph_scripting.html) |
| 83 | [83_tools_updating_extensions](83_tools_updating_extensions/TUTORIAL.md) | Adding and Updating Extensions Guide | `extension` | [t172](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/utilities/updating_extensions.html) |
| 84 | [84_tools_extension_template_generator](84_tools_extension_template_generator/TUTORIAL.md) | Extension Template Generator | `extension` | [t164](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/utilities/extension_template_generator.html) |
| 85 | [85_tools_extension_templates_tutorial](85_tools_extension_templates_tutorial/TUTORIAL.md) | Extension Template Generator Explained | `extension` | [t165](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/utilities/extension_templates_tutorial.html) |
| 86 | [86_tools_custom_interactive_examples](86_tools_custom_interactive_examples/TUTORIAL.md) | Custom Interactive Examples | `extension` | [t163](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/utilities/custom_interactive_examples.html) |
| 87 | [87_tools_omnigraph_custom_python_nodes](87_tools_omnigraph_custom_python_nodes/TUTORIAL.md) | Custom Python Nodes | `extension` | [t107](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/omnigraph/omnigraph_custom_python_nodes.html) |
| 88 | [88_tools_vscode_extension_template_generator](88_tools_vscode_extension_template_generator/TUTORIAL.md) | Advanced Extension Template Generator from VS Code | `extension` | [t167](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/utilities/vscode_extension_template_generator.html) |
| 89 | [89_tools_custom_cpp_extensions](89_tools_custom_cpp_extensions/TUTORIAL.md) | Custom Extensions: C++ | `external` | [t166](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/utilities/custom_cpp_extensions.html) |
| 90 | [90_tools_omnigraph_custom_cpp_nodes](90_tools_omnigraph_custom_cpp_nodes/TUTORIAL.md) | Custom C++ Nodes | `external` | [t108](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/omnigraph/omnigraph_custom_cpp_nodes.html) |
| 91 | [91_tools_util_debug_draw](91_tools_util_debug_draw/TUTORIAL.md) | Debug Drawing Extension API | `script_editor` | [t168](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/utilities/debugging/ext_isaacsim_util_debug_draw.html) |
| 92 | [92_tools_advanced_python_debugging](92_tools_advanced_python_debugging/TUTORIAL.md) | Debugging With Visual Studio Code | `standalone` | [t170](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/utilities/debugging/tutorial_advanced_python_debugging.html) |
| 93 | [93_tools_profiling_performance](93_tools_profiling_performance/TUTORIAL.md) | Profiling Performance Using Tracy | `standalone` | [t171](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/utilities/debugging/profiling_performance.html) |

<a id="environments_behaviors"></a>

## 94–103 · 환경 구축과 로봇 행동

창고·컨베이어·Occupancy Map을 만들고 RMPflow와 확장 개발 경험을 Cortex의 의사결정·행동 예제에 적용한다. 지도 작성은 다음 ROS 내비게이션의 배경이 된다.

분야별 실행 방식은 각 안내를 따릅니다. 이 단계만 검색: `python3 src/catalog.py list --stage environments_behaviors`

| 순서 | 패키지 / 한국어 실습 안내 | 공식 제목 | 실행 방식 | 출처 |
|---|---|---|---|---|
| 94 | [94_digital_twin_static_assets](94_digital_twin_static_assets/TUTORIAL.md) | Static Warehouse Assets | `script_editor` | [t079](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/digital_twin/warehouse_logistics/tutorial_static_assets.html) |
| 95 | [95_digital_twin_ext_omni_warehouse_creator](95_digital_twin_ext_omni_warehouse_creator/TUTORIAL.md) | Warehouse Creator Extension | `gui` | [t077](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/digital_twin/warehouse_logistics/ext_omni_warehouse_creator.html) |
| 96 | [96_digital_twin_asset_gen_conveyor](96_digital_twin_asset_gen_conveyor/TUTORIAL.md) | Conveyor Belt Utility | `gui` | [t078](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/digital_twin/warehouse_logistics/ext_isaacsim_asset_gen_conveyor.html) |
| 97 | [97_digital_twin_asset_generator_occupancy_map](97_digital_twin_asset_generator_occupancy_map/TUTORIAL.md) | Mapping | `gui` | [t087](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/digital_twin/ext_isaacsim_asset_generator_occupancy_map.html) |
| 98 | [98_digital_twin_cortex_1_overview](98_digital_twin_cortex_1_overview/TUTORIAL.md) | Isaac Cortex: Overview | `standalone` | [t081](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/cortex_tutorials/tutorial_cortex_1_overview.html) |
| 99 | [99_digital_twin_cortex_2_decider_networks](99_digital_twin_cortex_2_decider_networks/TUTORIAL.md) | Decider networks | `standalone` | [t082](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/cortex_tutorials/tutorial_cortex_2_decider_networks.html) |
| 100 | [100_digital_twin_cortex_3_example_peck_games](100_digital_twin_cortex_3_example_peck_games/TUTORIAL.md) | Behavior Examples: Peck Games | `standalone` | [t083](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/cortex_tutorials/tutorial_cortex_3_example_peck_games.html) |
| 101 | [101_digital_twin_cortex_4_franka_block_stacking](101_digital_twin_cortex_4_franka_block_stacking/TUTORIAL.md) | Walkthrough: Franka Block Stacking | `standalone` | [t084](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/cortex_tutorials/tutorial_cortex_4_franka_block_stacking.html) |
| 102 | [102_digital_twin_cortex_5_ur10_bin_stacking](102_digital_twin_cortex_5_ur10_bin_stacking/TUTORIAL.md) | Walkthrough: UR10 Bin Stacking | `standalone` | [t085](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/cortex_tutorials/tutorial_cortex_5_ur10_bin_stacking.html) |
| 103 | [103_digital_twin_cortex_7_cortex_extension](103_digital_twin_cortex_7_cortex_extension/TUTORIAL.md) | Building Cortex Based Extensions | `extension` | [t086](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/cortex_tutorials/tutorial_cortex_7_cortex_extension.html) |

<a id="ros2_basics"></a>

## 104–121 · ROS 2 연결과 기본 통신

TurtleBot 제어와 시계·TF·통신 설정을 익히고 카메라·Lidar·관절 제어를 연결한 뒤 standalone·launch·simulation control을 실습한다.

분야별 실행 방식은 각 안내를 따릅니다. 이 단계만 검색: `python3 src/catalog.py list --stage ros2_basics`

| 순서 | 패키지 / 한국어 실습 안내 | 공식 제목 | 실행 방식 | 출처 |
|---|---|---|---|---|
| 104 | [104_ros2_ros2_turtlebot](104_ros2_ros2_turtlebot/TUTORIAL.md) | URDF Import: Turtlebot | `gui` | [t007](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_turtlebot.html) |
| 105 | [105_ros2_ros2_drive_turtlebot](105_ros2_ros2_drive_turtlebot/TUTORIAL.md) | Driving TurtleBot using ROS 2 Messages | `ros2` | [t008](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_drive_turtlebot.html) |
| 106 | [106_ros2_ros2_clock](106_ros2_ros2_clock/TUTORIAL.md) | ROS 2 Clock | `ros2` | [t009](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_clock.html) |
| 107 | [107_ros2_ros2_rtf](107_ros2_ros2_rtf/TUTORIAL.md) | ROS 2 Publish Real Time Factor (RTF) | `ros2` | [t010](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_rtf.html) |
| 108 | [108_ros2_ros2_tf](108_ros2_ros2_tf/TUTORIAL.md) | ROS2 Transform Trees and Odometry | `gui` | [t015](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_tf.html) |
| 109 | [109_ros2_ros2_publish_rate](109_ros2_ros2_publish_rate/TUTORIAL.md) | ROS2 Setting Publish Rates | `script_editor` | [t016](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_publish_rate.html) |
| 110 | [110_ros2_ros2_qos](110_ros2_ros2_qos/TUTORIAL.md) | ROS 2 Quality of Service (QoS) | `gui` | [t017](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_qos.html) |
| 111 | [111_ros2_ros2_name_override](111_ros2_ros2_name_override/TUTORIAL.md) | NameOverride Attribute | `ros2` | [t019](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_name_override.html) |
| 112 | [112_ros2_ros2_auto_namespace](112_ros2_ros2_auto_namespace/TUTORIAL.md) | Automatic ROS 2 Namespace Generation | `script_editor` | [t021](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_auto_namespace.html) |
| 113 | [113_ros2_ros2_camera](113_ros2_ros2_camera/TUTORIAL.md) | ROS 2 Cameras | `ros2` | [t011](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_camera.html) |
| 114 | [114_ros2_ros2_camera_publishing](114_ros2_ros2_camera_publishing/TUTORIAL.md) | Publishing Camera’s Data | `ros2` | [t013](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_camera_publishing.html) |
| 115 | [115_ros2_ros2_camera_noise](115_ros2_ros2_camera_noise/TUTORIAL.md) | Add Noise to Camera | `ros2` | [t012](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_camera_noise.html) |
| 116 | [116_ros2_ros2_rtx_lidar](116_ros2_ros2_rtx_lidar/TUTORIAL.md) | RTX Lidar Sensors | `ros2` | [t014](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_rtx_lidar.html) |
| 117 | [117_ros2_ros2_manipulation](117_ros2_ros2_manipulation/TUTORIAL.md) | ROS2 Joint Control: Extension Python Scripting | `ros2` | [t018](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_manipulation.html) |
| 118 | [118_ros2_ros2_ackermann_controller](118_ros2_ros2_ackermann_controller/TUTORIAL.md) | ROS 2 Ackermann Controller | `script_editor` | [t020](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_ackermann_controller.html) |
| 119 | [119_ros2_ros2_python](119_ros2_ros2_python/TUTORIAL.md) | ROS 2 Bridge in Standalone Workflow | `standalone` | [t022](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_python.html) |
| 120 | [120_ros2_ros2_launch](120_ros2_ros2_launch/TUTORIAL.md) | ROS 2 Launch | `ros2` | [t033](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_launch.html) |
| 121 | [121_ros2_ros2_simulation_control](121_ros2_ros2_simulation_control/TUTORIAL.md) | ROS2 Simulation Control | `ros2` | [t034](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_simulation_control.html) |

<a id="ros2_applications"></a>

## 122–131 · ROS 2 응용과 사용자 인터페이스

내비게이션·다중 로봇·MoveIt을 적용한 뒤 generic topic/service, 사용자 메시지, Python/C++ OmniGraph 노드를 구현한다.

분야별 실행 방식은 각 안내를 따릅니다. 이 단계만 검색: `python3 src/catalog.py list --stage ros2_applications`

| 순서 | 패키지 / 한국어 실습 안내 | 공식 제목 | 실행 방식 | 출처 |
|---|---|---|---|---|
| 122 | [122_ros2_ros2_navigation](122_ros2_ros2_navigation/TUTORIAL.md) | ROS 2 Navigation | `gui` | [t023](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_navigation.html) |
| 123 | [123_ros2_ros2_multi_navigation](123_ros2_ros2_multi_navigation/TUTORIAL.md) | Multiple Robot ROS2 Navigation | `gui` | [t024](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_multi_navigation.html) |
| 124 | [124_ros2_ros2_navigation_block_world](124_ros2_ros2_navigation_block_world/TUTORIAL.md) | ROS 2 Navigation with Block World Generator | `gui` | [t025](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_navigation_block_world.html) |
| 125 | [125_ros2_ros2_moveit](125_ros2_ros2_moveit/TUTORIAL.md) | MoveIt 2 | `gui` | [t026](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_moveit.html) |
| 126 | [126_ros2_ros2_generic_publisher_subscriber](126_ros2_ros2_generic_publisher_subscriber/TUTORIAL.md) | ROS 2 Generic Publisher and Subscriber | `script_editor` | [t027](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_generic_publisher_subscriber.html) |
| 127 | [127_ros2_ros2_generic_server_client](127_ros2_ros2_generic_server_client/TUTORIAL.md) | ROS 2 Generic Server and Client | `script_editor` | [t028](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_generic_server_client.html) |
| 128 | [128_ros2_ros2_prim_service](128_ros2_ros2_prim_service/TUTORIAL.md) | ROS 2 Service for Manipulating Prims Attributes | `script_editor` | [t029](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_prim_service.html) |
| 129 | [129_ros2_ros2_custom_message_python](129_ros2_ros2_custom_message_python/TUTORIAL.md) | ROS 2 Python Custom Messages | `standalone` | [t030](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_custom_message_python.html) |
| 130 | [130_ros2_ros2_custom_omnigraph_node_python](130_ros2_ros2_custom_omnigraph_node_python/TUTORIAL.md) | ROS 2 Python Custom OmniGraph Node | `extension` | [t031](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_custom_omnigraph_node_python.html) |
| 131 | [131_ros2_ros2_omnigraph_cpp_node](131_ros2_ros2_omnigraph_cpp_node/TUTORIAL.md) | ROS 2 Custom C++ OmniGraph Node | `external` | [t032](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_omnigraph_cpp_node.html) |

<a id="replicator"></a>

## 132–143 · Replicator 합성 데이터 기초와 확장

의미 라벨과 Recorder부터 스크립트·무작위화·캡처 시점·장면 및 물체 데이터셋을 익히고 증강·사용자 노드·행동 스크립트·로봇 응용으로 확장한다.

분야별 실행 방식은 각 안내를 따릅니다. 이 단계만 검색: `python3 src/catalog.py list --stage replicator`

| 순서 | 패키지 / 한국어 실습 안내 | 공식 제목 | 실행 방식 | 출처 |
|---|---|---|---|---|
| 132 | [132_replicator_replicator_overview](132_replicator_replicator_overview/TUTORIAL.md) | Overview | `standalone` | [t035](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_overview.html) |
| 133 | [133_replicator_replicator_recorder](133_replicator_replicator_recorder/TUTORIAL.md) | Synthetic Data Recorder | `standalone` | [t036](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_recorder.html) |
| 134 | [134_replicator_replicator_getting_started](134_replicator_replicator_getting_started/TUTORIAL.md) | Getting Started Scripts | `standalone` | [t037](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_getting_started.html) |
| 135 | [135_replicator_replicator_isaac_randomizers](135_replicator_replicator_isaac_randomizers/TUTORIAL.md) | Randomization Snippets | `standalone` | [t047](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_isaac_randomizers.html) |
| 136 | [136_replicator_replicator_isaac_snippets](136_replicator_replicator_isaac_snippets/TUTORIAL.md) | Useful Snippets | `standalone` | [t048](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_isaac_snippets.html) |
| 137 | [137_replicator_replicator_scene_based_sdg](137_replicator_replicator_scene_based_sdg/TUTORIAL.md) | Scene Based Synthetic Dataset Generation | `standalone` | [t038](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_scene_based_sdg.html) |
| 138 | [138_replicator_replicator_object_based_sdg](138_replicator_replicator_object_based_sdg/TUTORIAL.md) | Object Based Synthetic Dataset Generation | `standalone` | [t039](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_object_based_sdg.html) |
| 139 | [139_replicator_replicator_augmentation](139_replicator_replicator_augmentation/TUTORIAL.md) | Data Augmentation | `standalone` | [t044](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_augmentation.html) |
| 140 | [140_replicator_replicator_custom_og_randomizer](140_replicator_replicator_custom_og_randomizer/TUTORIAL.md) | Custom Replicator Randomization Nodes | `standalone` | [t045](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_custom_og_randomizer.html) |
| 141 | [141_replicator_replicator_modular_scripting](141_replicator_replicator_modular_scripting/TUTORIAL.md) | Modular Behavior Scripting | `standalone` | [t046](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_modular_scripting.html) |
| 142 | [142_replicator_replicator_amr_navigation](142_replicator_replicator_amr_navigation/TUTORIAL.md) | Randomization in Simulation – AMR Navigation | `standalone` | [t041](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_amr_navigation.html) |
| 143 | [143_replicator_replicator_ur10_palletizing](143_replicator_replicator_ur10_palletizing/TUTORIAL.md) | Randomization in Simulation – UR10 Palletizing | `standalone` | [t042](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_ur10_palletizing.html) |

<a id="object_sdg"></a>

## 144–155 · 물체 시뮬레이션과 YAML 무작위화

IRO 전체 실행에서 설정·Mutable·카메라·기하·조명·속성·변환을 익히고 Harmonizer·Macro·분포·의존 무작위화로 나아간다.

분야별 실행 방식은 각 안내를 따릅니다. 이 단계만 검색: `python3 src/catalog.py list --stage object_sdg`

| 순서 | 패키지 / 한국어 실습 안내 | 공식 제목 | 실행 방식 | 출처 |
|---|---|---|---|---|
| 144 | [144_events_replicator_object](144_events_replicator_object/TUTORIAL.md) | Object Simulation and Synthetic Data Generation | `extension` | [t058](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/tutorial_replicator_object.html) |
| 145 | [145_events_ext_replicator_object_setting](145_events_ext_replicator_object_setting/TUTORIAL.md) | Setting | `extension` | [t059](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_replicator-object/setting.html) |
| 146 | [146_events_ext_replicator_object_mutable](146_events_ext_replicator_object_mutable/TUTORIAL.md) | Mutable | `extension` | [t060](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_replicator-object/mutable.html) |
| 147 | [147_events_ext_replicator_object_camera](147_events_ext_replicator_object_camera/TUTORIAL.md) | Camera | `extension` | [t061](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_replicator-object/camera.html) |
| 148 | [148_events_ext_replicator_object_geometry](148_events_ext_replicator_object_geometry/TUTORIAL.md) | Geometry | `extension` | [t062](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_replicator-object/geometry.html) |
| 149 | [149_events_ext_replicator_object_light](149_events_ext_replicator_object_light/TUTORIAL.md) | Light | `extension` | [t063](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_replicator-object/light.html) |
| 150 | [150_events_ext_replicator_object_mutable_attribute](150_events_ext_replicator_object_mutable_attribute/TUTORIAL.md) | Mutable Attribute | `extension` | [t064](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_replicator-object/mutable_attribute.html) |
| 151 | [151_events_ext_replicator_object_transformation](151_events_ext_replicator_object_transformation/TUTORIAL.md) | Transformation | `extension` | [t065](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_replicator-object/transformation.html) |
| 152 | [152_events_ext_replicator_object_harmonizer](152_events_ext_replicator_object_harmonizer/TUTORIAL.md) | Harmonizer | `extension` | [t066](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_replicator-object/harmonizer.html) |
| 153 | [153_events_ext_replicator_object_macro](153_events_ext_replicator_object_macro/TUTORIAL.md) | Macro | `extension` | [t067](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_replicator-object/macro.html) |
| 154 | [154_events_ext_replicator_object_distribution_visualizer](154_events_ext_replicator_object_distribution_visualizer/TUTORIAL.md) | Distribution Visualizer | `gui` | [t068](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_replicator-object/distribution_visualizer.html) |
| 155 | [155_events_ext_replicator_object_randomization_dependency](155_events_ext_replicator_object_randomization_dependency/TUTORIAL.md) | Randomization Dependency: Incremental Examples | `extension` | [t069](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_replicator-object/randomization_dependency.html) |

<a id="actor_events"></a>

## 156–161 · 액터와 공간 이벤트 데이터

액터 실행부터 동작·카메라·Writer·사용자 설정을 익히고 물리 공간의 사건 시나리오로 연결한다.

분야별 실행 방식은 각 안내를 따릅니다. 이 단계만 검색: `python3 src/catalog.py list --stage actor_events`

| 순서 | 패키지 / 한국어 실습 안내 | 공식 제목 | 실행 방식 | 출처 |
|---|---|---|---|---|
| 156 | [156_events_replicator_agent](156_events_replicator_agent/TUTORIAL.md) | Actor Simulation and Synthetic Data Generation | `gui` | [t053](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/tutorial_replicator_agent.html) |
| 157 | [157_events_ext_replicator_agent_actor_control](157_events_ext_replicator_agent_actor_control/TUTORIAL.md) | Actor Control | `gui` | [t054](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_replicator-agent/actor_control.html) |
| 158 | [158_events_ext_replicator_agent_camera_control](158_events_ext_replicator_agent_camera_control/TUTORIAL.md) | Camera Control | `gui` | [t055](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_replicator-agent/camera_control.html) |
| 159 | [159_events_ext_replicator_agent_writer_control](159_events_ext_replicator_agent_writer_control/TUTORIAL.md) | Writer Control | `gui` | [t056](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_replicator-agent/writer_control.html) |
| 160 | [160_events_ext_replicator_agent_customization](160_events_ext_replicator_agent_customization/TUTORIAL.md) | Customization | `gui` | [t057](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_replicator-agent/customization.html) |
| 161 | [161_events_replicator_incident](161_events_replicator_incident/TUTORIAL.md) | Physical Space Event Generation | `gui` | [t071](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/tutorial_replicator_incident.html) |

<a id="policies_scaling"></a>

## 162–167 · 병렬 환경과 학습 정책 활용

Instanceable 자산과 Cloner를 익히고 이미 학습된 정책 예제, 정책 배포, ROS 제어, MobilityGen 궤적 기록·재렌더링을 연결한다.

분야별 실행 방식은 각 안내를 따릅니다. 이 단계만 검색: `python3 src/catalog.py list --stage policies_scaling`

| 순서 | 패키지 / 한국어 실습 안내 | 공식 제목 | 실행 방식 | 출처 |
|---|---|---|---|---|
| 162 | [162_motion_instanceable_assets](162_motion_instanceable_assets/TUTORIAL.md) | Instanceable Assets | `standalone` | [t006](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/isaac_lab_tutorials/tutorial_instanceable_assets.html) |
| 163 | [163_motion_cloner](163_motion_cloner/TUTORIAL.md) | Getting Started with Cloner | `standalone` | [t005](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/isaac_lab_tutorials/tutorial_cloner.html) |
| 164 | [164_motion_robot_policy_example](164_motion_robot_policy_example/TUTORIAL.md) | Reinforcement Learning Policies Examples in Isaac Sim | `standalone` | [t144](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_simulation/ext_isaacsim_robot_policy_example.html) |
| 165 | [165_motion_policy_deployment](165_motion_policy_deployment/TUTORIAL.md) | Deploying Policies in Isaac Sim | `standalone` | [t003](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/isaac_lab_tutorials/tutorial_policy_deployment.html) |
| 166 | [166_ros2_ros2_rl_controller](166_ros2_ros2_rl_controller/TUTORIAL.md) | Running a Reinforcement Learning Policy through ROS 2 and Isaac Sim | `gui` | [t004](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_rl_controller.html) |
| 167 | [167_sdg_extra_replicator_mobility_gen](167_sdg_extra_replicator_mobility_gen/TUTORIAL.md) | Data Generation with MobilityGen | `gui` | [t076](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/synthetic_data_generation/tutorial_replicator_mobility_gen.html) |

<a id="advanced_integrations"></a>

## 168–174 · 고급 데이터 생성과 외부 시스템 통합

집기 평가에서 Infinigen·Cosmos·VLM 데이터 흐름, NuRec 장면, cuRobo·cuMotion과 cuOpt 서비스로 넓힌다. 별도 데이터·모델·설치·서비스가 필요한 통합 실습을 뒤에 둔다.

분야별 실행 방식은 각 안내를 따릅니다. 이 단계만 검색: `python3 src/catalog.py list --stage advanced_integrations`

| 순서 | 패키지 / 한국어 실습 안내 | 공식 제목 | 실행 방식 | 출처 |
|---|---|---|---|---|
| 168 | [168_sdg_extra_replicator_grasping_sdg](168_sdg_extra_replicator_grasping_sdg/TUTORIAL.md) | Grasping Synthetic Data Generation | `standalone` | [t075](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/synthetic_data_generation/tutorial_replicator_grasping_sdg.html) |
| 169 | [169_replicator_replicator_infinigen_sdg](169_replicator_replicator_infinigen_sdg/TUTORIAL.md) | Environment Based Synthetic Dataset Generation with Infinigen | `external` | [t040](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_infinigen_sdg.html) |
| 170 | [170_replicator_replicator_cosmos](170_replicator_replicator_cosmos/TUTORIAL.md) | Cosmos Synthetic Data Generation | `standalone` | [t043](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_cosmos.html) |
| 171 | [171_events_replicator_caption](171_events_replicator_caption/TUTORIAL.md) | VLM Scene Captioning | `script_editor` | [t070](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/tutorial_replicator_caption.html) |
| 172 | [172_digital_twin_nurec_navigation](172_digital_twin_nurec_navigation/TUTORIAL.md) | Neural Volume Rendering | `standalone` | [t178](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/assets/usd_assets_nurec.html) |
| 173 | [173_motion_manipulators_curobo](173_motion_manipulators_curobo/TUTORIAL.md) | cuRobo and cuMotion | `external` | [t141](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/manipulators/manipulators_curobo.html) |
| 174 | [174_digital_twin_logistics_tutorial_cuopt](174_digital_twin_logistics_tutorial_cuopt/TUTORIAL.md) | NVIDIA cuOpt | `gui` | [t080](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/digital_twin/warehouse_logistics/logistics_tutorial_cuopt.html) |

<a id="legacy_reference"></a>

## 175–179 · 사용 중단 문서와 레거시 참고

공식 원문이 deprecated로 표시된 ShapeNet·SceneBlox·온라인 생성·Pose Estimation 생성 및 학습을 마지막 참고 과정으로 둔다. ShapeNet 실습 자체는 현재 OBJ→USD 변환 경로를 사용한다.

분야별 실행 방식은 각 안내를 따릅니다. 이 단계만 검색: `python3 src/catalog.py list --stage legacy_reference`

| 순서 | 패키지 / 한국어 실습 안내 | 공식 제목 | 실행 방식 | 출처 |
|---|---|---|---|---|
| 175 | [175_importers_shapenet_importer](175_importers_shapenet_importer/TUTORIAL.md) | Tutorial: ShapeNet Importer | `standalone` | [t114](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/importer_exporter/shapenet_importer.html) |
| 176 | [176_replicator_replicator_sceneblox](176_replicator_replicator_sceneblox/TUTORIAL.md) | Scene Generation with SceneBlox | `standalone` | [t052](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_sceneblox.html) |
| 177 | [177_replicator_replicator_online_generation](177_replicator_replicator_online_generation/TUTORIAL.md) | Online Generation | `external` | [t049](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_online_generation.html) |
| 178 | [178_replicator_replicator_pose_estimation](178_replicator_replicator_pose_estimation/TUTORIAL.md) | Pose Estimation Synthetic Data Generation | `standalone` | [t050](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_pose_estimation.html) |
| 179 | [179_replicator_replicator_training_pose_estimation_model](179_replicator_replicator_training_pose_estimation_model/TUTORIAL.md) | Training Pose Estimation Model with Synthetic Data | `external` | [t051](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_training_pose_estimation_model.html) |

