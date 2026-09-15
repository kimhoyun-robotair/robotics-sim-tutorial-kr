# NVIDIA 예제 출처와 변경 사항

`camera_manual.py`는 NVIDIA Isaac Sim 5.1.0 설치본의
`standalone_examples/api/isaacsim.ros2.bridge/camera_manual.py`를 기반으로 합니다.
원본 NVIDIA copyright와 Apache-2.0 고지를 보존했으며 라이선스 전문은
`LICENSE-NVIDIA-EXAMPLES`에 있습니다.

변경 사항: `--steps`와 `--headless` 실행 옵션, GUI의 Pause/Stop 중 앱 업데이트와
재개 처리, 양수 스텝 한도 및 headless 기본 1200회, 초기화 실패 시 오류 보고와
`finally`에서 앱 종료를 추가했습니다. 원본의 RGB/Depth/CameraInfo 수동 게이트와
카메라 회전 동작을 유지합니다.

공식 문서: https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_python.html
