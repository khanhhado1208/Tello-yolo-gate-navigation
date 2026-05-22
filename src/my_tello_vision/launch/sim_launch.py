import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import ExecuteProcess

def generate_launch_description():
    # Get the path to the drone model
    pkg_tello_description = get_package_share_directory('tello_description')
    drone_urdf = os.path.join(pkg_tello_description, 'urdf', 'tello.urdf')

    return LaunchDescription([
        # 1. Gazebo Server
        ExecuteProcess(
            cmd=['gzserver', '--verbose', '-s', 'libgazebo_ros_init.so', '-s', 'libgazebo_ros_factory.so', 'empty.world'],
            output='screen'
        ),

        # 2. Gazebo Client
        ExecuteProcess(
            cmd=['gzclient'],
            output='screen'
        ),

        # 3. Inject Drone Entity (FIXED: Now points to the URDF file)
        Node(
            package='tello_gazebo',
            executable='inject_entity.py',
            output='screen',
            arguments=[drone_urdf, '0', '0', '1', '0'] # file, x, y, z, yaw
        ),

        # 4. Tello Driver
        Node(
            package='tello_driver',
            executable='tello_driver_main',
            output='screen',
            parameters=[{
                'tello_ip': '127.0.0.1',
                'tello_port': 8889,
                'connect_timeout_sec': 10.0
            }]
        ),

        # 5. Vision Control
        Node(
            package='my_tello_vision',
            executable='tello_vision_control.py',
            output='screen'
        ),
    ])
