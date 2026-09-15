"""Rename Franka ROS joint and TF names while preserving USD prim paths."""
import argparse

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--steps", type=int, default=None, help="Simulation steps before exit; omitted: GUI until closed, headless 3600")
    parser.add_argument("--headless", action="store_true")
    args = parser.parse_args()
    if args.steps is not None and args.steps < 1:
        parser.error("--steps must be positive")
    if args.steps is None and args.headless:
        args.steps = 3600
    from isaacsim import SimulationApp
    app = SimulationApp({"headless": args.headless})
    try:
        import omni.graph.core as og
        from isaacsim.core.api import World
        from isaacsim.core.prims import SingleArticulation
        from isaacsim.core.utils.extensions import enable_extension
        from isaacsim.core.utils.stage import add_reference_to_stage
        from isaacsim.storage.native import get_assets_root_path
        enable_extension("isaacsim.ros2.bridge")
        app.update()
        world = World(stage_units_in_meters=1.0, physics_dt=1/60, rendering_dt=1/60)
        world.scene.add_default_ground_plane()
        root = get_assets_root_path()
        if not root:
            raise RuntimeError("Isaac 5.1 asset root unavailable")
        add_reference_to_stage(root + "/Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd", "/panda")
        robot = world.scene.add(SingleArticulation(prim_path="/panda", name="panda"))
        keys = og.Controller.Keys
        nodes = [("Tick", "omni.graph.action.OnPlaybackTick"), ("Context", "isaacsim.ros2.bridge.ROS2Context"),
                 ("Time", "isaacsim.core.nodes.IsaacReadSimulationTime"),
                 ("Publish", "isaacsim.ros2.bridge.ROS2PublishJointState"),
                 ("Subscribe", "isaacsim.ros2.bridge.ROS2SubscribeJointState"),
                 ("Actuator", "isaacsim.core.nodes.IsaacArticulationController")]
        links = [("Tick.outputs:tick", n + ".inputs:execIn") for n in ["Publish", "Subscribe", "Actuator"]]
        links += [("Context.outputs:context", n + ".inputs:context") for n in ["Publish", "Subscribe"]]
        links += [("Time.outputs:simulationTime", "Publish.inputs:timeStamp")]
        links += [("Subscribe.outputs:" + field, "Actuator.inputs:" + field)
                  for field in ["jointNames", "positionCommand", "velocityCommand", "effortCommand"]]
        values = [("Context.inputs:useDomainIDEnvVar", True), ("Publish.inputs:targetPrim", ["/panda"]),
                  ("Actuator.inputs:robotPath", "/panda"), ("Publish.inputs:topicName", "/joint_states"),
                  ("Subscribe.inputs:topicName", "/joint_command")]
        from pxr import Sdf, UsdPhysics
        matches = [prim for prim in world.stage.Traverse()
                   if prim.GetName() == "panda_joint1" and prim.IsA(UsdPhysics.Joint)]
        if len(matches) != 1:
            raise RuntimeError(f"Expected one panda_joint1, found {len(matches)}")
        matches[0].CreateAttribute("isaac:nameOverride", Sdf.ValueTypeNames.String).Set("shoulder_pan")
        link = world.stage.GetPrimAtPath("/panda/panda_link0")
        if not link.IsValid():
            raise RuntimeError("Expected /panda/panda_link0 for TF name exercise")
        link.CreateAttribute("isaac:nameOverride", Sdf.ValueTypeNames.String).Set("robot_base")
        nodes += [("Resolver", "isaacsim.core.nodes.IsaacJointNameResolver"),
                  ("TF", "isaacsim.ros2.bridge.ROS2PublishTransformTree")]
        links.remove(("Subscribe.outputs:jointNames", "Actuator.inputs:jointNames"))
        links.remove(("Tick.outputs:tick", "Actuator.inputs:execIn"))
        links += [("Tick.outputs:tick", "Resolver.inputs:execIn"),
                  ("Subscribe.outputs:jointNames", "Resolver.inputs:jointNames"),
                  ("Resolver.outputs:jointNames", "Actuator.inputs:jointNames"),
                  ("Resolver.outputs:execOut", "Actuator.inputs:execIn"),
                  ("Tick.outputs:tick", "TF.inputs:execIn"),
                  ("Context.outputs:context", "TF.inputs:context"),
                  ("Time.outputs:simulationTime", "TF.inputs:timeStamp")]
        values += [("Resolver.inputs:robotPath", "/panda"), ("TF.inputs:targetPrims", ["/panda"]),
                   ("TF.inputs:topicName", "/tf")]
        print("USD path remains", str(matches[0].GetPath()), "ROS alias=shoulder_pan")
        og.Controller.edit({"graph_path": "/JointGraph", "evaluator_name": "execution"},
                           {keys.CREATE_NODES: nodes, keys.CONNECT: links, keys.SET_VALUES: values})
        world.reset()
        print("actual_joint_names=", robot.dof_names)
        frame = 0
        while app.is_running() and (args.steps is None or frame < args.steps):
            world.step(render=True)
            if frame % 120 == 0:
                print("joint_positions_rad=", robot.get_joint_positions().tolist())
            frame += 1
        world.stop()
    finally:
        app.close()

if __name__ == "__main__":
    main()
