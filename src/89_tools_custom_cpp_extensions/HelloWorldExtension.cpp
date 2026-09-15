#define CARB_EXPORTS
#include <cstdio>
#include <carb/PluginUtils.h>
#include <omni/ext/IExt.h>

const carb::PluginImplDesc pluginImplDesc = {
    "omni.example.cpp.hello_world.plugin", "Korean lifecycle lesson", "Tutorial",
    carb::PluginHotReload::eEnabled, "dev"
};
namespace omni::example::cpp::hello_world {
class ExampleCppHelloWorldExtension : public omni::ext::IExt {
public:
    void onStartup(const char* extId) override {
        std::printf("Korean C++ extension started: %s\n", extId);
    }
    void onShutdown() override {
        std::printf("Korean C++ extension stopped\n");
    }
};
}
CARB_PLUGIN_IMPL(pluginImplDesc, omni::example::cpp::hello_world::ExampleCppHelloWorldExtension)
void fillInterface(omni::example::cpp::hello_world::ExampleCppHelloWorldExtension&) {}
