"""Measure Isaac Sim real time factor and publish std_msgs/Float32."""
import argparse
import time

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--steps", type=int, default=None, help="Simulation steps before exit; omitted: GUI until closed, headless 1200")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--delay", type=float, default=0.0, help="extra wall seconds per frame")
    args = parser.parse_args()
    if (args.steps is not None and args.steps < 1) or args.delay < 0:
        parser.error("steps must be positive; delay must be nonnegative")
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
        og.Controller.edit({"graph_path": "/RTFGraph", "evaluator_name": "execution"}, {
            keys.CREATE_NODES: [("Tick", "omni.graph.action.OnPlaybackTick"),
                ("Context", "isaacsim.ros2.bridge.ROS2Context"),
                ("RTF", "isaacsim.core.nodes.IsaacRealTimeFactor"),
                ("Publisher", "isaacsim.ros2.bridge.ROS2Publisher")],
            keys.SET_VALUES: [("Publisher.inputs:topicName", "/topic"),
                ("Publisher.inputs:messagePackage", "std_msgs"),
                ("Publisher.inputs:messageSubfolder", "msg"),
                ("Publisher.inputs:messageName", "Float32"),
                ("Context.inputs:useDomainIDEnvVar", True)],
            keys.CONNECT: [("Tick.outputs:tick", "Publisher.inputs:execIn"),
                ("Context.outputs:context", "Publisher.inputs:context")]})
        app.update()
        og.Controller.connect(og.Controller.attribute("/RTFGraph/RTF.outputs:rtf"),
                              og.Controller.attribute("/RTFGraph/Publisher.inputs:data"))
        world.reset()
        frame = 0
        while app.is_running() and (args.steps is None or frame < args.steps):
            world.step(render=True)
            if frame % 60 == 0:
                print("measured_rtf=", og.Controller.attribute("/RTFGraph/RTF.outputs:rtf").get())
            if args.delay:
                time.sleep(args.delay)
            frame += 1
        world.stop()
    finally:
        app.close()

if __name__ == "__main__":
    main()
