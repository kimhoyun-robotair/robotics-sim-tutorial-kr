// Copyright 2026 gazebo-sim-tutorial-kr contributors
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#ifndef GAZEBO_TUTORIAL_PLUGINS__PATH_RECORDER_CONFIG_HPP_
#define GAZEBO_TUTORIAL_PLUGINS__PATH_RECORDER_CONFIG_HPP_

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstddef>
#include <limits>
#include <optional>
#include <string>

namespace gazebo_tutorial_plugins
{

/// SDF에서 읽는 ground-truth 경로 플러그인의 설정값이다.
struct PathRecorderConfig
{
  double update_rate{10.0};
  std::string topic{"ground_truth_path"};
  std::string frame{"world"};
  std::size_t max_points{2000U};

  [[nodiscard]] bool IsValid() const noexcept
  {
    return std::isfinite(update_rate) && update_rate > 0.0 &&
           !topic.empty() && !frame.empty() && max_points > 0U;
  }

  /// 유효한 설정에서 호출한다. 극단적으로 큰 주파수도 최소 1 ns로 제한한다.
  [[nodiscard]] std::chrono::nanoseconds PublishPeriod() const noexcept
  {
    using Nanoseconds = std::chrono::nanoseconds;
    using Rep = Nanoseconds::rep;
    constexpr long double kNanosecondsPerSecond = 1'000'000'000.0L;

    const long double count = kNanosecondsPerSecond /
      static_cast<long double>(update_rate);
    if (count >= static_cast<long double>(std::numeric_limits<Rep>::max())) {
      return Nanoseconds::max();
    }
    if (count <= 1.0L) {
      return Nanoseconds{1};
    }
    return Nanoseconds{static_cast<Rep>(count)};
  }
};

/// wall time이 아니라 simulation time을 기준으로 발행 시점을 판정한다.
class SimulationRateGate
{
public:
  explicit SimulationRateGate(std::chrono::nanoseconds period)
  {
    SetPeriod(period);
  }

  void SetPeriod(std::chrono::nanoseconds period) noexcept
  {
    period_ = std::max(period, std::chrono::nanoseconds{1});
    Reset();
  }

  void Reset() noexcept
  {
    last_publish_time_.reset();
  }

  [[nodiscard]] bool ShouldPublish(std::chrono::nanoseconds simulation_time) noexcept
  {
    // 첫 샘플과 world reset 직후의 첫 샘플은 즉시 발행한다.
    if (!last_publish_time_ || simulation_time < *last_publish_time_) {
      last_publish_time_ = simulation_time;
      return true;
    }

    if (simulation_time - *last_publish_time_ < period_) {
      return false;
    }

    last_publish_time_ = simulation_time;
    return true;
  }

private:
  std::chrono::nanoseconds period_{std::chrono::milliseconds{100}};
  std::optional<std::chrono::nanoseconds> last_publish_time_;
};

}  // namespace gazebo_tutorial_plugins

#endif  // GAZEBO_TUTORIAL_PLUGINS__PATH_RECORDER_CONFIG_HPP_
