#!/usr/bin/env python3

import os

from ament_index_python.packages import (
    get_package_share_directory,
)

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import (
    PythonLaunchDescriptionSource,
)


def robot_moveit(
    robot_launch_file,
    robot_name,
    tf_prefix,
):

    return IncludeLaunchDescription(

        PythonLaunchDescriptionSource(
            robot_launch_file
        ),

        launch_arguments={
            "robot_name": robot_name,
            "tf_prefix": tf_prefix,
            "ur_type": "ur10e",

        }.items(),
    )


def generate_launch_description():

    workcell_share = get_package_share_directory(
        "robot_workcell"
    )

    robot_launch_file = os.path.join(
        workcell_share,
        "launch",
        "ur_workcell_moveit_robot.launch.py",
    )

    robot1 = robot_moveit(
        robot_launch_file,
        "robot1",
        "robot1_",
    )

    robot2 = robot_moveit(
        robot_launch_file,
        "robot2",
        "robot2_",
    )

    robot3 = robot_moveit(
        robot_launch_file,
        "robot3",
        "robot3_",
    )

    robot4 = robot_moveit(
        robot_launch_file,
        "robot4",
        "robot4_",
    )

    return LaunchDescription([
        robot1,
        robot2,
        robot3,
        robot4,
    ])

