# 26. IMU와 접촉 센서의 물리 데이터를 읽다

## 목표와 준비

작은 상자를 바닥에 떨어뜨리고 IMU와 접촉 센서를 읽는다. 화면 밝기와 무관하게 갱신되는 물리 센서의 특성을 확인한다. 이번 실습은 23~25단계의 카메라·LiDAR와 별도 장면에서 진행한다.

6.0.1의 새 API는 `isaacsim.sensors.experimental.physics`이다. `IMU`와 `Contact`는 Prim을 구성하고, `IMUSensor`와 `ContactSensor`는 시뮬레이션 중 값을 읽는다. 기존 `isaacsim.sensors.physics` 예제의 `sensorPeriod`를 새 API에 그대로 넣지 않는다. 새 물리 센서는 물리 스텝마다 갱신된다.

## 1. 센서를 붙일 몸체를 정하다

센서는 `/World/Box/Imu`, `/World/Box/Contact`처럼 Rigid Body 아래에 만든다. 위치만 로봇과 비슷하게 맞춘 독립 Prim은 몸체의 움직임을 따라가는 장착 관계가 아니다.

```python
from isaacsim.sensors.experimental.physics import IMU, IMUSensor, Contact, ContactSensor

imu = IMUSensor(IMU.create(
    "/World/Box/Imu",
    translations=[[0, 0, 0]],
    linear_acceleration_filter_size=10,
))
contact = ContactSensor(Contact.create(
    "/World/Box/Contact",
    translations=[[0, 0, -0.1]],
    min_threshold=0.0, max_threshold=1000.0, radius=0.2,
))
```

Contact 센서는 충돌 정보를 읽을 수 있도록 필요한 Contact Report 설정을 적용한다. 접촉 위치와 센서의 radius가 맞아야 한다. 이 실습에서는 0.2 m 상자의 바닥 중심에 센서를 두고 바닥의 접촉점들을 포함한다.

## 2. 중력 포함 여부를 구분하다

```python
with_gravity = imu.get_data(read_gravity=True)
without_gravity = imu.get_data(read_gravity=False)
print(with_gravity["linear_acceleration"])
print(without_gravity["linear_acceleration"])
```

정지한 몸체에서 가속도계의 출력은 중력을 포함하는지에 따라 달라진다. 단순히 모든 축이 0이 아니라고 노이즈라 판단하지 않는다. 이 실습의 정지 검사는 `read_gravity=False`를 사용한다. 중력을 포함한 값은 센서 좌표계의 방향과 함께 해석한다.

필터 크기를 늘리면 갑작스러운 측정 변화가 완만해지지만 반응도 늦어진다. 물리 모델이 발산하는 문제를 큰 필터로 덮어서는 안 된다.

## 3. Script Editor에서 완결 실습을 실행하다

Isaac Sim GUI에서 Window → Extensions를 열고 `isaacsim.sensors.experimental.physics`를 켠다. Window → Script Editor를 연 뒤 다음 코드를 한 번 실행한다. `OUTPUT` 한 곳을 자신의 저장소 안 절대 경로로 바꾼다. 이 코드는 현재 장면을 새 장면으로 바꾸므로 이전 실습은 먼저 저장한다.

