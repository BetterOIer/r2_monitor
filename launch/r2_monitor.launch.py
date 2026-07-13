from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='r2_monitor',
            executable='monitor_node',
            name='r2_monitor_node',
            output='screen',
        ),
    ])
