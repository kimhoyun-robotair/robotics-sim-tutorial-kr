# SPDX-FileCopyrightText: Copyright (c) 2023-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

import random

import bin_stacking_behavior as behavior
import isaacsim.cortex.framework.math_util as math_util
# Cortex의 math_util은 로봇과 물체의 위치·회전 및 변환 행렬 계산을 돕는 함수들을 제공한다.
import numpy as np
from isaacsim.core.api.objects import VisualCapsule, VisualSphere
# VisualCapsule은 물리 동작 없이 캡슐 모양을 표시하는 객체이다.
# VisualSphere는 물리 동작 없이 구 모양을 표시하는 객체이다.
from isaacsim.core.api.tasks import BaseTask
# BaseTask는 장면 구성, 초기화, 관측값 제공을 하나의 시뮬레이션 작업으로 묶는 기본 클래스이다.
from isaacsim.core.prims import XFormPrim
# XFormPrim은 경로로 선택한 Prim의 위치, 회전, 스케일을 배열 단위로 다룬다.
# Prim은 USD 장면의 객체 단위이며 같은 경로의 Prim을 감싸도 새 객체를 복제하는 것은 아니다.
from isaacsim.core.utils.stage import add_reference_to_stage
# add_reference_to_stage는 외부 USD 자산을 현재 Stage의 지정한 Prim 경로에 참조로 연결한다.
from isaacsim.cortex.framework.cortex_rigid_prim import CortexRigidPrim
# CortexRigidPrim은 Cortex 작업에서 물체의 강체 상태와 자세를 다루는 래퍼이다.
from isaacsim.cortex.framework.cortex_utils import get_assets_root_path_or_die
# get_assets_root_path_or_die는 Cortex 예제에서 사용할 자산 루트를 찾고 찾지 못하면 오류를 발생시킨다.
from isaacsim.cortex.framework.cortex_world import CortexWorld
# CortexWorld는 물리 시뮬레이션과 로봇의 행동 의사결정을 함께 진행하는 World이다.
from isaacsim.cortex.framework.robot import CortexUr10
# CortexUr10은 Cortex의 동작 명령을 받는 UR10 로봇 클래스이다.


class Ur10Assets:
    def __init__(self):
        self.assets_root_path = get_assets_root_path_or_die()

        self.ur10_table_usd = (
            self.assets_root_path + "/Isaac/Samples/Leonardo/Stage/ur10_bin_stacking_short_suction.usd"
        )
        self.small_klt_usd = self.assets_root_path + "/Isaac/Props/KLT_Bin/small_KLT.usd"
        self.background_usd = self.assets_root_path + "/Isaac/Environments/Simple_Warehouse/warehouse.usd"
        self.rubiks_cube_usd = self.assets_root_path + "/Isaac/Props/Rubiks_Cube/rubiks_cube.usd"


def print_diagnostics(diagnostic):
    print("=========== logical state ==========")
    if diagnostic.bin_name:
        print("active bin info:")
        print("- bin_obj.name: {}".format(diagnostic.bin_name))
        print("- bin_base: {}".format(diagnostic.bin_base))
        print("- grasp_T:\n{}".format(diagnostic.grasp))
        print("- is_grasp_reached: {}".format(diagnostic.grasp_reached))
        print("- is_attached:  {}".format(diagnostic.attached))
        print("- needs_flip:  {}".format(diagnostic.needs_flip))
    else:
        print("<no active bin>")

    print("------------------------------------")


def random_bin_spawn_transform():
    x = random.uniform(-0.15, 0.15)
    y = 1.5
    z = -0.15
    position = np.array([x, y, z])

    z = random.random() * 0.02 - 0.01
    w = random.random() * 0.02 - 0.01
    norm = np.sqrt(z**2 + w**2)
    quat = math_util.Quaternion([w / norm, 0, 0, z / norm])
    if random.random() > 0.5:
        print("<flip>")
        # flip the bin so it's upside down
        quat = quat * math_util.Quaternion([0, 0, 1, 0])
    else:
        print("<no flip>")

    return position, quat.vals


