# 공식 문서·예제 대응표

확인 기준은 2026-09-09의 `v3.0.0-beta2.patch1`이다. 아래 링크는 공식 저장소의 같은 태그를 가리킨다. 웹의 `main`·`develop` 문서는 이후 변경될 수 있으므로, 명령이나 인자가 다르면 이 태그 소스와 먼저 비교한다. 이 문서는 공식 자료 전체의 번역본이 아니라 초보자가 실습하며 이해하도록 순서를 다시 구성한 한국어 안내서이다.

## 학습 단계와 공식 자료

| 이 튜토리얼 | 공식 설명·실행 소스 | 읽을 때 확인할 부분 |
| --- | --- | --- |
| 01–02 생태계 | [공식 소개](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/README.md) | 학습 프레임워크의 역할, 3.0 beta 표시 |
| 03 사양 | [설치 개요](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/docs/source/setup/installation/index.rst) | 운영체제·메모리·Python 요구사항 |
| 04–05 설치 | [pip 설치](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/docs/source/setup/installation/pip_installation.rst), [의존성](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/pyproject.toml) | Isaac Sim 6.0.1과 Python 3.12 조합 |
| 06–08 GUI | [Isaac Sim GUI 안내](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/gui/reference_user_interface.html) | Viewport, Stage, Property, 타임라인 |
| 09 앱 실행 | [launch_app](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/docs/source/tutorials/00_sim/launch_app.rst), [AppLauncher 구현](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/source/isaaclab/isaaclab/app/app_launcher.py) | 시뮬레이터 실행 후 필요한 모듈 import |
| 10 장면 생성 | [create_empty](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/scripts/tutorials/00_sim/create_empty.py), [spawn_prims](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/scripts/tutorials/00_sim/spawn_prims.py) | cfg.func, 조명, simulation step |
| 11–14 자산 | [run_rigid_object 설명](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/docs/source/tutorials/01_assets/run_rigid_object.rst), [코드](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/scripts/tutorials/01_assets/run_rigid_object.py) | 기본 root pose 복사, reset, state 갱신 |
| 15–16 로봇 | [run_articulation](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/scripts/tutorials/01_assets/run_articulation.py), [Franka 설정](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/source/isaaclab_assets/isaaclab_assets/robots/franka.py) | actuator·gravity·초기 관절 설정 |
| 17 병렬 장면 | [create_scene](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/scripts/tutorials/02_scene/create_scene.py) | env namespace, env_origins, scene.reset |
| 18–19 카메라 | [run_usd_camera](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/scripts/tutorials/04_sensors/run_usd_camera.py), [CameraData](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/source/isaaclab/isaaclab/sensors/camera/camera_data.py) | renderer_cfg, camera pose, ProxyArray |
| 20 접촉 센서 | [add_sensors_on_robot](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/scripts/tutorials/04_sensors/add_sensors_on_robot.py) | activate_contact_sensors, 힘의 좌표계 |
| 21 raycast | [run_ray_caster](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/scripts/tutorials/04_sensors/run_ray_caster.py) | mesh_prim_paths와 유효 hit 처리 |
| 22 센서 시각화 | [카메라 시각화](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/scripts/tutorials/07_visualizers/run_tiled_camera_visualizer.py) | 렌더링과 화면 표시의 차이 |
| 23–24 환경 | [Manager 환경](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/docs/source/tutorials/03_envs/create_manager_rl_env.rst), [Direct 환경](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/docs/source/tutorials/03_envs/create_direct_rl_env.rst) | 같은 RL 루프, 다른 코드 구성 |
| 25 기준 정책 | [random_agent](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/scripts/environments/random_agent.py) | 무작위 행동으로 관측·reset 경로 확인 |
| 26–29 학습 | [학습 실행](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/docs/source/tutorials/03_envs/run_rl_training.rst), [학습 설정](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/docs/source/tutorials/03_envs/configuring_rl_training.rst) | 통합 train/play, task별 agent 등록 |
| 30 사용자 task | [Gym 등록](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/docs/source/tutorials/03_envs/register_rl_env_gym.rst) | task ID, 환경 cfg, agent cfg entry point |
| 31 환경 수정 | [Direct 환경 수정](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/docs/source/tutorials/03_envs/modify_direct_rl_env.rst) | 관측·행동 크기와 초기화·보상의 일관성 |
| 32 모방학습 | [공식 Mimic 패키지](https://github.com/isaac-sim/IsaacLab/tree/v3.0.0-beta2.patch1/source/isaaclab_mimic) | 시연 기록, 성공 판정, 데이터 생성 흐름 |
| 33–36 평가 | [공식 학습 워크플로 구현](https://github.com/isaac-sim/IsaacLab/tree/v3.0.0-beta2.patch1/source/isaaclab_rl/isaaclab_rl) | checkpoint와 normalizer, wrapper와 종료 처리 |

## 더 실습할 공식 튜토리얼

본문을 끝낸 뒤 아래 예제로 확장한다. 각 실행 파일 상단의 명령을 그대로 복사하기 전에 `--help`와 AppLauncher 인자를 확인한다. 고정 태그 안에도 일부 docstring에 과거 `--headless` 표기가 남아 있다. 이 안내서의 실행 명령은 `--viz kit` 또는 `--viz none`을 사용한다.

| 확장 주제 | 공식 예제 | 먼저 확인할 조건 |
| --- | --- | --- |
| 다른 로봇 자산 추가 | [add_new_robot.py](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/scripts/tutorials/01_assets/add_new_robot.py) | 링크·관절 이름, 고정 base, 충돌, 단위 |
| 변형체 | [run_deformable_object.py](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/scripts/tutorials/01_assets/run_deformable_object.py) | 지원 backend, 재질, 시간 간격 |
| 표면 그리퍼 | [run_surface_gripper.py](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/scripts/tutorials/01_assets/run_surface_gripper.py) | task와 backend별 지원 여부 |
| 상대 좌표 | [run_frame_transformer.py](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/scripts/tutorials/04_sensors/run_frame_transformer.py) | source·target 프레임과 offset |
| RayCaster 카메라 | [run_ray_caster_camera.py](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/scripts/tutorials/04_sensors/run_ray_caster_camera.py) | RTX RGB 카메라와 관측 종류가 다름 |
| 역기구학 | [run_diff_ik.py](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/scripts/tutorials/05_controllers/run_diff_ik.py) | root frame 목표, Jacobian index |
| Operational Space Control | [run_osc.py](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/scripts/tutorials/05_controllers/run_osc.py) | 관성·중력·접촉 제어와 토크 제한 |
| USD 장면에서 정책 추론 | [policy_inference_in_usd.py](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/scripts/tutorials/03_envs/policy_inference_in_usd.py) | 학습과 동일한 관측 순서·action scale |
| 실제 로봇 배포 준비 | [anymal_c_env.py](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/scripts/tutorials/06_deploy/anymal_c_env.py) | 제어 주기·조인트 순서·제한, 실제 하드웨어 시험은 별개 |

## 출처를 다시 확인하는 방법

```bash
git -C "$ISAACLAB_ROOT" rev-parse HEAD
python "$TUTORIAL_ROOT/isaaclab_tutorial/tools/check_tutorial.py" \
  --upstream "$ISAACLAB_ROOT"
```

[소스 해시 목록](../reports/upstream-source-manifest.json)은 확인한 설치·튜토리얼 파일의 SHA-256을 보관한다. 소스 해시는 읽은 버전을 식별하며 실행 성공을 증명하지 않는다. 장면·로봇·센서·학습 실행의 증거는 별도의 GPU 보고서와 영상으로 남긴다.
