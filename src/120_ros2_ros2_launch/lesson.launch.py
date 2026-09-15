"""Include the official launcher and start a real clock observer after scene readiness."""
from pathlib import Path
import shlex
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, IncludeLaunchDescription, RegisterEventHandler
from launch.event_handlers import OnProcessIO
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    scene = str(Path(__file__).with_name('clock_scene.py').resolve())
    official = Path(get_package_share_directory('isaacsim'))/'launch/run_isaacsim.launch.py'
    state = {'tail':'','started':False}
    observer = ExecuteProcess(cmd=['ros2','topic','echo','/clock','--once'],output='screen')
    def on_stdout(event):
        if state['started']:
            return []
        state['tail'] = (state['tail']+event.text.decode(errors='replace'))[-4096:]
        if 'LOCAL_CLOCK_SCENE_READY' in state['tail']:
            state['started'] = True
            return [observer]
        return []
    return LaunchDescription([
        DeclareLaunchArgument('install_path',default_value=str(Path.home()/'isaacsim')),
        DeclareLaunchArgument('ros_distro',default_value='humble'),
        RegisterEventHandler(OnProcessIO(on_stdout=on_stdout)),
        IncludeLaunchDescription(PythonLaunchDescriptionSource(str(official)),launch_arguments={
            'install_path':LaunchConfiguration('install_path'),
            'version':'5.1.0','use_internal_libs':'true',
            'ros_distro':LaunchConfiguration('ros_distro'),'standalone':shlex.quote(scene)}.items())])
