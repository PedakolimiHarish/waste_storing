#!/usr/bin/env python3

import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():

    package_name = 'robot_arm_description'

    pkg_share = get_package_share_directory(package_name)

    default_urdf = os.path.join(
        pkg_share,
        'urdf',
        'robot_arm.urdf.xacro'
    )

    default_rviz = os.path.join(
        pkg_share,
        'rviz',
        'robot_arm.rviz'
    )

    # ------------------------------------------------------------------
    # Launch arguments
    # ------------------------------------------------------------------

    urdf_model = LaunchConfiguration('urdf_model')
    jsp_gui = LaunchConfiguration('jsp_gui')
    use_rviz = LaunchConfiguration('use_rviz')
    use_sim_time = LaunchConfiguration('use_sim_time')

    declare_urdf_model = DeclareLaunchArgument(
        'urdf_model',
        default_value=default_urdf,
        description='Path to the robot URDF/Xacro file'
    )

    declare_jsp_gui = DeclareLaunchArgument(
        'jsp_gui',
        default_value='true',
        choices=['true', 'false'],
        description='Start joint_state_publisher_gui'
    )

    declare_use_rviz = DeclareLaunchArgument(
        'use_rviz',
        default_value='true',
        choices=['true', 'false'],
        description='Start RViz2'
    )

    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        choices=['true', 'false'],
        description='Use simulation time'
    )

    # ------------------------------------------------------------------
    # Robot description
    # ------------------------------------------------------------------

    robot_description = ParameterValue(
        Command([
            'xacro ',
            urdf_model
        ]),
        value_type=str
    )

    # ------------------------------------------------------------------
    # Robot State Publisher
    # ------------------------------------------------------------------

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[
            {
                'robot_description': robot_description,
                'use_sim_time': use_sim_time
            }
        ]
    )

    # ------------------------------------------------------------------
    # Joint State Publisher GUI
    # ------------------------------------------------------------------

    joint_state_publisher_gui = Node(
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui',
        name='joint_state_publisher_gui',
        output='screen',
        parameters=[
            {
                'use_sim_time': use_sim_time
            }
        ],
        condition=IfCondition(jsp_gui)
    )

    # ------------------------------------------------------------------
    # RViz
    # ------------------------------------------------------------------

    rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=[
            '-d',
            default_rviz
        ],
        parameters=[
            {
                'use_sim_time': use_sim_time
            }
        ],
        condition=IfCondition(use_rviz)
    )

    # ------------------------------------------------------------------
    # Launch
    # ------------------------------------------------------------------

    return LaunchDescription([
        declare_urdf_model,
        declare_jsp_gui,
        declare_use_rviz,
        declare_use_sim_time,

        robot_state_publisher,
        joint_state_publisher_gui,
        rviz,
    ])
