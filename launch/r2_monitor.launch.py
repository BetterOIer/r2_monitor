from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, RegisterEventHandler, TimerAction
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessStart
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    open_browser = DeclareLaunchArgument('open_browser', default_value='false')
    start_rosbridge = DeclareLaunchArgument('start_rosbridge', default_value='false')
    rosbridge = Node(
        package='rosbridge_server',
        executable='rosbridge_websocket',
        name='rosbridge_monitor',
        condition=IfCondition(LaunchConfiguration('start_rosbridge')),
        parameters=[{'port': 9090}],
        output='screen',
    )
    monitor = Node(package='r2_monitor', executable='monitor_node', output='screen')
    web_dir = PathJoinSubstitution([FindPackageShare('r2_monitor'), 'web'])
    web_server = ExecuteProcess(
        cmd=['python3', '-m', 'http.server', '7893', '--bind', '0.0.0.0', '--directory', web_dir],
        shell=False,
        name='r2_monitor_web',
        output='screen',
    )
    open_web = ExecuteProcess(
        condition=IfCondition(LaunchConfiguration('open_browser')),
        cmd=['xdg-open', 'http://localhost:7893/r2_monitor.html'],
        shell=False,
    )
    delayed_open = RegisterEventHandler(
        OnProcessStart(target_action=web_server, on_start=[TimerAction(period=1.0, actions=[open_web])])
    )
    return LaunchDescription([open_browser, start_rosbridge, rosbridge, monitor, web_server, delayed_open])
