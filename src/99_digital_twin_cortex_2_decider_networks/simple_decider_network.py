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


from isaacsim.cortex.framework.df import DfAction, DfDecider, DfDecision, DfNetwork
from isaacsim.cortex.framework.dfb import DfRobotApiContext


class Context(DfRobotApiContext):
    def __init__(self, robot):
        super().__init__(robot)

        self.reset()
        self.add_monitors([Context.monitor_y, Context.monitor_is_left, Context.monitor_is_middle])

    def reset(self):
        self.y = None
        self.is_left = None
        self.is_middle = None

    def monitor_y(self):
        self.y = self.robot.arm.get_fk_p()[1]

    def monitor_is_left(self):
        self.is_left = self.y < 0

    def monitor_is_middle(self):
        self.is_middle = -0.15 < self.y and self.y < 0.15


class PrintAction(DfAction):
    def __init__(self, msg=None):
        super().__init__()
        self.msg = msg

    def __str__(self):
        return self.msg

    def enter(self):
        if self.params is not None:
            self.msg = self.params
            print(self.params)
        else:
            print(self.msg)


class Dispatch(DfDecider):
    def __init__(self):
        super().__init__()
        self.add_child("print_left", PrintAction("<left>"))
        self.add_child("print_right", PrintAction("<right>"))
        self.add_child("print", PrintAction(""))

    def decide(self):
        if self.context.is_middle:
            return DfDecision("print", "<middle>")  # Send parameters down to generic print.

        if self.context.is_left:
            return DfDecision("print_left")
        else:
            return DfDecision("print_right")


def make_decider_network(robot):
    return DfNetwork(Dispatch(), context=Context(robot))
