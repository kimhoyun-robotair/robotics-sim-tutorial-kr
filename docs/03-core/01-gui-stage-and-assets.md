# GUI, Stage와 자산

이 튜토리얼에서는 빈 Stage에 바닥, 조명과 물체를 배치하고 USD 계층을 읽는다. 마지막에는 원본 자산을 복사하지 않고 참조로 조립한 장면을 저장한다.

## 1. 화면의 여섯 영역 살펴보기

Isaac Sim을 실행한다.

```bash
cd ~/isaacsim
./isaac-sim.sh
```

처음 실행하면 셰이더 캐시를 준비하느라 시간이 오래 걸릴 수 있다. 화면이 열린 뒤 다음 영역을 확인한다.

| 영역 | 역할 | 이 장에서 할 일 |
|---|---|---|
| Menu Bar | 파일, 생성, 도구, 창과 확장 기능을 연다. | `File > New`, `Create`, `Window`를 사용한다. |
| Viewport | 현재 카메라에서 Stage를 렌더링한다. | 선택, 이동, 회전, 확대·축소를 수행한다. |
| Main Toolbar | 선택 도구와 Timeline 제어가 있다. | Play, Pause, Stop을 구분한다. |
| Browsers | 자산, 재질과 예제를 찾는다. | 자산을 Stage로 끌어다 놓는다. |
| Stage | 현재 USD 장면의 prim 계층을 보여 준다. | `/World/...` 경로를 읽고 부모·자식을 정리한다. |
| Property | 선택한 prim의 속성과 적용된 API 스키마를 보여 준다. | 변환, 강체, 충돌 등을 수정한다. |

Viewport 기본 조작은 마우스 설정에 따라 약간 다르다. 보통 우클릭을 누른 채 `W/A/S/D/Q/E`로 이동하고, `F`로 선택한 prim에 초점을 맞춘다. `W`, `E`, `R`은 각각 이동, 회전, 크기 조절 도구의 단축키이다. 조작 핸들의 축은 빨강 X, 초록 Y, 파랑 Z이다. Isaac Sim의 로봇 장면은 기본적으로 Z축이 위를 향한다.

### 선택과 좌표계

Stage에서 prim을 선택한 뒤 `W`를 누른다. 조작 핸들 메뉴에서 **World**와 **Local**을 번갈아 선택해 본다.

- World 좌표계는 장면의 고정 축을 따른다.
- Local 좌표계는 prim의 회전된 축을 따른다.
- Property의 변환 값은 정확한 수치 입력에 적합하다.
- 회전 UI는 도(degree)로 표시되는 경우가 많지만 로봇 제어 API의 관절각은 라디안을 사용한다. 서로 섞지 않는다.

## 2. Stage, prim과 속성

USD Stage는 하나의 장면을 합성한 결과이다. Stage 안의 주소 가능한 항목을 **prim**이라고 하며 `/World/table/cup`처럼 절대 경로로 찾는다. prim에는 자료형, 속성, 연결 관계, 메타데이터와 API 스키마가 있다.

다음 구분을 습관화한다.

- `/World`는 흔히 장면의 기본 prim이 되는 루트 Xform이다.
- Xform prim은 자식의 좌표계를 묶는다.
- 메시, Cube, 카메라, DistantLight는 구체적인 유형이 정해진 prim이다.
- `RigidBodyAPI`, `CollisionAPI`, `MassAPI` 같은 API 스키마는 기존 prim에 물리 의미를 추가한다.
- Stage 창의 계층은 파일 하나의 내용이 아니라 여러 레이어와 참조가 합성된 최종 모습일 수 있다.

## 3. 첫 장면 만들기

