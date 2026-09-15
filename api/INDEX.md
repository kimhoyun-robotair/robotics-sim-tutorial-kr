# API 색인

[읽는 방법](00_README.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

180개 튜토리얼에서 확인한 **154개 API 항목**이다. 첫 등장 튜토리얼의 숫자 순이며, 앞의 번호는 API 문서 번호이다.

| API 번호 | API | 첫 튜토리얼 | 짧은 설명 |
|---|---|---|---|
| 001 | [isaacsim.SimulationApp](001_SimulationApp.md) | [00](../src/00_core_quickstart_isaacsim/TUTORIAL.md) | Python 스크립트에서 Isaac Sim 애플리케이션을 시작하고 프레임 갱신과 종료를 관리하는 클래스이다. |
| 002 | [omni.usd](002_omni.usd.md) | [00](../src/00_core_quickstart_isaacsim/TUTORIAL.md) | Isaac Sim에서 현재 열린 USD Stage를 가져오고 장면의 로딩·선택 상태를 관리한다. |
| 003 | [isaacsim.core.api.World](003_isaacsim.core.api.World.md) | [00](../src/00_core_quickstart_isaacsim/TUTORIAL.md) | 장면의 객체와 작업을 관리하면서 물리·렌더링 시뮬레이션을 진행하는 클래스이다. |
| 004 | [isaacsim.core.api.objects](004_isaacsim.core.api.objects.md) | [00](../src/00_core_quickstart_isaacsim/TUTORIAL.md) | 위치·크기·색상 등을 지정해 튜토리얼에 필요한 기본 도형을 만드는 클래스 모음이다. |
| 005 | [isaacsim.core.prims](005_isaacsim.core.prims.md) | [00](../src/00_core_quickstart_isaacsim/TUTORIAL.md) | USD Prim을 감싸 위치·강체·충돌·관절 상태를 Python에서 다루는 클래스 모음이다. |
| 006 | [isaacsim.core.utils.rotations](006_isaacsim.core.utils.rotations.md) | [00](../src/00_core_quickstart_isaacsim/TUTORIAL.md) | 오일러 각과 쿼터니언 사이에서 회전 표현을 변환하는 함수 모음이다. |
| 007 | [isaacsim.core.utils.viewports](007_isaacsim.core.utils.viewports.md) | [00](../src/00_core_quickstart_isaacsim/TUTORIAL.md) | Isaac Sim 화면에서 장면을 바라보는 카메라 시점을 설정하는 유틸리티이다. |
| 008 | [pxr.Gf](008_pxr.Gf.md) | [00](../src/00_core_quickstart_isaacsim/TUTORIAL.md) | USD 속성에 넣을 위치·색상·회전 값과 좌표 변환 계산을 위한 수학 타입이다. |
| 009 | [pxr.UsdGeom](009_pxr.UsdGeom.md) | [00](../src/00_core_quickstart_isaacsim/TUTORIAL.md) | USD 형상·카메라를 만들고 위치·회전·크기와 장면의 좌표 기준을 다룬다. |
| 010 | [pxr.UsdLux](010_pxr.UsdLux.md) | [00](../src/00_core_quickstart_isaacsim/TUTORIAL.md) | 장면과 센서 영상에 필요한 USD 조명을 만들고 밝기·색상·방향을 설정한다. |
| 011 | [isaacsim.core.api.scenes.Scene](011_isaacsim.core.api.scenes.Scene.md) | [00](../src/00_core_quickstart_isaacsim/TUTORIAL.md) | World 안의 시뮬레이션 객체를 이름으로 등록하고 찾아 사용하는 장면 관리 클래스이다. |
| 012 | [pxr.Sdf](012_pxr.Sdf.md) | [00](../src/00_core_quickstart_isaacsim/TUTORIAL.md) | USD 파일의 레이어, prim 경로와 속성 자료형을 다루는 기반 API이다. |
| 013 | [pxr.Usd](013_pxr.Usd.md) | [00](../src/00_core_quickstart_isaacsim/TUTORIAL.md) | USD Stage를 열거나 만들고 prim·속성·참조·variant와 편집 대상을 다룬다. |
| 014 | [isaacsim.core.api.objects.ground_plane](014_isaacsim.core.api.objects.ground_plane.md) | [00](../src/00_core_quickstart_isaacsim/TUTORIAL.md) | 물체와 충돌하는 평평한 지면을 만드는 GroundPlane 클래스를 제공하는 모듈이다. |
| 015 | [isaacsim.core.api.robots](015_isaacsim.core.api.robots.md) | [02](../src/02_core_core_hello_robot/TUTORIAL.md) | USD 장면에 있는 로봇을 감싸 관절 정보와 자세를 읽고 제어하는 Robot 클래스를 제공한다. |
| 016 | [isaacsim.core.utils.stage](016_isaacsim.core.utils.stage.md) | [02](../src/02_core_core_hello_robot/TUTORIAL.md) | USD Stage를 만들거나 열고, 기존 USD 파일을 현재 장면에 참조로 추가하는 함수 모음이다. |
| 017 | [isaacsim.core.utils.nucleus](017_isaacsim.core.utils.nucleus.md) | [02](../src/02_core_core_hello_robot/TUTORIAL.md) | 초기 Core 튜토리얼에서 Isaac Sim 에셋 루트 경로를 찾을 때 사용하는 import 경로이다. |
| 018 | [isaacsim.core.utils.types](018_isaacsim.core.utils.types.md) | [02](../src/02_core_core_hello_robot/TUTORIAL.md) | 로봇 제어에 전달할 관절 명령을 묶는 자료형을 제공하는 모듈이다. |
| 019 | [isaacsim.robot.wheeled_robots.robots](019_isaacsim.robot.wheeled_robots.robots.md) | [02](../src/02_core_core_hello_robot/TUTORIAL.md) | 바퀴 관절을 지정해 이동 로봇을 다룹니다. |
| 020 | [isaacsim.core.api.controllers.ArticulationController](020_isaacsim.core.api.controllers.ArticulationController.md) | [02](../src/02_core_core_hello_robot/TUTORIAL.md) | ArticulationAction에 담긴 관절 명령을 로봇의 관절 구조에 적용하는 제어기이다. |
| 021 | [isaacsim.storage.native](021_isaacsim.storage.native.md) | [03](../src/03_core_quickstart_isaacsim_robot/TUTORIAL.md) | Isaac Sim 기본 에셋이 저장된 위치를 조회하는 스토리지 유틸리티이다. |
| 022 | [omni.kit.app](022_omni.kit.app.md) | [05](../src/05_python_usd_python_scripting_concepts/TUTORIAL.md) | Isaac Sim을 실행하는 Kit 앱의 업데이트와 확장 관리 인터페이스에 접근한다. |
| 023 | [isaacsim.core.utils.extensions](023_isaacsim.core.utils.extensions.md) | [06](../src/06_python_usd_manual_standalone_python/TUTORIAL.md) | Isaac Sim 확장을 코드에서 활성화하고 설치 경로를 찾는 함수 모음이다. |
| 024 | [omni.kit.commands](024_omni.kit.commands.md) | [06](../src/06_python_usd_manual_standalone_python/TUTORIAL.md) | 등록된 명령을 이름으로 실행해 장면 편집, 로봇 가져오기, 센서 생성을 수행한다. |
| 025 | [omni.timeline](025_omni.timeline.md) | [06](../src/06_python_usd_manual_standalone_python/TUTORIAL.md) | 시뮬레이션의 재생 상태와 현재 시간을 제어하는 타임라인 인터페이스다. |
| 026 | [pxr.PhysicsSchemaTools](026_pxr.PhysicsSchemaTools.md) | [06](../src/06_python_usd_manual_standalone_python/TUTORIAL.md) | USD 장면에 물체를 받칠 지면을 만드는 물리 스키마 보조 도구이다. |
| 027 | [pxr.PhysxSchema](027_pxr.PhysxSchema.md) | [06](../src/06_python_usd_manual_standalone_python/TUTORIAL.md) | USD 물리 객체에 PhysX 전용 시뮬레이션 설정을 추가하거나 조회한다. |
| 028 | [pxr.UsdPhysics](028_pxr.UsdPhysics.md) | [06](../src/06_python_usd_manual_standalone_python/TUTORIAL.md) | 강체·충돌체·질량·관절 같은 물리 구조를 USD prim에 정의하고 검사한다. |
| 029 | [isaacsim.asset.importer.urdf](029_isaacsim.asset.importer.urdf.md) | [06](../src/06_python_usd_manual_standalone_python/TUTORIAL.md) | URDF를 가져올 설정과 관절 구동 방식을 지정합니다. |
| 030 | [isaacsim.core.api.physics_context.PhysicsContext](030_isaacsim.core.api.physics_context.PhysicsContext.md) | [09](../src/09_python_usd_core_api_overview/TUTORIAL.md) | World가 사용하는 물리 장면과 PhysX 설정에 접근하는 클래스이다. |
| 031 | [pxr.UsdShade](031_pxr.UsdShade.md) | [10](../src/10_python_usd_open_usd/TUTORIAL.md) | USD 재질과 셰이더를 만들고 물체에 연결한다. |
| 032 | [pxr.UsdUtils](032_pxr.UsdUtils.md) | [12](../src/12_python_usd_usd_tools/TUTORIAL.md) | USD 파일의 에셋 경로를 일괄 수정할 때 사용하는 보조 API이다. |
| 033 | [omni.kit.actions.core](033_omni.kit.actions.core.md) | [13](../src/13_python_usd_omniverse_tools/TUTORIAL.md) | 확장 ID와 액션 ID로 Python 동작을 등록하고 실행한다. |
| 034 | [omni.kit.undo](034_omni.kit.undo.md) | [13](../src/13_python_usd_omniverse_tools/TUTORIAL.md) | Kit 명령으로 만든 편집 이력을 되돌리거나 다시 적용한다. |
| 035 | [carb.settings](035_carb.settings.md) | [15](../src/15_tools_carb_settings/TUTORIAL.md) | 경로 형태의 키로 Isaac Sim과 확장의 실행 설정을 읽고 쓴다. |
| 036 | [omni.ext](036_omni.ext.md) | [15](../src/15_tools_carb_settings/TUTORIAL.md) | Python 확장의 시작과 종료 동작을 구현하는 기본 인터페이스를 제공한다. |
| 037 | [carb](037_carb.md) | [16](../src/16_python_usd_environment_setup/TUTORIAL.md) | Isaac Sim 기반 런타임의 로그 함수와 숫자 자료형을 사용한다. |
| 038 | [isaacsim.core.api.materials](038_isaacsim.core.api.materials.md) | [16](../src/16_python_usd_environment_setup/TUTORIAL.md) | 물체의 접촉 특성과 화면에 보이는 외형을 설정할 재질 클래스를 제공한다. |
| 039 | [isaacsim.core.utils.semantics](039_isaacsim.core.utils.semantics.md) | [16](../src/16_python_usd_environment_setup/TUTORIAL.md) | 합성 데이터와 인식 결과에 사용할 물체의 의미 라벨을 붙이거나 정리하는 함수 모음이다. |
| 040 | [omni.physx](040_omni.physx.md) | [16](../src/16_python_usd_environment_setup/TUTORIAL.md) | 실행 중인 PhysX 장면에 질의하거나 물리 스텝 이벤트를 구독한다. |
| 041 | [omni.kit.asset_converter](041_omni.kit.asset_converter.md) | [16](../src/16_python_usd_environment_setup/TUTORIAL.md) | 로컬 OBJ 메시를 USD 파일로 변환하는 비동기 작업을 만든다. |
| 042 | [isaacsim.ros2.bridge](042_isaacsim.ros2.bridge.md) | [17](../src/17_python_usd_util_snippets/TUTORIAL.md) | Isaac Sim의 로봇·센서·시뮬레이션 시간을 ROS 2 토픽과 서비스에 연결한다. |
| 043 | [isaacsim.util.debug_draw](043_isaacsim.util.debug_draw.md) | [17](../src/17_python_usd_util_snippets/TUTORIAL.md) | 뷰포트에 점, 선, 곡선을 그려 확인합니다. |
| 044 | [omni.kit.viewport.utility](044_omni.kit.viewport.utility.md) | [17](../src/17_python_usd_util_snippets/TUTORIAL.md) | 현재 활성 Viewport를 가져와 카메라와 렌더링 출력을 연결한다. |
| 045 | [omni.kit.widget.viewport.api.ViewportAPI](045_omni.kit.widget.viewport.api.ViewportAPI.md) | [17](../src/17_python_usd_util_snippets/TUTORIAL.md) | 활성 viewport의 렌더 해상도·카메라·render product를 다루는 객체이다. |
| 046 | [isaacsim.core.api.controllers](046_isaacsim.core.api.controllers.md) | [23](../src/23_core_core_adding_controller/TUTORIAL.md) | 사용자 정의 제어기를 작성할 때 상속하는 BaseController 클래스를 제공하는 모듈이다. |
| 047 | [isaacsim.robot.wheeled_robots.controllers](047_isaacsim.robot.wheeled_robots.controllers.md) | [23](../src/23_core_core_adding_controller/TUTORIAL.md) | 이동 목표를 바퀴 속도 명령으로 바꿉니다. |
| 048 | [isaacsim.robot.manipulators.examples.franka.tasks](048_isaacsim.robot.manipulators.examples.franka.tasks.md) | [24](../src/24_core_core_adding_manipulator/TUTORIAL.md) | Franka용 집기와 목표 추종 작업을 구성합니다. |
| 049 | [isaacsim.robot.manipulators.examples.franka.controllers](049_isaacsim.robot.manipulators.examples.franka.controllers.md) | [24](../src/24_core_core_adding_manipulator/TUTORIAL.md) | Franka의 물체 집기·옮기기 순서를 제어합니다. |
| 050 | [isaacsim.robot.manipulators.grippers](050_isaacsim.robot.manipulators.grippers.md) | [24](../src/24_core_core_adding_manipulator/TUTORIAL.md) | 평행 그리퍼의 손가락 관절을 제어합니다. |
| 051 | [isaacsim.core.api.tasks](051_isaacsim.core.api.tasks.md) | [24](../src/24_core_core_adding_manipulator/TUTORIAL.md) | 로봇과 물체 배치, 관측값, 매 스텝 처리 등을 작업 단위로 구성하는 BaseTask를 제공한다. |
| 052 | [isaacsim.robot.manipulators.examples.franka](052_isaacsim.robot.manipulators.examples.franka.md) | [24](../src/24_core_core_adding_manipulator/TUTORIAL.md) | Franka 로봇과 기본 그리퍼를 생성합니다. |
| 053 | [isaacsim.core.utils.prims](053_isaacsim.core.utils.prims.md) | [25](../src/25_core_core_adding_multiple_robots/TUTORIAL.md) | USD Prim의 존재 여부를 확인하거나 에셋·변환을 지정해 Prim을 만드는 함수 모음이다. |
| 054 | [isaacsim.core.utils.string](054_isaacsim.core.utils.string.md) | [25](../src/25_core_core_adding_multiple_robots/TUTORIAL.md) | 장면에 여러 작업이나 로봇을 추가할 때 겹치지 않는 이름을 만드는 유틸리티이다. |
| 055 | [isaacsim.robot.manipulators.examples.franka.controllers.rmpflow_controller](055_isaacsim.robot.manipulators.examples.franka.controllers.rmpflow_controller.md) | [27](../src/27_core_advanced_data_logging/TUTORIAL.md) | Franka가 목표 위치·자세를 따라가도록 제어합니다. |
| 056 | [isaacsim.core.api.loggers.DataLogger](056_isaacsim.core.api.loggers.DataLogger.md) | [27](../src/27_core_advanced_data_logging/TUTORIAL.md) | 시뮬레이션 중 관절·목표 상태를 프레임별로 기록하고 다시 읽는 클래스이다. |
| 057 | [omni.isaac.dynamic_control._dynamic_control](057_omni.isaac.dynamic_control._dynamic_control.md) | [28](../src/28_python_usd_robots_simulation/TUTORIAL.md) | 물리 객체의 핸들로 로봇 상태와 관절 목표를 다루는 이전 제어 API입니다. |
| 058 | [usd.schema.isaac.robot_schema](058_usd.schema.isaac.robot_schema.md) | [29](../src/29_python_usd_robot_schema/TUTORIAL.md) | USD에 로봇 구조와 부착 지점 정보를 부여합니다. |
| 059 | [usd.schema.isaac.robot_schema.utils](059_usd.schema.isaac.robot_schema.utils.md) | [29](../src/29_python_usd_robot_schema/TUTORIAL.md) | Robot Schema에 기록된 링크·관절과 로봇 연결 트리를 조사하는 유틸리티입니다. |
| 060 | [isaacsim.asset.importer.mjcf](060_isaacsim.asset.importer.mjcf.md) | [31](../src/31_importers_import_mjcf/TUTORIAL.md) | MJCF XML 모델을 USD 로봇 자산으로 가져오는 확장과 명령 API입니다. |
| 061 | [nvidia.srl.from_usd.to_urdf](061_nvidia.srl.from_usd.to_urdf.md) | [32](../src/32_importers_export_urdf/TUTORIAL.md) | USD 로봇을 URDF와 메시 파일로 내보냅니다. |
| 062 | [isaacsim.util.merge_mesh.commands](062_isaacsim.util.merge_mesh.commands.md) | [33](../src/33_importers_util_merge_mesh/TUTORIAL.md) | 여러 메시를 하나로 합치는 Kit 명령을 제공합니다. |
| 063 | [isaacsim.robot.manipulators](063_isaacsim.robot.manipulators.md) | [43](../src/43_robot_setup_pickplace_example/TUTORIAL.md) | 로봇 팔과 끝단·그리퍼를 하나의 객체로 다룹니다. |
| 064 | [isaacsim.robot.manipulators.controllers](064_isaacsim.robot.manipulators.controllers.md) | [43](../src/43_robot_setup_pickplace_example/TUTORIAL.md) | 팔 제어기와 그리퍼를 조합해 집기 작업을 수행합니다. |
| 065 | [isaacsim.robot_motion.motion_generation](065_isaacsim.robot_motion.motion_generation.md) | [43](../src/43_robot_setup_pickplace_example/TUTORIAL.md) | 역기구학, 경로·궤적 생성, RMPflow를 로봇 관절 제어에 연결합니다. |
| 066 | [isaacsim.robot_setup.assembler](066_isaacsim.robot_setup.assembler.md) | [49](../src/49_importers_assemble_robots/TUTORIAL.md) | 로봇 팔과 다른 로봇 부품을 부착 지점에 조립합니다. |
| 067 | [omni.asset_validator.core](067_omni.asset_validator.core.md) | [50](../src/50_importers_asset_validation/TUTORIAL.md) | USD Stage에 선택한 검사 규칙을 실행하고 발견된 문제를 모은다. |
| 068 | [isaacsim.asset.validation.physics_rules](068_isaacsim.asset.validation.physics_rules.md) | [50](../src/50_importers_asset_validation/TUTORIAL.md) | USD 자산의 질량과 충돌 메시 설정을 검사합니다. |
| 069 | [isaacsim.robot.wheeled_robots.controllers.differential_controller](069_isaacsim.robot.wheeled_robots.controllers.differential_controller.md) | [52](../src/52_motion_mobile_robot_controllers/TUTORIAL.md) | 차동구동 로봇의 좌우 바퀴 속도를 계산합니다. |
| 070 | [isaacsim.robot.wheeled_robots.controllers.holonomic_controller](070_isaacsim.robot.wheeled_robots.controllers.holonomic_controller.md) | [52](../src/52_motion_mobile_robot_controllers/TUTORIAL.md) | 전후·좌우·회전 속도를 전방향 바퀴 명령으로 바꿉니다. |
| 071 | [isaacsim.robot.wheeled_robots.controllers.ackermann_controller](071_isaacsim.robot.wheeled_robots.controllers.ackermann_controller.md) | [52](../src/52_motion_mobile_robot_controllers/TUTORIAL.md) | 차량의 조향각과 구동 바퀴 속도를 계산합니다. |
| 072 | [lula](072_lula.md) | [55](../src/55_motion_manipulators_lula_trajectory_generator/TUTORIAL.md) | 위치·회전과 관절·끝단 경로 명세를 만듭니다. |
| 073 | [isaacsim.robot_motion.motion_generation.lula](073_isaacsim.robot_motion.motion_generation.lula.md) | [57](../src/57_motion_manipulators_lula_rrt/TUTORIAL.md) | 장애물을 고려해 RRT 경로를 계획합니다. |
| 074 | [isaacsim.robot.surface_gripper](074_isaacsim.robot.surface_gripper.md) | [60](../src/60_motion_robot_surface_gripper/TUTORIAL.md) | 표면 그리퍼의 흡착 동작과 잡은 물체를 확인합니다. |
| 075 | [isaacsim.robot.surface_gripper._surface_gripper](075_isaacsim.robot.surface_gripper._surface_gripper.md) | [60](../src/60_motion_robot_surface_gripper/TUTORIAL.md) | 표면 그리퍼의 상태 값을 이름 있는 상태로 해석합니다. |
| 076 | [isaacsim.robot_setup.grasp_editor](076_isaacsim.robot_setup.grasp_editor.md) | [61](../src/61_motion_grasp_editor/TUTORIAL.md) | 저장된 grasp에서 그리퍼의 월드 자세를 계산합니다. |
| 077 | [isaacsim.sensors.camera](077_isaacsim.sensors.camera.md) | [62](../src/62_sensors_sensors_camera/TUTORIAL.md) | RGB 영상과 깊이 데이터를 얻고 카메라의 렌즈와 센서 설정을 조절한다. |
| 078 | [isaacsim.core.utils.numpy.rotations](078_isaacsim.core.utils.numpy.rotations.md) | [62](../src/62_sensors_sensors_camera/TUTORIAL.md) | NumPy 배열로 표현한 회전값을 변환하는 유틸리티이다. |
| 079 | [isaacsim.sensors.physics](079_isaacsim.sensors.physics.md) | [65](../src/65_sensors_sensors_physics_contact/TUTORIAL.md) | 접촉력·관절 토크·IMU 측정값을 물리 시뮬레이션에서 읽는다. |
| 080 | [isaacsim.sensors.physx](080_isaacsim.sensors.physx.md) | [68](../src/68_sensors_sensors_physics_proximity/TUTORIAL.md) | PhysX 기반 근접 센서와 거리 센서의 충돌·거리 데이터를 읽는다. |
| 081 | [pxr.Semantics](081_pxr.Semantics.md) | [70](../src/70_sensors_sensors_physx_lidar/TUTORIAL.md) | PhysX LiDAR의 탐지 대상을 구분하도록 prim에 의미 라벨을 기록한다. |
| 082 | [isaacsim.sensors.rtx](082_isaacsim.sensors.rtx.md) | [72](../src/72_sensors_sensors_rtx_lidar/TUTORIAL.md) | RTX LiDAR의 점군을 수집하고 센서에 반응하는 재질을 설정한다. |
| 083 | [omni.replicator.core](083_omni.replicator.core.md) | [73](../src/73_sensors_sensors_rtx_radar/TUTORIAL.md) | 장면 무작위화, 센서 데이터 추출, 합성 데이터 저장을 연결하는 Replicator API다. |
| 084 | [omni.anim.navigation.core](084_omni.anim.navigation.core.md) | [77](../src/77_events_sensors_rtx_placement/TUTORIAL.md) | 센서 배치 예제에서 사용할 NavMesh가 준비되어 있는지 확인한다. |
| 085 | [omni.graph.core](085_omni.graph.core.md) | [82](../src/82_tools_omnigraph_scripting/TUTORIAL.md) | Python으로 OmniGraph의 노드·연결·입력값을 만들고 그래프를 실행한다. |
| 086 | [omni.graph.action](086_omni.graph.action.md) | [82](../src/82_tools_omnigraph_scripting/TUTORIAL.md) | 재생·갱신 시점에 실행 신호를 보내는 OmniGraph 노드 계열입니다. |
| 087 | [omni.graph.ui_nodes](087_omni.graph.ui_nodes.md) | [82](../src/82_tools_omnigraph_scripting/TUTORIAL.md) | 그래프에서 문자열을 출력하는 PrintText 노드를 제공합니다. |
| 088 | [omni.graph.nodes](088_omni.graph.nodes.md) | [82](../src/82_tools_omnigraph_scripting/TUTORIAL.md) | 상수·벡터·USD 속성 데이터를 처리하는 OmniGraph 노드 계열입니다. |
| 089 | [omni.ui](089_omni.ui.md) | [83](../src/83_tools_updating_extensions/TUTORIAL.md) | Kit 확장 안에 작은 제어 창과 버튼을 만든다. |
| 090 | [isaacsim.examples.browser](090_isaacsim.examples.browser.md) | [86](../src/86_tools_custom_interactive_examples/TUTORIAL.md) | 사용자 예제를 Isaac Sim Examples Browser에 등록하고 해제하는 모듈이다. |
| 091 | [isaacsim.examples.interactive.base_sample](091_isaacsim.examples.interactive.base_sample.md) | [86](../src/86_tools_custom_interactive_examples/TUTORIAL.md) | Load·Reset 버튼과 비동기 장면 초기화 흐름을 갖춘 사용자 예제의 기반 클래스 모음이다. |
| 092 | [omni::ext::IExt](092_omni.ext.IExt.cpp.md) | [89](../src/89_tools_custom_cpp_extensions/TUTORIAL.md) | C++ Kit 확장의 시작과 종료 동작을 구현하는 인터페이스이다. |
| 093 | [carb C++ plugin API](093_carb.cpp.plugin.md) | [89](../src/89_tools_custom_cpp_extensions/TUTORIAL.md) | C++ 확장을 Kit에서 읽을 수 있는 Carbonite 플러그인으로 등록하는 API이다. |
| 094 | [OmniGraph C++ node API](094_omni.graph.cpp.md) | [90](../src/90_tools_omnigraph_custom_cpp_nodes/TUTORIAL.md) | OGN 정의에서 생성된 데이터베이스를 통해 C++ OmniGraph 노드를 구현하는 API이다. |
| 095 | [carb.profiler](095_carb.profiler.md) | [93](../src/93_tools_profiling_performance/TUTORIAL.md) | Python 함수와 코드 구간에 성능 측정 표시를 넣는다. |
| 096 | [isaacsim.cortex.framework.cortex_world](096_isaacsim.cortex.framework.cortex_world.md) | [98](../src/98_digital_twin_cortex_1_overview/TUTORIAL.md) | Cortex 로봇과 의사결정 네트워크를 시뮬레이션에 등록하고 실행합니다. |
| 097 | [isaacsim.cortex.framework.df](097_isaacsim.cortex.framework.df.md) | [98](../src/98_digital_twin_cortex_1_overview/TUTORIAL.md) | 상태 머신과 의사결정 노드를 조합하여 로봇의 행동 흐름을 구성합니다. |
| 098 | [isaacsim.cortex.framework.dfb](098_isaacsim.cortex.framework.dfb.md) | [98](../src/98_digital_twin_cortex_1_overview/TUTORIAL.md) | Cortex의 로봇 컨텍스트와 접근·그리퍼·복귀 행동을 재사용합니다. |
| 099 | [isaacsim.cortex.framework.robot](099_isaacsim.cortex.framework.robot.md) | [98](../src/98_digital_twin_cortex_1_overview/TUTORIAL.md) | Cortex 행동에서 제어할 Franka와 UR10 로봇을 준비합니다. |
| 100 | [isaacsim.cortex.framework.motion_commander](100_isaacsim.cortex.framework.motion_commander.md) | [98](../src/98_digital_twin_cortex_1_overview/TUTORIAL.md) | Cortex 로봇 팔에 보낼 목표 자세와 접근 조건을 묶습니다. |
| 101 | [isaacsim.cortex.framework.cortex_utils](101_isaacsim.cortex.framework.cortex_utils.md) | [99](../src/99_digital_twin_cortex_2_decider_networks/TUTORIAL.md) | Cortex 행동 파일을 불러오고 Isaac 자산의 기본 경로를 확인합니다. |
| 102 | [isaacsim.cortex.framework.math_util](102_isaacsim.cortex.framework.math_util.md) | [100](../src/100_digital_twin_cortex_3_example_peck_games/TUTORIAL.md) | Cortex 목표 자세의 회전·변환 계산과 도달 여부 판정을 수행합니다. |
| 103 | [isaacsim.cortex.framework.cortex_object](103_isaacsim.cortex.framework.cortex_object.md) | [101](../src/101_digital_twin_cortex_4_franka_block_stacking/TUTORIAL.md) | Core 객체를 Cortex 행동이 사용하는 물체 인터페이스로 감쌉니다. |
| 104 | [isaacsim.core.api.articulations.ArticulationSubset](104_isaacsim.core.api.articulations.ArticulationSubset.md) | [101](../src/101_digital_twin_cortex_4_franka_block_stacking/TUTORIAL.md) | 로봇 articulation의 관절 일부를 이름으로 묶는 클래스이다. |
| 105 | [isaacsim.cortex.framework.cortex_rigid_prim](105_isaacsim.cortex.framework.cortex_rigid_prim.md) | [102](../src/102_digital_twin_cortex_5_ur10_bin_stacking/TUTORIAL.md) | Cortex 작업에서 움직이는 상자의 강체 Prim을 다룹니다. |
| 106 | [isaacsim.core.utils.math](106_isaacsim.core.utils.math.md) | [102](../src/102_digital_twin_cortex_5_ur10_bin_stacking/TUTORIAL.md) | 벡터 계산에 사용하는 간단한 수학 유틸리티이다. |
| 107 | [isaacsim.cortex.framework.obstacle_monitor_context](107_isaacsim.cortex.framework.obstacle_monitor_context.md) | [102](../src/102_digital_twin_cortex_5_ur10_bin_stacking/TUTORIAL.md) | 작업 상황에 따라 Cortex 경로 생성에 사용할 장애물을 선택합니다. |
| 108 | [isaacsim.robot.wheeled_robots](108_isaacsim.robot.wheeled_robots.md) | [105](../src/105_ros2_ros2_drive_turtlebot/TUTORIAL.md) | 차륜 로봇의 속도·조향 명령을 관절 명령으로 바꾸는 OmniGraph 노드 계열입니다. |
| 109 | [isaacsim.core.nodes](109_isaacsim.core.nodes.md) | [105](../src/105_ros2_ros2_drive_turtlebot/TUTORIAL.md) | 로봇 제어·시간·렌더링을 OmniGraph에 연결하는 노드와 Python 노드의 상태 관리 클래스를 제공한다. |
| 110 | [isaacsim.core.api.SimulationContext](110_isaacsim.core.api.SimulationContext.md) | [113](../src/113_ros2_ros2_camera/TUTORIAL.md) | 물리 초기화, 재생 상태와 시뮬레이션 스텝을 직접 관리하는 클래스이다. |
| 111 | [omni.syntheticdata](111_omni.syntheticdata.md) | [114](../src/114_ros2_ros2_camera_publishing/TUTORIAL.md) | 렌더링으로 만들어지는 센서 데이터의 처리 노드 연결을 다룬다. |
| 112 | [warp](112_warp.md) | [115](../src/115_ros2_ros2_camera_noise/TUTORIAL.md) | 카메라 영상과 깊이 데이터의 노이즈·색상 변환을 GPU에서 처리할 커널을 작성한다. |
| 113 | [usdrt.Sdf](113_usdrt.Sdf.md) | [119](../src/119_ros2_ros2_python/TUTORIAL.md) | OmniGraph의 카메라 대상 입력에 전달할 USDRT 경로 값을 만든다. |
| 114 | [omni.syntheticdata._syntheticdata](114_omni.syntheticdata._syntheticdata.md) | [119](../src/119_ros2_ros2_python/TUTORIAL.md) | 수동 카메라 발행 예제에서 센서 종류를 나타내는 열거형을 사용한다. |
| 115 | [simulation_interfaces.msg](115_simulation_interfaces.msg.md) | [121](../src/121_ros2_ros2_simulation_control/TUTORIAL.md) | ROS 2 시뮬레이션 제어의 실행 상태와 요청 결과를 표현한다. |
| 116 | [simulation_interfaces.srv](116_simulation_interfaces.srv.md) | [121](../src/121_ros2_ros2_simulation_control/TUTORIAL.md) | ROS 2 서비스로 Isaac Sim의 실행 상태·물체·스텝 진행을 제어한다. |
| 117 | [isaac_ros2_messages.srv](117_isaac_ros2_messages.srv.md) | [128](../src/128_ros2_ros2_prim_service/TUTORIAL.md) | ROS 2 서비스 요청으로 USD Prim의 속성값을 읽고 수정한다. |
| 118 | [omni.replicator.replicator_yaml](118_omni.replicator.replicator_yaml.md) | [132](../src/132_replicator_replicator_overview/TUTORIAL.md) | Replicator의 장면·랜덤화·기록 작업을 YAML로 표현하는 설정 인터페이스입니다. |
| 119 | [isaacsim.replicator.synthetic_recorder.synthetic_recorder](119_isaacsim.replicator.synthetic_recorder.synthetic_recorder.md) | [133](../src/133_replicator_replicator_recorder/TUTORIAL.md) | `SyntheticRecorder`는 카메라의 합성 데이터를 설정된 writer로 기록하는 클래스이다. |
| 120 | [isaacsim.replicator.writers](120_isaacsim.replicator.writers.md) | [133](../src/133_replicator_replicator_recorder/TUTORIAL.md) | 합성 데이터의 시각화 결과를 기록하는 Isaac Sim Writer API입니다. |
| 121 | [omni.simready.explorer](121_omni.simready.explorer.md) | [135](../src/135_replicator_replicator_isaac_randomizers/TUTORIAL.md) | SimReady 애셋 카탈로그에서 실습 장면에 사용할 물체를 찾는다. |
| 122 | [carb.eventdispatcher](122_carb.eventdispatcher.md) | [136](../src/136_replicator_replicator_isaac_snippets/TUTORIAL.md) | 이름이 붙은 앱 이벤트와 사용자 이벤트를 구독하거나 전달한다. |
| 123 | [omni.graph.scriptnode](123_omni.graph.scriptnode.md) | [136](../src/136_replicator_replicator_isaac_snippets/TUTORIAL.md) | 그래프 노드 안에서 Python 코드를 실행하는 ScriptNode를 제공합니다. |
| 124 | [carb.events](124_carb.events.md) | [136](../src/136_replicator_replicator_isaac_snippets/TUTORIAL.md) | Kit 이벤트 스트림을 구독하고 콜백으로 전달된 이벤트를 읽는 모듈이다. |
| 125 | [isaacsim.core.utils.bounds](125_isaacsim.core.utils.bounds.md) | [137](../src/137_replicator_replicator_scene_based_sdg/TUTORIAL.md) | Prim의 경계 상자를 계산해 물체 배치와 카메라 촬영 범위를 정하는 함수 모음이다. |
| 126 | [usdrt.Usd](126_usdrt.Usd.md) | [138](../src/138_replicator_replicator_object_based_sdg/TUTORIAL.md) | Fabric 장면에 연결해 특정 API 스키마가 적용된 prim을 조회한다. |
| 127 | [omni.replicator.core.scripts.utils](127_omni.replicator.core.scripts.utils.md) | [140](../src/140_replicator_replicator_custom_og_randomizer/TUTORIAL.md) | 사용자 OmniGraph 노드를 Replicator의 트리거 안에서 호출할 수 있게 연결한다. |
| 128 | [isaacsim.replicator.behavior.behaviors](128_isaacsim.replicator.behavior.behaviors.md) | [141](../src/141_replicator_replicator_modular_scripting/TUTORIAL.md) | Prim에 붙여 장면 속성을 바꾸거나 대상을 바라보게 하는 Replicator behavior 클래스 모음이다. |
| 129 | [isaacsim.replicator.behavior.utils.behavior_utils](129_isaacsim.replicator.behavior.utils.behavior_utils.md) | [141](../src/141_replicator_replicator_modular_scripting/TUTORIAL.md) | Behavior 스크립트를 Prim에 연결하고 완료 이벤트를 기다리는 비동기 도우미 모듈이다. |
| 130 | [omni.kit.scripting](130_omni.kit.scripting.md) | [141](../src/141_replicator_replicator_modular_scripting/TUTORIAL.md) | USD Prim에 연결해 재생 상태에 따라 실행하는 Python 동작 스크립트의 기반이다. |
| 131 | [omni.client](131_omni.client.md) | [142](../src/142_replicator_replicator_amr_navigation/TUTORIAL.md) | 애셋 저장 위치의 파일 목록을 읽어 장면에 추가할 USD 파일을 찾는다. |
| 132 | [omni.usd.commands](132_omni.usd.commands.md) | [142](../src/142_replicator_replicator_amr_navigation/TUTORIAL.md) | USD 장면 편집용 Kit 명령을 제공하는 모듈이다. |
| 133 | [isaacsim.examples.interactive.ur10_palletizing.ur10_palletizing](133_isaacsim.examples.interactive.ur10_palletizing.ur10_palletizing.md) | [143](../src/143_replicator_replicator_ur10_palletizing/TUTORIAL.md) | UR10의 상자 쌓기 예제 장면을 불러와 실행하는 BinStacking 클래스를 제공한다. |
| 134 | [isaacsim.replicator.object](134_isaacsim.replicator.object.md) | [144](../src/144_events_replicator_object/TUTORIAL.md) | 물체·카메라·조명과 랜덤화를 YAML로 지정하는 Object SDG 설정 API입니다. |
| 135 | [isaacsim.replicator.agent](135_isaacsim.replicator.agent.md) | [156](../src/156_events_replicator_agent/TUTORIAL.md) | 사람·로봇의 행동과 카메라·기록을 지정하는 Actor SDG 설정 API입니다. |
| 136 | [pxr.UsdSkel](136_pxr.UsdSkel.md) | [160](../src/160_events_ext_replicator_agent_customization/TUTORIAL.md) | 캐릭터 애니메이션 리타게팅에 전달할 prim의 스켈레톤·애니메이션 타입을 확인한다. |
| 137 | [isaacsim.replicator.incident](137_isaacsim.replicator.incident.md) | [161](../src/161_events_replicator_incident/TUTORIAL.md) | 전도·화재·유출 사건과 발생 시점을 지정하는 Incident SDG 설정 API입니다. |
| 138 | [isaacsim.core.cloner](138_isaacsim.core.cloner.md) | [163](../src/163_motion_cloner/TUTORIAL.md) | 원본 환경을 여러 경로에 복제하고 배치·물리 복제·충돌 관계를 설정하는 클래스 모음이다. |
| 139 | [isaacsim.robot.policy.examples.robots](139_isaacsim.robot.policy.examples.robots.md) | [164](../src/164_motion_robot_policy_example/TUTORIAL.md) | H1과 Spot의 학습된 평지 보행 정책을 시뮬레이션에서 실행합니다. |
| 140 | [isaacsim.replicator.mobility_gen.examples.robots](140_isaacsim.replicator.mobility_gen.examples.robots.md) | [167](../src/167_sdg_extra_replicator_mobility_gen/TUTORIAL.md) | MobilityGen에서 사용할 수 있는 예제 로봇 클래스를 제공하는 모듈이다. |
| 141 | [isaacsim.replicator.mobility_gen.impl.robot](141_isaacsim.replicator.mobility_gen.impl.robot.md) | [167](../src/167_sdg_extra_replicator_mobility_gen/TUTORIAL.md) | MobilityGen 로봇 구현을 등록하는 `ROBOTS` 레지스트리를 제공하는 모듈이다. |
| 142 | [isaacsim.replicator.mobility_gen.impl.build](142_isaacsim.replicator.mobility_gen.impl.build.md) | [167](../src/167_sdg_extra_replicator_mobility_gen/TUTORIAL.md) | MobilityGen 기록 디렉터리에서 재생할 시나리오를 구성하는 모듈이다. |
| 143 | [isaacsim.replicator.mobility_gen.impl.reader](143_isaacsim.replicator.mobility_gen.impl.reader.md) | [167](../src/167_sdg_extra_replicator_mobility_gen/TUTORIAL.md) | `MobilityGenReader`는 저장된 MobilityGen 기록에서 프레임별 상태를 읽는 클래스이다. |
| 144 | [isaacsim.replicator.mobility_gen.impl.writer](144_isaacsim.replicator.mobility_gen.impl.writer.md) | [167](../src/167_sdg_extra_replicator_mobility_gen/TUTORIAL.md) | `MobilityGenWriter`는 재생한 로봇 상태와 센서 결과를 MobilityGen 데이터 형식으로 저장하는 클래스이다. |
| 145 | [isaacsim.replicator.mobility_gen.impl.utils.global_utils](145_isaacsim.replicator.mobility_gen.impl.utils.global_utils.md) | [167](../src/167_sdg_extra_replicator_mobility_gen/TUTORIAL.md) | MobilityGen이 공유하는 시뮬레이션 World에 접근하는 도우미 모듈이다. |
| 146 | [isaacsim.replicator.grasping.grasping_manager](146_isaacsim.replicator.grasping.grasping_manager.md) | [168](../src/168_sdg_extra_replicator_grasping_sdg/TUTORIAL.md) | `GraspingManager`는 물체를 잡을 후보 자세를 생성하고 물리 시뮬레이션으로 평가하는 클래스이다. |
| 147 | [isaacsim.replicator.caption.core.settings](147_isaacsim.replicator.caption.core.settings.md) | [171](../src/171_events_replicator_caption/TUTORIAL.md) | `ReplicatorCaptionSettings`는 장면 캡션 생성에 사용할 설정 경로와 대상 카메라를 지정하는 클래스이다. |
| 148 | [isaacsim.replicator.caption.core.stage_info_manager](148_isaacsim.replicator.caption.core.stage_info_manager.md) | [171](../src/171_events_replicator_caption/TUTORIAL.md) | `StageInfoManager`는 카메라 기준의 장면 정보를 모아 장면 그래프 생성을 실행하는 클래스이다. |
| 149 | [isaacsim.replicator.scene_blox.generation.scene_generator](149_isaacsim.replicator.scene_blox.generation.scene_generator.md) | [176](../src/176_replicator_replicator_sceneblox/TUTORIAL.md) | `SceneGenerator`는 완성된 SceneBlox 격자를 실제 USD 장면으로 만드는 클래스이다. |
| 150 | [isaacsim.replicator.scene_blox.grid_utils](150_isaacsim.replicator.scene_blox.grid_utils.md) | [176](../src/176_replicator_replicator_sceneblox/TUTORIAL.md) | SceneBlox 격자 생성에 필요한 공통 도구를 묶은 패키지이며, 튜토리얼에서는 `config`를 가져온다. |
| 151 | [isaacsim.replicator.scene_blox.grid_utils.grid](151_isaacsim.replicator.scene_blox.grid_utils.grid.md) | [176](../src/176_replicator_replicator_sceneblox/TUTORIAL.md) | `Grid`는 타일 배치 규칙과 제약을 만족하는 SceneBlox 격자를 구하는 클래스이다. |
| 152 | [isaacsim.replicator.scene_blox.grid_utils.grid_constraints](152_isaacsim.replicator.scene_blox.grid_utils.grid_constraints.md) | [176](../src/176_replicator_replicator_sceneblox/TUTORIAL.md) | `GridConstraints`는 SceneBlox 격자의 영역별 타일 배치 제한을 관리하는 클래스이다. |
| 153 | [isaacsim.replicator.scene_blox.grid_utils.tile](153_isaacsim.replicator.scene_blox.grid_utils.tile.md) | [176](../src/176_replicator_replicator_sceneblox/TUTORIAL.md) | SceneBlox 타일 후보와 배치 규칙을 읽는 모듈이다. |
| 154 | [isaacsim.replicator.scene_blox.grid_utils.tile_superposition](154_isaacsim.replicator.scene_blox.grid_utils.tile_superposition.md) | [176](../src/176_replicator_replicator_sceneblox/TUTORIAL.md) | `TileSuperposition`은 격자 한 칸에 놓일 수 있는 타일 후보와 선택 가중치를 담는 클래스이다. |
