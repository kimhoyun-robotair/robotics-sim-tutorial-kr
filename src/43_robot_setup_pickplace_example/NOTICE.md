# 포함한 설정 파일의 출처

`config/robot_descriptor.yaml`, `config/ur10e_rmpflow_common.yaml`은 NVIDIA Isaac Sim 5.1.0 설치본의
`standalone_examples/api/isaacsim.robot.manipulators/ur10e/rmpflow/`에서 가져왔습니다.
NVIDIA CORPORATION & AFFILIATES의 Apache-2.0 고지와 라이선스를 보존합니다.

`config/ur10e_kinematics.urdf`는 같은 폴더의 `ur10e.urdf`에서 모든 visual/collision 요소만 제거한 버전입니다.
kinematics에 필요한 joint/link/inertial을 유지하며 누락된 외부 mesh 경로 의존성을 없앴습니다.
렌더링/물리 모델은 공식 `ur_gripper.usd`가 계속 담당합니다.

로컬 변경: descriptor의 `ee_link/...` collision sphere link 이름 7개를 함께 제공된 URDF의 실제 link 이름과
일치시켰습니다. 예를 들어 base는 `ee_link_robotiq_arg2f_base_link`, 손가락은 `left_inner_finger`입니다.
이름 변경 이외의 sphere 위치/크기와 RMP 파라미터는 원본 그대로입니다.

출처: https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/tutorial_pickplace_example.html
