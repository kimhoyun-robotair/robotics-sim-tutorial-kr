"""Run in Isaac Sim 5.1 Script Editor on a new, stopped stage."""
import omni.graph.core as og
import omni.usd
from pxr import Gf, UsdGeom
from isaacsim.core.utils.extensions import enable_extension

enable_extension('isaacsim.ros2.bridge')
stage = omni.usd.get_context().get_stage()
if stage is None:
    raise RuntimeError('Open a new stage before running this file')
if stage.GetPrimAtPath('/PrimServices') or stage.GetPrimAtPath('/World/Cube'):
    raise RuntimeError('Use a new stage: /PrimServices or /World/Cube already exists')
UsdGeom.SetStageMetersPerUnit(stage, 1.0)
UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
UsdGeom.Xform.Define(stage, '/World')
cube = UsdGeom.Cube.Define(stage, '/World/Cube')
cube.CreateSizeAttr(0.5)
cube.AddTranslateOp().Set(Gf.Vec3d(0, 0, 0.25))
cube.AddOrientOp().Set(Gf.Quatf(1, 0, 0, 0))
cube.CreateDisplayColorAttr([(0.15, 0.55, 0.9)])
keys = og.Controller.Keys
og.Controller.edit({'graph_path': '/PrimServices', 'evaluator_name': 'execution'}, {
    keys.CREATE_NODES: [('Tick', 'omni.graph.action.OnPlaybackTick'),
                        ('Context', 'isaacsim.ros2.bridge.ROS2Context'),
                        ('Prims', 'isaacsim.ros2.bridge.ROS2ServicePrim')],
    keys.CONNECT: [('Tick.outputs:tick', 'Prims.inputs:execIn'),
                   ('Context.outputs:context', 'Prims.inputs:context')]})
print('Press Play, then call /get_prims and /get_prim_attribute from ROS.')
