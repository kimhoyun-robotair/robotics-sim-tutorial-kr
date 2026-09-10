from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest
from launch import LaunchContext

LAUNCH_DIRECTORY = Path(__file__).parents[1] / "tutorial_bot_bringup" / "launch"


def _load_launch_module(filename: str):
    spec = spec_from_file_location(filename.replace(".", "_"), LAUNCH_DIRECTORY / filename)
    assert spec is not None
    assert spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _simulation_context(**overrides: str) -> LaunchContext:
    context = LaunchContext()
    context.launch_configurations.update(
        {
            "world": "training",
            "model_name": "tutorial_bot",
            "namespace": "/",
            "tf_prefix": "",
            "nav2": "false",
            "amcl": "true",
            "gui": "false",
            "rviz": "false",
            **overrides,
        }
    )
    return context


def _multi_robot_context(**overrides: str) -> LaunchContext:
    context = LaunchContext()
    context.launch_configurations.update(
        {
            "world": "sensor-test",
            "gui": "false",
            "robot1_name": "robot1",
            "robot2_name": "robot2",
            "robot1_namespace": "/robot1",
            "robot2_namespace": "/robot2",
            **overrides,
        }
    )
    return context


@pytest.mark.parametrize(
    ("argument_name", "payload_template"),
    [
        ("model_name", "tutorial_bot -o {sentinel}"),
        ("namespace", "/robot1 -o {sentinel}"),
        ("tf_prefix", "robot1_ -o {sentinel}"),
    ],
)
def test_simulation_rejects_xacro_option_injection(
    argument_name: str, payload_template: str, tmp_path: Path
) -> None:
    launch_module = _load_launch_module("simulation.launch.py")
    sentinel = tmp_path / "xacro-sentinel"
    payload = payload_template.format(sentinel=sentinel)

    with pytest.raises(launch_module._LaunchContractError, match=argument_name):
        launch_module._launch_stack(_simulation_context(**{argument_name: payload}))

    assert not sentinel.exists()


@pytest.mark.parametrize(
    ("argument_name", "payload_template"),
    [
        ("robot1_name", "robot1 -o {sentinel}"),
        ("robot2_name", "robot2 -o {sentinel}"),
        ("robot1_namespace", "/robot1 -o {sentinel}"),
        ("robot2_namespace", "/robot2 -o {sentinel}"),
    ],
)
def test_multi_robot_rejects_xacro_option_injection(
    argument_name: str, payload_template: str, tmp_path: Path
) -> None:
    launch_module = _load_launch_module("multi_robot.launch.py")
    sentinel = tmp_path / "xacro-sentinel"
    payload = payload_template.format(sentinel=sentinel)

    with pytest.raises(launch_module._LaunchContractError, match=argument_name):
        launch_module._launch_stack(_multi_robot_context(**{argument_name: payload}))

    assert not sentinel.exists()


def test_multi_robot_accepts_installed_training_world() -> None:
    launch_module = _load_launch_module("multi_robot.launch.py")

    actions = launch_module._launch_stack(_multi_robot_context(world="training"))

    assert actions


@pytest.mark.parametrize(
    ("gui", "expected_flags"),
    [("true", ["-r"]), ("false", ["-s", "-r", "--headless-rendering"])],
)
def test_multi_robot_selects_gazebo_gui_or_headless_mode(
    gui: str, expected_flags: list[str]
) -> None:
    from launch.actions import IncludeLaunchDescription

    launch_module = _load_launch_module("multi_robot.launch.py")
    actions = launch_module._launch_stack(_multi_robot_context(gui=gui))
    gazebo = next(action for action in actions if isinstance(action, IncludeLaunchDescription))
    arguments = dict(gazebo.launch_arguments)
    gz_args = arguments["gz_args"]
    assert isinstance(gz_args, str)
    command = gz_args.split()

    assert command[:-1] == expected_flags
    assert Path(command[-1]).name == "sensor-test.sdf"
    assert arguments["on_exit_shutdown"] == "true"


@pytest.mark.parametrize(
    "world_name",
    [
        "../worlds/sensor-test",
        str(
            LAUNCH_DIRECTORY.parents[1]
            / "tutorial_bot_gazebo"
            / "worlds"
            / "sensor-test"
        ),
        "sensor-test -o /tmp/world-sentinel",
    ],
)
def test_multi_robot_rejects_unsafe_world_names(world_name: str) -> None:
    launch_module = _load_launch_module("multi_robot.launch.py")

    with pytest.raises(launch_module._LaunchContractError, match="world"):
        launch_module._launch_stack(_multi_robot_context(world=world_name))


@pytest.mark.parametrize(
    ("argument_name", "value"),
    [
        ("model_name", "tutorial_bot"),
        ("namespace", "/"),
        ("tf_prefix", ""),
    ],
)
def test_simulation_accepts_documented_xacro_values(
    argument_name: str, value: str
) -> None:
    launch_module = _load_launch_module("simulation.launch.py")

    actions = launch_module._launch_stack(_simulation_context(**{argument_name: value}))

    assert actions


@pytest.mark.parametrize("overrides", [{"namespace": "/robot1"}, {"tf_prefix": "robot1_"}])
def test_simulation_rejects_unconfigured_namespaced_graph(overrides: dict[str, str]) -> None:
    launch_module = _load_launch_module("simulation.launch.py")
    with pytest.raises(launch_module._LaunchContractError, match="multi_robot.launch.py"):
        launch_module._launch_stack(_simulation_context(**overrides))


@pytest.mark.parametrize("amcl", ["true", "false"])
def test_nav2_starts_map_server_with_exactly_one_localization_source(amcl: str) -> None:
    from launch.actions import DeclareLaunchArgument
    from launch.utilities import normalize_to_list_of_substitutions, perform_substitutions
    from launch_ros.actions import Node

    launch_module = _load_launch_module("nav2.launch.py")
    context = LaunchContext()
    for action in launch_module.generate_launch_description().entities:
        if isinstance(action, DeclareLaunchArgument):
            action.execute(context)
    context.launch_configurations["amcl"] = amcl
    actions = launch_module._launch_stack(context)
    executables = [
        perform_substitutions(context, normalize_to_list_of_substitutions(action.node_executable))
        for action in actions if isinstance(action, Node)
    ]

    assert executables.count("map_server") == 1
    assert executables.count("amcl") == (1 if amcl == "true" else 0)
    assert executables.count("static_transform_publisher") == (0 if amcl == "true" else 1)
    assert executables.count("lifecycle_manager") == 1


def test_simulation_rejects_invalid_amcl_option() -> None:
    launch_module = _load_launch_module("simulation.launch.py")
    with pytest.raises(launch_module._LaunchContractError, match="amcl"):
        launch_module._launch_stack(_simulation_context(amcl="maybe"))
