"""Script Editor, while Play is active: read the actual articulation tensor properties."""
import omni.usd
from pxr import UsdPhysics
from isaacsim.core.prims import SingleArticulation

stage = omni.usd.get_context().get_stage()
root = stage.GetPrimAtPath("/h1")
if not root:
    raise RuntimeError("Expected /h1; inspect the stage root and update the path for your copy")
robot = SingleArticulation(prim_path="/h1", name="h1_policy_inspection")
robot.initialize()
print("DOF order:", robot.dof_names)
print("Runtime positions (rad):", robot.get_joint_positions())
print("Runtime properties (rad-based gains/velocities):", robot.dof_properties)
