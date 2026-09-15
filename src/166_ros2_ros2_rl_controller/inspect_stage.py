"""Inspect the loaded H1 ROS policy scenario in Isaac Sim Script Editor."""
import omni.usd
from pxr import UsdPhysics, PhysxSchema
stage = omni.usd.get_context().get_stage()
scenes = [prim for prim in stage.Traverse() if prim.IsA(UsdPhysics.Scene)]
if not scenes:
    raise RuntimeError("No PhysicsScene loaded")
for prim in scenes:
    api = PhysxSchema.PhysxSceneAPI(prim)
    print("physics_scene=", prim.GetPath(), "Hz=", api.GetTimeStepsPerSecondAttr().Get(),
          "gpu_dynamics=", api.GetEnableGPUDynamicsAttr().Get(), "broadphase=", api.GetBroadphaseTypeAttr().Get())
for prim in stage.Traverse():
    if "Imu" in prim.GetTypeName() or prim.GetName() == "Imu_Sensor":
        print("imu=", prim.GetPath())
    if prim.GetTypeName() == "OmniGraph":
        print("graph=", prim.GetPath(), "pipeline=", prim.GetAttribute("pipelineStage").Get())
    node_type = prim.GetAttribute("node:type")
    if node_type and "ROS2" in str(node_type.Get()):
        print("ROS_node=", prim.GetPath(), node_type.Get(),
              "topic=", prim.GetAttribute("inputs:topicName").Get())
