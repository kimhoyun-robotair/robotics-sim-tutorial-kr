"""Manually trigger ROS clock publication in Isaac Sim 5.1."""
import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--steps', type=int, default=None, help='Simulation steps before exit; omitted: GUI until closed, headless 1200')
parser.add_argument('--every', type=int, default=10, help='Publish manual clock every N simulation steps')
parser.add_argument('--domain-id', type=int, default=1)
parser.add_argument('--headless', action='store_true')
parser.add_argument('--output', type=Path, default=Path(__file__).parent / 'output' / 'clock_schedule.json')
args = parser.parse_args()
if (args.steps is not None and args.steps < 1) or args.every < 1 or not 0 <= args.domain_id <= 232:
    parser.error('steps/every must be positive; domain-id must be 0..232')
if args.steps is None and args.headless:
    args.steps = 1200
if args.output.exists():
    parser.error(f'Output already exists: {args.output}; choose another --output')

from isaacsim import SimulationApp
app = SimulationApp({'headless': args.headless})
try:
    import omni.graph.core as og
    from isaacsim.core.api import SimulationContext
    from isaacsim.core.utils.extensions import enable_extension

    enable_extension('isaacsim.ros2.bridge')
    app.update()
    keys = og.Controller.Keys
    graph, _, _, _ = og.Controller.edit(
        {'graph_path': '/ClockLab', 'evaluator_name': 'execution'},
        {keys.CREATE_NODES: [
            ('Tick', 'omni.graph.action.OnPlaybackTick'),
            ('Impulse', 'omni.graph.action.OnImpulseEvent'),
            ('Time', 'isaacsim.core.nodes.IsaacReadSimulationTime'),
            ('Context', 'isaacsim.ros2.bridge.ROS2Context'),
            ('Auto', 'isaacsim.ros2.bridge.ROS2PublishClock'),
            ('Manual', 'isaacsim.ros2.bridge.ROS2PublishClock')],
         keys.CONNECT: [
            ('Tick.outputs:tick', 'Auto.inputs:execIn'),
            ('Impulse.outputs:execOut', 'Manual.inputs:execIn'),
            ('Time.outputs:simulationTime', 'Auto.inputs:timeStamp'),
            ('Time.outputs:simulationTime', 'Manual.inputs:timeStamp'),
            ('Context.outputs:context', 'Auto.inputs:context'),
            ('Context.outputs:context', 'Manual.inputs:context')],
         keys.SET_VALUES: [
            ('Auto.inputs:topicName', '/sim_time'),
            ('Manual.inputs:topicName', '/manual_time'),
            ('Context.inputs:domain_id', args.domain_id),
            ('Context.inputs:useDomainIDEnvVar', False)]})
    sim = SimulationContext(physics_dt=1/60, rendering_dt=1/60, stage_units_in_meters=1.0)
    sim.initialize_physics()
    sim.play()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as stream:
        stream.write('{"domain_id": ' + json.dumps(args.domain_id))
        stream.write(', "requested_steps": ' + json.dumps(args.steps))
        stream.write(', "manual_trigger_schedule": [\n')
        frame = 0
        first_trigger = True
        while app.is_running() and (args.steps is None or frame < args.steps):
            if frame % args.every == 0:
                og.Controller.set(og.Controller.attribute('/ClockLab/Impulse.state:enableImpulse'), True)
                if not first_trigger:
                    stream.write(',\n')
                json.dump({'frame': frame, 'simulation_time_before_step': sim.current_time}, stream)
                first_trigger = False
            sim.step(render=True)
            frame += 1
        stream.write('\n], "note": "Trigger schedule only; DDS reception must be observed with ros2 topic echo."}\n')
    sim.stop()
    print(f'Wrote actual trigger schedule to {args.output}')
finally:
    app.close()
