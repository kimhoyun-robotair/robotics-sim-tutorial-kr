# SPDX-FileCopyrightText: Copyright (c) 2022-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
parser = argparse.ArgumentParser(description="Isaac Sim 5.1 native Cortex example")
parser.add_argument("--headless", action="store_true")
parser.add_argument("--interactive", action="store_true")
parser.add_argument("--steps", type=int, default=None,
                    help="Physics steps before exit; omitted: GUI until closed, headless 1800")
args = parser.parse_args()
if (args.steps is not None and args.steps < 1) or (args.headless and args.interactive):
    parser.error("Use positive steps; interactive mode requires a window")
if args.steps is None and args.headless:
    args.steps = 1800
from isaacsim import SimulationApp
# SimulationApp은 Python에서 Isaac Sim의 Kit 애플리케이션을 시작하고 갱신·종료하는 클래스이다.
# headless=True는 창 없이 실행한다는 뜻이며, omni와 Isaac Sim 확장 모듈은 앱 생성 후 import한다.

simulation_app = SimulationApp({"headless": args.headless})

import time

import numpy as np
from isaacsim.cortex.framework.cortex_world import CortexWorld
# CortexWorld는 물리 시뮬레이션과 로봇의 행동 의사결정을 함께 진행하는 World이다.
from isaacsim.cortex.framework.df import DfNetwork, DfState, DfStateMachineDecider, DfStateSequence
# DfNetwork는 로봇의 행동 선택을 구성하는 Cortex 의사결정 네트워크이다.
# DfState는 진입·실행·종료 동작을 정의하는 Cortex 상태의 기본 클래스이다.
# DfStateMachineDecider는 상태 기계를 Cortex 의사결정 구조에 연결한다.
# DfStateSequence는 여러 상태를 순서대로 실행하는 상태 시퀀스이다.
from isaacsim.cortex.framework.dfb import DfBasicContext
# DfBasicContext는 의사결정 네트워크에서 로봇과 공유 상태에 접근하는 기본 문맥이다.
from isaacsim.cortex.framework.robot import add_franka_to_stage
# add_franka_to_stage는 Cortex에서 제어할 Franka 로봇을 Stage에 추가한다.


class NullspaceShiftState(DfState):
    def __init__(self):
        super().__init__()
        self.config_mean = np.array([0.00, -1.3, 0.00, -2.87, 0.00, 2.00, 0.75])
        self.target_p = np.array([0.7, 0.0, 0.5])
        self.construction_time = time.time()

    def enter(self):
        # Change the posture configuration while maintaining a consistent target.
        posture_config = self.config_mean + np.random.randn(7)
        self.context.robot.arm.send_end_effector(target_position=self.target_p, posture_config=posture_config)

        self.entry_time = time.time()

        # Close the gripper if open and open the gripper if closed. It closes more quickly than it
        # opens.
        gripper = self.context.robot.gripper
        if gripper.get_width() > 0.05:
            gripper.close(speed=0.5)
        else:
            gripper.open(speed=0.1)

        print("[%f] <enter> sampling posture config" % (self.entry_time - self.construction_time))

    def step(self):
        if time.time() - self.entry_time < 2.0:
            return self
        return None


def main():
    world = CortexWorld()
    robot = world.add_robot(add_franka_to_stage(name="franka", prim_path="/World/franka"))
    # 기본 바닥을 Scene에 추가한다. 이 바닥은 강체가 떨어졌을 때 충돌할 표면이다.
    world.scene.add_default_ground_plane()

    decider_network = DfNetwork(
        DfStateMachineDecider(DfStateSequence([NullspaceShiftState()], loop=True)), context=DfBasicContext(robot)
    )
    # Cortex 행동 네트워크를 등록하여 시뮬레이션 중 의사결정을 갱신한다.
    world.add_decider_network(decider_network)

    # CortexWorld의 실행 루프를 시작하여 물리와 행동 네트워크를 함께 진행한다.
    world.run(simulation_app, play_on_entry=not args.interactive,
              is_done_cb=lambda: args.steps is not None and world.current_time_step_index >= args.steps)


if __name__ == "__main__":
    try:
        main()
    finally:
        # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
        simulation_app.close()
