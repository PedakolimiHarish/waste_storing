#!/usr/bin/env python3

import os
import tempfile

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    OpaqueFunction,
    RegisterEventHandler,
)
from launch.event_handlers import OnShutdown
from launch.substitutions import (
    Command,
    FindExecutable,
    LaunchConfiguration,
)
from launch_ros.actions import Node

from ament_index_python.packages import (
    get_package_share_directory,
)

def create_controller_file(
    template_file,
    robot_name,
    tf_prefix,
):
    """
    Create a robot-specific controller configuration.

    Only joint names are prefixed.
    Controller names are NOT rewritten here.
    """

    with open(template_file, "r") as file:
        content = file.read()

    content = content.replace(
        "${tf_prefix}",
        tf_prefix,
    )

    fd, path = tempfile.mkstemp(
        prefix=f"{robot_name}_controllers_",
        suffix=".yaml",
    )

    with os.fdopen(fd, "w") as file:
        file.write(content)

    return path


def create_jsb_file(
    robot_name,
):
    content = f"""\
/{robot_name}/joint_state_broadcaster:
  ros__parameters:
    type: joint_state_broadcaster/JointStateBroadcaster
"""

    fd, path = tempfile.mkstemp(
        prefix=f"{robot_name}_jsb_",
        suffix=".yaml",
    )

    with os.fdopen(fd, "w") as file:
        file.write(content)

    return path


def create_jtc_file(
    robot_name,
    tf_prefix,
):
    joints = [
        f"{tf_prefix}shoulder_pan_joint",
        f"{tf_prefix}shoulder_lift_joint",
        f"{tf_prefix}elbow_joint",
        f"{tf_prefix}wrist_1_joint",
        f"{tf_prefix}wrist_2_joint",
        f"{tf_prefix}wrist_3_joint",
    ]

    content = f"""\
/{robot_name}/joint_trajectory_controller:
  ros__parameters:
    type: joint_trajectory_controller/JointTrajectoryController

    joints:
"""

    for joint in joints:
        content += f"      - {joint}\n"

    content += """\
    command_interfaces:
      - position

    state_interfaces:
      - position
      - velocity

    state_publish_rate: 100.0
    action_monitor_rate: 20.0

    allow_partial_joints_goal: false

    constraints:
      stopped_velocity_tolerance: 0.2
      goal_time: 0.0
"""

    fd, path = tempfile.mkstemp(
        prefix=f"{robot_name}_jtc_",
        suffix=".yaml",
    )

    with os.fdopen(fd, "w") as file:
        file.write(content)

    return path

def create_gripper_controller_file(
    robot_name,
    tf_prefix,
):
    gripper_joint = (
        f"{tf_prefix}robotiq_85_left_knuckle_joint"
    )

    content = f"""\
/{robot_name}/robotiq_gripper_controller:
  ros__parameters:
    type: joint_trajectory_controller/JointTrajectoryController

    joints:
      - {gripper_joint}

    command_interfaces:
      - position

    state_interfaces:
      - position
      - velocity

    state_publish_rate: 100.0
    action_monitor_rate: 20.0

    allow_partial_joints_goal: false

    constraints:
      stopped_velocity_tolerance: 0.2
      goal_time: 0.0
"""

    fd, path = tempfile.mkstemp(
        prefix=f"{robot_name}_gripper_",
        suffix=".yaml",
    )

    with os.fdopen(fd, "w") as file:
        file.write(content)

    return path

def cleanup_temp_files(paths):
    for path in paths:
        try:
            if path and os.path.exists(path):
                os.remove(path)
                print(
                    f"[robot_workcell] Removed temporary file: {path}"
                )
        except OSError as exc:
            print(
                f"[robot_workcell] Could not remove "
                f"{path}: {exc}"
            )

