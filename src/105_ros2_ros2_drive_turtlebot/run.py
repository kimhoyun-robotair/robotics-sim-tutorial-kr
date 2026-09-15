"""Drive the official TurtleBot3 USD with a ROS 2 Twist OmniGraph."""
import argparse

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--steps", type=int, default=None, help="Simulation steps before exit; omitted: GUI until closed, headless 3600")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--robot-usd", help="optional locally imported TurtleBot USD")
    args = parser.parse_args()
    if args.steps is not None and args.steps < 1:
        parser.error("--steps must be positive")
    if args.steps is None and args.headless:
        args.steps = 3600
    from isaacsim import SimulationApp
    app = SimulationApp({"headless": args.headless})
    try:
        import numpy as np
        import omni.graph.core as og
        from pxr import UsdPhysics
        from isaacsim.core.api import World
        from isaacsim.core.prims import SingleArticulation
        from isaacsim.core.utils.extensions import enable_extension
        from isaacsim.core.utils.stage import add_reference_to_stage
        from isaacsim.storage.native import get_assets_root_path
        enable_extension("isaacsim.ros2.bridge")
        enable_extension("isaacsim.robot.wheeled_robots")
        app.update()
        world = World(stage_units_in_meters=1.0, physics_dt=1/60, rendering_dt=1/60)
        world.scene.add_default_ground_plane()
        root = get_assets_root_path() if not args.robot_usd else None
        if not args.robot_usd and not root:
            raise RuntimeError("Isaac 5.1 asset root unavailable; use --robot-usd")
        usd = args.robot_usd or root + "/Isaac/Robots/Turtlebot/Turtlebot3/turtlebot3_burger.usd"
        robot_prim = add_reference_to_stage(usd_path=usd, prim_path="/World/turtlebot3_burger")
        # The lesson uses one root at the robot prim, as specified by the official graph workflow.
        for prim in world.stage.Traverse():
            if prim.GetPath().HasPrefix(robot_prim.GetPath()) and prim.HasAPI(UsdPhysics.ArticulationRootAPI):
                prim.RemoveAPI(UsdPhysics.ArticulationRootAPI)
        UsdPhysics.ArticulationRootAPI.Apply(robot_prim)
        robot = world.scene.add(SingleArticulation(prim_path=str(robot_prim.GetPath()), name="turtlebot", position=np.array([0.,0.,0.05])))
        keys = og.Controller.Keys
        og.Controller.edit({"graph_path": "/DriveGraph", "evaluator_name": "execution"}, {
            keys.CREATE_NODES: [("Tick", "omni.graph.action.OnPlaybackTick"),
                ("Context", "isaacsim.ros2.bridge.ROS2Context"),
                ("Twist", "isaacsim.ros2.bridge.ROS2SubscribeTwist"),
                ("Linear", "omni.graph.nodes.BreakVector3"),
                ("Angular", "omni.graph.nodes.BreakVector3"),
                ("Differential", "isaacsim.robot.wheeled_robots.DifferentialController"),
                ("Actuator", "isaacsim.core.nodes.IsaacArticulationController")],
            keys.SET_VALUES: [("Context.inputs:useDomainIDEnvVar", True), ("Twist.inputs:topicName", "/cmd_vel"),
                ("Differential.inputs:wheelRadius", 0.025), ("Differential.inputs:wheelDistance", 0.16),
                ("Differential.inputs:maxLinearSpeed", 0.22), ("Differential.inputs:maxAngularSpeed", 1.0),
                ("Actuator.inputs:robotPath", "/World/turtlebot3_burger"),
                ("Actuator.inputs:jointNames", ["wheel_left_joint", "wheel_right_joint"])],
            keys.CONNECT: [("Tick.outputs:tick", "Twist.inputs:execIn"),
                ("Tick.outputs:tick", "Differential.inputs:execIn"), ("Tick.outputs:tick", "Actuator.inputs:execIn"),
                ("Context.outputs:context", "Twist.inputs:context"),
                ("Twist.outputs:linearVelocity", "Linear.inputs:tuple"),
                ("Twist.outputs:angularVelocity", "Angular.inputs:tuple"),
                ("Linear.outputs:x", "Differential.inputs:linearVelocity"),
                ("Angular.outputs:z", "Differential.inputs:angularVelocity"),
                ("Differential.outputs:velocityCommand", "Actuator.inputs:velocityCommand")]})
        world.reset()
        print("actual_joint_names=", robot.dof_names)
        frame = 0
        while app.is_running() and (args.steps is None or frame < args.steps):
            world.step(render=True)
            if frame % 120 == 0:
                print("position_m=", robot.get_world_pose()[0].tolist(), "wheel_commands_rad_s=",
                      og.Controller.attribute("/DriveGraph/Differential.outputs:velocityCommand").get())
            frame += 1
        world.stop()
    finally:
        app.close()

if __name__ == "__main__":
    main()
