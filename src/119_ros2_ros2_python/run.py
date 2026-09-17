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
# SimulationApp은 Python에서 Isaac Sim의 Kit 애플리케이션을 시작하고 갱신·종료하는 클래스이다.
# headless=True는 창 없이 실행한다는 뜻이며, omni와 Isaac Sim 확장 모듈은 앱 생성 후 import한다.
app = SimulationApp({'headless': args.headless})
try:
    import omni.graph.core as og
    # omni.graph.core는 노드와 연결로 실행 흐름을 구성하는 OmniGraph API이다.
    # Controller.edit에서 노드 생성, 입력값 설정, 출력과 입력의 연결을 정의한다.
    from isaacsim.core.api import SimulationContext
    # SimulationContext는 물리 및 렌더링 시간 간격과 시뮬레이션의 재생·정지·step을 관리한다.
    from isaacsim.core.utils.extensions import enable_extension
    # enable_extension은 이름으로 지정한 Kit 확장을 활성화하여 해당 기능과 명령을 사용할 수 있게 한다.

    enable_extension('isaacsim.ros2.bridge')
    # Kit의 한 프레임을 갱신하여 렌더링·이벤트·비동기 작업을 처리한다.
    # 물리 진행 여부는 현재 타임라인의 재생 상태와 설정에 따라 달라진다.
    app.update()
    keys = og.Controller.Keys
    # OmniGraph의 노드와 입력값을 만들고 포트를 연결한다.
    # 실행 포트는 처리 순서를, 데이터 포트는 시간·센서·관절 값의 전달 경로를 정한다.
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
    # 물리 엔진과 시뮬레이션 핸들을 초기화한다.
    sim.initialize_physics()
    # 타임라인을 재생 상태로 전환하여 물리 시뮬레이션이 진행되게 한다.
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
            # SimulationContext의 시간 간격으로 시뮬레이션을 한 step 진행한다.
            sim.step(render=True)
            frame += 1
        stream.write('\n], "note": "Trigger schedule only; DDS reception must be observed with ros2 topic echo."}\n')
    sim.stop()
    print(f'Wrote actual trigger schedule to {args.output}')
finally:
    # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
    app.close()