class BinStackingTask(BaseTask):
    def __init__(self, env_path, assets):
        super().__init__("bin_stacking")
        self.assets = assets

        self.env_path = "/World/Ur10Table"
        self.bins = []
        self.stashed_bins = []
        self.on_conveyor = None

    def _spawn_bin(self, rigid_bin):
        x, q = random_bin_spawn_transform()
        rigid_bin.set_world_pose(position=x, orientation=q)
        rigid_bin.set_linear_velocity(np.array([0, -0.30, 0]))
        rigid_bin.set_visibility(True)

    def post_reset(self) -> None:
        if len(self.bins) > 0:
            for rigid_bin in self.bins:
                self.scene.remove_object(rigid_bin.name)
            self.bins.clear()

        self.on_conveyor = None

    def pre_step(self, time_step_index, simulation_time) -> None:
        """Spawn a new randomly oriented bin if the previous bin has been placed."""
        spawn_new = False
        if self.on_conveyor is None:
            spawn_new = True
        else:
            (x, y, z), _ = self.on_conveyor.get_world_pose()
            is_on_conveyor = y > 0.0 and -0.4 < x and x < 0.4
            if not is_on_conveyor:
                spawn_new = True

        if spawn_new:
            name = "bin_{}".format(len(self.bins))
            prim_path = self.env_path + "/bins/{}".format(name)
            add_reference_to_stage(usd_path=self.assets.small_klt_usd, prim_path=prim_path)
            self.on_conveyor = self.scene.add(CortexRigidPrim(name=name, prim_path=prim_path))

            self._spawn_bin(self.on_conveyor)
            self.bins.append(self.on_conveyor)


def main():
    world = CortexWorld()

    env_path = "/World/Ur10Table"
    ur10_assets = Ur10Assets()
    add_reference_to_stage(usd_path=ur10_assets.ur10_table_usd, prim_path=env_path)
    add_reference_to_stage(usd_path=ur10_assets.background_usd, prim_path="/World/Background")
    background_prim = XFormPrim(
        "/World/Background",
        positions=np.array([[10.00, 2.00, -1.18180]]),
        orientations=np.array([[0.7071, 0, 0, 0.7071]]),
    )
    robot = world.add_robot(CortexUr10(name="robot", prim_path="{}/ur10".format(env_path)))

    # 생성한 객체를 World의 Scene에 등록하여 이름으로 찾고 초기화할 수 있게 한다.
    obs = world.scene.add(
        VisualSphere(
            "/World/Ur10Table/Obstacles/FlipStationSphere",
            name="flip_station_sphere",
            position=np.array([0.73, 0.76, -0.13]),
            radius=0.2,
            visible=False,
        )
    )
    robot.register_obstacle(obs)
    obs = world.scene.add(
        VisualSphere(
            "/World/Ur10Table/Obstacles/NavigationDome",
            name="navigation_dome_obs",
            position=[-0.031, -0.018, -1.086],
            radius=1.1,
            visible=False,
        )
    )
    robot.register_obstacle(obs)

    az = np.array([1.0, 0.0, -0.3])
    ax = np.array([0.0, 1.0, 0.0])
    ay = np.cross(az, ax)
    R = math_util.pack_R(ax, ay, az)
    quat = math_util.matrix_to_quat(R)
    obs = world.scene.add(
        VisualCapsule(
            "/World/Ur10Table/Obstacles/NavigationBarrier",
            name="navigation_barrier_obs",
            position=[0.471, 0.276, -0.463 - 0.1],
            orientation=quat,
            radius=0.5,
            height=0.9,
            visible=False,
        )
    )
    robot.register_obstacle(obs)

    obs = world.scene.add(
        VisualCapsule(
            "/World/Ur10Table/Obstacles/NavigationFlipStation",
            name="navigation_flip_station_obs",
            position=np.array([0.766, 0.755, -0.5]),
            radius=0.5,
            height=0.5,
            visible=False,
        )
    )
    robot.register_obstacle(obs)

    # 작업을 World에 등록하여 장면 구성과 관측값·초기화를 World와 함께 관리한다.
    world.add_task(BinStackingTask(env_path, ur10_assets))
    # Cortex 행동 네트워크를 등록하여 시뮬레이션 중 의사결정을 갱신한다.
    world.add_decider_network(behavior.make_decider_network(robot, print_diagnostics))

    # CortexWorld의 실행 루프를 시작하여 물리와 행동 네트워크를 함께 진행한다.
    world.run(simulation_app, play_on_entry=not args.interactive,
              is_done_cb=lambda: args.steps is not None and world.current_time_step_index >= args.steps)


if __name__ == "__main__":
    try:
        main()
    finally:
        # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
        simulation_app.close()
