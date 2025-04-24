from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='ds_sensors',
            executable='talker',
            name='sensor_right',
            output='screen',
            emulate_tty=True,
            parameters=[
                {'direction_parameter': 30, 'gpio_trigger_parameter': 15, 'gpio_echo_parameter': 11}
            ]
        ),
        Node(
            package='ds_sensors',
            executable='talker',
            name='sensor_left',
            output='screen',
            emulate_tty=True,
            parameters=[
                {'direction_parameter': 150, 'gpio_trigger_parameter': 16, 'gpio_echo_parameter': 12}
            ]
        ),
        Node(
            package='ds_sensors',
            executable='talker',
            name='sensor_back',
            output='screen',
            emulate_tty=True,
            parameters=[
                {'direction_parameter': 300, 'gpio_trigger_parameter': 32, 'gpio_echo_parameter': 31}
            ]
        )
    ])