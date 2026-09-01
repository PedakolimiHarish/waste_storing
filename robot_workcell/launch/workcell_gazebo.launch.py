#!/usr/bin/env python3

import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import (
    IncludeLaunchDescription,
    RegisterEventHandler,
    SetEnvironmentVariable,
    ExecuteProcess,
)
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

# ============================================================
# Start conveyor command
# ============================================================

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

# ============================================================
# Controller readiness checker
# ============================================================

def create_robot_ready_checker(robot_name):
    """
    Wait until both the joint_state_broadcaster and
    joint_trajectory_controller are active for the robot.

    The process exits only when the robot is ready.
    """

    script = f"""
        while true; do

            output=$(ros2 control list_controllers \
                -c /{robot_name}/controller_manager 2>/dev/null || true)

            jsb=$(echo "$output" | grep -E \
                '^joint_state_broadcaster[[:space:]]+joint_state_broadcaster/JointStateBroadcaster[[:space:]]+active$' \
                || true)

            jtc=$(echo "$output" | grep -E \
                '^joint_trajectory_controller[[:space:]]+joint_trajectory_controller/JointTrajectoryController[[:space:]]+active$' \
                || true)

            if [ -n "$jsb" ] && [ -n "$jtc" ]; then
                echo "[workcell] {robot_name} controllers READY"
                exit 0
            fi

            sleep 1
        done
        """

    return ExecuteProcess(
        cmd=["bash", "-c", script],
        output="screen",
    )


def generate_launch_description():

    # ----------------------------------------------------------
    # Package paths
    # ----------------------------------------------------------

    workcell_share = get_package_share_directory(
        "robot_workcell"
    )

    conveyor_share = get_package_share_directory(
        "conveyorbelt_gz"
    )

    ur_simulation_share = get_package_share_directory(
        "ur_simulation_gz"
    )

    ros_gz_sim_share = get_package_share_directory(
        "ros_gz_sim"
    )

    robotiq_share = get_package_share_directory(
        "robotiq_description"
    )

    robotiq_resource_path = os.path.dirname(
        robotiq_share
    )

    # ----------------------------------------------------------
    # Files
    # ----------------------------------------------------------

    world_file = os.path.join(
        workcell_share,
        "worlds",
        "waste_sorting_cell.sdf",
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

    # ----------------------------------------------------------
    # Gazebo resource paths
    # ----------------------------------------------------------

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
        robotiq_resource_path,
    ])

    gazebo_resource_path = SetEnvironmentVariable(
        name="GZ_SIM_RESOURCE_PATH",
        value=resource_path,
    )

    # ----------------------------------------------------------
    # Gazebo -- START ONCE
    # ----------------------------------------------------------

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

    # ----------------------------------------------------------
    # /clock bridge -- START ONCE
    # ----------------------------------------------------------

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
    # ROBOT 1
    # ==========================================================

    robot1 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(robot_launch_file),
        launch_arguments={
            "robot_name": "robot1",
            "ur_type": "ur10e",
            "tf_prefix": "robot1_",
            "controllers_file": controllers_file,
            "description_file": description_file,
            "spawn_x": "-3.75",
            "spawn_y": "1",
            "spawn_z": "0.75",
            "spawn_yaw": "-1.57079632679",
        }.items(),
    )

    robot1_ready = create_robot_ready_checker(
        "robot1"
    )

    # ==========================================================
    # ROBOT 2
    # ==========================================================

    robot2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(robot_launch_file),
        launch_arguments={
            "robot_name": "robot2",
            "ur_type": "ur10e",
            "tf_prefix": "robot2_",
            "controllers_file": controllers_file,
            "description_file": description_file,
            "spawn_x": "-1.25",
            "spawn_y": "-1",
            "spawn_z": "0.75",
            "spawn_yaw": "1.57079632679",
        }.items(),
    )

    robot2_ready = create_robot_ready_checker(
        "robot2"
    )

    # ==========================================================
    # ROBOT 3
    # ==========================================================

    robot3 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(robot_launch_file),
        launch_arguments={
            "robot_name": "robot3",
            "ur_type": "ur10e",
            "tf_prefix": "robot3_",
            "controllers_file": controllers_file,
            "description_file": description_file,
            "spawn_x": "1.25",
            "spawn_y": "1",
            "spawn_z": "0.75",
            "spawn_yaw": "-1.57079632679",
        }.items(),
    )

    robot3_ready = create_robot_ready_checker(
        "robot3"
    )

    # ==========================================================
    # ROBOT 4
    # ==========================================================

    robot4 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(robot_launch_file),
        launch_arguments={
            "robot_name": "robot4",
            "ur_type": "ur10e",
            "tf_prefix": "robot4_",
            "controllers_file": controllers_file,
            "description_file": description_file,
            "spawn_x": "3.75",
            "spawn_y": "-1",
            "spawn_z": "0.75",
            "spawn_yaw": "1.57079632679",
        }.items(),
    )

    robot4_ready = create_robot_ready_checker(
        "robot4"
    )

    # ==========================================================
    # SEQUENTIAL STARTUP
    # ==========================================================

    start_robot2_after_robot1 = RegisterEventHandler(
        OnProcessExit(
            target_action=robot1_ready,
            on_exit=[
                robot2,
                robot2_ready,
            ],
        )
    )

    start_robot3_after_robot2 = RegisterEventHandler(
        OnProcessExit(
            target_action=robot2_ready,
            on_exit=[
                robot3,
                robot3_ready,
            ],
        )
    )

    start_robot4_after_robot3 = RegisterEventHandler(
        OnProcessExit(
            target_action=robot3_ready,
            on_exit=[
                robot4,
                robot4_ready,
            ],
        )
    )

    # ----------------------------------------------------------
    # Launch
    # ----------------------------------------------------------

    return LaunchDescription([
        gazebo_resource_path,

        gazebo,

        clock_bridge,

        # Start conveyor automatically once its service exists.
        conveyor_start,

        # Robot 1 starts immediately.
        robot1,
        robot1_ready,

        # Robot 2 starts after Robot 1 is ready.
        start_robot2_after_robot1,

        # Robot 3 starts after Robot 2 is ready.
        start_robot3_after_robot2,

        # Robot 4 starts after Robot 3 is ready.
        start_robot4_after_robot3,
    ])
