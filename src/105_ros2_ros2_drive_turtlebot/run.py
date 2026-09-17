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
    # SimulationApp은 Python에서 Isaac Sim의 Kit 애플리케이션을 시작하고 갱신·종료하는 클래스이다.
    # headless=True는 창 없이 실행한다는 뜻이며, omni와 Isaac Sim 확장 모듈은 앱 생성 후 import한다.
    app = SimulationApp({"headless": args.headless})
    try:
        import numpy as np
        import omni.graph.core as og
        # omni.graph.core는 노드와 연결로 실행 흐름을 구성하는 OmniGraph API이다.
        # Controller.edit에서 노드 생성, 입력값 설정, 출력과 입력의 연결을 정의한다.
        from pxr import UsdPhysics
        # pxr은 USD 장면을 직접 다루는 OpenUSD의 Python 바인딩이다.
        # UsdPhysics는 강체·충돌·관절·물리 재질의 USD 스키마를 다룬다.
        from isaacsim.core.api import World
        # World는 Stage의 객체와 작업을 관리하고 물리·렌더링 시간 간격, 초기화, 시뮬레이션 진행을 제어한다.
        from isaacsim.core.prims import SingleArticulation
        # SingleArticulation은 하나의 관절 구조를 감싸 관절 위치·속도·힘을 읽고 제어한다.
        from isaacsim.core.utils.extensions import enable_extension
        # enable_extension은 이름으로 지정한 Kit 확장을 활성화하여 해당 기능과 명령을 사용할 수 있게 한다.
        from isaacsim.core.utils.stage import add_reference_to_stage
        # add_reference_to_stage는 외부 USD 자산을 현재 Stage의 지정한 Prim 경로에 참조로 연결한다.
        from isaacsim.storage.native import get_assets_root_path
        # get_assets_root_path는 Isaac Sim 기본 자산의 루트 경로를 찾는다.
        # 반환 경로에 로봇·환경 USD의 상대 경로를 붙여 사용할 수 있다.
        enable_extension("isaacsim.ros2.bridge")
        enable_extension("isaacsim.robot.wheeled_robots")
        # Kit의 한 프레임을 갱신하여 렌더링·이벤트·비동기 작업을 처리한다.
        # 물리 진행 여부는 현재 타임라인의 재생 상태와 설정에 따라 달라진다.
        app.update()
        # stage_units_in_meters는 장면 길이 단위이고, physics_dt·rendering_dt는 각각 물리·렌더링 시간 간격(초)이다.
        world = World(stage_units_in_meters=1.0, physics_dt=1/60, rendering_dt=1/60)
        # 기본 바닥을 Scene에 추가한다. 이 바닥은 강체가 떨어졌을 때 충돌할 표면이다.
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
        # 관절로 연결된 구조의 articulation 루트를 지정한다.
        UsdPhysics.ArticulationRootAPI.Apply(robot_prim)
        # 생성한 객체를 World의 Scene에 등록하여 이름으로 찾고 초기화할 수 있게 한다.
        robot = world.scene.add(SingleArticulation(prim_path=str(robot_prim.GetPath()), name="turtlebot", position=np.array([0.,0.,0.05])))
        keys = og.Controller.Keys
        # OmniGraph의 노드와 입력값을 만들고 포트를 연결한다.
        # 실행 포트는 처리 순서를, 데이터 포트는 시간·센서·관절 값의 전달 경로를 정한다.
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
        # World를 초기화하고 등록된 객체의 물리 핸들을 준비한다. 관절·강체 상태를 읽기 전에 호출한다.
        world.reset()
        print("actual_joint_names=", robot.dof_names)
        frame = 0
        while app.is_running() and (args.steps is None or frame < args.steps):
            # 물리 시뮬레이션을 한 step 진행한다. render는 이 호출에서 렌더링도 수행할지 지정한다.
            world.step(render=True)
            if frame % 120 == 0:
                # 로봇의 월드 위치와 회전 쿼터니언을 읽는다.
                print("position_m=", robot.get_world_pose()[0].tolist(), "wheel_commands_rad_s=",
                      og.Controller.attribute("/DriveGraph/Differential.outputs:velocityCommand").get())
            frame += 1
        world.stop()
    finally:
        # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
        app.close()

if __name__ == "__main__":
    main()
