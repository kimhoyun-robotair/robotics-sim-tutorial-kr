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
    app = SimulationApp({"headless": args.headless})
    try:
        import omni.graph.core as og
        from isaacsim.core.api import World
        from isaacsim.core.utils.extensions import enable_extension
        enable_extension("isaacsim.ros2.bridge")
        app.update()
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
        og.Controller.edit({"graph_path": "/ClockGraph", "evaluator_name": "execution"},
                           {keys.CREATE_NODES: nodes, keys.CONNECT: links, keys.SET_VALUES: values})
        world.reset()
        frame = 0
        while app.is_running() and (args.steps is None or frame < args.steps):
            world.step(render=True)
            if args.mode == "subscribe" and frame % 60 == 0:
                print("received_clock_seconds=", og.Controller.attribute("/ClockGraph/Clock.outputs:timeStamp").get())
            frame += 1
        world.stop()
    finally:
        app.close()

if __name__ == "__main__":
    main()
