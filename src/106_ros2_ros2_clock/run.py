"""Publish or receive ROS clock through an Isaac Sim 5.1 OmniGraph."""
import argparse

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["simulation", "system", "subscribe"], default="simulation")
    parser.add_argument("--steps", type=int, default=None, help="Simulation steps before exit; omitted: GUI until closed, headless 1200")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--reset-on-stop", action="store_true")
    args = parser.parse_args()
    if args.steps is not None and args.steps < 1:
        parser.error("--steps must be positive")
    if args.steps is None and args.headless:
        args.steps = 1200
    from isaacsim import SimulationApp
    # SimulationApp은 Python에서 Isaac Sim의 Kit 애플리케이션을 시작하고 갱신·종료하는 클래스이다.
    # headless=True는 창 없이 실행한다는 뜻이며, omni와 Isaac Sim 확장 모듈은 앱 생성 후 import한다.
    app = SimulationApp({"headless": args.headless})
    try:
        import omni.graph.core as og
        # omni.graph.core는 노드와 연결로 실행 흐름을 구성하는 OmniGraph API이다.
        # Controller.edit에서 노드 생성, 입력값 설정, 출력과 입력의 연결을 정의한다.
        from isaacsim.core.api import World
        # World는 Stage의 객체와 작업을 관리하고 물리·렌더링 시간 간격, 초기화, 시뮬레이션 진행을 제어한다.
        from isaacsim.core.utils.extensions import enable_extension
        # enable_extension은 이름으로 지정한 Kit 확장을 활성화하여 해당 기능과 명령을 사용할 수 있게 한다.
        enable_extension("isaacsim.ros2.bridge")
        # Kit의 한 프레임을 갱신하여 렌더링·이벤트·비동기 작업을 처리한다.
        # 물리 진행 여부는 현재 타임라인의 재생 상태와 설정에 따라 달라진다.
        app.update()
        # stage_units_in_meters는 장면 길이 단위이고, physics_dt·rendering_dt는 각각 물리·렌더링 시간 간격(초)이다.
        world = World(stage_units_in_meters=1.0, physics_dt=1/60, rendering_dt=1/60)
        keys = og.Controller.Keys
        nodes = [("Tick", "omni.graph.action.OnPlaybackTick"), ("Context", "isaacsim.ros2.bridge.ROS2Context")]
        links = [("Tick.outputs:tick", "Clock.inputs:execIn"), ("Context.outputs:context", "Clock.inputs:context")]
        values = [("Clock.inputs:topicName", "/clock"), ("Context.inputs:useDomainIDEnvVar", True)]
        if args.mode == "subscribe":
            nodes.append(("Clock", "isaacsim.ros2.bridge.ROS2SubscribeClock"))
        else:
            nodes.append(("Clock", "isaacsim.ros2.bridge.ROS2PublishClock"))
            kind = "IsaacReadSystemTime" if args.mode == "system" else "IsaacReadSimulationTime"
            field = "systemTime" if args.mode == "system" else "simulationTime"
            nodes.append(("Time", "isaacsim.core.nodes." + kind))
            links.append(("Time.outputs:" + field, "Clock.inputs:timeStamp"))
            if args.mode == "simulation":
                values.append(("Time.inputs:resetOnStop", args.reset_on_stop))
        # OmniGraph의 노드와 입력값을 만들고 포트를 연결한다.
        # 실행 포트는 처리 순서를, 데이터 포트는 시간·센서·관절 값의 전달 경로를 정한다.
        og.Controller.edit({"graph_path": "/ClockGraph", "evaluator_name": "execution"},
                           {keys.CREATE_NODES: nodes, keys.CONNECT: links, keys.SET_VALUES: values})
        # World를 초기화하고 등록된 객체의 물리 핸들을 준비한다. 관절·강체 상태를 읽기 전에 호출한다.
        world.reset()
        frame = 0
        while app.is_running() and (args.steps is None or frame < args.steps):
            # 물리 시뮬레이션을 한 step 진행한다. render는 이 호출에서 렌더링도 수행할지 지정한다.
            world.step(render=True)
            if args.mode == "subscribe" and frame % 60 == 0:
                print("received_clock_seconds=", og.Controller.attribute("/ClockGraph/Clock.outputs:timeStamp").get())
            frame += 1
        world.stop()
    finally:
        # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
        app.close()

if __name__ == "__main__":
    main()
