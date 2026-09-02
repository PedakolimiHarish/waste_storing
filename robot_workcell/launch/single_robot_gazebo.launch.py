#!/usr/bin/env python3

import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription,ExecuteProcess, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

def create_conveyor_start_command():

    script = r"""
        echo "[workcell] Waiting for conveyor control service..."

        until ros2 service list 2>/dev/null | grep -q "^/CONVEYORPOWER$"; do
            sleep 1
        done

        echo "[workcell] Conveyor service READY"
        echo "[workcell] Starting conveyor at 100% power..."

        ros2 service call \
            /CONVEYORPOWER \
            conveyorbelt_msgs/srv/ConveyorBeltControl \
            "{power: 100.0}"

        echo "[workcell] Conveyor START command sent"
    """

    return ExecuteProcess(
        cmd=["bash", "-c", script],
        output="screen",
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

    robotiq_share = get_package_share_directory(
        "robotiq_description"
    )

    # ==========================================================
    # Files
    # ==========================================================

    world_file = os.path.join(
        workcell_share,
        "worlds",
        "waste_sorting_cell_single.sdf",
    )

    robot_launch_file = os.path.join(
        workcell_share,
        "launch",
        "ur_workcell_robot.launch.py",
    )

    controllers_file = os.path.join(
        workcell_share,
        "config",
        "controllers.yaml",
    )

    description_file = os.path.join(
        workcell_share,
        "urdf",
        "ur10e_robotiq.urdf.xacro",
    )

    # ==========================================================
    # Gazebo resource paths
    # ==========================================================

    workcell_models = os.path.join(
        workcell_share,
        "models",
    )

    conveyor_models = os.path.join(
        conveyor_share,
        "models",
    )

    # model://robotiq_description/...
    # requires the parent "share" directory
    robotiq_resource_path = os.path.dirname(
        robotiq_share
    )

    resource_path = os.pathsep.join([
        workcell_models,
        conveyor_models,
        robotiq_resource_path,
    ])

    gazebo_resource_path = SetEnvironmentVariable(
        name="GZ_SIM_RESOURCE_PATH",
        value=resource_path,
    )

    # ==========================================================
    # Gazebo
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
    # Clock bridge
    # ==========================================================

    clock_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            "/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock"
        ],
        output="screen",
    )

    conveyor_start = create_conveyor_start_command()

    # ==========================================================
    # Single Robot
    # ==========================================================

    robot = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            robot_launch_file
        ),
        launch_arguments={
            "robot_name": "robot1",
            "ur_type": "ur10e",
            "tf_prefix": "robot1_",
            "controllers_file": controllers_file,
            "description_file": description_file,

            # Robot 1 position
            "spawn_x": "0",
            "spawn_y": "1.0",
            "spawn_z": "0.75",
            "spawn_yaw": "-1.57079632679",
        }.items(),
    )

    # ==========================================================
    # Launch
    # ==========================================================

    return LaunchDescription([
        gazebo_resource_path,
        gazebo,
        clock_bridge,
        conveyor_start,
        robot,
    ])
