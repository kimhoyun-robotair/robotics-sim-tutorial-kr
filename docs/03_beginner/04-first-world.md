# 첫 World 실행하기

> **난이도:** 초급  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** SDF 기초

## 학습 목표

- 물리 step, 중력, 정적 바닥, 동적 상자의 관계를 코드에서 찾는다.
- SDF를 검사한 뒤 GUI와 Server-only 모드로 실행한다.
- CLI 관찰값으로 world가 제대로 올라왔는지 확인한다.

## world를 구성하는 네 블록

`examples/gazebo/worlds/first-world.sdf`는 외부 mesh 없이 다음 네 블록만으로 실행된다.

1. physics 설정과 world System
2. directional light `sun`
3. 정적 바닥 `ground`
4. 동적 상자 `training_box`와 정적 표식 `beacon`

physics 설정은 다음과 같다.

```xml
<gravity>0 0 -9.8</gravity>
<physics name="default_physics" type="ignored">
  <max_step_size>0.001</max_step_size>
  <real_time_factor>1.0</real_time_factor>
</physics>
```

`max_step_size=0.001`은 한 physics update의 simulation time 간격이 1 ms임을 뜻한다. 이상적으로 RTF가 1이면 1초에 약 1,000번의 physics update가 필요하다. 실제 RTF는 컴퓨터 부하에 따라 달라진다.

조명은 pose, 방향, 색, 그림자 여부를 가진다.

```xml
<light name="sun" type="directional">
  <pose>0 0 10 0 0 0</pose>
  <cast_shadows>true</cast_shadows>
  <direction>-0.5 0.1 -0.9</direction>
  <diffuse>1 1 1 1</diffuse>
  <specular>0.2 0.2 0.2 1</specular>
</light>
```

## 실습 1: 검사하고 실행하기

저장소 루트에서 SDF를 먼저 검사한다.

```bash
gz sdf -k examples/gazebo/worlds/first-world.sdf
```

`Valid.`를 확인한 뒤 GUI로 실행한다.

```bash
gz sim examples/gazebo/worlds/first-world.sdf
```

<figure class="course-figure">
  <img src="../../assets/diagrams/beginner-first-world.svg" alt="first_world의 회색 바닥과 빨간 training_box 및 파란 beacon 예상 화면" loading="lazy">
  <figcaption>그림 1. 정적 ground, 동적 training_box, 정적 beacon을 이름과 색으로 구분한다.</figcaption>
</figure>

GUI에는 회색 바닥, 빨간 상자 `training_box`, 파란 원통 `beacon`이 보여야 한다. `training_box`의 중심 z는 0.5 m이고 높이는 1 m이므로 바닥과 정확히 맞닿은 상태에서 시작한다.

## 실습 2: Server-only 검증하기

CI나 원격 서버에서는 GUI 없이 같은 world를 실행한다.

```bash
gz sim -s -r examples/gazebo/worlds/first-world.sdf
```

다른 terminal에서 world 관련 service와 model 목록을 확인한다.

```bash
gz service -l | grep '^/world/first_world/'
gz model --list
```

정상이라면 model 목록에 다음 이름이 나타난다.

```text
ground
training_box
beacon
```

상태 topic도 한 표본만 읽어 simulation time이 증가하는지 확인한다.

```bash
gz topic -e -t /world/first_world/stats -n 1
```

## 실습 3: 코드 한 줄을 바꾸고 결과 예측하기

원본을 보존하기 위해 임시 복사본으로 실험한다.

```bash
cp examples/gazebo/worlds/first-world.sdf /tmp/first-world-static-box.sdf
sed -i '/<model name="training_box">/a\      <static>true</static>' \
  /tmp/first-world-static-box.sdf
gz sdf -k /tmp/first-world-static-box.sdf
gz sim -r /tmp/first-world-static-box.sdf
```

GUI에서 상자를 들어 올린 뒤 재생하면 원본의 동적 상자와 달리 중력으로 떨어지지 않는다. 한 태그의 차이가 물리 동작으로 이어지는지 확인하는 실험이다.

## 동작 원리

Physics System은 동적 `training_box`와 정적 `ground`의 collision을 이용해 접촉을 계산한다. SceneBroadcaster System은 그 결과를 GUI에 전달한다. `beacon`에는 visual만 있고 `<static>true</static>`이므로 파란 표식으로만 사용된다.

## 예상 관찰

1. `gz sdf -k`가 `Valid.`를 출력한다.
2. Entity Tree와 `gz model --list`에 같은 model 세 개가 나타난다.
3. 재생 후 `training_box`는 바닥 위에 남고 `beacon`은 움직이지 않는다.
4. Pause 상태에서는 simulation time과 물리 상태가 함께 멈춘다.
5. Server-only 모드에서도 stats topic과 world service를 확인할 수 있다.

## 문제 해결

- SDF 검사가 실패하면 오류 line의 XML 요소와 닫는 태그부터 확인한다.
- `gz model --list`가 Server를 찾지 못하면 `gz sim`이 실행 중인지 확인한다.
- server는 시작하지만 GUI가 열리지 않으면 [문제 해결](../02_getting-started/03_troubleshooting.md)의 렌더링 항목을 확인한다.
- 상대 경로를 찾지 못하면 `pwd`가 저장소 루트인지 확인한다.

[다음: Xacro로 `tutorial_bot` 만들기](05-first-robot.md)
