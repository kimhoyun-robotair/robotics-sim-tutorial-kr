#include <OgnExampleNodeDatabase.h>

namespace omni::example::cpp::omnigraph_node {
class OgnExampleNode {
public:
    static bool compute(OgnExampleNodeDatabase& db) {
        db.outputs.positive() = db.inputs.value() > 0.0;
        return true;
    }
};
REGISTER_OGN_NODE()
}
