from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='ds_sensors',
            executable='talker',
            name='sensor_front_left',
            output='screen',
            emulate_tty=True,
            parameters=[
                {'direction_parameter': 315, 'gpio_trigger_parameter': 16, 'gpio_echo_parameter': 12}
            ]
        ),
        Node(
            package='ds_sensors',
            executable='talker',
            name='sensor_front_right',
            output='screen',
            emulate_tty=True,
            parameters=[
                {'direction_parameter': 225, 'gpio_trigger_parameter': 32, 'gpio_echo_parameter': 31}
            ]
        ),
        Node(
            package='ds_sensors',
            executable='talker',
            name='sensor_back_left',
            output='screen',
            emulate_tty=True,
            parameters=[
                {'direction_parameter': 45, 'gpio_trigger_parameter': 36, 'gpio_echo_parameter': 35}
            ]
        ),
        Node(
            package='ds_sensors',
            executable='talker',
            name='sensor_back_right',
            output='screen',
            emulate_tty=True,
            parameters=[
                {'direction_parameter': 135, 'gpio_trigger_parameter': 15, 'gpio_echo_parameter': 11}
            ]
        )
    ])