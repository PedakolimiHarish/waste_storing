#!/usr/bin/env python3

import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution

from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():

    # ==============================================================
    # Package
    # ==============================================================

    package_name = 'robot_arm_description'

    pkg_share = FindPackageShare(package_name)

    # ==============================================================
    # Default files
    # ==============================================================

    default_urdf = PathJoinSubstitution([
        pkg_share,
        'urdf',
        'robot_arm.urdf.xacro'
    ])

    default_rviz = PathJoinSubstitution([
        pkg_share,
        'rviz',
        'robot_arm.rviz'
    ])

    # ==============================================================
    # Launch configurations
    # ==============================================================

    urdf_model = LaunchConfiguration('urdf_model')
    use_jsp = LaunchConfiguration('use_jsp')
    jsp_gui = LaunchConfiguration('jsp_gui')
    use_rviz = LaunchConfiguration('use_rviz')
    use_sim_time = LaunchConfiguration('use_sim_time')

    # ==============================================================
    # Launch arguments
    # ==============================================================

    declare_urdf_model = DeclareLaunchArgument(
        name='urdf_model',
        default_value=default_urdf,
        description='Path to the robot URDF/Xacro file'
    )

    declare_use_jsp = DeclareLaunchArgument(
        name='use_jsp',
        default_value='false',
        choices=['true', 'false'],
        description='Start joint_state_publisher'
    )

    declare_jsp_gui = DeclareLaunchArgument(
        name='jsp_gui',
        default_value='false',
        choices=['true', 'false'],
        description='Start joint_state_publisher_gui'
    )

    declare_use_rviz = DeclareLaunchArgument(
        name='use_rviz',
        default_value='false',
        choices=['true', 'false'],
        description='Start RViz2'
    )

    declare_use_sim_time = DeclareLaunchArgument(
        name='use_sim_time',
        default_value='true',
        choices=['true', 'false'],
        description='Use simulation time'
    )

    # ==============================================================
    # Robot description
    # ==============================================================

    robot_description = ParameterValue(
        Command([
            'xacro ',
            urdf_model
        ]),
        value_type=str
    )

    # ==============================================================
    # Robot State Publisher
    # ==============================================================

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

    # ==============================================================
    # Joint State Publisher
    # ==============================================================

    joint_state_publisher = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher',
        output='screen',
        parameters=[
            {   'robot_description': robot_description,
                'use_sim_time': use_sim_time
            }
        ],
        condition=IfCondition(use_jsp)
    )

    # ==============================================================
    # Joint State Publisher GUI
    # ==============================================================

    joint_state_publisher_gui = Node(
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui',
        name='joint_state_publisher_gui',
        output='screen',

        condition=IfCondition(
            use_jsp
        ),
    )

    # ==============================================================
    # RViz
    # ==============================================================

    rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',

        condition=IfCondition(use_rviz),

        parameters=[
            {
                'use_sim_time': use_sim_time,
            }
        ],
    )

    # ==============================================================
    # Launch Description
    # ==============================================================

    return LaunchDescription([

        # Arguments
        declare_urdf_model,
        declare_use_jsp,
        declare_jsp_gui,
        declare_use_rviz,
        declare_use_sim_time,

        # Nodes
        robot_state_publisher,
        joint_state_publisher,
        joint_state_publisher_gui,
        rviz,

    ])
