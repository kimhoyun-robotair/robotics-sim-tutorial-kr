# 48. t117 · 관절 stiffness/damping을 실제 추종 응답으로 조정하기

권장 학습 순서 **48** · 로봇 자산 가져오기와 제작 · 출처 ID `t117`

Isaac Sim **5.1.0**에서 하나의 실제 articulation joint에 step/sine 위치 목표를 보내고 CSV로 측정한다. native Gain Tuner의 UI 실험도 동일한 로컬 `arm.urdf`로 수행한다. fake response나 미리 계산한 곡선을 simulator 결과처럼 표시하지 않는다.

## 준비와 실행

Isaac Sim 5.1, RTX GPU/드라이버, `isaacsim.asset.importer.urdf`, `isaacsim.robot_setup.gain_tuner`가 필요하다. 2-link/1-joint URDF와 inertia가 패키지 안에 있으므로 별도 로봇 asset은 필요 없다.

```bash
export ISAAC_SIM=/home/hoyunkim/isaacsim
cd src/48_importers_robot_setup_gain_tuner
"$ISAAC_SIM/python.sh" run.py --kp 20 --kd 1 --wave step
"$ISAAC_SIM/python.sh" run.py --kp 20 --kd 2 --wave step --output output/more_damping
"$ISAAC_SIM/python.sh" run.py --interactive --output output/gui
```

`--steps`를 생략한 GUI 실행은 사용자가 창을 닫을 때까지 유지된다. `--steps 120`처럼 양수를 지정하면 해당 횟수 후 자동 종료하며, `--steps 0`도 GUI를 계속 유지한다. `--headless`에서 생략하면 기존 600회 한도를 사용한다. `--interactive`는 GUI가 목표값을 제어하도록 바꾸는 옵션이며, 명시한 `--steps` 종료 한도는 그대로 적용된다. 실행 중에도 물리·제어가 계속 진행되며, 결과 요약은 실행을 마칠 때 기록한다.

기본 물리는 120 Hz, 600 step은 5초다. `response.csv`에는 시간, 목표 rad, 실제 rad, 속도 rad/s, 목표-실제 오차가 기록된다. 0.5초에 목표가 0→0.5 rad로 바뀐다. 결과가 이미 있으면 새로운 output 폴더를 지정한다.

## 응답 비교

1. 두 CSV에서 목표를 처음 넘는지(overshoot), 최종 오차가 남는지, 목표 부근의 진동이 얼마나 지속되는지 비교한다.
2. 첫 비교는 kp=20을 고정하고 kd만 1→2로 바꾼다. damping이 커질수록 무조건 좋다는 결론 대신 수렴 속도와 진동을 함께 본다.
3. `--wave sine --output output/sine`로 0.5 Hz, amplitude 0.3 rad 입력을 보낸다. 이 실습은 Gain Tuner와 같이 목표 속도를 0으로 보내 damping 영향을 관찰한다. 생산 trajectory controller의 feedforward 속도 명령과는 다르다.
4. URDF의 관절 limit ±1.2 rad, max velocity 2 rad/s, effort 20 Nm를 확인한다. 목표가 limit를 넘는 실험과 gain 부족을 혼동하지 않는다.

## native Gain Tuner 사용

1. `--interactive`로 열고 **Tools > Robotics > Gain Tuner**를 연다. Play 상태에서 import된 articulation을 선택한다. 이 모드에서 script는 별도 목표를 보내지 않으므로 UI 실험과 충돌하지 않는다.
2. **Tuning Gains / Tuning Options**에서 Stiffness 모드를 선택하고 shoulder의 stiffness=20, damping=1로 시작한다. Position mode를 유지한다.
3. **Gains Test**에서 Step Function을 선택하고 해당 joint의 Test를 체크한다. Step Minimum=0, Step Maximum=0.5, Period=2초, Phase=0으로 입력한다. sequence는 한 관절만 첫 그룹에 두고 실행한다.
4. **Test Results**에서 command/actual position과 velocity를 비교한다. damping만 변경하고 다시 실행한다. 각 sequence 시작 때 초기 자세로 reset됨을 확인한다.
5. Sinusoidal로 바꾸어 Amplitude/Offset은 joint range의 **백분율**임을 확인한다. 중앙 근처 작은 amplitude에서 시작하고 limit/max velocity/acceleration을 넘어가지 않게 한다.
6. Natural Frequency 모드로 전환해 damping ratio를 1.0, 0.5, 2.0으로 각각 시험한다. 다른 설정은 유지한다. home configuration에서 계산하는 관성이 자세가 바뀌면 달라질 수 있음을 고려한다.

## drive의 의미

PhysX joint drive는 현재 step에서 position/velocity 제약을 푸는 implicit drive다. 직관적으로 목표-실제 오차에 `Kp`, 속도 오차에 `Kd`가 곱해져 effort가 생기고 max force로 제한된다. revolute는 회전, prismatic은 이동을 제어한다.

| 모드 | 설정과 의미 |
|---|---|
| Position | stiffness > 0, damping으로 진동 억제 |
| Velocity | stiffness=0, damping > 0으로 속도 추종 |
| None | stiffness=damping=0, 별도 direct effort가 제어 |
| Mimic | 일반 drive 대신 reference joint coupling 사용 |
| Force / Acceleration | 직접 힘·토크 적용 / 질량으로 정규화된 가속도형 적용 |

`omega_n = sqrt(Kp / inertia)`, `zeta = Kd / (2 * inertia * omega_n)` 관계로 spring-damper 직관을 얻는다. angular frequency(rad/s)와 Hz를 혼동하지 않는다. `zeta=1`은 이상적인 단일축 모델의 임계 감쇠다. 실제 다관절·중력·effort clamp까지 이 식 하나로 보장되지 않는다.

코드의 `ArticulationAction`은 목표 명령이고 `get_joint_positions()/get_joint_velocities()`는 물리 엔진의 실제 측정이다. `initialize`는 `World.reset()` 과정에서 수행된다. 이상한 응답은 drive type, inertia, 시간 간격, effort saturation부터 확인한다. CSV 파일이 있다는 이유만으로 수렴을 통과 판정하지 않는다. 이 변경은 CLI/문법만 검증했으며 실제 응답과 native plots는 미검증이다.

## 출처

[Isaac Sim 5.1 Gain Tuner Extension](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup/ext_isaacsim_robot_setup_gain_tuner.html), [tuning options](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup/ext_isaacsim_robot_setup_gain_tuner.html#tuning-options), [gain tests](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup/ext_isaacsim_robot_setup_gain_tuner.html#gains-tests).
