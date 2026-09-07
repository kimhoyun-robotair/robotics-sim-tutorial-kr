# Copyright 2026 kimhoyun
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""follow_waypoints 동작을 실행하는 ROS 2 진입점."""

from nav2_programming.common import run_demo


def main(args=None):
    """ROS 인자를 받아 예제를 실행하고 결과를 종료 코드로 전달한다."""
    return run_demo('follow_waypoints', args)


if __name__ == '__main__':
    raise SystemExit(main())

