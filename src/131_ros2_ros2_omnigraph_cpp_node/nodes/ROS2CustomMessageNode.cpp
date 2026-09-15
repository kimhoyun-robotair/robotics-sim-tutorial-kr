#include <ROS2CustomMessageNodeDatabase.h>
#include <rcl/rcl.h>
#include <tutorial_interfaces/msg/sphere.h>
#include <cmath>
#include <cstdint>
#include <cstdio>

namespace omni::example::cpp::omnigraph_node_ros {

class ROS2CustomMessageNode {
public:
    ROS2CustomMessageNode() = default;
    ROS2CustomMessageNode(const ROS2CustomMessageNode&) = delete;
    ROS2CustomMessageNode& operator=(const ROS2CustomMessageNode&) = delete;
    ~ROS2CustomMessageNode() { close(); }

    static bool compute(ROS2CustomMessageNodeDatabase& db) {
        auto& self = db.internalState<ROS2CustomMessageNode>();
        const auto center = db.inputs.publishCenter();
        const auto radius = db.inputs.publishRadius();
        if (!std::isfinite(radius) || radius < 0 || !std::isfinite(center[0]) ||
            !std::isfinite(center[1]) || !std::isfinite(center[2])) {
            std::fprintf(stderr, "Sphere center must be finite and radius nonnegative.\n");
            return false;
        }
        if (!self.publisher_ready && !self.open()) return false;
        tutorial_interfaces__msg__Sphere message{};
        if (!tutorial_interfaces__msg__Sphere__init(&message)) return false;
        message.center.x = center[0];
        message.center.y = center[1];
        message.center.z = center[2];
        message.radius = radius;
        const auto result = rcl_publish(&self.publisher, &message, nullptr);
        tutorial_interfaces__msg__Sphere__fini(&message);
        if (!check(result, "publish Sphere")) return false;
        db.outputs.publishedCount() = ++self.count;
        return true;
    }

    static void releaseInstance(NodeObj const& node, GraphInstanceID instance) {
        auto& self = ROS2CustomMessageNodeDatabase::sPerInstanceState<ROS2CustomMessageNode>(node, instance);
        self.close();
    }

private:
    rcl_context_t context = rcl_get_zero_initialized_context();
    rcl_node_t node = rcl_get_zero_initialized_node();
    rcl_publisher_t publisher = rcl_get_zero_initialized_publisher();
    bool context_ready = false;
    bool node_ready = false;
    bool publisher_ready = false;
    std::uint64_t count = 0;

    static bool check(rcl_ret_t result, const char* operation) {
        if (result == RCL_RET_OK) return true;
        std::fprintf(stderr, "%s failed with rcl status %d\n", operation, result);
        return false;
    }

    bool open() {
        rcl_init_options_t options = rcl_get_zero_initialized_init_options();
        if (!check(rcl_init_options_init(&options, rcl_get_default_allocator()), "init options")) return false;
        const auto result = rcl_init(0, nullptr, &options, &context);
        check(rcl_init_options_fini(&options), "free init options");
        if (!check(result, "init context")) return false;
        context_ready = true;
        auto node_options = rcl_node_get_default_options();
        if (!check(rcl_node_init(&node, "sphere_lesson", "/custom_node", &context, &node_options), "init node")) {
            close();
            return false;
        }
        node_ready = true;
        auto publisher_options = rcl_publisher_get_default_options();
        if (!check(rcl_publisher_init(&publisher, &node,
                ROSIDL_GET_MSG_TYPE_SUPPORT(tutorial_interfaces, msg, Sphere),
                "sphere_msg", &publisher_options), "init publisher")) {
            close();
            return false;
        }
        publisher_ready = true;
        return true;
    }

    void close() {
        if (publisher_ready) check(rcl_publisher_fini(&publisher, &node), "free publisher");
        if (node_ready) check(rcl_node_fini(&node), "free node");
        if (context_ready) {
            if (rcl_context_is_valid(&context)) check(rcl_shutdown(&context), "shutdown context");
            check(rcl_context_fini(&context), "free context");
        }
        publisher = rcl_get_zero_initialized_publisher();
        node = rcl_get_zero_initialized_node();
        context = rcl_get_zero_initialized_context();
        publisher_ready = node_ready = context_ready = false;
        count = 0;
    }
};

REGISTER_OGN_NODE()
}
