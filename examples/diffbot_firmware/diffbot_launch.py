import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    pkg_share = get_package_share_directory('diffbot_firmware')

    # Robot State Publisher Node
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{'use_sim_time': False}]
    )

    # Differential Drive Controller Node
    diffbot_node = Node(
        package='diffbot_firmware',
        executable='diffbot_controller',
        name='diffbot_controller',
        output='screen',
        remappings=[
            ('/cmd_vel', '/teleop/cmd_vel'),
            ('/odom', '/diffbot/odom')
        ]
    )

    return LaunchDescription([
        robot_state_publisher_node,
        diffbot_node
    ])
