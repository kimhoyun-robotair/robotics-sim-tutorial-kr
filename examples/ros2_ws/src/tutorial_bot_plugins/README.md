# tutorial_bot_plugins

Gazebo Harmonic용 `TutorialBotDiagnosticsSystem`과 공개 계약을 설치하는 package이다.

플러그인은 ECS에서 대상 모델의 pose를 읽어 누적 이동 거리를 계산하고, Gazebo
Transport로 상태와 거리를 발행한다. enable topic과 reset service도 제공한다.
`source install/setup.bash`를 실행하면 package의 DSV hook이 설치된 `lib` 디렉터리를
`GZ_SIM_SYSTEM_PLUGIN_PATH`에 추가한다.

고급 장의 자동 검증은 `config/diagnostics-contract.yaml`과 실제 library, topic,
service가 일치하는지 확인한다.
