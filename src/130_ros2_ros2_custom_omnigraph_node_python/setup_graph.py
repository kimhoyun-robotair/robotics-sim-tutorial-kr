"""Run in Script Editor after enabling the local kr.ros2.fibonacci extension."""
import omni.graph.core as og
import omni.usd
stage = omni.usd.get_context().get_stage()
if stage is None or stage.GetPrimAtPath('/FibonacciLab'):
    raise RuntimeError('Open a new stage without /FibonacciLab')
keys = og.Controller.Keys
og.Controller.edit({'graph_path':'/FibonacciLab','evaluator_name':'execution'}, {
    keys.CREATE_NODES:[('Tick','omni.graph.action.OnPlaybackTick'),
                       ('Fibonacci','kr.ros2.fibonacci.Fibonacci')],
    keys.CONNECT:[('Tick.outputs:tick','Fibonacci.inputs:execIn')]})
print('Play, then publish /number. Inspect Fibonacci outputs:fibonacci in the graph.')
