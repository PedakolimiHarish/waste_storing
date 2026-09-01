#!/usr/bin/env python3

import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import (
    IncludeLaunchDescription,
    SetEnvironmentVariable,
)
from launch.launch_description_sources import (
    PythonLaunchDescriptionSource,
)


def generate_launch_description():

    # ==========================================================
    # Package paths
    # ==========================================================

    workcell_share = get_package_share_directory(
        "robot_workcell"
    )

    conveyor_share = get_package_share_directory(
        "conveyorbelt_gz"
    )

    ros_gz_sim_share = get_package_share_directory(
        "ros_gz_sim"
    )

    # ==========================================================
    # World
    # ==========================================================

    world_file = os.path.join(
        workcell_share,
        "worlds",
        "waste_sorting_cell.sdf",
    )

    # ==========================================================
    # Gazebo model/resource paths
    # ==========================================================

    workcell_models = os.path.join(
        workcell_share,
        "models",
    )

    conveyor_models = os.path.join(
        conveyor_share,
        "models",
    )

    resource_path = os.pathsep.join([
        workcell_models,
        conveyor_models,
    ])

    gazebo_resource_path = SetEnvironmentVariable(
        name="GZ_SIM_RESOURCE_PATH",
        value=resource_path,
    )

    # ==========================================================
    # Start Gazebo with world only
    # ==========================================================

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                ros_gz_sim_share,
                "launch",
                "gz_sim.launch.py",
            )
        ),
        launch_arguments={
            "gz_args": f"-r -v 4 {world_file}",
            "on_exit_shutdown": "true",
        }.items(),
    )

    # ==========================================================
    # Launch
    # ==========================================================

    return LaunchDescription([
        gazebo_resource_path,
        gazebo,
    ])