1. `File > New`를 누른다.
2. `Create > Physics > Ground Plane`으로 바닥을 만든다.
3. `Create > Lights > Distant Light`로 조명을 만든다.
4. `Create > Shape > Cube`로 큐브를 만든다.
5. Stage에서 Cube를 선택한다. Property의 Geometry 또는 Raw USD Properties에서 `size`를 `0.2`로, Transform의 Scale을 `(1, 1, 1)`로, Translate를 `(0, 0, 1)`로 설정한다. 단위는 미터이다.
6. Play를 누른다. 아직 큐브는 떨어지지 않는다. 시각 형상만 만들었기 때문이다.
7. Stop을 누르고 Cube를 다시 선택한다.
8. Property의 `Add > Physics > Rigid Body with Colliders Preset`을 적용한다.
9. 큐브의 Physics 속성에서 Mass를 `1.0 kg`으로 지정한다.
10. Play를 누른다. 큐브가 떨어져 바닥과 충돌하고 중심 높이 Z가 약 `0.1 m`에서 멈춰야 한다.

여기서 **강체**와 **충돌 형상**은 별개이다. 강체는 중력, 질량, 속도를 갖는 동역학 객체이고, 충돌 형상은 접촉에 쓰는 형상이다. 둘 중 하나만 있으면 각각 “움직이지만 통과하는 객체” 또는 “움직이지 않는 충돌 벽” 같은 구성이 된다.

### 검증 체크포인트

- [ ] Stage에 `/World`, GroundPlane, DistantLight, Cube가 보인다.
- [ ] Play 전 Cube의 Z가 약 1 m이다.
- [ ] Play 뒤 Cube가 바닥 위에서 정지한다.
- [ ] Stop 뒤 초기 위치로 돌아가는지 확인한다. Stop은 작성 상태로 복귀하지만 코드로 작성한 변경은 남을 수 있다.

## 4. Timeline을 정확히 이해하기

| 조작 | 의미 | 주의점 |
|---|---|---|
| Play | 시뮬레이션 시간을 진행하고 물리를 계산한다. | 초기화 직후 첫 물리 스텝 전에는 일부 텐서/view 데이터가 없다. |
| Pause | 현재 물리 상태를 유지한 채 시간의 진행을 멈춘다. | 다시 Play하면 이어서 실행한다. |
| Stop | Timeline을 정지하고 시뮬레이션 상태를 재설정한다. | Extension 예제는 Stop→Play만으로 자체 상태가 완전히 초기화되지 않을 수 있으므로 제공된 초기화를 사용한다. |
| 스텝 | 한 프레임 또는 설정된 스텝만 진행한다. | 접촉·제어 문제를 관찰하기 좋다. |

렌더링 프레임률과 물리 시간 간격은 같은 개념이 아니다. 화면을 한 번 그리는 동안 물리를 여러 단계로 계산할 수 있다. 제어 코드는 실제 `step_size`를 받아 계산해야 하며 “한 콜백이 항상 1/60초”라고 가정하지 않는다.

## 5. 자산을 복제하지 말고 참조하기

Content Browser에서 환경이나 로봇 USD를 Stage 또는 Viewport로 끌면 일반적으로 참조 prim이 생긴다. 참조는 원본 파일을 장면 안에 통째로 복제하지 않고 그 구성을 합성한다.

권장 장면 구조는 다음과 같다.

```text
/World
  /PhysicsScene
  /Environment        # 환경 USD 참조
  /Robots
    /Robot_01         # 로봇 USD 참조
  /Props
    /Box_01
  /Sensors
  /Looks
```

참조를 선택하고 변환을 바꾸면 이 장면의 상위 레이어에 덮어쓴 속성값이 기록된다. 원본 로봇 파일은 바뀌지 않는다. 반복해서 사용할 로봇은 `robot.usd`로, 배치와 조명은 `scene.usd`로 분리하는 편이 유지보수에 유리하다.

### Reference, Payload, Instance의 선택