```python
import asyncio
import json
from pathlib import Path
import traceback
import numpy as np
import omni.kit.app
import omni.timeline
import omni.usd
from pxr import Gf, UsdGeom, UsdPhysics, UsdLux
from isaacsim.sensors.experimental.physics import IMU, IMUSensor, Contact, ContactSensor

OUTPUT = Path("/home/YOUR_NAME/robotics-sim-tutorial-kr/artifacts/imu-contact")

async def physics_sensor_lab():
    report = {"passed": False, "read_gravity": False}
    rows = []
    timeline = omni.timeline.get_timeline_interface()
    try:
        timeline.stop()
        await omni.usd.get_context().new_stage_async()
        stage = omni.usd.get_context().get_stage()
        UsdGeom.SetStageMetersPerUnit(stage, 1.0)
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
        UsdGeom.Xform.Define(stage, "/World")
        scene = UsdPhysics.Scene.Define(stage, "/World/PhysicsScene")
        scene.CreateGravityDirectionAttr(Gf.Vec3f(0, 0, -1))
        scene.CreateGravityMagnitudeAttr(9.81)
        floor = UsdGeom.Cube.Define(stage, "/World/Floor")
        floor.CreateSizeAttr(1.0)
        floor.AddTranslateOp().Set(Gf.Vec3d(0, 0, -0.05))
        floor.AddScaleOp().Set(Gf.Vec3f(4, 4, 0.1))
        UsdPhysics.CollisionAPI.Apply(floor.GetPrim())
        box = UsdGeom.Cube.Define(stage, "/World/Box")
        box.CreateSizeAttr(0.2)
        box.AddTranslateOp().Set(Gf.Vec3d(0, 0, 0.5))
        UsdPhysics.RigidBodyAPI.Apply(box.GetPrim())
        UsdPhysics.CollisionAPI.Apply(box.GetPrim())
        UsdPhysics.MassAPI.Apply(box.GetPrim()).CreateMassAttr(1.0)
        UsdLux.DomeLight.Define(stage, "/World/Light").CreateIntensityAttr(1000)
        imu = IMUSensor(IMU.create("/World/Box/Imu",
                                  linear_acceleration_filter_size=10))
        contact = ContactSensor(Contact.create(
            "/World/Box/Contact", translations=[[0, 0, -0.1]],
            min_threshold=0.0, max_threshold=1000.0, radius=0.2))
        timeline.play()
        for tick in range(360):
            await omni.kit.app.get_app().next_update_async()
            if tick < 240:  # 낙하와 접촉 직후의 과도 구간은 분리한다.
                continue
            frame = imu.get_data(read_gravity=False)
            c = contact.get_data()
            if not frame or not c or not contact.get_sensor_reading().is_valid:
                raise RuntimeError("유효한 물리 센서 데이터가 없다")
            a = np.asarray(frame["linear_acceleration"], dtype=float)
            w = np.asarray(frame["angular_velocity"], dtype=float)
            q = np.asarray(frame["orientation"], dtype=float)
            if a.shape != (3,) or w.shape != (3,) or q.shape != (4,):
                raise RuntimeError("예상한 센서 배열 형태가 아니다")
            if not np.isfinite(np.r_[a, w, q, c["force"]]).all():
                raise RuntimeError("센서 값에 NaN 또는 inf가 있다")
            if abs(np.linalg.norm(q)-1) > 0.01:
                raise RuntimeError("IMU 자세 quaternion이 단위 quaternion이 아니다")
            rows.append([float(frame["time"]), float(frame["physics_step"]),
                         *a, *w, *q, float(c["force"]), float(c["in_contact"])])
        values = np.asarray(rows)
        if len(values) < 60 or values[-1, 1] <= 0 or not np.all(np.diff(values[:, 1]) > 0):
            raise RuntimeError("표본이 부족하거나 physics_step이 증가하지 않는다")
        tail = values[-60:]
        accel = float(np.median(np.linalg.norm(tail[:, 2:5], axis=1)))
        gyro = float(np.median(np.linalg.norm(tail[:, 5:8], axis=1)))
        force = float(np.median(tail[:, 12]))
        if accel > 0.5 or gyro > 0.1 or not 7.0 < force < 13.0:
            raise RuntimeError(f"정지 상태 검사 실패: a={accel}, w={gyro}, F={force}")
        if not np.all(tail[:, 13] == 1):
            raise RuntimeError("마지막 정지 구간에서 접촉이 끊어진다")
        report.update(passed=True, samples=len(rows), median_acceleration=accel,
                      median_angular_velocity=gyro, median_contact_force_n=force)
    except Exception as error:
        report.update(passed=False, error=str(error), traceback=traceback.format_exc())
    finally:
        timeline.stop()
        OUTPUT.mkdir(parents=True, exist_ok=True)
        np.save(OUTPUT / "physics_sensor_samples.npy", np.asarray(rows))
        (OUTPUT / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False))
        print(json.dumps(report, indent=2, ensure_ascii=False))

physics_sensor_task = asyncio.ensure_future(physics_sensor_lab())
```

Script Editor에서는 이미 앱이 실행 중이므로 `SimulationApp`을 다시 만들지 않는다. `next_update_async()`로 앱에 제어권을 돌려주어 GUI와 물리 스텝이 진행되게 한다. 이 단계의 실행 코드는 위 전체 블록이며 별도 `.py` 파일 실행이 필요한 단계는 아니다.

## 기대 결과와 문제 진단

1 kg 상자가 내려와 바닥에 멈춘다. 마지막 정지 구간에서 중력을 제외한 가속도와 각속도는 작고 접촉력은 약 9.81 N 부근이다. 교육용 허용 범위는 코드에서 7~13 N으로 설정했다. 상자와 바닥의 물성, 시간 간격을 바꾸면 이 판정 조건도 다시 검토한다.

- 데이터가 없다면 센서의 부모가 Rigid Body인지, Play 상태인지 확인한다.
- 접촉력이 0이라면 바닥 Collider와 Contact 위치·반경을 확인한다.
- IMU에서 큰 순간값이 나왔다면 충돌 직후인지 정지 구간인지 구분한다.
- 접촉력으로 로봇의 구동 토크를 직접 추정하지 않는다. 관절의 effort와 바닥 접촉력은 측정 위치와 의미가 다르다.

이 코드의 API는 6.0.1 공식 문서에 대조했지만, 작성 환경에 GPU와 Isaac Sim이 없어 실제 낙하·센서 측정은 실행하지 못했다. 출력된 보고서를 확인한 뒤 다음 단계로 진행한다.

## 확인 과제

중력을 포함한 IMU 출력과 제외한 출력을 동시에 기록하고, 정지 자세를 바꾸었을 때 어느 축이 달라지는지 설명한다. 필터 크기 1과 10의 충돌 직후 응답도 비교한다. 비교 실험은 서로 다른 결과 폴더에 저장한다.

## 공식 참고 자료

- [6.0.1 Physics Sensors 이전 안내](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/migration_guides/isaac_sim_6_0/sensors_physics_to_experimental_physics.html)
- [6.0.1 IMU/Contact Authoring·Runtime API](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/py/source/extensions/isaacsim.sensors.experimental.physics/docs/index.html)
- [6.0.1 IMU의 측정 의미](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/sensors/isaacsim_sensors_physics_imu.html)

[이전](25-rtx-lidar.md) · [다음](27-project-sensor-lab.md)