def launch_setup(context, *args, **kwargs):

    robot_name = LaunchConfiguration(
        "robot_name"
    ).perform(context)

    ur_type = LaunchConfiguration(
        "ur_type"
    )

    tf_prefix = LaunchConfiguration(
        "tf_prefix"
    ).perform(context)

    controllers_file = LaunchConfiguration(
        "controllers_file"
    ).perform(context)

    description_file = LaunchConfiguration(
        "description_file"
    )

    safety_limits = LaunchConfiguration(
        "safety_limits"
    )

    safety_pos_margin = LaunchConfiguration(
        "safety_pos_margin"
    )

    safety_k_position = LaunchConfiguration(
        "safety_k_position"
    )

    spawn_x = LaunchConfiguration(
        "spawn_x"
    )

    spawn_y = LaunchConfiguration(
        "spawn_y"
    )

    spawn_z = LaunchConfiguration(
        "spawn_z"
    )

    spawn_yaw = LaunchConfiguration(
        "spawn_yaw"
    )

    controller_file = create_controller_file(
        controllers_file,
        robot_name,
        tf_prefix,
    )

    jsb_file = create_jsb_file(
        robot_name,
    )

    jtc_file = create_jtc_file(
        robot_name,
        tf_prefix,
    )

    gripper_controller_file = create_gripper_controller_file(
        robot_name,
        tf_prefix,
    )

    temp_files = [
        controller_file,
        jsb_file,
        jtc_file,
        gripper_controller_file,
    ]

    cleanup_handler = RegisterEventHandler(
        OnShutdown(
            on_shutdown=[
                OpaqueFunction(
                    function=lambda context:
                    cleanup_temp_files(temp_files)
                )
            ]
        )
    )



    # ----------------------------------------------------------
    # Robot description
    # ----------------------------------------------------------

    robot_description_content = Command(
        [
            FindExecutable(name="xacro"),
            " ",
            description_file,
            " ",
            "safety_limits:=",
            safety_limits,
            " ",
            "safety_pos_margin:=",
            safety_pos_margin,
            " ",
            "safety_k_position:=",
            safety_k_position,
            " ",
            "name:=",
            robot_name,
            " ",
            "ur_type:=",
            ur_type,
            " ",
            "tf_prefix:=",
            tf_prefix,
            " ",
            "simulation_controllers:=",
            controller_file,
            " ",
            "ros_namespace:=",
            robot_name,
        ]
    )

    # ----------------------------------------------------------
    # Robot State Publisher
    # ----------------------------------------------------------

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        namespace=robot_name,
        name="robot_state_publisher",
        output="screen",
        parameters=[
            {
                "use_sim_time": True,
                "robot_description": robot_description_content,
            }
        ],
    )

    # ----------------------------------------------------------
    # Spawn
    # ----------------------------------------------------------

    gz_spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        output="screen",
        arguments=[
            "-string",
            robot_description_content,
            "-name",
            robot_name,
            "-x",
            spawn_x,
            "-y",
            spawn_y,
            "-z",
            spawn_z,
            "-Y",
            spawn_yaw,
            "-allow_renaming",
            "false",
        ],
    )

    # ----------------------------------------------------------
    # Joint State Broadcaster
    # ----------------------------------------------------------

    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        namespace=robot_name,
        output="screen",
        arguments=[
            "joint_state_broadcaster",
            "--controller-manager",
            "controller_manager",
            "--controller-manager-timeout",
            "120",
            "--param-file",
            jsb_file,
        ],
    )

    # ----------------------------------------------------------
    # Joint Trajectory Controller
    # ----------------------------------------------------------

    joint_trajectory_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        namespace=robot_name,
        output="screen",
        arguments=[
            "joint_trajectory_controller",
            "--controller-manager",
            "controller_manager",
            "--controller-manager-timeout",
            "120",
            "--param-file",
            jtc_file,
        ],
    )

    gripper_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        namespace=robot_name,
        output="screen",
        arguments=[
            "robotiq_gripper_controller",
            "--controller-manager",
            "controller_manager",
            "--controller-manager-timeout",
            "120",
            "--param-file",
            gripper_controller_file,
        ],
    )

    return [
        robot_state_publisher,
        gz_spawn_entity,
        joint_state_broadcaster_spawner,
        joint_trajectory_controller_spawner,
        gripper_controller_spawner,
        cleanup_handler,
    ]


def generate_launch_description():

    return LaunchDescription([
        DeclareLaunchArgument(
            "robot_name",
            default_value="robot1",
        ),

        DeclareLaunchArgument(
            "ur_type",
            default_value="ur10e",
        ),

        DeclareLaunchArgument(
            "tf_prefix",
            default_value="",
        ),

        DeclareLaunchArgument(
            "controllers_file",
        ),

        DeclareLaunchArgument(
            "description_file",
            default_value=os.path.join(
                get_package_share_directory("robot_workcell"),
                "urdf",
                "ur10e_robotiq.urdf.xacro",
            ),
        ),

        DeclareLaunchArgument(
            "safety_limits",
            default_value="true",
        ),

        DeclareLaunchArgument(
            "safety_pos_margin",
            default_value="0.15",
        ),

        DeclareLaunchArgument(
            "safety_k_position",
            default_value="20",
        ),

        DeclareLaunchArgument(
            "spawn_x",
            default_value="0.0",
        ),

        DeclareLaunchArgument(
            "spawn_y",
            default_value="0.0",
        ),

        DeclareLaunchArgument(
            "spawn_z",
            default_value="0.75",
        ),

        DeclareLaunchArgument(
            "spawn_yaw",
            default_value="0.0",
        ),

        OpaqueFunction(
            function=launch_setup
        ),
    ])