| 방식 | 적합한 경우 | 핵심 특징 |
|---|---|---|
| 참조 | 대부분의 로봇·환경 조립 | 원본 구성에 현재 레이어에서 덮어쓴 값을 반영한다. |
| Payload | 매우 큰 환경의 일부만 불러올 때 | 필요할 때만 불러올 수 있어 편집기 응답성과 메모리를 관리하기 좋다. |
| Instanceable 참조 | 같은 정적/반복 자산이 매우 많음 | 공통 원형(prototype)을 공유해 메모리를 줄이지만 인스턴스 내부를 개별 편집하기 어렵다. |
| Copy | 원본과 완전히 분리해 구조를 바꿔야 함 | 중복 데이터와 업데이트 비용이 생긴다. |

## 6. Asset Browser와 Content Browser

Isaac Sim Asset Browser는 NVIDIA가 제공하는 로봇, 환경, 센서와 소품을 용도별로 찾기 편하다. Content Browser는 로컬 파일과 연결된 저장 위치를 탐색하는 일반 파일 브라우저이다. 자산을 넣은 뒤 다음을 확인한다.

1. prim 경로가 예상한 위치인지 확인한다.
2. 원본 자산의 기본 prim이 올바르게 참조되었는지 확인한다.
3. `F`로 자산에 초점을 맞춘다. 보이지 않으면 크기 또는 단위를 의심한다.
4. 눈 아이콘과 `visibility`를 확인한다.
5. Output Log에서 누락된 텍스처와 참조 경로를 찾는다.

## 7. Property 패널에서 스키마 읽기

Cube를 선택하면 Property에 변환, Display, 재질 등의 영역이 보인다. `Add` 메뉴는 prim에 스키마를 적용한다. 물리 객체를 진단할 때 다음 질문에 순서대로 답한다.

1. 이 prim 자체 또는 자식에 충돌 형상이 있는가?
2. 동적으로 움직여야 한다면 강체 API가 있는가?
3. 질량 또는 밀도가 합리적인가?
4. 충돌 형상 근사가 형상에 맞는가?
5. 물리 재질이 충돌 형상에 연결되었는가?
6. articulation 링크라면 중첩된 별도 강체 구조가 잘못 들어가 있지 않은가?

## 8. 저장과 재열기

1. `File > Save As`를 눌러 `core_gui_scene.usda` 또는 `core_gui_scene.usd`로 저장한다.
2. 학습 중에는 변경 내용을 텍스트로 비교할 수 있는 `.usda`가 편리하다.
3. `File > New`로 비운 뒤 저장한 파일을 다시 연다.
4. Play하여 같은 결과가 나는지 확인한다.

상대 참조가 있다면 파일을 다른 위치로 옮겼을 때 깨질 수 있다. 프로젝트 자산은 일정한 폴더 구조를 만들고 가능하면 상대 경로로 묶는다. 임시 캐시 URL이나 개인 홈의 절대 경로를 배포 장면에 남기지 않는다.

## 9. 짧은 실습: 두 큐브 비교

다음 목표를 GUI만으로 달성한다.

- 빨간 큐브는 강체와 충돌 형상을 모두 갖게 한다.
- 파란 큐브는 충돌 형상만 갖게 하고 바닥에서 0.5 m 위에 둔다.
- Play했을 때 빨간 큐브는 파란 큐브 위에 떨어지고 파란 큐브는 공중에 고정되어 있어야 한다.

결과가 다르면 각 큐브의 적용 스키마와 충돌 형상 위치를 확인한다. 이 실습은 “보이는 메시”, “충돌 형상”, “동역학 물체”가 각기 다른 역할을 맡는다는 점을 익히기 위한 것이다.

## 출처

- [User Interface Reference](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/gui/reference_user_interface.html)
- [Keyboard Shortcuts Reference](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/gui/reference_keyboard_shortcuts.html)
- [Isaac Sim Basic Usage Tutorial](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/introduction/quickstart_isaacsim.html)
- [Content Browser](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/utilities/content_browser.html)
- [Isaac Sim Asset Browser](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/utilities/asset_browser.html)
- [Asset Structure](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup/asset_structure.html)
- [Physics Simulation Fundamentals](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/physics/simulation_fundamentals.html)
