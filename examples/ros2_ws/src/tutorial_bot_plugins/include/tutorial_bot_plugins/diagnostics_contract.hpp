#ifndef TUTORIAL_BOT_PLUGINS__DIAGNOSTICS_CONTRACT_HPP_
#define TUTORIAL_BOT_PLUGINS__DIAGNOSTICS_CONTRACT_HPP_

#include <array>
#include <string_view>

namespace tutorial_bot_plugins::contract
{
inline constexpr std::string_view kPluginClass =
  "gz::sim::systems::TutorialBotDiagnostics";
inline constexpr std::string_view kPluginLibrary =
  "libTutorialBotDiagnosticsSystem.so";
inline constexpr std::string_view kDefaultModelName = "tutorial_bot";
inline constexpr std::string_view kDistanceTopic =
  "/tutorial_bot/diagnostics/distance";
inline constexpr std::string_view kStatusTopic =
  "/tutorial_bot/diagnostics/status";
inline constexpr std::string_view kEnableTopic =
  "/tutorial_bot/diagnostics/enable";
inline constexpr std::string_view kResetService =
  "/tutorial_bot/diagnostics/reset";
inline constexpr double kPublishPeriodSeconds = 0.1;
inline constexpr bool kInitiallyEnabled = true;
inline constexpr std::array<std::string_view, 5> kStates = {
  "WAITING_FOR_MODEL", "READY", "DISABLED", "MODEL_REMOVED", "INVALID_CONFIG"};
}

#endif
