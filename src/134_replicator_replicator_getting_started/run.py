"""Four independent Replicator lessons: writer, multi-camera, events and randomizers."""
import argparse
import json
from pathlib import Path
import random


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--example", choices=["basic", "multi", "randomize", "events"], default="basic")
    parser.add_argument("--frames", type=int, default=4)
    parser.add_argument("--steps", type=int, default=None, help="Maximum physics updates in events mode; omitted: 300 for capture, then GUI stays open")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--rt-subframes", type=int, default=4)
    parser.add_argument("--pose-writer", action="store_true", help="Also attach PoseWriter in multi mode")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    keep_open = args.steps is None and not args.headless
    capture_steps = args.steps if args.steps is not None else 300
    if min(args.frames, capture_steps, args.rt_subframes) < 1:
        parser.error("frames, steps and rt-subframes must be positive")
    output = (args.output or Path(__file__).with_name("output") / args.example).resolve()
    if output.exists():
        parser.error(f"Choose a fresh --output: {output}")
    output.mkdir(parents=True)
    from isaacsim import SimulationApp
    # SimulationApp은 Python에서 Isaac Sim의 Kit 애플리케이션을 시작하고 갱신·종료하는 클래스이다.
    # headless=True는 창 없이 실행한다는 뜻이며, omni와 Isaac Sim 확장 모듈은 앱 생성 후 import한다.
    app = SimulationApp({"headless": args.headless})
    try:
        import carb.settings
        # carb.settings는 경로 형태의 키로 Kit의 렌더링·시뮬레이션 설정을 읽고 변경하는 API이다.
        import numpy as np
        import omni.replicator.core as rep
        # omni.replicator.core는 장면 무작위화와 합성 데이터 생성을 위한 API이다.
        # render product는 카메라의 렌더링 출력이며, annotator는 데이터를 추출하고 writer는 결과를 저장한다.
        import omni.timeline
        # omni.timeline은 시뮬레이션 시간과 재생·일시정지·정지를 제어하는 API이다.
        import omni.usd
        # omni.usd는 현재 Kit 애플리케이션의 USD 문맥에 접근하는 모듈이다.
        # get_context().get_stage()로 객체·조명 등이 들어 있는 현재 Stage를 얻는다.
        from isaacsim.core.utils.semantics import add_labels
        # add_labels는 Prim에 의미 라벨을 부여하여 합성 데이터에서 객체의 클래스를 구분할 수 있게 한다.
        from pxr import UsdGeom, UsdLux, UsdPhysics
        # pxr은 USD 장면을 직접 다루는 OpenUSD의 Python 바인딩이다.
        # UsdGeom은 형상, 변환, 카메라와 장면 단위·축 설정을 다룬다.
        # UsdLux는 조명 Prim과 빛의 속성을 다룬다.
        # UsdPhysics는 강체·충돌·관절·물리 재질의 USD 스키마를 다룬다.
        # 새 USD Stage를 열어 이 예제의 장면을 구성한다.
        omni.usd.get_context().new_stage()
        stage = omni.usd.get_context().get_stage()
        # USD 장면에서 위쪽으로 사용할 축을 지정한다.
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
        # USD 좌표 한 단위가 몇 미터인지 지정하여 장면의 길이 단위를 맞춘다.
        UsdGeom.SetStageMetersPerUnit(stage, 1.0)
        # 타임라인 재생에 따른 자동 캡처 여부를 설정한다. False이면 아래의 명시적 캡처 호출로 제어한다.
        rep.orchestrator.set_capture_on_play(False)
        carb.settings.get_settings().set("/rtx/post/dlss/execMode", 2)
        # Replicator가 사용할 난수 시드를 설정하여 무작위화 결과를 재현하기 쉽게 한다.
        rep.set_global_seed(42)
        random.seed(42)
        # 주변을 둘러싸는 DomeLight를 생성하여 장면의 환경 조명을 설정한다.
        UsdLux.DomeLight.Define(stage, "/World/Light").CreateIntensityAttr(600)
        # USD Stage에 Cube 형상을 직접 정의한다. 물리 동작이 필요하면 강체·충돌 API를 별도로 적용한다.
        cube = UsdGeom.Cube.Define(stage, "/World/Cube")
        cube.CreateSizeAttr(0.6)
        translation = cube.AddTranslateOp()
        translation.Set((0, 0, 2 if args.example == "events" else 0))
        add_labels(cube.GetPrim(), labels=["carton"], instance_name="class")
        camera = rep.create.camera(position=(4, 4, 3), look_at=(0, 0, 1 if args.example == "events" else 0))
        # 카메라와 해상도를 연결한 render product를 만든다. 이후 annotator나 writer를 여기에 연결한다.
        products = [rep.create.render_product(camera, (512, 512), name="front")]
        writers = []
        rgb_annotators = []
        # 등록된 writer를 선택하여 이미지와 주석 데이터의 저장 형식을 정한다.
        writer = rep.writers.get("BasicWriter")
        writer.initialize(output_dir=str(output), rgb=True, bounding_box_2d_tight=True,
                          semantic_segmentation=True, colorize_semantic_segmentation=True)
        writers.append(writer)
        if args.example == "multi":
            camera2 = rep.create.camera(position=(-4, 3, 2), look_at=(0, 0, 0))
            products.append(rep.create.render_product(camera2, (320, 240), name="side"))

            def serializable(value):
                if isinstance(value, np.ndarray):
                    return value.tolist()
                if isinstance(value, np.generic):
                    return value.item()
                if isinstance(value, dict):
                    return {str(k): serializable(v) for k, v in value.items()}
                if isinstance(value, (tuple, list)):
                    return [serializable(v) for v in value]
                return value

            class CameraMetadataWriter(rep.Writer):
                def __init__(self):
                    self.data_structure = "renderProduct"
                    # 이름으로 annotator를 가져와 렌더링 결과에서 필요한 데이터를 추출한다.
                    self.annotators = [rep.annotators.get("camera_params"), rep.annotators.get("bounding_box_3d")]
                    self.frame = 0

                def write(self, data):
                    (output / f"camera_metadata_{self.frame:04d}.json").write_text(json.dumps(serializable(data), indent=2))
                    self.frame += 1

            writers.append(CameraMetadataWriter())
            if args.pose_writer:
                pose = rep.writers.get("PoseWriter")
                pose.initialize(output_dir=str(output / "pose"), write_debug_images=True, skip_empty_frames=False)
                writers.append(pose)
            for product in products:
                annotator = rep.annotators.get("rgb")
                # annotator를 render product에 연결하여 렌더링 결과에서 해당 데이터를 추출하게 한다.
                annotator.attach(product)
                rgb_annotators.append(annotator)
        for item in writers:
            item.attach(products)
        if args.example == "randomize":
            # 이름을 지정한 이벤트가 발생했을 때 실행할 Replicator 작업을 정의한다.
            with rep.trigger.on_custom_event(event_name="change_light"):
                rep.create.light(light_type="Dome", intensity=600, color=rep.distribution.uniform((0.2, 0.2, 0.2), (1, 1, 1)))
        observations = []
        captures = 0
        if args.example == "events":
            # 중력 등 물리 시뮬레이션의 공통 설정을 저장할 PhysicsScene을 정의한다.
            physics = UsdPhysics.Scene.Define(stage, "/World/PhysicsScene")
            physics.CreateGravityDirectionAttr((0, 0, -1))
            physics.CreateGravityMagnitudeAttr(9.81)
            # 형상 Prim에 충돌 API를 적용하여 접촉 계산에 참여하게 한다.
            UsdPhysics.CollisionAPI.Apply(cube.GetPrim())
            # Prim에 강체 API를 적용하여 물리 시뮬레이션이 자세와 속도를 계산할 수 있게 한다.
            UsdPhysics.RigidBodyAPI.Apply(cube.GetPrim())
            timeline = omni.timeline.get_timeline_interface()
            timeline.play()
            previous_height = 2.0
            for step in range(capture_steps):
                # Kit의 한 프레임을 갱신하여 렌더링·이벤트·비동기 작업을 처리한다.
                # 물리 진행 여부는 현재 타임라인의 재생 상태와 설정에 따라 달라진다.
                app.update()
                height = float(translation.Get()[2])
                if height < 0:
                    break
                if previous_height - height >= 0.4:
                    timeline.pause()
                    # Replicator의 캡처를 한 번 진행한다. rt_subframes는 캡처를 위한 렌더링 누적 프레임 수이다.
                    rep.orchestrator.step(delta_time=0.0, rt_subframes=args.rt_subframes)
                    UsdGeom.Imageable(cube).MakeInvisible()
                    try:
                        rep.orchestrator.step(delta_time=0.0, rt_subframes=args.rt_subframes)
                    finally:
                        UsdGeom.Imageable(cube).MakeVisible()
                    observations.append({"step":step,"height":height,"pair":[captures,captures+1]})
                    captures += 2
                    previous_height = height
                    if captures >= args.frames * 2:
                        break
                    timeline.play()
            timeline.stop()
            if not observations:
                raise RuntimeError("No falling-height event observed; inspect physics and USD transform updates")
        else:
            for frame in range(args.frames):
                if args.example == "randomize":
                    translation.Set((random.uniform(-1, 1), random.uniform(-1, 1), 0))
                    if frame % 2 == 0:
                        # 등록한 사용자 이벤트를 발생시켜 해당 Replicator 무작위화 그래프를 실행하게 한다.
                        rep.utils.send_og_event(event_name="change_light")
                rep.orchestrator.step(delta_time=0.0, rt_subframes=args.rt_subframes)
                observations.append({"frame":frame,"position":list(translation.Get()),
                                     "rgb_shapes":[list(a.get_data().shape) for a in rgb_annotators]})
                captures += 1
        # 예약된 합성 데이터 처리와 writer의 저장 작업이 끝날 때까지 기다린다.
        rep.orchestrator.wait_until_complete()
        for item in writers:
            item.detach()
        for annotator in rgb_annotators:
            annotator.detach()
        for product in products:
            product.destroy()
        (output / "observations.json").write_text(json.dumps(observations, indent=2))
        print(f"Capture steps: {captures}; actual observations: {output / 'observations.json'}")
        while keep_open and app.is_running():
            app.update()
    finally:
        # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
        app.close()


if __name__ == "__main__":
    main()
