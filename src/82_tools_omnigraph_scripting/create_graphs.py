"""Create normal and on-demand graphs in the running Kit app."""
import omni.graph.core as og
import omni.usd

stage = omni.usd.get_context().get_stage()
for path in ("/LessonGraph", "/LessonDemand"):
    if stage.GetPrimAtPath(path):
        raise RuntimeError(f"{path} exists; open a fresh stage before running")
keys = og.Controller.Keys
normal_graph, _, _, _ = og.Controller.edit(
    {"graph_path": "/LessonGraph", "evaluator_name": "execution"},
    {keys.CREATE_NODES: [("tick", "omni.graph.action.OnPlaybackTick"),
                         ("print", "omni.graph.ui_nodes.PrintText")],
     keys.SET_VALUES: [("print.inputs:text", "normal playback graph"),
                       ("print.inputs:logLevel", "Warning")],
     keys.CONNECT: [("tick.outputs:tick", "print.inputs:execIn")]})
demand_graph, _, _, _ = og.Controller.edit(
    {"graph_path": "/LessonDemand", "evaluator_name": "execution",
     "pipeline_stage": og.GraphPipelineStage.GRAPH_PIPELINE_STAGE_ONDEMAND},
    {keys.CREATE_NODES: [("tick", "omni.graph.action.OnTick"),
                         ("print", "omni.graph.ui_nodes.PrintText")],
     keys.SET_VALUES: [("print.inputs:text", "one demand evaluation"),
                       ("print.inputs:logLevel", "Warning")],
     keys.CONNECT: [("tick.outputs:tick", "print.inputs:execIn")]})
print("Created /LessonGraph and /LessonDemand")
