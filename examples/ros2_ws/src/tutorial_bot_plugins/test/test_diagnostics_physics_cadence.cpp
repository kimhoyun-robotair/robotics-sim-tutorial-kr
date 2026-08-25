#include <gtest/gtest.h>

#include <gz/msgs/double.pb.h>
#include <gz/msgs/stringmsg.pb.h>
#include <gz/msgs/world_stats.pb.h>
#include <gz/sim/Server.hh>
#include <gz/sim/ServerConfig.hh>
#include <gz/transport/Node.hh>

#include <chrono>
#include <condition_variable>
#include <cstdint>
#include <filesystem>
#include <mutex>
#include <string>
#include <vector>

namespace
{
struct Observation
{
  std::vector<double> simTimes;
  std::size_t distances{0};
  std::size_t statuses{0};
};

class VariantObserver
{
public:
  VariantObserver(const std::string & worldName, const std::string & topicPrefix)
  {
    node_.Subscribe(
      "/world/" + worldName + "/stats", &VariantObserver::OnStats, this);
    node_.Subscribe(
      topicPrefix + "/distance", &VariantObserver::OnDistance, this);
    node_.Subscribe(topicPrefix + "/status", &VariantObserver::OnStatus, this);
  }

  Observation Run(const std::filesystem::path & world, const std::uint64_t iterations)
  {
    gz::sim::ServerConfig config;
    config.SetSdfFile(world.string());
    gz::sim::Server server(config);
    EXPECT_TRUE(server.Run(true, iterations, false));

    std::unique_lock<std::mutex> lock(mutex_);
    condition_.wait_for(lock, std::chrono::seconds(2), [this] {
      return !simTimes_.empty() && distances_ > 0 && statuses_ > 0;
    });
    return {simTimes_, distances_, statuses_};
  }

private:
  void OnStats(const gz::msgs::WorldStatistics & message)
  {
    std::lock_guard<std::mutex> lock(mutex_);
    simTimes_.push_back(
      static_cast<double>(message.sim_time().sec()) +
      static_cast<double>(message.sim_time().nsec()) * 1e-9);
    condition_.notify_all();
  }

  void OnDistance(const gz::msgs::Double &)
  {
    std::lock_guard<std::mutex> lock(mutex_);
    ++distances_;
    condition_.notify_all();
  }

  void OnStatus(const gz::msgs::StringMsg &)
  {
    std::lock_guard<std::mutex> lock(mutex_);
    ++statuses_;
    condition_.notify_all();
  }

  gz::transport::Node node_;
  std::mutex mutex_;
  std::condition_variable condition_;
  std::vector<double> simTimes_;
  std::size_t distances_{0};
  std::size_t statuses_{0};
};

void ExpectMonotonicTwoSeconds(const Observation & observation)
{
  ASSERT_GT(observation.simTimes.size(), 1u) << "world stats unavailable";
  for (std::size_t index = 1; index < observation.simTimes.size(); ++index) {
    EXPECT_GT(observation.simTimes[index], observation.simTimes[index - 1]);
  }
  EXPECT_GE(observation.simTimes.back(), 1.99);
  EXPECT_LE(observation.simTimes.back(), 2.0);
  EXPECT_GT(observation.distances, 0u);
  EXPECT_GT(observation.statuses, 0u);
}
}

TEST(DiagnosticsPhysicsCadence, ReportsDeterministicSimulationCadence)
{
  const auto worldDirectory = std::filesystem::path(TUTORIAL_BOT_WORLD_DIR);
  const auto fastWorld = worldDirectory / "advanced-fast.sdf";
  const auto slowWorld = worldDirectory / "advanced-slow.sdf";
  ASSERT_TRUE(std::filesystem::is_regular_file(fastWorld))
    << "cadence world variant unavailable: " << fastWorld;
  ASSERT_TRUE(std::filesystem::is_regular_file(slowWorld))
    << "cadence world variant unavailable: " << slowWorld;

  VariantObserver fastObserver("advanced_fast", "/tutorial_bot/fast/diagnostics");
  const auto fast = fastObserver.Run(fastWorld, 2000);
  VariantObserver slowObserver("advanced_slow", "/tutorial_bot/slow/diagnostics");
  const auto slow = slowObserver.Run(slowWorld, 500);

  ExpectMonotonicTwoSeconds(fast);
  ExpectMonotonicTwoSeconds(slow);
  ASSERT_GT(slow.distances, 0u);
  const double ratio =
    static_cast<double>(fast.distances) / static_cast<double>(slow.distances);
  EXPECT_GE(ratio, 3.0);
  EXPECT_LE(ratio, 5.0);
}
